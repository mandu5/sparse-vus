"""Reconstruct native TimeEval saved-output evidence without local input bytes.

Supports the original public/raster/bucket study and the supplemental
raster/interval/bucket study. Only saved protocols, manifests, receipts, trial
logs and result CSVs are read. Frozen absolute input/source paths are never
followed. This is weaker than the live-input auditors: it does not reacquire
data, repeat fits, evaluate metrics, or verify raw/source/score file bytes.
"""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import median

import numpy as np


REVISION = '7c3622757b1a3afa9a84cbc97ce132d9e379f715'
IDS = ('algorithm', 'hyper_params_id', 'collection', 'dataset', 'repetition')
METRICS = ('ROC_AUC', 'PR_AUC', 'RANGE_PR_AUC')
CONTRACTS = ('native_default50', 'all_observed')
PUBLIC_METHODS = ('public', 'raster', 'bucket')
CONTROL_METHODS = ('raster', 'interval', 'bucket')
STATUSES = ('COMPLETE', 'TIMEOUT', 'notrun_due_to_prespecified_censor')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def invalid_constant(value):
    raise ValueError('nonfinite JSON constant: ' + value)


def json_file(path):
    return json.loads(Path(path).read_text(), parse_constant=invalid_constant)


def records(path):
    return [json.loads(line, parse_constant=invalid_constant)
            for line in Path(path).read_text().splitlines()]


def csv_rows(path):
    with Path(path).open(newline='') as handle:
        return list(csv.DictReader(handle))


def identities(rows):
    return [[str(row[name]) for name in IDS] for row in rows]


def numeric(rows):
    values = np.asarray([[float(row[name]) for name in METRICS] for row in rows])
    require(values.ndim == 2 and values.shape[1] == 3 and np.isfinite(values).all(),
            'three finite native metric outputs required on every completed row')
    return values


def compare(actual, expected, tolerance=1e-10):
    require(actual.shape == expected.shape, 'metric output shape differs')
    error = float(np.max(np.abs(actual - expected)))
    require(error <= tolerance, 'scalar output parity exceeded tolerance: ' + str(error))
    return error


def sha_string(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in '0123456789abcdef' for c in value))


def contained(run, relative):
    require(isinstance(relative, str) and not Path(relative).is_absolute(),
            'trial directory must be relative to the archived run')
    result = (run / relative).resolve()
    require(result.is_relative_to(run), 'trial artifact escaped archived run')
    return result


def declared_query_plan(binding):
    """Check metadata identities/counts, without claiming to inspect scores."""
    plan = binding['query_plan']
    require(identities(plan) == binding['row_ids'], 'query-plan profile coverage/order differs')
    for item in plan:
        n, distinct = item['n'], item['distinct_scores']
        require(type(n) is int and type(distinct) is int and 1 <= distinct <= n,
                'invalid declared score cardinality or length')
        require(item['constant_score_shortcut'] is (distinct == 1), 'constant-score declaration differs')
        require(set(item['contracts']) == set(CONTRACTS), 'query-plan contract coverage differs')
        all_count = distinct - 1
        default_count = all_count
        if all_count > 50:
            stride = all_count // 49
            default_count = (all_count - 1) // stride + 1
            if (default_count - 1) * stride != all_count - 1:
                default_count += 1
        for contract, expected in [('native_default50', default_count), ('all_observed', all_count)]:
            query = item['contracts'][contract]
            require(query['emitted_queries'] == expected, 'declared native sampler query count differs')
            require(sha_string(query['thresholds_binary64_le_sha256']), 'invalid declared threshold hash')
    for batch in binding['batches']:
        selected = [item for item in plan if item['collection'] in batch['families']]
        for contract in CONTRACTS:
            counts = [item['contracts'][contract]['emitted_queries'] for item in selected]
            require(batch['query_counts'][contract] == {
                'total': sum(counts), 'minimum': min(counts), 'maximum': max(counts)},
                'batch declared query counts differ')


