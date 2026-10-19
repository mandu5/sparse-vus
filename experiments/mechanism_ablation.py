"""Frozen score-preprocessing ablation and synthetic support-density study.

The full-sort adapter feeds the original, unchanged compiled sparse kernel.
Run only after the primary benchmark releases the CPU:

  /opt/anaconda3/bin/python experiments/mechanism_ablation.py --validate-only
  /opt/anaconda3/bin/python experiments/mechanism_ablation.py --run \
      --cpu-clearance 'Builder confirmed main benchmark and scaling finished.'

The standalone validation functions are the adapter's regression tests. They
compare every prepared array before comparing metric values, including ties.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'mechanism_results'
PROTOCOL = ROOT / 'artifacts' / 'mechanism_protocol.json'
RESULTS = ROOT / 'artifacts' / 'mechanism_results.json'
sys.dont_write_bytecode = True
for key in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
            'VECLIB_MAXIMUM_THREADS', 'NUMBA_NUM_THREADS']:
    os.environ[key] = '1'
os.environ['NUMBA_CACHE_DIR'] = str(OUT / '.cache' / 'numba')
os.environ.setdefault('MPLCONFIGDIR', str(OUT / '.cache' / 'matplotlib'))

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import platform
import subprocess
import time

import numba
import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

sys.path.insert(0, str(ROOT / 'src'))
from sparse_vus.core import (_prepare, _validate_inputs, dense_vus, expanded_ranges,
                             nearest_two_interval_distances, ranges)
from sparse_vus.compiled import (_sparse_kernel, dense_vus_direct_jit,
                                 dense_vus_jit, sparse_vus_jit)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_sha256(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def _prepare_fullsort(y, scores, max_buffer):
    """Same sparse preparation, with only the global rank-count step changed."""
    y, scores = _validate_inputs(y, scores, max_buffer)
    n = len(y)
    starts, ends = ranges(y)
    lo, hi = expanded_ranges(starts, ends, n, max_buffer)
    pos = np.concatenate([np.arange(a, b + 1) for a, b in zip(lo, hi)])
    original = y[pos].astype(bool)
    d1, d2 = nearest_two_interval_distances(pos, starts, ends)
    values, inverse = np.unique(scores[pos], return_inverse=True)
    # At threshold v, before counts scores > v and after counts scores >= v.
    # Everything outside this global-count step is identical to _prepare.
    sorted_scores = np.sort(scores)
    before_ascending = n - np.searchsorted(sorted_scores, values, side='right')
    after_ascending = n - np.searchsorted(sorted_scores, values, side='left')
    before, after = before_ascending[::-1], after_ascending[::-1]
    group = len(values) - 1 - inverse
    support_index = np.full(n, -1, dtype=np.int64)
    support_index[pos] = np.arange(len(pos))
    return y, scores, starts, ends, pos, original, d1, d2, group, before, after, support_index


def fullsort_sparse_vus_jit(y, scores, max_buffer):
    values = _prepare_fullsort(y, scores, max_buffer)
    y, scores, starts, ends, pos, original, d1, d2, group, before, after, _ = values
    return _sparse_kernel(len(y), float(y.sum()), starts, ends, pos, original,
                          d1, d2, group, before, after, max_buffer)


METHODS = {
    'sparse_numba': sparse_vus_jit,
    'fullsort_sparse_numba': fullsort_sparse_vus_jit,
    'dense_numpy': dense_vus,
    'dense_numba': dense_vus_jit,
    'dense_direct_numba': dense_vus_direct_jit,
}


def assert_preparation_equal(y, scores, width):
    expected = _prepare(y, scores, width)
    actual = _prepare_fullsort(y, scores, width)
    names = ['y', 'scores', 'starts', 'ends', 'pos', 'original', 'd1', 'd2',
             'group', 'before', 'after', 'support_index']
    assert len(actual) == len(expected) == len(names)
    for name, a, b in zip(names, actual, expected):
        np.testing.assert_array_equal(a, b, err_msg=f'preparation field: {name}')
        assert a.dtype == b.dtype, (name, a.dtype, b.dtype)
    return expected


def validation_cases(spec):
    fixed = [
        ([0, 1, 0, 0, 1, 0], [3, 2, 2, 1, 2, 0], 0),
        ([1, 0, 0, 0, 0, 1], [2, 2, 2, 2, 2, 2], 30),
        ([0, 0, 1, 1, 0, 0, 0, 0], [10, 9, 2, 2, 2, 1, 0, -1], 2),
        ([0, 1, 0, 1, 0, 1, 0, 0], list(range(8)), 1),
        ([0, 0, 0, 0, 0, 1], [2, 1, 0, -1, -2, -3], 100),
    ]
    assert len(fixed) == spec['structured_cases']
    for index, (y, scores, width) in enumerate(fixed):
        yield f'structured-{index}', np.asarray(y, np.int8), np.asarray(scores, float), width
    for index in range(spec['random_cases']):
        rng = np.random.default_rng(np.random.SeedSequence([spec['seed'], index]))
        n = spec['n'][index % len(spec['n'])]
        y = rng.integers(0, 2, size=n, dtype=np.int8)
        y[0], y[-1] = 0, 1
        mode = spec['score_modes'][(index // len(spec['n'])) % len(spec['score_modes'])]
        if mode == 'continuous':
            scores = rng.normal(size=n)
        elif mode == 'quantized3':
            scores = rng.integers(0, 3, size=n).astype(float)
        elif mode == 'binary':
            scores = rng.integers(0, 2, size=n).astype(float)
        elif mode == 'constant':
            scores = np.ones(n)
        elif mode == 'ordered':
            scores = np.arange(n, dtype=float)
        else:
            scores = np.arange(n, dtype=float)[::-1].copy()
        width = spec['widths'][index % len(spec['widths'])]
        yield f'random-{index}', y, scores, width


def validate(spec):
    rows = []
    tolerance = spec['tolerance']['absolute']
    for name, y, scores, width in validation_cases(spec['validation']):
        prepared = assert_preparation_equal(y, scores, width)
        values = {method: np.asarray(function(y, scores, width), dtype=float)
                  for method, function in METHODS.items()}
        np.testing.assert_array_equal(values['fullsort_sparse_numba'], values['sparse_numba'])
        expected = values['dense_numpy']
        errors = {}
        for method, value in values.items():
            assert np.isfinite(value).all(), (name, method, value)
            np.testing.assert_allclose(value, expected, atol=tolerance, rtol=0,
                                       err_msg=f'{name}: {method}')
            errors[method] = float(np.max(np.abs(value - expected)))
        rows.append({'case': name, 'n': len(y), 'max_buffer': width,
                     'support_points': len(prepared[4]), 'support_scores': len(prepared[9]),
                     'label_sha256': array_sha256(y), 'score_sha256': array_sha256(scores),
                     'max_error': max(errors.values()), 'errors': errors,
                     'values': {method: value.tolist() for method, value in values.items()}})
    return {'status': 'passed', 'cases': len(rows), 'preparation_arrays_equal': True,
            'max_error': max(row['max_error'] for row in rows), 'rows': rows}


def grid(spec):
    cases = []
    for n in spec['n']:
        for density_index, density in enumerate(spec['positive_label_densities']):
            positive_points = round(n * density)
            for intervals in spec['positive_interval_counts']:
                if intervals > positive_points:
                    continue
                for width in spec['max_buffer']:
                    cases.append({'case_id': f'n{n}-d{density_index}-k{intervals}-w{width}',
                                  'n': n, 'density_index': density_index,
                                  'positive_label_density': density,
                                  'positive_points': positive_points,
                                  'intervals': intervals, 'max_buffer': width})
    assert len(cases) == spec['feasible_cells']
    np.random.default_rng(spec['case_order_seed']).shuffle(cases)
    return cases


def make_case(case, seed):
    n, intervals, total = case['n'], case['intervals'], case['positive_points']
    y = np.zeros(n, dtype=np.int8)
    quotient, remainder = divmod(total, intervals)
    for j in range(intervals):
        left, right = j * n // intervals, (j + 1) * n // intervals
        length = quotient + (j < remainder)
        start = left + (right - left - length) // 2
        y[start:start + length] = 1
    assert int(y.sum()) == total
    assert len(ranges(y)[0]) == intervals
    rng = np.random.default_rng(np.random.SeedSequence(
        [seed, n, case['density_index'], intervals]))
    return y, rng.normal(size=n)


def check_frozen_core(spec):
    for name, expected in spec['core_sha256'].items():
        if sha256(ROOT / name) != expected:
            raise RuntimeError(f'Frozen core changed: {name}')


def source_hashes(spec):
    names = list(spec['core_sha256']) + ['experiments/mechanism_ablation.py',
                                       'artifacts/mechanism_protocol.json']
    return {name: sha256(ROOT / name) for name in names}


def environment():
    def sysctl(key):
        try:
            return subprocess.check_output(['sysctl', '-n', key], text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    return {'python': sys.version, 'executable': sys.executable,
            'platform': platform.platform(), 'machine': platform.machine(),
            'cpu': sysctl('machdep.cpu.brand_string'), 'memory_bytes': sysctl('hw.memsize'),
            'numpy': np.__version__, 'numba': numba.__version__,
            'numba_threads': numba.get_num_threads(), 'threadpool_info': threadpool_info(),
            'numba_cache_dir': os.environ['NUMBA_CACHE_DIR']}


def timed(function, y, scores, width):
    begin = time.perf_counter_ns()
    result = function(y, scores, width)
    elapsed_ns = time.perf_counter_ns() - begin
    return np.asarray(result, dtype=float), elapsed_ns


def benchmark_case(case, spec, method_rng):
    y, scores = make_case(case, spec['seed'])
    receipts = []
    durations = {name: [] for name in METHODS}
    expected = None
    max_error = 0.0
    for repetition in range(spec['repetitions']):
        order = list(METHODS)
        method_rng.shuffle(order)
        for position, name in enumerate(order):
            value, elapsed_ns = timed(METHODS[name], y, scores, case['max_buffer'])
            if not np.isfinite(value).all():
                raise ArithmeticError(f'Nonfinite metric: {case["case_id"]}, {name}')
            if expected is None:
                expected = value.copy()
            error = float(np.max(np.abs(value - expected)))
            max_error = max(max_error, error)
            if error > spec['tolerance']['absolute']:
                raise ArithmeticError(f'Parity failed: {case["case_id"]}, {name}, {error}')
            durations[name].append(elapsed_ns / 1e9)
            receipts.append({'repetition': repetition, 'order_position': position,
                             'method': name, 'elapsed_ns': elapsed_ns,
                             'value': value.tolist(), 'error_vs_first': error})
    # This extra exact-array check is outside every timed method call.
    prepared = assert_preparation_equal(y, scores, case['max_buffer'])
    sparse_values = [r['value'] for r in receipts if r['method'] in
                     ('sparse_numba', 'fullsort_sparse_numba')]
    for value in sparse_values[1:]:
        np.testing.assert_array_equal(value, sparse_values[0])
    medians = {name: float(np.median(times)) for name, times in durations.items()}
    dense_name = min((name for name in METHODS if name.startswith('dense_')),
                     key=medians.__getitem__)
    sparse_time, fullsort_time = medians['sparse_numba'], medians['fullsort_sparse_numba']
    return {**case, 'label_sha256': array_sha256(y), 'score_sha256': array_sha256(scores),
            'support_points': len(prepared[4]), 'support_scores': len(prepared[9]),
            'support_fraction': len(prepared[4]) / case['n'],
            'support_score_fraction': len(prepared[9]) / case['n'],
            'preparation_arrays_equal': True, 'max_parity_error': max_error,
            'receipts': receipts, 'seconds': durations, 'median_seconds': medians,
            'fastest_dense_method': dense_name,
            'speedup_current_vs_fullsort': fullsort_time / sparse_time,
            'speedup_current_vs_fastest_dense': medians[dense_name] / sparse_time,
            'speedup_fullsort_vs_fastest_dense': medians[dense_name] / fullsort_time}


def ratio_summary(values, spec):
    return {'count': len(values), 'geometric_mean': math.exp(sum(map(math.log, values)) / len(values)),
            'median': float(np.median(values)), 'minimum': min(values), 'maximum': max(values),
            'material_wins': sum(x >= spec['reporting']['material_win_ratio'] for x in values),
            'material_losses': sum(x <= spec['reporting']['material_loss_ratio'] for x in values)}


def summarize(rows, spec):
    names = ['speedup_current_vs_fullsort', 'speedup_current_vs_fastest_dense',
             'speedup_fullsort_vs_fastest_dense']
    result = {'cases': len(rows), 'timed_calls': sum(len(row['receipts']) for row in rows),
              'max_parity_error': max(row['max_parity_error'] for row in rows),
              'all_preparation_arrays_equal': all(row['preparation_arrays_equal'] for row in rows),
              'ratios': {name: ratio_summary([row[name] for row in rows], spec) for name in names},
              'by_n_width': [], 'by_support_fraction': []}
    for n in spec['n']:
        for width in spec['max_buffer']:
            selected = [row for row in rows if row['n'] == n and row['max_buffer'] == width]
            result['by_n_width'].append({'n': n, 'max_buffer': width,
                **{name: ratio_summary([row[name] for row in selected], spec) for name in names}})
    bins = spec['reporting']['support_fraction_bins']
    for lo, hi in zip(bins[:-1], bins[1:]):
        selected = [row for row in rows if lo <= row['support_fraction'] < hi]
        if selected:
            result['by_support_fraction'].append({'lower_inclusive': lo, 'upper_exclusive': hi,
                **{name: ratio_summary([row[name] for row in selected], spec) for name in names}})
    return result


def plot_results(rows, spec):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    colors = dict(zip(spec['max_buffer'], ['#0072B2', '#E69F00', '#009E73', '#CC79A7']))
    ratios = [('speedup_current_vs_fullsort', 'Full-sort sparse / support-bin sparse'),
              ('speedup_current_vs_fastest_dense', 'Fastest dense / support-bin sparse')]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, constrained_layout=True)
    for row_index, n in enumerate(spec['n']):
        for column, (key, label) in enumerate(ratios):
            ax = axes[row_index, column]
            for width in spec['max_buffer']:
                selected = [r for r in rows if r['n'] == n and r['max_buffer'] == width]
                ax.scatter([r['support_fraction'] for r in selected], [r[key] for r in selected],
                           color=colors[width], s=27, alpha=.8, edgecolors='white', linewidths=.35)
            ax.axhline(1, color='#555555', lw=1, linestyle='--')
            ax.set_xscale('log')
            ax.set_yscale('log', base=2)
            ax.set_title(f'n = {n:,}; {label}', fontsize=10)
            ax.set_ylabel('Runtime ratio (>1 favors support-bin sparse)')
            ax.grid(alpha=.2, which='both')
            if row_index == 1:
                ax.set_xlabel('Realized maximum-support fraction Q/n')
    handles = [Line2D([], [], marker='o', linestyle='', color=colors[w], label=f'L = {w}')
               for w in spec['max_buffer']]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, 1.05),
               ncol=len(handles), frameon=False)
    target = ROOT / 'paper' / 'figures'
    target.mkdir(parents=True, exist_ok=True)
    outputs = []
    for suffix in ['pdf', 'png', 'svg']:
        path = target / f'mechanism.{suffix}'
        fig.savefig(path, dpi=180, bbox_inches='tight')
        outputs.append({'path': str(path.relative_to(ROOT)), 'sha256': sha256(path)})
    plt.close(fig)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--validate-only', action='store_true')
    mode.add_argument('--run', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--cpu-clearance', default='')
    args = parser.parse_args()
    spec = json.loads(PROTOCOL.read_text())
    check_frozen_core(spec)
    numba.set_num_threads(1)
    threadpool_limits(1)
    OUT.mkdir(parents=True, exist_ok=True)
    if args.validate_only:
        validation = validate(spec)
        write_json(OUT / 'validation.json', validation)
        print(json.dumps({key: value for key, value in validation.items() if key != 'rows'}), flush=True)
        return
    if not args.cpu_clearance:
        parser.error('--run requires a recorded --cpu-clearance message')
    receipt_path = OUT / 'run_receipt.json'
    row_path = OUT / 'raw_cases.jsonl'
    sources = source_hashes(spec)
    rows = []
    if receipt_path.exists():
        if not args.resume:
            raise FileExistsError('An existing run must not be silently overwritten; use --resume.')
        receipt = json.loads(receipt_path.read_text())
        if receipt['source_sha256'] != sources or receipt['status'] != 'running':
            raise RuntimeError('Resume requires identical sources and an interrupted running receipt.')
        rows = [json.loads(line) for line in row_path.read_text().splitlines()]
    else:
        if args.resume:
            raise FileNotFoundError('No run receipt to resume.')
        receipt = {'status': 'running', 'started_utc': utc_now(),
                   'cpu_clearance': args.cpu_clearance, 'source_sha256': sources,
                   'protocol_sha256': sha256(PROTOCOL), 'environment': environment()}
        write_json(receipt_path, receipt)
    try:
        y = np.array([0, 1, 0, 0, 1, 0], np.int8)
        scores = np.arange(len(y), dtype=float)
        warmup = {name: timed(function, y, scores, 4)[1] / 1e9 for name, function in METHODS.items()}
        receipt['first_call_seconds_excluded_from_timings'] = warmup
        validation = validate(spec)
        write_json(OUT / 'validation.json', validation)
        receipt['validation'] = {key: value for key, value in validation.items() if key != 'rows'}
        write_json(receipt_path, receipt)
        completed = {row['case_id'] for row in rows}
        if len(completed) != len(rows):
            raise RuntimeError('Duplicate case receipts are not allowed.')
        method_rng = np.random.default_rng(spec['method_order_seed'])
        with row_path.open('a' if rows else 'x') as log:
            for case in grid(spec):
                if case['case_id'] in completed:
                    # Advance the same fixed random-order stream on resume.
                    for _ in range(spec['repetitions']):
                        discarded_order = list(METHODS)
                        method_rng.shuffle(discarded_order)
                    continue
                row = benchmark_case(case, spec, method_rng)
                rows.append(row)
                log.write(json.dumps(row, allow_nan=False) + '\n')
                log.flush()
                print(json.dumps({'completed': len(rows), 'total': spec['feasible_cells'],
                                  'case': row['case_id'], 'Q_fraction': row['support_fraction'],
                                  'sort_ablation_ratio': row['speedup_current_vs_fullsort'],
                                  'fastest_dense_ratio': row['speedup_current_vs_fastest_dense']}), flush=True)
        check_frozen_core(spec)
        if len(rows) != spec['feasible_cells']:
            raise RuntimeError('The complete frozen grid was not evaluated.')
        summary = summarize(rows, spec)
        figures = plot_results(rows, spec)
        result = {'status': 'complete', 'protocol_sha256': sha256(PROTOCOL),
                  'source_sha256': sources, 'summary': summary,
                  'rows': sorted(rows, key=lambda row: (row['n'], row['density_index'],
                                                       row['intervals'], row['max_buffer'])),
                  'figures': figures, 'interpretation': spec['reporting']['interpretation'],
                  'mechanism_boundary': 'Support unique/group construction and the integration '
                  'kernel are held fixed. This isolates the global rank-count step; it does '
                  'not claim that this adapter is the best implementation using a global sort.'}
        write_json(RESULTS, result)
        receipt.update({'status': 'complete', 'completed_utc': utc_now(), 'summary': summary,
                        'raw_cases_sha256': sha256(row_path), 'results_sha256': sha256(RESULTS),
                        'figures': figures})
        write_json(receipt_path, receipt)
        print(json.dumps(summary, indent=2), flush=True)
    except Exception as error:
        receipt.update({'status': 'failed', 'failed_utc': utc_now(),
                        'error_type': type(error).__name__, 'error': str(error),
                        'completed_cases': len(rows)})
        write_json(receipt_path, receipt)
        raise


if __name__ == '__main__':
    main()
