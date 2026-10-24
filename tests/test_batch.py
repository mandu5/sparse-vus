"""Batch reuse must preserve the complete scalar operator, not only winners."""
import numpy as np
import pytest

from sparse_vus.batch import batch_pr
from sparse_vus.pr_compiled import dense_pr_direct_jit


@pytest.mark.parametrize("strategy", ["geometry", "stream"])
def test_complete_off_support_tie_and_signed_zero(strategy):
    # Dropping tied negatives or treating -0 as another threshold breaks these.
    actual = batch_pr([0, 1, 0], [[0., -0., 0.], [1., 2., 0.], [3., 2., 1.]], 0,
                      strategy=strategy)
    np.testing.assert_allclose(actual, [1/3, 1., 1/2], rtol=0, atol=1e-15)


@pytest.mark.parametrize("strategy", ["geometry", "stream"])
@pytest.mark.parametrize("width", [0, 1, 2, 5, 12, 30])
def test_boundaries_overlap_and_dense_labels_match_independent_dense(strategy, width):
    # Wrong component IDs, adjacent merging, or double-overlap mass are visible.
    for y in ([1, 1, 0, 0, 0, 1, 1], [0, 1, 0, 1, 0, 1, 0],
              [1, 1, 1, 0, 1, 1, 1], [0, 0, 0, 1, 0, 0, 0]):
        scores = np.asarray([[4, 3, 1, 2, 6, 2, -1], [1]*7, [-3, 0, 1, 6, 3, 4, 2]], float)
        expected = [dense_pr_direct_jit(y, s, width) for s in scores]
        np.testing.assert_allclose(batch_pr(y, scores, width, strategy=strategy),
                                   expected, rtol=0, atol=2e-13)


@pytest.mark.parametrize("strategy", ["geometry", "stream"])
def test_full_precision_and_tied_random_inputs(strategy):
    rng = np.random.default_rng(20261024)
    for n in [3, 17, 63, 127]:
        for repeat in range(8):
            y = rng.integers(0, 2, n); y[0], y[-1] = 0, 1
            scores = rng.normal(size=(4, n))
            if repeat % 2:
                scores = np.round(scores)
            width = int(rng.integers(0, 40))
            expected = [dense_pr_direct_jit(y, s, width) for s in scores]
            np.testing.assert_allclose(batch_pr(y, scores, width, strategy=strategy),
                                       expected, rtol=0, atol=2e-13)


@pytest.mark.parametrize("scores", [[], [1, 2, 3], [[1, 2]],
                                   [[1, 2, 3], [0, np.nan, 1]],
                                   [[1, 2, 3], [0, np.inf, 1]]])
def test_invalid_or_nonfinite_member_is_rejected(scores):
    with pytest.raises(ValueError):
        batch_pr([0, 1, 0], scores, 2)


@pytest.mark.parametrize("labels,width", [([0, 0, 0], 2), ([1, 1, 1], 2),
                                          ([0, .5, 1], 2), ([0, 1, 0], -1),
                                          ([0, 1, 0], 1.5)])
def test_scalar_validation_is_preserved(labels, width):
    with pytest.raises(ValueError):
        batch_pr(labels, [[1, 2, 3]], width)


def test_inputs_unchanged_and_noncontiguous_models_supported():
    y = np.array([0, 1, 0, 0, 1, 0])
    raw = np.arange(36., dtype=float).reshape(6, 6)
    scores = raw.T[::2]
    before = raw.copy(); y_before = y.copy()
    got = batch_pr(y, scores, 6)
    expected = [dense_pr_direct_jit(y, s, 6) for s in scores]
    np.testing.assert_allclose(got, expected, rtol=0, atol=1e-13)
    np.testing.assert_array_equal(raw, before)
    np.testing.assert_array_equal(y, y_before)


def test_unknown_strategy_fails_instead_of_silent_fallback():
    with pytest.raises(ValueError):
        batch_pr([0, 1, 0], [[1, 2, 3]], 2, strategy="fastest")
