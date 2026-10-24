import importlib.util
from pathlib import Path

import numpy as np
import pytest


def load_module():
    path = Path(__file__).resolve().parents[1] / "experiments/pvldb_supplement.py"
    spec = importlib.util.spec_from_file_location("supplement", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selection_loss_measures_the_selected_model_on_exact_values():
    assess = load_module().selection_loss
    result = assess([.9, .7, .6], [.8, .81, .2])
    assert result["selected"] == [1]
    assert result["minimum_regret"] == pytest.approx(.2)
    assert result["maximum_regret"] == pytest.approx(.2)
    assert result["identical_winner_set"] is False


def test_approximate_ties_report_best_and_worst_possible_loss():
    assess = load_module().selection_loss
    result = assess([.9, .7, .6], [.8, .8 + 5e-11, .1])
    assert result["selected"] == [0, 1]
    assert result["minimum_regret"] == 0
    assert result["maximum_regret"] == pytest.approx(.2)
    assert result["identical_winner_set"] is False


def test_identical_scores_and_single_model_have_zero_regret():
    assess = load_module().selection_loss
    for values in ([.5], [.5, .5], [.2, .6, .3]):
        result = assess(values, values)
        assert result["minimum_regret"] == result["maximum_regret"] == 0
        assert result["identical_winner_set"] is True


@pytest.mark.parametrize("exact,approx", [([], []), ([.5], [.2, .3]), ([np.nan], [.2])])
def test_bad_selection_inputs_rejected(exact, approx):
    with pytest.raises(ValueError):
        load_module().selection_loss(exact, approx)
