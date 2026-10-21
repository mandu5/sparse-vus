"""Executable witnesses for the separately stated mathematical subclasses."""
import numpy as np
import pytest

from sparse_vus.saturation import profile_saturation, sparse_pr_saturation_jit


@pytest.mark.parametrize("n,positives,start", [(9,1,0), (9,1,4), (31,3,14), (64,8,56)])
@pytest.mark.parametrize("ordering", ["original_first", "original_last", "random"])
def test_one_interval_uniform_bound_under_distinct_scores(n, positives, start, ordering):
    y = np.zeros(n, dtype=np.uint8)
    y[start:start+positives] = 1
    rng = np.random.default_rng(20261021 + n + positives)
    permutation = rng.permutation(n)
    if ordering != "random":
        permutation = np.concatenate((permutation[y[permutation] == 0],
                                      permutation[y[permutation] == 1]))
        if ordering == "original_last":
            permutation = permutation[::-1]
    scores = np.empty(n, dtype=np.float64)
    scores[permutation] = np.arange(n, dtype=np.float64)
    profile = profile_saturation(y, scores, 2*n+1)
    maximum = int(np.ceil(2*np.sqrt(2)*positives))
    assert profile["K"] == 1
    assert all(j <= min(q, maximum) for j,q in zip(profile["visited"], profile["active"]))
    if positives == 1:
        assert max(profile["visited"]) <= 3


@pytest.mark.parametrize("n,width", [(4,4), (17,0), (17,8), (17,17)])
def test_unread_off_support_score_changes_every_width_integral(n, width):
    """Adversary witnesses the score-query lower bound; no timing inference."""
    y = np.zeros(n, dtype=np.uint8)
    y[0] = 1
    scores = -np.arange(n, dtype=np.float64)
    scores[0] = 1.0
    assert sparse_pr_saturation_jit(y, scores, width) == 1.0
    outside = range(width//2 + 1, n)
    assert len(outside) >= n/4
    for index in outside:
        changed = scores.copy()
        changed[index] = 2.0
        assert len(np.unique(changed)) == n
        assert sparse_pr_saturation_jit(y, changed, width) == 0.5


@pytest.mark.parametrize("width", [8,32,128])
def test_singleton_ties_defeat_constant_prefix_bound(width):
    n = 2*width+1
    y = np.zeros(n, dtype=np.uint8)
    y[width] = 1
    profile = profile_saturation(y, np.ones(n), width)
    expected = [2*(w//2)+1 for w in range(width+1)]
    assert profile["visited"] == expected
    assert profile["active"] == expected
    assert max(profile["visited"]) > 3
