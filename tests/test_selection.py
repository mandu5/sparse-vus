"""Model-selection policy checks and exact-target integration comparisons."""
import numpy as np
import pytest


def api():
    import importlib.util

    assert importlib.util.find_spec("sparse_vus.selection") is not None
    from sparse_vus.selection import select_pr_model

    return select_pr_model


def test_mapping_must_not_be_empty():
    select_pr_model = api()
    with pytest.raises(ValueError, match="nonempty"):
        select_pr_model([0, 1], {}, 0)


def test_decisive_winner_needs_no_exact_fallback():
    select_pr_model = api()
    y = np.array([0, 0, 1, 1, 0, 0])
    result = select_pr_model(y, {"poor": -y, "good": y}, 0)
    assert result.selected == ("good",)
    assert result.early_winner
    assert result.candidate_models == ("good",)
    assert result.candidate_count == 1
    assert result.pruned_models == ("poor",)
    assert result.exact_fallback_count == 0
    assert result.certified_evaluations == 2
    assert result.certified_curve_evaluations == 2
    assert result.certified_unique_widths == 2
    assert result.exact_pr == {}


def test_tied_survivors_prune_poor_model_before_exact_fallback():
    select_pr_model = api()
    y = np.array([0, 0, 1, 1, 0, 0])
    scores = {"tie-b": y, "poor": -y, "tie-a": y}
    pruned = select_pr_model(y, scores, 0)
    unpruned = select_pr_model(y, scores, 0, prune=False)
    assert pruned.selected == unpruned.selected == ("tie-a", "tie-b")
    assert not pruned.early_winner and not unpruned.early_winner
    assert pruned.candidate_models == ("tie-a", "tie-b")
    assert pruned.exact_fallback_count == pruned.candidate_count == 2
    assert unpruned.exact_fallback_count == unpruned.candidate_count == 3
    assert pruned.pruned_models == ("poor",)
    assert unpruned.pruned_models == ()
    assert tuple(pruned.exact_pr) == ("tie-a", "tie-b")


def test_single_model_is_selected_without_fallback():
    result = api()([0, 1], {"only": [0., 1.]}, 3)
    assert result.selected == ("only",)
    assert result.early_winner
    assert result.exact_fallback_count == 0
    assert result.certified_evaluations == 1


def test_screening_uses_strict_numerical_separation():
    api()
    from sparse_vus.selection import ORDER_MARGIN, _screen

    competitor_upper = .4
    threshold = competitor_upper + ORDER_MARGIN
    at_boundary = {"a": (threshold, .6), "b": (.3, competitor_upper)}
    winner, candidates = _screen(at_boundary, False)
    assert winner is None
    assert candidates == ("a", "b")
    above_boundary = {"a": (np.nextafter(threshold, np.inf), .6), "b": (.3, competitor_upper)}
    winner, candidates = _screen(above_boundary, True)
    assert winner == "a"
    assert candidates == ("a",)


def test_pruning_preserves_models_within_the_guard_margin():
    api()
    from sparse_vus.selection import ORDER_MARGIN, _screen

    best_lower = .5
    prune_threshold = best_lower - ORDER_MARGIN
    bounds = {
        "a": (best_lower, .7),
        "b": (.49, prune_threshold),
        "c": (.48, np.nextafter(prune_threshold, -np.inf)),
        "d": (.49, .6),
    }
    winner, candidates = _screen(bounds, True)
    assert winner is None
    assert candidates == ("a", "b", "d")
    assert _screen(bounds, False) == (None, ("a", "b", "c", "d"))


def test_exact_tie_rule_includes_all_models_within_absolute_tolerance():
    api()
    from sparse_vus.selection import TIE_ATOL, _tied_winners

    # Values at zero avoid introducing subtraction roundoff into the boundary.
    values = {"best": TIE_ATOL, "boundary": 0.0, "middle": TIE_ATOL / 2}
    assert _tied_winners(values) == ("best", "boundary", "middle")
    assert _tied_winners({"best": 2 * TIE_ATOL, "outside": 0.0}) == ("best",)


@pytest.mark.parametrize("seed", range(25))
def test_selection_agrees_with_exact_all_models_and_is_order_independent(seed):
    select_pr_model = api()
    from sparse_vus import sparse_vus

    rng = np.random.default_rng(seed)
    n = int(rng.integers(8, 60))
    y = rng.integers(0, 2, n)
    y[0], y[-1] = 0, 1
    L = int(rng.integers(0, 18))
    scores = {
        "detector-c": rng.normal(size=n),
        "detector-a": rng.integers(0, 4, n),
        "detector-b": rng.normal(size=n) + rng.uniform(0, 2) * y,
    }
    exact = {name: sparse_vus(y, score, L)[1] for name, score in scores.items()}
    maximum = max(exact.values())
    expected = tuple(sorted(name for name, value in exact.items() if maximum - value <= 1e-10))
    result = select_pr_model(y, scores, L)
    reversed_result = select_pr_model(y, dict(reversed(list(scores.items()))), L)
    unpruned = select_pr_model(y, scores, L, prune=False)
    assert result.selected == reversed_result.selected == unpruned.selected == expected
    assert result.candidate_models == reversed_result.candidate_models
    assert result.exact_fallback_count <= unpruned.exact_fallback_count
    assert result.total_models == result.certified_evaluations == 3
    assert result.certified_unique_widths <= 3 * (L + 1)


def test_accepts_compiled_exact_evaluator():
    select_pr_model = api()
    pytest.importorskip("numba")
    from sparse_vus.compiled import sparse_vus_jit

    y = np.array([0, 0, 1, 1, 0, 0])
    scores = {"a": y, "b": y, "poor": -y}
    result = select_pr_model(y, scores, 4, exact_evaluator=sparse_vus_jit)
    assert result.selected == ("a", "b")
    assert result.exact_fallback_count == 2


@pytest.mark.parametrize("bad_scores", [{}, [], {1: [0., 1.]}])
def test_rejects_invalid_model_mapping(bad_scores):
    with pytest.raises(ValueError, match="mapping"):
        api()([0, 1], bad_scores, 0)


def test_rejects_invalid_exact_evaluator_before_model_work():
    with pytest.raises(ValueError, match="exact_evaluator"):
        api()([0, 1], {"a": [0., 1.]}, 0, exact_evaluator=None)
