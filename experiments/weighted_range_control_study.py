"""Supplemental closed-form interval control; frozen studies stay unchanged.

Reuses the frozen study's acquisition-free timed loop and its independent
saved-curve auditor. 'incremental' denotes bucket for grid100 and sweep for
distinct queries. A raster control is remeasured in every balanced order.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_frozen_weighted_study', ROOT / 'experiments/weighted_range_study.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
np = study.np
SOURCES = (*study.SOURCES, 'experiments/weighted_range_control_study.py',
           'src/sparse_vus/weighted_range_control.py')


def freeze(args):
    inputs = study.read(args.inputs)
    cases = inputs['cases']
    assert len(cases) == 26
    assert {f: sum(c['family'] == f for c in cases) for f in ('WSD', 'Stock', 'MSL')} == {'WSD': 12, 'Stock': 12, 'MSL': 2}
    for c in cases:
        assert study.sha(study.input_path(c)) == c['npz_sha256']
        with np.load(study.input_path(c), allow_pickle=False) as z:
            assert z['scores'].shape == (2, c['n']) and z['labels'].shape == (c['n'],)
            assert np.isfinite(z['scores']).all()
    args.output.mkdir(parents=True, exist_ok=False)
    study.write(args.output / 'protocol.json', {
        'status': 'FROZEN_BEFORE_CLOSED_FORM_CONTROL_TIMINGS',
        'utc': datetime.now(timezone.utc).isoformat(),
        'sources': {s: study.sha(ROOT / s) for s in SOURCES},
        'inputs_path': str(args.inputs.resolve().relative_to(ROOT)),
        'inputs_sha256': study.sha(args.inputs), 'model_order': ['FFT', 'COPOD'], 'cases': cases,
        'biases': ['flat', 'front', 'back', 'middle'], 'cardinalities': ['one', 'reciprocal', 'improved'],
        'alpha': .2, 'precision_weighting': 'unweighted average over all predicted windows',
        'queries': {'grid100': 'np.linspace(min(score),max(score),100), strict score > threshold',
                    'distinct': 'np.unique(score), strict >, all observed thresholds; excludes below-min state'},
        'orders': [list(p) for p in itertools.permutations(['raster', 'interval', 'incremental'])],
        'incremental_mapping': {'grid100': 'bucket', 'distinct': 'sweep'},
        'control': 'Per-query complete score scan and predicted interval discovery, fixed-label count/moment prefixes for precision, ordered true/predicted interval intersections and closed-form positional masses for recall. No cross-threshold metric state. Same compiler and canonical arithmetic target.',
        'timing': 'Serial one thread. Each measurement includes both public detector profiles, validation, interval/prefix construction, queries, mask/component discovery or score sort/query bucket, metric curves and maximum selection. Excludes compilation, training and file IO.',
        'parity_atol': 1e-10, 'winner_atol': 1e-10, 'bootstrap_seed': 20261024, 'bootstrap_resamples': 10000,
        'comparisons': [['grid100', 'interval', 'incremental'], ['distinct', 'interval', 'incremental'],
                        ['grid100', 'raster', 'interval'], ['distinct', 'raster', 'interval']],
        'uncertainty': 'Same fixed-panel paired-order bootstrap as weighted v2: median times per method/semantic/case, equal semantic log weights, six matched order indices shared across methods and semantics, 10000 draws. Bonferroni36 over three collections and12 semantics per comparison; aggregate correction3. Separate recording-reweighting sensitivity is not population coverage. Methods compared only at identical query contracts; hosts never pooled.',
        'hypothesis': 'Determine whether the coupled state retains an advantage after conventional closed-form interval/prefix-per-query optimization. Both wins and losses, all cases and all12 semantic contracts retained.',
        'chronology': 'Supplemental control added after independent reviewer identified that weighted-v2 raster evaluates point weights at each query. Existing weighted-v2 timings/results are preserved. This is a prospective supplemental ablation, not a replacement or a claim of original preregistration.',
        'failure_policy': 'No replacement/exclusion. Identity mismatch, nonfinite curve or discrepancy above1e-10 halts and preserves partial outputs; changed runtime requires a new protocol/version.',
        'data_note': 'Same selected real panel and public detectors as weighted v2. Raw/source identities enforced. No new cohort selection based on measured performance.'})


def evaluate(method, labels, scores, query, bias, card):
    from sparse_vus.weighted_range import weighted_range_metrics
    from sparse_vus.weighted_range_control import weighted_range_interval_control
    curves, values = [], []
    for x in scores:
        thresholds = np.linspace(x.min(), x.max(), 100) if query == 'grid100' else np.unique(x)
        options = dict(alpha=.2, precision_bias=bias, recall_bias=bias, cardinality=card)
        if method == 'interval':
            curve = weighted_range_interval_control(labels, x, thresholds, **options)
        else:
            backend = ('bucket' if query == 'grid100' else 'sweep') if method == 'incremental' else method
            if backend not in ('raster', 'bucket', 'sweep'):
                raise ValueError('unknown control-study method')
            curve = weighted_range_metrics(backend, labels, x, thresholds, **options)
        curves.append(curve)
        values.append(float(np.max(curve[:, 2])))
    return curves, values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['freeze', 'run'])
    parser.add_argument('--inputs', type=Path, default=study.BASE / 'workload-generation.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze(args)
    else:
        study.evaluate = evaluate
        study.run(args)


if __name__ == '__main__':
    main()
