"""Compiled-control artifact checks; duration fields are fabricated test data.

No detector or real metric workload is evaluated in these tests.  The interval
adapter has its own native-semantic tests in test_timeeval_interval_adapter.py.
"""
import csv
import importlib.util
import itertools
import json
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDITOR = load_module('_interval_control_auditor', 'experiments/audit_timeeval_interval_control.py')
WRAPPER = load_module('_interval_control_runner', 'scripts/run_timeeval_interval_control.py')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def write_lines(path, rows):
    path.write_text(''.join(json.dumps(row, allow_nan=False) + '\n' for row in rows))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def update_hash(run, field, filename):
    complete = AUDITOR.json_file(run / 'complete.json')
    complete[field] = AUDITOR.digest(run / filename)
    write_json(run / 'complete.json', complete)


def fixture(tmp_path, censor=False):
    """Six tiny profile identities and all 144 planned, fabricated records."""
    workload, source, prts = (tmp_path / name for name in ('workload', 'source', 'prts'))
    source.mkdir()
    prts.mkdir()
    (source / 'source.txt').write_text('source identity fixture\n')
    (prts / 'source.txt').write_text('dependency identity fixture\n')
    rows = []
    for family in ('A', 'B', 'C'):
        for model in ('FFT', 'COPOD'):
            row = dict(algorithm=model, hyper_params_id='fixture', collection=family,
                       dataset=family + '-tiny', repetition='1', status='Status.OK')
            rows.append(row)
            path = workload / 'results' / model / 'fixture' / family / row['dataset'] / '1' / 'anomaly_scores.ts'
            path.parent.mkdir(parents=True)
            path.write_text('0\n1\n0\n1\n')
    write_csv(workload / 'results/results.csv', rows)
    (workload / 'datasets').mkdir()
    (workload / 'datasets/datasets.csv').write_text('collection_name,dataset_name,test_path\n')
    batches = [{'name': 'combined', 'families': ['A', 'B', 'C'], 'row_count': 6}]
    batches += [{'name': name, 'families': [name], 'row_count': 2} for name in ('A', 'B', 'C')]
    binding = {
        'schema': 'timeeval-consumer-study-v1',
        'source_revision': AUDITOR.REVISION,
        'dependencies': {'fixture': 'not a runtime environment'},
        'source_directory': str(source), 'prts_directory': str(prts),
        'workload_directory': str(workload), 'source_sha256': AUDITOR.tree_hashes(source),
        'prts_sha256': AUDITOR.tree_hashes(prts),
        'project_sha256': {name: AUDITOR.digest(ROOT / name) for name in AUDITOR.REQUIRED_PROJECT_SOURCES},
        'input_sha256': {kind + '/' + name: sha for kind in ('datasets', 'results')
                         for name, sha in AUDITOR.tree_hashes(workload / kind).items()},
        'workload_receipts': {}, 'row_ids': AUDITOR.identities(rows), 'batches': batches,
        'design': WRAPPER.design(),
    }
    protocol = tmp_path / 'protocol.json'
    write_json(protocol, {'status': 'FROZEN_FABRICATED_TEST_FIXTURE', 'timeeval_consumer': binding})
    run = tmp_path / 'run'
    run.mkdir()
    write_json(run / 'bound-protocol.json', AUDITOR.json_file(protocol))
    write_json(run / 'run-start.json', {'global_protocol_sha256': AUDITOR.digest(protocol),
               'dependencies': binding['dependencies'], 'warmup_completed': True})
    write_json(run / 'threadpools.json', [{'num_threads': 1}])
    trials, metrics = [], []
    durations = {'raster': 12., 'interval': 6., 'bucket': 3.}
    first_censored = None
    for contract in AUDITOR.CONTRACTS:
        for batch in batches:
            selected = [row for row in rows if row['collection'] in batch['families']]
            for repeat, order in enumerate(itertools.permutations(AUDITOR.METHODS)):
                for position, method in enumerate(order):
                    identity = dict(trial=len(trials), contract=contract, batch=batch['name'],
                                    round=repeat, position=position, method=method, row_count=len(selected))
                    censor_key = censor and contract == 'native_default50' and batch['name'] == 'combined' and method == 'interval'
                    if censor_key and repeat:
                        trials.append({**identity, 'status': 'notrun_due_to_prespecified_censor',
                                       'first_censored_trial': first_censored})
                        continue
                    trial = run / 'trials' / str(identity['trial'])
                    trial.mkdir(parents=True)
                    (trial / 'stdout.log').write_text('')
                    (trial / 'stderr.log').write_text('')
                    shutil.copytree(workload / 'results', trial / 'results')
                    if censor_key:
                        first_censored = identity['trial']
                        trials.append({**identity, 'status': 'TIMEOUT', 'seconds': 600.01,
                                       'completion_seconds_lower_bound': 600,
                                       'directory': str(trial.relative_to(run))})
                        continue
                    output = [{**row, 'ROC_AUC': .3, 'PR_AUC': .4, 'RANGE_PR_AUC': .5} for row in selected]
                    write_csv(trial / 'results/results.csv', output)
                    trials.append({**identity, 'status': 'COMPLETE', 'seconds': durations[method],
                                   'directory': str(trial.relative_to(run))})
                    metrics.append({**identity, 'results_sha256': AUDITOR.digest(trial / 'results/results.csv'),
                                    'public_reference_available': False,
                                    'max_error_against_available_reference': 0., 'rows': output})
    summary = {'comparisons': {}, 'public_parity_available': {}}
    for contract in AUDITOR.CONTRACTS:
        summary['comparisons'][contract] = {}
        for batch in batches:
            summary['public_parity_available'][contract + '/' + batch['name']] = False
            selected_trials = [r for r in trials if r['contract'] == contract and r['batch'] == batch['name']]
            keyed = {(r['round'], r['method']): r for r in selected_trials}
            comparisons = {}
            for a, b in AUDITOR.PAIRS:
                ratios, bounds = [], []
                for repeat in range(6):
                    baseline, candidate = keyed[repeat, a], keyed[repeat, b]
                    if baseline['status'] == candidate['status'] == 'COMPLETE':
                        ratios.append(durations[a] / durations[b])
                    elif baseline['status'] == 'TIMEOUT' and candidate['status'] == 'COMPLETE':
                        bounds.append({'round': repeat, 'strict_speedup_lower_bound': 600 / durations[b]})
                value = {'completed_paired_rounds': len(ratios), 'paired_speedups': ratios,
                         'censored_bounds': bounds, 'approximate_paired_order_ci95': None}
                if len(ratios) == 6:
                    value.update(geometric_speedup=ratios[0], approximate_paired_order_ci95=[ratios[0]] * 2)
                comparisons[a + '_over_' + b] = value
            summary['comparisons'][contract][batch['name']] = {'comparisons': comparisons,
                'status_counts': {s: sum(r['status'] == s for r in selected_trials)
                                  for s in ('COMPLETE', 'TIMEOUT', 'notrun_due_to_prespecified_censor')}}
    write_lines(run / 'trials.jsonl', trials)
    write_lines(run / 'metrics.jsonl', metrics)
    write_json(run / 'summary.json', summary)
    write_json(run / 'complete.json', {
        'status': 'COMPLETE_WITH_CENSORING' if censor else 'COMPLETE',
        'global_protocol_sha256': AUDITOR.digest(protocol), 'recorded_trials': 144, 'planned_trials': 144,
        'censored_keys': int(censor), 'timed_attempts': 139 if censor else 144,
        'trials_sha256': AUDITOR.digest(run / 'trials.jsonl'),
        'metrics_sha256': AUDITOR.digest(run / 'metrics.jsonl'),
        'summary_sha256': AUDITOR.digest(run / 'summary.json')})
    return run, protocol


