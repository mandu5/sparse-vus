"""Frozen native TimeEval recalculation study; manifest and tiny validation first.

No real timing is permitted without a separately frozen global protocol whose
timeeval_consumer section matches the read-only manifest produced here.
"""
from __future__ import annotations

import os
THREAD_VARIABLES = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
                    'NUMBA_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')
for _variable in THREAD_VARIABLES:
    os.environ[_variable] = '1'

import argparse
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import itertools
import json
import logging
from pathlib import Path
import platform
import shutil
import signal
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
REVISION = '7c3622757b1a3afa9a84cbc97ce132d9e379f715'
METRICS = ('ROC_AUC', 'PR_AUC', 'RANGE_PR_AUC')
METHODS = ('public', 'raster', 'bucket')
CONTRACTS = ('native_default50', 'all_observed')
IDS = ('algorithm', 'hyper_params_id', 'collection', 'dataset', 'repetition')
SOURCE_ANCHORS = {
    'timeeval/metrics/__init__.py': '3d79e78d897e4b027f5b6c070a36a77e148bc2e08c429f929d14859df2513ced',
    'timeeval/metrics/metric.py': '2333740807f8573784210b0796da16cae8d7b0aa81f391a0e43af0f3daf1f320',
    'timeeval/metrics/auc_metrics.py': 'dcf1c0cfe11cfed7b7b6acb1fc32e5d1041145da0bfb361768fc1d3b291b0feb',
    'timeeval/metrics/range_metrics.py': 'ba45a0cd3994c075de1026bbbe086ba7a03d0c7a86ca894d1d0cfe854521f5c4',
    'scripts/recalculate_metrics.py': 'f374fed35411a0b54afef844b9ff60139e607e88034c7768c3396fbae35564e5',
}
PROJECT_SOURCES = ('scripts/run_timeeval_strengthening.py',
                   'src/sparse_vus/timeeval_adapter.py',
                   'src/sparse_vus/weighted_range.py', 'src/sparse_vus/range_sweep.py',
                   'src/sparse_vus/__init__.py', 'src/sparse_vus/core.py')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write_new(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def append(handle, value):
    handle.write(json.dumps(value, allow_nan=False) + '\n')
    handle.flush()


def tree_hashes(root):
    excluded = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', 'build', 'dist'}
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not excluded.intersection(p.relative_to(root).parts)
            and not any(part.endswith('.egg-info') for part in p.relative_to(root).parts)
            and p.suffix not in ('.pyc', '.pyo') and p.name != '.DS_Store'}


def versions():
    names = ('timeeval', 'prts', 'numpy', 'scipy', 'scikit-learn', 'pandas',
             'numba', 'llvmlite', 'joblib', 'threadpoolctl', 'dask', 'distributed',
             'multiprocessing_logging', 'tqdm')
    return {name: importlib.metadata.version(name) for name in names}


