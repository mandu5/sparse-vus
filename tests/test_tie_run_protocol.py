"""Research receipts must bind decisions to the frozen contract."""
import importlib.util
import json
from pathlib import Path
import random

import pytest


def fixture(tmp_path, monkeypatch, *, tolerance=1e-11):
    path = Path(__file__).resolve().parents[1]/'experiments/benchmark_tie_runs.py'
    spec = importlib.util.spec_from_file_location('tie_run_benchmark_test', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, 'ROOT', tmp_path)
    source = tmp_path/'candidate.py'
    source.write_text('original implementation\n')
    output = tmp_path/'study'
    output.mkdir()
    item = {'case_id': 'fixture', 'phase': 'development', 'family': 'fixture',
            'max_buffer': 0, 'positive_points': 1}
    (output/'inputs.json').write_text(json.dumps([item]))
    p = {'version': 1, 'methods': list(mod.METHODS), 'repetitions': 1,
         'seed': 19, 'parity_atol': tolerance, 'cases': 1,
         'source_sha256': {'candidate.py': mod.digest(source)},
         'manifest_sha256': {}, 'inputs_sha256': mod.digest(output/'inputs.json')}
    (output/'protocol.json').write_text(json.dumps(p))
    order = list(mod.METHODS)
    random.Random(19).shuffle(order)
    row = {**item, 'orders': [order], 'methods': {name: {
        'seconds': [1.], 'values': [.5+(1e-13 if name == 'tie_runs' else 0.)]}
        for name in mod.METHODS}, 'tie_profile': {'events': [1], 'run_queries': [1]},
        'position_profile': {'visited': [1]}}
    (output/'measurements.jsonl').write_text(json.dumps(row)+'\n')
    done = {'status': 'COMPLETE', 'cases': 1,
            'protocol_sha256': mod.digest(output/'protocol.json'),
            'measurements_sha256': mod.digest(output/'measurements.jsonl')}
    (output/'completion.json').write_text(json.dumps(done))
    return mod, output, source


def test_report_uses_frozen_tolerance(tmp_path, monkeypatch):
    mod, output, _ = fixture(tmp_path, monkeypatch, tolerance=1e-14)
    assert mod.report(output)['status'] == 'FAIL'


def test_report_rejects_measured_source_drift(tmp_path, monkeypatch):
    mod, output, source = fixture(tmp_path, monkeypatch)
    source.write_text('changed implementation\n')
    with pytest.raises(ValueError, match='Source changed'):
        mod.report(output)