def audit(run, protocol_path, manifest_path):
    run = Path(run).resolve()
    protocol_path, manifest_path = Path(protocol_path).resolve(), Path(manifest_path).resolve()
    protocol, manifest = json_file(protocol_path), json_file(manifest_path)
    complete, start = json_file(run / 'complete.json'), json_file(run / 'run-start.json')
    require(str(protocol['status']).startswith('FROZEN'), 'protocol was not frozen')
    protocol_sha = digest(protocol_path)
    require(complete['global_protocol_sha256'] == start['global_protocol_sha256'] == protocol_sha,
            'global protocol binding differs')
    require(json_file(run / 'bound-protocol.json') == protocol, 'bound protocol content differs')
    binding = protocol['timeeval_consumer']
    require(manifest == binding, 'standalone manifest differs from embedded protocol payload')
    manifest_sha = digest(manifest_path)
    if 'manifest_sha256' in protocol:
        require(protocol['manifest_sha256'] == manifest_sha, 'standalone manifest SHA differs')
    require(binding['schema'] == 'timeeval-consumer-study-v1', 'native manifest schema differs')
    require(binding['source_revision'] == REVISION, 'declared native source revision differs')
    require(binding['timing_or_metric_outcomes_consumed'] is False, 'manifest construction declaration differs')
    require(not (run / 'failure.json').exists(), 'run has a failure receipt')
    require(start['dependencies'] == binding['dependencies'], 'recorded runtime dependencies differ')
    require(start['warmup_completed'] is True, 'warmup completion was not recorded')
    for pool in json_file(run / 'threadpools.json'):
        require(pool['num_threads'] == 1, 'recorded numeric thread count differs')
    design = binding['design']
    methods = tuple(design['methods'])
    if methods == PUBLIC_METHODS:
        kind = 'original_public_comparison'
        pairs = (('public', 'bucket'), ('raster', 'bucket'), ('public', 'raster'))
        require(design.get('study_kind') in (None, kind), 'public study kind differs')
    elif methods == CONTROL_METHODS:
        kind = 'compiled_interval_control'
        pairs = (('interval', 'bucket'), ('raster', 'bucket'), ('raster', 'interval'))
        require(design['study_kind'] == kind, 'supplemental study kind differs')
        require(design['public_reference_evaluated'] is False, 'invented public reference in study design')
        require(design['comparison_pairs'] == [list(pair) for pair in pairs], 'compiled comparison pairs differ')
    else:
        raise ValueError('unsupported native study method set/order')
    require(design['orders'] == [list(p) for p in itertools.permutations(methods)],
            'orders are not the six balanced permutations')
    require(design['metrics'] == list(METRICS), 'native default metric list differs')
    require(design['workflow_timeout_seconds'] == 600, 'deadline differs')
    require(design['n_jobs'] == design['numerical_threads'] == 1, 'serial execution design differs')
    require(design['atol'] == 1e-10 and design['rtol'] == 0, 'scalar parity contract differs')
    require(design['bootstrap'] == {'samples': 10000, 'seed': 20261024}, 'bootstrap design differs')
    require(set(design['contracts']) == set(CONTRACTS), 'native contract coverage differs')
    for contract, maximum in [('native_default50', 50), ('all_observed', 'positive_infinity')]:
        require(design['contracts'][contract] == {
            'max_samples': maximum, 'r_alpha': 0, 'p_alpha': 0, 'cardinality': 'one', 'bias': 'flat'},
            'native range configuration differs')
    for field in ('source_sha256', 'input_sha256', 'project_sha256', 'prts_sha256'):
        require(isinstance(binding[field], dict) and bool(binding[field]) and
                all(isinstance(name, str) and sha_string(sha) for name, sha in binding[field].items()),
                'malformed declared source/input hash map: ' + field)
    for field, filename in [('trials_sha256', 'trials.jsonl'), ('metrics_sha256', 'metrics.jsonl'),
                            ('summary_sha256', 'summary.json')]:
        require(digest(run / filename) == complete[field], 'saved result artifact hash differs: ' + filename)
    archived_receipts = {}
    for name, receipt in binding['workload_receipts'].items():
        require(sha_string(receipt['sha256']), 'invalid declared workload-receipt hash')
        # Only sibling archived receipts are eligible. Never follow the original
        # machine's absolute path, even if it happens to exist on this host.
        archived = protocol_path.parent / Path(receipt['path']).name
        if archived.is_file():
            require(digest(archived) == receipt['sha256'], 'archived workload receipt hash differs: ' + name)
            archived_receipts[name] = {'saved_receipt_bytes_verified': True, 'sha256': receipt['sha256']}
        else:
            archived_receipts[name] = {'saved_receipt_bytes_verified': False,
                                      'reason': 'receipt not present beside archived protocol'}

    row_ids = binding['row_ids']
    require(bool(row_ids) and all(isinstance(row, list) and len(row) == len(IDS)
                                and all(isinstance(value, str) for value in row) for row in row_ids),
            'manifest requires nonempty string profile identities')
    require(len({tuple(row) for row in row_ids}) == len(row_ids) == binding['records'],
            'manifest profile count/uniqueness differs')
    families = sorted({row[2] for row in row_ids})
    require(len(families) == 3 and len(binding['batches']) == 4, 'three-family and combined batch coverage differs')
    require(binding['batches'][0]['name'] == 'combined' and binding['batches'][0]['families'] == families,
            'primary combined batch differs')
    require([batch['families'] for batch in binding['batches'][1:]] == [[name] for name in families],
            'individual family batch coverage/order differs')
    batches = {batch['name']: batch for batch in binding['batches']}
    require(len(batches) == 4, 'duplicate native batch name')
    batch_ids = {name: [row for row in row_ids if row[2] in batch['families']]
                 for name, batch in batches.items()}
    for name, batch in batches.items():
        require(len(batch_ids[name]) == batch['row_count'], 'frozen batch profile count differs')
    declared_query_plan(binding)
    expected = []
    for contract in CONTRACTS:
        for batch in binding['batches']:
            for repeat, order in enumerate(itertools.permutations(methods)):
                for position, method in enumerate(order):
                    expected.append(dict(trial=len(expected), contract=contract, batch=batch['name'],
                                         round=repeat, position=position, method=method,
                                         row_count=batch['row_count']))
    trials, metric_lines = records(run / 'trials.jsonl'), records(run / 'metrics.jsonl')
    require(len(expected) == len(trials) == complete['recorded_trials'] == complete['planned_trials'] == 144,
            'planned 144-record coverage differs')
    metric_records = {record['trial']: record for record in metric_lines}
    require(len(metric_records) == len(metric_lines), 'duplicate metric-record identity')
    require([record['trial'] for record in metric_lines] ==
            [record['trial'] for record in trials if record['status'] == 'COMPLETE'],
            'completed metric-record coverage/order differs')
    censored, values, references, profiles = {}, {}, {}, {}
    directories, max_error = set(), 0.
    status_counts = {status: 0 for status in STATUSES}
    for want, actual in zip(expected, trials):
        require(all(actual.get(key) == value for key, value in want.items()), 'trial identity/order differs')
        status = actual['status']
        require(status in status_counts, 'unknown trial status')
        status_counts[status] += 1
        key = actual['method'], actual['contract'], actual['batch']
        if status == 'notrun_due_to_prespecified_censor':
            require(key in censored and actual['first_censored_trial'] == censored[key],
                    'skip lacks prior matching censor')
            require('seconds' not in actual and 'directory' not in actual and actual['trial'] not in metric_records,
                    'skipped attempt has fabricated outcomes')
            continue
        require(key not in censored, 'attempt rerun after prespecified censor')
        require(math.isfinite(actual['seconds']) and actual['seconds'] > 0, 'invalid saved elapsed time')
        trial = contained(run, actual['directory'])
        require(trial not in directories, 'timed attempts require distinct trial directories')
        directories.add(trial)
        require((trial / 'stdout.log').is_file() and (trial / 'stderr.log').is_file(), 'saved trial logs missing')
        result_csv = trial / 'results/results.csv'
        require(result_csv.resolve().is_relative_to(run), 'saved result CSV escaped archived run')
        if status == 'TIMEOUT':
            require(actual['completion_seconds_lower_bound'] == 600 and actual['seconds'] >= 600,
                    'censor lower bound is unsupported')
            require(actual['trial'] not in metric_records, 'censored workflow has fabricated complete outputs')
            require(result_csv.is_file(), 'censored workflow input-template CSV missing')
            # This file is the copied template, not an authenticated completed
            # result: no metric values are extracted from censored workflows.
            require(identities(csv_rows(result_csv)) == batch_ids[actual['batch']],
                    'censored workflow template row identities differ')
            censored[key] = actual['trial']
            continue
        require(actual['trial'] in metric_records, 'completed workflow lacks saved output record')
        metric = metric_records[actual['trial']]
        require(all(metric.get(key) == value for key, value in want.items()), 'metric-record identity differs')
        require(result_csv.is_file(), 'completed result CSV missing')
        require(digest(result_csv) == metric['results_sha256'], 'completed result CSV hash differs')
        rows = csv_rows(result_csv)
        require(len(rows) == actual['row_count'], 'completed row count differs')
        require(identities(rows) == batch_ids[actual['batch']] == identities(metric['rows']),
                'completed row identities differ')
        require(all(row['status'] == 'Status.OK' for row in rows), 'completed native row status changed')
        output = numeric(rows)
        compare(output, numeric(metric['rows']), tolerance=1e-14)
        group = actual['contract'], actual['batch']
        group_outputs = values.setdefault(group, [])
        group_outputs.append((actual['method'], output))
        if actual['method'] == 'public' and group not in references:
            references[group] = output
        require(metric['public_reference_available'] is (group in references),
                'invented or missing public reference in trial')
        reference = references.get(group, group_outputs[0][1])
        error = compare(output, reference)
        if actual['method'] == 'public':
            for _, prior in group_outputs:
                error = max(error, compare(prior, output))
        declared_error = metric['max_error_against_available_reference']
        require(math.isfinite(declared_error) and 0 <= declared_error <= 1e-10 and
                abs(error - declared_error) <= 1e-14, 'per-trial scalar parity error receipt differs')
        max_error = max(max_error, error)
        for row_id, row_values in zip(identities(rows), output):
            profiles.setdefault((actual['contract'],) + tuple(row_id), []).append((actual['method'], row_values))
    require(len(metric_records) == status_counts['COMPLETE'], 'extra or missing metric records')
    require(len(censored) == complete['censored_keys'], 'censor-key count differs')
    require(complete['timed_attempts'] == status_counts['COMPLETE'] + status_counts['TIMEOUT'],
            'timed-attempt count differs')
    require(complete['status'] == ('COMPLETE_WITH_CENSORING' if censored else 'COMPLETE'),
            'completion status differs')
    summary = json_file(run / 'summary.json')
    public_flags = {contract + '/' + name: (contract, name) in references
                    for contract in CONTRACTS for name in batches}
    require(summary['public_parity_available'] == public_flags,
            'invented public reference or incomplete reference coverage in summary')
    require(set(summary['comparisons']) == set(CONTRACTS), 'summary contract coverage differs')
    public_coverage, compiled_coverage = {}, {}
    for contract in CONTRACTS:
        missing_public = []
        missing_compiled = {method: [] for method in methods if method != 'public'}
        for row_id in row_ids:
            outputs = profiles.get((contract,) + tuple(row_id), [])
            public = [value for method, value in outputs if method == 'public']
            if not public:
                missing_public.append(row_id)
            seen = {method for method, _ in outputs}
            for method in missing_compiled:
                if method not in seen:
                    missing_compiled[method].append(row_id)
            if outputs:
                reference = public[0] if public else outputs[0][1]
                for _, output in outputs:
                    max_error = max(max_error, compare(output, reference))
        public_coverage[contract] = {'available': len(row_ids) - len(missing_public),
            'total': len(row_ids), 'complete': not missing_public, 'missing_row_ids': missing_public,
            'scope': 'Saved completed public outputs at the same contract only; no input re-evaluation or recovered censored timing.'}
        compiled_coverage[contract] = {
            method: {'available': len(row_ids) - len(missing), 'total': len(row_ids),
                     'complete': not missing, 'missing_row_ids': missing}
            for method, missing in missing_compiled.items()}

    reconstructed, absolute_times = {}, {}
    for contract in CONTRACTS:
        require(set(summary['comparisons'][contract]) == set(batches), 'summary batch coverage differs')
        reconstructed[contract], absolute_times[contract] = {}, {}
        for name in batches:
            selected = [record for record in trials if record['contract'] == contract and record['batch'] == name]
            keyed = {(record['round'], record['method']): record for record in selected}
            reported_batch = summary['comparisons'][contract][name]
            require(reported_batch['status_counts'] == {
                status: sum(record['status'] == status for record in selected) for status in STATUSES},
                'batch status counts differ')
            require(set(reported_batch['comparisons']) == {a + '_over_' + b for a, b in pairs},
                    'summary comparison pair set differs')
            reconstructed[contract][name], absolute_times[contract][name] = {}, {}
            for method in methods:
                durations = [record['seconds'] for record in selected
                             if record['method'] == method and record['status'] == 'COMPLETE']
                absolute_times[contract][name][method] = {
                    'completed_orders': len(durations), 'median_seconds': median(durations) if durations else None}
            for baseline, candidate in pairs:
                ratios, bounds = [], []
                for repeat in range(6):
                    a, b = keyed[repeat, baseline], keyed[repeat, candidate]
                    if a['status'] == b['status'] == 'COMPLETE':
                        ratios.append(a['seconds'] / b['seconds'])
                    elif a['status'] == 'TIMEOUT' and b['status'] == 'COMPLETE':
                        bounds.append({'round': repeat, 'strict_speedup_lower_bound': 600 / b['seconds']})
                pair_name = baseline + '_over_' + candidate
                reported = reported_batch['comparisons'][pair_name]
                require(reported['completed_paired_rounds'] == len(ratios), 'paired coverage differs')
                require(reported['paired_speedups'] == ratios and reported['censored_bounds'] == bounds,
                        'paired ratios or censor bounds differ')
                result = {'completed_paired_orders': len(ratios), 'paired_speedups': ratios,
                          'censored_bounds': bounds, 'approximate_paired_order_ci95': None}
                if len(ratios) == 6:
                    logs = np.log(np.asarray(ratios))
                    center = float(np.exp(logs.mean()))
                    indices = np.random.default_rng(20261024).integers(6, size=(10000, 6))
                    interval = np.exp(np.quantile(logs[indices].mean(axis=1), [.025, .975]))
                    require(math.isfinite(reported['geometric_speedup']) and
                            abs(reported['geometric_speedup'] - center) <= 1e-12 * max(1, center),
                            'geometric speed ratio differs')
                    recorded_interval = np.asarray(reported['approximate_paired_order_ci95'])
                    require(recorded_interval.shape == (2,) and np.isfinite(recorded_interval).all() and
                            np.allclose(recorded_interval, interval, atol=1e-12, rtol=1e-12),
                            'paired-order bootstrap interval differs')
                    result.update(geometric_speedup=center, approximate_paired_order_ci95=interval.tolist())
                else:
                    require(reported['approximate_paired_order_ci95'] is None and 'geometric_speedup' not in reported,
                            'censored/incomplete pairs have fabricated interval or complete ratio')
                reconstructed[contract][name][pair_name] = result
    return {'status': 'ARCHIVED_NATIVE_OUTPUT_RECONSTRUCTION_PASSED', 'study_kind': kind,
            'local_input_bytes_verified': False, 'local_source_bytes_verified': False,
            'metric_outputs_recomputed': False, 'detector_fitting_repeated': False,
            'runner_or_candidate_imported': False, 'completed_result_csv_bytes_verified': True,
            'verification_scope': 'Saved protocol/manifest/run/record bindings, declared query metadata, complete result CSVs, identities, parity, censors and matched summaries only. No raw data, label, detector-score or source byte verification; censored CSV metric values are never used.',
            'protocol_sha256': protocol_sha, 'manifest_sha256': manifest_sha,
            'standalone_manifest_matches_embedded_payload': True,
            'manifest_sha256_recorded_in_global_protocol': 'manifest_sha256' in protocol,
            'archived_workload_receipts': archived_receipts,
            'planned_trials': len(expected), 'status_counts': status_counts,
            'max_absolute_scalar_error': max_error,
            'public_reference_evaluated': methods == PUBLIC_METHODS,
            'public_parity_available': public_flags,
            'per_profile_public_reference_coverage': public_coverage,
            'per_profile_compiled_output_coverage': compiled_coverage,
            'absolute_workflow_times': absolute_times,
            'reconstructed_comparisons': reconstructed,
            'complete_sha256': digest(run / 'complete.json'), 'auditor_sha256': digest(__file__)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'new archive-audit output path required')
    result = audit(args.run, args.protocol, args.manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({key: result[key] for key in (
        'status', 'study_kind', 'local_input_bytes_verified', 'planned_trials',
        'status_counts', 'max_absolute_scalar_error')}))


if __name__ == '__main__':
    main()
