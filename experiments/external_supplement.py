"""Post-review, fixed cross-family comparison with real dtaianomaly code.

Selections use only length and source-family metadata, never metric/runtime
outcomes. Timeouts are censored outcomes, not fabricated baseline runtimes.
"""
from __future__ import annotations
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
            'VECLIB_MAXIMUM_THREADS', 'NUMBA_NUM_THREADS'):
    os.environ[key] = '1'
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
import multiprocessing as mp
from pathlib import Path
import platform
import queue
import statistics
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
MODEL = 'bolt_base_64'
WIDTH = 30
LIMIT = 10.0
ART = ROOT/'artifacts'


def freeze_protocol():
    protocol = {'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'Post-review supplemental protocol; written before this experiment, after inspecting main interim outcomes.',
        'selection': 'For each family, sort complete common-series metadata by (n,series); choose index 0 and floor(count/2), dropping duplicates. No score or runtime criterion.',
        'model': MODEL, 'maximum_buffer': WIDTH,
        'methods': ['sparse_numba', 'dtaianomaly250', 'dtaianomaly_exact'],
        'repetitions': 3, 'method_order': 'seeded random order per case, then three calls per method',
        'seed': 713810, 'per_call_budget_seconds': LIMIT,
        'timeout': 'Each worker loads data and warms kernels before a ready message. Parent stops the call after its announced timer reaches the budget. A timeout is right-censored; no numeric speed ratio is assigned.',
        'warmup': 'Excluded; actual upstream fastmath/parallel kernel preserved, one thread. Both ROC and PR obtained from one shared call.',
        'parity_tolerance': 1e-11, 'reporting': 'All selected cases, completion counts, errors, three raw durations or censorship, family scope. Ratios only for completed cases, with their denominator.'}
    path = ART/'external_supplement_protocol.json'
    if path.exists():
        raise FileExistsError('Protocol already exists; preserve it.')
    path.write_text(json.dumps(protocol, indent=2)+'\n')
    return protocol


def worker(stem, method, output):
    import numpy as np
    import pandas as pd
    import numba
    from threadpoolctl import threadpool_limits, threadpool_info
    from sparse_vus.compiled import sparse_vus_jit
    from dtaianomaly_adapter import dtaianomaly_vus
    numba.set_num_threads(1); threadpool_limits(1)
    with zipfile.ZipFile(ROOT/'cache/TSB-AD-U.zip') as z:
        member = next(n for n in z.namelist() if Path(n).stem == stem and n.endswith('.csv'))
        labels_raw = z.read(member)
        y = pd.read_csv(io.BytesIO(labels_raw))['Label'].to_numpy(dtype=np.int8)
    with zipfile.ZipFile(ROOT/f'cache/{MODEL}.score-range.zip') as z:
        score_raw = z.read(f'scores/{stem}.npy')
        scores = np.load(io.BytesIO(score_raw), allow_pickle=False)
    n = len(y)
    yy, ss = np.array([0, 1, 0, 0, 1, 0], dtype=np.int8), np.arange(6, dtype=float)
    warm_start = time.perf_counter()
    if method == 'sparse_numba':
        sparse_vus_jit(yy, ss, 4)
        calculate = lambda: sparse_vus_jit(y, scores, WIDTH)
    else:
        dtaianomaly_vus(yy, ss, 4, 6)
        calculate = lambda: dtaianomaly_vus(y, scores, WIDTH, n if method.endswith('_exact') else 250)
    output.put({'phase': 'warm', 'warm_seconds': time.perf_counter()-warm_start,
                'label_sha256': hashlib.sha256(labels_raw).hexdigest(),
                'score_sha256': hashlib.sha256(score_raw).hexdigest(), 'n': n,
                'threads': numba.get_num_threads(), 'threadpool_info': threadpool_info(),
                'python': sys.version, 'executable': sys.executable,
                'numpy': np.__version__, 'numba': numba.__version__, 'pandas': pd.__version__})
    for repeat in range(3):
        # perf_counter is a shared monotonic clock on supported Python 3.11+.
        output.put({'phase': 'start', 'repeat': repeat, 'started': time.perf_counter()})
        started = time.perf_counter()
        value = calculate()
        elapsed = time.perf_counter()-started
        output.put({'phase': 'result', 'repeat': repeat,
                    'result': [float(v) for v in value], 'seconds': elapsed})
    output.put({'phase': 'complete'})


