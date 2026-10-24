"""Direct-ramp control must preserve global ties, overlap clipping and PR."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))


@pytest.mark.parametrize('width', [0, 1, 2, 8, 30, 60])
def test_conventional_compiled_control_matches_direct_definition(width):
    from support_cumsum_control import support_cumsum_pr
    from sparse_vus.pr_compiled import dense_pr_direct_jit
    rng = np.random.default_rng(20261024)
    for _ in range(20):
        y = rng.integers(0, 2, 25, dtype=np.int8)
        y[0], y[1] = 0, 1
        scores = rng.integers(-3, 5, len(y)).astype(float)
        assert support_cumsum_pr(y, scores, width) == pytest.approx(
            dense_pr_direct_jit(y, scores, width), abs=1e-12)


def test_off_support_complete_ties_and_extreme_scores():
    from support_cumsum_control import support_cumsum_pr
    from sparse_vus.pr_compiled import dense_pr_direct_jit
    assert support_cumsum_pr([0, 1, 0, 0], [3., 3., 3., 3.], 0) == pytest.approx(.25)
    x = np.array([-np.finfo(float).max, -0., 0., np.nextafter(0., 1.), np.finfo(float).max])
    y = np.array([0, 1, 0, 1, 0], np.int8)
    for width in (0, 8):
        assert support_cumsum_pr(y, x, width) == pytest.approx(dense_pr_direct_jit(y, x, width), abs=1e-12)
