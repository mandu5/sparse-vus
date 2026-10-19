"""Validate the analytic fixed-threshold-grid counterexample; no timing claims."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sparse_vus import sparse_vus, sampled_vus


def counterexample(n: int, positives: int, max_buffer: int):
    """Appending low-score negatives preserves all existing scores and labels."""
    start = 20
    half = max_buffer // 2
    y = np.zeros(n, dtype=np.int8)
    y[start:start + positives] = 1
    scores = -np.arange(n, dtype=float)
    scores[0] = positives + 2
    scores[start:start + positives] = np.arange(positives + 1, 1, -1)
    support = np.arange(start - half, start + positives + half)
    buffer = support[y[support] == 0]
    scores[buffer] = 1 - np.arange(len(buffer)) / (len(buffer) + 1)
    return y, scores


def main():
    protocol = {"purpose": "Deterministic verification of a motivating proposition, not a standalone novelty claim or performance experiment",
                "thresholds": 250, "lengths": [10000, 100000], "positive_counts": [1, 10],
                "max_buffers": [0, 6], "absolute_tolerance": 1e-11}
    rows = []
    for positives in protocol["positive_counts"]:
        for width in protocol["max_buffers"]:
            for n in protocol["lengths"]:
                y, scores = counterexample(n, positives, width)
                exact = sparse_vus(y, scores, width)
                sampled = sampled_vus(y, scores, width, thresholds=protocol["thresholds"])
                k = 1 + (n - 1) // (protocol["thresholds"] - 1)
                support_count = positives + 2 * (width // 2)
                if k < support_count + 1:
                    raise AssertionError("Second threshold does not yet include all support")
                expected_exact = sum(j / (j + 1) for j in range(1, positives + 1)) / positives
                mean_label_mass = np.mean([positives + 2 * sum(np.sqrt(1 - d / w) for d in range(1, w // 2 + 1)) if w else positives for w in range(width + 1)])
                expected_sampled = float(mean_label_mass / k)
                error = max(abs(exact[1] - expected_exact), abs(sampled[1] - expected_sampled))
                if not np.isfinite(error) or error > protocol["absolute_tolerance"]:
                    raise AssertionError((positives, width, n, exact, sampled, error))
                rows.append({"n": n, "positives": positives, "max_buffer": width, "second_grid_rank": k,
                             "exact_pr": exact[1], "sampled_pr": sampled[1], "expected_exact_pr": expected_exact,
                             "expected_sampled_pr": expected_sampled, "absolute_sampling_error": abs(exact[1] - sampled[1]),
                             "formula_error": error})
    result = {"status": "PASS", "protocol": protocol, "rows": rows,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (ROOT / "artifacts/fixed_grid_pr_counterexample.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
