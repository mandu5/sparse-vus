"""Prospectively frozen paired experiment for PR-only exact model selection.

Freeze uses only released metadata/source hashes. Execution requires the exact
frozen protocol hash; no held-out outcome is loaded by the freeze operation.
The partition is previously studied data, not an unseen external dataset.
"""
from __future__ import annotations

import os
for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_key] = "1"

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics
import sys
import time

from advancement_data_gate import released_metadata

ROOT = Path(__file__).resolve().parents[1]
EXACT = ("sparse_pr", "dense_pr_direct", "sparse_both", "dense_nearest_both", "klein_pr", "benchopt_both", "radix_pr", "radix_both", "dense_pr_direct_radix", "dense_pr_nearest_radix")
METHODS = (*EXACT, "v02_race", "fast_race", "fast_exact_completion", "fast_race_radix")
SOURCES = (
    "experiments/benchmark_pr_engine.py", "experiments/benchmark_advancement.py",
    "experiments/advancement_data_gate.py", "experiments/fast_vus_adapter.py",
    "experiments/benchopt_vus_adapter.py", "src/sparse_vus/pr_compiled.py",
    "src/sparse_vus/fast_racing.py", "src/sparse_vus/racing.py",
    "src/sparse_vus/certified.py", "src/sparse_vus/selection.py",
    "src/sparse_vus/core.py", "src/sparse_vus/compiled.py",
    "src/sparse_vus/radix.py", "src/sparse_vus/dense_radix.py",
    ".cache/fast_vus/fast_vus.py", ".cache/benchopt_vus/metrics.py",
)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def source_hashes(root=ROOT):
    return {name: digest(root / name) for name in SOURCES}


