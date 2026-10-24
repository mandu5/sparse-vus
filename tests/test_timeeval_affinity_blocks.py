"""Protocol/statistical tests with fabricated durations; no metric or timing run."""
import copy
import importlib.util
import itertools
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def runner():
    path = ROOT / 'scripts/run_timeeval_affinity_blocks.py'
    assert path.is_file(), 'affinity session orchestration has not been implemented'
    spec = importlib.util.spec_from_file_location('_affinity_blocks_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generation():
    return {'status': 'ALL_SELECTED_PROFILES_GENERATED',
            'selected_cases': 26, 'selected_profiles': 52, 'successful_profiles': 52,
            'metric_evaluation_performed': False,
            'profiles': [{'case_id': f'case-{i}', 'model': m, 'status': 'Status.OK',
                          'score_array_sha256': f'array-{i}-{m}',
                          'native_score_sha256': f'text-{i}-{m}'}
                         for i in range(26) for m in ('FFT', 'COPOD')]}


def fabricated_records(plan):
    # Within each block the paired raster/bucket ratios are 1,2,4,8,16.
    # Their equal-block geometric mean is exactly 4, independent of the
    # method position and the common within-round time multiplier.
    result = []
    for block in plan['blocks']:
        ratio = 2 ** block['block']
        for trial in block['trials']:
            seconds = {'bucket': 1., 'raster': ratio,
                       'interval': 2 * ratio}[trial['method']]
            result.append({**trial, 'block': block['block'], 'status': 'COMPLETE',
                           'seconds': seconds * (trial['round'] + 1)})
    return result


def test_every_frozen_block_covers_balanced_methods_and_both_contracts():
    r = runner(); plan = r.design()
    assert [b['block'] for b in plan['blocks']] == [0, 1, 2, 3, 4]
    assert sum(len(b['trials']) for b in plan['blocks']) == 180
    permutations = set(itertools.permutations(('raster', 'interval', 'bucket')))
    for block in plan['blocks']:
        assert len(block['warmup']) == 6
        assert [t['trial'] for t in block['trials']] == list(range(36))
        for contract in ('native_default50', 'all_observed'):
            orders = []
            for repeat in range(6):
                group = [t for t in block['trials'] if t['contract'] == contract
                         and t['round'] == repeat]
                assert len(group) == 3
                orders.append(tuple(t['method'] for t in group))
            assert set(orders) == permutations
    assert plan == r.design()  # independent invocations preserve frozen order


def test_one_changed_profile_or_missing_profile_prevents_same_input_claim():
    r = runner(); original = generation(); current = copy.deepcopy(original)
    assert r.profile_identity(current, [original, original])['matches'] is True
    current['profiles'][7]['score_array_sha256'] = 'different'
    result = r.profile_identity(current, [original, original])
    assert result['matches'] is False
    assert any(x['field'] == 'score_array_sha256' for x in result['mismatches'])
    current = generation(); current['profiles'].pop()
    with pytest.raises(ValueError, match='52|coverage'):
        r.profile_identity(current, [original, original])


def test_disagreement_between_two_linux_reference_hashes_is_not_ignored():
    r = runner(); original = generation(); control = copy.deepcopy(original)
    control['profiles'][3]['native_score_sha256'] = 'different'
    assert r.profile_identity(original, [original, control])['matches'] is False


def test_resampling_uses_five_blocks_and_retains_the_extreme_block():
    r = runner(); plan = r.design()
    summary = r.summarize(fabricated_records(plan), plan)
    value = summary['comparisons']['all_observed/raster_over_bucket']
    assert value['block_ratios'] == pytest.approx([1., 2., 4., 8., 16.])
    assert value['geometric_ratio'] == pytest.approx(4.)
    assert value['block_range'] == pytest.approx([1., 16.])
    assert value['resampling_units'] == 5
    assert value['exact_bootstrap_sequences'] == 3125
    assert value['within_block_pairs'] == [6] * 5
    # If the individual 30 order pairs were resampled as independent units,
    # this interval would be narrower and the stated unit count would fail.
    lo, hi = value['descriptive_block_bootstrap95_bonferroni4']
    assert lo < 2 and hi > 8
    assert summary['comparisons']['native_default50/interval_over_bucket'][
        'geometric_ratio'] == pytest.approx(8.)


@pytest.mark.parametrize('alteration', ['missing', 'duplicate', 'wrong_identity'])
def test_incomplete_or_relabelled_schedule_cannot_produce_a_complete_summary(alteration):
    r = runner(); plan = r.design(); records = fabricated_records(plan)
    if alteration == 'missing':
        records.pop()
    elif alteration == 'duplicate':
        records.append(copy.deepcopy(records[0]))
    else:
        records[0]['method'] = 'public'
    with pytest.raises(ValueError, match='coverage|identity|duplicate'):
        r.summarize(records, plan)


def test_a_timeout_is_retained_and_prevents_a_five_complete_block_interval():
    r = runner(); plan = r.design(); records = fabricated_records(plan)
    row = next(x for x in records if x['block'] == 4 and x['method'] == 'raster'
               and x['contract'] == 'all_observed')
    row['status'] = 'TIMEOUT'; row['seconds'] = 600.1
    summary = r.summarize(records, plan)
    value = summary['comparisons']['all_observed/raster_over_bucket']
    assert value['descriptive_block_bootstrap95_bonferroni4'] is None
    assert value['block_ratios'][-1] is None
    assert value['complete_blocks'] == 4
    assert summary['status_counts']['TIMEOUT'] == 1
    assert summary['comparisons']['all_observed/interval_over_bucket'][
        'complete_blocks'] == 5


def test_cpu_policy_never_selects_an_unpermitted_core():
    r = runner()
    assert r.choose_core([7, 3, 9]) == 3
    with pytest.raises(ValueError, match='permitted'):
        r.choose_core([])


def test_changed_file_invalidates_the_frozen_orchestration_binding(tmp_path):
    r = runner(); path = tmp_path / 'source.py'; path.write_text('original')
    bindings = {str(path): r.digest(path)}
    r.verify_files(bindings)
    path.write_text('changed')
    with pytest.raises(ValueError, match='binding'):
        r.verify_files(bindings)


def test_pairwise_output_gate_catches_two_methods_straddling_a_reference():
    r = runner()

    def compare(x, y):
        difference = abs(x - y)
        if difference > 1e-10:
            raise ValueError('scalar parity exceeded')
        return difference

    # Both perturbed outputs pass against the first result, yet differ from
    # each other by more than the permitted absolute scalar error.
    earlier = [0.5, 0.5 + 0.75e-10]
    current = 0.5 - 0.75e-10
    assert compare(current, earlier[0]) < 1e-10
    with pytest.raises(ValueError, match='parity'):
        r.pairwise_error(current, earlier, compare)


def test_full_trial_rows_after_failed_final_binding_gate_cannot_supply_a_block(tmp_path):
    r = runner(); plan = r.design(); records = fabricated_records(plan)
    # A child can write every timing row and then fail its final input check.
    # Those rows remain visible, but cannot stand in for a successful block.
    eligibility = {i: {'eligible': True, 'reasons': []} for i in range(5)}
    eligibility[4] = r.block_eligibility(tmp_path, {'block': 4, 'returncode': 1,
                                                 'block_complete_sha256': None}, 'frozen', 7)
    assert eligibility[4]['eligible'] is False
    result = r.summarize(records, plan, eligibility)
    for value in result['comparisons'].values():
        assert value['within_block_pairs'] == [6] * 5
        assert value['paired_order_ratios_by_block'][4]  # retained, not hidden
        assert value['complete_blocks'] == 4
        assert value['block_ratios'][4] is None
        assert value['descriptive_block_bootstrap95_bonferroni4'] is None


def test_cross_block_comparison_rejects_a_common_shift_of_all_methods():
    r = runner()

    def compare(x, y):
        error = max(abs(a - b) for a, b in zip(x, y))
        if error > 1e-10:
            raise ValueError('default-three scalar parity exceeded')
        return error

    outputs = [{'block': block, 'contract': 'native_default50', 'path': f'{block}/{method}',
                'values': [0.3, 0.4, 0.5 + (0.01 if block == 4 else 0)]}
               for block in range(5) for method in ('raster', 'interval', 'bucket')]
    result = r.compare_block_outputs(outputs, compare)
    assert result['status'] == 'FAILED'
    assert any(failure['right_block'] == 4 for failure in result['failures'])
    assert result['compared_cross_block_pairs'] == 90


def test_malformed_child_trace_is_retained_without_aborting_the_supervisor(tmp_path):
    r = runner(); path = tmp_path / 'trials.jsonl'
    raw = b'{"block":0,"trial":0,"status":"COMPLETE"}\n{"block":0,"trial":'
    path.write_bytes(raw)
    rows, issues = r.read_trial_trace(path)
    assert rows == [{'block': 0, 'trial': 0, 'status': 'COMPLETE'}]
    assert issues and issues[0]['line'] == 2
    assert path.read_bytes() == raw


def test_an_auxiliary_thread_cannot_escape_the_fixed_affinity_or_pool_limit():
    r = runner()
    r.validate_threads({101: [7], 102: [7]}, 7, [{'num_threads': 1}])
    with pytest.raises(ValueError, match='affinity'):
        r.validate_threads({101: [7], 102: [7, 8]}, 7, [{'num_threads': 1}])
    with pytest.raises(ValueError, match='pool'):
        r.validate_threads({101: [7]}, 7, [{'num_threads': 2}])


def test_supervisor_attempts_all_five_after_a_crashed_child_leaves_a_partial_line(tmp_path, monkeypatch):
    r = runner(); plan = r.design(); rows = fabricated_records(plan)
    host = {'permitted_affinity': [7, 8], 'cpu_models': ['fixture'],
            'hostname': 'fixture', 'boot_id': 'fixture'}
    protocol = {'study': plan, 'chosen_core': 7, 'supervisor_preflight': host}
    monkeypatch.setattr(r, 'check_protocol', lambda *args: protocol)
    monkeypatch.setattr(r, 'cpu_receipt', lambda *args: host)
    # The native CSV auditor has its separate real-array path; this regression
    # isolates process continuation and eligibility using only fabricated data.
    monkeypatch.setattr(r, 'audit_saved_outputs', lambda *args:
                        {'status': 'PASS', 'complete_output_coverage': True})
    attempted = []

    class Child:
        def __init__(self, command, **kwargs):
            self.block = int(command[command.index('--block') + 1])
            self.directory = Path(command[command.index('--out') + 1])
            self.pid = 9000 + self.block
            attempted.append(self.block)

        def wait(self):
            selected = [row for row in rows if row['block'] == self.block]
            text = ''.join(json.dumps(row) + '\n' for row in selected)
            if self.block == 0:
                text += '{"block":0,"trial":'
            (self.directory / 'trials.jsonl').write_text(text)
            if self.block == 0:
                return 1  # all timing rows exist, but final validation did not finish
            (self.directory / 'metrics.jsonl').write_text('')
            for name in ('child-initial.json', 'block-start.json'):
                r.write_new(self.directory / name, {})
            r.write_new(self.directory / 'block-complete.json', {
                'block': self.block, 'protocol_sha256': 'fixture-protocol',
                'recorded_trials': 36, 'status': 'COMPLETE',
                'input_bindings_verified_after_block': True,
                'native_cpu': {'permitted_affinity': [7]},
                'thread_contract': {'affinities_by_tid': {'101': [7]},
                                    'numerical_pools': [{'num_threads': 1}]},
                'evidence_sha256': {name: r.digest(self.directory / name) for name in
                                   ('child-initial.json', 'block-start.json', 'trials.jsonl', 'metrics.jsonl')}})
            return 0

    monkeypatch.setattr(r.subprocess, 'Popen', Child)
    out = tmp_path / 'run'
    args = SimpleNamespace(protocol=tmp_path / 'protocol.json',
                           protocol_sha256='fixture-protocol', out=out)
    with pytest.raises(ValueError, match='five complete valid blocks'):
        r.run_sessions(args)
    assert attempted == [0, 1, 2, 3, 4]
    receipts = r.read_json(out / 'session-processes.json')
    assert receipts[0]['trace_parse_issues'][0]['line'] == 37
    assert (out / 'blocks/00/trials.jsonl').read_bytes().endswith(b'{"block":0,"trial":')
    assert r.read_json(out / 'complete.json')['observed_trials'] == 180
    for comparison in r.read_json(out / 'summary.json')['comparisons'].values():
        assert comparison['complete_blocks'] == 4
        assert comparison['descriptive_block_bootstrap95_bonferroni4'] is None


@pytest.mark.parametrize('status', ['INVALID_OUTPUT', 'TIMEOUT'])
def test_invalid_output_invalidates_whole_block_but_timeout_only_its_comparison(tmp_path, status):
    r = runner(); plan = r.design(); records = fabricated_records(plan)
    row = next(item for item in records if item['block'] == 4
               and item['contract'] == 'native_default50' and item['method'] == 'raster')
    row['status'] = status
    selected = [item for item in records if item['block'] == 4]
    (tmp_path / 'trials.jsonl').write_text(''.join(json.dumps(item) + '\n' for item in selected))
    (tmp_path / 'metrics.jsonl').write_text('')
    for name in ('child-initial.json', 'block-start.json'):
        r.write_new(tmp_path / name, {})
    r.write_new(tmp_path / 'block-complete.json', {
        'block': 4, 'protocol_sha256': 'fixture-protocol', 'recorded_trials': 36,
        'status': 'COMPLETE_WITH_FAILED_TRIALS', 'input_bindings_verified_after_block': True,
        'native_cpu': {'permitted_affinity': [7]},
        'thread_contract': {'affinities_by_tid': {'101': [7]}, 'numerical_pools': [{'num_threads': 1}]},
        'evidence_sha256': {name: r.digest(tmp_path / name) for name in
                           ('child-initial.json', 'block-start.json', 'trials.jsonl', 'metrics.jsonl')}})
    process = {'block': 4, 'returncode': 0, 'trace_parse_issues': [],
               'block_complete_sha256': r.digest(tmp_path / 'block-complete.json')}
    eligibility = {i: {'eligible': True, 'reasons': []} for i in range(5)}
    eligibility[4] = r.block_eligibility(tmp_path, process, 'fixture-protocol', 7)
    assert eligibility[4]['eligible'] is (status == 'TIMEOUT')
    if status == 'INVALID_OUTPUT':
        assert any('INVALID_OUTPUT' in reason for reason in eligibility[4]['reasons'])
    summary = r.summarize(records, plan, eligibility)
    for name, comparison in summary['comparisons'].items():
        suppressed = status == 'INVALID_OUTPUT' or name == 'native_default50/raster_over_bucket'
        assert comparison['complete_blocks'] == (4 if suppressed else 5)
        assert (comparison['descriptive_block_bootstrap95_bonferroni4'] is None) is suppressed
