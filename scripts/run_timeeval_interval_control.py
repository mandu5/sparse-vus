"""Supplemental compiled interval control for the native TimeEval workflow.

The frozen original runner is imported without changing its file.  Its workflow
boundary, input audits, six balanced orders, trial copies, and artifact receipts
are reused.  Only the method suite, comparison pairs, and protocol-bound source
set change.  This study evaluates no public/prts range implementation and cannot
establish public range-output parity; its retained public-reference flags are
false.  Native ROC_AUC and PR_AUC remain unchanged in every method.

Use the original manifest/run CLI with a separate frozen global protocol and
output directory.  The protocol section remains ``timeeval_consumer``; the
explicit ``design.study_kind`` prevents mixing the two studies.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METHODS = ('raster', 'interval', 'bucket')
PAIRS = (('interval', 'bucket'), ('raster', 'bucket'), ('raster', 'interval'))

_SPEC = importlib.util.spec_from_file_location(
    '_frozen_timeeval_interval_control_base', ROOT / 'scripts/run_timeeval_strengthening.py')
BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(BASE)

_original_design = BASE.design
_original_metric_suite = BASE.metric_suite
BASE.METHODS = METHODS
BASE.PROJECT_SOURCES = BASE.PROJECT_SOURCES + (
    'scripts/run_timeeval_interval_control.py',
    'src/sparse_vus/weighted_range_control.py',
    'src/sparse_vus/timeeval_interval_adapter.py',
    'experiments/audit_timeeval_strengthening.py',
    'experiments/audit_timeeval_interval_control.py',
)


def design():
    value = _original_design()
    value.update(
        study_kind='compiled_interval_control',
        comparison_pairs=[list(pair) for pair in PAIRS],
        public_reference_evaluated=False,
        comparison_scope=(
            'Supplemental comparison of three compiled implementations on the same '
            'native default-three-metric recalculation. The interval method rebuilds '
            'predicted runs and traverses ordered interval overlaps with closed-form '
            'positional masses for every query. Raster and bucket are the frozen '
            'compiled controls. The public range method is not executed or '
            'relabeled; native ROC_AUC and PR_AUC remain unchanged.'),
        output_parity_scope=(
            'All completed compiled outputs are compared within the same contract '
            'and batch at absolute tolerance 1e-10. Public-reference flags retained '
            'by the original orchestration are always false. This supplemental '
            'study alone supplies no public-implementation parity evidence.'),
    )
    return value


def metric_suite(native, method, contract):
    if method not in METHODS:
        raise ValueError('unknown compiled control method')
    if method != 'interval':
        return _original_metric_suite(native, method, contract)
    from sparse_vus.timeeval_interval_adapter import adapt_range_metric_interval_control
    metrics = [deepcopy(native._metrics[name]) for name in BASE.METRICS]
    if contract == 'all_observed':
        metrics[-1]._max_samples = float('inf')
    elif contract != 'native_default50':
        raise ValueError('unknown consumer contract')
    metrics[-1] = adapt_range_metric_interval_control(metrics[-1])
    return metrics


def summarize(records, payload):
    """Pair only equal-contract, equal-batch, equal-round completed workflows."""
    import numpy as np
    result = {}
    for contract in BASE.CONTRACTS:
        result[contract] = {}
        for batch in payload['batches']:
            selected = [r for r in records if r['contract'] == contract and r['batch'] == batch['name']]
            keyed = {(r['round'], r['method']): r for r in selected}
            comparisons = {}
            for baseline, candidate in PAIRS:
                ratios, bounds = [], []
                for repeat in range(6):
                    a, b = keyed[repeat, baseline], keyed[repeat, candidate]
                    if a['status'] == b['status'] == 'COMPLETE':
                        ratios.append(a['seconds'] / b['seconds'])
                    elif a['status'] == 'TIMEOUT' and b['status'] == 'COMPLETE':
                        bounds.append({'round': repeat, 'strict_speedup_lower_bound':
                                       a['completion_seconds_lower_bound'] / b['seconds']})
                item = {'completed_paired_rounds': len(ratios), 'paired_speedups': ratios,
                        'censored_bounds': bounds, 'approximate_paired_order_ci95': None}
                if len(ratios) == 6:
                    logs = np.log(ratios)
                    samples = np.random.default_rng(20261024).integers(6, size=(10000, 6))
                    item.update(geometric_speedup=float(np.exp(logs.mean())),
                                approximate_paired_order_ci95=np.exp(np.quantile(
                                    logs[samples].mean(axis=1), [.025, .975])).tolist())
                else:
                    item['interval_unavailable_reason'] = (
                        'six complete paired orders required; censored/not-run '
                        'attempts are not fabricated observations')
                comparisons[baseline + '_over_' + candidate] = item
            result[contract][batch['name']] = {'comparisons': comparisons,
                'status_counts': {status: sum(r['status'] == status for r in selected)
                                  for status in ('COMPLETE', 'TIMEOUT', 'notrun_due_to_prespecified_censor')}}
    return result


BASE.design = design
BASE.metric_suite = metric_suite
BASE.summarize = summarize


if __name__ == '__main__':
    BASE.main()
