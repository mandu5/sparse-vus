"""Independently reconstruct whole-call model-selection experiment receipts.

This post-run audit evaluates no metric or selection kernel. It reconstructs
selection semantics, work accounting and timing aggregates from raw records,
then reconciles their input identities with the immutable released corpus.
Run after controlled timing ends, because the provenance gate reads archives.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

from advancement_data_gate import validate_advancement_data

ROOT = Path(__file__).resolve().parents[1]
METHODS = (
    "sparse_exact", "dense_direct", "dense_nearest", "fast_vus_exact_pr",
    "fixed250_pr", "certificate_prune", "certificate_no_prune",
)
CERTIFIED = ("certificate_prune", "certificate_no_prune")
EXACT_COMPARATORS = ("dense_direct", "dense_nearest", "fast_vus_exact_pr")
TIE = 1e-10
ORDER_MARGIN = 3e-10
REQUIRED_SOURCES = {
    "experiments/benchmark_selection.py", "experiments/benchmark_advancement.py",
    "experiments/fast_vus_adapter.py", "src/sparse_vus/selection.py",
    "src/sparse_vus/certified.py", "src/sparse_vus/core.py",
    "src/sparse_vus/compiled.py", ".cache/fast_vus/fast_vus.py",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def names(value, allowed, *, nonempty=True):
    require(isinstance(value, list) and value == sorted(set(value)),
            "Selection names must be unique sorted lists")
    require(set(value) <= set(allowed) and (bool(value) or not nonempty),
            "Selection contains absent model or is unexpectedly empty")


def value_map(value, expected):
    require(set(value) == set(expected), "Model-value coverage mismatch")
    require(all(finite_number(v) and -TIE <= v <= 1 + TIE for v in value.values()),
            "Invalid PR value")


def exact_winners(pr):
    best = max(pr.values())
    return sorted(model for model, value in pr.items() if best - value <= TIE)


def compare_tree(actual, expected, location):
    """Check a summary against independently recomputed raw-record statistics."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected),
                f"Summary field coverage differs: {location}")
        for key in expected:
            compare_tree(actual[key], expected[key], f"{location}/{key}")
    elif isinstance(expected, float):
        require(finite_number(actual) and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12),
                f"Summary numeric mismatch: {location}")
    else:
        require(type(actual) is type(expected) and actual == expected,
                f"Summary value mismatch: {location}")


