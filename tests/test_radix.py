"""Fixed-word preparation preserves the original metric and score-tie contract."""
import hashlib
import importlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from sparse_vus.core import _prepare

ROOT = Path(__file__).resolve().parents[1]
ORACLE_SHA256 = "bd547c9746fc1b9bbce2895e20cb156f97d23365d5dce8c2a3fab90622ccdced"
PREP_FIELDS = ("labels", "scores", "starts", "ends", "positions", "original",
               "nearest", "second_nearest", "groups", "before", "after", "support_index")


def module():
    assert importlib.util.find_spec("sparse_vus.radix") is not None, "Radix preparation is missing"
    return importlib.import_module("sparse_vus.radix")


@pytest.fixture(scope="module")
def oracle():
    path = ROOT / "cache/official_metrics.py"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ORACLE_SHA256
    spec = importlib.util.spec_from_file_location("radix_pinned_vus_oracle", path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded.metricor()


def test_global_ties_and_signed_zero_have_hand_counted_ranks():
    prepared = module()._prepare_radix([0, 1, 0, 1, 0, 0],
                                       [3., -0., 0., -2., -0., -2.], 0)
    np.testing.assert_array_equal(prepared[4], [1, 3])
    np.testing.assert_array_equal(prepared[8], [0, 1])
    np.testing.assert_array_equal(prepared[9], [1, 4])
    np.testing.assert_array_equal(prepared[10], [4, 6])
    # Negating only the sign bit would reverse the order of negative scores.
    assert module().sparse_pr_radix_jit([0, 1], [-2., -1.], 0) == 1.
    # Treating +0/-0 as distinct thresholds would make this order-dependent.
    assert module().sparse_pr_radix_jit([0, 1], [-0., 0.], 0) == .5
    assert module().sparse_pr_radix_jit([0, 1], [0., -0.], 0) == .5


@pytest.mark.parametrize("seed", range(48))
def test_all_preparation_arrays_and_both_integrals_match_reference(seed, oracle):
    rng = np.random.default_rng(2026102191 + seed)
    n = int(rng.choice([7, 19, 43, 71]))
    labels = (rng.random(n) < rng.choice([.02, .2, .8])).astype(np.int8)
    labels[0], labels[-1] = seed % 2, 1 - seed % 2
    scores = rng.normal(size=n) if seed % 3 == 0 else rng.integers(-4, 4, n).astype(float)
    if seed % 3 == 2:
        scores[scores == 0] = -0.
    width = int(rng.choice([0, 1, 2, 3, 7, 30, 90]))
    actual = module()._prepare_radix(labels, scores, width)
    expected = _prepare(labels, scores, width)
    for field, a, b in zip(PREP_FIELDS, actual, expected):
        np.testing.assert_array_equal(a, b, err_msg=field)
    official = oracle.RangeAUC_volume_opt(labels, scores, width, thre=n)[-2:]
    pair = module().sparse_vus_radix_jit(labels, scores, width)
    pr = module().sparse_pr_radix_jit(labels, scores, width)
    np.testing.assert_allclose(pair, official, atol=1e-11, rtol=0)
    assert pr == pytest.approx(official[1], abs=1e-11, rel=0)


def score_representations():
    extreme = np.array([-np.finfo(float).max, -1., -np.finfo(float).tiny,
                        -np.nextafter(0., 1.), -0., 0., np.nextafter(0., 1.),
                        np.finfo(float).tiny, 1., np.finfo(float).max])
    padded = np.zeros(20)
    padded[::2] = extreme
    readonly = extreme.copy()
    readonly.flags.writeable = False
    return [extreme, extreme.astype(">f8"), padded[::2], extreme[::-1], readonly,
            np.array([0, 1, 2**53, 2**53 + 1, 2**63, 2**63 + 1,
                      2**64 - 1, 5, 5, 3], dtype=np.uint64)]


@pytest.mark.parametrize("scores", score_representations(),
                         ids=["finite_extremes", "big_endian", "strided", "reversed", "readonly", "uint64"])
@pytest.mark.parametrize("width", [0, 1, 2, 7, 25])
def test_score_representations_preserve_conversion_and_inputs(scores, width, oracle):
    labels = np.array([0, 1, 0, 0, 1, 0, 0, 1, 0, 1], dtype=np.uint8)
    labels.flags.writeable = False
    labels_before, scores_before = labels.tobytes(), scores.tobytes()
    expected = _prepare(labels, scores, width)
    actual = module()._prepare_radix(labels, scores, np.int64(width))
    for field, a, b in zip(PREP_FIELDS, actual, expected):
        np.testing.assert_array_equal(a, b, err_msg=field)
    # API conversion intentionally merges integers indistinguishable as float64.
    official = oracle.RangeAUC_volume_opt(labels, scores.astype(float), width, thre=len(labels))[-2:]
    pair = module().sparse_vus_radix_jit(labels, scores, width)
    np.testing.assert_allclose(pair, official, atol=1e-11, rtol=0)
    assert module().sparse_pr_radix_jit(labels, scores, width) == pytest.approx(official[1], abs=1e-11, rel=0)
    assert labels.tobytes() == labels_before
    assert scores.tobytes() == scores_before


@pytest.mark.parametrize("labels,width", [
    ([1, 1, 1, 0, 0, 0], 0),       # one interval: second distance is infinity
    ([0, 0, 0, 1, 1, 1], 20),      # boundary support clipping
    ([1, 0, 1, 0, 1, 0, 1], 1),    # dense separate intervals
    ([1, 0, 0, 1, 0, 0, 1], 2),    # adjacent expansions stay separate
    ([1, 0, 0, 1, 0, 0, 1], 4),    # overlapping expansions merge
    ([0, 1, 0, 0, 0, 0, 1, 0], 40),
])
def test_linear_geometry_covers_nearest_distinct_intervals(labels, width):
    scores = np.arange(len(labels), dtype=float)
    expected, actual = _prepare(labels, scores, width), module()._prepare_radix(labels, scores, width)
    for field, a, b in zip(PREP_FIELDS, actual, expected):
        np.testing.assert_array_equal(a, b, err_msg=field)


@pytest.mark.parametrize("entry", ["_prepare_radix", "sparse_pr_radix_jit", "sparse_vus_radix_jit"])
@pytest.mark.parametrize("labels,scores,width", [
    ([0, 0], [0, 1], 1), ([1, 1], [0, 1], 1), ([0, 1.5], [0, 1], 1),
    ([0, 1], [0, float("nan")], 1), ([0, 1], [0, float("inf")], 1),
    ([0, 1], [float("-inf"), 0], 1), ([0, 1], [0], 1),
    ([[0, 1]], [[0, 1]], 1), ([0, 1], [0, 1], -1), ([0, 1], [0, 1], 1.5),
])
def test_invalid_inputs_are_rejected_before_bit_sorting(entry, labels, scores, width):
    with pytest.raises(ValueError):
        getattr(module(), entry)(labels, scores, width)