def freeze(output, split, *, adaptive_fraction=.125, memory_bytes=8 * 1024 * 1024,
           include_full_budget=False, root=ROOT):
    if split not in ("development", "holdout"):
        raise ValueError("Unknown split")
    if include_full_budget and split != "development":
        raise ValueError("The full-budget variant is development only")
    if not math.isfinite(adaptive_fraction) or not 0 < adaptive_fraction <= 1:
        raise ValueError("adaptive_fraction must be finite in (0, 1]")
    if type(memory_bytes) is not int or memory_bytes < 0:
        raise ValueError("memory_bytes must be a nonnegative integer")
    metadata, models, score_hashes, development, _, _ = released_metadata(root)
    selected = sorted(development if split == "development" else set(metadata) - set(development))
    if len(selected) != (42 if split == "development" else 308):
        raise ValueError("Unexpected split coverage")
    inputs = [{"series": series, "family": metadata[series]["family"],
               "n": metadata[series]["n"], "max_buffer": width,
               "label_sha256": metadata[series]["label_sha256"],
               "score_sha256": {m: score_hashes[series, m] for m in models}}
              for width in (30, 100, 300) for series in selected]
    hashes = source_hashes(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "inputs.json", inputs)
    protocol = {
        "version": 3, "created_utc": datetime.now(timezone.utc).isoformat(),
        "split": split, "cases": len(inputs), "models": models,
        "families": sorted({r["family"] for r in inputs}),
        "widths": [30, 100, 300], "primary_width": 30, "secondary_width": 100,
        "stress_width": 300, "primary_widths": [30, 100],
        "task_order": "width_then_series",
        "task_order_reason": "Complete the primary L=30 block before L=100 and stress L=300; selected series are sorted within each block. All 924 holdout tasks remain planned. No outcome-dependent early stopping or omission; seeded method randomization remains within every case.",
        "primary_widths_meaning": "Combined primary and secondary descriptive report; the decision test uses only L=30.",
        "repetitions": 3, "seed": 2026102101,
        "method_ids": [*METHODS] + (["fast_full_budget"] if include_full_budget else []),
        "adaptive_fraction": adaptive_fraction, "memory_bytes_per_model": memory_bytes,
        "include_full_budget": include_full_budget,
        "tie_atol": 1e-10, "order_margin": 3e-10,
        "containment_tolerance": 1e-10, "exact_parity_tolerance": 1e-11,
        "bootstrap": {"unit": "family", "repetitions": 2000, "seed": 2026102102,
                      "confidence": .95, "references": ["fast_race", "sparse_pr", "radix_pr", "fast_race_radix"]},
        "primary_decision": "All semantic checks pass; at L=30 fast_race has both geomean and aggregate-ratio lower 95% family-bootstrap bounds above 1 against each of sparse_pr, dense_pr_direct, and radix_pr. This narrow decision is not broad or global SOTA acceptance.",
        "radix_primary_decision": "All semantic checks pass; at L=30 radix_pr has both geomean and aggregate-ratio lower 95% family-bootstrap bounds above 1 against each of sparse_pr, dense_pr_direct, dense_nearest_both, dense_pr_direct_radix, and dense_pr_nearest_radix. External Klein/Benchopt comparisons are descriptive; no global SOTA claim.",
        "radix_racing_decision": "All semantic checks pass; at L=30 fast_race_radix has both geomean and aggregate-ratio lower 95% family-bootstrap bounds above 1 against each of sparse_pr, dense_pr_direct, radix_pr, dense_pr_direct_radix, and dense_pr_nearest_radix. This is separate from the exact radix hypothesis.",
        "uncertainty_scope": "Paired whole-call case medians; resample all observed family clusters with replacement and retain every series/width condition within each sampled cluster. CIs describe between-family/case variation, not uncertainty from three timing repetitions. Other comparator CIs are descriptive and unadjusted. Report within-case max/min timing spread separately.",
        "history": "Development is the previous metadata-selected 42-series partition. The 308-series complement was previously studied in exact-metric experiments; it is prospectively held out only from this new policy-development run, within the same 23 source families. This is not retrospective preregistration of earlier studies or an unseen-domain test.",
        "preformal_amendment": "Version 2 adds radix_pr, radix_both, and fast_race_radix before any formal development or holdout measurements. A disclosed exploratory probe used only the six largest-n series among the existing 42 development series, all three models, L=30, three randomized repeats. It reported 18/18 wins, median 2.654x and total 1.16806s to 0.420764s against comparison-sort PR exact. Selection for large n limits that evidence; these pilot timings are not pooled into formal results. The 308-series policy holdout was not used by the probe.",
        "preholdout_amendment": "Version 3 follows the completed and independently audited 126-case v2 development experiment, whose radix exact primary decision passed and racing decision failed. Exact radix is the main hypothesis; adaptive fraction 0.125 and memory budget are unchanged. Add parameter-free direct/nearest dense radix PR-only controls to isolate generic radix preparation and PR-only work from sparse support. Strengthen the radix exact and radix racing intersections to include both controls. Change case order prospectively to width then series. No held-out outcomes were inspected before this amendment; all new timings are paired within this v3 run, without pooling v2 timings. Historical v2 data and its exact original auditor remain preserved under source-v2.",
        "selection": "Unchanged released labels and all three released score vectors, including documented leading zero padding. Complete input identities are frozen before these new outcomes.",
        "timing": "Three serial repetitions in independent seeded random method order per task; one thread, warm JIT. Each timed complete three-model selection includes validation, sorting/preparation, all metric/controller work, and construction of the API result. Input loading and conversion of API results to JSON receipts are outside timing. No cross-run timing substitution.",
        "comparators": "Sparse and direct-dense PR-only compiled exact controls, Klein actual PR-only code, prior paired sparse/nearest-dense compiled code, Benchopt actual paired ROC+PR code, previous width racer, new racer, zero-adaptation exact-completion ablation, exact radix PR/paired variants, radix-prepared racer, and matched direct/nearest dense radix PR-only controls. All exhaustive methods use all distinct score thresholds and widths 0..L. Benchopt and the paired controls perform extra ROC work; PR-only controls isolate that confound. Sparse radix variants retain their metric kernels and change preparation; matched dense radix controls include global radix preparation and full-array metric work.",
        "excluded_external": "DTAIAnomaly is excluded from this full 924-task main experiment based on the prior 10-second per-call censor and quadratic runtime. Its bounded external-supplement appendix is separate; those older/censored timings are not fused into these paired ratios. This experiment does not close all possible comparators or establish global SOTA.",
        "reporting": "All cases, exact ties, all tail regressions, family statistics, geomean and total-cost ratios. Float64 numerical audits are not formal outward-rounded certification. Retained curve bytes are not peak memory. Detector inference and input I/O are excluded.",
        "inputs_sha256": digest(output / "inputs.json"), "source_sha256": hashes,
    }
    write_json(output / "protocol.json", protocol)
    return protocol