def test_wrapper_keeps_original_module_code_and_binds_new_sources():
    assert WRAPPER.BASE.METHODS == AUDITOR.METHODS == ('raster', 'interval', 'bucket')
    assert WRAPPER.BASE.run.__code__.co_filename == str(ROOT / 'scripts/run_timeeval_strengthening.py')
    assert set(WRAPPER.BASE.PROJECT_SOURCES) == set(AUDITOR.REQUIRED_PROJECT_SOURCES)
    assert WRAPPER.design()['study_kind'] == 'compiled_interval_control'
    assert WRAPPER.design()['public_reference_evaluated'] is False
    assert WRAPPER.design()['comparison_pairs'] == [list(pair) for pair in AUDITOR.PAIRS]


@pytest.mark.parametrize('censor', [False, True])
def test_audits_all_compiled_outputs_without_public_claims(tmp_path, censor):
    run, protocol = fixture(tmp_path, censor)
    result = AUDITOR.audit(run, protocol)
    assert result['status'] == 'INDEPENDENT_NATIVE_INTERVAL_CONTROL_AUDIT_PASSED'
    assert result['status_counts']['COMPLETE'] == (138 if censor else 144)
    assert result['public_reference_evaluated'] is False
    assert all(value is False for value in result['public_parity_available'].values())
    assert result['max_absolute_scalar_error'] == 0
    assert result['metric_outputs_recomputed'] is False
    assert result['runner_or_candidate_imported'] is False


