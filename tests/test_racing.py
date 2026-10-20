"""Incremental PR racing, exact tie handling, and work-reuse checks."""
import numpy as np
import pytest


def api():
    import importlib.util

    assert importlib.util.find_spec("sparse_vus.racing") is not None
    from sparse_vus.racing import PRWidthState, race_pr_models

    return PRWidthState, race_pr_models


def test_state_refines_one_new_width_and_encloses_exact_pr():
    PRWidthState, _ = api()
    from sparse_vus import sparse_vus

    y = np.zeros(40, dtype=int)
    y[12:16] = 1
    scores = np.random.default_rng(300).normal(size=40)
    L = 21
    target = sparse_vus(y, scores, L)[1]
    state = PRWidthState(y, scores, L)
    previous_lower, previous_upper = state.pr_interval
    assert previous_lower - 2e-12 <= target <= previous_upper + 2e-12
    while not state.exact:
        count = state.evaluated_count
        assert state.refine()
        assert state.evaluated_count == count + 1
        lower, upper = state.pr_interval
        assert lower - 2e-12 <= target <= upper + 2e-12
        assert lower >= previous_lower - 2e-12
        assert upper <= previous_upper + 2e-12
        previous_lower, previous_upper = lower, upper
    assert state.exact_pr == pytest.approx(target, abs=2e-12)
    assert state.pr_interval == (state.exact_pr, state.exact_pr)
    assert state.evaluated_count == L + 1
    assert not state.refine()


def test_decisive_race_stops_without_refinement_or_exact_fallback():
    _, race_pr_models = api()
    y = np.zeros(1000, dtype=int)
    y[450:470] = 1
    result = race_pr_models(y, {"poor": -y, "perfect": y}, 100)
    assert result.selected == ("perfect",)
    assert result.early_winner
    assert result.refinement_steps == 0
    assert result.total_unique_widths == 4
    assert result.total_curve_evaluations == result.initial_curve_evaluations == 4
    assert result.full_evaluation_count == 0
    assert result.exact_pr == {}


def test_exact_ties_finish_from_existing_state_and_prune_poor_detector():
    _, race_pr_models = api()
    y = np.zeros(80, dtype=int)
    y[30:35] = 1
    scores = {"b": y, "poor": -y, "a": y}
    result = race_pr_models(y, scores, 12)
    assert result.selected == ("a", "b")
    assert result.candidate_models == ("a", "b")
    assert result.pruned_models == ("poor",)
    assert not result.early_winner
    assert result.full_evaluation_count == 2
    assert tuple(result.exact_pr) == ("a", "b")
    assert result.bounds["poor"].evaluated_widths == (0, 12)
    assert result.refinement_steps == 2 * (13 - 2)
    assert result.total_unique_widths == 2 * 13 + 2


def test_no_pruning_ablation_refines_poor_model_when_ties_remain():
    _, race_pr_models = api()
    y = np.zeros(80, dtype=int)
    y[30:35] = 1
    scores = {"b": y, "poor": -y, "a": y}
    result = race_pr_models(y, scores, 12, prune=False)
    assert result.selected == ("a", "b")
    assert result.pruned_models == ()
    assert result.full_evaluation_count == 3
    assert result.total_unique_widths == 3 * 13


def test_merge_blocks_and_zero_width_can_start_exact():
    PRWidthState, race_pr_models = api()
    state = PRWidthState([1, 0, 1, 0, 0, 1, 0], np.arange(7), 3)
    assert state.exact
    assert state.evaluated_count == 4
    assert state.refinement_steps == 0
    result = race_pr_models([0, 1], {"a": [0., 1.], "b": [0., 1.]}, 0)
    assert result.selected == ("a", "b")
    assert result.full_evaluation_count == 2
    assert result.total_unique_widths == 2


def test_single_detector_does_not_require_all_widths():
    _, race_pr_models = api()
    result = race_pr_models([0, 0, 1, 1, 0, 0], {"only": np.arange(6)}, 20)
    assert result.selected == ("only",)
    assert result.early_winner
    assert result.refinement_steps == 0


@pytest.mark.parametrize("seed", range(40))
def test_incremental_race_matches_exact_all_models(seed):
    _, race_pr_models = api()
    from sparse_vus import sparse_vus

    rng = np.random.default_rng(500 + seed)
    n = int(rng.integers(8, 70))
    y = rng.integers(0, 2, n)
    y[0], y[-1] = 0, 1
    L = int(rng.integers(0, 30))
    scores = {
        "c": rng.normal(size=n),
        "a": rng.integers(0, 4, n),
        "b": rng.normal(size=n) + rng.uniform(0, 2) * y,
    }
    if seed % 5 == 0:
        scores["c"] = scores["a"].copy()
    exact = {name: sparse_vus(y, score, L)[1] for name, score in scores.items()}
    best = max(exact.values())
    expected = tuple(sorted(name for name, value in exact.items() if best - value <= 1e-10))
    result = race_pr_models(y, scores, L)
    reversed_result = race_pr_models(y, dict(reversed(list(scores.items()))), L)
    assert result.selected == reversed_result.selected == expected
    assert result.total_unique_widths == reversed_result.total_unique_widths
    assert result.total_unique_widths <= len(scores) * (L + 1)
    assert result.total_unique_widths == result.initial_unique_widths + result.refinement_steps
    for name, bounds in result.bounds.items():
        assert bounds.pr_lower - 2e-12 <= exact[name] <= bounds.pr_upper + 2e-12


def test_state_snapshot_is_immutable_and_does_not_freeze_future_refinement():
    PRWidthState, _ = api()
    state = PRWidthState([0, 0, 1, 1, 0, 0], np.arange(6), 10)
    before = state.snapshot()
    state.refine()
    after = state.snapshot()
    assert len(after.evaluated_widths) == len(before.evaluated_widths) + 1
    assert before.evaluated_widths == (0, 10)


def test_linear_screening_matches_fixed_policy_for_valid_intervals():
    api()
    from sparse_vus.racing import _screen_race
    from sparse_vus.selection import _screen

    rng = np.random.default_rng(893)
    for count in (1, 2, 3, 10, 50):
        names = tuple(f"model-{i:02d}" for i in range(count))
        for _ in range(10):
            endpoints = np.sort(rng.random((count, 2)), axis=1)
            pairs = dict(zip(names, map(tuple, endpoints)))
            for prune in (False, True):
                assert _screen_race(names, pairs, prune) == _screen(pairs, prune)


@pytest.mark.parametrize("invalid", [{}, [], {1: [0., 1.]}])
def test_rejects_invalid_model_mapping(invalid):
    _, race_pr_models = api()
    with pytest.raises(ValueError, match="mapping"):
        race_pr_models([0, 1], invalid, 0)
