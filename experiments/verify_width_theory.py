"""Reproduce the finite checks supporting merge-aware width certificates.

Run from any directory:
    python experiments/verify_width_theory.py --output results/width-theory.json

The label enumeration is exhaustive only for lengths 2 through 7.  Each
label vector receives four seeded score patterns, not every score ordering.
LP and direct-curve comparisons are Float64 checks, not formal interval
arithmetic verification.  No downloads, model calls, or timed benchmarks run.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import scipy
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sparse_vus.certified import PreparedEvaluator, _pbox_extremum, width_bounds
from sparse_vus.core import sparse_vus


SEED = 20261020
CURVE_ATOL = 2e-12
BOUND_ATOL = 2e-12
LP_ATOL = 1e-9


def direct_full_rank_curve(y, scores, width):
    """Independent sum-and-clip construction and every distinct score event.

    Uses neither sparse support preparation, nearest interval distances, nor
    any helper or kernel from sparse_vus.  Segments are merged directly.
    """
    y = np.asarray(y, dtype=np.int8)
    scores = np.asarray(scores, dtype=float)
    n, p = len(y), int(y.sum())
    edges = np.diff(np.r_[0, y, 0])
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1) - 1
    weight = y.astype(float)
    segments = []
    radius = width // 2
    for start, end in zip(starts, ends):
        lo, hi = max(0, start - radius), min(n - 1, end + radius)
        for i in range(lo, start):
            weight[i] += np.sqrt(1 - (start - i) / width)
        for i in range(end + 1, hi + 1):
            weight[i] += np.sqrt(1 - (i - end) / width)
        if segments and lo <= segments[-1][1]:
            segments[-1] = (segments[-1][0], hi)
        else:
            segments.append((lo, hi))
    weight = np.minimum(weight, 1)
    order = np.argsort(-scores, kind="stable")
    last = np.r_[np.flatnonzero(np.diff(scores[order]) != 0), n - 1]
    count = last + 1
    tp = weight[order].cumsum()[last]
    buf = (weight * (1 - y))[order].cumsum()[last]
    hits = np.array([
        sum(np.any(scores[a:b + 1] >= scores[order[k]]) for a, b in segments)
        for k in last
    ])
    recall = np.minimum(tp / (p + buf / 2), 1) * hits / len(segments)
    precision = tp / count
    fpr = (count - tp) / (n - p - buf / 2)
    roc_x, roc_y = np.r_[0., fpr, 1.], np.r_[0., recall, 1.]
    roc = float(np.dot(np.diff(roc_x), (roc_y[1:] + roc_y[:-1]) / 2))
    pr = float(np.dot(np.diff(np.r_[0., recall]), precision))
    return np.array([roc, pr]), len(segments)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_linear_programs(rng, report):
    part = dict(
        checks=0,
        event_counts=list(range(1, 20)),
        draws_per_event_count=20,
        objectives_per_draw=2,
        absolute_tolerance=LP_ATOL,
        max_absolute_error=0.0,
        solver="scipy.optimize.linprog(method='highs')",
    )
    report["pbox_linear_programs"] = part
    for groups in range(1, 20):
        matrix = np.tril(np.ones((groups, groups)))
        for draw in range(20):
            r = np.sort(rng.random(groups - 1))
            s = np.sort(rng.random(groups - 1))
            lower = np.r_[np.minimum(r, s), 1.]
            upper = np.r_[np.maximum(r, s), 1.]
            precision = rng.random(groups)
            for maximize in (False, True):
                optimum = linprog(
                    -precision if maximize else precision,
                    A_ub=np.vstack([matrix, -matrix]),
                    b_ub=np.r_[upper, -lower],
                    bounds=(0, None),
                    method="highs",
                )
                require(optimum.success, f"LP failed at G={groups}, draw={draw}: {optimum.message}")
                expected = -optimum.fun if maximize else optimum.fun
                actual = float(_pbox_extremum(lower, upper, precision, maximize))
                error = abs(expected - actual)
                part["checks"] += 1
                part["max_absolute_error"] = max(part["max_absolute_error"], error)
                require(error <= LP_ATOL, f"P-box/LP disagreement: G={groups}, draw={draw}, error={error}")
    require(part["checks"] == 760, "Unexpected LP coverage count")


def check_small_labels(rng, report):
    part = dict(
        label_lengths=list(range(2, 8)),
        labels="Every binary vector containing both classes",
        score_patterns=[
            "First seeded permutation of distinct integer scores",
            "Second seeded permutation of distinct integer scores",
            "First seeded independent integer vector with values 0,1,2",
            "Second seeded independent integer vector with values 0,1,2",
        ],
        width_rule="Every integer width from 0 through 2*n+1",
        label_vectors=0,
        input_cases=0,
        direct_curve_checks=0,
        width_enclosures=0,
        mean_comparisons_with_numpy_sparse=0,
        max_curve_absolute_error=0.0,
        max_mean_absolute_error=0.0,
        max_bound_violation=0.0,
        curve_absolute_tolerance=CURVE_ATOL,
        enclosure_absolute_tolerance=BOUND_ATOL,
        exhaustive_scope="Labels only; four seeded score patterns, not all rankings or ties",
    )
    report["small_label_enumeration"] = part
    for n in range(2, 8):
        for labels in product([0, 1], repeat=n):
            if sum(labels) in (0, n):
                continue
            part["label_vectors"] += 1
            y = np.array(labels, dtype=np.int8)
            for kind in range(4):
                scores = (rng.permutation(n).astype(float) if kind < 2
                          else rng.integers(0, 3, n).astype(float))
                max_buffer = 2 * n + 1
                evaluator = PreparedEvaluator(y, scores, max_buffer, cache_size=max_buffer + 1)
                curves = [evaluator.evaluate(w) for w in range(max_buffer + 1)]
                references = []
                for width, curve in enumerate(curves):
                    expected, segment_count = direct_full_rank_curve(y, scores, width)
                    error = float(np.max(np.abs(expected - [curve.roc, curve.pr])))
                    part["direct_curve_checks"] += 1
                    part["max_curve_absolute_error"] = max(part["max_curve_absolute_error"], error)
                    require(curve.segments == segment_count,
                            f"Segment mismatch for n={n}, y={labels}, pattern={kind}, w={width}")
                    require(error <= CURVE_ATOL,
                            f"Direct curve mismatch for n={n}, y={labels}, pattern={kind}, w={width}: {error}")
                    references.append(expected)
                mean = np.mean(references, axis=0)
                existing_exact = np.asarray(sparse_vus(y, scores, max_buffer))
                mean_error = float(np.max(np.abs(mean - existing_exact)))
                part["mean_comparisons_with_numpy_sparse"] += 1
                part["max_mean_absolute_error"] = max(part["max_mean_absolute_error"], mean_error)
                require(mean_error <= CURVE_ATOL,
                        f"Existing NumPy exact mean mismatch for n={n}, y={labels}: {mean_error}")
                for left, right in evaluator.merge_free_intervals:
                    lower, upper = width_bounds(curves[left], curves[right])
                    for width in range(left, right + 1):
                        value = references[width]
                        violation = max(0.0, float(np.max(np.asarray(lower) - value)),
                                        float(np.max(value - np.asarray(upper))))
                        part["width_enclosures"] += 1
                        part["max_bound_violation"] = max(part["max_bound_violation"], violation)
                        require(violation <= BOUND_ATOL,
                                f"Enclosure failure for n={n}, y={labels}, pattern={kind}, "
                                f"interval=({left},{right}), width={width}: {violation}")
                part["input_cases"] += 1
    require(part["label_vectors"] == 240, "Unexpected label enumeration count")
    require(part["input_cases"] == 960, "Unexpected input case count")
    require(part["direct_curve_checks"] == 13776, "Unexpected direct-curve count")
    require(part["width_enclosures"] == 13776, "Unexpected enclosure count")


def check_counterexamples(report):
    output = {}
    report["counterexamples"] = output

    y = np.zeros(20, dtype=np.int8)
    y[[0, 2, 19]] = 1
    scores = np.array([20, 4, 19, 3, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 2, 1])
    evaluator = PreparedEvaluator(y, scores, 2)
    values = {}
    for width in (1, 2):
        direct, segments = direct_full_rank_curve(y, scores, width)
        curve = evaluator.evaluate(width)
        require(np.max(np.abs(direct - [curve.roc, curve.pr])) <= CURVE_ATOL,
                "ROC counterexample reference mismatch")
        values[str(width)] = dict(roc=float(direct[0]), pr=float(direct[1]), segments=segments)
    require(values["2"]["roc"] < values["1"]["roc"] - .03,
            "Expected ROC decrease across merge was absent")
    require((values["1"]["segments"], values["2"]["segments"]) == (3, 2),
            "Unexpected segment counts in ROC counterexample")
    try:
        width_bounds(evaluator.evaluate(1), evaluator.evaluate(2))
    except ValueError:
        pass
    else:
        raise AssertionError("Cross-merge bound was not rejected")
    output["roc_decrease_at_merge"] = dict(
        n=20, positive_indices=[0, 2, 19], scores=scores.tolist(), values=values,
        cross_merge_bound_rejected=True,
    )

    # Independently derived three-width PR witness.  The first segment merge
    # is at width 402, so all three evaluated widths share the same partition.
    y = np.zeros(700, dtype=np.int8)
    y[100:200] = 1
    y[600] = 1
    scores = np.zeros(700)
    scores[100:150] = 3
    scores[150:200] = scores[600] = 1
    scores[0:100] = scores[200:550] = scores[599] = 2
    evaluator = PreparedEvaluator(y, scores, 400)
    values = {}
    for width in (1, 2, 400):
        direct, segments = direct_full_rank_curve(y, scores, width)
        curve = evaluator.evaluate(width)
        require(np.max(np.abs(direct - [curve.roc, curve.pr])) <= CURVE_ATOL,
                f"PR counterexample reference mismatch at width {width}")
        require(segments == 2 and curve.segments == 2, "Unexpected merge in PR counterexample")
        values[str(width)] = dict(roc=float(direct[0]), pr=float(direct[1]), segments=segments)
    require(values["2"]["pr"] < min(values["1"]["pr"], values["400"]["pr"]) - .01,
            "Expected interior PR value below both endpoint values was absent")
    lower, upper = width_bounds(evaluator.evaluate(1), evaluator.evaluate(400))
    require(lower[1] - BOUND_ATOL <= values["2"]["pr"] <= upper[1] + BOUND_ATOL,
            "P-box failed to enclose PR counterexample")
    ramp, initial_recall = np.sqrt(.5), 25 / 101
    intermediate_recall = (50 + 3 * ramp) / (101 + 1.5 * ramp)
    analytic_pr_1 = initial_recall + (1 - initial_recall) * 101 / 552
    analytic_pr_2 = (initial_recall
                     + (intermediate_recall - initial_recall) * (50 + 3 * ramp) / 501
                     + (1 - intermediate_recall) * (101 + 3 * ramp) / 552)
    analytic_pr_400_lower = initial_recall + (1 - initial_recall) * (50 + 451 * ramp) / 501
    require(abs(values["1"]["pr"] - analytic_pr_1) <= CURVE_ATOL, "PR1 formula mismatch")
    require(abs(values["2"]["pr"] - analytic_pr_2) <= CURVE_ATOL, "PR2 formula mismatch")
    require(values["400"]["pr"] + CURVE_ATOL >= analytic_pr_400_lower, "PR400 analytic lower bound mismatch")
    output["pr_interior_below_both_endpoints_without_merge"] = dict(
        n=700,
        positive_slices_python_half_open=[[100, 200]],
        additional_positive_indices=[600],
        default_score=0,
        score_assignments_python_half_open=[
            {"slice": [100, 150], "score": 3},
            {"slice": [150, 200], "score": 1},
            {"indices": [600], "score": 1},
            {"slice": [0, 100], "score": 2},
            {"slice": [200, 550], "score": 2},
            {"indices": [599], "score": 2},
        ],
        first_merge_width=402,
        values=values,
        pbox_pr_lower=float(lower[1]),
        pbox_pr_upper=float(upper[1]),
        analytic_pr_1=float(analytic_pr_1),
        analytic_pr_2=float(analytic_pr_2),
        analytic_pr_400_lower=float(analytic_pr_400_lower),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="JSON verification receipt")
    args = parser.parse_args()
    started = time.perf_counter()
    source_paths = [
        "experiments/verify_width_theory.py",
        "src/sparse_vus/certified.py",
        "src/sparse_vus/core.py",
    ]
    report = dict(
        schema_version=1,
        status="RUNNING",
        created_utc=datetime.now(timezone.utc).isoformat(),
        seed=SEED,
        source_sha256={path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in source_paths},
        git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        versions=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
        scope="Finite Float64 verification, not a proof of all inputs or formal machine intervals",
        timing_scope="Validation duration only; not a controlled runtime comparison",
    )
    try:
        rng = np.random.default_rng(SEED)
        check_linear_programs(rng, report)
        check_small_labels(rng, report)
        check_counterexamples(report)
        report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = dict(type=type(error).__name__, message=str(error))
    report["elapsed_seconds"] = time.perf_counter() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(status=report["status"], output=str(args.output),
                         elapsed_seconds=report["elapsed_seconds"]), indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
