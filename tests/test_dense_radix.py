"""Dense PR-only controls isolate radix ranking from sparse event elimination.

Design contract: both public calls validate/convert inputs, obtain every global
rank with radix._descending_keys/_radix_argsort, and return a scalar PR mean
over all widths. The direct control reuses pr_compiled._dense_pr_direct_kernel.
The nearest control computes interval distances for arange(n), then runs its
own all-position PR-only sweep with reusable width scratch. Neither prepares
support events or performs ROC work. The wrapper-spy test protects this dense
comparator boundary; oracle tests independently protect the metric semantics.

Drafted before dense_radix.py exists. Execute the RED/GREEN sequence only after
the parent clears the concurrent frozen development benchmark.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
ORACLE_SHA256 = "bd547c9746fc1b9bbce2895e20cb156f97d23365d5dce8c2a3fab90622ccdced"
METHODS = ("dense_pr_direct_radix_jit", "dense_pr_nearest_radix_jit")


def module():
    assert importlib.util.find_spec("sparse_vus.dense_radix") is not None, "Dense radix controls are missing"
    return importlib.import_module("sparse_vus.dense_radix")


@pytest.fixture(scope="module")
def oracle():
    path = ROOT / "cache/official_metrics.py"
    assert path.is_file(), "Run python experiments/fetch_reference.py first"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ORACLE_SHA256
    spec = importlib.util.spec_from_file_location("dense_radix_pinned_oracle", path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded.metricor()


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("scores", [[-0., 0.], [0., -0.], [4., 4.]])
def test_numerically_tied_scores_enter_one_threshold(method, scores):
    result = getattr(module(), method)([0, 1], scores, 0)
    assert type(result) is float
    assert result == .5


@pytest.mark.parametrize("method", METHODS)
def test_off_support_ties_keep_hand_computed_global_precision(method):
    # Rank 1 is negative. The zero tie admits one positive plus two negatives;
    # the final -2 tie admits the second positive plus one negative. Existence
    # reward makes the first recall (1/2)*(1/2)=1/4, so PR is
    # (1/4)*(1/4) + (1-1/4)*(2/6) = 5/16.
    result = getattr(module(), method)([0, 1, 0, 1, 0, 0],
                                      [3., -0., 0., -2., -0., -2.], 0)
    assert result == pytest.approx(5 / 16, abs=1e-15, rel=0)
    assert getattr(module(), method)([0, 1], [-2., -1.], 0) == 1.


@pytest.mark.parametrize("method", METHODS)
def test_full_thresholds_retain_rank_two_anomaly_on_long_negative_tail(method):
    # A fixed 250-rank grid skips rank 2 here; exact PR is 1/2 regardless
    # of the 999 lower-scored negatives. No expensive oracle call is needed.
    labels = np.zeros(1001, dtype=np.int8)
    labels[1] = 1
    scores = np.arange(len(labels), 0, -1, dtype=float)
    assert getattr(module(), method)(labels, scores, 0) == .5


@pytest.mark.parametrize("method", METHODS)
def test_documented_example_returns_pr_not_roc(method):
    result = getattr(module(), method)([0, 1, 0, 0, 1, 0], [1, 2, 3, 4, 5, 6], 4)
    assert result == pytest.approx(0.6834092121537311, rel=0, abs=1e-12)


@pytest.mark.parametrize("width", [0, 1, 2, 3, 4, 7, 14, 31])
@pytest.mark.parametrize("labels,scores", [
    ([0, 1, 0, 0, 1, 0, 0, 0], [7, 2, 3, 2, 1, 6, 4, 0]),
    ([0, 1, 0, 0, 0, 1, 0, 0], [0, 3, 1, 7, 2, 3, 6, 4]),
    ([1, 1, 0, 0, 0, 1, 1], [1, 0, 4, 2, 6, 3, 5]),
    ([0, 0, 0, 1, 1, 1], [4, 2, 5, 0, 3, 1]),
    ([0, 1, 0, 0, 1, 0], [1, 1, 1, 1, 1, 1]),
    ([1, 1, 1, 0, 1, 1], [5, 2, 1, 3, 4, 0]),
])
def test_boundaries_adjacency_overlap_and_dynamic_mass_against_oracle(labels, scores, width, oracle):
    labels, scores = np.asarray(labels), np.asarray(scores, dtype=float)
    expected = oracle.RangeAUC_volume_opt(labels, scores, width, thre=len(labels))[-1]
    for method in METHODS:
        result = getattr(module(), method)(labels, scores, width)
        assert result == pytest.approx(expected, rel=0, abs=1e-11)


@pytest.mark.parametrize("seed", range(24))
def test_independent_score_orders_and_label_densities_against_oracle(seed, oracle):
    rng = np.random.default_rng(20261021873 + seed)
    n = int(rng.choice([7, 19, 41, 67]))
    labels = (rng.random(n) < rng.choice([.03, .25, .8])).astype(np.int8)
    labels[0], labels[-1] = seed % 2, 1 - seed % 2
    scores = rng.normal(size=n) if seed % 3 == 0 else rng.integers(-3, 3, n).astype(float)
    width = int(rng.choice([0, 1, 2, 9, 30]))
    expected = oracle.RangeAUC_volume_opt(labels, scores, width, thre=n)[-1]
    for method in METHODS:
        result = getattr(module(), method)(labels, scores, width)
        assert result == pytest.approx(expected, rel=0, abs=1e-11)


def score_representations():
    tiny = np.nextafter(0., 1.)
    extreme = np.array([-np.finfo(float).max, -1., -np.finfo(float).tiny,
                        -tiny, -0., 0., tiny, np.finfo(float).tiny,
                        1., np.finfo(float).max])
    padded = np.zeros(20)
    padded[::2] = extreme
    readonly = extreme.copy()
    readonly.flags.writeable = False
    return [extreme, extreme.astype(">f8"), padded[::2], extreme[::-1], readonly,
            np.array([0, 1, 2**53, 2**53 + 1, 2**63, 2**63 + 1,
                      2**64 - 1, 5, 5, 3], dtype=np.uint64)]


@pytest.mark.parametrize("scores", score_representations(),
                         ids=["finite_extremes", "big_endian", "strided", "reversed", "readonly", "uint64"])
@pytest.mark.parametrize("width", [0, 1, 4, 25])
def test_conversion_and_layout_do_not_change_inputs_or_metric(scores, width, oracle):
    labels = np.array([0, 1, 0, 0, 1, 0, 0, 1, 0, 1], dtype=np.uint8)
    labels.flags.writeable = False
    before = labels.tobytes(), scores.tobytes()
    expected = oracle.RangeAUC_volume_opt(labels, scores.astype(float), width, thre=len(labels))[-1]
    for method in METHODS:
        result = getattr(module(), method)(labels, scores, np.int64(width))
        assert result == pytest.approx(expected, rel=0, abs=1e-11)
        assert (labels.tobytes(), scores.tobytes()) == before


@pytest.mark.parametrize("method", METHODS)
def test_dense_control_passes_all_positions_to_radix_and_kernel(method, monkeypatch):
    dense = module()
    radix = importlib.import_module("sparse_vus.radix")
    core = importlib.import_module("sparse_vus.core")
    labels = np.zeros(17, dtype=np.int8)
    labels[[4, 12]] = 1
    scores = np.arange(17, dtype=float)[::-1]
    calls = {}

    def forbidden(*args, **kwargs):
        pytest.fail("Dense comparator must not prepare sparse support events")

    def keys(values):
        calls["key_scores"] = values.copy()
        return radix._descending_keys(values)

    def order(values):
        calls["key_count"] = len(values)
        return radix._radix_argsort(values)

    def distances(positions, starts, ends):
        calls["distance_positions"] = positions.copy()
        return radix._nearest_two_linear(positions, starts, ends)

    def direct_kernel(y, x, starts, ends, rank, width):
        calls["kernel_labels"], calls["kernel_scores"], calls["rank"] = y.copy(), x.copy(), rank.copy()
        assert width == 0
        return .375

    def nearest_kernel(y, x, starts, ends, d1, d2, rank, width):
        calls["distance_sizes"] = len(d1), len(d2)
        return direct_kernel(y, x, starts, ends, rank, width)

    monkeypatch.setattr(core, "_prepare", forbidden)
    monkeypatch.setattr(radix, "_prepare_radix", forbidden)
    monkeypatch.setattr(dense, "_descending_keys", keys)
    monkeypatch.setattr(dense, "_radix_argsort", order)
    monkeypatch.setattr(dense, "_nearest_two_linear", distances)
    monkeypatch.setattr(dense, "_dense_pr_direct_kernel", direct_kernel)
    monkeypatch.setattr(dense, "_dense_pr_nearest_radix_kernel", nearest_kernel)
    assert getattr(dense, method)(labels, scores, 0) == .375
    np.testing.assert_array_equal(calls["key_scores"], scores)
    assert calls["key_count"] == len(labels)
    np.testing.assert_array_equal(calls["kernel_labels"], labels)
    np.testing.assert_array_equal(calls["kernel_scores"], scores)
    np.testing.assert_array_equal(calls["rank"], np.arange(len(labels)))
    if method == "dense_pr_nearest_radix_jit":
        np.testing.assert_array_equal(calls["distance_positions"], np.arange(len(labels)))
        assert calls["distance_sizes"] == (len(labels), len(labels))
    else:
        assert "distance_positions" not in calls


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("labels,scores,width", [
    ([0, 0], [0, 1], 1), ([1, 1], [0, 1], 1), ([0, 1.5], [0, 1], 1),
    ([0, 1], [0, float("nan")], 1), ([0, 1], [0, float("inf")], 1),
    ([0, 1], [float("-inf"), 0], 1), ([0, 1], [0], 1),
    ([[0, 1]], [[0, 1]], 1), ([0, 1], [0, 1], -1), ([0, 1], [0, 1], 1.5),
])
def test_invalid_inputs_are_rejected_before_radix_or_kernel(method, labels, scores, width):
    with pytest.raises(ValueError):
        getattr(module(), method)(labels, scores, width)
