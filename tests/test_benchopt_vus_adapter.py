"""Parity and integrity checks for the pinned external Benchopt VUS kernel."""
import importlib
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
from sparse_vus.core import sampled_vus, sparse_vus


@pytest.fixture
def adapter():
    assert importlib.util.find_spec("benchopt_vus_adapter") is not None, "Benchopt adapter is missing"
    return importlib.import_module("benchopt_vus_adapter")


@pytest.mark.parametrize("seed", range(8))
def test_external_benchopt_full_and_sampled_thresholds(adapter, seed):
    rng = np.random.default_rng(20261021 + seed)
    n = int(rng.integers(12, 65))
    labels = (rng.random(n) < .35).astype(np.int8)
    labels[0], labels[-1] = seed % 2, 1 - seed % 2
    scores = rng.normal(size=n) if seed % 2 else rng.integers(0, 7, n).astype(float)
    width = seed * 2
    np.testing.assert_allclose(adapter.benchopt_vus(labels, scores, width, max_samples=n),
                               sparse_vus(labels, scores, width), atol=3e-14, rtol=0)
    np.testing.assert_allclose(adapter.benchopt_vus(labels, scores, width, max_samples=7),
                               sampled_vus(labels, scores, width, thresholds=7), atol=3e-14, rtol=0)


@pytest.mark.parametrize("labels,scores,width", [
    ([0, 1, 0, 0, 1, 0], [1, 2, 3, 4, 5, 6], 4),
    ([1, 0, 1, 0], [3, 2, 1, 0], 0),
    ([1, 0, 0, 0, 1], [4, 1, 3, 2, 0], 12),
    ([0, 1, 0, 1, 0, 1, 0], [1] * 7, 5),
    ([1, 0, 0, 1, 0, 0, 1], [2, 3, 3, 1, 0, 2, 3], 2),
])
def test_external_benchopt_edges_overlaps_and_ties(adapter, labels, scores, width):
    np.testing.assert_allclose(adapter.benchopt_vus(labels, scores, width, max_samples=len(labels)),
                               sparse_vus(labels, scores, width), atol=3e-14, rtol=0)


def test_default_grid_does_not_silently_become_exact(adapter):
    labels = np.zeros(1001, dtype=np.int8)
    labels[1] = 1
    scores = np.arange(1001, 0, -1, dtype=float)
    assert adapter.benchopt_vus(labels, scores, 0)[1] == pytest.approx(.2)
    assert adapter.benchopt_vus(labels, scores, 0, max_samples=len(labels))[1] == pytest.approx(.5)


def test_tampered_source_is_rejected_before_execution(adapter, tmp_path, monkeypatch):
    (tmp_path / "metrics.py").write_text("raise RuntimeError('must not execute')\n")
    monkeypatch.setattr(adapter, "CACHE", tmp_path)
    adapter._load_kernel.cache_clear()
    try:
        with pytest.raises(ValueError, match="hash mismatch"):
            adapter.benchopt_vus([0, 1], [0, 1], 0)
    finally:
        adapter._load_kernel.cache_clear()