def validate_frozen(output, expected_hash, split, *, root=ROOT):
    output = Path(output)
    if digest(output / "protocol.json") != expected_hash:
        raise ValueError("Frozen protocol hash differs")
    protocol = json.loads((output / "protocol.json").read_text())
    if protocol["version"] != 3 or protocol["task_order"] != "width_then_series":
        raise ValueError("This driver requires the v3 width-first protocol")
    if protocol["split"] != split or digest(output / "inputs.json") != protocol["inputs_sha256"]:
        raise ValueError("Frozen split/input binding differs")
    if source_hashes(root) != protocol["source_sha256"]:
        raise ValueError("Source changed after protocol freeze")
    if any((output / filename).exists() for filename in ("environment.json", "measurements.jsonl", "summary.json")):
        raise ValueError("Run already started; output is append-only and cannot be replayed")
    # Reconcile the metadata-only partition again before touching metric inputs.
    metadata, models, score_hashes, development, _, _ = released_metadata(root)
    selected = sorted(development if split == "development" else set(metadata) - set(development))
    expected_inputs = [{"series": s, "family": metadata[s]["family"], "n": metadata[s]["n"],
                        "max_buffer": w, "label_sha256": metadata[s]["label_sha256"],
                        "score_sha256": {m: score_hashes[s, m] for m in models}}
                       for w in (30, 100, 300) for s in selected]
    inputs = json.loads((output / "inputs.json").read_text())
    if inputs != expected_inputs or protocol["models"] != models or protocol["cases"] != len(inputs):
        raise ValueError("Frozen manifest does not match the immutable partition")
    return protocol, inputs


def exact_selection(labels, scores, width, evaluator):
    values = {model: float(evaluator(labels, score, width)) for model, score in sorted(scores.items())}
    best = max(values.values())
    return {"selected": sorted(m for m, value in values.items() if best - value <= 1e-10), "pr": values}


def make_methods(protocol):
    sys.path.insert(0, str(ROOT / "src"))
    from sparse_vus.pr_compiled import sparse_pr_jit, dense_pr_direct_jit
    from sparse_vus.compiled import sparse_vus_jit, dense_vus_jit
    from sparse_vus.racing import race_pr_models
    from sparse_vus.fast_racing import race_pr_models_fast
    from sparse_vus.radix import sparse_pr_radix_jit, sparse_vus_radix_jit
    from sparse_vus.dense_radix import dense_pr_direct_radix_jit, dense_pr_nearest_radix_jit
    from fast_vus_adapter import fast_vus_pr
    from benchopt_vus_adapter import benchopt_vus
    functions = {
        "sparse_pr": sparse_pr_jit, "dense_pr_direct": dense_pr_direct_jit,
        "sparse_both": lambda y, s, w: sparse_vus_jit(y, s, w)[1],
        "dense_nearest_both": lambda y, s, w: dense_vus_jit(y, s, w)[1],
        "klein_pr": lambda y, s, w: fast_vus_pr(y, s, w, len(s)),
        "benchopt_both": lambda y, s, w: benchopt_vus(y, s, w, max_samples=len(s))[1],
        "radix_pr": sparse_pr_radix_jit,
        "radix_both": lambda y, s, w: sparse_vus_radix_jit(y, s, w)[1],
        "dense_pr_direct_radix": dense_pr_direct_radix_jit,
        "dense_pr_nearest_radix": dense_pr_nearest_radix_jit,
    }
    methods = {name: (lambda y, scores, w, fn=fn: exact_selection(y, scores, w, fn))
               for name, fn in functions.items()}
    methods["v02_race"] = lambda y, s, w: race_pr_models(y, s, w, prune=True)
    fractions = {"fast_race": protocol["adaptive_fraction"], "fast_exact_completion": 0.}
    for name, fraction in fractions.items():
        methods[name] = lambda y, s, w, f=fraction: race_pr_models_fast(
            y, s, w, adaptive_fraction=f, memory_bytes=protocol["memory_bytes_per_model"], prune=True)
    methods["fast_race_radix"] = lambda y, s, w: race_pr_models_fast(
        y, s, w, adaptive_fraction=protocol["adaptive_fraction"],
        memory_bytes=protocol["memory_bytes_per_model"], prune=True, preparation="radix")
    if protocol["include_full_budget"]:
        methods["fast_full_budget"] = lambda y, s, w: race_pr_models_fast(
            y, s, w, adaptive_fraction=1., memory_bytes=protocol["memory_bytes_per_model"], prune=True)
    if list(methods) != protocol["method_ids"]:
        raise ValueError("Method adapter set differs from frozen protocol")
    return methods