def run_method(stem, method):
    ctx = mp.get_context('spawn')
    messages = ctx.Queue()
    process = ctx.Process(target=worker, args=(stem, method, messages))
    process.start()
    result = {'method': method, 'status': 'UNKNOWN', 'calls': []}
    deadline = time.perf_counter()+180  # separate startup/JIT allowance
    started = None
    try:
        while True:
            remaining = max(0.001, deadline-time.perf_counter())
            try:
                message = messages.get(timeout=min(1.0, remaining))
            except queue.Empty:
                if process.is_alive() and time.perf_counter() < deadline:
                    continue
                if not process.is_alive():
                    result['status'] = 'ERROR'; result['exitcode'] = process.exitcode
                else:
                    result['status'] = 'TIMEOUT' if started is not None else 'STARTUP_TIMEOUT'
                    result['budget_seconds'] = LIMIT if started is not None else 180
                    if started is not None:
                        result['elapsed_to_termination_request'] = time.perf_counter()-started
                break
            if message['phase'] == 'warm':
                result.update({k: v for k, v in message.items() if k != 'phase'})
            elif message['phase'] == 'start':
                started = message['started']; deadline = started+LIMIT
            elif message['phase'] == 'result':
                result['calls'].append({k: v for k, v in message.items() if k != 'phase'})
                if message['seconds'] > LIMIT or time.perf_counter() > deadline:
                    result.update(status='TIMEOUT', budget_seconds=LIMIT,
                                  censor_reason='Result completed or arrived after the announced call budget')
                    break
                started = None; deadline = time.perf_counter()+10
            elif message['phase'] == 'complete':
                if len(result['calls']) != 3:
                    result['status'] = 'ERROR'; result['error'] = 'Missing timing repetitions'
                    break
                result['status'] = 'COMPLETE'
                result['median_seconds'] = statistics.median(c['seconds'] for c in result['calls'])
                break
    finally:
        if result['status'] != 'COMPLETE' and process.is_alive():
            process.terminate()
        process.join(timeout=10)
        if process.is_alive():
            process.kill(); process.join()
        messages.close()
    return result


