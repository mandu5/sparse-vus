"""Reproduce independent automated core-review checks against pinned upstream.

Adapted from the reviewer's /tmp/review_sparse_vus.py. This is automated
verification, not human peer review, a novelty assessment, or acceptance.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import itertools
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from sparse_vus import sparse_vus, dense_vus
from sparse_vus.compiled import (
    sparse_vus_jit, dense_vus_jit, dense_vus_direct_jit,
)

REFERENCE_SHA = "bd547c9746fc1b9bbce2895e20cb156f97d23365d5dce8c2a3fab90622ccdced"
FUNCTIONS = (sparse_vus, dense_vus, sparse_vus_jit, dense_vus_jit, dense_vus_direct_jit)
WIDTHS = (0, 1, 2, 3, 4, 7, 12)
TOLERANCE = 1e-11
RANDOM_SEED = 714099


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    paths = sorted((ROOT / "src/sparse_vus").glob("*.py"))
    paths += [Path(__file__)]
    return {str(path.relative_to(ROOT)): digest(path) for path in paths}


def git(args):
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else None


def run():
    started = time.perf_counter()
    initial_hashes = source_hashes()
    reference_path = ROOT / "cache/official_metrics.py"
    if not reference_path.exists():
        raise FileNotFoundError("Run python experiments/fetch_reference.py first")
    if digest(reference_path) != REFERENCE_SHA:
        raise ValueError("Reference source SHA-256 mismatch")
    spec = importlib.util.spec_from_file_location("independent_official_metrics", reference_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reference = module.metricor()
    maxima = {section: {fn.__name__: 0.0 for fn in FUNCTIONS}
              for section in ("exhaustive", "random")}

    def check(y, scores, width, section):
        expected = np.asarray(reference.RangeAUC_volume_opt(y, scores, width, thre=len(y))[-2:])
        for fn in FUNCTIONS:
            # Extreme finite scores can overflow np.diff in the dense grouping
            # predicate; the nonzero comparison still groups them correctly.
            with np.errstate(over="ignore"):
                actual = np.asarray(fn(y, scores, width))
            error = float(np.max(np.abs(actual - expected)))
            if not np.isfinite(actual).all() or not np.isfinite(error) or error > TOLERANCE:
                raise AssertionError({"function": fn.__name__, "labels": y.tolist(),
                    "scores": scores.tolist(), "width": width,
                    "expected": expected.tolist(), "actual": actual.tolist()})
            maxima[section][fn.__name__] = max(maxima[section][fn.__name__], error)

    exhaustive_count = 0
    for n in range(2, 5):
        for labels in itertools.product((0, 1), repeat=n):
            if sum(labels) in (0, n):
                continue
            y = np.asarray(labels)
            for scores in itertools.product((0.0, 1.0), repeat=n):
                for width in WIDTHS:
                    check(y, np.asarray(scores), width, "exhaustive")
                    exhaustive_count += 1
    print(f"Exhaustive cases passed: {exhaustive_count}", file=sys.stderr, flush=True)

    rng = np.random.default_rng(RANDOM_SEED)
    for index in range(120):
        n = int(rng.integers(2, 200))
        y = (rng.random(n) < rng.uniform(.01, .99)).astype(int)
        if y.sum() in (0, n):
            y[rng.integers(n)] = 1 - y[0]
        scores = (rng.choice([-1e308, -1.0, -0.0, 1.0, 1e308], n)
                  if index % 3 == 0 else rng.normal(size=n))
        width = int(rng.integers(0, 3 * n))
        check(y, scores, width, "random")

    for dtype in (np.uint8, np.uint64):
        for fn in FUNCTIONS:
            assert fn(np.asarray([0, 1]), np.asarray([0, 1], dtype=dtype), 0) == (1.0, 1.0)
    if source_hashes() != initial_hashes:
        raise RuntimeError("Reviewed source changed during verification; rerun")
    return {
        "reviewer": "Automated independent agent; not human peer review or acceptance",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "environment": {
            "executable": sys.executable, "python": sys.version,
            "platform": platform.platform(), "machine": platform.machine(),
            "packages": {name: importlib.metadata.version(name)
                         for name in ("numpy", "numba", "scipy", "scikit-learn")},
            "thread_environment": {name: os.environ.get(name) for name in
                                   ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "NUMBA_NUM_THREADS")},
        },
        "git_head": git(["rev-parse", "HEAD"]),
        "git_status_porcelain": git(["status", "--porcelain"]),
        "reference_sha256": REFERENCE_SHA,
        "source_sha256": initial_hashes,
        "exhaustive": {"cases": exhaustive_count, "n": [2, 3, 4],
            "labels": "All binary arrays containing both classes",
            "scores": "All binary score arrays, including constant ties",
            "max_buffers": list(WIDTHS)},
        "random": {"cases": 120, "seed": RANDOM_SEED, "indices": [0, 119],
            "n": "rng.integers(2,200)", "max_buffer": "rng.integers(0,3*n)",
            "labels": "Bernoulli rate drawn uniformly from .01 to .99; force both classes only if needed",
            "scores": "Every third case: {-1e308,-1,-0,1,1e308}; otherwise standard normal"},
        "unsigned_regression": "uint8 and uint64 [0,1] passed for all five paths",
        "tolerance": TOLERANCE, "maximum_absolute_errors": maxima,
        "seconds": time.perf_counter() - started,
        "limitations": ["Finite verification does not prove floating-point equality for all inputs",
                         "No benchmark-speed, novelty, paper, or acceptance assessment"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = run()
    text = json.dumps(receipt, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
