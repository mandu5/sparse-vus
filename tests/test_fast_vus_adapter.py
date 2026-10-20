"""Parity checks for the unmodified, hash-pinned external fast-VUS code."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
import fast_vus_adapter as adapter
from sparse_vus.core import sampled_vus, sparse_vus


@pytest.mark.parametrize("seed", range(24))
def test_external_fast_vus_matches_full_and_sampled_thresholds(seed):
    rng = np.random.default_rng(926100 + seed)
    n = int(rng.integers(8, 100))
    labels = (rng.random(n) < rng.uniform(.05, .8)).astype(np.int8)
    labels[0], labels[-1] = seed % 2, 1 - seed % 2
    scores = rng.normal(size=n) if seed % 2 else rng.integers(0, 8, n).astype(float)
    width = seed % 13
    assert adapter.fast_vus_pr(labels, scores, width, max_samples=n) == pytest.approx(
        sparse_vus(labels, scores, width)[1], abs=3e-14, rel=0
    )
    assert adapter.fast_vus_pr(labels, scores, width, max_samples=7) == pytest.approx(
        sampled_vus(labels, scores, width, thresholds=7)[1], abs=3e-14, rel=0
    )


@pytest.mark.parametrize(
    "labels,scores,width",
    [
        ([0, 1, 0, 0, 1, 0], [1, 2, 3, 4, 5, 6], 4),
        ([1, 0, 1, 0], [3, 2, 1, 0], 0),
        ([1, 0, 0, 0, 1], [4, 1, 3, 2, 0], 12),
        ([0, 1, 0, 1, 0, 1, 0], [1] * 7, 5),
        ([1, 0, 0, 1, 0, 0, 1], [2, 3, 3, 1, 0, 2, 3], 2),
    ],
)
def test_external_fast_vus_edges_overlaps_and_ties(labels, scores, width):
    assert adapter.fast_vus_pr(labels, scores, width, max_samples=len(labels)) == pytest.approx(
        sparse_vus(labels, scores, width)[1], abs=3e-14, rel=0
    )


def test_default_grid_is_sampled_rather_than_full_threshold():
    labels = np.zeros(1001, dtype=np.int8)
    labels[1] = 1
    scores = np.arange(1001, 0, -1, dtype=float)
    assert adapter.fast_vus_pr(labels, scores, 0) == pytest.approx(.2)
    assert adapter.fast_vus_pr(labels, scores, 0, max_samples=len(labels)) == pytest.approx(.5)


def test_tampered_cached_source_is_rejected(tmp_path, monkeypatch):
    (tmp_path / "fast_vus.py").write_text("raise RuntimeError('must not execute')\n")
    monkeypatch.setattr(adapter, "CACHE", tmp_path)
    adapter._load_module.cache_clear()
    try:
        with pytest.raises(ValueError, match="hash mismatch"):
            adapter.fast_vus_pr([0, 1], [0, 1], 0)
    finally:
        adapter._load_module.cache_clear()