def design():
    return {
        'metrics': list(METRICS), 'methods': list(METHODS),
        'contracts': {
            'native_default50': {'max_samples': 50, 'r_alpha': 0, 'p_alpha': 0,
                                 'cardinality': 'one', 'bias': 'flat'},
            'all_observed': {'max_samples': 'positive_infinity', 'r_alpha': 0,
                             'p_alpha': 0, 'cardinality': 'one', 'bias': 'flat'},
        },
        'orders': [list(p) for p in itertools.permutations(METHODS)],
        'n_jobs': 1, 'numerical_threads': 1, 'atol': 1e-10, 'rtol': 0,
        'workflow_timeout_seconds': 600,
        'censor_rule': 'After first timeout for a method/contract/batch, mark all remaining attempts for that key notrun_due_to_prespecified_censor; do not replace inputs. Other keys continue.',
        'timed': 'Native MetricComputor constructor plus recompute(True), including dataset/results/score/optional-metrics CSV reads, default three metrics, final results.csv write/close, and one wall-clock deadline arming call. Deadline-handler setup and cleanup are outside the interval.',
        'excluded': 'Imports, source/input hash audits, environment/log setup, metric-object creation, tiny JIT warmup, trial-template copying/filtering, post-run parity audit and summaries. No cold-disk/fsync/training claim.',
        'all_observed_semantics': 'Native unique-score queries except the minimum, native synthetic first/last points, >= eligibility, lexsort and trapezoidal integration; only max_samples is configured to infinity.',
        'query_accounting': 'Read-only native score distinct counts and exact source-sampler query counts are frozen per profile/contract. max_samples=50 is nominal, not a hard cap. Constant-score profiles would use the native zero shortcut without curve evaluation.',
        'uncertainty': 'Six paired orders of fixed workloads; approximate paired-order bootstrap intervals describe execution variability and order sensitivity, not recording or deployment populations. No cross-contract speed ratios. No interval without all six completed matched pairs.',
        'bootstrap': {'samples': 10000, 'seed': 20261024},
        'order_of_work': 'contracts in declared order, combined batch then sorted families, six method permutations per batch',
    }


def workload_rows(workload):
    import pandas as pd
    rows = pd.read_csv(workload / 'results/results.csv')
    required = set(IDS) | {'status'}
    if not required.issubset(rows.columns) or rows.empty or rows[list(IDS)].duplicated().any():
        raise ValueError('nonempty unique native result identifiers and status required')
    if set(METRICS).intersection(rows.columns):
        raise ValueError('input results template must not contain stale output metric columns')
    if set(rows.status) != {'Status.OK'}:
        raise ValueError('study requires successful generated profiles; preserve failures in generation receipt')
    for row in rows.itertuples(index=False):
        score = workload / 'results' / str(row.algorithm) / str(row.hyper_params_id) / str(row.collection) / str(row.dataset) / str(row.repetition) / 'anomaly_scores.ts'
        if not score.is_file():
            raise ValueError('missing native score file: ' + str(score))
    return rows


def source_check(source):
    for name, expected in SOURCE_ANCHORS.items():
        if digest(source / name) != expected:
            raise ValueError('pinned native source mismatch: ' + name)
    if not (source / 'timeeval/_version.py').exists():
        raise ValueError('complete TimeEval source tree required, not selected-source cache')


def input_hashes(workload):
    return {**{'datasets/' + k: v for k, v in tree_hashes(workload / 'datasets').items()},
            **{'results/' + k: v for k, v in tree_hashes(workload / 'results').items()}}


def source_thresholds(unique_scores, max_samples):
    """The pinned native sampler, without evaluating labels or metric values."""
    import numpy as np
    thresholds = unique_scores[1:]
    n_thresholds = thresholds.shape[0]
    if n_thresholds > max_samples:
        every_nth = n_thresholds // (max_samples - 1)
        sampled_thresholds = thresholds[::every_nth]
        if thresholds[-1] == sampled_thresholds[-1]:
            thresholds = sampled_thresholds
        else:
            thresholds = np.r_[sampled_thresholds, thresholds[-1]]
    return thresholds


def query_plan(workload, rows):
    import numpy as np
    plan = []
    for row in rows.itertuples(index=False):
        score_path = workload / 'results' / str(row.algorithm) / str(row.hyper_params_id) / str(row.collection) / str(row.dataset) / str(row.repetition) / 'anomaly_scores.ts'
        scores = np.atleast_1d(np.genfromtxt(score_path, delimiter=','))
        if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
            raise ValueError('query planning requires finite native score vectors')
        unique_scores = np.unique(scores)
        contracts = {}
        for contract, maximum in [('native_default50', 50), ('all_observed', float('inf'))]:
            queries = source_thresholds(unique_scores, maximum)
            contracts[contract] = {'emitted_queries': len(queries),
                'thresholds_binary64_le_sha256': hashlib.sha256(np.asarray(queries, dtype='<f8').tobytes()).hexdigest()}
        plan.append({**{name: str(getattr(row, name)) for name in IDS},
                     'n': len(scores), 'distinct_scores': len(unique_scores),
                     'constant_score_shortcut': len(unique_scores) == 1, 'contracts': contracts})
    return plan