def validate_worker_receipt(measured, row, expected_score):
    from verify_artifact import numeric
    for field, expected in [('n', row['n']), ('label_sha256', row['label_member_sha256']),
                            ('score_sha256', expected_score), ('threads', 1)]:
        if measured.get(field) != expected:
            raise ValueError(f'worker input or environment mismatch: {field}')
    for pool in measured.get('threadpool_info', []):
        if pool['num_threads'] != 1:
            raise ValueError('worker thread pool is not single-threaded')
    for call in measured['calls']:
        if numeric(call['seconds'], 'call duration') <= 0:
            raise ValueError('invalid call duration')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--freeze', action='store_true')
    args = parser.parse_args()
    if args.freeze:
        print(json.dumps(freeze_protocol(), indent=2)); return
    import numpy as np
    from verify_artifact import finite_tree, discrepancy
    destination = ART/'external_supplement.jsonl'
    selection_path = ART/'external_supplement_selection.json'
    summary_path = ART/'external_supplement_summary.json'
    environment_path = ART/'external_supplement_environment.json'
    if any(p.exists() for p in (destination, selection_path, summary_path, environment_path)):
        raise FileExistsError('Preserve prior supplement outputs; do not overwrite')
    protocol_path = ART/'external_supplement_protocol.json'
    main_path = ART/'public_benchmark.jsonl'
    gate_path = ART/'final_artifact_gate.json'
    score_receipt_path = ART/f'{MODEL}-download.json'
    bound_paths = [protocol_path, main_path, gate_path, score_receipt_path]
    bound_hashes = {str(p.relative_to(ROOT)): digest(p) for p in bound_paths}
    protocol = json.loads(protocol_path.read_text())
    if (protocol['model'], protocol['maximum_buffer'], protocol['repetitions'],
        protocol['per_call_budget_seconds']) != (MODEL, WIDTH, 3, LIMIT):
        raise ValueError('protocol differs from this implementation')
    gate = json.loads(gate_path.read_text())
    if gate['status'] != 'PASS' or gate['input_sha256']['public_benchmark.jsonl'] != digest(main_path):
        raise ValueError('A PASS final gate bound to these main records is required')
    if gate['gate_source_sha256'] != digest(ROOT/'experiments/verify_artifact.py'):
        raise ValueError('Rerun current artifact gate before the supplement')
    rows = [json.loads(x) for x in main_path.read_text().splitlines()]
    if len(rows) != gate['metric_evaluations'] or len({r['series'] for r in rows}) != gate['unique_series']:
        raise ValueError('main coverage differs from its verified receipt')
    score_hashes = {Path(v['path']).stem: v['sha256']
                    for v in json.loads(score_receipt_path.read_text())['members']}
    families = defaultdict(list)
    for row in rows:
        if row['model'] == MODEL and row['max_buffer'] == WIDTH:
            families[row['family']].append(row)
    selected = []
    for family, items in sorted(families.items()):
        ordered = sorted(items, key=lambda r: (r['n'], r['series']))
        for i in sorted({0, len(ordered)//2}):
            selected.append(ordered[i])
    selection_path.write_text(json.dumps([{'series': r['series'], 'family': r['family'], 'n': r['n'],
                        'support_fraction': r['support_points']/r['n'],
                        'label_sha256': r['label_member_sha256'], 'score_sha256': score_hashes[r['series']]}
                        for r in selected], indent=2)+'\n')
    bound_hashes[str(selection_path.relative_to(ROOT))] = digest(selection_path)
    source_files = [Path(__file__), ROOT/'experiments/dtaianomaly_adapter.py',
                    ROOT/'experiments/verify_artifact.py',
                    ROOT/'src/sparse_vus/core.py', ROOT/'src/sparse_vus/compiled.py',
                    ROOT/'.cache/dtaianomaly/_volume_under_surface_metrics.py']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    import numba
    environment = {'started_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
        'machine': platform.machine(), 'numpy': np.__version__, 'numba': numba.__version__,
        'thread_environment': {k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS',
            'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMBA_NUM_THREADS')},
        'source_sha256': hashes, 'input_sha256': bound_hashes}
    if sys.platform == 'darwin':
        environment['cpu'] = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip()
        environment['memory_bytes'] = int(subprocess.check_output(['sysctl', '-n', 'hw.memsize'], text=True))
    environment_path.write_text(json.dumps(environment, indent=2)+'\n')
    rng = np.random.default_rng(protocol['seed']); output_rows = []
    with destination.open('w') as out:
        for row in selected:
            methods = list(protocol['methods']); rng.shuffle(methods)
            result = {'series': row['series'], 'family': row['family'], 'n': row['n'],
                      'model': MODEL, 'max_buffer': WIDTH, 'methods': {}}
            for method in methods:
                measured = run_method(row['series'], method)
                result['methods'][method] = measured
                try:
                    finite_tree(measured)
                    if measured['status'] not in ('COMPLETE', 'TIMEOUT'):
                        raise RuntimeError(f'supplement worker failure: {measured}')
                    validate_worker_receipt(measured, row, score_hashes[row['series']])
                    target = row['sampled250'] if method == 'dtaianomaly250' else row['exact']
                    for call in measured['calls']:
                        call['target_error'] = discrepancy(call['result'], target)
                        if call['target_error'] > protocol['parity_tolerance']:
                            raise ValueError(f'supplement parity failure: {row["series"]} {method}')
                except Exception as exc:
                    result['status'] = 'FAIL'; result['error'] = f'{type(exc).__name__}: {exc}'
                    out.write(json.dumps(result)+'\n'); out.flush()
                    summary_path.write_text(json.dumps({'status': 'FAIL', 'error': result['error'],
                        'completed_cases': len(output_rows), 'failed_series': row['series'],
                        'input_sha256': bound_hashes, 'source_sha256': hashes}, indent=2)+'\n')
                    raise
            finite_tree(result)
            output_rows.append(result); out.write(json.dumps(result)+'\n'); out.flush()
            print(json.dumps({'completed': len(output_rows), 'selected': len(selected), 'series': row['series'],
                              'status': {k: v['status'] for k, v in result['methods'].items()}}), flush=True)
    for path, expected_digest in {**hashes, **bound_hashes}.items():
        if digest(ROOT/path) != expected_digest:
            summary_path.write_text(json.dumps({'status': 'FAIL', 'error': f'Bound source or input changed: {path}'})+'\n')
            raise ValueError(f'source or input changed during supplement: {path}')
    summary = {'status': 'PASS', 'scope': 'Post-review length-stratified cross-family supplement',
               'series': len(selected), 'families': len(families), 'model': MODEL, 'max_buffer': WIDTH,
               'source_sha256': hashes, 'input_sha256': bound_hashes,
               'completed_utc': datetime.now(timezone.utc).isoformat(),
               'environment_sha256': digest(environment_path),
               'protocol_sha256': digest(protocol_path),
               'records_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'comparisons': {}}
    for method in protocol['methods']:
        complete = [r for r in output_rows if r['methods'][method]['status'] == 'COMPLETE']
        paired = [r for r in complete if r['methods']['sparse_numba']['status'] == 'COMPLETE']
        ratios = [r['methods'][method]['median_seconds']/r['methods']['sparse_numba']['median_seconds'] for r in paired]
        summary['comparisons'][method] = {'complete': len(complete), 'timeout': len(output_rows)-len(complete),
            'paired_complete': len(paired), 'median_ratio_on_complete_pairs': float(np.median(ratios)) if ratios else None,
            'min_ratio_on_complete_pairs': min(ratios) if ratios else None,
            'max_ratio_on_complete_pairs': max(ratios) if ratios else None}
    summary['max_error'] = max(c['target_error'] for r in output_rows for m in r['methods'].values() for c in m['calls'])
    finite_tree(summary)
    summary_path.write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
