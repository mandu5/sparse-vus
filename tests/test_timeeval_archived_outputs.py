"""Archive integrity tests with fabricated durations and no retained raw inputs."""
import importlib.util
import json
from pathlib import Path
import shutil
import struct

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LEGACY = load('_legacy_archive_fixture', 'tests/test_timeeval_audit.py')
CONTROL = load('_control_archive_fixture', 'tests/test_timeeval_interval_control.py')
AUDITOR = load('_standalone_native_archive_auditor', 'experiments/audit_timeeval_archived_outputs.py')


def fixture(tmp_path, kind='original', censor=False):
    factory = LEGACY if kind == 'original' else CONTROL
    run, protocol = factory.fixture(tmp_path, censor)
    value = AUDITOR.json_file(protocol)
    binding = value['timeeval_consumer']
    binding.update(schema='timeeval-consumer-study-v1', source_revision=AUDITOR.REVISION,
                   records=len(binding['row_ids']), timing_or_metric_outcomes_consumed=False)
    binding['design']['bootstrap'] = {'samples': 10000, 'seed': 20261024}
    binding['query_plan'] = []
    threshold_sha = AUDITOR.hashlib.sha256(struct.pack('<d', 1.)).hexdigest()
    for identity in binding['row_ids']:
        binding['query_plan'].append({**dict(zip(AUDITOR.IDS, identity)),
            'n': 4, 'distinct_scores': 2, 'constant_score_shortcut': False,
            'contracts': {name: {'emitted_queries': 1, 'thresholds_binary64_le_sha256': threshold_sha}
                          for name in AUDITOR.CONTRACTS}})
    for batch in binding['batches']:
        batch['query_counts'] = {name: {'total': batch['row_count'], 'minimum': 1, 'maximum': 1}
                                 for name in AUDITOR.CONTRACTS}
    manifest = tmp_path / 'manifest.json'
    LEGACY.write_json(manifest, binding)
    value['manifest_sha256'] = AUDITOR.digest(manifest)
    LEGACY.write_json(protocol, value)
    LEGACY.write_json(run / 'bound-protocol.json', value)
    for filename in ('run-start.json', 'complete.json'):
        receipt = AUDITOR.json_file(run / filename)
        receipt['global_protocol_sha256'] = AUDITOR.digest(protocol)
        LEGACY.write_json(run / filename, receipt)
    # Model the published archive: retain result CSVs/logs, remove all detector
    # scores, native dataset inputs, upstream source trees and dependency bytes.
    for path in (run / 'trials').rglob('anomaly_scores.ts'):
        path.unlink()
    for key in ('workload_directory', 'source_directory', 'prts_directory'):
        shutil.rmtree(binding[key])
    return run, protocol, manifest


@pytest.mark.parametrize('kind', ['original', 'control'])
@pytest.mark.parametrize('censor', [False, True])
def test_archive_reconstructs_both_studies_without_input_or_source_bytes(tmp_path, kind, censor):
    run, protocol, manifest = fixture(tmp_path, kind, censor)
    result = AUDITOR.audit(run, protocol, manifest)
    assert result['status'] == 'ARCHIVED_NATIVE_OUTPUT_RECONSTRUCTION_PASSED'
    assert result['study_kind'] == ('original_public_comparison' if kind == 'original' else 'compiled_interval_control')
    assert result['local_input_bytes_verified'] is False
    assert result['local_source_bytes_verified'] is False
    assert result['metric_outputs_recomputed'] is False
    assert result['runner_or_candidate_imported'] is False
    assert result['status_counts']['COMPLETE'] == (138 if censor else 144)
    assert result['max_absolute_scalar_error'] == 0.
    if kind == 'control':
        assert result['public_reference_evaluated'] is False
        assert not any(result['public_parity_available'].values())
    else:
        assert result['per_profile_public_reference_coverage']['native_default50']['complete'] is True


@pytest.mark.parametrize('tamper', ['missing', 'modified'])
def test_missing_or_modified_completed_csv_fails(tmp_path, tamper):
    run, protocol, manifest = fixture(tmp_path)
    record = AUDITOR.records(run / 'trials.jsonl')[0]
    path = run / record['directory'] / 'results/results.csv'
    if tamper == 'missing':
        path.unlink()
    else:
        path.write_text(path.read_text().replace('0.5', '0.6'))
    with pytest.raises(ValueError, match='completed result CSV'):
        AUDITOR.audit(run, protocol, manifest)


def test_modified_protocol_rejected_against_run_receipts(tmp_path):
    run, protocol, manifest = fixture(tmp_path)
    value = AUDITOR.json_file(protocol)
    value['extra_unbound_field'] = 'changed after timing'
    LEGACY.write_json(protocol, value)
    with pytest.raises(ValueError, match='global protocol binding'):
        AUDITOR.audit(run, protocol, manifest)


def test_standalone_manifest_must_equal_embedded_frozen_payload(tmp_path):
    run, protocol, manifest = fixture(tmp_path)
    value = AUDITOR.json_file(manifest)
    value['records'] += 1
    LEGACY.write_json(manifest, value)
    with pytest.raises(ValueError, match='manifest'):
        AUDITOR.audit(run, protocol, manifest)