def workload_receipts(workload, rows, generation_path, audit_path):
    generation, audit = json.loads(generation_path.read_text()), json.loads(audit_path.read_text())
    if generation.get('status') != 'ALL_SELECTED_PROFILES_GENERATED' or generation.get('metric_evaluation_performed') is not False:
        raise ValueError('complete pre-metric workload generation receipt required')
    if generation.get('successful_profiles') != len(rows) or generation.get('selected_profiles') != len(rows):
        raise ValueError('workload generation coverage differs from native result rows')
    if audit.get('status') != 'NATIVE_INPUTS_VERIFIED_WITHOUT_METRIC_EVALUATION' or audit.get('metric_evaluation_performed') is not False:
        raise ValueError('native input audit without metric evaluation required')
    if audit.get('profiles_verified') != len(rows) or audit.get('generation_sha256') != digest(generation_path):
        raise ValueError('native input audit does not bind this generation receipt')
    layout = generation['native_layout']
    for relative, key in [('datasets/datasets.csv', 'datasets_sha256'),
                          ('results/results.csv', 'results_sha256')]:
        if digest(workload / relative) != layout[key]:
            raise ValueError('native CSV differs from generation receipt: ' + relative)
    profiles = {(p['model'], p['case_id']): p for p in generation['profiles']}
    if len(profiles) != len(rows):
        raise ValueError('generation receipt profile identities are missing or duplicated')
    for row in rows.itertuples(index=False):
        profile = profiles.get((str(row.algorithm), str(row.dataset)))
        score = workload / 'results' / str(row.algorithm) / str(row.hyper_params_id) / str(row.collection) / str(row.dataset) / str(row.repetition) / 'anomaly_scores.ts'
        if profile is None or profile.get('status') != 'Status.OK' or digest(score) != profile['native_score_sha256']:
            raise ValueError('native score differs from successful generation receipt')
    return {name: {'path': str(path.resolve()), 'sha256': digest(path)}
            for name, path in [('generation', generation_path), ('native_input_audit', audit_path)]}


def manifest(workload, source, generation_path, audit_path):
    workload, source = workload.resolve(), source.resolve()
    source_check(source)
    rows = workload_rows(workload)
    families = sorted(str(v) for v in rows.collection.unique())
    if len(families) != 3:
        raise ValueError('the frozen study requires exactly three declared families')
    batches = [{'name': 'combined', 'families': families, 'row_count': len(rows)}]
    for i, family in enumerate(families):
        batches.append({'name': f'family-{i}-{family}', 'families': [family],
                        'row_count': int((rows.collection.astype(str) == family).sum())})
    queries = query_plan(workload, rows)
    for batch in batches:
        selected = [p for p in queries if p['collection'] in batch['families']]
        batch['query_counts'] = {}
        for contract in CONTRACTS:
            counts = [p['contracts'][contract]['emitted_queries'] for p in selected]
            batch['query_counts'][contract] = {'total': sum(counts), 'minimum': min(counts),
                                               'maximum': max(counts)}
    dependency_versions = versions()
    if dependency_versions['prts'] != '1.0.0.3':
        raise ValueError('pinned prts 1.0.0.3 required')
    import prts
    return {
        'schema': 'timeeval-consumer-study-v1',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_repository': 'https://github.com/TimeEval/TimeEval',
        'source_revision': REVISION, 'source_directory': str(source),
        'workload_directory': str(workload),
        'source_sha256': tree_hashes(source),
        'input_sha256': input_hashes(workload),
        'workload_receipts': workload_receipts(workload, rows, generation_path, audit_path),
        'project_sha256': {name: digest(ROOT / name) for name in PROJECT_SOURCES},
        'prts_directory': str(Path(prts.__file__).parent.resolve()),
        'prts_sha256': tree_hashes(Path(prts.__file__).parent),
        'python_version': platform.python_version(), 'dependencies': dependency_versions,
        'batches': batches, 'query_plan': queries, 'design': design(),
        'row_ids': rows[list(IDS)].astype(str).values.tolist(),
        'records': len(rows), 'timing_or_metric_outcomes_consumed': False,
    }


