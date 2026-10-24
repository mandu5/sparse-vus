"""Frozen post-review comparison against compiled conventional support cumsums."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np
from audit_pvldb20261024 import digest, read

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/pvldb-research-20261024'
PRIMARY = BASE / 'full-precision'
OUT = BASE / 'compiled-support-control'
CACHE = ROOT / '.cache/pvldb-full-precision-20261024'
METHODS = ['released', 'stream', 'support_cumsum']


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def freeze():
    parent = read(PRIMARY / 'protocol.json')
    sources = dict(parent['source_sha256'])
    for file in ('experiments/pvldb_compiled_control.py', 'experiments/support_cumsum_control.py'):
        sources[file] = digest(ROOT / file)
    orders = [METHODS[i:] + METHODS[:i] for i in range(len(METHODS))]
    orders += [list(reversed(order)) for order in orders.copy()]
    OUT.mkdir(exist_ok=False)
    write(OUT / 'protocol.json', {
        'status': 'FROZEN_AFTER_FINAL_BLIND_REVIEW_BEFORE_THIS_CONTROL_TIMING',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'primary_protocol_sha256': digest(PRIMARY / 'protocol.json'),
        'inputs_sha256': digest(PRIMARY / 'inputs.json'),
        'primary_records_sha256': digest(PRIMARY / 'records.jsonl'),
        'source_sha256': sources, 'methods': METHODS, 'orders': orders,
        'workflow_orders': orders, 'width': 30, 'parity_atol': 1e-11, 'winner_tie_atol': 1e-10,
        'cohort': 'All 73 primary recordings and eight unchanged stored float64 score vectors.',
        'hypothesis': 'At fixed validation/radix/global-tie ranking and compiled execution, compare conventional direct-ramp support cumsums to nearest-interval geometry and batch sharing. Report all outcomes, including no geometric benefit.',
        'control': 'New optimized author reimplementation of the support-cumsum approach, with support-local scratch and original-label mass cached across widths. Not unchanged public Klein or a literal JIT. Does not use nearest-interval distances.',
        'timing': 'Six balanced serial orders, warm JIT/imports, complete calls including validation/preparation/selection. Six balanced file-to-decision passes per collection; no training/cold-storage/fsync claim.',
        'uncertainty': '10000 seeded log-ratio case resamples, familywise95 across three collections per comparison, with equal-label-block sensitivity. Workflow uncertainty only fixed-input trial variability.',
        'failure_policy': 'No exclusions or replacements. Nonfinite output, reference discrepancy above tolerance or different winner set halts.',
    })


def evaluate(method, y, scores):
    if method == 'support_cumsum':
        from support_cumsum_control import support_cumsum_pr
        values = np.asarray([support_cumsum_pr(y, s, 30) for s in scores])
        return values, np.flatnonzero(values >= values.max() - 1e-10).tolist()
    from pvldb_full_precision import evaluate as original
    return original(method, y, scores, 30)


def run():
    sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments')]
    p = read(OUT / 'protocol.json')
    for file, h in p['source_sha256'].items():
        if digest(ROOT / file) != h:
            raise ValueError('source binding: ' + file)
    for key, file in [('primary_protocol_sha256', 'protocol.json'), ('inputs_sha256', 'inputs.json'), ('primary_records_sha256', 'records.jsonl')]:
        if digest(PRIMARY / file) != p[key]:
            raise ValueError('parent binding: ' + file)
    cases = read(PRIMARY / 'inputs.json')['series']
    for c in cases:
        if digest(CACHE / c['file']) != c['npz_sha256']:
            raise ValueError('input bytes')
    references = {r['series']: r['values'] for r in map(json.loads, (PRIMARY / 'records.jsonl').read_text().splitlines())
                  if r['method'] == 'released' and r['trial'] == 0 and r['width'] == 30}
    write(OUT / 'run-start.json', {'utc': datetime.now(timezone.utc).isoformat(),
          'protocol_sha256': digest(OUT / 'protocol.json'), 'platform': platform.platform(), 'python': sys.version})
    for method in METHODS:
        evaluate(method, np.array([0, 1, 0, 0, 1, 0], np.int8), np.tile(np.arange(6.), (8, 1)))
    with (OUT / 'records.jsonl').open('x') as f:
        for c in cases:
            with np.load(CACHE / c['file'], allow_pickle=False) as z:
                y, scores = z['labels'], z['scores']
            reference = np.asarray(references[c['series']])
            truth = np.flatnonzero(reference >= reference.max() - p['winner_tie_atol']).tolist()
            for trial, order in enumerate(p['orders']):
                for method in order:
                    start = time.perf_counter_ns()
                    values, winners = evaluate(method, y, scores)
                    seconds = (time.perf_counter_ns() - start) * 1e-9
                    error = float(np.max(np.abs(values - reference)))
                    if not np.isfinite(values).all() or error > p['parity_atol'] or winners != truth:
                        raise ValueError('parity: ' + c['series'] + ' ' + method)
                    f.write(json.dumps({'series': c['series'], 'family': c['family'], 'method': method,
                        'trial': trial, 'seconds': seconds, 'values': values.tolist(), 'winners': winners, 'pr_error': error}, allow_nan=False) + '\n')
                    f.flush()
            print(c['series'], 'complete', flush=True)
    with (OUT / 'workflows.jsonl').open('x') as f:
        for family in ('NAB', 'SMAP', 'SMD'):
            group = [c for c in cases if c['family'] == family]
            for trial, order in enumerate(p['workflow_orders']):
                for method in order:
                    start = time.perf_counter_ns()
                    decisions = []
                    for c in group:
                        with np.load(CACHE / c['file'], allow_pickle=False) as z:
                            values, winners = evaluate(method, z['labels'], z['scores'])
                        decisions.append({'series': c['series'], 'values': values.tolist(), 'winners': winners})
                    with (CACHE / 'last-compiled-control-output.json').open('w') as target:
                        json.dump(decisions, target, allow_nan=False)
                    seconds = (time.perf_counter_ns() - start) * 1e-9
                    f.write(json.dumps({'family': family, 'method': method, 'trial': trial, 'seconds': seconds,
                        'decisions': decisions}, allow_nan=False) + '\n')
                    f.flush()
            print(family, 'workflow complete', flush=True)
    write(OUT / 'complete.json', {'status': 'COMPLETE', 'utc': datetime.now(timezone.utc).isoformat(),
          'protocol_sha256': digest(OUT / 'protocol.json'), 'records_sha256': digest(OUT / 'records.jsonl'),
          'workflows_sha256': digest(OUT / 'workflows.jsonl')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['freeze', 'run'])
    globals()[parser.parse_args().command]()
