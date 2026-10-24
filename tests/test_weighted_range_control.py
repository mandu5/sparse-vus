"""Conventional interval control checked against an independent Fraction oracle.

These tests catch skipped/repeated ordered intersections, wrong local interval
coordinates, missing midpoint splits, cardinality errors, threshold-state reuse,
and altered numeric validation. The oracle enumerates finite sets and individual
weights; it uses no production closed-form or prefix helpers.
"""
import itertools

import numpy as np
import pytest

from test_weighted_range import oracle


def test_control_recomputes_off_label_merge_with_literal_expected_values():
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    actual = weighted_range_interval_control(
        [1, 0, 1], [3., 1., 2.], [1., 0., 1.],
        precision_bias='middle', recall_bias='middle')
    np.testing.assert_allclose(
        actual, [[1., 1., 1.], [.25, 1., .4], [1., 1., 1.]],
        atol=2e-14, rtol=0)


@pytest.mark.parametrize('bias', ['flat', 'front', 'back', 'middle'])
@pytest.mark.parametrize('cardinality', ['one', 'reciprocal', 'improved'])
def test_short_tied_inputs_against_independent_fraction_oracle(bias, cardinality):
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    thresholds = np.array([np.inf, 0., -np.inf, 1., -1., 0.])
    for n in range(1, 4):
        for labels in itertools.product([0, 1], repeat=n):
            for values in itertools.product([-1., 0., 1.], repeat=n):
                scores = np.array(values)
                expected = [oracle(labels, scores > t, .2, bias, bias, cardinality)
                            for t in thresholds]
                actual = weighted_range_interval_control(
                    labels, scores, thresholds, precision_bias=bias,
                    recall_bias=bias, cardinality=cardinality)
                np.testing.assert_allclose(actual, expected, atol=3e-13, rtol=0)


@pytest.mark.parametrize('pbias,rbias', itertools.product(
    ['flat', 'front', 'back', 'middle'], repeat=2))
