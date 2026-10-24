"""Frozen supplementary baseline/accuracy study on the complete fixed panel.

Added after the primary result to address omitted public comparator coverage.
It is explicitly a supplementary comparison, not a replacement primary test.
"""
from __future__ import annotations
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[key] = "1"
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "artifacts/pvldb-research-20261024/full-precision"
OUT = ROOT / "artifacts/pvldb-research-20261024/supplement"
CACHE = ROOT / ".cache/pvldb-full-precision-20261024"
METHODS = ["stream", "klein_exact", "benchopt_pair", "radix_pair", "klein250", "klein1000"]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while block := f.read(1 << 20): h.update(block)
    return h.hexdigest()


def new_json(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write("\n")


def selection_loss(exact, approximate):
    exact, approximate = np.asarray(exact, float), np.asarray(approximate, float)
    if (exact.ndim != 1 or len(exact) == 0 or exact.shape != approximate.shape
            or not np.isfinite(exact).all() or not np.isfinite(approximate).all()):
        raise ValueError("matching nonempty finite vectors required")
    truth = np.flatnonzero(exact >= exact.max() - 1e-10).tolist()
    chosen = np.flatnonzero(approximate >= approximate.max() - 1e-10).tolist()
    loss = exact.max() - exact[chosen]
    return {"selected": chosen, "exact_winners": truth,
            "minimum_regret": float(loss.min()), "maximum_regret": float(loss.max()),
            "identical_winner_set": chosen == truth}


def evaluate(method, y, scores):
    from sparse_vus.batch import batch_pr
    from sparse_vus.radix import sparse_vus_radix_jit
    from fast_vus_adapter import fast_vus_pr
    from benchopt_vus_adapter import benchopt_vus
    if method == "stream":
        return batch_pr(y, scores, 30), None
    if method in ("benchopt_pair", "radix_pair"):
        f = (lambda y, s: benchopt_vus(y, s, 30, len(y))) if method == "benchopt_pair" else (lambda y, s: sparse_vus_radix_jit(y, s, 30))
        pairs = np.asarray([f(y, s) for s in scores])
        return pairs[:, 1], pairs[:, 0]
    h = {"klein_exact": len(y), "klein250": 250, "klein1000": 1000}[method]
    return np.asarray([fast_vus_pr(y, s, 30, h) for s in scores]), None


def freeze():
    primary = json.loads((PRIMARY / "protocol.json").read_text())
    sources = dict(primary["source_sha256"])
    for path in ["experiments/pvldb_supplement.py", "experiments/benchopt_vus_adapter.py", ".cache/benchopt_vus/metrics.py"]:
        sources[path] = digest(ROOT / path)
    orders = [METHODS[i:] + METHODS[:i] for i in range(len(METHODS))]
    orders += [list(reversed(order)) for order in orders]
    OUT.mkdir(parents=True, exist_ok=False)
    new_json(OUT / "protocol.json", {
        "status": "FROZEN_AFTER_PRIMARY_RESULTS_BEFORE_SUPPLEMENT_OUTCOMES",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "primary_protocol_sha256": digest(PRIMARY / "protocol.json"),
        "inputs_sha256": digest(PRIMARY / "inputs.json"), "source_sha256": sources,
        "methods": METHODS, "orders": orders, "width": 30,
        "cohort": "All 73 fixed full-precision series and all eight stored scores; no exclusions or regenerated inputs",
        "comparison": "Unchanged Benchopt computes ROC and PR. Report its native PR-consumer cost AND matched two-output radix/Benchopt comparison. Klein PR exact and default250/1000 form separate accuracy-cost comparisons.",
        "timing": "Single numerical thread, warm JIT, complete public calls and winner selection. Balanced orders. A separate complete collection pass includes reads and output writes.",
        "repetitions": len(orders), "regret_threshold": .01,
        "uncertainty": "Paired log-ratio bootstrap of case medians plus identical-label-block sensitivity; no physical-recording iid or unseen-data claim",
        "failure_policy": "Record all losses; scalar parity>1e-11 or mismatched exact winner sets halt; sampled errors retained, not failures",
    })


def verify():
    p = json.loads((OUT / "protocol.json").read_text())
    for path, expected in p["source_sha256"].items():
        if digest(ROOT / path) != expected: raise ValueError(f"source changed: {path}")
    if digest(PRIMARY / "inputs.json") != p["inputs_sha256"]: raise ValueError("inputs changed")
    if digest(PRIMARY / "protocol.json") != p["primary_protocol_sha256"]: raise ValueError("primary changed")
    return p


def run():
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "experiments")]
    p = verify(); inputs = json.loads((PRIMARY / "inputs.json").read_text())["series"]
    for row in inputs:
        if digest(CACHE / row["file"]) != row["npz_sha256"]: raise ValueError("score file changed")
    new_json(OUT / "run-start.json", {"platform": platform.platform(), "python": sys.version,
             "protocol_sha256": digest(OUT / "protocol.json"), "utc": datetime.now(timezone.utc).isoformat()})
    y = np.array([0, 1, 0, 0, 1, 0], np.int8); scores = np.tile(np.arange(6.), (8, 1))
    for method in METHODS: evaluate(method, y, scores)
    with (OUT / "records.jsonl").open("x") as f:
        for case in inputs:
            with np.load(CACHE / case["file"], allow_pickle=False) as z: y, scores = z["labels"], z["scores"]
            expected_pr, expected_roc = evaluate("radix_pair", y, scores)
            for trial, order in enumerate(p["orders"]):
                for method in order:
                    start = time.perf_counter_ns()
                    pr, roc = evaluate(method, y, scores)
                    chosen = np.flatnonzero(pr >= pr.max() - 1e-10).tolist()
                    seconds = (time.perf_counter_ns() - start) * 1e-9
                    error = float(np.max(np.abs(pr - expected_pr)))
                    roc_error = None if roc is None else float(np.max(np.abs(roc - expected_roc)))
                    selection = selection_loss(expected_pr, pr)
                    if method not in ("klein250", "klein1000") and (error > 1e-11 or (roc_error or 0) > 1e-11 or not selection["identical_winner_set"]):
                        raise ValueError(f"exact parity failure: {case['series']} {method}")
                    row = {"series": case["series"], "family": case["family"], "method": method,
                           "trial": trial, "seconds": seconds, "values": pr.tolist(), "winners": chosen,
                           "pr_error": error, "roc_error": roc_error, "selection": selection}
                    f.write(json.dumps(row, allow_nan=False) + "\n"); f.flush()
            print(case["series"], "complete", flush=True)
    with (OUT / "workflows.jsonl").open("x") as f:
        for family in ("NAB", "SMAP", "SMD"):
            cases = [c for c in inputs if c["family"] == family]
            for trial, order in enumerate(p["orders"]):
                for method in order:
                    start = time.perf_counter_ns(); decisions = []
                    for case in cases:
                        with np.load(CACHE / case["file"], allow_pickle=False) as z:
                            pr, roc = evaluate(method, z["labels"], z["scores"])
                        decisions.append({"series": case["series"], "values": pr.tolist(),
                                          "roc": None if roc is None else roc.tolist(),
                                          "winners": np.flatnonzero(pr >= pr.max() - 1e-10).tolist()})
                    with (CACHE / "last-supplement-output.json").open("w") as output: json.dump(decisions, output, allow_nan=False)
                    seconds = (time.perf_counter_ns() - start) * 1e-9
                    f.write(json.dumps({"family": family, "method": method, "trial": trial,
                                        "seconds": seconds, "decisions": decisions}) + "\n"); f.flush()
            print(family, "workflow complete", flush=True)
    new_json(OUT / "complete.json", {"status": "COMPLETE", "protocol_sha256": digest(OUT / "protocol.json"),
             "records_sha256": digest(OUT / "records.jsonl"), "workflows_sha256": digest(OUT / "workflows.jsonl"),
             "utc": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=["freeze", "run"])
    globals()[parser.parse_args().command]()
