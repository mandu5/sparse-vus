"""Fail-closed audit of completed benchmark receipts, independent of reporting.

Run after benchmark_public.py, before generating scientific claims. This checks
the stored final numerical outputs; it does not assert that unrecorded outputs
from earlier timing repetitions were independently checked.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
TOL = 1e-11
METHODS = {'sparse_numpy', 'sparse_numba', 'dense_numpy', 'dense_numba', 'dense_direct_numba'}


def finite_tree(value, path='root'):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f'nonfinite value: {path}')
    if isinstance(value, dict):
        for k, v in value.items():
            finite_tree(v, f'{path}.{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            finite_tree(v, f'{path}[{i}]')


def numeric(value, name='number'):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be a real JSON number')
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f'nonfinite {name}') from exc
    if not math.isfinite(result):
        raise ValueError(f'nonfinite {name}')
    return result


def discrepancy(x, y):
    if not isinstance(x, (list, tuple)) or not isinstance(y, (list, tuple)):
        raise ValueError('metric outputs must be numeric sequences')
    if len(x) != 2 or len(y) != 2:
        raise ValueError('metric outputs must contain ROC and PR')
    return max(abs(numeric(a, 'metric') - numeric(b, 'metric')) for a, b in zip(x, y))


def validate_times(times, repetitions, name):
    if not isinstance(times, list) or len(times) != repetitions:
        raise ValueError(f'timings invalid: {name}')
    if any(numeric(t, 'timing') <= 0 for t in times):
        raise ValueError(f'timings invalid: {name}')


def validate_external(row, primary, tolerance=TOL):
    finite_tree(row)
    errors = {}
    for name in ('official250', 'dtaianomaly250', 'dtaianomaly_exact'):
        target = primary['exact'] if name.endswith('_exact') else primary['sampled250']
        value = row[name]
        err = discrepancy(value['result'], target)
        if err > tolerance:
            raise ValueError(f'external parity failed: {name}: {err}')
        claimed = numeric(value['sampled_error'] if name == 'official250' else value['target_error'], 'stored error')
        if abs(claimed - err) > 1e-14:
            raise ValueError(f'external stored error inconsistent: {name}')
        times = value['seconds']
        expected_reps = 1 if name == 'official250' else 3
        validate_times(times, expected_reps, name)
        if name != 'official250' and abs(statistics.median(times) - numeric(value['median_seconds'], 'median')) > 1e-14:
            raise ValueError(f'external median inconsistent: {name}')
        errors[name] = err
    return errors


def audit(root=ROOT):
    out = root / 'artifacts'
    paths = {name: out / name for name in [
        'public_benchmark.jsonl', 'public_benchmark_receipt.json', 'benchmark_environment.json',
        'public_external_baselines.json', 'crop_parity.json', 'public_exclusions.json',
        'selected_series.json', 'dtaianomaly_source.json']}
    content = {name: json.loads(path.read_text()) for name, path in paths.items() if not name.endswith('.jsonl')}
    for name, value in content.items():
        finite_tree(value, name)
    raw = paths['public_benchmark.jsonl'].read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    protocol = json.loads((root / 'experiments/protocol.json').read_text())
    selection = content['selected_series.json']
    exclusions = content['public_exclusions.json']
    valid = set(selection['ordered_series']) - {r['series'] for r in exclusions}
    expected = {(s, m, w) for s in valid for m in selection['models']
                for w in protocol['public_data']['max_buffer']}
    indexed, max_main = {}, 0.0
    for row in rows:
        finite_tree(row)
        key = (row['series'], row['model'], row['max_buffer'])
        if key in indexed:
            raise ValueError(f'duplicate benchmark row: {key}')
        indexed[key] = row
        if set(row['results']) != METHODS or set(row['seconds']) != METHODS:
            raise ValueError('method coverage differs from protocol')
        errors = [discrepancy(row['exact'], value) for value in row['results'].values()]
        if max(errors) > TOL or abs(max(errors) - numeric(row['max_parity_error'], 'parity error')) > 1e-14:
            raise ValueError(f'main parity failed: {key}')
        max_main = max(max_main, *errors)
        for name, times in row['seconds'].items():
            validate_times(times, protocol['public_data']['timing_repetitions'], name)
            if abs(statistics.median(times) - numeric(row['median_seconds'][name], 'median')) > 1e-14:
                raise ValueError(f'invalid median: {key}, {name}')
        ratio = min(v for k, v in row['median_seconds'].items() if k.startswith('dense')) / row['median_seconds']['sparse_numba']
        if not math.isclose(ratio, numeric(row['speedup_vs_fastest_dense'], 'speed ratio'), rel_tol=1e-13):
            raise ValueError('reported speed ratio inconsistent')
        discrepancy(row['sampled250'], row['exact'])
        delta = [a - b for a, b in zip(row['sampled250'], row['exact'])]
        if discrepancy(delta, row['sampled250_delta']) > 1e-14:
            raise ValueError('sampled delta inconsistent')
        if not 0 < row['positive_points'] < row['n'] or not 0 < row['support_points'] <= row['n']:
            raise ValueError('invalid label or support counts')
    if set(indexed) != expected:
        raise ValueError(f'incomplete coverage: observed {len(indexed)}, expected {len(expected)}')
    receipt = content['public_benchmark_receipt.json']
    if receipt['metric_evaluations'] != len(rows) or receipt['unique_series'] != len(valid):
        raise ValueError('benchmark receipt count mismatch')
    if receipt['score_vectors'] != len(valid) * len(selection['models']):
        raise ValueError('score vector count mismatch')
    if receipt['records_sha256'] != hashlib.sha256(raw).hexdigest():
        raise ValueError('benchmark record digest mismatch')
    crop_rows = content['crop_parity.json']
    crop_keys = [(r['series'], r['model'], r['width']) for r in crop_rows]
    if len(crop_keys) != len(set(crop_keys)) or set(crop_keys) != expected:
        raise ValueError('crop parity coverage mismatch')
    crop_errors = [r[k] for r in crop_rows if 'skipped' not in r for k in ('exact_error', 'sampled_error')]
    if any(numeric(e, 'crop error') < 0 or numeric(e, 'crop error') > TOL for e in crop_errors):
        raise ValueError('official crop parity failed')
    external = content['public_external_baselines.json']
    external_keys = [(r['series'], r['model'], r['width']) for r in external]
    external_expected = {k for k in expected if k[0] in selection['ordered_series'][:12]}
    if len(external_keys) != len(set(external_keys)) or set(external_keys) != external_expected:
        raise ValueError('external comparator coverage mismatch')
    external_errors = [error for row, key in zip(external, external_keys)
                       for error in validate_external(row, indexed[key]).values()]
    environment = content['benchmark_environment.json']
    for relative, expected_hash in environment['source_sha256'].items():
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f'source changed since benchmark: {relative}')
    dta = content['dtaianomaly_source.json']
    source = root / '.cache/dtaianomaly/_volume_under_surface_metrics.py'
    if hashlib.sha256(source.read_bytes()).hexdigest() != dta['source_sha256']:
        raise ValueError('external dtaianomaly source mismatch')
    official = root / 'cache/official_metrics.py'
    if hashlib.sha256(official.read_bytes()).hexdigest() != 'bd547c9746fc1b9bbce2895e20cb156f97d23365d5dce8c2a3fab90622ccdced':
        raise ValueError('external official source mismatch')
    return {'status': 'PASS', 'completed_utc': datetime.now(timezone.utc).isoformat(),
            'unique_series': len(valid), 'score_vectors': len(valid) * len(selection['models']),
            'metric_evaluations': len(rows), 'main_method_comparisons': len(rows) * (len(METHODS) - 1),
            'crop_checks': len(crop_errors), 'crop_skipped': sum('skipped' in r for r in crop_rows),
            'external_comparisons': len(external_errors), 'exclusions': len(exclusions),
            'maximum_main_error': max_main, 'maximum_crop_error': max(crop_errors, default=0),
            'maximum_external_error': max(external_errors, default=0),
            'source_hash_checks': len(environment['source_sha256']) + 2,
            'checks': ['finite values', 'all expected rows', 'no duplicates', 'last-output parity',
                       'external comparator parity', 'timing repetitions and medians',
                       'recomputed speed ratios', 'source and record hashes'],
            'input_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()},
            'gate_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='artifacts/final_artifact_gate.json')
    args = parser.parse_args()
    try:
        result = audit()
    except Exception as exc:
        result = {'status': 'FAIL', 'error': f'{type(exc).__name__}: {exc}'}
        (ROOT / args.output).write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
        raise SystemExit(1)
    (ROOT / args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
