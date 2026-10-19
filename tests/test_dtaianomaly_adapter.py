"""Third-party metric audit, requiring the pinned reference download."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from dtaianomaly_adapter import dtaianomaly_vus
from sparse_vus.core import sparse_vus, sampled_vus


@pytest.mark.parametrize('seed', range(24))
def test_pinned_third_party_matches_exact_and_sampled(seed):
    rng = np.random.default_rng(527100 + seed)
    n = int(rng.integers(10, 100))
    labels = (rng.random(n) < rng.uniform(.05, .8)).astype(np.int8)
    labels[0], labels[-1] = 0, 1
    scores = rng.normal(size=n) if seed % 2 else rng.integers(0, 8, size=n).astype(float)
    width = seed % 13
    np.testing.assert_allclose(dtaianomaly_vus(labels, scores, width, n),
                               sparse_vus(labels, scores, width), atol=3e-14, rtol=0)
    np.testing.assert_allclose(dtaianomaly_vus(labels, scores, width, 7),
                               sampled_vus(labels, scores, width, thresholds=7), atol=3e-14, rtol=0)
