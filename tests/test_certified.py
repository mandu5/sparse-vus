"""Independent checks of merge-aware width certificates."""
import numpy as np
import pytest


def api():
    # A missing new module is a test assertion failure in the first red run.
    import importlib.util

    assert importlib.util.find_spec("sparse_vus.certified") is not None
    from sparse_vus.certified import PreparedEvaluator, certified_vus, width_bounds

    return PreparedEvaluator, certified_vus, width_bounds


def direct_curve(y, scores, w):
    """Full ranks and direct interval ramps; independent of sparse helpers."""
    y = np.asarray(y, dtype=np.int8)
    scores = np.asarray(scores, dtype=float)
    n, p = len(y), int(y.sum())
    edges = np.diff(np.r_[0, y, 0])
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1) - 1
    weights = y.astype(float)
    segments = []
    for a, b in zip(starts, ends):
        lo, hi = max(0, a - w // 2), min(n - 1, b + w // 2)
        for i in range(lo, a):
            weights[i] += np.sqrt(1 - (a - i) / w)
        for i in range(b + 1, hi + 1):
            weights[i] += np.sqrt(1 - (i - b) / w)
        if segments and lo <= segments[-1][1]:
            segments[-1] = (segments[-1][0], hi)
        else:
            segments.append((lo, hi))
    weights = np.minimum(weights, 1)
    order = np.argsort(-scores, kind="stable")
    last = np.r_[np.flatnonzero(np.diff(scores[order])), n - 1]
    C = last + 1
    T = weights[order].cumsum()[last]
    B = (weights * (1 - y))[order].cumsum()[last]
    H = np.array([sum(np.any(scores[a:b + 1] >= scores[order[k]]) for a, b in segments) for k in last])
    R = np.minimum(T / (p + B / 2), 1) * H / len(segments)
    A = T / C
    F = (C - T) / (n - p - B / 2)
    roc = np.dot(np.diff(np.r_[0, F, 1]), (np.r_[0, R, 1][1:] + np.r_[0, R, 1][:-1]) / 2)
    pr = np.dot(np.diff(np.r_[0, R]), A)
    return np.array([roc, pr])


def test_exact_width_zero_and_one():
    PreparedEvaluator, certified_vus, _ = api()
    y, s = [1, 0, 1, 0], [3, 2, 1, 0]
    evaluator = PreparedEvaluator(y, s, 1)
    assert evaluator.evaluate(0).roc == pytest.approx(.625)
    assert evaluator.evaluate(0).pr == pytest.approx(.75)
    np.testing.assert_array_equal(evaluator.evaluate(0).recall, evaluator.evaluate(1).recall)
    result = certified_vus(y, s, 1, atol=0)
    assert result.exact
    assert result.total_widths == 2
    assert result.evaluated_widths == (0, 1)
    np.testing.assert_allclose(result.estimate, [.625, .75], rtol=0, atol=1e-14)


@pytest.mark.parametrize("seed", range(100))
def test_curves_and_bounds_against_independent_dense(seed):
    PreparedEvaluator, certified_vus, width_bounds = api()
    rng = np.random.default_rng(seed)
    n = int(rng.integers(3, 50))
    y = rng.integers(0, 2, n)
    y[0], y[-1] = 0, 1
    s = rng.integers(-2, 3, n).astype(float) if seed % 3 == 0 else rng.normal(size=n)
    L = int(rng.integers(0, 50))
    evaluator = PreparedEvaluator(y, s, L)
    exact = []
    for w in range(L + 1):
        reference = direct_curve(y, s, w)
        curve = evaluator.evaluate(w)
        np.testing.assert_allclose([curve.roc, curve.pr], reference, rtol=0, atol=2e-13)
        exact.append(reference)
    for a, b in evaluator.merge_free_intervals:
        lower, upper = width_bounds(evaluator.evaluate(a), evaluator.evaluate(b))
        for w in range(a, b + 1):
            assert np.all(exact[w] >= np.asarray(lower) - 2e-12)
            assert np.all(exact[w] <= np.asarray(upper) + 2e-12)
    result = certified_vus(y, s, L, atol=.02)
    mean = np.mean(exact, axis=0)
    assert result.roc_lower - 2e-12 <= mean[0] <= result.roc_upper + 2e-12
    assert result.pr_lower - 2e-12 <= mean[1] <= result.pr_upper + 2e-12
    assert max(result.roc_upper - result.roc_lower, result.pr_upper - result.pr_lower) / 2 <= .02 + 2e-12
    assert len(result.evaluated_widths) <= L + 1
    exact_result = certified_vus(y, s, L, atol=0)
    assert exact_result.exact
    np.testing.assert_allclose(exact_result.estimate, mean, rtol=0, atol=2e-13)


def test_merge_partition_and_unsupported_cross_merge_bound():
    PreparedEvaluator, _, width_bounds = api()
    evaluator = PreparedEvaluator([1, 0, 1, 0, 0, 1, 0], np.arange(7), 10)
    assert evaluator.merge_free_intervals == ((0, 1), (2, 3), (4, 10))
    with pytest.raises(ValueError, match="merge"):
        width_bounds(evaluator.evaluate(1), evaluator.evaluate(4))


def test_adaptive_evaluation_skips_widths_for_separated_detector():
    _, certified_vus, _ = api()
    rng = np.random.default_rng(491)
    n, L = 5000, 300
    y = np.zeros(n, dtype=int)
    y[2400:2440] = 1
    s = rng.normal(size=n) + 4 * y
    result = certified_vus(y, s, L, atol=.01)
    assert not result.exact
    assert len(result.evaluated_widths) < (L + 1) // 4
    # This is an operation-count assertion, not a wall-clock performance claim.
    assert result.curve_evaluations <= 3 * len(result.evaluated_widths)
    assert result.roc_upper - result.roc_lower <= .02 + 2e-12
    assert result.pr_upper - result.pr_lower <= .02 + 2e-12


def test_pbox_extrema_against_independent_linear_program():
    api()
    from sparse_vus.certified import _pbox_extremum

    scipy_optimize = pytest.importorskip("scipy.optimize")
    rng = np.random.default_rng(20261020)
    for G in range(1, 16):
        for _ in range(4):
            r, s = np.sort(rng.random(G - 1)), np.sort(rng.random(G - 1))
            lower, upper = np.r_[np.minimum(r, s), 1.], np.r_[np.maximum(r, s), 1.]
            precision = rng.random(G)
            matrix = np.tril(np.ones((G, G)))
            for maximize in (False, True):
                optimum = scipy_optimize.linprog(
                    -precision if maximize else precision,
                    A_ub=np.vstack([matrix, -matrix]),
                    b_ub=np.r_[upper, -lower],
                    bounds=(0, None),
                    method="highs",
                )
                assert optimum.success
                expected = -optimum.fun if maximize else optimum.fun
                assert _pbox_extremum(lower, upper, precision, maximize) == pytest.approx(expected, abs=1e-10)


@pytest.mark.parametrize("bad_atol", [-1, float("nan"), float("inf")])
def test_rejects_invalid_tolerance(bad_atol):
    _, certified_vus, _ = api()
    with pytest.raises(ValueError, match="atol"):
        certified_vus([0, 1], [0., 1.], 3, atol=bad_atol)


def test_rejects_width_outside_prepared_range():
    PreparedEvaluator, _, _ = api()
    evaluator = PreparedEvaluator([0, 1], [0., 1.], 3)
    for invalid in (-1, 4, 1.5):
        with pytest.raises(ValueError, match="width"):
            evaluator.evaluate(invalid)


def test_pr_decreases_without_merge_but_pbox_bounds_remain_valid():
    PreparedEvaluator, _, width_bounds = api()
    y = np.zeros(30, dtype=int)
    y[[1, 27]] = 1
    scores = [4, 3, 3, 5, 6, 4, 4, 5, 2, 9, 4, 9, 8, 4, 2,
              9, 4, 5, 2, 3, 5, 5, 7, 6, 1, 1, 4, 0, 6, 8]
    evaluator = PreparedEvaluator(y, scores, 18)
    left, middle, right = (evaluator.evaluate(w) for w in (15, 16, 18))
    assert left.segments == middle.segments == right.segments == 2
    assert middle.pr < left.pr - .02
    assert np.all(middle.recall >= left.recall - 1e-14)
    assert np.all(middle.precision >= left.precision - 1e-14)
    lower, upper = width_bounds(left, right)
    assert lower[1] <= direct_curve(y, scores, 16)[1] <= upper[1]


def test_roc_decreases_at_merge_so_global_endpoint_bound_is_rejected():
    PreparedEvaluator, _, width_bounds = api()
    y = np.zeros(20, dtype=int)
    y[[0, 2, 19]] = 1
    scores = [20, 4, 19, 3, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 2, 1]
    evaluator = PreparedEvaluator(y, scores, 2)
    left, right = evaluator.evaluate(1), evaluator.evaluate(2)
    assert (left.segments, right.segments) == (3, 2)
    assert right.roc < left.roc - .03
    assert left.roc == pytest.approx(4 / 9)
    np.testing.assert_allclose([right.roc, right.pr], direct_curve(y, scores, 2), rtol=0, atol=1e-13)
    with pytest.raises(ValueError, match="merge"):
        width_bounds(left, right)
