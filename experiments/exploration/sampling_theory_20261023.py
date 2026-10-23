"""Exploratory, untimed checks of threshold-sampling theory; no production API.

Run from the repository root with PYTHONPATH=src. The receipt is printed to
stdout. No frozen experiment, downloaded source, or cache is overwritten.
"""
from __future__ import annotations

import itertools
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments"))
from fast_vus_adapter import fast_vus_pr
from sparse_vus.core import dense_vus, sampled_vus
from sparse_vus.saturation import sparse_pr_saturation_jit


def scores_for_order(order):
    order = np.asarray(order, dtype=int)
    assert len(set(order)) == len(order)
    out = np.empty(len(order), dtype=float)
    out[order] = np.arange(len(order), 0, -1, dtype=float)
    return out


def curves(y, scores, width):
    """Full complete-tie states, built by direct temporal weights/predictions."""
    n = len(y)
    intervals = []
    for i, yi in enumerate(y):
        if yi and (i == 0 or not y[i - 1]):
            intervals.append([i, i])
        elif yi:
            intervals[-1][1] = i
    weights = np.asarray(y, dtype=float).copy()
    for a, b in intervals:
        for d in range(1, width // 2 + 1):
            for i in (a - d, b + d):
                if 0 <= i < n:
                    weights[i] += math.sqrt(1 - d / width)
    weights = np.minimum(weights, 1)
    expanded = []
    for a, b in intervals:
        a, b = max(0, a - width // 2), min(n - 1, b + width // 2)
        if expanded and expanded[-1][1] >= a:
            expanded[-1][1] = max(expanded[-1][1], b)
        else:
            expanded.append([a, b])
    rows = [[0, 0, 0, 0, 0]]
    for threshold in sorted(set(scores), reverse=True):
        pred = scores >= threshold
        c = int(sum(pred))
        t = float(np.dot(weights, pred))
        bmass = float(np.dot(weights * (1 - y), pred))
        hit = sum(bool(np.any(pred[a:b + 1])) for a, b in expanded)
        recall = min(t / (sum(y) + bmass / 2), 1) * hit / len(expanded)
        rows.append([c, t, recall, bmass, hit])
    return np.asarray(rows)


def sampled_indices(states, n, h):
    counts = 1 + np.linspace(0, n - 1, h).astype(int)
    return np.r_[0, np.searchsorted(states[:, 0], counts)]


def enclose(states, selected, positives):
    lower = upper = 0.0
    for ia, ib in zip(selected[:-1], selected[1:]):
        ca, ta, ra = states[ia, :3]
        cb, tb, rb = states[ib, :3]
        if cb == ca or rb == ra:
            continue
        delta = tb - ta
        lo = ta / (cb - delta) if cb > delta else 1.0
        hi = tb / (ca + delta)
        slope = positives / cb
        cut = min(rb, max(ra, lo / slope))
        lower += lo * (cut - ra) + slope * (rb * rb - cut * cut) / 2
        upper += (rb - ra) * hi
    return lower, upper


def area(states):
    return float(np.diff(states[:, 2]) @ (states[1:, 1] / states[1:, 0]))


def verify_enclosures():
    cases = 0
    worst = 0.0
    rng = np.random.default_rng(20261023)
    fixtures = []
    for n in range(2, 6):
        for labels in itertools.product((0, 1), repeat=n):
            if 0 < sum(labels) < n:
                for score in itertools.product((0, 1), repeat=n):
                    fixtures.append((np.array(labels), np.array(score, dtype=float)))
    for _ in range(500):
        n = int(rng.integers(2, 30))
        y = rng.integers(0, 2, n)
        if not 0 < sum(y) < n:
            y[0], y[-1] = 0, 1
        fixtures.append((y, rng.integers(-3, 4, n).astype(float)))
    for y, s in fixtures:
        for w in (0, 1, 2, 5):
            rows = curves(y, s, w)
            target = area(rows)
            for h in (2, 3, 5):
                chosen = sampled_indices(rows, len(y), h)
                lower, upper = enclose(rows, chosen, int(sum(y)))
                violation = max(lower - target, target - upper, 0)
                worst = max(worst, violation)
                assert violation < 2e-14, (y, s, w, h, target, lower, upper)
                cases += 1
    return {"enclosures_checked": cases, "maximum_roundoff_violation": worst}


def overestimate_case(h, q, m, width, competitor_distance=None):
    n = 1 + (h - 1) * q
    assert 1 <= m < q and width // 2 < n - m
    y = np.zeros(n, dtype=np.int8)
    y[0] = 1
    order = list(range(n - m, n)) + [0] + list(range(1, n - m))
    s = scores_for_order(order)
    exact = sparse_pr_saturation_jit(y, s, width)
    upstream = fast_vus_pr(y, s, width, h)
    # Closed form from only the q-m near-original points present by grid knot2.
    mass_sum = float(width + 1)
    for d in range(1, q - m + 1):
        ws = np.arange(2 * d, width + 1, dtype=float)
        mass_sum += float(np.sqrt(1 - d / ws).sum())
    formula = mass_sum / ((width + 1) * (q + 1))
    assert abs(exact - 1 / (m + 1)) < 2e-13
    assert abs(upstream - formula) < 2e-13
    # A simple finite lower bound, deliberately drops the first 2q widths.
    count = max(0, width - 2 * q + 1)
    harmonic = sum(1 / w for w in range(2 * q, width + 1))
    lower = (count * (q - m + 1) - (q - m) * (q - m + 1) * harmonic / 2)
    lower /= (width + 1) * (q + 1)
    assert formula + 2e-14 >= lower
    result = {"H": h, "q": q, "m": m, "n": n, "L": width,
            "exact": exact, "sampled": upstream, "closed_form": formula,
            "proved_lower_bound": lower, "overestimation": upstream - exact}
    if competitor_distance is not None:
        d = competitor_distance
        far = list(range(n - (q - 1), n))
        assert far[0] > width // 2 and d < far[0]
        front = set([d, 0] + far)
        sb = scores_for_order([d, 0] + far + [i for i in range(n) if i not in front])
        eb = sparse_pr_saturation_jit(y, sb, width)
        ab = fast_vus_pr(y, sb, width, h)
        wb = np.arange(2 * d, width + 1, dtype=float)
        a = np.sqrt(1 - d / wb)
        r = a / (1 + a / 2)
        inactive = min(2 * d, width + 1)
        eb_formula = (inactive / 2 + np.sum(r * a + (1 - r) * (1 + a) / 2)) / (width + 1)
        ab_formula = (inactive / (q + 1) + np.sum(r * a + (1 - r) * (1 + a) / (q + 1))) / (width + 1)
        for labels, score, expected, approx in ((y, s, exact, upstream), (y, sb, eb, ab)):
            assert abs(dense_vus(labels, score, width)[1] - expected) < 2e-13
            assert abs(sampled_vus(labels, score, width, h)[1] - approx) < 2e-13
            assert abs(fast_vus_pr(labels, score, width, n) - expected) < 2e-13
        assert abs(eb - eb_formula) < 2e-13
        assert abs(ab - ab_formula) < 2e-13
        assert eb > exact and upstream > ab
        result["same_label_competitor"] = {
            "distance": d, "exact": eb, "sampled": ab,
            "exact_formula": float(eb_formula), "sampled_formula": float(ab_formula),
            "wrong_selection_regret": eb - exact,
            "sampled_wrong_winner_margin": upstream - ab,
            "dense_and_unmodified_full_threshold_parity": True,
        }
    return result


def rational_large_witness():
    """Prove a finite >.98 overestimate bound without allocating its huge data."""
    q, m, h = 2_000_000, 1000, 250
    width = (h - 1) * q
    # exp(5) > its degree7 Taylor truncation > L/(2q-1), so harmonic<5.
    exp5_lower = sum(Fraction(5 ** j, math.factorial(j)) for j in range(8))
    assert exp5_lower > Fraction(width, 2 * q - 1)
    denominator = (width + 1) * (q + 1)
    lower = Fraction((width - 2 * q + 1) * (q - m + 1), denominator)
    lower -= Fraction(5 * (q - m) * (q - m + 1), 2 * denominator)
    exact = Fraction(1, m + 1)
    assert lower - exact > Fraction(98, 100)
    return {"n": 1 + (h - 1) * q, "L": width, "H": h, "q": q, "m": m,
            "kind": "exact_rational_lower_bound_only_not_an_executed_metric_case",
            "sampled_proved_lower_bound": str(lower),
            "exact_value": str(exact),
            "overestimation_strictly_greater_than_0_98": True}


def indistinguishable_case(h, q, m, width):
    n = 1 + (h - 1) * q
    start = width // 2 + 1
    y = np.zeros(n, dtype=np.int8)
    y[start:start + m] = 1
    original = list(range(start, start + m))
    support = set(range(start - width // 2, start + m + width // 2))
    outside = [i for i in range(n) if i not in support]
    assert len(outside) >= q + 1 - m
    first = outside[:q + 1 - m]
    tail = [i for i in range(n) if i not in set(first + original)]
    sa = scores_for_order(first[:1] + original + first[1:] + tail)
    sb = scores_for_order(first + original + tail)
    same = True
    for w in range(width + 1):
        a, b = curves(y, sa, w), curves(y, sb, w)
        ia = sampled_indices(a, n, h)
        ib = sampled_indices(b, n, h)
        same &= bool(np.array_equal(a[ia], b[ib]))
    ea, eb = dense_vus(y, sa, width)[1], dense_vus(y, sb, width)[1]
    aa, ab = sampled_vus(y, sa, width, h)[1], sampled_vus(y, sb, width, h)[1]
    assert same and aa == ab
    assert abs(ea - sum(j / (j + 1) for j in range(1, m + 1)) / m) < 1e-13
    assert abs(eb - sum(j / (q + 1 - m + j) for j in range(1, m + 1)) / m) < 1e-13
    return {"H": h, "q": q, "m": m, "n": n, "L": width,
            "all_sampled_states_identical": same, "exact_A": ea, "exact_B": eb,
            "sampled_A": aa, "sampled_B": ab, "exact_gap": ea - eb}


if __name__ == "__main__":
    report = {
        "status": "exploratory_theory_checks_not_a_timing_benchmark",
        "sources": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in [Path(__file__).resolve(), ROOT / "src/sparse_vus/core.py",
                                 ROOT / "src/sparse_vus/saturation.py",
                                 ROOT / "experiments/fast_vus_adapter.py",
                                 ROOT / ".cache/fast_vus/fast_vus.py"]},
        "enclosures": verify_enclosures(),
        "indistinguishability": [indistinguishable_case(10, 40, 8, 6),
                                 indistinguishable_case(20, 120, 20, 8)],
        "overestimation": [overestimate_case(250, 10, 3, 30, 5),
                           overestimate_case(250, 20, 4, 100, 5),
                           overestimate_case(250, 40, 6, 300, 1),
                           overestimate_case(10, 40, 4, 350),
                           overestimate_case(250, 8, 2, 1992),
                           overestimate_case(250, 30, 5, 7470)],
        "asymptotic_sampled_lower_bound_H250_Lleqn":
            1 - 2 / 249 - math.log(249 / 2) / (2 * 249),
        "finite_rational_witness": rational_large_witness(),
    }
    print(json.dumps(report, indent=2))
