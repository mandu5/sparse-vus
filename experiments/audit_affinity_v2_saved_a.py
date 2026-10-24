"""Independent stdlib-only reconstruction of the frozen v2 saved artifact.

Reads saved metadata and scalar CSVs only. Never imports the producer or
evaluates/fits a metric. Statistics are reconstructed before producer summaries
are opened. Raw observation/score vectors are deliberately absent from the
public archive; this audit checks their bound receipts, not unavailable bytes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import zipfile

COMMIT = 'd8494c25a8c6fe44616a34bdded375dc3993d048'
RUN = '40091476529'
ZIP_SHA = '8d1fd2e2715c8eb4b28c5f1861143766498686aa072a3c72b9d539ca57b6b595'
REL = 'artifacts/pvldb-research-20261024/strengthening'
IDS = ('algorithm', 'hyper_params_id', 'collection', 'dataset', 'repetition')
METRICS = ('ROC_AUC', 'PR_AUC', 'RANGE_PR_AUC')
METHODS = ('raster', 'interval', 'bucket')
CONTRACTS = ('native_default50', 'all_observed')
THREADS = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
           'NUMBA_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def bound(path, expected):
    require(sha(path) == expected, 'hash differs: ' + str(path))


def block_statistics(records):
    """Use multinomial count configurations, not the producer's ordered loop."""
    output = {}
    for contract in CONTRACTS:
        for control in ('raster', 'interval'):
            means, paired, workflow_seconds = [], [], []
            for block in range(5):
                data = {(r['round'], r['method']): r['seconds'] for r in records
                        if r['contract'] == contract and r['block'] == block}
                require(len(data) == 18, 'block/contract has missing or duplicate methods')
                logs = [math.log(data[i, control]) - math.log(data[i, 'bucket'])
                        for i in range(6)]
                means.append(math.fsum(logs) / 6)
                paired.append([data[i, control] / data[i, 'bucket'] for i in range(6)])
                workflow_seconds.append({m: math.exp(math.fsum(
                    math.log(data[i, m]) for i in range(6)) / 6)
                    for m in (control, 'bucket')})
            samples, configurations = [], 0
            for bag in itertools.combinations_with_replacement(range(5), 5):
                configurations += 1
                frequency = Counter(bag)
                counts = [frequency[i] for i in range(5)]
                multiplicity = math.factorial(5) // math.prod(math.factorial(n) for n in counts)
                value = math.fsum(counts[i] * means[i] for i in range(5)) / 5
                samples.extend([value] * multiplicity)
            require(configurations == 126 and len(samples) == 3125, 'bootstrap population differs')
            samples.sort()

            def quantile(probability):
                index = probability * (len(samples) - 1)
                low = int(index)
                fraction = index - low
                return math.exp((1 - fraction) * samples[low]
                                + fraction * samples[min(low + 1, len(samples) - 1)])

            output[contract + '/' + control + '_over_bucket'] = {
                'block_ratios': [math.exp(x) for x in means],
                'geometric_ratio': math.exp(math.fsum(means) / 5),
                'block_range': [math.exp(min(means)), math.exp(max(means))],
                'paired_order_ratios_by_block': paired,
                'control_and_bucket_geometric_seconds_by_block': workflow_seconds,
                'descriptive_block_bootstrap95_bonferroni4': [quantile(.00625), quantile(.99375)],
                'multinomial_configurations': configurations,
                'exact_empirical_samples': len(samples), 'resampling_units': 5,
            }
    return output


