"""Diagnose exact frozen-report portability without accepting any tolerance.

Rebuilds the main report using its unchanged producer functions. No metric is
executed and no frozen output is modified. Exit 0 means identical JSON bytes;
exit 1 means a mismatch (including float last-bit differences); exit 2 means
the diagnostic could not complete. --output must name a new file.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import platform
import struct
import sys
import traceback
import warnings

ROOT = Path(__file__).resolve().parents[1]
STUDY = 'artifacts/msad-sampling-20261023'


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            result.update(block)
    return result.hexdigest()


def float_ulp_distance(expected, actual):
    """Binary64 representable-step distance; None for nonfinite inputs."""
    if not math.isfinite(expected) or not math.isfinite(actual):
        return None
    def ordered(value):
        bits = struct.unpack('>Q', struct.pack('>d', value))[0]
        return (~bits & ((1 << 64)-1)) if bits >> 63 else bits | (1 << 63)
    return abs(ordered(expected)-ordered(actual))


def recursive_differences(expected, actual, path='$'):
    """Return all exact JSON-tree differences, exposing both tree values.

    Paths use bracket notation. Type mismatches are retained even where
    Python equality would conflate bool/int or int/float. Float comparisons
    distinguish signed zero and report ULP distance without a tolerance.
    """
    differences = []
    def item(kind, location, old, new, **extra):
        entry = {'path': location, 'kind': kind,
                 'expected_type': type(old).__name__, 'actual_type': type(new).__name__,
                 'expected': old, 'actual': new}
        entry.update(extra)
        differences.append(entry)
    def visit(old, new, location):
        if type(old) is not type(new):
            item('type', location, old, new)
        elif isinstance(old, dict):
            for key in sorted(set(old) | set(new)):
                child = location+'['+json.dumps(key, ensure_ascii=False)+']'
                if key not in old:
                    item('unexpected_key', child, None, new[key], expected_present=False, actual_present=True)
                elif key not in new:
                    item('missing_key', child, old[key], None, expected_present=True, actual_present=False)
                else:
                    visit(old[key], new[key], child)
        elif isinstance(old, list):
            if len(old) != len(new):
                item('list_length', location, len(old), len(new), container_type='list')
            for index in range(max(len(old), len(new))):
                child = f'{location}[{index}]'
                if index >= len(old):
                    item('unexpected_item', child, None, new[index], expected_present=False, actual_present=True)
                elif index >= len(new):
                    item('missing_item', child, old[index], None, expected_present=True, actual_present=False)
                else:
                    visit(old[index], new[index], child)
        elif isinstance(old, float):
            if struct.pack('>d', old) != struct.pack('>d', new):
                distance = abs(old-new)
                item('float', location, old, new, ulp_distance=float_ulp_distance(old, new),
                     absolute_difference=distance if math.isfinite(distance) else None,
                     expected_hex=old.hex(), actual_hex=new.hex())
        elif old != new:
            item('value', location, old, new)
    visit(expected, actual, path)
    return differences


def compare_payloads(expected_payload, actual_payload):
    """Compare serialized reports and return parsed trees plus exact diffs."""
    expected, actual = json.loads(expected_payload), json.loads(actual_payload)
    differences = recursive_differences(expected, actual)
    return {'expected_tree': expected, 'rebuilt_tree': actual,
            'serialized_exact_equal': expected_payload == actual_payload,
            'tree_exact_equal': not differences, 'differences': differences}


def capture_numpy_environment():
    import numpy as np
    def capture(function):
        out, err = io.StringIO(), io.StringIO()
        failure = None
        with redirect_stdout(out), redirect_stderr(err), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            try:
                function()
            except Exception as exc:
                failure = {'type': type(exc).__name__, 'message': str(exc)}
        return {'stdout': out.getvalue(), 'stderr': err.getvalue(),
                'warnings': [str(w.message) for w in caught], 'error': failure}
    runtime = capture(np.show_runtime) if hasattr(np, 'show_runtime') else {
        'available': False, 'reason': 'numpy.show_runtime is absent in this version'}
    function_info = getattr(getattr(np.lib, 'introspect', None), 'opt_func_info', None)
    if function_info is None:
        introspection = {'available': False, 'reason': 'numpy.lib.introspect.opt_func_info is absent'}
    else:
        try:
            introspection = {'available': True, 'func_name': '^(log|exp)$',
                             'result': function_info(func_name='^(log|exp)$')}
        except Exception as exc:
            introspection = {'available': True, 'error_type': type(exc).__name__, 'error': str(exc)}
    return {'python': sys.version, 'python_executable': sys.executable,
            'python_implementation': platform.python_implementation(),
            'numpy_version': np.__version__, 'platform': platform.platform(),
            'uname': dict(platform.uname()._asdict()), 'byteorder': sys.byteorder,
            'numpy_show_runtime': runtime, 'numpy_show_config': capture(np.show_config),
            'numpy_log_exp_dispatch': introspection,
            'numeric_environment': {key: os.environ.get(key) for key in (
                'NPY_DISABLE_CPU_FEATURES', 'NPY_ENABLE_CPU_FEATURES', 'NUMPY_EXPERIMENTAL_ARRAY_FUNCTION',
                'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                'VECLIB_MAXIMUM_THREADS', 'NUMBA_NUM_THREADS')}}


def diagnose(root=ROOT):
    """Rebuild through frozen functions; expose both trees for callers/tests."""
    root = Path(root)
    source = root/'experiments/msad_sampling_study.py'
    spec = importlib.util.spec_from_file_location('portability_frozen_main_report', source)
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    directory = root/STUDY
    protocol_path, records_path = directory/'protocol.json', directory/'records.jsonl'
    protocol = json.loads(protocol_path.read_text())
    manifest_path = root/protocol['acquisition_manifest']
    manifest = json.loads(manifest_path.read_text())
    records_hash = digest(records_path)
    reference = directory/f'report-{records_hash[:16]}.json'
    rebuilt = frozen.build_report(frozen.read_records(records_path).values(), manifest['series'], protocol)
    rebuilt.update(protocol_sha256=digest(protocol_path),
                   source_manifest_sha256=digest(directory/'source_manifest.json'),
                   records_sha256=records_hash)
    payload = json.dumps(rebuilt, indent=2, allow_nan=False)+'\n'
    expected_payload = reference.read_text()
    comparison = compare_payloads(expected_payload, payload)
    differences = comparison['differences']
    distances = [d['ulp_distance'] for d in differences if d['kind'] == 'float' and d['ulp_distance'] is not None]
    return {'status': 'EXACT_MATCH' if comparison['serialized_exact_equal'] else 'MISMATCH',
            'comparison_contract': 'Exact serialized JSON and exact parsed-tree comparison; no tolerance accepted',
            'scope': 'Rebuild report aggregation from preserved metric-call records; no metric execution or raw-cache reads; source integrity is checked separately by the bundle audit',
            'reference': str(reference.relative_to(root)),
            'source_sha256': digest(source), 'diagnostic_source_sha256': digest(Path(__file__)),
            'protocol_sha256': digest(protocol_path), 'manifest_sha256': digest(manifest_path),
            'source_manifest_sha256': digest(directory/'source_manifest.json'),
            'records_sha256': records_hash, 'reference_report_sha256': digest(reference),
            'rebuilt_payload_sha256': hashlib.sha256(payload.encode()).hexdigest(),
            'environment': capture_numpy_environment(),
            'difference_count': len(differences),
            'difference_counts_by_kind': dict(Counter(d['kind'] for d in differences)),
            'maximum_float_ulp_distance': max(distances, default=None), **comparison}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New diagnostic JSON file; never overwritten')
    args = parser.parse_args()
    path = Path(args.output).expanduser().resolve()
    if path.exists():
        parser.error('Output already exists; refusing to overwrite')
    try:
        result = diagnose()
        code = 0 if result['status'] == 'EXACT_MATCH' else 1
    except Exception as exc:
        result = {'status': 'ERROR', 'exception_type': type(exc).__name__,
                  'exception_message': str(exc), 'traceback': traceback.format_exc()}
        try:
            result['environment'] = capture_numpy_environment()
        except Exception as environment_error:
            result['environment_error'] = str(environment_error)
        code = 2
    with path.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'status': result['status'], 'output': str(path),
                      'serialized_exact_equal': result.get('serialized_exact_equal'),
                      'tree_exact_equal': result.get('tree_exact_equal'),
                      'difference_count': result.get('difference_count'),
                      'maximum_float_ulp_distance': result.get('maximum_float_ulp_distance')}))
    raise SystemExit(code)


if __name__ == '__main__': main()
