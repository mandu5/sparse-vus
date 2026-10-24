"""Independent read-only audit of supplemental compiled TimeEval controls.

Imports only the original independent auditor's parsing/hash helpers and NumPy.
It never imports the workflow runner, metric candidates, TimeEval, or prts, and
does not evaluate metrics.  Both auditor files must be bound before timing.
"""
import argparse
import importlib.util
import itertools
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REVISION = '7c3622757b1a3afa9a84cbc97ce132d9e379f715'
IDS = ('algorithm', 'hyper_params_id', 'collection', 'dataset', 'repetition')
METRICS = ('ROC_AUC', 'PR_AUC', 'RANGE_PR_AUC')
METHODS = ('raster', 'interval', 'bucket')
CONTRACTS = ('native_default50', 'all_observed')
PAIRS = (('interval', 'bucket'), ('raster', 'bucket'), ('raster', 'interval'))
REQUIRED_PROJECT_SOURCES = (
    'scripts/run_timeeval_strengthening.py',
    'src/sparse_vus/timeeval_adapter.py',
    'src/sparse_vus/weighted_range.py',
    'src/sparse_vus/range_sweep.py',
    'src/sparse_vus/__init__.py',
    'src/sparse_vus/core.py',
    'scripts/run_timeeval_interval_control.py',
    'src/sparse_vus/weighted_range_control.py',
    'src/sparse_vus/timeeval_interval_adapter.py',
    'experiments/audit_timeeval_strengthening.py',
    'experiments/audit_timeeval_interval_control.py',
)

_SPEC = importlib.util.spec_from_file_location(
    '_native_control_artifact_helpers', ROOT / 'experiments/audit_timeeval_strengthening.py')
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)
require = _HELPERS.require
digest = _HELPERS.digest
json_file = _HELPERS.json_file
records = _HELPERS.records
tree_hashes = _HELPERS.tree_hashes
csv_rows = _HELPERS.csv_rows
identities = _HELPERS.identities
numeric = _HELPERS.numeric
compare = _HELPERS.compare


