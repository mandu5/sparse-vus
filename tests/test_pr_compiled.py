"""PR-only controls must preserve the pinned metric, not just model winners."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
ORACLE_SHA256 = "bd547c9746fc1b9bbce2895e20cb156f97d23365d5dce8c2a3fab90622ccdced"
METHODS = ("sparse_pr_jit", "dense_pr_direct_jit")


def module():
    assert importlib.util.find_spec("sparse_vus.pr_compiled") is not None, "PR-only controls are missing"
    return importlib.import_module("sparse_vus.pr_compiled")


@pytest.fixture(scope="module")
def oracle():
    path = ROOT / "cache/official_metrics.py"
    assert path.is_file(), "Run python experiments/fetch_reference.py first"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ORACLE_SHA256
    spec = importlib.util.spec_from_file_location("pr_control_pinned_oracle", path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded.metricor()


@pytest.mark.parametrize("method", METHODS)
def test_all_tied_at_width_zero_is_prevalence(method):
    # Processing tied scores separately would make this depend on point order.
    result = getattr(module(), method)([0, 1], [4, 4], 0)
    assert type(result) is float
    assert result == .5


@pytest.mark.parametrize("method", METHODS)
def test_documented_example_returns_pr_not_roc(method):
    result = getattr(module(), method)([0, 1, 0, 0, 1, 0], [1, 2, 3, 4, 5, 6], 4)
    assert result == pytest.approx(0.6834092121537311, rel=0, abs=1e-12)


@pytest.mark.parametrize("width", range(15))
@pytest.mark.parametrize("labels,scores", [
    # Odd/even gaps exercise adjacency, first overlap and interval merging.
    ([0, 1, 0, 0, 1, 0, 0, 0], [7, 2, 3, 2, 1, 6, 4, 0]),
    ([0, 1, 0, 0, 0, 1, 0, 0], [0, 3, 1, 7, 2, 3, 6, 4]),
    # Boundary labels and widths beyond the sequence must clip expansions.
    ([1, 1, 0, 0, 0, 1, 1], [1, 0, 4, 2, 6, 3, 5]),
    # Every threshold is tied; dynamic buffer mass still changes with width.
    ([0, 1, 0, 0, 1, 0], [1, 1, 1, 1, 1, 1]),
    # Dense positives catch overlap sum-and-clip and dynamic positive mass.
    ([1, 1, 1, 0, 1, 1], [5, 2, 1, 3, 4, 0]),
])
def test_every_small_width_matches_pinned_reference(labels, scores, width, oracle):
    labels, scores = np.asarray(labels), np.asarray(scores, dtype=float)
    expected = oracle.RangeAUC_volume_opt(labels, scores, width, thre=len(labels))[-1]
    for method in METHODS:
        actual = getattr(module(), method)(labels, scores, width)
        assert actual == pytest.approx(expected, rel=0, abs=1e-11)


@pytest.mark.parametrize("seed", range(60))
def test_independently_seeded_orders_ties_and_density_against_oracle(seed, oracle):
    rng = np.random.default_rng(20261021000 + seed)
    size = int(rng.choice([7, 17, 31, 63]))
    labels = (rng.random(size) < rng.choice([.05, .3, .8])).astype(np.int8)
    labels[0], labels[-1] = 0, 1
    if seed % 3 == 0:
        scores = rng.normal(size=size)
    elif seed % 3 == 1:
        scores = rng.integers(-2, 4, size=size).astype(float)
    else:
        scores = rng.integers(0, 2, size=size).astype(float)
    width = int(rng.choice([0, 1, 2, 7, 16, 40]))
    expected = oracle.RangeAUC_volume_opt(labels, scores, width, thre=size)[-1]
    for method in METHODS:
        actual = getattr(module(), method)(labels, scores, width)
        assert actual == pytest.approx(expected, rel=0, abs=1e-11)


@pytest.mark.parametrize("method", METHODS)
def test_strided_unsigned_inputs_are_converted_without_mutation(method, oracle):
    labels = np.array([0, 9, 1, 9, 0, 9, 1, 9, 0, 9], dtype=np.uint8)[::2]
    scores = np.array([0, 99, 2, 99, 4, 99, 2, 99, 1, 99], dtype=np.uint64)[::2]
    original_labels, original_scores = labels.copy(), scores.copy()
    expected = oracle.RangeAUC_volume_opt(labels.copy(), scores.astype(float), 8, thre=len(labels))[-1]
    result = getattr(module(), method)(labels, scores, np.int64(8))
    assert result == pytest.approx(expected, rel=0, abs=1e-11)
    np.testing.assert_array_equal(labels, original_labels)
    np.testing.assert_array_equal(scores, original_scores)


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("labels,scores,width", [
    ([0, 1.5], [0, 1], 1), ([0, 0], [0, 1], 1), ([1, 1], [0, 1], 1),
    ([0, 1], [0, float("nan")], 1), ([0, 1], [0, float("inf")], 1),
    ([0, 1], [0], 1), ([[0, 1]], [[0, 1]], 1),
    ([0, 1], [0, 1], -1), ([0, 1], [0, 1], 1.5),
])
def test_invalid_inputs_do_not_enter_compiled_kernels(method, labels, scores, width):
    with pytest.raises(ValueError):
        getattr(module(), method)(labels, scores, width)


def test_exact_completion_fills_only_unknown_widths_and_reports_actual_work(oracle):
    from sparse_vus.core import _prepare

    labels = np.array([0, 1, 0, 0, 0, 1, 0], dtype=np.int8)
    scores = np.array([7., 2., 5., 2., 1., 4., 6.])
    width = 9
    prepared = _prepare(labels, scores, width)
    y, _, starts, ends, pos, original, d1, d2, group, _, after, _ = prepared
    means = [oracle.RangeAUC_volume_opt(labels, scores, w, thre=len(labels))[-1]
             for w in range(width + 1)]
    expected = np.array([(w + 1) * means[w] - (w * means[w - 1] if w else 0)
                         for w in range(width + 1)])
    values = np.full(width + 1, np.nan)
    observed = np.array([0, 3, 9])
    values[observed] = expected[observed]
    before = values[observed].copy()
    complete = getattr(module(), "_sparse_pr_complete")
    args = (len(y), float(y.sum()), starts, ends, pos, original, d1, d2, group, after)
    assert complete(*args, values) == len(values) - len(observed)
    np.testing.assert_array_equal(values[observed], before)
    np.testing.assert_allclose(values, expected, atol=1e-11, rtol=0)
    assert complete(*args, values) == 0
    # Existing slots are opaque to this low-level helper: even a sentinel may
    # not be silently recomputed. The caller owns their numerical validity.
    values[3] = 17.25
    values[7] = np.nan
    assert complete(*args, values) == 1
    assert values[3] == 17.25
    assert values[7] == pytest.approx(expected[7], abs=1e-11, rel=0)
