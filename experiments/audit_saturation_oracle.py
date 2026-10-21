"""Bounded independent dense-oracle audit of active-prefix VUS.

The oracle constructs ramps, overlap-only components and all distinct score
thresholds directly. It imports no sparse_vus helper. Only the implementations
under test are imported from sparse_vus.saturation. No downloads or benchmarks
are performed. By default the JSON receipt is printed; --output also saves it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHECKED_FILES = (
    "src/sparse_vus/saturation.py",
    "src/sparse_vus/radix.py",
    "src/sparse_vus/core.py",
    "paper/saturation_method.tex",
)
STOP_MODES = (("saturation", True), ("full", False),
              ("last_original_positive", "last_positive"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dense_oracle(labels, scores, maximum_width):
    """Direct full-threshold reference; no production interval/rank helpers."""
    labels = np.asarray(labels, dtype=np.int8)
    scores = np.asarray(scores, dtype=np.float64)
    intervals = []
    start = None
    for index, value in enumerate([*labels, 0]):
        if value and start is None:
            start = index
        if not value and start is not None:
            intervals.append((start, index - 1))
            start = None
    length = len(labels)
    positives = int(sum(labels))
    thresholds = sorted(set(scores), reverse=True)
    areas = []
    for width in range(maximum_width + 1):
        radius = width // 2
        weights = labels.astype(np.float64)
        components = []
        for left, right in intervals:
            for index in range(max(0, left - radius), left):
                weights[index] += np.sqrt(1.0 - (left - index) / width)
            for index in range(right + 1, min(length, right + radius + 1)):
                weights[index] += np.sqrt(1.0 - (index - right) / width)
            lower, upper = max(0, left - radius), min(length - 1, right + radius)
            # Closed intervals merge on overlap, never just adjacency.
            if components and lower <= components[-1][1]:
                components[-1] = (components[-1][0], upper)
            else:
                components.append((lower, upper))
        weights = np.minimum(weights, 1.0)
        old_recall = old_fpr = roc = pr = 0.0
        for threshold in thresholds:
            prediction = scores >= threshold
            count = int(prediction.sum())
            true_mass = float(weights[prediction].sum())
            buffer_mass = float(weights[prediction & (labels == 0)].sum())
            positive_mass = positives + buffer_mass / 2.0
            hits = sum(bool(prediction[lower:upper + 1].any())
                       for lower, upper in components)
            recall = min(true_mass / positive_mass, 1.0) * hits / len(components)
            fpr = (count - true_mass) / (length - positive_mass)
            pr += (recall - old_recall) * true_mass / count
            roc += (fpr - old_fpr) * (recall + old_recall) / 2.0
            old_recall, old_fpr = recall, fpr
        roc += (1.0 - old_fpr) * (1.0 + old_recall) / 2.0
        areas.append((roc, pr))
    return np.mean(areas, axis=0)


def audit(max_length: int, tolerance: float):
    started = datetime.now(timezone.utc).isoformat()
    started_clock = time.monotonic()
    source_before = {relative: sha256(ROOT / relative) for relative in CHECKED_FILES}
    script_before = sha256(Path(__file__))
    sys.path.insert(0, str(ROOT / "src"))
    from sparse_vus.saturation import (
        sparse_pr_saturation_jit, sparse_vus_saturation_jit,
    )
    import numba

    failures = []
    failure_count = 0
    case_counts = {"exhaustive": 0, "strided": 0}
    mode_counts = {name: 0 for name, _ in STOP_MODES}
    maximum_pair_error = maximum_pr_error = 0.0

    def check(labels, scores, width, category):
        nonlocal failure_count, maximum_pair_error, maximum_pr_error
        expected = dense_oracle(labels, scores, width)
        case_counts[category] += 1
        for name, stop in STOP_MODES:
            paired = np.asarray(sparse_vus_saturation_jit(
                labels, scores, width, stop=stop), dtype=np.float64)
            pr = sparse_pr_saturation_jit(labels, scores, width, stop=stop)
            pair_error = float(np.max(np.abs(paired - expected)))
            pr_error = abs(float(pr) - float(expected[1]))
            mode_counts[name] += 1
            maximum_pair_error = max(maximum_pair_error, pair_error)
            maximum_pr_error = max(maximum_pr_error, pr_error)
            if (not np.isfinite(paired).all() or not np.isfinite(pr)
                    or pair_error > tolerance or pr_error > tolerance):
                failure_count += 1
                if len(failures) < 20:
                    failures.append({"labels": np.asarray(labels).tolist(),
                                     "scores": np.asarray(scores).tolist(),
                                     "width": width, "mode": name,
                                     "expected": expected.tolist(),
                                     "paired": paired.tolist(), "pr": float(pr),
                                     "pair_error": pair_error, "pr_error": pr_error})

    for length in range(2, max_length + 1):
        for labels in itertools.product((0, 1), repeat=length):
            if sum(labels) in (0, length):
                continue
            for scores in itertools.product((-1.0, 0.0, 1.0), repeat=length):
                check(labels, scores, 2 * length + 1, "exhaustive")

    labels = np.asarray([0, 1, 0, 0, 1, 0], dtype=np.int8)
    scores = np.asarray([0.0, 2.0, 1.0, 3.0, -1.0, 5.0])
    check(labels[::-1], scores[::-1], 13, "strided")
    check(np.repeat(labels, 2)[::2], np.repeat(scores, 2)[::2], 13, "strided")

    source_after = {relative: sha256(ROOT / relative) for relative in CHECKED_FILES}
    script_after = sha256(Path(__file__))
    stable = source_before == source_after and script_before == script_after
    return {
        "status": "PASS" if failure_count == 0 and stable else "FAIL",
        "schema_version": 1, "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds_including_imports_and_compilation": time.monotonic() - started_clock,
        "protocol": {
            "lengths": [2, max_length], "labels": "all both-class binary label vectors",
            "scores": "all assignments from {-1, 0, 1}; ties admitted atomically",
            "maximum_width": "2*n+1, evaluating every integer width from zero",
            "additional_inputs": "one reversed and one non-contiguous stride view, n=6, L=13",
            "stop_modes": [name for name, _ in STOP_MODES],
            "targets": ["paired ROC/PR public call", "PR-only public call"],
            "absolute_tolerance": tolerance, "relative_tolerance": 0.0,
            "oracle": "direct ramps, overlap-only interval merging, every distinct global threshold",
            "shared_production_helpers_used_by_oracle": [],
        },
        "case_counts": case_counts, "case_mode_counts": mode_counts,
        "case_mode_pairs": sum(mode_counts.values()),
        "candidate_public_calls": 2 * sum(mode_counts.values()),
        "maximum_paired_absolute_error": maximum_pair_error,
        "maximum_pr_only_absolute_error": maximum_pr_error,
        "failure_count": failure_count, "first_failures": failures,
        "source_sha256_before": source_before, "source_sha256_after": source_after,
        "oracle_script_sha256": script_before, "sources_unchanged_during_audit": stable,
        "environment": {"python": sys.version, "numpy": np.__version__,
                        "numba": numba.__version__, "platform": platform.platform()},
        "limits": ["Exhaustive only within the stated finite labels/score domain.",
                   "Uses floating-point arithmetic, not symbolic or directed-rounding certification.",
                   "The independently written oracle is in-session validation, not external reproduction.",
                   "No performance, generalization, novelty or publication claim is established."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-length", type=int, choices=range(2, 7), default=5)
    parser.add_argument("--atol", type=float, default=2e-12)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not np.isfinite(args.atol) or args.atol < 0:
        parser.error("--atol must be finite and nonnegative")
    result = audit(args.max_length, args.atol)
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
