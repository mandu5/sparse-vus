"""Exact portability diagnostics must surface, not forgive, changed reports."""
import importlib.util
import math
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1]/'experiments/diagnose_sampling_report_portability.py'
SPEC = importlib.util.spec_from_file_location('report_portability_tests', PATH)
diagnostic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diagnostic)


def test_exact_tree_and_serialization_equality_are_separate():
    result = diagnostic.compare_payloads('{"a":1,"b":2}', '{"b":2,"a":1}')
    assert result['tree_exact_equal'] and not result['serialized_exact_equal']
    assert result['expected_tree'] == result['rebuilt_tree'] == {'a': 1, 'b': 2}


def test_nested_float_mutation_exposes_values_path_and_one_ulp():
    changed = math.nextafter(.5, 1.)
    differences = diagnostic.recursive_differences({'panel': [0.5]}, {'panel': [changed]})
    assert len(differences) == 1
    difference = differences[0]
    assert difference['path'] == '$["panel"][0]'
    assert difference['expected'] == .5 and difference['actual'] == changed
    assert difference['kind'] == 'float' and difference['ulp_distance'] == 1


@pytest.mark.parametrize('expected,actual', [(True, 1), (1, 1.), ('1', 1)])
def test_type_changes_are_not_hidden_by_python_equality(expected, actual):
    differences = diagnostic.recursive_differences(expected, actual)
    assert len(differences) == 1 and differences[0]['kind'] == 'type'
    assert differences[0]['expected_type'] == type(expected).__name__
    assert differences[0]['actual_type'] == type(actual).__name__


def test_missing_dict_key_and_list_items_are_explicit():
    differences = diagnostic.recursive_differences({'x': [1, 2], 'gone': None}, {'x': [1]})
    assert {(d['path'], d['kind']) for d in differences} == {
        ('$["gone"]', 'missing_key'), ('$["x"]', 'list_length'), ('$["x"][1]', 'missing_item')}
    assert diagnostic.recursive_differences([], [2])[1]['kind'] == 'unexpected_item'


def test_signed_zero_and_negative_float_steps_remain_visible():
    assert diagnostic.recursive_differences(-0., 0.)[0]['ulp_distance'] == 1
    assert diagnostic.float_ulp_distance(-1., math.nextafter(-1., 0.)) == 1
    assert diagnostic.float_ulp_distance(float('inf'), 1.) is None


def test_identical_nested_tree_has_no_differences():
    value = {'a': [None, True, 1, .5, 'x'], 'b': {}}
    assert diagnostic.recursive_differences(value, value) == []
