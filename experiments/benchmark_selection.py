"""Measure whole three-model PR selection, including every fallback.

This is a post-baseline follow-up, with protocol frozen before its own results.
The 42-series selection is inherited from the released metadata-only selection.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import time

from benchmark_advancement import (
    ROOT, Corpus, corpus_rows, digest, write_json, np, numba,
    sparse_vus_jit, dense_vus_direct_jit, dense_vus_jit, threadpool_limits,
    threadpool_info,
)
from fast_vus_adapter import fast_vus_pr, source_receipt
from sparse_vus.selection import select_pr_model


def exact_selection(y, scores, width, evaluator):
    values = {name: float(evaluator(y, score, width)[1])
              for name, score in sorted(scores.items())}
    best = max(values.values())
    return {"selected": sorted(name for name, value in values.items()
                               if best - value <= 1e-10),
            "pr": values}


def bounded_selection(y, scores, width, *, prune):
    result = select_pr_model(y, scores, width, atol=0.01, prune=prune,
                             exact_evaluator=sparse_vus_jit)
    return {
        "selected": list(result.selected),
        "early_winner": result.early_winner,
        "candidates": list(result.candidate_models),
        "pruned": list(result.pruned_models),
        "exact_fallback_count": result.exact_fallback_count,
        "certified_evaluations": result.certified_evaluations,
        "certified_curve_evaluations": result.certified_curve_evaluations,
        "certified_unique_widths": result.certified_unique_widths,
        "exact_pr": result.exact_pr,
        "bounds": {name: [value.pr_lower, value.pr_upper]
                   for name, value in result.bounds.items()},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cpu-clearance", required=True)
    args = parser.parse_args()
    groups = defaultdict(list)
    for row in corpus_rows("certified"):
        groups[(row["series"], row["max_buffer"])].append(row)
    selected = sorted(groups)
    protocol = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "Post-baseline follow-up; frozen before this selection experiment.",
        "cases": len(selected), "models_per_case": 3, "repetitions": 3,
        "seed": 202610203, "atol": 0.01,
        "selection": "Released metadata-only 42 series, all three released models; "
                     "widths 30, 100, 300. Width 300 is an explicit stress regime.",
        "selection_sha256": hashlib.sha256(json.dumps(
            selected, separators=(",", ":")).encode()).hexdigest(),
        "contract": "Return all models within 1e-10 of the maximum exact PR. "
                    "Certificate-first uses 3e-10 numerical separation, then exact "
                    "fallback for unresolved candidates. No-pruning ablation falls "
                    "back to all three models when unresolved.",
        "timing": "Whole three-model calls including validation, preprocessing, "
                  "bounds and fallback. Loading precomputed scores and JIT warmup "
                  "excluded. One thread; randomized method order, three repetitions.",
        "scope": "Numerically audited selection on frozen inputs, not a formal "
                 "outward-rounded Float64 certificate or detector training speedup.",
        "fixed250": "Speed/decision-error comparator, not an exact-contract baseline.",
        "exact_parity_tolerance": 1e-11,
        "float64_containment_tolerance": 1e-10,
    }
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "protocol.json", protocol)
    numba.set_num_threads(1)
    threadpool_limits(1)
    methods = {
        "sparse_exact": lambda y, s, w: exact_selection(y, s, w, sparse_vus_jit),
        "dense_direct": lambda y, s, w: exact_selection(y, s, w, dense_vus_direct_jit),
        "dense_nearest": lambda y, s, w: exact_selection(y, s, w, dense_vus_jit),
        "fast_vus_exact_pr": lambda y, s, w: exact_selection(
            y, s, w, lambda yy, ss, ww: (None, fast_vus_pr(yy, ss, ww, len(yy)))),
        "fixed250_pr": lambda y, s, w: exact_selection(
            y, s, w, lambda yy, ss, ww: (None, fast_vus_pr(yy, ss, ww, 250))),
        "certificate_prune": lambda y, s, w: bounded_selection(y, s, w, prune=True),
        "certificate_no_prune": lambda y, s, w: bounded_selection(y, s, w, prune=False),
    }
    yy = np.array([0, 1, 0, 0, 1, 0], dtype=np.int8)
    ss = {"a": np.arange(6, dtype=float), "b": np.arange(6, dtype=float)[::-1],
          "c": np.array([1., 1., 2., 2., 3., 3.])}
    warmup = {}
    for name, fn in methods.items():
        start = time.perf_counter()
        fn(yy, ss, 4)
        warmup[name] = time.perf_counter() - start
    sources = [
        Path(__file__), ROOT / "experiments/benchmark_advancement.py",
        ROOT / "experiments/fast_vus_adapter.py",
        ROOT / "src/sparse_vus/selection.py", ROOT / "src/sparse_vus/certified.py",
        ROOT / "src/sparse_vus/core.py", ROOT / "src/sparse_vus/compiled.py",
        ROOT / ".cache/fast_vus/fast_vus.py",
    ]
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    write_json(args.output / "environment.json", {
        "platform": platform.platform(), "machine": platform.machine(),
        "python": sys.version, "numpy": np.__version__, "numba": numba.__version__,
        "threads": numba.get_num_threads(), "threadpool_info": threadpool_info(),
        "source_sha256": hashes, "protocol_sha256": digest(args.output / "protocol.json"),
        "cpu_clearance": args.cpu_clearance, "warmup_seconds": warmup,
        "external_baseline": source_receipt(),
    })
    corpus, rng = Corpus(), np.random.default_rng(protocol["seed"])
    violations, records = [], []
    with (args.output / "measurements.jsonl").open("x") as stream:
        for index, (series, width) in enumerate(selected):
            rows = groups[(series, width)]
            scores, score_hashes, labels = {}, {}, None
            for row in rows:
                y, s = corpus.load(row)
                if labels is not None and not np.array_equal(y, labels):
                    raise ValueError("model labels differ")
                labels, scores[row["model"]] = y, s
                score_hashes[row["model"]] = corpus.hashes[row["model"]][series]
            if len(scores) != 3:
                raise ValueError("incomplete model coverage")
            timings, results = defaultdict(list), {}
            for repeat in range(protocol["repetitions"]):
                order = list(methods)
                rng.shuffle(order)
                for name in order:
                    start = time.perf_counter()
                    result = methods[name](labels, scores, width)
                    timings[name].append(time.perf_counter() - start)
                    if name in results and results[name] != result:
                        raise ValueError(f"nondeterministic selection: {name}")
                    results[name] = result
            reference = results["sparse_exact"]
            for name, result in results.items():
                if name != "fixed250_pr" and result["selected"] != reference["selected"]:
                    violations.append([series, width, name, "wrong selection"])
                if name in ("dense_direct", "dense_nearest", "fast_vus_exact_pr"):
                    if max(abs(v - reference["pr"][m])
                           for m, v in result["pr"].items()) > 1e-11:
                        violations.append([series, width, name, "exact parity"])
                if name.startswith("certificate"):
                    for model, (lower, upper) in result["bounds"].items():
                        if not lower - 1e-10 <= reference["pr"][model] <= upper + 1e-10:
                            violations.append([series, width, name, "enclosure"])
            record = {
                "series": series, "family": rows[0]["family"], "n": len(labels),
                "max_buffer": width, "label_sha256": rows[0]["label_member_sha256"],
                "score_sha256": score_hashes, "values": results,
                "seconds": dict(timings),
                "median_seconds": {n: statistics.median(v) for n, v in timings.items()},
                "fixed250_wrong_selection": results["fixed250_pr"]["selected"]
                                            != reference["selected"],
                "exact_unique_winner": len(reference["selected"]) == 1,
            }
            stream.write(json.dumps(record, allow_nan=False) + "\n")
            stream.flush()
            records.append(record)
            if (index + 1) % 6 == 0 or index + 1 == len(selected):
                print(f"{index + 1}/{len(selected)} cases; violations={len(violations)}",
                      flush=True)
    if any(digest(ROOT / name) != value for name, value in hashes.items()):
        raise ValueError("measured source changed")
    report = {
        "status": "PASS" if not violations else "FAIL", "cases": len(records),
        "violations": violations,
        "measurements_sha256": digest(args.output / "measurements.jsonl"),
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "by_width": {},
    }
    for width in (30, 100, 300):
        group = [r for r in records if r["max_buffer"] == width]
        out = {"cases": len(group),
               "exact_unique_winner_cases": sum(r["exact_unique_winner"] for r in group),
               "fixed250_wrong_selections": sum(r["fixed250_wrong_selection"] for r in group),
               "sum_case_median_seconds": {
                   m: sum(r["median_seconds"][m] for r in group) for m in methods}}
        for name in ("certificate_prune", "certificate_no_prune"):
            out[name] = {
                "early_winners": sum(r["values"][name]["early_winner"] for r in group),
                "exact_fallback_evaluations": sum(
                    r["values"][name]["exact_fallback_count"] for r in group),
                "ratios_by_comparator": {
                    comparator: {
                        "median": float(np.median([
                            r["median_seconds"][comparator] / r["median_seconds"][name]
                            for r in group])),
                        "faster_cases": sum(r["median_seconds"][comparator]
                                            > r["median_seconds"][name] for r in group),
                    } for comparator in methods if comparator != name},
            }
        report["by_width"][str(width)] = out
    write_json(args.output / "summary.json", report)
    print(json.dumps(report, indent=2, allow_nan=False), flush=True)
    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
