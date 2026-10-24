"""Mathematical invariants for the exploratory paired timing summary."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
sys.path.insert(0, str(EXPERIMENTS))
spec = importlib.util.spec_from_file_location("direct_comparison", EXPERIMENTS / "audit_weighted_direct_comparison.py")
direct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(direct)


def test_paired_common_trial_noise_cancels_exactly():
    candidate = np.arange(1, 145, dtype=float).reshape(2, 12, 6)
    result = direct.direct_summary(4 * candidate, candidate, 4, direct.load_bootstrap(), 20261024, 500)
    assert result["geometric_ratio"] == pytest.approx(4)
    assert result["paired_order95_interval"] == pytest.approx([4, 4])
    assert (result["recording_wins"], result["recording_losses"]) == (2, 0)


def test_opposite_semantic_trial_effects_share_indices():
    control = np.tile([[1., 1, 1, 10, 10, 10], [10., 10, 10, 1, 1, 1]], (1, 6, 1))
    candidate = np.ones_like(control)
    result = direct.direct_summary(control, candidate, 5.5, direct.load_bootstrap(), 20261024, 1000)
    low, high = result["paired_order95_interval"]
    assert low == pytest.approx(np.sqrt(10))
    assert high == pytest.approx(5.5)


def test_wrong_center_or_nonpositive_duration_is_rejected():
    candidate = np.ones((2, 12, 6))
    with pytest.raises(ValueError, match="center differs"):
        direct.direct_summary(candidate, candidate, 2, direct.load_bootstrap(), 20261024, 10)
    candidate[0, 0, 0] = 0
    with pytest.raises(ValueError, match="positive"):
        direct.direct_summary(candidate, candidate, 1, direct.load_bootstrap(), 20261024, 10)