def serialize_result(name, result):
    """Only receipt conversion occurs here, outside the measured API call."""
    if name in EXACT:
        return result
    bounds = {model: {"pr_lower": b.pr_lower, "pr_upper": b.pr_upper, "exact": b.exact,
                      "evaluated_widths": list(b.evaluated_widths),
                      "curve_evaluations": b.curve_evaluations,
                      "numerical_guard": b.numerical_guard}
              for model, b in result.bounds.items()}
    full = {model: b.pr_lower for model, b in result.bounds.items() if b.exact}
    out = {"selected": list(result.selected), "candidates": list(result.candidate_models),
           "bounds": bounds, "exact_pr": full, "full_evaluation_count": len(full),
           "early_winner": result.early_winner,
           "total_unique_widths": result.total_unique_widths,
           "total_curve_evaluations": result.total_curve_evaluations}
    if name == "v02_race":
        out.update(pruned=list(result.pruned_models),
                   initial_unique_widths=result.initial_unique_widths,
                   initial_curve_evaluations=result.initial_curve_evaluations,
                   refinement_steps=result.refinement_steps)
        if result.exact_pr != full or result.full_evaluation_count != len(full):
            raise ValueError("Old racer exact-result metadata disagrees")
    else:
        out.update(fallback_models=list(result.fallback_models),
                   retained_curve_bytes=result.retained_curve_bytes,
                   adaptive_curve_evaluations=result.adaptive_curve_evaluations,
                   completion_curve_evaluations=result.completion_curve_evaluations)
    return out


def timed_call(name, method, labels, scores, width):
    start = time.perf_counter()
    result = method(labels, scores, width)
    elapsed = time.perf_counter() - start
    converted = serialize_result(name, result)
    # Releasing the richer racer result must not be charged to the next
    # randomized method when that method assigns its own return value.
    del result
    return converted, elapsed


def ratio_statistics(rows, method, comparator):
    import numpy as np
    numerator = np.array([r["median_seconds"][comparator] for r in rows])
    denominator = np.array([r["median_seconds"][method] for r in rows])
    ratios = numerator / denominator
    family_means = {f: float(np.exp(np.mean(np.log([
        ratio for row, ratio in zip(rows, ratios) if row["family"] == f]))))
                    for f in sorted({r["family"] for r in rows})}
    return {"median": float(np.median(ratios)), "geomean": float(np.exp(np.log(ratios).mean())),
            "aggregate_ratio": float(numerator.sum() / denominator.sum()),
            "faster_cases": int(np.sum(ratios > 1)), "slower_cases": int(np.sum(ratios < 1)),
            "min_ratio": float(ratios.min()), "max_ratio": float(ratios.max()),
            "p05_ratio": float(np.percentile(ratios, 5)),
            "max_slowdown": float((1 / ratios).max()), "p95_slowdown": float(np.percentile(1 / ratios, 95)),
            "slowdowns_over_2x": int(np.sum(1 / ratios > 2)),
            "macro_family_geomean": float(np.exp(np.log(list(family_means.values())).mean())),
            "family_geomeans": family_means}


