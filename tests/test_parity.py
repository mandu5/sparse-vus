"""Tests written before transferring the exploratory implementation."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np
import pytest

from sparse_vus import sparse_vus, dense_vus

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def reference():
    path = ROOT / "cache" / "official_metrics.py"
    if not path.exists():
        pytest.fail("Fetch the pinned reference with python experiments/fetch_reference.py")
    spec = importlib.util.spec_from_file_location("official_metrics", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.metricor()


def case(index):
    # Independently seeded cases remain unchanged if execution is partitioned.
    rng = np.random.default_rng(20261019000 + index)
    n = int(rng.choice([8, 16, 24, 48, 80, 128]))
    y = (rng.random(n) < rng.choice([0.03, 0.1, 0.3, 0.6, 0.9])).astype(int)
    y[0], y[-1] = 0, 1
    mode = index % 5
    s = rng.normal(size=n) if mode == 0 else (
        rng.integers(0, 5, n).astype(float) if mode == 1 else (
        rng.integers(0, 2, n).astype(float) if mode == 2 else (
        np.ones(n) if mode == 3 else np.arange(n, dtype=float))))
    return y, s, int(rng.choice([0, 1, 2, 5, 11, 24, 48]))


@pytest.mark.parametrize("index", range(1000))
def test_random_full_threshold_parity(index, reference):
    y, s, width = case(index)
    expected = reference.RangeAUC_volume_opt(y, s, width, thre=len(y))[-2:]
    np.testing.assert_allclose(sparse_vus(y, s, width), expected, atol=1e-11, rtol=0)
    np.testing.assert_allclose(dense_vus(y, s, width), expected, atol=1e-11, rtol=0)


@pytest.mark.parametrize("y,s,width", [
    ([0,0,1,0,0,0], [4,6,3,2,1,5], 5),
    ([1,1,0,0,0,1,1], [1,0,4,2,6,3,5], 8),
    ([0,1,0,0,1,0,0,0,1,0], [1,2,3,1,5,2,4,3,0,4], 12),
    ([0,1,0,0,1,0], [1,2,3,4,5,6], 2),
    ([0,1,0,0,1,0], [1,1,1,1,1,1], 10),
    ([1,1,1,0,1,1], [5,2,1,3,4,0], 10),
])
def test_structured_edge_cases(y, s, width, reference):
    y, s = np.asarray(y), np.asarray(s, dtype=float)
    expected = reference.RangeAUC_volume_opt(y, s, width, thre=len(y))[-2:]
    np.testing.assert_allclose(sparse_vus(y, s, width), expected, atol=1e-11, rtol=0)
    np.testing.assert_allclose(dense_vus(y, s, width), expected, atol=1e-11, rtol=0)


@pytest.mark.parametrize("y,s,width", [
    ([0,1.5], [0,1], 1), ([0,0], [0,1], 1), ([1,1], [0,1], 1),
    ([0,1], [0,float('nan')], 1), ([0,1], [0,float('inf')], 1),
    ([0,1], [0], 1), ([[0,1]], [[0,1]], 1),
    ([0,1], [0,1], -1), ([0,1], [0,1], 1.5),
])
def test_invalid_input(y, s, width):
    with pytest.raises(ValueError):
        sparse_vus(y, s, width)


@pytest.mark.parametrize("dtype", [np.uint8, np.uint64])
def test_unsigned_score_order(dtype):
    y = np.array([0, 1])
    s = np.array([0, 1], dtype=dtype)
    assert dense_vus(y, s, 0) == (1.0, 1.0)
