"""Smoke check an installed wheel in an environment with NumPy but no Numba."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import sparse_vus
from sparse_vus.certified import certified_vus
from sparse_vus.racing import race_pr_models
from sparse_vus.selection import select_pr_model


def main():
    repository = Path(__file__).resolve().parents[1]
    installed = Path(sparse_vus.__file__).resolve()
    if installed.is_relative_to(repository):
        raise AssertionError("Smoke check imported repository source, not an installed wheel")
    if importlib.util.find_spec("numba") is not None:
        raise AssertionError("This check requires the base, NumPy-only installation")
    labels = np.array([0, 1, 0, 0, 1, 0])
    scores = np.arange(1, 7, dtype=float)
    expected = (0.6892652251673258, 0.6834092121537311)
    exact = sparse_vus.sparse_vus(labels, scores, 4)
    np.testing.assert_allclose(exact, expected, rtol=0, atol=1e-12)
    bounds = certified_vus(labels, scores, 4, atol=0)
    np.testing.assert_allclose(bounds.estimate, expected, rtol=0, atol=1e-12)
    assert bounds.exact and bounds.evaluated_count == 5
    models = {"good": labels.astype(float), "poor": -labels.astype(float)}
    reference = {name: sparse_vus.dense_vus(labels, score, 4)[1]
                 for name, score in models.items()}
    target = tuple(sorted(name for name, value in reference.items()
                          if max(reference.values()) - value <= 1e-10))
    assert select_pr_model(labels, models, 4).selected == target
    assert race_pr_models(labels, models, 4).selected == target
    print(f"PASS: installed NumPy-only wheel at {installed}")


if __name__ == "__main__":
    main()
