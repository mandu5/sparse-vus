"""Behavioral guards for experiment reconstruction."""
import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / 'experiments/benchmark_saturation.py'
    spec = importlib.util.spec_from_file_location('saturation_experiment', path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def rows():
    return [dict(case_id=str(i), family='f'+str(i), max_buffer=30,
                 methods={'saturation':{'seconds':[1., 1., 1.], 'values':[.5]*3},
                          'radix':{'seconds':[2., 2., 2.], 'values':[.5]*3}})
            for i in range(4)]


def test_report_reconstructs_exact_paired_ratios():
    report = module().summarize(rows(), bootstrap_repetitions=40)
    comparison = report['widths']['30']['comparisons']['radix']
    assert comparison['median_ratio'] == 2.
    assert comparison['aggregate_ratio'] == 2.
    assert comparison['geomean_ratio'] == 2.
    assert comparison['geomean_ci95'] == [2., 2.]
    assert comparison['wins'] == 4
    assert report['parity_pass'] is True


def test_report_detects_semantic_error_and_rejects_duplicate_cases():
    data = rows()
    data[1]['methods']['radix']['values'][1] += 1e-4
    assert module().summarize(data, bootstrap_repetitions=40)['parity_pass'] is False
    with pytest.raises(ValueError, match='Duplicate'):
        module().summarize(data + [data[0]], bootstrap_repetitions=40)


def test_report_rejects_missing_method_and_invalid_timing():
    data = rows()
    del data[1]['methods']['radix']
    with pytest.raises(ValueError, match='method'):
        module().summarize(data, bootstrap_repetitions=40)
    data = rows()
    data[1]['methods']['radix']['seconds'][0] = 0
    with pytest.raises(ValueError, match='timing'):
        module().summarize(data, bootstrap_repetitions=40)


def test_frozen_inputs_exclude_historical_measurements():
    historical = dict(series='s', family='f', model='m', n=5, positive_points=1,
                      max_buffer=100, label_member_sha256='label',
                      exact={'pr':.3}, sampled250=.2, results={'seconds':4},
                      median_seconds=3, speedup_vs_fastest_dense=99)
    actual = module().case_input(historical, 'score')
    assert actual == dict(series='s',family='f',model='m',n=5,positive_points=1,
                          max_buffer=100,label_member_sha256='label',
                          score_member_sha256='score',case_id='s|m|100')
