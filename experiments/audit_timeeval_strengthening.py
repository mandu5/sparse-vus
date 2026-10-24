"""Independent read-only audit of a completed native-consumer study.

Does not import the consumer runner, candidate package, TimeEval, or prts.
Only the explicitly new --out receipt is written.
"""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
IDS = ('algorithm', 'hyper_params_id', 'collection', 'dataset', 'repetition')
METRICS = ('ROC_AUC', 'PR_AUC', 'RANGE_PR_AUC')
METHODS = ('public', 'raster', 'bucket')
CONTRACTS = ('native_default50', 'all_observed')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def json_file(path):
    return json.loads(Path(path).read_text())


def records(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def tree_hashes(root):
    excluded = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', 'build', 'dist'}
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not excluded.intersection(p.relative_to(root).parts)
            and not any(part.endswith('.egg-info') for part in p.relative_to(root).parts)
            and p.suffix not in ('.pyc', '.pyo') and p.name != '.DS_Store'}


def csv_rows(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))


def identities(rows):
    return [[str(row[k]) for k in IDS] for row in rows]


def numeric(rows):
    values = np.asarray([[float(row[k]) for k in METRICS] for row in rows])
    require(values.ndim == 2 and values.shape[1] == 3 and np.isfinite(values).all(),
            'three finite native metric outputs required on every completed row')
    return values


def compare(actual, expected, tolerance=1e-10):
    require(actual.shape == expected.shape, 'metric output shape differs')
    error = float(np.max(np.abs(actual - expected)))
    require(error <= tolerance, 'scalar output parity exceeded tolerance: ' + str(error))
    return error


