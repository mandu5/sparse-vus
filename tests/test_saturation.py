"""Independent semantic tests for the active-prefix evaluator."""
import itertools

import numpy as np
import pytest

from sparse_vus.compiled import dense_vus_direct_jit


def functions():
    from sparse_vus.saturation import (
        sparse_pr_saturation_jit, sparse_vus_saturation_jit,
    )
    return sparse_pr_saturation_jit, sparse_vus_saturation_jit


def check_case(y, scores, width):
    pr, both = functions()
    expected = dense_vus_direct_jit(y, scores, width)
    np.testing.assert_allclose(both(y, scores, width), expected, rtol=0, atol=1e-11)
    assert pr(y, scores, width) == pytest.approx(expected[1], rel=0, abs=1e-11)


def test_perfect_singleton_preserves_full_curve_area():
    y = np.array([0, 0, 1, 0, 0], dtype=np.int8)
    scores = np.array([1., 2., 9., 0., -1.])
    check_case(y, scores, 10)


@pytest.mark.parametrize("width", [0, 1, 2, 3, 4, 5, 6, 14])
def test_complete_ties_and_component_merge_boundaries(width):
    # The middle of a tie must never be treated as a complete threshold.
    y = np.array([0, 1, 0, 0, 0, 0, 1, 0], dtype=np.int8)
    for scores in (np.ones(8), np.array([3., 3., 3., 0., 0., 2., 2., 2.]),
                   np.array([0., 2., 3., 3., 3., 3., -9., 0.])):
        check_case(y, scores, width)


def test_mass_saturation_does_not_replace_component_coverage():
    y = np.zeros(60, dtype=np.int8)
    y[[10, 50]] = 1
    scores = -np.arange(60, dtype=np.float64)
    scores[6:15] += 200
    scores[50] = -1000
    check_case(y, scores, 16)


def test_exhaustive_small_binary_labels_and_tied_scores():
    for n in range(2, 5):
        for labels in itertools.product((0, 1), repeat=n):
            if not 0 < sum(labels) < n:
                continue
            y = np.asarray(labels, dtype=np.int8)
            for values in itertools.product((0., 1.), repeat=n):
                check_case(y, np.asarray(values), 2 * n + 1)


def test_randomized_full_width_direct_reference():
    rng = np.random.default_rng(2026102111)
    for _ in range(120):
        n = int(rng.integers(6, 160))
        y = (rng.random(n) < rng.uniform(.02, .8)).astype(np.int8)
        y[0], y[-1] = 0, 1
        scores = rng.integers(-6, 7, size=n).astype(np.float64)
        if rng.random() < .5:
            scores += rng.random(n)
        check_case(y, scores, int(rng.integers(0, 2 * n + 5)))


@pytest.mark.parametrize("scores", [
    np.array([-0., 0., -1., 1., -0., 2.]),
    np.array([-np.finfo(float).max, np.finfo(float).max, 0.,
              np.nextafter(0., 1.), -np.nextafter(0., 1.), 1.]),
    np.array([2**60, 2**60 + 1, 2**60 + 2, 0, -1, 2**60 + 3], dtype=np.int64),
])
def test_binary64_input_semantics(scores):
    check_case(np.array([0, 1, 0, 1, 0, 0], dtype=np.int8), scores, 20)


@pytest.mark.parametrize("y,scores,width", [
    ([0, 0], [0., 1.], 2), ([1, 1], [0., 1.], 2),
    ([0, 1], [0., np.nan], 2), ([0, 1], [0., np.inf], 2),
    ([0, 1], [0.], 2), ([0, 1], [0., 1.], -1),
])
def test_invalid_inputs_rejected(y, scores, width):
    for fn in functions():
        with pytest.raises((ValueError, TypeError)):
            fn(y, scores, width)


def test_profile_separation_and_all_stop_ablations():
    from sparse_vus.saturation import profile_saturation
    y = np.zeros(1001, dtype=np.int8)
    y[500] = 1
    scores = np.zeros(1001)
    scores[500] = 1
    early = profile_saturation(y, scores, 500)
    late = profile_saturation(y, scores, 500, stop=False)
    assert early['Q'] == 501
    assert early['K'] == 1
    assert early['visited'] == [1] * 501
    assert late['visited'] == late['active']
    assert sum(early['visited']) < sum(late['visited']) / 100
    assert early['values'] == pytest.approx(late['values'], abs=1e-11)


def test_buffer_saturation_precedes_last_original_positive():
    from sparse_vus.saturation import profile_saturation
    y = np.zeros(25, dtype=np.int8)
    y[[5, 18]] = 1
    scores = np.zeros(25)
    scores[[5, 4, 6, 17, 18]] = [10, 9, 8, 7, -10]
    early = profile_saturation(y, scores, 6)
    last = profile_saturation(y, scores, 6, stop='last_positive')
    full = profile_saturation(y, scores, 6, stop=False)
    assert early['visited'][6] < last['visited'][6]
    for actual in (early, last, full):
        np.testing.assert_allclose(list(actual['values'].values()),
                                   dense_vus_direct_jit(y, scores, 6), atol=1e-11, rtol=0)


@pytest.mark.parametrize('stop', [False, 'last_positive'])
def test_stop_controls_preserve_independent_reference(stop):
    pr, both = functions()
    rng = np.random.default_rng(2026102112)
    for _ in range(40):
        y = rng.integers(0, 2, size=70, dtype=np.int8)
        y[0], y[-1] = 0, 1
        scores = rng.integers(-4, 5, size=70).astype(float)
        width = int(rng.integers(0, 150))
        expected = dense_vus_direct_jit(y, scores, width)
        np.testing.assert_allclose(both(y, scores, width, stop=stop), expected,
                                   atol=1e-11, rtol=0)
        assert pr(y, scores, width, stop=stop) == pytest.approx(expected[1], abs=1e-11)
