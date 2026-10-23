"""Synthetic checks for the full-grid certificate ledger's exact decisions."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / 'experiments/msad_full_certificate_study.py'
spec = importlib.util.spec_from_file_location('msad_full_certificate_tests', PATH)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def interval(model, lower, upper, scale=100):
    return dict(model=model, status='ok', lower_numerator=str(lower),
                upper_numerator=str(upper), scale=str(scale))


def test_exact_separation_and_regret_at_declared_cutoff():
    rows = [interval('A', 51, 52), interval('B', 49, 50)]
    d = study.decide(rows, ['B'])
    assert d['certified_unique_winner'] == ['A']
    assert d['sampled_set_certifiably_suboptimal']
    assert d['sampled_set_certified_regret_at_least_0_01']
    assert d['regret_lower_numerator'] == '1'
    assert d['regret_lower_denominator'] == '100'


def test_touching_intervals_and_sampled_tie_preserve_uncertainty():
    rows = [interval('A', 50, 52), interval('B', 49, 50)]
    assert study.decide(rows, ['B'])['certified_unique_winner'] == []
    assert not study.decide(rows, ['A', 'B'])['sampled_set_certifiably_suboptimal']


def test_bigint_decisions_do_not_coerce_to_float():
    scale = 1 << 90
    rows = [interval('A', scale//2+1, scale//2+2, scale),
            interval('B', scale//2-1, scale//2, scale)]
    assert study.decide(rows, ['B'])['certified_unique_winner'] == ['A']


def test_invalid_or_duplicate_models_rejected():
    with pytest.raises(ValueError, match='duplicate'):
        study.decide([interval('A', 1, 2), interval('A', 1, 2)], ['A'])
    with pytest.raises(ValueError):
        study.decide([interval('A', 2, 1), interval('B', 0, 1)], ['B'])


def test_overlap_is_not_mistaken_for_nesting_or_equality():
    full = interval('A', 45, 55)
    old = interval('A', 40, 50)
    relation = study.compare_intervals(full, old)
    assert relation['overlap'] and not relation['full_contained_in_sampled']
    assert not relation['identical']
    assert not study.compare_intervals(full, interval('A', 0, 44))['overlap']
