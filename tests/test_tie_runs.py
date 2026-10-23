"""Independent correctness and work witnesses for the one-interval extension."""
import itertools
import math

import numpy as np
import pytest

from sparse_vus.compiled import dense_vus_direct_jit


def candidate():
    from sparse_vus.tie_runs import interval_vus_tie_runs_jit
    return interval_vus_tie_runs_jit


def check(y, scores, width):
    expected = dense_vus_direct_jit(y, scores, width)
    np.testing.assert_allclose(candidate()(y, scores, width), expected,
                               rtol=0, atol=1e-11)


def test_all_tied_singleton_matches_dense():
    check(np.array([0, 0, 1, 0, 0]), np.ones(5), 16)


def test_exhaustive_small_interval_labels_and_binary_scores():
    for n in range(2, 6):
        for a in range(n):
            for b in range(a, n):
                if a == 0 and b == n-1:
                    continue
                y = np.zeros(n, dtype=np.uint8)
                y[a:b+1] = 1
                for values in itertools.product((-1., 1.), repeat=n):
                    check(y, np.asarray(values), 2*n+1)


@pytest.mark.parametrize('width', [0, 1, 2, 3, 8, 41, 4096])
def test_boundary_interval_and_offsupport_global_ties(width):
    y = np.array([1, 1, 0, 0, 0, 0, 0, 0])
    for scores in (np.ones(8), np.array([0., 1., 2., 0., 2., 1., 1., 2.])):
        check(y, scores, width)


@pytest.mark.parametrize('scores', [
    np.array([-0., 0., -1., 1., -0., 2.]),
    np.array([-np.finfo(float).max, np.finfo(float).max, 0.,
              np.nextafter(0., 1.), -np.nextafter(0., 1.), 1.]),
    np.array([2**60, 2**60+1, 2**60+2, 0, -1, 2**60+3], dtype=np.int64),
])
def test_conversion_and_extreme_scores(scores):
    check(np.array([0, 1, 1, 0, 0, 0]), scores, 20)


def test_random_tied_spatial_runs_and_fragmented_groups():
    rng = np.random.default_rng(202610231)
    for _ in range(140):
        n = int(rng.integers(8, 300))
        a = int(rng.integers(n-1))
        b = int(rng.integers(a, n-1))
        y = np.zeros(n, dtype=np.uint8)
        y[a:b+1] = 1
        scores = rng.integers(-4, 5, size=n).astype(float)
        if rng.random() < .5:
            scores = np.repeat(scores[::7], 7)[:n]
        check(y, scores, int(rng.integers(0, 2*n+5)))


@pytest.mark.parametrize('y,scores,width', [
    ([1, 0, 1], [1., 2., 3.], 3),
    ([0, 0], [0., 1.], 2), ([1, 1], [0., 1.], 2),
    ([0, 1], [0., np.nan], 2), ([0, 1], [0., np.inf], 2),
    ([0, 1], [0.], 2), ([0, 1], [0., 1.], -1),
])
def test_invalid_inputs_and_multiple_intervals_rejected(y, scores, width):
    with pytest.raises((ValueError, TypeError)):
        candidate()(y, scores, width)


def test_fixed_point_prefix_and_queries_match_integer_oracle():
    from sparse_vus.tie_runs import _sqrt_prefix, _sqrt_range
    table = _sqrt_prefix(10000)
    total = 0
    for j in range(10001):
        if j:
            p, q = math.sqrt(j).as_integer_ratio()
            total += (p << 52) // q
        limbs = sum(int(table[k, j]) << (64*k) for k in range(3))
        assert limbs == total
    for lo, hi in [(1, 10000), (9999, 10000), (5000, 5000), (27, 927)]:
        expected = math.fsum(math.sqrt(j) for j in range(lo, hi+1))
        assert _sqrt_range(table, lo, hi) == pytest.approx(expected, rel=5e-16)


def test_high_limb_and_chained_borrow_preserve_range_sum():
    from sparse_vus.tie_runs import _sqrt_range
    pairs = [(2**64-1, 2**64), (2**64+18, 2**128+17),
             (2**128-1, 2**128), (2**128+2**64+1, 2**147-1)]
    rng = np.random.default_rng(202610235)
    for _ in range(100):
        left = sum(int(v) << (32*k) for k, v in enumerate(rng.integers(0, 2**32, 4)))
        right = left + sum(int(v) << (32*k) for k, v in enumerate(rng.integers(1, 2**32, 4)))
        pairs.append((left, right))
    mask = 2**64-1
    for left, right in pairs:
        table = np.zeros((3, 3), dtype=np.uint64)
        for j, value in ((1, left), (2, right)):
            for k in range(3):
                table[k, j] = (value >> (64*k)) & mask
        expected = math.ldexp(float(right-left), -52)
        actual = _sqrt_range(table, 2, 2)
        assert abs(actual-expected) <= 2*math.ulp(expected)


def test_all_tied_work_depends_on_runs_not_tie_cardinality():
    from sparse_vus.tie_runs import profile_tie_runs
    for width in (32, 128, 512):
        y = np.zeros(2*width+1, dtype=np.uint8)
        y[width] = 1
        profile = profile_tie_runs(y, np.ones(len(y)), width)
        assert profile['events'] == [1] * (width+1)
        assert profile['run_queries'] == [1] * (width+1)
        assert profile['positions_aggregated'] == [1+2*(w//2) for w in range(width+1)]
        assert profile['groups'] == profile['runs'] == 1


def test_integer_stop_bound_and_pr_route():
    from sparse_vus.tie_runs import profile_tie_runs, interval_pr_tie_runs_jit
    rng = np.random.default_rng(202610232)
    for p in (1, 3, 8):
        y = np.zeros(90, dtype=np.uint8)
        y[35:35+p] = 1
        scores = rng.integers(-10, 11, 90).astype(float)
        result = profile_tie_runs(y, scores, 80)
        assert max(result['events']) <= 3*p
        assert interval_pr_tie_runs_jit(y, scores, 80) == pytest.approx(
            result['values']['pr'], abs=1e-15)
        check(y, scores, 80)
