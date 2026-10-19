"""Regression checks for errors the initial reporting harness could overlook."""
import copy
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from verify_artifact import finite_tree, validate_external


def example():
    exact, sampled = [.81, .43], [.8, .4]
    row = {'official250': {'result': sampled, 'sampled_error': 0., 'seconds': [.2]},
           'dtaianomaly250': {'result': sampled, 'target_error': 0., 'seconds': [.1, .2, .3], 'median_seconds': .2},
           'dtaianomaly_exact': {'result': exact, 'target_error': 0., 'seconds': [.5, .6, .7], 'median_seconds': .6}}
    return copy.deepcopy(row), {'exact': exact, 'sampled250': sampled}


def test_external_numeric_failure_is_not_omitted():
    row, primary = example()
    assert max(validate_external(row, primary).values()) == 0
    row['dtaianomaly_exact']['result'][0] += .01
    row['dtaianomaly_exact']['target_error'] = .01
    with pytest.raises(ValueError, match='external parity failed'):
        validate_external(row, primary)


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -float('inf')])
def test_nonfinite_nested_data_fails_closed(bad):
    with pytest.raises(ValueError, match='nonfinite'):
        finite_tree({'arbitrary': [{'value': bad}]})
    row, primary = example()
    row['official250']['sampled_error'] = bad
    with pytest.raises(ValueError, match='nonfinite'):
        validate_external(row, primary)


def test_external_invalid_timing_fails_closed():
    row, primary = example()
    row['dtaianomaly250']['seconds'][0] = 0
    with pytest.raises(ValueError, match='timings invalid'):
        validate_external(row, primary)


@pytest.mark.parametrize('bad', ['NaN', 'Infinity', '0.8', True, None, {}, 10**1000])
def test_metric_values_must_be_finite_json_numbers(bad):
    row, primary = example()
    row['official250']['result'][0] = bad
    with pytest.raises(ValueError):
        validate_external(row, primary)


@pytest.mark.parametrize('key', ['target_error', 'median_seconds', 'seconds'])
@pytest.mark.parametrize('bad', ['NaN', '0.2', True, None])
def test_numeric_metadata_does_not_accept_coercions(key, bad):
    row, primary = example()
    if key == 'seconds':
        row['dtaianomaly250'][key][0] = bad
    else:
        row['dtaianomaly250'][key] = bad
    with pytest.raises(ValueError):
        validate_external(row, primary)
