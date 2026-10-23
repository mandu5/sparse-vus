"""Corruption, coverage, and exact-decision checks for the public-only audit."""
from copy import deepcopy
from fractions import Fraction
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1]/'experiments/audit_certified_sampling_bundle.py'
SPEC = importlib.util.spec_from_file_location('bundle_audit_tests', PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


@pytest.mark.parametrize('rows', [[{'key': 'a'}], [{'key': 'a'}, {'key': 'b'}, {'key': 'foreign'}]])
def test_missing_or_foreign_records_fail_even_if_receipt_count_is_plausible(rows):
    with pytest.raises(ValueError, match='missing or unexpected'):
        audit.unique_index(rows, lambda r: r['key'], {'a', 'b'}, 'fixture')


def test_identical_duplicate_records_are_rejected():
    with pytest.raises(ValueError, match='duplicate'):
        audit.unique_index([{'key': 'a'}, {'key': 'a'}], lambda r: r['key'])


def test_mutated_frozen_source_is_rejected(tmp_path):
    source = tmp_path/'frozen.py'
    source.write_text('value = 1\n')
    expected = audit.sha256(source)
    bundle = audit.Bundle(tmp_path)
    bundle.hash('frozen.py', expected)
    source.write_text('value = 2\n')
    with pytest.raises(ValueError, match='Hash mismatch'):
        bundle.hash('frozen.py', expected)


def test_raw_cache_is_never_read_and_only_pinned_external_commitment_is_allowed(tmp_path):
    bundle = audit.Bundle(tmp_path)
    with pytest.raises(ValueError, match='cache access prohibited'):
        bundle.hash('.cache/anything')
    bundle.sources({audit.EXTERNAL_SOURCE: audit.EXTERNAL_DIGEST})
    assert bundle.external == {audit.EXTERNAL_SOURCE: audit.EXTERNAL_DIGEST}
    with pytest.raises(ValueError, match='commitment changed'):
        bundle.sources({audit.EXTERNAL_SOURCE: '0'*64})


def test_output_never_overwrites_or_enters_artifacts(tmp_path):
    with pytest.raises(ValueError, match='outside artifacts'):
        audit.output_path(tmp_path/'artifacts'/'receipt.json', tmp_path)
    present = tmp_path/'existing.json'
    present.write_text('{}')
    with pytest.raises(ValueError, match='already exists'):
        audit.output_path(present, tmp_path)


def test_numerical_tied_winner_sets_retain_best_and_worst_regret():
    d = audit.numerical_decision({'A': .8, 'B': .5, 'C': .7}, {'A': .4, 'B': .6, 'C': .6})
    assert d['sampled_winners'] == ['B', 'C']
    assert d['best_regret'] == pytest.approx(.1)
    assert d['worst_regret'] == pytest.approx(.3)


def test_integer_cutoff_and_sub_float_margins_use_exact_arithmetic():
    rows = [dict(model='A', lower_numerator='51', upper_numerator='52', scale='100'),
            dict(model='B', lower_numerator='49', upper_numerator='50', scale='100')]
    winners, lower, upper = audit.integer_decision(rows, ['B'])
    assert winners == ['A'] and lower == Fraction(1, 100) and upper == Fraction(3, 100)
    scale = 1 << 90
    rows = [dict(model='A', lower_numerator=str(scale//2+1), upper_numerator=str(scale//2+2), scale=str(scale)),
            dict(model='B', lower_numerator=str(scale//2-1), upper_numerator=str(scale//2), scale=str(scale))]
    assert audit.integer_decision(rows, ['B'])[0] == ['A']


def stopping_fixture():
    D = 1 << 32
    return {'original_positive_count': 1, 'predicted_count': 3,
        'buffer_lower_numerator': str(2*D), 'buffer_upper_numerator': str(2*D),
        'weight_scale': str(D), 'hit_count': 1, 'components': 1,
        'saturation_buffer_threshold_numerator': str(2*D),
        'lower_mass_minus_threshold_numerator': '0', 'upper_mass_minus_threshold_numerator': '0',
        'recall_lower_fraction': ['1', '1'], 'recall_upper_fraction': ['1', '1']}


@pytest.mark.parametrize('field,value', [
    ('lower_mass_minus_threshold_numerator', '1'),
    ('recall_lower_fraction', ['1', '2']),
    ('hit_count', 2),
    ('buffer_upper_numerator', str(4 << 32)),
])
def test_corrupted_integer_stopping_witness_rejected(field, value):
    state = stopping_fixture()
    assert audit.stopping_state(state, 2) == (Fraction(1), Fraction(1))
    state[field] = value
    with pytest.raises(ValueError):
        audit.stopping_state(state, 2)


def test_predecessor_cannot_be_claimed_unsaturated_by_forged_fraction():
    state = deepcopy(stopping_fixture())
    state['recall_upper_fraction'] = ['999', '1000']
    with pytest.raises(ValueError, match='Forged recall fraction'):
        audit.stopping_state(state, 2)