def audit(archive, zip_path, repo):
    bound(zip_path, ZIP_SHA)
    with zipfile.ZipFile(zip_path) as zipped:
        members = [i.filename for i in zipped.infolist() if not i.is_dir()]
        require(len(members) == len(set(members)) == 697, 'ZIP population differs')
        for name in members:
            require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'unsafe member')
            require((archive / name).read_bytes() == zipped.read(name), 'extraction differs: ' + name)
    session = archive / 'affinity-blocks-linux-v2'
    protocol_path = archive / 'affinity-blocks-protocol-v2.json'
    protocol = read(protocol_path)
    protocol_sha = sha(protocol_path)
    plan, payload = protocol['study'], protocol['timeeval_consumer']
    require(plan['schema'] == 'timeeval-affinity-five-blocks-v2-new-realization', 'study differs')
    require(plan['seed'] == 2026102405 and plan['planned_trials'] == 180, 'design differs')
    require([b['block'] for b in plan['blocks']] == list(range(5)), 'block coverage differs')
    require(plan['failed_predecessor']['measured_blocks'] == 0, 'v1 relabeled')
    require(plan == read(archive / 'affinity-design-v2.json'), 'saved design differs')
    require(read(session / 'bound-protocol.json') == protocol, 'bound protocol differs')

    records = []
    for block in plan['blocks']:
        number = block['block']
        trials = lines(session / 'blocks' / f'{number:02d}' / 'trials.jsonl')
        require(len(trials) == len(block['trials']) == 36, 'trial population differs')
        require([t['trial'] for t in trials] == list(range(36)), 'trial identity/order differs')
        require(block['warmup'] == [{'contract': c, 'method': m} for c in CONTRACTS for m in METHODS],
                'warm-up schedule differs')
        for contract in CONTRACTS:
            orders = [tuple(t['method'] for t in block['trials']
                            if t['contract'] == contract and t['round'] == repeat)
                      for repeat in range(6)]
            require(set(orders) == set(itertools.permutations(METHODS)), 'permutation balance differs')
        for trial, planned in zip(trials, block['trials']):
            require(trial['block'] == number and all(trial[k] == v for k, v in planned.items()),
                    'trial does not match frozen plan')
            require(trial['status'] == 'COMPLETE', 'noncomplete observation retained; no complete audit')
            require(type(trial['seconds']) in (float, int) and math.isfinite(trial['seconds'])
                    and trial['seconds'] > 0, 'invalid duration')
        records.extend(trials)
    # No producer summary has been opened at this point.
    reconstructed = block_statistics(records)

    def git_bytes(name):
        return subprocess.check_output(['git', '-C', str(repo), 'show', COMMIT + ':' + name])

    def git_json(name):
        return json.loads(git_bytes(name))

    start = read(archive / 'affinity-reproduction-start.json')
    require(start['source_commit'] == COMMIT, 'execution source commit differs')
    ci = start['ci_environment']
    require(ci['GITHUB_SHA'] == COMMIT and ci['GITHUB_RUN_ID'] == RUN
            and ci['GITHUB_RUN_ATTEMPT'] == '1'
            and ci['GITHUB_REF'] == 'refs/tags/strength/affinity-blocks-linux-v2', 'CI identity differs')
    for name, expected in start['committed_source_sha256'].items():
        require(hashlib.sha256(git_bytes(name)).hexdigest() == expected, 'committed source differs: ' + name)
    execution_root = Path(payload['workload_directory'].split('/.cache/', 1)[0])
    for name, expected in protocol['file_bindings'].items():
        relative = str(Path(name).relative_to(execution_root))
        require(hashlib.sha256(git_bytes(relative)).hexdigest() == expected, 'protocol source differs: ' + relative)
    for name, expected in payload['project_sha256'].items():
        require(hashlib.sha256(git_bytes(name)).hexdigest() == expected, 'native project source differs: ' + name)
    identity_path = archive / Path(protocol['identity_receipt']['path']).name
    bound(identity_path, protocol['identity_receipt']['sha256'])
    for receipt in payload['workload_receipts'].values():
        bound(archive / Path(receipt['path']).name, receipt['sha256'])
    prepared = read(archive / 'affinity-prepared.json')
    require(prepared['source_commit'] == COMMIT and prepared['protocol_sha256'] == protocol_sha,
            'prepared receipt differs')
    for field, name in [('generation_sha256', 'workload-generation.json'),
                        ('native_input_audit_sha256', 'native-input-audit.json'),
                        ('design_sha256', 'affinity-design-v2.json')]:
        bound(archive / name, prepared[field])

    generation = read(archive / 'workload-generation.json')
    input_audit = read(archive / 'native-input-audit.json')
    raw_protocol = read(archive / 'workload-protocol.json')
    bound(archive / 'workload-protocol.json', generation['protocol_sha256'])
    bound(archive / 'workload-generation.json', input_audit['generation_sha256'])
    require(input_audit['protocol_sha256'] == generation['protocol_sha256'], 'input protocol differs')
    require(generation['status'] == 'ALL_SELECTED_PROFILES_GENERATED'
            and (generation['selected_cases'], generation['selected_profiles'], generation['successful_profiles'])
            == (26, 52, 52), 'generation incomplete')
    require(generation['metric_evaluation_performed'] is False
            and input_audit['metric_evaluation_performed'] is False
            and input_audit['candidate_code_imported'] is False, 'preparation scope differs')
    require(input_audit['status'] == 'NATIVE_INPUTS_VERIFIED_WITHOUT_METRIC_EVALUATION'
            and input_audit['datasets_verified'] == 26 and input_audit['profiles_verified'] == 52,
            'native audit incomplete')
    require(sum(c['n'] for c in generation['cases']) == input_audit['total_rows'] == 386447,
            'input row population differs')
    observed_native = {k.split('/.cache/strengthening-workload/', 1)[1]: v
                       for k, v in input_audit['input_sha256'].items()
                       if '/.cache/strengthening-workload/' in k
                       and (k.endswith('.csv') or k.endswith('/anomaly_scores.ts'))}
    require(observed_native == payload['input_sha256'] and len(observed_native) == 80,
            'native input receipts differ')
    profiles = {(p['case_id'], p['model']): p for p in generation['profiles']}
    require(len(profiles) == 52 and len(payload['row_ids']) == 52 and len(payload['query_plan']) == 52,
            'profile population differs')
    query_totals = Counter()
    for row, query in zip(payload['row_ids'], payload['query_plan']):
        require([query[k] for k in IDS] == row, 'query row identity differs')
        profile = profiles[row[3], row[0]]
        require(profile['status'] == 'Status.OK' and profile['metric_evaluation_performed'] is False,
                'profile preparation status differs')
        require(profile['shape'] == [query['n']] and profile['distinct_values'] == query['distinct_scores'],
                'query cardinality differs from profile')
        score = 'results/' + '/'.join(row) + '/anomaly_scores.ts'
        require(observed_native[score] == profile['native_score_sha256'], 'score receipt differs')
        count = query['distinct_scores'] - 1
        stride = count // 49 if count > 50 else 1
        default = ((count - 1) // stride + 1 + int((count - 1) % stride != 0)) if count else 0
        require(query['constant_score_shortcut'] == (count == 0), 'constant-score shortcut differs')
        for contract, expected in [('native_default50', default), ('all_observed', count)]:
            q = query['contracts'][contract]
            require(q['emitted_queries'] == expected, 'realized query count differs')
            require(len(q['thresholds_binary64_le_sha256']) == 64, 'malformed threshold hash')
            if not expected:
                require(q['thresholds_binary64_le_sha256'] == hashlib.sha256(b'').hexdigest(),
                        'empty query hash differs')
            query_totals[contract] += expected

    relations = []
    expected_profile_diffs, expected_native_diffs, expected_query_diffs = [], [], []
    for number, (name, consumer_file) in enumerate([
            ('linux-original-replay', 'timeeval-global.json'),
            ('linux-interval-replay', 'timeeval-control-global.json')]):
        prior = git_json(REL + '/' + name + '/workload-generation.json')
        previous = git_json(REL + '/' + name + '/' + consumer_file)['timeeval_consumer']
        prior_raw = git_json(REL + '/' + name + '/workload-protocol.json')
        require(generation['selection_sha256'] == prior['selection_sha256']
                and generation['models'] == prior['models'], 'prior selection/model differs')
        for key in ('datasets_sha256', 'results_sha256', 'immutable_template'):
            require(generation['native_layout'][key] == prior['native_layout'][key], 'native layout differs')
        raw_fields = ('id', 'family', 'n', 'positive', 'raw_sha256', 'observation_hashes',
                      'label_hash', 'archive_member', 'native_test_sha256')
        require([{k: p[k] for k in raw_fields} for p in raw_protocol['cases']]
                == [{k: p[k] for k in raw_fields} for p in prior_raw['cases']], 'prior raw/typed identity differs')
        require(raw_protocol['raw_archive']['sha256'] == prior_raw['raw_archive']['sha256'], 'raw archive differs')
        old = {(p['case_id'], p['model']): p for p in prior['profiles']}
        require(profiles.keys() == old.keys(), 'prior profile coverage differs')
        differences = []
        for key, current in profiles.items():
            for field in ('score_array_sha256', 'native_score_sha256'):
                if current[field] != old[key][field]:
                    item = {'reference': number, 'identity': list(key), 'field': field,
                            'actual': current[field], 'expected': old[key][field]}
                    expected_profile_diffs.append(item)
                    differences.append(item)
        require(observed_native.keys() == previous['input_sha256'].keys(), 'prior input file set differs')
        native_diffs = []
        for path, value in observed_native.items():
            if value != previous['input_sha256'][path]:
                require(path.endswith('/anomaly_scores.ts'), 'prior non-score native input differs')
                item = {'reference': number, 'path': path, 'actual': value,
                        'expected': previous['input_sha256'][path]}
                expected_native_diffs.append(item)
                native_diffs.append(item)
        if payload['query_plan'] != previous['query_plan']:
            expected_query_diffs.append({'reference': number, 'actual': payload['query_plan'],
                                         'expected': previous['query_plan']})
        relations.append({'reference': name, 'profile_hash_differences': differences,
                          'native_score_file_differences': native_diffs,
                          'full_native_input_map_identical': observed_native == previous['input_sha256'],
                          'full_realized_query_plan_identical': payload['query_plan'] == previous['query_plan']})
        if number == 1:
            for key in ('source_revision', 'source_sha256', 'project_sha256', 'prts_sha256',
                        'dependencies', 'python_version', 'row_ids', 'records', 'design'):
                require(payload[key] == previous[key], 'pinned native environment/contract differs: ' + key)
    identity = read(identity_path)
    require(identity['hard_inputs_match'] is True and not identity['hard_input_differences'], 'hard gate failed')
    for key, expected in [('mismatches', expected_profile_diffs),
                          ('native_score_file_differences', expected_native_diffs),
                          ('query_plan_differences', expected_query_diffs)]:
        require(sorted(identity[key], key=str) == sorted(expected, key=str), 'reference diagnostics differ: ' + key)

    core = protocol['chosen_core']
    host = protocol['supervisor_preflight']
    require(core == min(host['permitted_affinity']), 'CPU choice differs')
    supervisor = read(session / 'supervisor-start.json')
    require(supervisor['protocol_sha256'] == protocol_sha, 'supervisor protocol differs')
    host_keys = ('hostname', 'boot_id', 'cpu_models')
    for key in host_keys:
        require(supervisor['native_cpu'][key] == host[key], 'supervisor host differs')
    processes = read(session / 'session-processes.json')
    require(len(processes) == 5, 'process count differs')
    process_ids, thread_snapshots, csv_files, outputs = [], [], [], []
    trace_csv_error = 0.0

    def thread_snapshot(value, pid):
        affinities = value['affinities_by_tid']
        require(str(pid) in affinities and all(v == [core] for v in affinities.values()), 'thread affinity differs')
        require(all(p['num_threads'] == 1 for p in value['numerical_pools']), 'thread pool size differs')
        thread_snapshots.append(len(affinities))

    for block in plan['blocks']:
        number = block['block']
        directory = session / 'blocks' / f'{number:02d}'
        proc = read(directory / 'process-receipt.json')
        require(proc == processes[number] and proc['block'] == number, 'process receipt differs')
        require(proc['returncode'] == 0 and proc['launch_error'] is None and not proc['trace_parse_issues'],
                'failed/invalid process')
        bound(directory / 'trials.jsonl', proc['raw_trials_sha256'])
        bound(directory / 'block-complete.json', proc['block_complete_sha256'])
        command = proc['command']
        require(command[command.index('--block') + 1] == str(number)
                and command[command.index('--protocol-sha256') + 1] == protocol_sha,
                'child command identity differs')
        initial = read(directory / 'child-initial.json')
        begin = read(directory / 'block-start.json')
        end = read(directory / 'block-complete.json')
        cpu = initial['native_cpu_before_affinity']
        pid = cpu['pid']
        require(pid == proc['pid'] and cpu['ppid'] == supervisor['native_cpu']['pid'], 'process identity differs')
        process_ids.append({'pid': pid, 'start_ticks': cpu['process_start_ticks']})
        require(cpu['permitted_affinity'] == host['permitted_affinity'], 'initial allowed CPU set differs')
        for key in host_keys:
            require(cpu[key] == host[key], 'child host differs')
        require(protocol['utc'] <= initial['utc'] <= begin['utc'] <= proc['completed_utc'], 'block chronology differs')
        require(proc['started_utc'] <= initial['utc'], 'child predates launch')
        for receipt in (initial, begin, end):
            require(receipt['protocol_sha256'] == protocol_sha and receipt['block'] == number,
                    'block/protocol identity differs')
        require(all(initial['thread_environment_before_import'][k] == '1' for k in THREADS)
                and all(begin['thread_environment'][k] == '1' for k in THREADS), 'thread environment differs')
        require(begin['dependencies'] == payload['dependencies'], 'block dependencies differ')
        require(begin['fixed_warmup_completed'] is True and begin['warmup_workflows'] == 6
                and begin['input_bindings_verified_before_timing'] is True
                and end['input_bindings_verified_after_block'] is True, 'block gates incomplete')
        require(end['status'] == 'COMPLETE' and end['recorded_trials'] == 36, 'block not complete')
        for receipt in (begin, end):
            require(receipt['native_cpu']['pid'] == pid and receipt['native_cpu']['permitted_affinity'] == [core],
                    'pinned child identity differs')
            thread_snapshot(receipt['thread_contract'], pid)
        for name, expected in end['evidence_sha256'].items():
            bound(directory / name, expected)
        bound(directory / 'trials.jsonl', end['trials_sha256'])
        bound(directory / 'metrics.jsonl', end['metrics_sha256'])
        measured = [r for r in records if r['block'] == number]
        for trial in measured:
            thread_snapshot(trial['thread_contract_before_timing'], pid)
        scalar_rows = lines(directory / 'metrics.jsonl')
        require(len(scalar_rows) == 36 and [r['trial'] for r in scalar_rows] == list(range(36)), 'metric trace differs')
        for item, trial in zip(scalar_rows, measured):
            require(all(item[k] == trial[k] for k in ('block', 'trial', 'directory', *block['trials'][0].keys())),
                    'metric/trial identity differs')
            require(item['public_reference_available'] is False, 'public parity scope differs')
        warmups = begin['warmup_results']
        require(len(warmups) == 6, 'warm-up output count differs')
        for item, expected in zip(warmups, block['warmup']):
            require(all(item[k] == v for k, v in expected.items()), 'warm-up identity differs')
        for item in warmups + scalar_rows:
            relative = Path(item['directory']) / 'results/results.csv'
            require(not relative.is_absolute() and '..' not in relative.parts, 'output path escapes block')
            path = directory / relative
            bound(path, item['results_sha256'])
            with path.open(newline='') as handle:
                frame = list(csv.DictReader(handle))
            require([[row[k] for k in IDS] for row in frame] == payload['row_ids'], 'CSV identity/order differs')
            values = [float(row[k]) for row in frame for k in METRICS]
            require(len(values) == 156 and all(map(math.isfinite, values)), 'invalid scalar population')
            if 'rows' in item:
                require([[str(row[k]) for k in IDS] for row in item['rows']] == payload['row_ids'],
                        'metric trace row identity differs')
                trace_values = [float(row[k]) for row in item['rows'] for k in METRICS]
                trace_csv_error = max(trace_csv_error, max(abs(x - y) for x, y in zip(values, trace_values)))
            entry = {'block': number, 'contract': item['contract'], 'method': item['method'],
                     'path': str(path.relative_to(archive)), 'sha256': sha(path), 'rows': len(frame)}
            csv_files.append(entry)
            outputs.append({**entry, 'values': values})
    require(len({p['pid'] for p in process_ids}) == len({p['start_ticks'] for p in process_ids}) == 5,
            'child process identities are not distinct')
    require(len(thread_snapshots) == 190, 'thread receipt coverage differs')
    require(len(csv_files) == len({x['path'] for x in csv_files}) == 210, 'CSV output population differs')
    require({archive / x['path'] for x in csv_files} == set(session.rglob('results.csv')), 'unreferenced CSV output')
    require(trace_csv_error <= 1e-10, 'metric trace/CSV scalar disagreement')
    parity_counts, parity_max = Counter(), defaultdict(float)
    for first, second in itertools.combinations(outputs, 2):
        if first['contract'] != second['contract']:
            continue
        kind = 'within_block' if first['block'] == second['block'] else 'cross_block'
        error = max(abs(x - y) for x, y in zip(first['values'], second['values']))
        parity_counts[kind] += 1
        parity_max[kind] = max(parity_max[kind], error)
        require(error <= 1e-10, 'scalar parity failure')
    require(parity_counts == {'within_block': 2100, 'cross_block': 8820}, 'parity pair coverage differs')

    complete = read(session / 'complete.json')
    require(complete['status'] == 'COMPLETE' and complete['protocol_sha256'] == protocol_sha
            and complete['planned_blocks'] == complete['attempted_blocks'] == 5
            and complete['planned_trials'] == complete['observed_trials'] == 180, 'completion population differs')
    for field, filename in [('process_receipts_sha256', 'session-processes.json'),
                            ('block_eligibility_sha256', 'block-eligibility.json'),
                            ('cross_block_output_parity_sha256', 'cross-block-output-parity.json')]:
        bound(session / filename, complete[field])
    for name, expected in complete['summary_receipts_sha256'].items():
        bound(session / name, expected)
    for block, files in complete['blocks'].items():
        for name, expected in files.items():
            bound(session / 'blocks' / f'{int(block):02d}' / name, expected)
    eligibility = read(session / 'block-eligibility.json')
    require(set(eligibility) == {str(i) for i in range(5)}
            and all(r['eligible'] is True and not r['reasons'] for r in eligibility.values()), 'eligibility differs')
    require(not list(archive.rglob('*failure*.json')), 'failure receipt present')
    reproduction = read(archive / 'affinity-reproduction-complete.json')
    require(reproduction['status'] == 'COMPLETE' and reproduction['protocol_sha256'] == protocol_sha,
            'reproduction completion differs')
    bound(session / 'complete.json', reproduction['sessions_complete_sha256'])

    # Producer statistics are consulted only after independent reconstruction.
    producer = read(session / 'summary.json')
    require(producer['status_counts'] == {'COMPLETE': 180}, 'producer status counts differ')
    require(set(producer['comparisons']) == set(reconstructed), 'producer contrast coverage differs')
    summary_errors = []
    for name, actual in reconstructed.items():
        expected = producer['comparisons'][name]
        require(expected['complete_blocks'] == 5 and expected['within_block_pairs'] == [6] * 5
                and expected['resampling_units'] == 5 and expected['exact_bootstrap_sequences'] == 3125,
                'producer inferential population differs')
        for key in ('block_ratios', 'block_range', 'descriptive_block_bootstrap95_bonferroni4'):
            summary_errors.extend(abs(a - b) for a, b in zip(actual[key], expected[key]))
        summary_errors.append(abs(actual['geometric_ratio'] - expected['geometric_ratio']))
    require(max(summary_errors) < 1e-12, 'producer statistics differ from reconstruction')
    parity = read(session / 'cross-block-output-parity.json')
    require(parity['status'] == 'PASS' and parity['complete_output_coverage'] is True
            and parity['saved_completed_outputs'] == 210 and parity['compared_cross_block_pairs'] == 8820,
            'producer parity population differs')
    return {
        'status': 'PASS_COMPLETE_SAVED_ARTIFACT_RECONSTRUCTION',
        'auditor': 'Independent AI-simulated reviewer A; stdlib-only saved-output reconstruction',
        'audit_utc': datetime.now(timezone.utc).isoformat(),
        'auditor_script_sha256': sha(__file__), 'source_commit': COMMIT, 'workflow_run': RUN,
        'zip_sha256': ZIP_SHA, 'archive': str(archive), 'archive_files_verified': len(members),
        'protocol_sha256': protocol_sha,
        'committed_source_bindings_verified': len(start['committed_source_sha256']),
        'protocol_file_bindings_verified': len(protocol['file_bindings']),
        'native_project_source_bindings_verified': len(payload['project_sha256']),
        'native_cpu': host, 'chosen_logical_cpu': core, 'child_processes': process_ids,
        'thread_affinity_snapshots_verified': len(thread_snapshots),
        'live_threads_per_snapshot_range': [min(thread_snapshots), max(thread_snapshots)],
        'status_counts': dict(Counter(r['status'] for r in records)),
        'warmup_outputs': 30, 'timed_scalar_outputs': 180, 'csv_outputs': len(csv_files),
        'scalar_values_checked': len(csv_files) * 156,
        'scalar_parity_pair_counts': dict(parity_counts), 'maximum_scalar_error': dict(parity_max),
        'maximum_metric_trace_csv_difference': trace_csv_error,
        'realized_query_totals': dict(query_totals), 'prior_score_query_relations': relations,
        'comparisons': reconstructed, 'maximum_producer_statistics_difference': max(summary_errors),
        'independent_statistics_computed_before_producer_summary_read': True,
        'csv_file_bindings': csv_files,
        'metric_execution_performed': False, 'detector_fitting_performed': False,
        'limits': [
            'Raw observations and score vectors are unarchived: their recorded hash/receipt consistency, '
            'profile cardinalities and sampler counts were checked; nonempty threshold-vector hashes '
            'were compared with bound references, not rederived from unavailable vectors.',
            'Five processes share one host, logical CPU, workload and environment; bootstrap intervals '
            'are descriptive and do not guarantee coverage or support host/workload-population inference.',
            'V1 remains failed preparation with zero measured blocks. Actual v2 score/query equality '
            'does not retroactively complete v1 or establish a cause of prior timing differences.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--zip', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.archive.resolve(), args.zip.resolve(), args.repo.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'archive_files_verified', 'csv_outputs',
                     'maximum_scalar_error', 'maximum_producer_statistics_difference')}, indent=2))


if __name__ == '__main__':
    main()