@pytest.mark.parametrize('cardinality', ['one', 'reciprocal', 'improved'])
@pytest.mark.parametrize('weighted', [False, True])
def test_ordered_intersections_with_mixed_biases_and_aggregations(
        pbias, rbias, cardinality, weighted):
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    # Long prediction crossing many truths, fragmented truth, coincident ends,
    # and false-positive prefix/suffix components exercise both pointer advances.
    cases = [
        ([0, 1, 0, 1, 1, 0, 1, 0, 1, 0],
         [0., 4., 3., 4., 4., 3., 4., 3., 4., 0.]),
        ([0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
         [4., 5., 0., 4., 1., 3., 0., 5., 4., 3.]),
        ([1, 1, 0, 0, 1, 1, 1, 0, 1, 1],
         [3., 3., 0., 2., 2., 3., 3., 0., 3., 3.]),
        ([0, 0, 1, 0, 1, 1, 0, 0, 0, 0],
         [4., 4., 3., 0., 3., 3., 0., 4., 4., 4.]),
    ]
    thresholds = np.array([2., -np.inf, 4., 0., np.inf, 3., 2.])
    for labels, values in cases:
        scores = np.array(values)
        expected = [oracle(labels, scores > t, .2, pbias, rbias,
                           cardinality, weighted) for t in thresholds]
        actual = weighted_range_interval_control(
            labels, scores, thresholds, precision_bias=pbias, recall_bias=rbias,
            cardinality=cardinality, weighted_precision=weighted)
        np.testing.assert_allclose(actual, expected, atol=3e-13, rtol=0)


@pytest.mark.parametrize('alpha', [0., .2, 1.])
def test_existence_weight_and_odd_midpoint_against_fraction_oracle(alpha):
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    labels = np.array([1, 1, 1, 1, 1, 0, 1, 1, 1])
    scores = np.array([5., 0., 3., 0., 4., 2., 4., 1., 5.])
    thresholds = np.array([3., 0., -np.inf, np.inf, 2.])
    expected = [oracle(labels, scores > t, alpha, 'front', 'middle', 'improved')
                for t in thresholds]
    actual = weighted_range_interval_control(
        labels, scores, thresholds, alpha=alpha, precision_bias='front',
        recall_bias='middle', cardinality='improved')
    np.testing.assert_allclose(actual, expected, atol=3e-13, rtol=0)


def test_weighted_precision_denominator_includes_unmatched_trailing_components():
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    # Predicted windows [0,0] and [2,4] have lengths 1 and 3. Only the first hits.
    actual = weighted_range_interval_control(
        [1, 0, 0, 0, 0], [2., 0., 2., 2., 2.], [1.],
        alpha=0, cardinality='one', weighted_precision=True)
    np.testing.assert_allclose(actual, [[.25, 1., .4]], atol=1e-15, rtol=0)


@pytest.mark.parametrize('bias_id,bias', enumerate(['flat', 'front', 'back', 'middle']))
def test_analytic_intersection_mass_matches_pointwise_integer_weights_at_large_offset(
        bias_id, bias):
    from sparse_vus.weighted_range_control import _interval_weight_sum

    # No enormous arrays: only the interval coordinates approach the int64 guard.
    for length in (1, 2, 3, 8, 17):
        a, b = 2**31 - 1 - length, 2**31 - 2
        for lo in range(a, b + 1):
            for hi in range(lo, b + 1):
                weights = []
                for i in range(lo, hi + 1):
                    if bias == 'flat':
                        weights.append(1)
                    elif bias == 'front':
                        weights.append(b - i + 1)
                    elif bias == 'back':
                        weights.append(i - a + 1)
                    else:
                        weights.append(min(i - a + 1, b - i + 1))
                assert _interval_weight_sum(a, b, lo, hi, bias_id) == sum(weights)


def test_middle_precision_distinguishes_equal_count_and_first_moment():
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    a = weighted_range_interval_control(
        [1, 0, 0, 1], [1.] * 4, [0.], cardinality='one', precision_bias='middle')
    b = weighted_range_interval_control(
        [0, 1, 1, 0], [1.] * 4, [0.], cardinality='one', precision_bias='middle')
    np.testing.assert_allclose([a[0, 0], b[0, 0]], [1/3, 2/3], atol=1e-15, rtol=0)


def test_empty_queries_and_no_positive_labels_have_explicit_zero_convention():
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    assert weighted_range_interval_control([0, 1], [0., 1.], []).shape == (0, 3)
    actual = weighted_range_interval_control(
        [0, 0, 0], [0., 1., 2.], [-np.inf, 0., np.inf])
    np.testing.assert_array_equal(actual, np.zeros((3, 3)))


def test_inputs_are_not_mutated_and_query_order_does_not_change_metric():
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    labels = np.array([1, 1, 0, 1, 0, 1])
    scores = np.array([2., 1., 3., 3., 0., 2.])
    thresholds = np.array([2., -np.inf, np.inf, 1., 2.])
    snapshots = [v.copy() for v in (labels, scores, thresholds)]
    actual = weighted_range_interval_control(labels, scores, thresholds)
    backwards = weighted_range_interval_control(labels, scores, thresholds[::-1])
    np.testing.assert_array_equal(actual, backwards[::-1])
    for value, expected in zip((labels, scores, thresholds), snapshots):
        np.testing.assert_array_equal(value, expected)


@pytest.mark.parametrize('options', [
    {'precision_bias': 'unknown'}, {'recall_bias': 'unknown'},
    {'cardinality': 'unknown'}, {'weighted_precision': 1},
    {'alpha': float('nan')}, {'alpha': -1}, {'alpha': 2},
])
def test_invalid_semantic_options_are_rejected(options):
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    with pytest.raises(ValueError):
        weighted_range_interval_control([0, 1], [0., 1.], [.5], **options)


@pytest.mark.parametrize('labels,scores,thresholds', [
    ([], [], [0.]), ([0, 1], [0.], [0.]), ([0, 2], [0., 1.], [0.]),
    ([0, 1], [0., np.inf], [0.]), ([0, 1], [0., 1.], [np.nan]),
    ([0], [1 + 1j], [0.]), ([0, 1], [2**54, 2**54 + 1], [0.]),
    ([0, 1], [0., 1.], [2**54]), ([[0, 1]], [0., 1.], [0.]),
])
def test_invalid_numeric_domain_is_rejected(labels, scores, thresholds):
    from sparse_vus.weighted_range_control import weighted_range_interval_control

    with pytest.raises(ValueError):
        weighted_range_interval_control(labels, scores, thresholds)