def bootstrap_summary(rows, methods, specification):
    import numpy as np
    groups = {str(w): [r for r in rows if r["max_buffer"] == w]
              for w in sorted({r["max_buffer"] for r in rows})}
    groups["combined_30_100"] = [r for r in rows if r["max_buffer"] in (30, 100)]
    out = {}
    for key, group in groups.items():
        families = sorted({r["family"] for r in group})
        rng = random.Random(specification["seed"])
        multiplicities = np.zeros((specification["repetitions"], len(families)), dtype=np.int64)
        for b in range(len(multiplicities)):
            for _ in families:
                multiplicities[b, rng.randrange(len(families))] += 1
        membership = np.array([[row["family"] == family for row in group] for family in families], dtype=np.float64)
        counts = membership.sum(axis=1)
        sampled_counts = multiplicities @ counts
        out[key] = {}
        for method in specification["references"]:
            out[key][method] = {}
            den = np.array([r["median_seconds"][method] for r in group])
            sampled_den = multiplicities @ (membership @ den)
            for comparator in methods:
                if comparator == method:
                    continue
                num = np.array([r["median_seconds"][comparator] for r in group])
                logsum = membership @ np.log(num / den)
                geometric = np.exp((multiplicities @ logsum) / sampled_counts)
                aggregate = (multiplicities @ (membership @ num)) / sampled_den
                out[key][method][comparator] = {
                    "families": len(families), "cases": len(group),
                    "geomean_ci95": np.percentile(geometric, [2.5, 97.5]).tolist(),
                    "aggregate_ratio_ci95": np.percentile(aggregate, [2.5, 97.5]).tolist()}
    return out


def summarize(rows, protocol):
    """Producer summaries use NumPy; the separate auditor reconstructs stdlib-only."""
    import numpy as np
    methods, by_width = protocol["method_ids"], {}
    error = slack = 0.
    for row in rows:
        reference = row["values"]["sparse_pr"]["pr"]
        for method in EXACT:
            error = max(error, max(abs(v - reference[m]) for m, v in row["values"][method]["pr"].items()))
        for method in methods[len(EXACT):]:
            for model, b in row["values"][method]["bounds"].items():
                slack = max(slack, b["pr_lower"] - reference[model], reference[model] - b["pr_upper"])
    for width in sorted({r["max_buffer"] for r in rows}):
        group = [r for r in rows if r["max_buffer"] == width]
        out = {"cases": len(group), "sum_case_median_seconds": {
            m: float(np.sum([r["median_seconds"][m] for r in group])) for m in methods}, "methods": {}}
        for method in ["sparse_pr", "radix_pr", *methods[len(EXACT):]]:
            entry = {"by_comparator": {c: ratio_statistics(group, method, c) for c in methods if c != method}}
            if method not in ("sparse_pr", "radix_pr"):
                values = [r["values"][method] for r in group]
                entry.update(total_unique_widths=sum(v["total_unique_widths"] for v in values),
                             total_curve_evaluations=sum(v["total_curve_evaluations"] for v in values),
                             full_model_evaluations=sum(v["full_evaluation_count"] for v in values),
                             median_unique_fraction=float(np.median([v["total_unique_widths"] / (3 * (width + 1)) for v in values])),
                             regressions_vs_sparse_pr=[{"series": r["series"], "family": r["family"],
                                 "ratio": r["median_seconds"]["sparse_pr"] / r["median_seconds"][method]}
                                 for r in group if r["median_seconds"][method] > r["median_seconds"]["sparse_pr"]])
                if method != "v02_race":
                    entry.update(fallback_models=sum(len(v["fallback_models"]) for v in values),
                                 adaptive_curve_evaluations=sum(v["adaptive_curve_evaluations"] for v in values),
                                 completion_curve_evaluations=sum(v["completion_curve_evaluations"] for v in values),
                                 max_retained_curve_bytes=max(v["retained_curve_bytes"] for v in values))
            out["methods"][method] = entry
        by_width[str(width)] = out
    intervals = bootstrap_summary(rows, methods, protocol["bootstrap"])
    def clears_controls(method, controls):
        return "30" in intervals and all(intervals["30"][method][c][metric][0] > 1
                                          for c in controls
                                          for metric in ("geomean_ci95", "aggregate_ratio_ci95"))
    passes = clears_controls("fast_race", ("sparse_pr", "dense_pr_direct", "radix_pr"))
    radix_passes = clears_controls("radix_pr", ("sparse_pr", "dense_pr_direct", "dense_nearest_both", "dense_pr_direct_radix", "dense_pr_nearest_radix"))
    radix_racing_passes = clears_controls("fast_race_radix", ("sparse_pr", "dense_pr_direct", "radix_pr", "dense_pr_direct_radix", "dense_pr_nearest_radix"))
    variation = {m: {"median_within_case_max_over_min": float(np.median([
        max(r["seconds"][m]) / min(r["seconds"][m]) for r in rows])),
        "max_within_case_max_over_min": max(max(r["seconds"][m]) / min(r["seconds"][m]) for r in rows)} for m in methods}
    return {"cases": len(rows), "max_exact_pr_error": error, "max_enclosure_slack": slack,
            "by_width": by_width, "uncertainty": intervals, "measurement_variation": variation,
            "primary_decision": {"width": 30, "passes": bool(passes),
                                 "criterion": "fast_race: both geomean and aggregate-ratio lower 95% family-bootstrap bounds exceed 1 against sparse_pr, dense_pr_direct, and radix_pr; correctness also required."},
            "radix_primary_decision": {"width": 30, "passes": bool(radix_passes),
                                       "criterion": "radix_pr: both geomean and aggregate-ratio lower 95% family-bootstrap bounds exceed 1 against sparse_pr, dense_pr_direct, dense_nearest_both, dense_pr_direct_radix, and dense_pr_nearest_radix; correctness also required."},
            "radix_racing_decision": {"width": 30, "passes": bool(radix_racing_passes),
                                      "criterion": "fast_race_radix: both geomean and aggregate-ratio lower 95% family-bootstrap bounds exceed 1 against sparse_pr, dense_pr_direct, radix_pr, dense_pr_direct_radix, and dense_pr_nearest_radix; correctness also required."}}


