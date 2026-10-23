"""Independent sampled-target parity; no generated expected metric values."""
import numpy as np
import pytest

pytest.importorskip("numba")
from sparse_vus.core import dense_vus
from sparse_vus.sampling import sampled_pr_radix_jit


@pytest.mark.parametrize("width", [0, 1, 2, 7, 30])
@pytest.mark.parametrize("budget", [2, 3, 11, 250])
def test_complete_ties_boundaries_and_overlap(width, budget):
    y = np.array([1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1])
    scores = np.array([0., -0., 3., 2., 2., -1., 1., 0., 2., 3., -2.])
    assert sampled_pr_radix_jit(y, scores, width, budget) == pytest.approx(
        dense_vus(y, scores, width, thresholds=budget)[1], abs=2e-14)


@pytest.mark.parametrize("seed", range(20))
def test_random_tied_and_distinct(seed):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, 37)
    y[:2] = [0, 1]
    scores = rng.normal(size=len(y))
    if seed % 2:
        scores = np.round(scores, 0)
    for width in (0, 8, 31):
        for budget in (2, 7, 37, 250):
            assert sampled_pr_radix_jit(y, scores, width, budget) == pytest.approx(
                dense_vus(y, scores, width, thresholds=budget)[1], abs=2e-14)


def test_all_score_tie():
    y = np.array([0, 1, 1, 0, 0, 0, 1])
    for budget in (2, 250):
        assert sampled_pr_radix_jit(y, np.ones(7), 30, budget) == pytest.approx(
            dense_vus(y, np.ones(7), 30, thresholds=budget)[1], abs=2e-14)


def test_unchanged_external_reference():
    from experiments.fast_vus_adapter import fast_vus_pr, CACHE
    if not (CACHE / "fast_vus.py").exists():
        pytest.skip("optional pinned upstream cache absent")
    rng = np.random.default_rng(32023)
    y = rng.integers(0, 2, 53)
    scores = np.round(rng.normal(size=53), 1)
    for width in (0, 30):
        for budget in (2, 7, 53, 250):
            assert sampled_pr_radix_jit(y, scores, width, budget) == pytest.approx(
                fast_vus_pr(y, scores, width, budget), abs=2e-14)


def test_post_saturation_overestimation_closed_form():
    n, q, m, width = 2491, 10, 3, 30
    y = np.zeros(n, dtype=np.int8)
    y[0] = 1
    order = np.r_[np.arange(n-m, n), np.arange(n-m)]
    scores = np.empty(n)
    scores[order] = np.arange(n, 0, -1)
    expected = np.mean([
        (1 + sum(np.sqrt(1-d/w) for d in range(1, min(q-m, w//2)+1))) / (q+1)
        for w in range(width+1)
    ])
    assert sampled_pr_radix_jit(y, scores, width) == pytest.approx(expected, abs=2e-14)
    assert expected > 0.5


@pytest.mark.parametrize("budget", [0, 1, -2, 2.5, True, "250"])
def test_invalid_budget(budget):
    with pytest.raises(ValueError, match="thresholds"):
        sampled_pr_radix_jit([0, 1], [1., 0.], 0, budget)


def test_invalid_inputs_preserve_public_contract():
    with pytest.raises(ValueError, match="finite"):
        sampled_pr_radix_jit([0, 1], [np.nan, 1.], 0)
    with pytest.raises(ValueError, match="both classes"):
        sampled_pr_radix_jit([1, 1], [0., 1.], 0)
