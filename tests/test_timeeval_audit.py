"""Artifact-audit contract tests using fabricated tiny records, never timings.

No TimeEval package, detector, metric kernel, or real study input is imported.
The constant duration fields below are test fixtures, not measured observations.
"""
import csv
import importlib.util
import itertools
import json
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    '_timeeval_output_auditor', ROOT / 'experiments/audit_timeeval_strengthening.py')
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


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


def fixture(tmp_path, censor):
    """A complete 144-record artifact layout with six tiny fabricated profiles."""
    workload, source, prts = (tmp_path / name for name in ('workload', 'source', 'prts'))
    source.mkdir(); prts.mkdir()
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
        'dependencies': {'fixture': 'not a runtime environment'},
        'source_directory': str(source), 'prts_directory': str(prts),
        'workload_directory': str(workload), 'source_sha256': AUDITOR.tree_hashes(source),
        'prts_sha256': AUDITOR.tree_hashes(prts),
        'project_sha256': {'experiments/audit_timeeval_strengthening.py': AUDITOR.digest(ROOT / 'experiments/audit_timeeval_strengthening.py')},
        'input_sha256': {kind + '/' + name: sha for kind in ('datasets', 'results')
                         for name, sha in AUDITOR.tree_hashes(workload / kind).items()},
        'workload_receipts': {}, 'row_ids': AUDITOR.identities(rows), 'batches': batches,
        'design': {'orders': [list(p) for p in itertools.permutations(AUDITOR.METHODS)],
                   'metrics': list(AUDITOR.METRICS), 'methods': list(AUDITOR.METHODS),
                   'workflow_timeout_seconds': 600, 'n_jobs': 1, 'numerical_threads': 1,
                   'atol': 1e-10, 'rtol': 0,
                   'contracts': {name: {'max_samples': maximum, 'r_alpha': 0, 'p_alpha': 0,
                                        'cardinality': 'one', 'bias': 'flat'}
                                 for name, maximum in [('native_default50', 50), ('all_observed', 'positive_infinity')]}},
    }
    protocol = tmp_path / 'protocol.json'
    write_json(protocol, {'status': 'FROZEN_FABRICATED_TEST_FIXTURE', 'timeeval_consumer': binding})
    run = tmp_path / 'run'; run.mkdir()
    write_json(run / 'bound-protocol.json', AUDITOR.json_file(protocol))
    write_json(run / 'run-start.json', {'global_protocol_sha256': AUDITOR.digest(protocol),
               'dependencies': binding['dependencies'], 'warmup_completed': True})
    write_json(run / 'threadpools.json', [{'num_threads': 1}])
    trials, metrics = [], []
    durations = {'public': 12., 'raster': 6., 'bucket': 3.}
    for contract in AUDITOR.CONTRACTS:
        for batch in batches:
            selected = [row for row in rows if row['collection'] in batch['families']]
            for repeat, order in enumerate(itertools.permutations(AUDITOR.METHODS)):
                for position, method in enumerate(order):
                    identity = dict(trial=len(trials), contract=contract, batch=batch['name'],
                                    round=repeat, position=position, method=method, row_count=len(selected))
                    censored_key = censor and contract == 'native_default50' and batch['name'] == 'combined' and method == 'public'
                    if censored_key and repeat:
                        trials.append({**identity, 'status': 'notrun_due_to_prespecified_censor', 'first_censored_trial': 0})
                        continue
                    trial = run / 'trials' / str(identity['trial'])
                    trial.mkdir(parents=True)
                    (trial / 'stdout.log').write_text('')
                    (trial / 'stderr.log').write_text('')
                    shutil.copytree(workload / 'results', trial / 'results')
                    if censored_key:
                        trials.append({**identity, 'status': 'TIMEOUT', 'seconds': 600.01,
                                       'completion_seconds_lower_bound': 600,
                                       'directory': str(trial.relative_to(run))})
                        continue
                    output = [{**row, 'ROC_AUC': .3, 'PR_AUC': .4, 'RANGE_PR_AUC': .5} for row in selected]
                    write_csv(trial / 'results/results.csv', output)
                    trials.append({**identity, 'status': 'COMPLETE', 'seconds': durations[method],
                                   'directory': str(trial.relative_to(run))})
                    available = not (censor and contract == 'native_default50' and batch['name'] == 'combined')
                    metrics.append({**identity, 'results_sha256': AUDITOR.digest(trial / 'results/results.csv'),
                                    'public_reference_available': available,
                                    'max_error_against_available_reference': 0., 'rows': output})
    summary = {'comparisons': {}, 'public_parity_available': {}}
    for contract in AUDITOR.CONTRACTS:
        summary['comparisons'][contract] = {}
        for batch in batches:
            key_censored = censor and contract == 'native_default50' and batch['name'] == 'combined'
            summary['public_parity_available'][contract + '/' + batch['name']] = not key_censored
            selected_trials = [r for r in trials if r['contract'] == contract and r['batch'] == batch['name']]
            comparisons = {}
            for a, b in [('public', 'bucket'), ('raster', 'bucket'), ('public', 'raster')]:
                ratio = durations[a] / durations[b]
                if key_censored and a == 'public':
                    value = {'completed_paired_rounds': 0, 'paired_speedups': [],
                             'censored_bounds': [{'round': 0, 'strict_speedup_lower_bound': 600 / durations[b]}],
                             'approximate_paired_order_ci95': None}
                else:
                    value = {'completed_paired_rounds': 6, 'paired_speedups': [ratio] * 6,
                             'censored_bounds': [], 'geometric_speedup': ratio,
                             'approximate_paired_order_ci95': [ratio, ratio]}
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