def audit_records(rows, protocol):
    """Pure receipt checks; independent of benchmark helpers or source archives."""
    require(protocol["models_per_case"] == 3 and protocol["repetitions"] == 3,
            "Unexpected model/repetition contract")
    require(protocol["atol"] == .01 and protocol["exact_parity_tolerance"] == 1e-11
            and protocol["float64_containment_tolerance"] == TIE,
            "Unexpected numerical contract")
    require(len(rows) == protocol["cases"] and bool(rows), "Incomplete selection coverage")
    keys = [(r["series"], r["max_buffer"]) for r in rows]
    require(len(keys) == len(set(keys)), "Duplicate selection case")
    require(keys == sorted(keys), "Selection order differs from frozen order")
    selection_hash = hashlib.sha256(json.dumps(keys, separators=(",", ":")).encode()).hexdigest()
    require(selection_hash == protocol["selection_sha256"], "Selection hash mismatch")
    max_parity = max_enclosure_slack = 0.0
    expanded = []
    for row in rows:
        width = row["max_buffer"]
        require(type(width) is int and width in (30, 100, 300), "Unexpected buffer width")
        models = sorted(row["score_sha256"])
        require(len(models) == 3 and all(isinstance(m, str) for m in models), "Model coverage mismatch")
        for field in ("values", "seconds", "median_seconds"):
            require(set(row[field]) == set(METHODS), f"Method coverage mismatch: {field}")
        for method in METHODS:
            calls = row["seconds"][method]
            require(len(calls) == 3 and all(finite_number(v) and v > 0 for v in calls),
                    "Invalid selection timing")
            require(finite_number(row["median_seconds"][method])
                    and statistics.median(calls) == row["median_seconds"][method],
                    "Forged selection median")
        reference = row["values"]["sparse_exact"]
        value_map(reference["pr"], models)
        target = exact_winners(reference["pr"])
        require(reference["selected"] == target, "Sparse reference selection contradicts its PR values")
        for method in ("sparse_exact", *EXACT_COMPARATORS, "fixed250_pr"):
            result = row["values"][method]
            value_map(result["pr"], models)
            names(result["selected"], models)
            require(result["selected"] == exact_winners(result["pr"]),
                    f"Selection contradicts own PR values: {method}")
            if method != "fixed250_pr":
                require(result["selected"] == target, f"Wrong exact selection: {method}")
                error = max(abs(result["pr"][m] - reference["pr"][m]) for m in models)
                max_parity = max(max_parity, error)
                require(error <= protocol["exact_parity_tolerance"], f"Exact PR mismatch: {method}")
        wrong250 = row["values"]["fixed250_pr"]["selected"] != target
        require(type(row["fixed250_wrong_selection"]) is bool and row["fixed250_wrong_selection"] == wrong250,
                "Incorrect fixed250 disagreement flag")
        require(type(row["exact_unique_winner"]) is bool and row["exact_unique_winner"] == (len(target) == 1),
                "Incorrect exact unique-winner flag")
        for method in CERTIFIED:
            result = row["values"][method]
            names(result["selected"], models)
            names(result["candidates"], models)
            names(result["pruned"], models, nonempty=False)
            require(result["selected"] == target, f"Wrong certificate selection: {method}")
            require(set(result["bounds"]) == set(models), "Missing initial model bound")
            bounds = result["bounds"]
            for model, pair in bounds.items():
                require(isinstance(pair, list) and len(pair) == 2 and all(finite_number(x) for x in pair),
                        "Nonfinite or invalid selection bound")
                lower, upper = pair
                require(-TIE <= lower <= upper <= 1 + TIE, "Reversed/out-of-range selection bound")
                require((upper - lower) / 2 <= protocol["atol"] + 1e-12,
                        "Initial bound exceeds requested tolerance")
                truth = reference["pr"][model]
                max_enclosure_slack = max(max_enclosure_slack, lower - truth, truth - upper)
                require(lower - TIE <= truth <= upper + TIE, "Selection bound excludes exact PR")
            early = [model for model in models
                     if all(bounds[model][0] > bounds[other][1] + ORDER_MARGIN
                            for other in models if other != model)]
            require(len(early) <= 1, "More than one early winner")
            require(type(result["early_winner"]) is bool and result["early_winner"] == bool(early),
                    "Early-winner flag lacks the required separation")
            if early:
                candidates = early
                expected_fallback = []
                require(result["selected"] == early, "Early winner is not selected")
            else:
                highest_lower = max(pair[0] for pair in bounds.values())
                candidates = (models if method == "certificate_no_prune" else
                              [m for m in models if bounds[m][1] >= highest_lower - ORDER_MARGIN])
                expected_fallback = candidates
            require(result["candidates"] == candidates
                    and result["pruned"] == [m for m in models if m not in candidates],
                    "Pruning/candidate policy mismatch")
            value_map(result["exact_pr"], expected_fallback)
            require(type(result["exact_fallback_count"]) is int
                    and result["exact_fallback_count"] == len(expected_fallback),
                    "Hidden or miscounted exact fallback")
            for model, value in result["exact_pr"].items():
                require(abs(value - reference["pr"][model]) <= protocol["exact_parity_tolerance"],
                        "Fallback PR differs from reference")
            if not early:
                require(result["selected"] == exact_winners(result["exact_pr"]),
                        "Fallback winner contradicts fallback PR values")
            require(type(result["certified_evaluations"]) is int
                    and result["certified_evaluations"] == len(models),
                    "Initial certification work count mismatch")
            unique, curves = result["certified_unique_widths"], result["certified_curve_evaluations"]
            require(type(unique) is type(curves) is int
                    and len(models) <= unique <= len(models) * (width + 1) and curves >= unique,
                    "Invalid certification width/curve accounting")
        for field in ("bounds", "certified_evaluations", "certified_unique_widths",
                      "certified_curve_evaluations"):
            require(row["values"][CERTIFIED[0]][field] == row["values"][CERTIFIED[1]][field],
                    "Pruning ablation changed the initial bound computation")
        expanded.extend({
            "series": row["series"], "family": row["family"], "n": row["n"],
            "max_buffer": width, "model": model, "label_sha256": row["label_sha256"],
            "score_sha256": row["score_sha256"][model],
        } for model in models)
    by_width = {}
    for width in sorted({row["max_buffer"] for row in rows}):
        group = [row for row in rows if row["max_buffer"] == width]
        summary = {
            "cases": len(group),
            "exact_unique_winner_cases": sum(row["exact_unique_winner"] for row in group),
            "fixed250_wrong_selections": sum(row["fixed250_wrong_selection"] for row in group),
            "sum_case_median_seconds": {
                method: sum(row["median_seconds"][method] for row in group) for method in METHODS},
        }
        for method in CERTIFIED:
            summary[method] = {
                "early_winners": sum(row["values"][method]["early_winner"] for row in group),
                "exact_fallback_evaluations": sum(row["values"][method]["exact_fallback_count"] for row in group),
                "ratios_by_comparator": {
                    comparator: {
                        "median": float(statistics.median(
                            row["median_seconds"][comparator] / row["median_seconds"][method] for row in group)),
                        "faster_cases": sum(row["median_seconds"][comparator] > row["median_seconds"][method]
                                            for row in group),
                    } for comparator in METHODS if comparator != method},
            }
        by_width[str(width)] = summary
    return {
        "cases": len(rows), "max_exact_pr_error": max_parity,
        "max_enclosure_slack": max_enclosure_slack,
        "by_width": by_width,
    }, expanded