def audit(run, protocol_path):
    protocol = json_file(protocol_path)
    binding = protocol['timeeval_consumer']
    complete, start = json_file(run / 'complete.json'), json_file(run / 'run-start.json')
    require(str(protocol['status']).startswith('FROZEN'), 'protocol was not frozen')
    protocol_sha = digest(protocol_path)
    require(complete['global_protocol_sha256'] == start['global_protocol_sha256'] == protocol_sha,
            'global protocol binding differs')
    require(json_file(run / 'bound-protocol.json') == protocol, 'bound protocol content differs')
    require(not (run / 'failure.json').exists(), 'run has a failure receipt')
    require(start['dependencies'] == binding['dependencies'], 'runtime package receipt differs')
    require(start['warmup_completed'] is True, 'warmup completion was not recorded')
    for pool in json_file(run / 'threadpools.json'):
        require(pool['num_threads'] == 1, 'numeric thread count differs')
    require(binding['design']['orders'] == [list(p) for p in itertools.permutations(METHODS)],
            'orders are not the six balanced permutations')
    require(binding['design']['metrics'] == list(METRICS), 'default metric list differs')
    require(binding['design']['methods'] == list(METHODS), 'method set differs')
    require(binding['design']['workflow_timeout_seconds'] == 600, 'deadline differs')
    require(binding['design']['n_jobs'] == binding['design']['numerical_threads'] == 1, 'serial execution design differs')
    require(binding['design']['atol'] == 1e-10 and binding['design']['rtol'] == 0, 'scalar parity contract differs')
    for contract, maximum in [('native_default50', 50), ('all_observed', 'positive_infinity')]:
        require(binding['design']['contracts'][contract] == {
            'max_samples': maximum, 'r_alpha': 0, 'p_alpha': 0, 'cardinality': 'one', 'bias': 'flat'},
            'native range configuration differs')
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
    metrics_records = records(run / 'metrics.jsonl')
    metric_records = {r['trial']: r for r in metrics_records}
    require(len(metric_records) == len(metrics_records), 'duplicate metric-record identity')
    template = csv_rows(Path(binding['workload_directory']) / 'results/results.csv')
    require(identities(template) == binding['row_ids'], 'template row identity/order differs')
    families = sorted({row['collection'] for row in template})
    require(len(families) == 3 and len(binding['batches']) == 4, 'three-family and combined batch coverage differs')
    require(binding['batches'][0]['name'] == 'combined' and binding['batches'][0]['families'] == families,
            'primary combined batch differs')
    require(sorted(b['families'] for b in binding['batches'][1:]) == [[name] for name in families],
            'individual family batch coverage differs')
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
    batches = {b['name']: b for b in binding['batches']}
    censored, values, public_seen, profile_values, max_error = {}, {}, set(), {}, 0.
    status_counts = {'COMPLETE': 0, 'TIMEOUT': 0, 'notrun_due_to_prespecified_censor': 0}
    for want, actual in zip(expected, trials):
        require(all(actual.get(k) == v for k, v in want.items()), 'trial identity/order differs')
        key = actual['method'], actual['contract'], actual['batch']
        status = actual['status']
        require(status in status_counts, 'unknown trial status')
        status_counts[status] += 1
        if status == 'notrun_due_to_prespecified_censor':
            require(key in censored and actual['first_censored_trial'] == censored[key], 'skip lacks prior matching censor')
            require('seconds' not in actual and actual['trial'] not in metric_records, 'skipped attempt has fabricated outcomes')
            continue
        require(key not in censored, 'attempt rerun after prespecified censor')
        require(math.isfinite(actual['seconds']) and actual['seconds'] > 0, 'invalid elapsed time')
        trial = (run / actual['directory']).resolve()
        require(trial.is_relative_to(run.resolve()), 'trial directory escaped run')
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
        group = actual['contract'], actual['batch']
        if actual['method'] == 'public':
            public_seen.add(group)
        require(metric['public_reference_available'] == (group in public_seen), 'per-trial public reference flag differs')
        require(math.isfinite(metric['max_error_against_available_reference']) and 0 <= metric['max_error_against_available_reference'] <= 1e-10,
                'per-trial parity receipt exceeds declared tolerance')
        values.setdefault(group, []).append((actual['method'], output))
        for row, row_values in zip(rows, output):
            profile = (actual['contract'],) + tuple(str(row[k]) for k in IDS)
            profile_values.setdefault(profile, []).append((actual['method'], row_values))
    require(len(metric_records) == status_counts['COMPLETE'], 'extra or missing metric records')
    require(len(censored) == complete['censored_keys'], 'censor-key count differs')
    require(complete['timed_attempts'] == status_counts['COMPLETE'] + status_counts['TIMEOUT'], 'timed-attempt count differs')
    require(complete['status'] == ('COMPLETE_WITH_CENSORING' if censored else 'COMPLETE'), 'completion status differs')
    summary = json_file(run / 'summary.json')
    for group, outputs in values.items():
        public = [v for m, v in outputs if m == 'public']
        reference = public[0] if public else outputs[0][1]
        for _, v in outputs:
            max_error = max(max_error, compare(v, reference))
        require(summary['public_parity_available']['/'.join(group)] == bool(public), 'public parity availability misstated')
    profile_coverage = {}
    for contract in CONTRACTS:
        missing = []
        for row_id in binding['row_ids']:
            outputs = profile_values.get((contract,) + tuple(row_id), [])
            public = [v for method, v in outputs if method == 'public']
            if not public:
                missing.append(row_id)
                continue
            for _, output in outputs:
                max_error = max(max_error, compare(output, public[0]))
        profile_coverage[contract] = {'available': len(template) - len(missing),
            'total': len(template), 'complete': not missing, 'missing_row_ids': missing,
            'scope': 'Completed public outputs from any native batch at the same contract; this does not recover censored workflow timing or its interval.'}
    reconstructed = {}
    for contract in CONTRACTS:
        reconstructed[contract] = {}
        for batch in binding['batches']:
            group_outputs = values.get((contract, batch['name']), [])
            require(summary['public_parity_available'][contract + '/' + batch['name']] == any(m == 'public' for m, _ in group_outputs),
                    'public parity availability misstated for empty or censored batch')
            selected = [r for r in trials if r['contract'] == contract and r['batch'] == batch['name']]
            keyed = {(r['round'], r['method']): r for r in selected}
            reported_batch = summary['comparisons'][contract][batch['name']]
            require(reported_batch['status_counts'] == {s: sum(r['status'] == s for r in selected) for s in status_counts},
                    'batch status counts differ')
            reconstructed[contract][batch['name']] = {}
            for a, b in [('public', 'bucket'), ('raster', 'bucket'), ('public', 'raster')]:
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
    return {'status': 'INDEPENDENT_NATIVE_CONSUMER_OUTPUT_AUDIT_PASSED',
            'protocol_sha256': protocol_sha, 'planned_trials': len(expected),
            'status_counts': status_counts, 'max_absolute_scalar_error': max_error,
            'metric_outputs_recomputed': False, 'runner_or_candidate_imported': False,
            'public_parity_available': summary['public_parity_available'],
            'per_profile_public_reference_coverage': profile_coverage,
            'reconstructed_comparisons': reconstructed,
            'auditor_sha256': digest(__file__), 'complete_sha256': digest(run / 'complete.json')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'output audit receipt already exists')
    result = audit(args.run.resolve(), args.protocol.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: result[k] for k in ['status', 'planned_trials', 'status_counts', 'max_absolute_scalar_error']}))


if __name__ == '__main__':
    main()