@pytest.mark.parametrize('where', ['trial', 'summary'])
def test_rejects_invented_public_reference(tmp_path, where):
    run, protocol = fixture(tmp_path)
    if where == 'trial':
        rows = AUDITOR.records(run / 'metrics.jsonl')
        rows[0]['public_reference_available'] = True
        write_lines(run / 'metrics.jsonl', rows)
        update_hash(run, 'metrics_sha256', 'metrics.jsonl')
    else:
        summary = AUDITOR.json_file(run / 'summary.json')
        summary['public_parity_available']['native_default50/combined'] = True
        write_json(run / 'summary.json', summary)
        update_hash(run, 'summary_sha256', 'summary.json')
    with pytest.raises(ValueError, match='public reference'):
        AUDITOR.audit(run, protocol)


@pytest.mark.parametrize('censor', [False, True])
def test_rejects_incorrect_or_censored_interval_even_if_hashes_match(tmp_path, censor):
    run, protocol = fixture(tmp_path, censor)
    summary = AUDITOR.json_file(run / 'summary.json')
    item = summary['comparisons']['native_default50']['combined']['comparisons']['interval_over_bucket']
    item['geometric_speedup'] = 2.
    item['approximate_paired_order_ci95'] = [4., 4.]
    write_json(run / 'summary.json', summary)
    update_hash(run, 'summary_sha256', 'summary.json')
    with pytest.raises(ValueError, match='fabricated|bootstrap interval'):
        AUDITOR.audit(run, protocol)


def test_rejects_scalar_disagreement_with_consistent_csv_json_hashes(tmp_path):
    run, protocol = fixture(tmp_path)
    metrics = AUDITOR.records(run / 'metrics.jsonl')
    record = next(r for r in metrics if r['method'] == 'interval')
    record['rows'][0]['RANGE_PR_AUC'] += 1e-5
    path = run / 'trials' / str(record['trial']) / 'results/results.csv'
    write_csv(path, record['rows'])
    record['results_sha256'] = AUDITOR.digest(path)
    write_lines(run / 'metrics.jsonl', metrics)
    update_hash(run, 'metrics_sha256', 'metrics.jsonl')
    with pytest.raises(ValueError, match='scalar output parity'):
        AUDITOR.audit(run, protocol)


def test_skip_requires_actual_earlier_censor(tmp_path):
    run, protocol = fixture(tmp_path, True)
    trials = AUDITOR.records(run / 'trials.jsonl')
    next(r for r in trials if r['status'] == 'notrun_due_to_prespecified_censor')['first_censored_trial'] = 999
    write_lines(run / 'trials.jsonl', trials)
    update_hash(run, 'trials_sha256', 'trials.jsonl')
    with pytest.raises(ValueError, match='prior matching censor'):
        AUDITOR.audit(run, protocol)


