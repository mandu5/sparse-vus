"""Padding sensitivity and family-stratified audit; no new timing claims.

Run with the benchmark Python environment:
  python experiments/ranking_robustness.py --freeze
  python experiments/ranking_robustness.py --self-test
  python experiments/ranking_robustness.py --run
  python experiments/ranking_robustness.py --verify

The two transformations are fixed before evaluation. Source score archives are
never changed. Neither a sensitivity analysis nor reuse of released scores is
a reproduction of the source paper's model leaderboard.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import itertools
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/robustness"
for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[variable] = "1"
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / "cache/numba-public-benchmark"))
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
from sparse_vus import sampled_vus
from sparse_vus.compiled import dense_vus_direct_jit, sparse_vus_jit

CONTEXT = 64
PADDED = ("bolt_base_64", "TimeMoE-200M_64")
VARIANTS = ("released", "first_score_fill64", "common_suffix64")
TOL = 1e-10
PARITY_TOL = 1e-11
BOOTSTRAPS = 5000
SEED = 2026102001


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def load_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def write_csv(path, rows):
    import csv
    with Path(path).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_input():
    """Verify both locked archives and every selected score member."""
    manifest = json.loads((ROOT / "experiments/data_manifest.json").read_text())
    locks = json.loads((ROOT / "experiments/data_hashes.json").read_text())
    for filename, expected in locks["files"].items():
        if sha(ROOT / "cache" / filename) != expected:
            raise ValueError(f"Input hash mismatch: {filename}")
    selection = json.loads((ROOT / "artifacts/selected_series.json").read_text())
    original = load_rows(ROOT / "artifacts/public_benchmark.jsonl")
    receipt = json.loads((ROOT / "artifacts/public_benchmark_receipt.json").read_text())
    if sha(ROOT / "artifacts/public_benchmark.jsonl") != receipt["records_sha256"]:
        raise ValueError("Original benchmark receipt mismatch")
    labels = {}
    with zipfile.ZipFile(ROOT / "cache/TSB-AD-U.zip") as archive:
        members = {Path(name).stem: name for name in archive.namelist()
                   if name.endswith(".csv")}
        for series in selection["ordered_series"]:
            raw = archive.read(members[series])
            labels[series] = (pd.read_csv(io.BytesIO(raw))["Label"].to_numpy(),
                              hashlib.sha256(raw).hexdigest())
    scores, score_hashes = {}, {}
    for model in manifest["models"]:
        name = model["name"]
        hashes = []
        with zipfile.ZipFile(ROOT / f"cache/{name}.score-range.zip") as archive:
            for member in archive.namelist():
                if member.startswith("scores/") and member.endswith(".npy"):
                    raw = archive.read(member)  # verifies ZIP CRC
                    member_hash = hashlib.sha256(raw).hexdigest()
                    hashes.append((member, member_hash))
                    series = Path(member).stem
                    if series in labels:
                        scores[series, name] = np.load(io.BytesIO(raw), allow_pickle=False)
                        score_hashes[series, name] = member_hash
        digest = hashlib.sha256(json.dumps(sorted(hashes), separators=(",", ":")).encode()).hexdigest()
        if digest != locks["score_member_manifests"][name]:
            raise ValueError(f"Score member manifest mismatch: {name}")
    models = sorted(m["name"] for m in manifest["models"])
    widths = sorted(set(r["max_buffer"] for r in original))
    expected = set(itertools.product(selection["ordered_series"], models, widths))
    keys = [(r["series"], r["model"], r["max_buffer"]) for r in original]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("Original benchmark coverage mismatch")
    for series, (y, label_hash) in labels.items():
        if not np.isin(y, [0, 1]).all() or not 0 < y.sum() < len(y):
            raise ValueError(f"Invalid labels: {series}")
        for model in models:
            s = scores[series, model]
            if s.ndim != 1 or len(s) != len(y) or not np.isfinite(s).all():
                raise ValueError(f"Invalid scores: {series}, {model}")
        if any(r["label_member_sha256"] != label_hash for r in original if r["series"] == series):
            raise ValueError(f"Original label identity mismatch: {series}")
    return labels, scores, score_hashes, original, models, widths


def source_bindings():
    paths = ["experiments/ranking_robustness.py", "experiments/data_manifest.json",
             "experiments/data_hashes.json", "experiments/protocol.json",
             "src/sparse_vus/core.py", "src/sparse_vus/compiled.py",
             "artifacts/public_benchmark.jsonl", "artifacts/public_benchmark_receipt.json",
             "artifacts/selected_series.json", "cache/official_metrics.py",
             "cache/score-archive-README.txt"]
    return {p: sha(ROOT / p) for p in paths}


def transform(y, score, model, variant):
    if variant == "released":
        return y, score
    if len(score) <= CONTEXT:
        raise ValueError("Context exceeds vector length")
    if variant == "common_suffix64":
        return y[CONTEXT:], score[CONTEXT:]
    if variant == "first_score_fill64":
        modified = score.copy()
        if model in PADDED:
            if not np.all(score[:CONTEXT] == 0):
                raise ValueError("Documented zero prefix absent")
            modified[:CONTEXT] = score[CONTEXT]
        return y, modified
    raise ValueError(variant)


def freeze():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "protocol.json").exists():
        raise FileExistsError("Frozen protocol exists; do not overwrite")
    labels, scores, hashes, original, models, widths = read_input()
    inventory = []
    for series in sorted(labels):
        y, label_hash = labels[series]
        item = {"series": series, "n": len(y), "positive_points": int(y.sum()),
                "removed_prefix_positives": int(y[:CONTEXT].sum()),
                "suffix_positive_points": int(y[CONTEXT:].sum()),
                "suffix_has_both_classes": bool(0 < y[CONTEXT:].sum() < len(y) - CONTEXT),
                "label_sha256": label_hash, "scores": {}}
        for model in models:
            s = scores[series, model]
            nonzero = np.flatnonzero(s != 0)
            item["scores"][model] = {"member_sha256": hashes[series, model],
                                    "leading_zeros": int(nonzero[0]) if len(nonzero) else len(s),
                                    "first_available_score": float(s[CONTEXT]),
                                    "suffix_zeros": int(np.count_nonzero(s[CONTEXT:] == 0))}
            if model in PADDED and item["scores"][model]["leading_zeros"] != CONTEXT:
                raise ValueError("Fixed context-64 padding assumption failed")
        inventory.append(item)
    protocol = {
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "After inspecting original results and input zero prefixes; before transformed metric evaluation. Post-publication sensitivity, not preregistration.",
        "models": models, "max_buffer": widths, "context": CONTEXT,
        "variants": {
            "released": "Reuse hash-bound complete original benchmark outputs.",
            "first_score_fill64": "For the two README-documented zero-padded models replace score[:64] with score[64]; retain full labels and TimesFM scores.",
            "common_suffix64": "Evaluate labels[64:] and score[64:] for all three models on identical positions."
        },
        "selection": "Every original series; explicitly log variant exclusions when transformed labels lack either class. No label-dependent crop start.",
        "end_point_caveat": "Suffix removal changes prevalence, ranking thresholds, and the left-boundary buffer geometry; it is a sensitivity analysis, not an invariant metric.",
        "ranking": {"pairs": "All three unordered model pairs, both widths and both metrics.",
                    "strict_tie_tolerance": TOL, "material_margin_grid": [1e-4, 1e-3, 1e-2],
                    "overlap": "Same series, width, metric and unordered pair versus released. Persistent means strict reversal in both."},
        "validation": "All newly computed exact outputs checked against dense direct-ramp compiled implementation at 1e-11. Seeded small fixtures additionally checked with pinned upstream exact and sampled code.",
        "statistics": {"seed": SEED, "resamples": BOOTSTRAPS,
                       "units": "Within a family, resample whole series retaining all models/widths/pairs. Across families, report equal-family means and family-cluster bootstrap.",
                       "scope": "Descriptive fixed-corpus intervals, no population-generalization or multiple-testing significance claim."},
        "timing": "No new performance measurements. Reuse original times only for absolute evaluator-cost and family-stratified summaries; inference and pipeline times are UNKNOWN.",
        "source_sha256": source_bindings()
    }
    json_write(OUT / "inventory.json", inventory)
    protocol["inventory_sha256"] = sha(OUT / "inventory.json")
    json_write(OUT / "protocol.json", protocol)
    print(json.dumps({"inventory_series": len(inventory), "models": models,
                      "suffix_exclusions": sum(not x["suffix_has_both_classes"] for x in inventory),
                      "series_with_removed_positives": sum(x["removed_prefix_positives"] > 0 for x in inventory),
                      "protocol_sha256": sha(OUT / "protocol.json")}), flush=True)


def verify_bindings(protocol):
    for path, expected in protocol["source_sha256"].items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"Frozen source changed: {path}")
    if sha(OUT / "inventory.json") != protocol["inventory_sha256"]:
        raise ValueError("Frozen inventory changed")


def sign(value, tolerance=TOL):
    return 0 if abs(value) <= tolerance else (1 if value > 0 else -1)


def pair_rows(rows):
    groups = defaultdict(dict)
    for row in rows:
        groups[row["variant"], row["series"], row["max_buffer"]][row["model"]] = row
    pairs, tops = [], []
    for (variant, series, width), models in sorted(groups.items()):
        if len(models) != 3:
            raise ValueError("Ranking group is incomplete")
        family = next(iter(models.values()))["family"]
        for index, metric in enumerate(("ROC", "PR")):
            for a, b in itertools.combinations(sorted(models), 2):
                de = models[a]["exact"][index] - models[b]["exact"][index]
                ds = models[a]["sampled250"][index] - models[b]["sampled250"][index]
                pairs.append({"variant": variant, "series": series, "family": family,
                              "max_buffer": width, "metric": metric, "model_a": a, "model_b": b,
                              "exact_delta": de, "sampled_delta": ds,
                              "exact_tie": sign(de) == 0, "sampled_tie": sign(ds) == 0,
                              "strict_reversal": sign(de) * sign(ds) == -1,
                              "minimum_margin": min(abs(de), abs(ds))})
            exact = {m: r["exact"][index] for m, r in models.items()}
            sampled = {m: r["sampled250"][index] for m, r in models.items()}
            te = sorted(m for m, value in exact.items() if max(exact.values()) - value <= TOL)
            ts = sorted(m for m, value in sampled.items() if max(sampled.values()) - value <= TOL)
            tops.append({"variant": variant, "series": series, "family": family,
                         "max_buffer": width, "metric": metric,
                         "exact_top_models": te, "sampled_top_models": ts,
                         "unique_top_change": len(te) == len(ts) == 1 and te != ts})
    return pairs, tops


def mean_ci(values, rng):
    values = np.asarray(values, dtype=float)
    means = np.mean(rng.choice(values, size=(BOOTSTRAPS, len(values)), replace=True), axis=1)
    return {"mean": float(values.mean()), "ci95": np.quantile(means, [.025, .975]).tolist(),
            "clusters": len(values)}


def describe(rows, pairs, tops):
    """Independent statistics implementation, separate from analyze_results.py."""
    rng = np.random.default_rng(SEED)
    summaries, families = {}, []
    for variant in VARIANTS:
        vr = [r for r in rows if r["variant"] == variant]
        summaries[variant] = {"series": len(set(r["series"] for r in vr)),
                              "evaluations": len(vr), "metrics": {}}
        for index, metric in enumerate(("ROC", "PR")):
            pp = [p for p in pairs if p["variant"] == variant and p["metric"] == metric]
            tt = [t for t in tops if t["variant"] == variant and t["metric"] == metric]
            reversals = [p for p in pp if p["strict_reversal"]]
            errors = np.asarray([r["sampled250"][index] - r["exact"][index] for r in vr])
            summary = {
                "pairs": len(pp), "strict_reversals": len(reversals),
                "affected_series": len(set(p["series"] for p in reversals)),
                "affected_families": sorted(set(p["family"] for p in reversals)),
                "exact_ties": sum(p["exact_tie"] for p in pp),
                "sampled_ties": sum(p["sampled_tie"] for p in pp),
                "unique_top_changes": sum(t["unique_top_change"] for t in tt),
                "top_cases": len(tt), "mean_signed_error": float(errors.mean()),
                "absolute_error_median": float(np.median(np.abs(errors))),
                "absolute_error_p95": float(np.quantile(np.abs(errors), .95)),
                "absolute_error_max": float(np.max(np.abs(errors))),
                "material_reversals": {str(m): sum(p["minimum_margin"] >= m for p in reversals)
                                       for m in (1e-4, 1e-3, 1e-2)}
            }
            family_rates = []
            for family in sorted(set(r["family"] for r in vr)):
                rr = [r for r in vr if r["family"] == family]
                fp = [p for p in pp if p["family"] == family]
                ft = [t for t in tt if t["family"] == family]
                series_names = sorted(set(r["series"] for r in rr))
                per_series_rates, per_series_error = [], []
                for series in series_names:
                    sp = [p for p in fp if p["series"] == series]
                    sr = [r for r in rr if r["series"] == series]
                    per_series_rates.append(np.mean([p["strict_reversal"] for p in sp]))
                    per_series_error.append(np.mean([r["sampled250"][index] - r["exact"][index] for r in sr]))
                rate, error = mean_ci(per_series_rates, rng), mean_ci(per_series_error, rng)
                family_rates.append(rate["mean"])
                families.append({"variant": variant, "metric": metric, "family": family,
                                 "series": len(series_names), "pairs": len(fp),
                                 "strict_reversals": sum(p["strict_reversal"] for p in fp),
                                 "affected_series": len(set(p["series"] for p in fp if p["strict_reversal"])),
                                 "unique_top_changes": sum(t["unique_top_change"] for t in ft),
                                 "reversal_rate": rate["mean"], "reversal_ci_low": rate["ci95"][0],
                                 "reversal_ci_high": rate["ci95"][1],
                                 "mean_signed_error": error["mean"],
                                 "error_ci_low": error["ci95"][0], "error_ci_high": error["ci95"][1]})
            summary["equal_family_reversal_rate"] = mean_ci(family_rates, rng)
            summaries[variant]["metrics"][metric] = summary
    lookup = {(p["variant"], p["series"], p["max_buffer"], p["metric"], p["model_a"], p["model_b"]): p
              for p in pairs}
    overlap = {}
    for variant in VARIANTS[1:]:
        overlap[variant] = {}
        for metric in ("ROC", "PR"):
            eligible = [p for p in pairs if p["variant"] == variant and p["metric"] == metric]
            transitions = defaultdict(int)
            for p in eligible:
                old = lookup["released", p["series"], p["max_buffer"], metric, p["model_a"], p["model_b"]]
                key = ("persistent" if p["strict_reversal"] else "lost") if old["strict_reversal"] else (
                    "new" if p["strict_reversal"] else "neither")
                transitions[key] += 1
                if key == "persistent":
                    transitions["persistent_same_direction"] += sign(p["exact_delta"]) == sign(old["exact_delta"])
            overlap[variant][metric] = dict(transitions)
    return {"variants": summaries, "reversal_overlap": overlap,
            "scope": "Post-publication sensitivity on the complete fixed corpus. Bootstrap intervals are descriptive, retaining series clusters within families; macro intervals weight source families equally."}, families


def timing_context(original):
    rng = np.random.default_rng(SEED + 1)
    families = []
    savings, dense, sparse = [], [], []
    for row in original:
        d = min(v for k, v in row["median_seconds"].items() if k.startswith("dense"))
        s = row["median_seconds"]["sparse_numba"]
        dense.append(d); sparse.append(s); savings.append(d - s)
    for family in sorted(set(r["family"] for r in original)):
        rr = [r for r in original if r["family"] == family]
        series = sorted(set(r["series"] for r in rr))
        logs = [np.mean([np.log(r["speedup_vs_fastest_dense"]) for r in rr if r["series"] == name])
                for name in series]
        ci = mean_ci(logs, rng)
        ratios = [r["speedup_vs_fastest_dense"] for r in rr]
        families.append({"family": family, "series": len(series), "evaluations": len(rr),
                         "geometric_mean_speedup": float(np.exp(ci["mean"])),
                         "series_bootstrap95": np.exp(ci["ci95"]).tolist(),
                         "slower_or_equal": sum(r <= 1 for r in ratios),
                         "material_slowdowns_le_1_over_1p1": sum(r <= 1 / 1.1 for r in ratios),
                         "minimum_speedup": min(ratios)})
    ratio = sum(dense) / sum(sparse)
    return {
        "source": "Original public_benchmark.jsonl medians, not newly timed.",
        "summed_evaluator_median_seconds": {"fastest_dense_per_case": sum(dense), "sparse": sum(sparse),
                                           "saved": sum(savings), "ratio": ratio},
        "per_evaluation_saved_seconds_quantiles": dict(zip(["min", "p25", "median", "p75", "max"],
                                                          np.quantile(savings, [0, .25, .5, .75, 1]).tolist())),
        "slowdown_cases": sum(x < 0 for x in savings),
        "family_summaries": families,
        "hypothetical_amdahl_speedup": {str(f): 1 / (1 - f + f / ratio) for f in [.01, .1, .5, 1]},
        "inference_time": "UNKNOWN: released scores reused; no detector training/inference measured.",
        "caveat": "Summing isolated per-case medians is a descriptive evaluator budget, not an observed pipeline wall time. Amdahl scenarios are hypothetical metric fractions."
    }


def self_test():
    spec = importlib.util.spec_from_file_location("pinned_official", ROOT / "cache/official_metrics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reference = module.metricor()
    rng = np.random.default_rng(SEED)
    max_exact_error, max_sample_error = 0., 0.
    for case in range(24):
        n = 80 + case
        y = (rng.random(n) < .15).astype(np.int8)
        y[64], y[65] = 1, 0
        score = rng.random(n)
        score[:64] = 0
        for variant in VARIANTS[1:]:
            yy, ss = transform(y, score, "bolt_base_64", variant)
            for width in (0, 10, 30):
                exact = np.asarray(sparse_vus_jit(yy, ss, width))
                dense = np.asarray(dense_vus_direct_jit(yy, ss, width))
                official = np.asarray(reference.RangeAUC_volume_opt(yy, ss, width, thre=len(yy))[-2:])
                approximate = np.asarray(sampled_vus(yy, ss, width))
                offsample = np.asarray(reference.RangeAUC_volume_opt(yy, ss, width, thre=250)[-2:])
                max_exact_error = max(max_exact_error, float(np.max(np.abs(exact - official))),
                                      float(np.max(np.abs(exact - dense))))
                max_sample_error = max(max_sample_error, float(np.max(np.abs(approximate - offsample))))
                if not np.isfinite([*exact, *dense, *official, *approximate, *offsample]).all():
                    raise AssertionError("Nonfinite validation result")
        assert np.all(score[:64] == 0), "Transformation mutated source"
    assert sign(0.) == sign(TOL) == 0 and sign(-1.) == -1 and sign(1.) == 1
    assert max(max_exact_error, max_sample_error) <= PARITY_TOL
    result = {"status": "PASS", "seed": SEED, "fixture_cases": 24,
              "transformed_metric_checks": 24 * 2 * 3,
              "max_exact_error": max_exact_error, "max_sample_error": max_sample_error}
    OUT.mkdir(parents=True, exist_ok=True)
    json_write(OUT / "self_test.json", result)
    print(json.dumps(result), flush=True)


def run():
    protocol = json.loads((OUT / "protocol.json").read_text())
    verify_bindings(protocol)
    if (OUT / "records.jsonl").exists():
        raise FileExistsError("Result records exist; preserve them instead of overwriting")
    self_test()
    labels, scores, hashes, original, models, widths = read_input()
    originals = {(r["series"], r["model"], r["max_buffer"]): r for r in original}
    rows, exclusions = [], []
    started = datetime.now(timezone.utc).isoformat()
    with (OUT / "records.jsonl").open("w") as stream:
        for number, series in enumerate(sorted(labels), 1):
            y, label_hash = labels[series]
            for variant in VARIANTS:
                yy, _ = transform(y, scores[series, models[0]], models[0], variant)
                if not 0 < yy.sum() < len(yy):
                    exclusions.append({"series": series, "variant": variant,
                                       "reason": "Transformed labels lack both binary classes",
                                       "n": len(yy), "positive_points": int(yy.sum())})
                    continue
                for model in models:
                    yy, ss = transform(y, scores[series, model], model, variant)
                    for width in widths:
                        old = originals[series, model, width]
                        reuse = variant == "released" or (variant == "first_score_fill64" and model not in PADDED)
                        if reuse:
                            exact, approximate = old["exact"], old["sampled250"]
                            error = float(old["max_parity_error"])
                        else:
                            exact = np.asarray(sparse_vus_jit(yy, ss, width))
                            dense = np.asarray(dense_vus_direct_jit(yy, ss, width))
                            approximate = np.asarray(sampled_vus(yy, ss, width))
                            error = float(np.max(np.abs(exact - dense)))
                        if error > PARITY_TOL or not np.isfinite([*exact, *approximate]).all():
                            raise ValueError(f"Metric validation failed: {series}, {model}, {variant}, {width}")
                        row = {"series": series, "family": old["family"], "model": model,
                               "variant": variant, "max_buffer": width,
                               "original_n": len(y), "n": len(yy), "positive_points": int(yy.sum()),
                               "removed_prefix_positives": int(y[:CONTEXT].sum()) if variant == "common_suffix64" else 0,
                               "exact": [float(x) for x in exact], "sampled250": [float(x) for x in approximate],
                               "exact_dense_error": error, "reused_original_result": reuse,
                               "source_score_member_sha256": hashes[series, model],
                               "label_member_sha256": label_hash}
                        rows.append(row)
                        stream.write(json.dumps(row, allow_nan=False) + "\n")
                        stream.flush()
            if number % 25 == 0:
                print(json.dumps({"completed_series": number, "total_series": len(labels),
                                  "records": len(rows)}), flush=True)
    json_write(OUT / "exclusions.json", exclusions)
    pairs, tops = pair_rows(rows)
    summary, families = describe(rows, pairs, tops)
    json_write(OUT / "summary.json", summary)
    json_write(OUT / "top_models.json", tops)
    write_csv(OUT / "ranking_pairs.csv", pairs)
    write_csv(OUT / "family_effects.csv", families)
    json_write(OUT / "timing_context.json", timing_context(original))
    verify_bindings(protocol)
    json_write(OUT / "receipt.json", {
        "status": "COMPLETE", "started_utc": started,
        "completed_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "executable": sys.executable, "numpy": np.__version__, "records": len(rows),
        "max_exact_dense_error": max(r["exact_dense_error"] for r in rows),
        "protocol_sha256": sha(OUT / "protocol.json"),
        "output_sha256": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "receipt.json"}
    })
    print(json.dumps(summary, indent=2), flush=True)


def verify():
    protocol = json.loads((OUT / "protocol.json").read_text())
    verify_bindings(protocol)
    receipt = json.loads((OUT / "receipt.json").read_text())
    for filename, expected in receipt["output_sha256"].items():
        if sha(OUT / filename) != expected:
            raise ValueError(f"Output hash mismatch: {filename}")
    rows = load_rows(OUT / "records.jsonl")
    exclusions = json.loads((OUT / "exclusions.json").read_text())
    inventory = json.loads((OUT / "inventory.json").read_text())
    excluded = {(r["variant"], r["series"]) for r in exclusions}
    expected = {(v, r["series"], m, w) for v in VARIANTS for r in inventory
                for m in protocol["models"] for w in protocol["max_buffer"]
                if (v, r["series"]) not in excluded}
    keys = [(r["variant"], r["series"], r["model"], r["max_buffer"]) for r in rows]
    if set(keys) != expected or len(keys) != len(expected):
        raise ValueError("Transformed coverage mismatch")
    if receipt["records"] != len(rows) or max(r["exact_dense_error"] for r in rows) > PARITY_TOL:
        raise ValueError("Receipt/parity mismatch")
    for r in rows:
        if not np.isfinite([*r["exact"], *r["sampled250"], r["exact_dense_error"]]).all():
            raise ValueError("Nonfinite record")
    pairs, tops = pair_rows(rows)
    summary, _ = describe(rows, pairs, tops)
    if summary != json.loads((OUT / "summary.json").read_text()):
        raise ValueError("Independent reconstruction of summary failed")
    released = summary["variants"]["released"]["metrics"]
    old = json.loads((ROOT / "artifacts/analysis_summary.json").read_text())["metrics"]
    for metric in ("ROC", "PR"):
        for new_key, old_key in [("strict_reversals", "strict_reversals"),
                                 ("affected_series", "affected_unique_series"),
                                 ("unique_top_changes", "unique_top_model_changes")]:
            if released[metric][new_key] != old[metric][old_key]:
                raise ValueError(f"Original analysis disagreement: {metric}, {new_key}")
    print(json.dumps({"status": "PASS", "records": len(rows), "pairs": len(pairs),
                      "exclusions": len(exclusions), "summary_recomputed": True,
                      "original_analysis_reproduced": True,
                      "max_exact_dense_error": receipt["max_exact_dense_error"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    options = parser.parse_args()
    if options.freeze:
        freeze()
    elif options.self_test:
        self_test()
    elif options.run:
        run()
    else:
        verify()