def verify_bindings(payload):
    if payload.get('schema') != 'timeeval-consumer-study-v1' or payload['design'] != design():
        raise ValueError('frozen study design differs from this runner')
    source = Path(payload['source_directory'])
    workload = Path(payload['workload_directory'])
    source_check(source)
    import prts
    if Path(prts.__file__).parent.resolve() != Path(payload['prts_directory']).resolve():
        raise ValueError('runtime prts import differs from bound source directory')
    actual = {'source_sha256': tree_hashes(source), 'input_sha256': input_hashes(workload),
              'project_sha256': {name: digest(ROOT / name) for name in PROJECT_SOURCES},
              'prts_sha256': tree_hashes(Path(payload['prts_directory']))}
    for key, hashes in actual.items():
        if hashes != payload[key]:
            raise ValueError(f'{key} binding mismatch, including added or removed files')
    for name, receipt in payload['workload_receipts'].items():
        if digest(receipt['path']) != receipt['sha256']:
            raise ValueError('workload receipt binding mismatch: ' + name)
    if versions() != payload['dependencies'] or platform.python_version() != payload['python_version']:
        raise ValueError('runtime environment differs from per-host frozen manifest')
    actual_ids = workload_rows(workload)[list(IDS)].astype(str).values.tolist()
    if actual_ids != payload['row_ids']:
        raise ValueError('frozen native row identity/order mismatch')
    return workload, source


