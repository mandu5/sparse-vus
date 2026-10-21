"""Exact-selection contract, enclosures and bounded work for PR engine."""
import importlib.util
import numpy as np
import pytest


def api():
    assert importlib.util.find_spec("sparse_vus.fast_racing") is not None
    from sparse_vus.fast_racing import race_pr_models_fast
    return race_pr_models_fast


@pytest.mark.parametrize("seed", range(60))
@pytest.mark.parametrize("budget", [0.0, 0.125, 1.0])
def test_matches_exact_winner_set_and_encloses_all_models(seed, budget):
    race = api()
    from sparse_vus import sparse_vus
    rng = np.random.default_rng(61000 + seed)
    n = int(rng.integers(6, 90))
    y = rng.integers(0, 2, n)
    if seed % 3 == 0:
        y[:] = 0
        y[n//2:n//2 + 2] = 1
    y[0], y[-1] = 0, 1
    width = int(rng.integers(0, 50))
    scores = {"a": rng.normal(size=n), "b": rng.integers(0, 4, n),
              "c": rng.normal(size=n) + y}
    if seed % 5 == 0:
        scores["c"] = scores["a"].copy()
    exact = {k: sparse_vus(y, s, width)[1] for k, s in scores.items()}
    best = max(exact.values())
    expected = tuple(sorted(k for k, v in exact.items() if best - v <= 1e-10))
    result = race(y, scores, width, adaptive_fraction=budget)
    assert result.selected == expected
    assert result.total_curve_evaluations == result.total_unique_widths
    assert result.adaptive_curve_evaluations + result.completion_curve_evaluations == result.total_curve_evaluations
    assert result.total_unique_widths <= len(scores) * (width + 1)
    for name, bound in result.bounds.items():
        assert bound.pr_lower - 2e-12 <= exact[name] <= bound.pr_upper + 2e-12
        assert bound.curve_evaluations == len(bound.evaluated_widths)


def test_separated_models_stop_early():
    race = api()
    y = np.zeros(1000, dtype=int)
    y[450:470] = 1
    result = race(y, {"poor": -y, "perfect": y}, 100)
    assert result.selected == ("perfect",)
    assert result.total_unique_widths == 4
    assert result.adaptive_curve_evaluations == 4
    assert result.completion_curve_evaluations == 0
    assert result.fallback_models == ()


def test_exact_survivor_tie_is_not_an_early_unique_winner():
    race = api()
    y = np.zeros(80, dtype=int)
    y[30:35] = 1
    result = race(y, {"a": y, "b": y, "poor": -y}, 40)
    assert result.selected == ("a", "b")
    assert result.total_unique_widths < 3 * 41
    assert not result.early_winner


def test_small_memory_budget_finishes_exact_without_duplicate_work():
    race = api()
    y = np.zeros(90, dtype=int)
    y[30:35] = 1
    scores = np.arange(90.)
    result = race(y, {"a": scores, "b": scores}, 40, memory_bytes=1)
    assert result.selected == ("a", "b")
    assert result.total_unique_widths == 82
    assert result.total_curve_evaluations == 82
    assert result.adaptive_curve_evaluations == 0
    assert result.completion_curve_evaluations == 82
    assert result.retained_curve_bytes <= 1
    assert result.fallback_models == ("a", "b")


def test_single_model_and_zero_width():
    race = api()
    assert race([0, 1], {"only": [0., 1.]}, 0).selected == ("only",)
    result = race([0, 1], {"a": [1., 1.], "b": [1., 1.]}, 0)
    assert result.selected == ("a", "b")
    assert result.total_unique_widths == 2


def test_fused_bounds_equal_two_independent_pbox_passes():
    import sparse_vus.fast_racing as fast
    from sparse_vus.certified import PreparedEvaluator, width_bounds
    assert hasattr(fast, "_pr_bounds")
    rng = np.random.default_rng(74622)
    for seed in range(20):
        y = np.zeros(100, dtype=int)
        y[20:25] = 1
        y[70:72] = 1
        scores = rng.integers(0, 15, len(y)) if seed % 2 else rng.normal(size=len(y))
        state = PreparedEvaluator(y, scores, 80)
        for left, right in state.merge_free_intervals:
            a, b = state.evaluate(left), state.evaluate(right)
            if left == right:
                continue
            lo, hi = width_bounds(a, b)
            actual = fast._pr_bounds(np.array([a.recall, a.precision]),
                                     np.array([b.recall, b.precision]))
            np.testing.assert_allclose(actual, [lo[1], hi[1]], rtol=0, atol=2e-14)


@pytest.mark.parametrize("kwargs", [{"adaptive_fraction": -1}, {"adaptive_fraction": 2},
                                     {"adaptive_fraction": float("nan")},
                                     {"memory_bytes": -1}, {"memory_bytes": 1.5}])
def test_rejects_invalid_resource_budgets(kwargs):
    race = api()
    with pytest.raises(ValueError):
        race([0, 1], {"a": [0., 1.]}, 0, **kwargs)


@pytest.mark.parametrize("seed", range(12))
@pytest.mark.parametrize("budget", [0.0, 0.125, 1.0])
def test_radix_preparation_preserves_race_decisions_and_accounting(seed, budget):
    rng = np.random.default_rng(93100 + seed)
    y = np.zeros(125, dtype=int)
    y[20:24] = 1
    y[80:84] = 1
    scores = {"a": rng.normal(size=len(y)), "b": rng.integers(-2, 4, len(y)),
              "c": rng.normal(size=len(y)) + y}
    if seed % 3 == 0:
        scores["c"] = scores["a"].copy()
    kwargs = dict(adaptive_fraction=budget)
    baseline = api()(y, scores, 50, preparation="histogram", **kwargs)
    actual = api()(y, scores, 50, preparation="radix", **kwargs)
    assert actual == baseline


@pytest.mark.parametrize("preparation", [None, "stable", [], 42])
def test_rejects_unknown_preparation(preparation):
    with pytest.raises(ValueError, match="preparation"):
        api()([0, 1], {"a": [0., 1.]}, 0, preparation=preparation)
