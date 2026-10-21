"""Independent reconstruction of frozen PR-engine experiment receipts.

No metric kernels or producer-summary helpers are imported. Source-data ZIPs
are checked only by the explicit completed-run audit, after controlled timing.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import random
import statistics
import zipfile

from advancement_data_gate import RELEASE_BINDINGS, released_metadata

ROOT = Path(__file__).resolve().parents[1]
EXACT = ("sparse_pr", "dense_pr_direct", "sparse_both", "dense_nearest_both", "klein_pr", "benchopt_both", "radix_pr", "radix_both", "dense_pr_direct_radix", "dense_pr_nearest_radix")
BASE_METHODS = (*EXACT, "v02_race", "fast_race", "fast_exact_completion", "fast_race_radix")
REQUIRED_SOURCES = {
    "experiments/benchmark_pr_engine.py", "experiments/benchmark_advancement.py",
    "experiments/advancement_data_gate.py", "experiments/fast_vus_adapter.py",
    "experiments/benchopt_vus_adapter.py", "src/sparse_vus/pr_compiled.py",
    "src/sparse_vus/fast_racing.py", "src/sparse_vus/racing.py",
    "src/sparse_vus/certified.py", "src/sparse_vus/selection.py",
    "src/sparse_vus/core.py", "src/sparse_vus/compiled.py",
    "src/sparse_vus/radix.py", "src/sparse_vus/dense_radix.py",
    ".cache/fast_vus/fast_vus.py", ".cache/benchopt_vus/metrics.py",
}
IDENTITY = ("series", "family", "n", "max_buffer", "label_sha256", "score_sha256")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return type(value) in (float, int) and math.isfinite(value)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def winner_set(values):
    best = max(values.values())
    return sorted(model for model, value in values.items() if best - value <= 1e-10)


def named_set(values, models, empty=False):
    need(isinstance(values, list) and values == sorted(set(values))
         and set(values) <= set(models) and (empty or bool(values)), "Invalid model-name set")


def check_values(values, models):
    need(set(values) == set(models), "Incomplete exact model values")
    need(all(finite(v) and -1e-10 <= v <= 1 + 1e-10 for v in values.values()), "Invalid exact PR")


def percentile(values, q):
    ordered = sorted(values)
    offset = (len(ordered) - 1) * q
    lo, hi = math.floor(offset), math.ceil(offset)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (offset - lo)


def ratio_statistics(rows, method, comparator):
    ratios = [r["median_seconds"][comparator] / r["median_seconds"][method] for r in rows]
    need(all(finite(v) and v > 0 for v in ratios), "Nonfinite derived speed ratio")
    families = defaultdict(list)
    for row, ratio in zip(rows, ratios):
        families[row["family"]].append(math.log(ratio))
    family_means = {f: math.exp(math.fsum(v) / len(v)) for f, v in sorted(families.items())}
    slowdowns = [1 / v for v in ratios]
    return {
        "median": statistics.median(ratios),
        "geomean": math.exp(math.fsum(math.log(v) for v in ratios) / len(ratios)),
        "aggregate_ratio": math.fsum(r["median_seconds"][comparator] for r in rows)
                           / math.fsum(r["median_seconds"][method] for r in rows),
        "faster_cases": sum(v > 1 for v in ratios), "slower_cases": sum(v < 1 for v in ratios),
        "min_ratio": min(ratios), "max_ratio": max(ratios), "p05_ratio": percentile(ratios, .05),
        "max_slowdown": max(slowdowns), "p95_slowdown": percentile(slowdowns, .95),
        "slowdowns_over_2x": sum(v > 2 for v in slowdowns),
        "macro_family_geomean": math.exp(math.fsum(math.log(v) for v in family_means.values()) / len(family_means)),
        "family_geomeans": family_means,
    }


def uncertainty(rows, methods, specification):
    """Resample family clusters with all member cases, never repetitions."""
    groups = {str(w): [r for r in rows if r["max_buffer"] == w]
              for w in sorted({r["max_buffer"] for r in rows})}
    groups["combined_30_100"] = [r for r in rows if r["max_buffer"] in (30, 100)]
    output = {}
    for name, cases in groups.items():
        families = sorted({r["family"] for r in cases})
        clusters = [[r for r in cases if r["family"] == family] for family in families]
        rng = random.Random(specification["seed"])
        samples = [[rng.randrange(len(clusters)) for _ in clusters]
                   for _ in range(specification["repetitions"])]
        output[name] = {}
        for method in specification["references"]:
            output[name][method] = {}
            for comparator in methods:
                if method == comparator:
                    continue
                n = [len(c) for c in clusters]
                logsum = [math.fsum(math.log(r["median_seconds"][comparator] / r["median_seconds"][method]) for r in c) for c in clusters]
                numerator = [math.fsum(r["median_seconds"][comparator] for r in c) for c in clusters]
                denominator = [math.fsum(r["median_seconds"][method] for r in c) for c in clusters]
                geometric = [math.exp(math.fsum(logsum[i] for i in sample) / sum(n[i] for i in sample)) for sample in samples]
                aggregate = [math.fsum(numerator[i] for i in sample) / math.fsum(denominator[i] for i in sample) for sample in samples]
                output[name][method][comparator] = {
                    "families": len(families), "cases": len(cases),
                    "geomean_ci95": [percentile(geometric, .025), percentile(geometric, .975)],
                    "aggregate_ratio_ci95": [percentile(aggregate, .025), percentile(aggregate, .975)],
                }
    return output


def audit_records(rows, protocol, inputs):
    need(protocol["version"] == 3 and protocol["split"] in ("development", "holdout"),
         "This auditor requires v3; use the unchanged source-v2 auditor for historical v2 runs")
    need(not protocol["include_full_budget"] or protocol["split"] == "development", "Full budget is development only")
    methods = [*BASE_METHODS] + (["fast_full_budget"] if protocol["include_full_budget"] else [])
    need(protocol["method_ids"] == methods, "Frozen method set differs")
    need(protocol["repetitions"] == 3 and protocol["widths"] == [30, 100, 300]
         and protocol["primary_widths"] == [30, 100], "Unexpected coverage contract")
    need(protocol["primary_width"] == 30 and protocol["secondary_width"] == 100
         and protocol["stress_width"] == 300, "Changed primary decision regime")
    need(protocol["task_order"] == "width_then_series", "Changed task ordering protocol")
    need(protocol["bootstrap"] == {"unit": "family", "repetitions": 2000, "seed": 2026102102,
                                   "confidence": .95, "references": ["fast_race", "sparse_pr", "radix_pr", "fast_race_radix"]},
         "Changed uncertainty protocol")
    need(protocol["tie_atol"] == 1e-10 and protocol["order_margin"] == 3e-10
         and protocol["containment_tolerance"] == 1e-10
         and protocol["exact_parity_tolerance"] == 1e-11, "Numerical contract differs")
    need(finite(protocol["adaptive_fraction"]) and 0 < protocol["adaptive_fraction"] <= 1
         and type(protocol["memory_bytes_per_model"]) is int and protocol["memory_bytes_per_model"] >= 0,
         "Invalid frozen work budget")
    models = protocol["models"]
    need(models == sorted(set(models)) and len(models) == 3, "Incomplete model coverage")
    keys = [(r["max_buffer"], r["series"]) for r in inputs]
    need(keys == sorted(keys) and len(keys) == len(set(keys)), "Invalid input task manifest")
    need(len(rows) == len(inputs) == protocol["cases"] and bool(rows), "Missing or duplicate tasks")
    rng = random.Random(protocol["seed"])
    max_error = max_slack = 0.0
    for row, identity in zip(rows, inputs):
        need({k: row[k] for k in IDENTITY} == identity, "Measured input identity differs from frozen task")
        width = row["max_buffer"]
        need(type(width) is int and width in (30, 100, 300), "Unexpected width")
        need(set(row["score_sha256"]) == set(models), "Missing score identity")
        for field in ("values", "seconds", "median_seconds"):
            need(set(row[field]) == set(methods), f"Missing method: {field}")
        expected_order = []
        for _ in range(3):
            order = methods.copy()
            rng.shuffle(order)
            expected_order.append(order)
        need(row["method_order"] == expected_order, "Method order differs from frozen randomization")
        for method in methods:
            durations = row["seconds"][method]
            need(len(durations) == 3 and all(finite(v) and v > 0 for v in durations), "Invalid timing")
            need(finite(row["median_seconds"][method])
                 and row["median_seconds"][method] == statistics.median(durations), "False timing median")
        reference = row["values"]["sparse_pr"]["pr"]
        check_values(reference, models)
        target = winner_set(reference)
        for method in EXACT:
            result = row["values"][method]
            check_values(result["pr"], models)
            need(result["selected"] == winner_set(result["pr"]) == target, "Wrong exact selection")
            error = max(abs(result["pr"][m] - reference[m]) for m in models)
            max_error = max(max_error, error)
            need(error <= 1e-11, "False exact baseline parity")
        for method in methods[len(EXACT):]:
            result = row["values"][method]
            for field in ("selected", "candidates"):
                named_set(result[field], models)
            need(result["selected"] == target, "Wrong racing selection or omitted exact tie")
            bounds = result["bounds"]
            need(set(bounds) == set(models), "Missing model bound")
            unique = curves = 0
            full = []
            for model in models:
                bound = bounds[model]
                lower, upper = bound["pr_lower"], bound["pr_upper"]
                need(finite(lower) and finite(upper) and -1e-10 <= lower <= upper <= 1 + 1e-10, "Invalid bound")
                slack = max(lower - reference[model], reference[model] - upper, 0.)
                max_slack = max(max_slack, slack)
                need(slack <= 1e-10, "Bound excludes exact PR")
                queried = bound["evaluated_widths"]
                need(isinstance(queried, list) and queried == sorted(set(queried)) and bool(queried)
                     and all(type(w) is int and 0 <= w <= width for w in queried), "Invalid queried widths")
                need(type(bound["curve_evaluations"]) is int and bound["curve_evaluations"] >= len(queried), "False curve count")
                need(type(bound["exact"]) is bool and bound["exact"] == (len(queried) == width + 1), "False exact flag")
                if bound["exact"]:
                    full.append(model)
                    need(lower == upper, "Exact bound is not singleton")
                unique += len(queried)
                curves += bound["curve_evaluations"]
            check_values(result["exact_pr"], full)
            need(all(abs(result["exact_pr"][m] - reference[m]) <= 1e-11
                     and abs(result["exact_pr"][m] - bounds[m]["pr_lower"]) <= 1e-11 for m in full), "Wrong exact model value")
            for count in ("total_unique_widths", "total_curve_evaluations", "full_evaluation_count"):
                need(type(result[count]) is int and result[count] >= 0, "Invalid work count")
            need(result["total_unique_widths"] == unique and result["total_curve_evaluations"] == curves
                 and result["full_evaluation_count"] == len(full), "Aggregate work is false")
            separated = [m for m in models if all(bounds[m]["pr_lower"] > bounds[o]["pr_upper"] + 3e-10
                                                  for o in models if o != m)]
            floor = max(b["pr_lower"] for b in bounds.values())
            candidates = separated or [m for m in models if bounds[m]["pr_upper"] >= floor - 3e-10]
            need(result["candidates"] == candidates, "Wrong candidate policy")
            excluded = [m for m in models if m not in candidates]
            need(all(max(reference.values()) - reference[m] > 1e-10 for m in excluded), "Pruned an exact tie")
            if not separated:
                need(all(bounds[m]["exact"] for m in candidates), "Stopped before surviving models became exact")
            need(type(result["early_winner"]) is bool, "Invalid early flag")
            if method == "v02_race":
                need(result["early_winner"] == bool(separated) and result["pruned"] == excluded, "False v0.2 decision metadata")
                for count in ("initial_unique_widths", "initial_curve_evaluations", "refinement_steps"):
                    need(type(result[count]) is int and result[count] >= 0, "Invalid old-racer count")
                need(unique == result["initial_unique_widths"] + result["refinement_steps"], "Old-racer width accounting differs")
                need(result["initial_curve_evaluations"] + result["refinement_steps"] <= curves
                     <= result["initial_curve_evaluations"] + 3 * result["refinement_steps"], "Old-racer curve accounting differs")
            else:
                need(curves == unique and all(b["curve_evaluations"] == len(b["evaluated_widths"]) for b in bounds.values()), "Fast racer recomputed widths")
                need(result["early_winner"] == (len(target) == 1 and len(full) < len(models)), "False fast early flag")
                named_set(result["fallback_models"], models, empty=True)
                need(set(result["fallback_models"]) <= set(full), "Fallback model did not complete")
                for count in ("retained_curve_bytes", "adaptive_curve_evaluations", "completion_curve_evaluations"):
                    need(type(result[count]) is int and result[count] >= 0, "Invalid fast-racer work count")
                need(result["adaptive_curve_evaluations"] + result["completion_curve_evaluations"] == curves, "Hidden phase work")
                need(result["retained_curve_bytes"] <= len(models) * protocol["memory_bytes_per_model"], "Retained memory exceeds budget")
                fraction = (0 if method == "fast_exact_completion" else 1 if method == "fast_full_budget" else protocol["adaptive_fraction"])
                cap = 0 if fraction == 0 else min(width + 1, max(2, int((width + 1) * fraction)))
                need(result["adaptive_curve_evaluations"] <= len(models) * cap, "Adaptive work exceeds width cap")
                need(result["completion_curve_evaluations"] >= len(result["fallback_models"]), "Fallback accounting is impossible")
                need(result["completion_curve_evaluations"] <= sum(
                    len(bounds[m]["evaluated_widths"]) for m in result["fallback_models"]), "Completion work lacks fallback models")
                need(all(len(bounds[m]["evaluated_widths"]) <= cap
                         for m in models if m not in result["fallback_models"]), "Nonfallback model exceeds adaptive budget")
                if fraction == 0:
                    need(full == models and result["fallback_models"] == models
                         and result["adaptive_curve_evaluations"] == 0
                         and result["completion_curve_evaluations"] == len(models) * (width + 1)
                         and result["retained_curve_bytes"] == 0, "Zero-adaptation ablation is not exact completion")
    by_width = {}
    for width in sorted({r["max_buffer"] for r in rows}):
        group = [r for r in rows if r["max_buffer"] == width]
        summary = {"cases": len(group), "sum_case_median_seconds": {
            m: math.fsum(r["median_seconds"][m] for r in group) for m in methods}, "methods": {}}
        for method in ["sparse_pr", "radix_pr", *methods[len(EXACT):]]:
            output = {
                "by_comparator": {c: ratio_statistics(group, method, c) for c in methods if c != method},
            }
            if method in ("sparse_pr", "radix_pr"):
                summary["methods"][method] = output
                continue
            output.update({
                "total_unique_widths": sum(r["values"][method]["total_unique_widths"] for r in group),
                "total_curve_evaluations": sum(r["values"][method]["total_curve_evaluations"] for r in group),
                "full_model_evaluations": sum(r["values"][method]["full_evaluation_count"] for r in group),
                "median_unique_fraction": statistics.median(r["values"][method]["total_unique_widths"] / (3 * (width + 1)) for r in group),
                "regressions_vs_sparse_pr": [{"series": r["series"], "family": r["family"],
                    "ratio": r["median_seconds"]["sparse_pr"] / r["median_seconds"][method]}
                    for r in group if r["median_seconds"][method] > r["median_seconds"]["sparse_pr"]],
            })
            if method != "v02_race":
                output.update(fallback_models=sum(len(r["values"][method]["fallback_models"]) for r in group),
                              adaptive_curve_evaluations=sum(r["values"][method]["adaptive_curve_evaluations"] for r in group),
                              completion_curve_evaluations=sum(r["values"][method]["completion_curve_evaluations"] for r in group),
                              max_retained_curve_bytes=max(r["values"][method]["retained_curve_bytes"] for r in group))
            summary["methods"][method] = output
        by_width[str(width)] = summary
    intervals = uncertainty(rows, methods, protocol["bootstrap"])
    primary_pass = "30" in intervals and all(
        intervals["30"]["fast_race"][comparator][measure][0] > 1
        for comparator in ("sparse_pr", "dense_pr_direct", "radix_pr")
        for measure in ("geomean_ci95", "aggregate_ratio_ci95"))
    radix_pass = "30" in intervals and all(
        intervals["30"]["radix_pr"][comparator][measure][0] > 1
        for comparator in ("sparse_pr", "dense_pr_direct", "dense_nearest_both", "dense_pr_direct_radix", "dense_pr_nearest_radix")
        for measure in ("geomean_ci95", "aggregate_ratio_ci95"))
    radix_racing_pass = "30" in intervals and all(
        intervals["30"]["fast_race_radix"][comparator][measure][0] > 1
        for comparator in ("sparse_pr", "dense_pr_direct", "radix_pr", "dense_pr_direct_radix", "dense_pr_nearest_radix")
        for measure in ("geomean_ci95", "aggregate_ratio_ci95"))
    timing_variation = {method: {
        "median_within_case_max_over_min": statistics.median(max(r["seconds"][method]) / min(r["seconds"][method]) for r in rows),
        "max_within_case_max_over_min": max(max(r["seconds"][method]) / min(r["seconds"][method]) for r in rows),
    } for method in methods}
    return {"cases": len(rows), "max_exact_pr_error": max_error, "max_enclosure_slack": max_slack,
            "by_width": by_width, "uncertainty": intervals, "measurement_variation": timing_variation,
            "primary_decision": {"width": 30, "passes": primary_pass,
                                 "criterion": "fast_race: both geomean and aggregate-ratio lower 95% family-bootstrap bounds exceed 1 against sparse_pr, dense_pr_direct, and radix_pr; correctness also required."},
            "radix_primary_decision": {"width": 30, "passes": radix_pass,
                                       "criterion": "radix_pr: both geomean and aggregate-ratio lower 95% family-bootstrap bounds exceed 1 against sparse_pr, dense_pr_direct, dense_nearest_both, dense_pr_direct_radix, and dense_pr_nearest_radix; correctness also required."},
            "radix_racing_decision": {"width": 30, "passes": radix_racing_pass,
                                      "criterion": "fast_race_radix: both geomean and aggregate-ratio lower 95% family-bootstrap bounds exceed 1 against sparse_pr, dense_pr_direct, radix_pr, dense_pr_direct_radix, and dense_pr_nearest_radix; correctness also required."}}


def compare(actual, expected, path="summary"):
    if isinstance(expected, dict):
        need(isinstance(actual, dict) and actual.keys() == expected.keys(), f"Summary fields differ: {path}")
        for key in expected:
            compare(actual[key], expected[key], f"{path}/{key}")
    elif isinstance(expected, list):
        need(isinstance(actual, list) and len(actual) == len(expected), f"Summary list differs: {path}")
        for i, (a, b) in enumerate(zip(actual, expected)):
            compare(a, b, f"{path}/{i}")
    elif isinstance(expected, float):
        need(finite(actual) and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), f"Summary numeric mismatch: {path}")
    else:
        need(type(actual) is type(expected) and actual == expected, f"Summary value mismatch: {path}")


def validate_inputs_manifest(inputs, protocol, root, *, verify_members=True):
    metadata, models, score_hashes, development, locks, receipt = released_metadata(root)
    wanted = sorted(development if protocol["split"] == "development" else set(metadata) - set(development))
    need(len(wanted) == (42 if protocol["split"] == "development" else 308), "Split coverage differs")
    expected = [{"series": s, "family": metadata[s]["family"], "n": metadata[s]["n"],
                 "max_buffer": w, "label_sha256": metadata[s]["label_sha256"],
                 "score_sha256": {m: score_hashes[s, m] for m in models}}
                for w in (30, 100, 300) for s in wanted]
    need(inputs == expected and protocol["models"] == models, "Frozen inputs differ from immutable split")
    result = {"status": "PASS", "series": len(wanted), "score_vectors": 3 * len(wanted),
              "release_bindings": RELEASE_BINDINGS, "original_measurements_sha256": receipt["records_sha256"],
              "source_members_checked": verify_members}
    if not verify_members:
        return result
    import numpy as np
    import pandas as pd
    for filename, expected_hash in locks["files"].items():
        need(sha(root / "cache" / filename) == expected_hash, f"Source file changed: {filename}")
    with zipfile.ZipFile(root / "cache/TSB-AD-U.zip") as archive:
        paths = [p for p in archive.namelist() if p.endswith(".csv")]
        mapping = {Path(p).stem: p for p in paths}
        need(len(mapping) == len(paths), "Ambiguous label member")
        for series in wanted:
            raw = archive.read(mapping[series])
            need(hashlib.sha256(raw).hexdigest() == metadata[series]["label_sha256"], "Actual label identity differs")
            labels = pd.read_csv(io.BytesIO(raw), usecols=["Label"])["Label"].to_numpy()
            need(len(labels) == metadata[series]["n"] and np.isin(labels, [0, 1]).all()
                 and 0 < labels.sum() == metadata[series]["positive_points"] < len(labels), "Actual label metadata differs")
    for model in models:
        with zipfile.ZipFile(root / f"cache/{model}.score-range.zip") as archive:
            need(len(archive.namelist()) == len(set(archive.namelist())), "Ambiguous score member")
            for series in wanted:
                raw = archive.read(f"scores/{series}.npy")
                need(hashlib.sha256(raw).hexdigest() == score_hashes[series, model], "Actual score identity differs")
                values = np.load(io.BytesIO(raw), allow_pickle=False)
                need(values.ndim == 1 and len(values) == metadata[series]["n"] and np.isfinite(values).all(), "Invalid actual score vector")
    return result


def audit_run(path, *, root=None):
    root, path = Path(root or ROOT), Path(path)
    protocol = json.loads((path / "protocol.json").read_text())
    inputs = json.loads((path / "inputs.json").read_text())
    env = json.loads((path / "environment.json").read_text())
    summary = json.loads((path / "summary.json").read_text())
    need(summary["status"] == "PASS" and not summary["violations"], "Producer did not pass")
    need(sha(path / "protocol.json") == env["protocol_sha256"] == summary["protocol_sha256"], "Protocol binding differs")
    need(sha(path / "inputs.json") == protocol["inputs_sha256"], "Frozen input bytes differ")
    need(sha(path / "measurements.jsonl") == summary["measurements_sha256"], "Raw-result hash differs")
    need(set(protocol["source_sha256"]) == REQUIRED_SOURCES, "Missing measured source binding")
    need(env["source_sha256"] == protocol["source_sha256"], "Environment source binding differs")
    for relative, value in protocol["source_sha256"].items():
        need(sha(root / relative) == value, f"Measured source changed: {relative}")
    need(env["threads"] == 1 and all(p["num_threads"] == 1 for p in env["threadpool_info"]), "Thread contract differs")
    need(set(env["warmup_seconds"]) == set(protocol["method_ids"])
         and all(finite(t) and t >= 0 for t in env["warmup_seconds"].values()), "Warmup coverage differs")
    rows = [json.loads(line) for line in (path / "measurements.jsonl").read_text().splitlines()]
    rebuilt = audit_records(rows, protocol, inputs)
    compare(summary["reconstructed"], rebuilt)
    provenance = validate_inputs_manifest(inputs, protocol, root)
    return {"status": "PASS", "completed_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Independent post-run reconstruction and immutable source-member reconciliation; no kernels rerun.",
            "protocol_sha256": sha(path / "protocol.json"), "inputs_sha256": sha(path / "inputs.json"),
            "measurements_sha256": sha(path / "measurements.jsonl"), "auditor_sha256": sha(Path(__file__)),
            "reconstructed": rebuilt, "data_provenance": provenance,
            "limitations": ["The holdout was previously studied in other experiments; it is held out for this new procedure only.",
                            "Floating-point containment is numerical, not formal outward rounding.",
                            "Retained curve bytes exclude other working arrays; this is not peak memory."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_run(args.run)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "cases": result["reconstructed"]["cases"],
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