def load_native(source):
    sys.path[:0] = [str(ROOT / 'src'), str(source)]
    import timeeval
    if Path(timeeval.__file__).resolve() != (source / 'timeeval/__init__.py').resolve():
        raise ValueError('native consumer must load the bound source tree in a fresh process')
    spec = importlib.util.spec_from_file_location('_native_timeeval_recalculation', source / 'scripts/recalculate_metrics.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if list(module._metrics[k].name for k in METRICS) != list(METRICS):
        raise ValueError('native metric names differ')
    return module


def metric_suite(native, method, contract):
    from sparse_vus.timeeval_adapter import adapt_range_metric
    metrics = [deepcopy(native._metrics[name]) for name in METRICS]
    if contract == 'all_observed':
        metrics[-1]._max_samples = float('inf')
    elif contract != 'native_default50':
        raise ValueError('unknown consumer contract')
    metrics[-1] = adapt_range_metric(metrics[-1], method)
    return metrics


def warmup(native):
    import numpy as np
    y = np.array([0,1,1,0,1,0,0,1,1,0], dtype=np.float64)
    x = np.array([0,3,2,1,4,2,1,2,3,0], dtype=np.float64)
    for contract in CONTRACTS:
        for method in METHODS:
            for metric in metric_suite(native, method, contract):
                value = metric(y, x)
                if not np.isfinite(value):
                    raise ValueError('nonfinite tiny warmup metric')


class WorkflowTimeout(BaseException):
    """Escape the native per-metric ``except Exception`` instead of swallowing deadlines."""


@contextmanager
def deadline(seconds):
    def expired(signum, frame):
        raise WorkflowTimeout(f'native workflow exceeded {seconds} seconds')
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    if previous_timer[0] != 0:
        raise ValueError('runner requires ownership of the process wall-clock timer')
    signal.signal(signal.SIGALRM, expired)
    started = time.perf_counter_ns()
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield started
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def copy_trial(workload, trial_dir, rows, combined):
    trial_dir.mkdir(parents=True, exist_ok=False)
    target = trial_dir / 'results'
    shutil.copytree(workload / 'results', target)
    if not combined:
        rows.to_csv(target / 'results.csv', index=False)
    return target


def execute(native, workload, result_dir, trial_dir, metrics, timed):
    with (trial_dir / 'stdout.log').open('x') as stdout, (trial_dir / 'stderr.log').open('x') as stderr:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            if not timed:
                consumer = native.MetricComputor(result_dir, [workload / 'datasets'], metrics,
                                                 save_to_dir=False, n_jobs=1)
                consumer.recompute(recompute_existing=True)
                return {'status': 'COMPLETE', 'timing_performed': False}
            try:
                with deadline(600) as started:
                    consumer = native.MetricComputor(result_dir, [workload / 'datasets'], metrics,
                                                     save_to_dir=False, n_jobs=1)
                    consumer.recompute(recompute_existing=True)
                    elapsed = (time.perf_counter_ns() - started) * 1e-9
                return {'status': 'COMPLETE', 'seconds': elapsed}
            except WorkflowTimeout as exc:
                return {'status': 'TIMEOUT', 'seconds': (time.perf_counter_ns() - started) * 1e-9,
                        'completion_seconds_lower_bound': 600, 'error': str(exc)}


def audit_output(path, expected_rows):
    import numpy as np
    import pandas as pd
    frame = pd.read_csv(path)
    if len(frame) != len(expected_rows) or not set(METRICS).issubset(frame.columns):
        raise ValueError('native consumer omitted rows or default metric outputs')
    if frame[list(IDS)].astype(str).values.tolist() != expected_rows[list(IDS)].astype(str).values.tolist():
        raise ValueError('native result identity/order changed')
    values = frame[list(METRICS)].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('nonfinite/missing native metric outputs, including swallowed upstream failures')
    return frame, values


def compare_values(actual, expected):
    import numpy as np
    if actual.shape != expected.shape:
        raise ValueError('default-three scalar output shape differs')
    difference = float(np.max(np.abs(actual - expected)))
    if difference > 1e-10:
        raise ValueError(f'default-three scalar parity exceeded 1e-10: {difference}')
    return difference


def configure_logging(out):
    logging.basicConfig(filename=out / 'native-consumer.log', filemode='x', level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s', force=True)


def validate_tiny(workload, source, out):
    import numpy as np
    rows = workload_rows(workload)
    if len(rows) > 6:
        raise ValueError('tiny validation is limited to six rows; real inputs require global freeze')
    total_points = sum(np.atleast_1d(np.loadtxt(p)).size for p in (workload / 'results').rglob('anomaly_scores.ts'))
    if total_points > 512:
        raise ValueError('tiny validation is limited to 512 score points')
    source_check(source)
    configure_logging(out)
    native = load_native(source)
    warmup(native)
    errors = []
    for contract in CONTRACTS:
        reference = None
        for method in METHODS:
            trial = out / (contract + '-' + method)
            result_dir = copy_trial(workload, trial, rows, combined=True)
            execute(native, workload, result_dir, trial, metric_suite(native, method, contract), timed=False)
            frame, values = audit_output(result_dir / 'results.csv', rows)
            if reference is None:
                reference = values
            errors.append(compare_values(values, reference))
    write_new(out / 'complete.json', {'status': 'TINY_NATIVE_CONSUMER_VALIDATED',
              'row_count': len(rows), 'methods': list(METHODS), 'contracts': list(CONTRACTS),
              'max_absolute_error': max(errors), 'timing_performed': False,
              'source_revision': REVISION})


def summarize(records, payload):
    import numpy as np
    result = {}
    pairs = [('public', 'bucket'), ('raster', 'bucket'), ('public', 'raster')]
    for contract in CONTRACTS:
        result[contract] = {}
        for batch in payload['batches']:
            selected = [r for r in records if r['contract'] == contract and r['batch'] == batch['name']]
            keyed = {(r['round'], r['method']): r for r in selected}
            comparisons = {}
            for baseline, candidate in pairs:
                ratios, bounds = [], []
                for repeat in range(6):
                    a, b = keyed[repeat, baseline], keyed[repeat, candidate]
                    if a['status'] == b['status'] == 'COMPLETE':
                        ratios.append(a['seconds'] / b['seconds'])
                    elif a['status'] == 'TIMEOUT' and b['status'] == 'COMPLETE':
                        bounds.append({'round': repeat, 'strict_speedup_lower_bound': a['completion_seconds_lower_bound'] / b['seconds']})
                item = {'completed_paired_rounds': len(ratios), 'paired_speedups': ratios,
                        'censored_bounds': bounds, 'approximate_paired_order_ci95': None}
                if len(ratios) == 6:
                    z = np.log(ratios)
                    samples = np.random.default_rng(20261024).integers(6, size=(10000, 6))
                    item.update(geometric_speedup=float(np.exp(z.mean())),
                                approximate_paired_order_ci95=np.exp(np.quantile(z[samples].mean(axis=1), [.025, .975])).tolist())
                else:
                    item['interval_unavailable_reason'] = 'six complete paired orders required; censored/not-run attempts are not fabricated observations'
                comparisons[baseline + '_over_' + candidate] = item
            result[contract][batch['name']] = {'comparisons': comparisons,
                'status_counts': {status: sum(r['status'] == status for r in selected)
                                  for status in ('COMPLETE', 'TIMEOUT', 'notrun_due_to_prespecified_censor')}}
    return result


def run(protocol_path, protocol_sha256, out):
    if digest(protocol_path) != protocol_sha256:
        raise ValueError('global protocol SHA256 mismatch')
    global_protocol = json.loads(protocol_path.read_text())
    if not str(global_protocol.get('status', '')).startswith('FROZEN'):
        raise ValueError('real timing requires a separately FROZEN global protocol')
    payload = global_protocol['timeeval_consumer']
    workload, source = verify_bindings(payload)
    write_new(out / 'bound-protocol.json', global_protocol)
    configure_logging(out)
    native = load_native(source)
    warmup(native)
    from threadpoolctl import threadpool_info, threadpool_limits
    import numba
    rows = workload_rows(workload)
    records, censored, references, group_values = [], {}, {}, {}
    write_new(out / 'run-start.json', {'utc': datetime.now(timezone.utc).isoformat(),
              'global_protocol_sha256': protocol_sha256, 'platform': platform.platform(),
              'python': sys.version, 'dependencies': versions(), 'warmup_completed': True})
    with threadpool_limits(limits=1), (out / 'trials.jsonl').open('x') as trace, (out / 'metrics.jsonl').open('x') as metrics_trace:
        if numba.get_num_threads() != 1:
            raise ValueError('single numerical thread contract violated')
        write_new(out / 'threadpools.json', threadpool_info())
        ordinal = 0
        for contract in CONTRACTS:
            for batch in payload['batches']:
                batch_rows = rows[rows.collection.astype(str).isin(batch['families'])].copy()
                if len(batch_rows) != batch['row_count']:
                    raise ValueError('batch row coverage mismatch')
                group = (contract, batch['name'])
                for repeat, order in enumerate(payload['design']['orders']):
                    for position, method in enumerate(order):
                        identity = {'trial': ordinal, 'contract': contract, 'batch': batch['name'],
                                    'round': repeat, 'position': position, 'method': method,
                                    'row_count': len(batch_rows)}
                        ordinal += 1
                        key = (method, contract, batch['name'])
                        if key in censored:
                            record = {**identity, 'status': 'notrun_due_to_prespecified_censor',
                                      'first_censored_trial': censored[key]}
                            records.append(record); append(trace, record)
                            continue
                        trial = out / 'trials' / f"{identity['trial']:03d}-{contract}-{batch['name']}-{method}"
                        result_dir = copy_trial(workload, trial, batch_rows, batch['name'] == 'combined')
                        metrics = metric_suite(native, method, contract)
                        outcome = execute(native, workload, result_dir, trial, metrics, timed=True)
                        record = {**identity, **outcome, 'directory': str(trial.relative_to(out))}
                        records.append(record); append(trace, record)
                        if outcome['status'] == 'TIMEOUT':
                            censored[key] = identity['trial']
                            continue
                        frame, values = audit_output(result_dir / 'results.csv', batch_rows)
                        group_values.setdefault(group, []).append(values)
                        if method == 'public' and group not in references:
                            references[group] = values
                        reference = references.get(group, group_values[group][0])
                        error = compare_values(values, reference)
                        if method == 'public':
                            for earlier in group_values[group]:
                                error = max(error, compare_values(earlier, values))
                        append(metrics_trace, {**identity, 'max_error_against_available_reference': error,
                               'public_reference_available': group in references,
                               'results_sha256': digest(result_dir / 'results.csv'),
                               'rows': frame[list(IDS) + list(METRICS)].to_dict(orient='records')})
                        print(f"{contract} {batch['name']} round={repeat} {method}: {outcome['seconds']:.6f}s", flush=True)
    verify_bindings(payload)
    expected_count = len(CONTRACTS) * len(payload['batches']) * 6 * len(METHODS)
    if len(records) != expected_count:
        raise ValueError('planned trial coverage incomplete')
    write_new(out / 'summary.json', {'comparisons': summarize(records, payload),
              'public_parity_available': {f'{c}/{b}': (c,b) in references for c in CONTRACTS for b in [x['name'] for x in payload['batches']]},
              'uncertainty_scope': payload['design']['uncertainty']})
    write_new(out / 'complete.json', {'status': 'COMPLETE_WITH_CENSORING' if censored else 'COMPLETE',
              'planned_trials': expected_count, 'recorded_trials': len(records),
              'timed_attempts': sum(r['status'] != 'notrun_due_to_prespecified_censor' for r in records),
              'censored_keys': len(censored), 'global_protocol_sha256': protocol_sha256,
              'trials_sha256': digest(out / 'trials.jsonl'), 'metrics_sha256': digest(out / 'metrics.jsonl'),
              'summary_sha256': digest(out / 'summary.json')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('manifest', 'validate'):
        p = sub.add_parser(name)
        p.add_argument('--workload', type=Path, required=True)
        p.add_argument('--source', type=Path, default=ROOT / '.cache/strengthening-timeeval-full')
        p.add_argument('--out', type=Path, required=True)
        if name == 'manifest':
            p.add_argument('--generation-receipt', type=Path, required=True)
            p.add_argument('--native-input-audit', type=Path, required=True)
    p = sub.add_parser('run')
    p.add_argument('--protocol', type=Path, required=True)
    p.add_argument('--protocol-sha256', required=True)
    p.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'manifest':
        args.out.parent.mkdir(parents=True, exist_ok=True)
        write_new(args.out, manifest(args.workload, args.source,
                                   args.generation_receipt, args.native_input_audit))
        print(args.out)
        return
    args.out.mkdir(parents=True, exist_ok=False)
    try:
        if args.command == 'validate':
            validate_tiny(args.workload.resolve(), args.source.resolve(), args.out.resolve())
        else:
            run(args.protocol.resolve(), args.protocol_sha256, args.out.resolve())
    except BaseException as exc:
        write_new(args.out / 'failure.json', {'status': 'FAILED', 'error_type': type(exc).__name__,
                  'error': str(exc), 'traceback': traceback.format_exc(),
                  'utc': datetime.now(timezone.utc).isoformat()})
        raise


if __name__ == '__main__':
    main()
