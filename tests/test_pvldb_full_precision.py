import importlib.util
from pathlib import Path
import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1] / "experiments/pvldb_full_precision.py"


def module():
    spec = importlib.util.spec_from_file_location("full_precision_study", PATH)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_score_generation_keeps_full_time_axis_and_is_deterministic():
    # Window alignment, hidden random seeds and output quantization would fail.
    m = module(); x = np.sin(np.arange(80)*.3)+np.arange(80)*.001
    a, _ = m.generate_scores(x); b, _ = m.generate_scores(x)
    assert a.shape == (8, 80) and np.isfinite(a).all()
    np.testing.assert_array_equal(a, b)
    assert np.any(a != np.round(a, 2))
    assert len({row.tobytes() for row in a}) >= 7


def test_constant_signal_retained_without_jitter():
    m = module(); scores, _ = m.generate_scores(np.ones(48))
    assert scores.shape == (8, 48) and np.isfinite(scores).all()
    assert all(len(np.unique(row)) == 1 for row in scores)


@pytest.mark.parametrize("x", [[], [1.], [1, float('nan'), 2], [1, float('inf'), 2]])
def test_nonfinite_or_too_short_input_rejected(x):
    with pytest.raises(ValueError):
        module().generate_scores(x)


def test_winner_policy_retains_near_ties_and_bootstrap_pairs_cases():
    m=module()
    assert m.winners([.5, .5+5e-11, .4]) == [0, 1]
    assert m.winners([.5, .5+2e-10, .4]) == [1]
    stats=m.paired_summary([1,2,3,4],[2,4,6,8],seed=21)
    assert stats["geometric_speedup"] == pytest.approx(2.)
    assert stats["ci95"] == pytest.approx([2.,2.])