@pytest.mark.parametrize('censor', [False, True])
def test_audits_complete_and_prespecified_censored_records(tmp_path, censor):
    run, protocol = fixture(tmp_path, censor)
    result = AUDITOR.audit(run, protocol)
    assert result['status'] == 'INDEPENDENT_NATIVE_CONSUMER_OUTPUT_AUDIT_PASSED'
    assert result['status_counts']['COMPLETE'] == (138 if censor else 144)
    assert result['max_absolute_scalar_error'] == 0
    assert result['metric_outputs_recomputed'] is False
    assert result['runner_or_candidate_imported'] is False
    assert result['per_profile_public_reference_coverage']['native_default50']['complete'] is True
    assert result['public_parity_available']['native_default50/combined'] is not censor


def test_skip_requires_earlier_matching_censor(tmp_path):
    run, protocol = fixture(tmp_path, True)
    trials = AUDITOR.records(run / 'trials.jsonl')
    skipped = next(r for r in trials if r['status'] == 'notrun_due_to_prespecified_censor')
    skipped['first_censored_trial'] = 999
    write_lines(run / 'trials.jsonl', trials)
    update_hash(run, 'trials_sha256', 'trials.jsonl')
    with pytest.raises(ValueError, match='prior matching censor'):
        AUDITOR.audit(run, protocol)


@pytest.mark.parametrize('censor', [False, True])
def test_rejects_incorrect_or_fabricated_intervals_even_with_matching_artifact_hash(tmp_path, censor):
    run, protocol = fixture(tmp_path, censor)
    summary = AUDITOR.json_file(run / 'summary.json')
    item = summary['comparisons']['native_default50']['combined']['comparisons']['public_over_bucket']
    item['geometric_speedup'] = 4.
    item['approximate_paired_order_ci95'] = [2., 2.]
    write_json(run / 'summary.json', summary)
    update_hash(run, 'summary_sha256', 'summary.json')
    with pytest.raises(ValueError, match='fabricated|bootstrap interval'):
        AUDITOR.audit(run, protocol)


def test_rejects_scalar_disagreement_even_when_csv_json_and_hashes_agree(tmp_path):
    run, protocol = fixture(tmp_path, False)
    metrics = AUDITOR.records(run / 'metrics.jsonl')
    record = next(r for r in metrics if r['method'] == 'bucket')
    record['rows'][0]['RANGE_PR_AUC'] += 1e-5
    path = run / 'trials' / str(record['trial']) / 'results/results.csv'
    write_csv(path, record['rows'])
    record['results_sha256'] = AUDITOR.digest(path)
    write_lines(run / 'metrics.jsonl', metrics)
    update_hash(run, 'metrics_sha256', 'metrics.jsonl')
    with pytest.raises(ValueError, match='scalar output parity'):
        AUDITOR.audit(run, protocol)


def test_added_optional_native_metric_cache_invalidates_input_tree(tmp_path):
    run, protocol = fixture(tmp_path, False)
    binding = AUDITOR.json_file(protocol)['timeeval_consumer']
    path = next((Path(binding['workload_directory']) / 'results').rglob('anomaly_scores.ts'))
    path.with_name('metrics.csv').write_text('RANGE_PR_AUC\n0.5\n')
    with pytest.raises(ValueError, match='added or removed'):
        AUDITOR.audit(run, protocol)