def audit(run, protocol_path):
    run, protocol_path = Path(run).resolve(), Path(protocol_path).resolve()
    protocol = json_file(protocol_path)
    binding = protocol['timeeval_consumer']
    complete, start = json_file(run / 'complete.json'), json_file(run / 'run-start.json')
    require(str(protocol['status']).startswith('FROZEN'), 'protocol was not frozen')
    require(binding['schema'] == 'timeeval-consumer-study-v1', 'native workflow schema differs')
    require(binding['source_revision'] == REVISION, 'native source revision differs')
    protocol_sha = digest(protocol_path)
    require(complete['global_protocol_sha256'] == start['global_protocol_sha256'] == protocol_sha,
            'global protocol binding differs')
    require(json_file(run / 'bound-protocol.json') == protocol, 'bound protocol content differs')
    require(not (run / 'failure.json').exists(), 'run has a failure receipt')
    require(start['dependencies'] == binding['dependencies'], 'runtime package receipt differs')
    require(start['warmup_completed'] is True, 'warmup completion was not recorded')
    for pool in json_file(run / 'threadpools.json'):
        require(pool['num_threads'] == 1, 'numeric thread count differs')
    design = binding['design']
    require(design['study_kind'] == 'compiled_interval_control', 'supplemental study kind differs')
    require(design['public_reference_evaluated'] is False, 'invented public reference in study design')
    require(design['comparison_pairs'] == [list(pair) for pair in PAIRS], 'compiled comparison pairs differ')
    require(design['orders'] == [list(p) for p in itertools.permutations(METHODS)],
            'orders are not the six balanced permutations')
    require(design['metrics'] == list(METRICS), 'default metric list differs')
    require(design['methods'] == list(METHODS), 'compiled method set differs')
    require(design['workflow_timeout_seconds'] == 600, 'deadline differs')
    require(design['n_jobs'] == design['numerical_threads'] == 1, 'serial execution design differs')
    require(design['atol'] == 1e-10 and design['rtol'] == 0, 'scalar parity contract differs')
    require(design['bootstrap'] == {'samples': 10000, 'seed': 20261024}, 'bootstrap design differs')
    require(set(design['contracts']) == set(CONTRACTS), 'native contract set differs')
    for contract, maximum in [('native_default50', 50), ('all_observed', 'positive_infinity')]:
        require(design['contracts'][contract] == {
            'max_samples': maximum, 'r_alpha': 0, 'p_alpha': 0, 'cardinality': 'one', 'bias': 'flat'},
            'native range configuration differs')
    require(set(binding['project_sha256']) == set(REQUIRED_PROJECT_SOURCES),
            'required runtime/auditor source set is not fully bound')
    for key, name in [('trials_sha256', 'trials.jsonl'), ('metrics_sha256', 'metrics.jsonl'),
                      ('summary_sha256', 'summary.json')]:
        require(digest(run / name) == complete[key], 'result artifact hash differs: ' + name)
    roots = [('source_sha256', Path(binding['source_directory'])),
             ('input_sha256', Path(binding['workload_directory'])),
             ('project_sha256', ROOT), ('prts_sha256', Path(binding['prts_directory']))]
    for key, root in roots:
        for relative, expected in binding[key].items():
            require(digest(root / relative) == expected, key + ' source/input hash differs: ' + relative)
        if key in ('source_sha256', 'prts_sha256'):
            require(tree_hashes(root) == binding[key], key + ' has added or removed files')
        elif key == 'input_sha256':
            actual = {kind + '/' + name: sha for kind in ('datasets', 'results')
                      for name, sha in tree_hashes(root / kind).items()}
            require(actual == binding[key], 'native input tree has added or removed files')
    for name, receipt in binding['workload_receipts'].items():
        require(digest(receipt['path']) == receipt['sha256'], 'receipt hash differs: ' + name)

    trials = records(run / 'trials.jsonl')
    metric_lines = records(run / 'metrics.jsonl')
    metric_records = {r['trial']: r for r in metric_lines}
    require(len(metric_records) == len(metric_lines), 'duplicate metric-record identity')
    template = csv_rows(Path(binding['workload_directory']) / 'results/results.csv')
    require(identities(template) == binding['row_ids'], 'template row identity/order differs')
    families = sorted({row['collection'] for row in template})
    require(len(families) == 3 and len(binding['batches']) == 4, 'three-family and combined batch coverage differs')
    require(binding['batches'][0]['name'] == 'combined' and binding['batches'][0]['families'] == families,
            'primary combined batch differs')
    require([b['families'] for b in binding['batches'][1:]] == [[name] for name in families],
            'individual family batch coverage/order differs')
    batches = {b['name']: b for b in binding['batches']}
    require(len(batches) == 4, 'duplicate native batch name')
    for batch in batches.values():
        require(batch['row_count'] == sum(r['collection'] in batch['families'] for r in template),
                'frozen batch row count differs from template')
    expected = []
    for contract in CONTRACTS:
        for batch in binding['batches']:
            for repeat, order in enumerate(itertools.permutations(METHODS)):
                for position, method in enumerate(order):
                    expected.append(dict(trial=len(expected), contract=contract, batch=batch['name'],
                                         round=repeat, position=position, method=method,
                                         row_count=batch['row_count']))
    require(len(expected) == len(trials) == complete['recorded_trials'] == complete['planned_trials'] == 144,
            'planned 144-record coverage differs')
    censored, values, profile_values, max_error = {}, {}, {}, 0.
    status_counts = {'COMPLETE': 0, 'TIMEOUT': 0, 'notrun_due_to_prespecified_censor': 0}
    for want, actual in zip(expected, trials):
        require(all(actual.get(k) == v for k, v in want.items()), 'trial identity/order differs')
        key = actual['method'], actual['contract'], actual['batch']
        status = actual['status']
        require(status in status_counts, 'unknown trial status')
        status_counts[status] += 1
        if status == 'notrun_due_to_prespecified_censor':
            require(key in censored and actual['first_censored_trial'] == censored[key], 'skip lacks prior matching censor')
            require('seconds' not in actual and 'directory' not in actual and actual['trial'] not in metric_records,
                    'skipped attempt has fabricated outcomes')
            continue
        require(key not in censored, 'attempt rerun after prespecified censor')
        require(math.isfinite(actual['seconds']) and actual['seconds'] > 0, 'invalid elapsed time')
        trial = (run / actual['directory']).resolve()
        require(trial.is_relative_to(run), 'trial directory escaped run')
        require((trial / 'stdout.log').is_file() and (trial / 'stderr.log').is_file(), 'trial logs missing')
        for relative, sha in binding['input_sha256'].items():
            if relative.startswith('results/') and relative != 'results/results.csv':
                require(digest(trial / relative) == sha, 'trial score/input artifact changed')
        if status == 'TIMEOUT':
            require(actual['completion_seconds_lower_bound'] == 600 and actual['seconds'] >= 600,
                    'censor lower bound is unsupported')
            require(actual['trial'] not in metric_records, 'censored workflow has fabricated complete outputs')
            censored[key] = actual['trial']
            continue
        require(actual['trial'] in metric_records, 'completed workflow lacks output audit record')
        metric = metric_records[actual['trial']]
        require(all(metric.get(k) == v for k, v in want.items()), 'metric-record identity differs')
        path = trial / 'results/results.csv'
        require(digest(path) == metric['results_sha256'], 'completed result CSV hash differs')
        rows = csv_rows(path)
        selected = [r for r in template if r['collection'] in batches[actual['batch']]['families']]
        require(len(rows) == len(selected) == actual['row_count'], 'completed row count differs')
        require(identities(rows) == identities(selected) == identities(metric['rows']), 'completed row identities differ')
        require(all(r['status'] == 'Status.OK' for r in rows), 'completed native row status changed')
        output = numeric(rows)
        compare(output, numeric(metric['rows']), tolerance=1e-14)
        require(metric['public_reference_available'] is False, 'invented public reference in compiled trial')
        require(math.isfinite(metric['max_error_against_available_reference']) and
                0 <= metric['max_error_against_available_reference'] <= 1e-10,
                'per-trial parity receipt exceeds declared tolerance')
        group = actual['contract'], actual['batch']
        prior = values.setdefault(group, [])
        reference = prior[0][1] if prior else output
        error = compare(output, reference)
        require(abs(error - metric['max_error_against_available_reference']) <= 1e-14,
                'per-trial parity error receipt differs from scalar outputs')
        max_error = max(max_error, error)
        prior.append((actual['method'], output))
        for row, row_values in zip(rows, output):
            profile = (actual['contract'],) + tuple(str(row[k]) for k in IDS)
            profile_values.setdefault(profile, []).append((actual['method'], row_values))
    require(len(metric_records) == status_counts['COMPLETE'], 'extra or missing metric records')
    require(len(censored) == complete['censored_keys'], 'censor-key count differs')
    require(complete['timed_attempts'] == status_counts['COMPLETE'] + status_counts['TIMEOUT'], 'timed-attempt count differs')
    require(complete['status'] == ('COMPLETE_WITH_CENSORING' if censored else 'COMPLETE'), 'completion status differs')
    summary = json_file(run / 'summary.json')
    expected_groups = {contract + '/' + b['name'] for contract in CONTRACTS for b in binding['batches']}
    require(set(summary['public_parity_available']) == expected_groups and
            all(flag is False for flag in summary['public_parity_available'].values()),
            'invented public reference or incomplete public-absence coverage in summary')
    require(set(summary['comparisons']) == set(CONTRACTS), 'summary contract coverage differs')

    profile_coverage = {}
    for contract in CONTRACTS:
        missing = {method: [] for method in METHODS}
        for row_id in binding['row_ids']:
            outputs = profile_values.get((contract,) + tuple(row_id), [])
            seen = {method for method, _ in outputs}
            for method in METHODS:
                if method not in seen:
                    missing[method].append(row_id)
            if outputs:
                for _, output in outputs:
                    max_error = max(max_error, compare(output, outputs[0][1]))
        profile_coverage[contract] = {
            method: {'available': len(template) - len(missing[method]), 'total': len(template),
                     'complete': not missing[method], 'missing_row_ids': missing[method]}
            for method in METHODS}

    reconstructed = {}
    for contract in CONTRACTS:
        require(set(summary['comparisons'][contract]) == set(batches), 'summary batch coverage differs')
        reconstructed[contract] = {}
        for batch in binding['batches']:
            selected = [r for r in trials if r['contract'] == contract and r['batch'] == batch['name']]
            keyed = {(r['round'], r['method']): r for r in selected}
            reported_batch = summary['comparisons'][contract][batch['name']]
            require(reported_batch['status_counts'] == {s: sum(r['status'] == s for r in selected) for s in status_counts},
                    'batch status counts differ')
            pair_names = {a + '_over_' + b for a, b in PAIRS}
            require(set(reported_batch['comparisons']) == pair_names, 'summary compiled pair set differs')
            reconstructed[contract][batch['name']] = {}
            for a, b in PAIRS:
                ratios, bounds = [], []
                for repeat in range(6):
                    baseline, candidate = keyed[repeat, a], keyed[repeat, b]
                    if baseline['status'] == candidate['status'] == 'COMPLETE':
                        ratios.append(baseline['seconds'] / candidate['seconds'])
                    elif baseline['status'] == 'TIMEOUT' and candidate['status'] == 'COMPLETE':
                        bounds.append({'round': repeat, 'strict_speedup_lower_bound': 600 / candidate['seconds']})
                name = a + '_over_' + b
                reported = reported_batch['comparisons'][name]
                require(reported['completed_paired_rounds'] == len(ratios), 'paired coverage differs')
                require(reported['paired_speedups'] == ratios and reported['censored_bounds'] == bounds,
                        'paired ratios or censor bounds differ')
                result = {'completed_paired_orders': len(ratios), 'censored_bounds': bounds}
                if len(ratios) == 6:
                    logs = np.log(np.asarray(ratios))
                    center = float(np.exp(logs.mean()))
                    indices = np.random.default_rng(20261024).integers(6, size=(10000, 6))
                    interval = np.exp(np.quantile(logs[indices].mean(axis=1), [.025, .975]))
                    require(abs(reported['geometric_speedup'] - center) <= 1e-12 * max(1, center), 'geometric ratio differs')
                    require(np.allclose(reported['approximate_paired_order_ci95'], interval, atol=1e-12, rtol=1e-12),
                            'paired-order bootstrap interval differs')
                    result.update(geometric_speedup=center, approximate_paired_order_ci95=interval.tolist())
                else:
                    require(reported['approximate_paired_order_ci95'] is None and 'geometric_speedup' not in reported,
                            'censored/incomplete pairs have fabricated interval or complete ratio')
                reconstructed[contract][batch['name']][name] = result
    return {'status': 'INDEPENDENT_NATIVE_INTERVAL_CONTROL_AUDIT_PASSED',
            'protocol_sha256': protocol_sha, 'planned_trials': len(expected),
            'status_counts': status_counts, 'max_absolute_scalar_error': max_error,
            'metric_outputs_recomputed': False, 'runner_or_candidate_imported': False,
            'public_reference_evaluated': False,
            'public_parity_available': summary['public_parity_available'],
            'per_profile_compiled_output_coverage': profile_coverage,
            'reconstructed_comparisons': reconstructed,
            'auditor_sha256': digest(__file__), 'complete_sha256': digest(run / 'complete.json')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'output audit receipt already exists')
    result = audit(args.run, args.protocol)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: result[k] for k in ['status', 'planned_trials', 'status_counts', 'max_absolute_scalar_error']}))


if __name__ == '__main__':
    main()