def test_auditor_itself_must_be_bound_before_timing(tmp_path):
    run, protocol = fixture(tmp_path)
    payload = AUDITOR.json_file(protocol)
    del payload['timeeval_consumer']['project_sha256']['experiments/audit_timeeval_interval_control.py']
    write_json(protocol, payload)
    write_json(run / 'bound-protocol.json', payload)
    for name in ('complete.json', 'run-start.json'):
        receipt = AUDITOR.json_file(run / name)
        receipt['global_protocol_sha256'] = AUDITOR.digest(protocol)
        write_json(run / name, receipt)
    with pytest.raises(ValueError, match='required runtime/auditor source'):
        AUDITOR.audit(run, protocol)


def test_summarizer_uses_within_contract_pairs_and_honors_censor(tmp_path):
    run, protocol = fixture(tmp_path, True)
    records = AUDITOR.records(run / 'trials.jsonl')
    payload = AUDITOR.json_file(protocol)['timeeval_consumer']
    summary = WRAPPER.summarize(records, payload)
    default = summary['native_default50']['combined']['comparisons']
    assert default['interval_over_bucket']['completed_paired_rounds'] == 0
    assert default['interval_over_bucket']['approximate_paired_order_ci95'] is None
    assert 'geometric_speedup' not in default['interval_over_bucket']
    assert default['raster_over_bucket']['geometric_speedup'] == pytest.approx(4.)
    exhaustive = summary['all_observed']['combined']['comparisons']
    assert exhaustive['interval_over_bucket']['geometric_speedup'] == pytest.approx(2.)


def test_wrapper_executes_actual_tiny_native_workflow_without_timing(tmp_path):
    import subprocess
    import sys

    source = ROOT / '.cache/strengthening-timeeval-full'
    if not source.exists():
        pytest.skip('pinned native source cache is optional')
    workload = tmp_path / 'tiny-native'
    data, results = workload / 'datasets', workload / 'results'
    rows, index = [], []
    for family in ('A', 'B', 'C'):
        case = family + '-tiny'
        relative = family + '/' + case + '.csv'
        dataset = data / relative
        dataset.parent.mkdir(parents=True)
        dataset.write_text('timestamp,value,is_anomaly\n' + ''.join(
            f'{i},{i/8},{v}\n' for i, v in enumerate([0, 1, 1, 0, 0, 1, 0, 0])))
        index.append(dict(collection_name=family, dataset_name=case,
                          test_path=relative, train_path=''))
        for model in ('FFT', 'COPOD'):
            score = results / model / 'tiny' / family / case / '1' / 'anomaly_scores.ts'
            score.parent.mkdir(parents=True)
            score.write_text('0\n3\n2\n1\n1\n4\n0\n2\n')
            rows.append(dict(algorithm=model, hyper_params_id='tiny', collection=family,
                             dataset=case, repetition=1, status='Status.OK'))
    write_csv(data / 'datasets.csv', index)
    write_csv(results / 'results.csv', rows)
    before = AUDITOR.tree_hashes(workload)
    out = tmp_path / 'native-validation'
    completed = subprocess.run([
        sys.executable, str(ROOT / 'scripts/run_timeeval_interval_control.py'),
        'validate', '--workload', str(workload), '--source', str(source), '--out', str(out),
    ], text=True, capture_output=True, timeout=60)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt = AUDITOR.json_file(out / 'complete.json')
    assert receipt['status'] == 'TINY_NATIVE_CONSUMER_VALIDATED'
    assert receipt['methods'] == list(AUDITOR.METHODS)
    assert receipt['contracts'] == list(AUDITOR.CONTRACTS)
    assert receipt['timing_performed'] is False
    assert receipt['row_count'] == 6
    assert receipt['max_absolute_error'] <= 1e-10
    assert AUDITOR.tree_hashes(workload) == before
