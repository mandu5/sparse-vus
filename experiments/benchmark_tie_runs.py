"""Frozen full-call tie-run experiment; no changes to older studies."""
from __future__ import annotations

import os
for _name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMBA_NUM_THREADS'):
    os.environ[_name] = '1'

import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'experiments'))
from benchmark_saturation import environment, ExternalCorpus
from benchmark_saturation_structural import array_digest, digest, write_json

METHODS = ('tie_runs', 'saturation', 'radix', 'klein')
SEED, REPS, ATOL = 202610234, 5, 1e-11


def sources():
    paths = list((ROOT/'src/sparse_vus').glob('*.py')) + [
        ROOT/'experiments'/name for name in (
            'benchmark_tie_runs.py', 'benchmark_saturation.py',
            'benchmark_saturation_structural.py', 'benchmark_advancement.py',
            'fast_vus_adapter.py')]
    paths += [ROOT/'docs/tie_run_protocol_20261023.md', ROOT/'.cache/fast_vus/fast_vus.py']
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def freeze(output):
    from benchmark_advancement import Corpus
    from sparse_vus.core import ranges
    output.mkdir(parents=True, exist_ok=False)
    (output/'inputs').mkdir()
    cache = ROOT/'.cache'/output.name
    cache.mkdir(parents=True, exist_ok=False)
    rows, bindings = [], {}

    def add(y, scores, meta, public=False):
        idx = len(rows)
        path = (output/'inputs' if public else cache)/f'{idx:03}.npz'
        np.savez(path, labels=y, scores=scores)
        rows.append({**meta, 'n': len(y), 'positive_points': int(y.sum()),
                     'input_path': str(path.relative_to(ROOT)),
                     'npz_sha256': digest(path), 'labels_sha256': array_digest(y),
                     'scores_sha256': array_digest(scores)})

    for width in (32, 128, 512, 2048):
        n, center = 4*width+3, 2*width+1
        for family in ('all_tied', 'distinct_original_last', 'eight_blocks',
                       'alternating', 'interval8_all_tied'):
            y = np.zeros(n, dtype=np.uint8)
            y[center:center+(8 if family == 'interval8_all_tied' else 1)] = 1
            scores = np.zeros(n)
            if family == 'distinct_original_last':
                scores = np.arange(n, dtype=float)
                scores[center] = -1.
            elif family == 'eight_blocks':
                scores = (np.arange(n)*8//n).astype(float)
            elif family == 'alternating':
                scores = (np.arange(n)%2).astype(float)
            add(y, scores, {'case_id': f'{family}|{width}', 'phase': 'structural',
                'family': family, 'series': family, 'model': family,
                'max_buffer': width}, True)

    for phase, loader in (('development', Corpus()), ('external', ExternalCorpus())):
        manifest = ROOT/f'artifacts/saturation/mac-{phase}/inputs.json'
        bindings[str(manifest.relative_to(ROOT))] = digest(manifest)
        for row in json.loads(manifest.read_text()):
            y, scores = loader.load(row)
            if len(ranges(y)[0]) != 1:
                continue
            if phase == 'development' and loader.hashes[row['model']][row['series']] != row['score_member_sha256']:
                raise ValueError('Original development score identity changed')
            add(y, scores, {key: row[key] for key in (
                'case_id', 'family', 'series', 'model', 'max_buffer')} | {'phase': phase})
    write_json(output/'inputs.json', rows)
    protocol = {'version': 1, 'methods': list(METHODS), 'repetitions': REPS,
                'seed': SEED, 'parity_atol': ATOL, 'cases': len(rows),
                'source_sha256': sources(), 'manifest_sha256': bindings,
                'inputs_sha256': digest(output/'inputs.json'),
                'history': 'Previously studied real arrays; reused evaluation, not unseen confirmation.',
                'decision': 'Accept numerical/work checks only if all prespecified assertions pass; timings descriptive, all losses retained.'}
    write_json(output/'protocol.json', protocol)
    return {'cases': len(rows), 'protocol_sha256': digest(output/'protocol.json')}


def contract(output, expected):
    if digest(output/'protocol.json') != expected:
        raise ValueError('Protocol changed')
    p = json.loads((output/'protocol.json').read_text())
    if digest(output/'inputs.json') != p['inputs_sha256']:
        raise ValueError('Inputs manifest changed')
    for name, value in p['source_sha256'].items():
        if digest(ROOT/name) != value:
            raise ValueError(f'Source changed: {name}')
    for name, value in p['manifest_sha256'].items():
        if digest(ROOT/name) != value:
            raise ValueError(f'Original manifest changed: {name}')
    return p, json.loads((output/'inputs.json').read_text())


def run(output, expected):
    from sparse_vus.tie_runs import interval_pr_tie_runs_jit, profile_tie_runs
    from sparse_vus.saturation import sparse_pr_saturation_jit, profile_saturation
    from sparse_vus.radix import sparse_pr_radix_jit
    from fast_vus_adapter import fast_vus_pr
    from threadpoolctl import threadpool_limits
    limits = threadpool_limits(limits=1)
    p, inputs = contract(output, expected)
    if any((output/name).exists() for name in ('environment.json', 'measurements.jsonl', 'completion.json')):
        raise ValueError('Run already started')
    methods = {'tie_runs': interval_pr_tie_runs_jit, 'saturation': sparse_pr_saturation_jit,
               'radix': sparse_pr_radix_jit, 'klein': lambda y,s,w: fast_vus_pr(y,s,w,len(y))}
    if list(methods) != p['methods']:
        raise ValueError('Method configuration differs from frozen protocol')
    write_json(output/'environment.json', environment())
    rng = random.Random(p['seed'])
    with (output/'measurements.jsonl').open('x') as stream:
        for i, item in enumerate(inputs):
            path = ROOT/item['input_path']
            if digest(path) != item['npz_sha256']:
                raise ValueError('NPZ changed')
            with np.load(path, allow_pickle=False) as data:
                y, scores = data['labels'], data['scores']
            if array_digest(y) != item['labels_sha256'] or array_digest(scores) != item['scores_sha256']:
                raise ValueError('Array identity changed')
            width = item['max_buffer']
            for fn in methods.values():
                fn(y, scores, width)
            values = {name: {'seconds': [], 'values': []} for name in methods}
            orders = []
            for _ in range(p['repetitions']):
                order = list(methods)
                rng.shuffle(order)
                orders.append(order)
                for name in order:
                    start = time.perf_counter_ns()
                    value = methods[name](y, scores, width)
                    elapsed = (time.perf_counter_ns()-start)/1e9
                    values[name]['seconds'].append(elapsed)
                    values[name]['values'].append(float(value))
            record = {**item, 'methods': values, 'orders': orders,
                      'tie_profile': profile_tie_runs(y, scores, width),
                      'position_profile': profile_saturation(y, scores, width)}
            stream.write(json.dumps(record, allow_nan=False)+'\n')
            stream.flush()
            if (i+1)%10 == 0 or i+1 == len(inputs):
                print(json.dumps({'completed': i+1, 'total': len(inputs)}), flush=True)
    contract(output, expected)
    write_json(output/'environment-end.json', environment())
    write_json(output/'completion.json', {'status': 'COMPLETE', 'cases': len(inputs),
               'protocol_sha256': expected, 'measurements_sha256': digest(output/'measurements.jsonl')})
    return report(output)


def report(output):
    done = json.loads((output/'completion.json').read_text())
    p, inputs = contract(output, done['protocol_sha256'])
    if done['status'] != 'COMPLETE' or done['cases'] != p['cases']:
        raise ValueError('Run did not complete the prescribed coverage')
    if done['protocol_sha256'] != digest(output/'protocol.json') or done['measurements_sha256'] != digest(output/'measurements.jsonl'):
        raise ValueError('Receipt mismatch')
    if p['inputs_sha256'] != digest(output/'inputs.json'):
        raise ValueError('Input manifest receipt mismatch')
    rows = [json.loads(line) for line in (output/'measurements.jsonl').read_text().splitlines()]
    if len(rows) != p['cases'] or len(inputs) != len(rows):
        raise ValueError('Incomplete coverage')
    maximum_error, cases, work_ok = 0., [], True
    rng = random.Random(p['seed'])
    for row, item in zip(rows, inputs):
        if any(row[key] != value for key, value in item.items()):
            raise ValueError('Input/output association mismatch')
        if list(row['methods']) != p['methods']:
            raise ValueError('Method coverage mismatch')
        orders = []
        for _ in range(p['repetitions']):
            order = list(p['methods'])
            rng.shuffle(order)
            orders.append(order)
        if orders != row['orders']:
            raise ValueError('Recorded order mismatch')
        for result in row['methods'].values():
            if len(result['seconds']) != p['repetitions'] or len(result['values']) != p['repetitions']:
                raise ValueError('Repetition coverage mismatch')
            if not all(np.isfinite(t) and t > 0 for t in result['seconds']):
                raise ValueError('Invalid timing')
            if not all(np.isfinite(v) for v in result['values']):
                raise ValueError('Invalid scalar')
        reference = row['methods']['radix']['values'][0]
        maximum_error = max(maximum_error, max(abs(v-reference) for r in row['methods'].values() for v in r['values']))
        prof = row['tie_profile']
        width = row['max_buffer']
        work_ok &= len(prof['events']) == width+1 and max(prof['events']) <= 3*row['positive_points']
        if row['phase'] == 'structural' and row['family'] == 'all_tied':
            work_ok &= prof['run_queries'] == [1]*(width+1)
            work_ok &= row['position_profile']['visited'] == [1+2*(w//2) for w in range(width+1)]
        med = {name: statistics.median(r['seconds']) for name, r in row['methods'].items()}
        cases.append({key: row[key] for key in ('case_id', 'phase', 'family', 'max_buffer')} |
                     {'seconds': med, 'ratios': {name: value/med['tie_runs'] for name, value in med.items() if name != 'tie_runs'},
                      'run_queries': sum(prof['run_queries']), 'position_visits': sum(row['position_profile']['visited'])})
    groups = {}
    for case in cases:
        group = case['family'] if case['phase'] == 'structural' else case['phase']
        groups.setdefault(f'{group}|L{case["max_buffer"]}', []).append(case)
    summaries = {}
    for name, items in groups.items():
        summaries[name] = {'cases': len(items), 'comparators': {
            method: {'median_ratio': statistics.median(c['ratios'][method] for c in items),
                     'losses': sum(c['ratios'][method] < 1 for c in items),
                     'aggregate_ratio': sum(c['seconds'][method] for c in items)/sum(c['seconds']['tie_runs'] for c in items)}
            for method in p['methods'] if method != 'tie_runs'}}
    result = {'status': 'PASS_PARITY_AND_WORK' if maximum_error <= p['parity_atol'] and work_ok else 'FAIL',
              'protocol_sha256': digest(output/'protocol.json'), 'cases': len(cases),
              'max_error': maximum_error, 'work_assertions': bool(work_ok),
              'summary': summaries, 'per_case': cases,
              'scope': 'Descriptive structural/reused-data evaluation; no new primary runtime success or unseen confirmation.'}
    path = output/'report.json'
    if path.exists() and json.loads(path.read_text()) != result:
        raise ValueError('Existing report reconstruction differs')
    if not path.exists():
        write_json(path, result)
    return {k: v for k, v in result.items() if k != 'per_case'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('freeze', 'run', 'report'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--protocol-sha256')
    args = parser.parse_args()
    output = args.output.resolve()
    value = freeze(output) if args.command == 'freeze' else (
        run(output, args.protocol_sha256) if args.command == 'run' else report(output))
    print(json.dumps(value, indent=2))