def test_wrong_schedule_fails_even_when_record_hash_is_repaired(tmp_path):
    run, protocol, manifest = fixture(tmp_path)
    records = AUDITOR.records(run / 'trials.jsonl')
    records[0]['method'] = 'bucket'
    LEGACY.write_lines(run / 'trials.jsonl', records)
    LEGACY.update_hash(run, 'trials_sha256', 'trials.jsonl')
    with pytest.raises(ValueError, match='trial identity/order'):
        AUDITOR.audit(run, protocol, manifest)


def test_missing_trial_coverage_fails_even_when_hash_is_repaired(tmp_path):
    run, protocol, manifest = fixture(tmp_path)
    records = AUDITOR.records(run / 'trials.jsonl')[:-1]
    LEGACY.write_lines(run / 'trials.jsonl', records)
    LEGACY.update_hash(run, 'trials_sha256', 'trials.jsonl')
    with pytest.raises(ValueError, match='144-record coverage'):
        AUDITOR.audit(run, protocol, manifest)


def test_wrong_profile_identity_fails_with_consistent_csv_and_json(tmp_path):
    run, protocol, manifest = fixture(tmp_path)
    metrics = AUDITOR.records(run / 'metrics.jsonl')
    record = metrics[0]
    record['rows'][0]['dataset'] = 'wrong-profile'
    path = run / AUDITOR.records(run / 'trials.jsonl')[0]['directory'] / 'results/results.csv'
    rows = AUDITOR.csv_rows(path)
    rows[0]['dataset'] = 'wrong-profile'
    LEGACY.write_csv(path, rows)
    record['results_sha256'] = AUDITOR.digest(path)
    LEGACY.write_lines(run / 'metrics.jsonl', metrics)
    LEGACY.update_hash(run, 'metrics_sha256', 'metrics.jsonl')
    with pytest.raises(ValueError, match='row identities'):
        AUDITOR.audit(run, protocol, manifest)


@pytest.mark.parametrize('kind', ['original', 'control'])
def test_fabricated_ci_for_censored_pairs_rejected(tmp_path, kind):
    run, protocol, manifest = fixture(tmp_path, kind, True)
    summary = AUDITOR.json_file(run / 'summary.json')
    pair = 'public_over_bucket' if kind == 'original' else 'interval_over_bucket'
    value = summary['comparisons']['native_default50']['combined']['comparisons'][pair]
    value['geometric_speedup'] = 2.
    value['approximate_paired_order_ci95'] = [1.5, 2.5]
    LEGACY.write_json(run / 'summary.json', summary)
    LEGACY.update_hash(run, 'summary_sha256', 'summary.json')
    with pytest.raises(ValueError, match='fabricated interval'):
        AUDITOR.audit(run, protocol, manifest)


def test_reconstructed_ratios_do_not_trust_saved_summary(tmp_path):
    run, protocol, manifest = fixture(tmp_path, 'control')
    summary = AUDITOR.json_file(run / 'summary.json')
    value = summary['comparisons']['all_observed']['combined']['comparisons']['interval_over_bucket']
    value['paired_speedups'][0] = 10.
    LEGACY.write_json(run / 'summary.json', summary)
    LEGACY.update_hash(run, 'summary_sha256', 'summary.json')
    with pytest.raises(ValueError, match='paired ratios'):
        AUDITOR.audit(run, protocol, manifest)


def test_compiled_archive_cannot_invent_public_coverage(tmp_path):
    run, protocol, manifest = fixture(tmp_path, 'control')
    summary = AUDITOR.json_file(run / 'summary.json')
    summary['public_parity_available']['native_default50/combined'] = True
    LEGACY.write_json(run / 'summary.json', summary)
    LEGACY.update_hash(run, 'summary_sha256', 'summary.json')
    with pytest.raises(ValueError, match='public reference'):
        AUDITOR.audit(run, protocol, manifest)


def test_same_trial_directory_cannot_stand_for_two_executions(tmp_path):
    run, protocol, manifest = fixture(tmp_path, 'control')
    records = AUDITOR.records(run / 'trials.jsonl')
    records[1]['directory'] = records[0]['directory']
    LEGACY.write_lines(run / 'trials.jsonl', records)
    LEGACY.update_hash(run, 'trials_sha256', 'trials.jsonl')
    with pytest.raises(ValueError, match='distinct trial directories'):
        AUDITOR.audit(run, protocol, manifest)


def test_scalar_disagreement_is_detected_after_all_output_hashes_match(tmp_path):
    run, protocol, manifest = fixture(tmp_path, 'control')
    metrics = AUDITOR.records(run / 'metrics.jsonl')
    record = next(r for r in metrics if r['method'] == 'interval')
    record['rows'][0]['RANGE_PR_AUC'] += 1e-5
    trial = AUDITOR.records(run / 'trials.jsonl')[record['trial']]
    path = run / trial['directory'] / 'results/results.csv'
    rows = AUDITOR.csv_rows(path)
    rows[0]['RANGE_PR_AUC'] = record['rows'][0]['RANGE_PR_AUC']
    LEGACY.write_csv(path, rows)
    record['results_sha256'] = AUDITOR.digest(path)
    LEGACY.write_lines(run / 'metrics.jsonl', metrics)
    LEGACY.update_hash(run, 'metrics_sha256', 'metrics.jsonl')
    with pytest.raises(ValueError, match='scalar output parity'):
        AUDITOR.audit(run, protocol, manifest)