def audit_selection_run(path, *, root=None):
    path, root = Path(path), Path(root or ROOT).resolve()
    protocol_path = path / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    environment = json.loads((path / "environment.json").read_text())
    summary = json.loads((path / "summary.json").read_text())
    raw = (path / "measurements.jsonl").read_bytes()
    require(summary["status"] == "PASS" and summary["violations"] == [], "Selection run did not pass")
    require(sha256 := hashlib.sha256(raw).hexdigest(), "Missing raw hash")
    require(summary["measurements_sha256"] == sha256, "Selection measurement hash mismatch")
    require(environment["protocol_sha256"] == digest(protocol_path), "Selection protocol binding mismatch")
    require(set(environment["source_sha256"]) == REQUIRED_SOURCES, "Selection source coverage mismatch")
    for relative, expected in environment["source_sha256"].items():
        source = (root / relative).resolve()
        require(source.is_relative_to(root) and source.is_file(), "Invalid measured source path")
        require(digest(source) == expected, f"Selection measured source changed: {relative}")
    require(environment["threads"] == 1
            and all(pool["num_threads"] == 1 for pool in environment["threadpool_info"]),
            "Selection timing thread contract differs")
    require(set(environment["warmup_seconds"]) == set(METHODS)
            and all(finite_number(v) and v >= 0 for v in environment["warmup_seconds"].values()),
            "Selection warmup accounting invalid")
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    reconstructed, expanded = audit_records(rows, protocol)
    require(summary["cases"] == reconstructed["cases"], "Selection summary count mismatch")
    compare_tree(summary["by_width"], reconstructed["by_width"], "by_width")
    provenance = validate_advancement_data(expanded, mode="certified", root=root)
    require(provenance["status"] == "PASS", "Selection source-data gate did not pass")
    return {
        "status": "PASS", "completed_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Independent post-run receipt reconstruction, no metric kernels rerun.",
        "measurements_sha256": sha256, "protocol_sha256": digest(protocol_path),
        "environment_sha256": digest(path / "environment.json"),
        "producer_summary_sha256": digest(path / "summary.json"),
        "auditor_sha256": digest(Path(__file__)), "source_sha256": environment["source_sha256"],
        "reconstructed": reconstructed, "data_provenance": provenance,
        "checks": ["hash/protocol/source binding", "mode-specific released-data identity",
                   "finite outputs and exact-model coverage", "all exact parity and tie selections",
                   "3e-10 early/pruning policy", "1e-10 tie retention", "all fallback work",
                   "same initial bounds in ablation", "positive finite times and medians",
                   "all summary counts, sums and comparator ratios"],
        "limitations": ["Input/kernel timing itself is not rerun.",
                        "Float64 enclosure checks are empirical, not outward-rounded certification.",
                        "Bound counters are validated for consistency, not reconstructed from an unrecorded per-model call trace."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_selection_run(args.run)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
