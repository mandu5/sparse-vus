"""Prospective v2 gates: raw equality stays mandatory; new scores are diagnostic."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REL = ROOT / 'artifacts/pvldb-research-20261024/strengthening'


def runner():
    spec = importlib.util.spec_from_file_location(
        '_new_realization', ROOT / 'scripts/run_timeeval_affinity_blocks_v2.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs():
    generation = json.loads((REL / 'linux-interval-replay/workload-generation.json').read_text())
    payload = json.loads((REL / 'linux-interval-replay/timeeval-control-global.json').read_text())['timeeval_consumer']
    return generation, payload


def test_new_score_and_query_realization_is_retained_without_claiming_prior_identity():
    r = runner(); prior, previous = inputs()
    current, payload = copy.deepcopy(prior), copy.deepcopy(previous)
    p = next(x for x in current['profiles'] if x['model'] == 'COPOD')
    p['score_array_sha256'] = p['native_score_sha256'] = 'fresh-score'
    path = next(x for x in payload['input_sha256'] if '/COPOD/' in x)
    payload['input_sha256'][path] = 'fresh-score'
    payload['query_plan'][1]['distinct_scores'] -= 1
    result = r.reference_diagnostics(current, [prior, prior], payload, [previous, previous])
    assert result['hard_inputs_match'] is True
    assert result['matches'] is False
    assert len(result['mismatches']) == 4
    assert len(result['query_plan_differences']) == 2
    assert len(result['native_score_file_differences']) == 2
    assert result['prior_score_identity_required'] is False


@pytest.mark.parametrize('change', ['raw', 'template', 'labels', 'selection', 'order', 'model', 'shape'])
def test_score_diagnostics_never_waive_raw_label_row_or_model_identity(change):
    r = runner(); prior, previous = inputs()
    current, payload = copy.deepcopy(prior), copy.deepcopy(previous)
    if change == 'raw':
        key = next(x for x in payload['input_sha256'] if x.startswith('datasets/') and x.endswith('.test.csv'))
        payload['input_sha256'][key] = 'changed'
    elif change == 'template':
        payload['input_sha256']['results/results.csv'] = 'changed'
    elif change == 'labels':
        current['cases'][0]['labels_sha256'] = 'changed'
    elif change == 'selection':
        current['selection_sha256'] = 'changed'
    elif change == 'order':
        payload['row_ids'].reverse()
    elif change == 'model':
        current['models'].reverse()
    else:
        current['profiles'][0]['shape'] = [1]
    result = r.reference_diagnostics(current, [prior, prior], payload, [previous, previous])
    assert result['hard_inputs_match'] is False
    assert result['hard_input_differences']


def test_unrecognized_extra_file_cannot_be_hidden_as_a_score_change():
    r = runner(); prior, previous = inputs(); payload = copy.deepcopy(previous)
    payload['input_sha256']['results/unexpected.csv'] = 'extra'
    assert not r.reference_diagnostics(prior, [prior, prior], payload, [previous, previous])['hard_inputs_match']


def test_new_realization_preserves_the_five_block_schedule():
    r = runner()
    spec = importlib.util.spec_from_file_location('_old_design', ROOT / 'scripts/run_timeeval_affinity_blocks.py')
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    assert r.design()['blocks'] == old.design()['blocks']
    assert r.design()['schema'] == 'timeeval-affinity-five-blocks-v2-new-realization'
    assert r.design()['failed_predecessor']['measured_blocks'] == 0
