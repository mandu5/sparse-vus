"""Independent public-consumer checks for the conventional interval control."""
import numpy as np
import pytest

pytest.importorskip('timeeval')
from timeeval import DefaultMetrics
from timeeval.metrics import RangePrecisionRangeRecallAUC


@pytest.mark.parametrize('case', ['ties', 'plateaus', 'all_positive', 'subnormal', 'float32'])
def test_interval_consumer_preserves_native_curve_and_auc(case):
    from sparse_vus.timeeval_interval_adapter import adapt_range_metric_interval_control

    if case == 'plateaus':
        labels = np.array([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0])
        scores = np.array([17, 1, 7, 2, 3, 4, 16, 8, 6, 14, 9, 5, 10, 11, 12, 15, 13, 0, 18.])
    elif case == 'all_positive':
        labels = np.ones(8, np.int64)
        scores = np.array([0., 7., 1., 6., 2., 5., 3., 4.])
    elif case == 'subnormal':
        labels = np.array([0, 1, 0, 1, 0, 1])
        scores = np.array([-1., -0., 0., np.nextafter(0., 1.), 1., 2.])
    elif case == 'float32':
        labels = np.array([0, 1, 1, 0, 1, 0, 1, 0])
        scores = np.array([0, .1, .1, .2, .4, .3, .2, .5], np.float32)
    else:
        labels = np.array([0, 1, 1, 0, 0, 1, 0, 1])
        scores = np.array([0., 0., 1., 1., 2., 2., 3., 3.])
    source = DefaultMetrics.RANGE_PR_AUC
    metric = adapt_range_metric_interval_control(source)
    expected = source._range_precision_recall_curve(labels, scores)
    actual = metric._range_precision_recall_curve(labels, scores)
    np.testing.assert_array_equal(actual[2], expected[2])
    np.testing.assert_allclose(
        actual[:2], expected[:2], atol=2e-7 if scores.dtype == np.float32 else 1e-12,
        rtol=0)
    assert metric(labels, scores) == pytest.approx(source(labels, scores), abs=1e-10, rel=0)
    assert source._range_precision_recall_curve.__func__.__module__ == 'timeeval.metrics.range_metrics'


@pytest.mark.parametrize('n,expected', [
    (12, [1., 4., 7., 10., 11.]), (11, [1., 4., 7., 10.]),
])
def test_interval_consumer_preserves_source_sampler_and_final_threshold(n, expected):
    from sparse_vus.timeeval_interval_adapter import adapt_range_metric_interval_control

    source = RangePrecisionRangeRecallAUC(max_samples=4, r_alpha=0, cardinality='one')
    metric = adapt_range_metric_interval_control(source)
    labels, scores = np.arange(n) % 2, np.arange(n, dtype=float)
    np.testing.assert_array_equal(metric._range_precision_recall_curve(labels, scores)[2], expected)
    assert metric(labels, scores) == pytest.approx(source(labels, scores), abs=1e-10, rel=0)


def test_interval_consumer_preserves_all_observed_thresholds():
    from sparse_vus.timeeval_interval_adapter import adapt_range_metric_interval_control

    source = RangePrecisionRangeRecallAUC(
        max_samples=float('inf'), r_alpha=0, cardinality='one')
    labels = (np.arange(67) % 7 < 3).astype(np.int64)
    scores = np.random.default_rng(91).permutation(67).astype(float)
    metric = adapt_range_metric_interval_control(source)
    actual = metric._range_precision_recall_curve(labels, scores)
    expected = source._range_precision_recall_curve(labels, scores)
    np.testing.assert_array_equal(actual[2], np.arange(1., 67.))
    np.testing.assert_allclose(actual[:2], expected[:2], atol=1e-12, rtol=0)
    assert metric(labels, scores) == pytest.approx(source(labels, scores), abs=1e-10, rel=0)


def test_native_inclusive_maximum_and_synthetic_terminal_remain_distinct():
    from sparse_vus.timeeval_interval_adapter import adapt_range_metric_interval_control

    metric = adapt_range_metric_interval_control(DefaultMetrics.RANGE_PR_AUC)
    precision, recall, thresholds = metric._range_precision_recall_curve(
        np.array([0, 1, 0, 1]), np.array([0., 1., 1., 2.]))
    np.testing.assert_array_equal(thresholds, [1., 2.])
    np.testing.assert_allclose(precision, [.5, 2/3, 1., 1.], atol=1e-15, rtol=0)
    np.testing.assert_allclose(recall, [1., 1., .5, 0.], atol=1e-15, rtol=0)


@pytest.mark.parametrize('labels', [[0, 1, 0, 1], [0, 0, 0, 0], [1, 1, 1, 1]])
def test_interval_consumer_preserves_native_constant_shortcut(labels):
    from sparse_vus.timeeval_interval_adapter import adapt_range_metric_interval_control

    metric = adapt_range_metric_interval_control(DefaultMetrics.RANGE_PR_AUC)
    with pytest.warns(UserWarning, match='constant'):
        assert metric(np.array(labels), np.ones(4)) == 0.


def test_interval_consumer_preserves_native_no_positive_error():
    from sparse_vus.timeeval_interval_adapter import adapt_range_metric_interval_control

    metric = adapt_range_metric_interval_control(DefaultMetrics.RANGE_PR_AUC)
    labels, scores = np.zeros(4, np.int64), np.arange(4, dtype=float)
    with pytest.raises(AssertionError):
        DefaultMetrics.RANGE_PR_AUC(labels, scores)
    with pytest.raises(AssertionError):
        metric(labels, scores)


def test_interval_consumer_preserves_native_score_validation_and_sanitization():
    from sparse_vus.timeeval_interval_adapter import adapt_range_metric_interval_control

    metric = adapt_range_metric_interval_control(DefaultMetrics.RANGE_PR_AUC)
    labels = np.array([0, 1, 0, 1, 0, 1])
    scores = np.array([np.nan, np.inf, -np.inf, .2, .5, .8])
    assert metric(labels, scores) == pytest.approx(
        DefaultMetrics.RANGE_PR_AUC(labels, scores), abs=1e-10, rel=0)
    with pytest.raises(ValueError, match='floats'):
        metric(labels, np.arange(6))


def test_interval_consumer_rejects_unsupported_cardinality_policy():
    from sparse_vus.timeeval_interval_adapter import adapt_range_metric_interval_control

    with pytest.raises(ValueError, match='native default'):
        adapt_range_metric_interval_control(DefaultMetrics.FIXED_RANGE_PR_AUC)