def execute(output, protocol_hash, split, cpu_clearance):
    output = Path(output)
    protocol, inputs = validate_frozen(output, protocol_hash, split)
    from benchmark_advancement import Corpus, np, numba, threadpool_limits, threadpool_info
    from fast_vus_adapter import source_receipt as klein_receipt
    from benchopt_vus_adapter import source_receipt as benchopt_receipt
    numba.set_num_threads(1)
    threadpool_limits(1)
    methods = make_methods(protocol)
    yy = np.zeros(32, dtype=np.int8)
    yy[[4, 5, 13, 25]] = 1
    ss = {"a": np.arange(32, dtype=float), "b": np.arange(32, dtype=float)[::-1],
          "c": np.repeat(np.arange(8, dtype=float), 4)}
    warmup = {}
    for name, fn in methods.items():
        start = time.perf_counter()
        serialize_result(name, fn(yy, ss, 30))
        serialize_result(name, fn(yy, {m: ss["a"] for m in ss}, 4))
        warmup[name] = time.perf_counter() - start
    if source_hashes() != protocol["source_sha256"]:
        raise ValueError("Source changed during warmup")
    write_json(output / "environment.json", {
        "started_utc": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
        "machine": platform.machine(), "processor": platform.processor(), "python": sys.version,
        "numpy": np.__version__, "numba": numba.__version__, "threads": numba.get_num_threads(),
        "threadpool_info": threadpool_info(), "warmup_seconds": warmup,
        "source_sha256": protocol["source_sha256"], "protocol_sha256": protocol_hash,
        "cpu_clearance": cpu_clearance,
        "external_sources": {"klein_pr": klein_receipt(), "benchopt_both": benchopt_receipt()},
    })
    corpus, rng, rows, violations = Corpus(), random.Random(protocol["seed"]), [], []
    with (output / "measurements.jsonl").open("x") as stream:
        for index, identity in enumerate(inputs):
            scores, labels = {}, None
            for model in protocol["models"]:
                y, score = corpus.load({"series": identity["series"], "model": model,
                                       "label_member_sha256": identity["label_sha256"]})
                if labels is not None and not np.array_equal(y, labels):
                    raise ValueError("Model label vectors differ")
                if len(y) != identity["n"] or len(score) != identity["n"] or corpus.hashes[model][identity["series"]] != identity["score_sha256"][model]:
                    raise ValueError("Loaded vector differs from frozen identity")
                labels, scores[model] = y, score
            values, durations, order_receipt = {}, defaultdict(list), []
            for repeat in range(3):
                order = list(methods)
                rng.shuffle(order)
                order_receipt.append(order)
                for name in order:
                    converted, elapsed = timed_call(name, methods[name], labels, scores, identity["max_buffer"])
                    if name in values and converted != values[name]:
                        raise ValueError(f"Nondeterministic result: {identity['series']}/{name}")
                    values[name] = converted
                    durations[name].append(elapsed)
            reference = values["sparse_pr"]
            for name, result in values.items():
                if result["selected"] != reference["selected"]:
                    violations.append([identity["series"], identity["max_buffer"], name, "selection"])
                if name in EXACT and max(abs(v - reference["pr"][m]) for m, v in result["pr"].items()) > 1e-11:
                    violations.append([identity["series"], identity["max_buffer"], name, "exact PR"])
                if name not in EXACT and any(not b["pr_lower"] - 1e-10 <= reference["pr"][m] <= b["pr_upper"] + 1e-10 for m, b in result["bounds"].items()):
                    violations.append([identity["series"], identity["max_buffer"], name, "enclosure"])
            row = {**identity, "values": values, "seconds": dict(durations),
                   "median_seconds": {name: statistics.median(t) for name, t in durations.items()},
                   "method_order": order_receipt}
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
            rows.append(row)
            if (index + 1) % 3 == 0 or index + 1 == len(inputs):
                print(f"{index + 1}/{len(inputs)} cases; violations={len(violations)}", flush=True)
    if source_hashes() != protocol["source_sha256"]:
        raise ValueError("Measured source changed during the run")
    summary = {"status": "PASS" if not violations else "FAIL", "violations": violations,
               "status_scope": "Semantic checks only; speedup decision is reported separately.",
               "completed_utc": datetime.now(timezone.utc).isoformat(),
               "protocol_sha256": protocol_hash, "measurements_sha256": digest(output / "measurements.jsonl"),
               "reconstructed": summarize(rows, protocol)}
    if violations:
        for decision in ("primary_decision", "radix_primary_decision", "radix_racing_decision"):
            summary["reconstructed"][decision]["passes"] = False
    write_json(output / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "cases": len(rows),
                      **{decision: summary["reconstructed"][decision]
                         for decision in ("primary_decision", "radix_primary_decision", "radix_racing_decision")}}, indent=2), flush=True)
    if violations:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("development", "holdout"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--freeze-only", action="store_true")
    modes.add_argument("--execute-frozen", metavar="SHA256")
    parser.add_argument("--cpu-clearance")
    parser.add_argument("--adaptive-fraction", type=float, default=.125)
    parser.add_argument("--memory-bytes", type=int, default=8 * 1024 * 1024)
    parser.add_argument("--full-budget-development", action="store_true")
    args = parser.parse_args()
    if not args.freeze_only and not args.cpu_clearance:
        parser.error("--cpu-clearance is required for timing execution")
    if args.split == "holdout" and not (args.freeze_only or args.execute_frozen):
        parser.error("Freeze the held-out protocol first, then execute its exact SHA256")
    if args.execute_frozen:
        # Configuration lives entirely in the frozen document for this mode.
        if args.full_budget_development or args.adaptive_fraction != .125 or args.memory_bytes != 8 * 1024 * 1024:
            parser.error("Do not override configuration while executing a frozen protocol")
        execute(args.output, args.execute_frozen, args.split, args.cpu_clearance)
        return
    freeze(args.output, args.split, adaptive_fraction=args.adaptive_fraction,
           memory_bytes=args.memory_bytes, include_full_budget=args.full_budget_development)
    frozen_hash = digest(args.output / "protocol.json")
    print(json.dumps({"protocol_sha256": frozen_hash, "output": str(args.output),
                      "state": "frozen_before_new_outcomes"}), flush=True)
    if not args.freeze_only:
        execute(args.output, frozen_hash, args.split, args.cpu_clearance)


if __name__ == "__main__":
    main()
