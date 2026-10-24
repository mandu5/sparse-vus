"""Acquisition boundary tests: do not train detectors or evaluate metrics."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import hashlib
import json

import numpy as np
import pytest


def preparer():
    path = Path(__file__).resolve().parents[1] / "scripts/prepare_strengthening_workload.py"
    assert path.exists(), "The frozen-workload acquisition implementation is missing"
    spec = spec_from_file_location("strengthening_workload", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_raw_parser_preserves_order_and_rejects_nonbinary_labels():
    module = preparer()
    x, labels = module.parse_raw(b"value,Label\n3.5,0\n-2.25,1\n0.125,0\n")
    np.testing.assert_array_equal(x, [[3.5], [-2.25], [0.125]])
    np.testing.assert_array_equal(labels, [0, 1, 0])
    assert x.shape == (3, 1)
    assert labels.dtype == np.int8
    with pytest.raises(ValueError):
        module.parse_raw(b"value,Label\n3.5,0\n-2.25,0.5\n0.125,1\n")
    with pytest.raises(ValueError):
        module.parse_raw(b"value,Label\n3.5,0\nnan,1\n0.125,0\n")


@pytest.mark.parametrize("invalid", ["upstream failed", np.array([1.0]),
                                      np.array([[0.0, 1.0]]),
                                      np.array([0.0, np.inf])])
def test_invalid_public_output_is_not_coerced_into_a_score(invalid):
    with pytest.raises(ValueError):
        preparer().validate_score(invalid, 2)


def test_native_score_serialization_preserves_ties_and_float_bits(tmp_path):
    module = preparer()
    score = np.array([-0.0, 0.0, np.nextafter(1.0, 2.0),
                      np.nextafter(1.0, 0.0), np.finfo(float).tiny,
                      np.finfo(float).max])
    target = tmp_path / "anomaly_scores.ts"
    module.write_native_score(target, score)
    loaded = np.genfromtxt(target)
    assert loaded.tobytes() == score.tobytes()
    tied = module.validate_score(np.zeros(6), 6)
    assert tied.tobytes() == np.zeros(6).tobytes()


def test_changed_upstream_source_is_rejected(tmp_path):
    module = preparer()
    source = tmp_path / "detector.py"
    source.write_bytes(b"original source\n")
    entries = [{"path": "detector.py", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]
    module.verify_files(tmp_path, entries)
    source.write_bytes(b"changed source\n")
    with pytest.raises(ValueError):
        module.verify_files(tmp_path, entries)


def test_frozen_protocol_cannot_be_overwritten(tmp_path):
    module = preparer()
    target = tmp_path / "protocol.json"
    module.write_new_json(target, {"selection": "first"})
    with pytest.raises(FileExistsError):
        module.write_new_json(target, {"selection": "replacement"})
    assert json.loads(target.read_text()) == {"selection": "first"}


def test_shared_cache_symlink_keeps_portable_logical_path(tmp_path):
    module = preparer()
    worktree = tmp_path / "worktree"
    shared_cache = tmp_path / "shared-cache"
    worktree.mkdir()
    shared_cache.mkdir()
    (worktree / ".cache").symlink_to(shared_cache, target_is_directory=True)
    target = shared_cache / "workload/arrays/example.npz"
    assert module.relative_cache_path(target, worktree) == ".cache/workload/arrays/example.npz"


def decoding_fixture(module):
    raw=b'Data,Label\n1,0\n2.9364790299813794,1\n4,0\n'
    rounded=float.fromhex('0x1.77de8b7b94754p+1')
    old=float.fromhex('0x1.77de8b7b94753p+1')
    x=np.array([[1.], [rounded], [4.]])
    restored=x.copy();restored[1,0]=old
    entry={'raw_member_sha256':hashlib.sha256(raw).hexdigest(),
           'row_index_zero_based':1,'column':'Data','literal':'2.9364790299813794',
           'original_frozen_binary64_hex':old.hex(),
           'correctly_rounded_binary64_hex':rounded.hex(),
           'original_frozen_observation_sha256':module.array_sha(restored[:,0]),
           'correctly_rounded_observation_sha256':module.array_sha(x[:,0])}
    return raw,x,restored,entry


def test_declared_decoding_restores_exact_frozen_bits_and_is_idempotent():
    module=preparer();raw,x,want,entry=decoding_fixture(module)
    actual=module.restore_frozen_decoding(raw,x,[entry])
    assert actual.tobytes()==want.tobytes()
    assert module.restore_frozen_decoding(raw,actual,[entry]).tobytes()==want.tobytes()
    assert x.tobytes()!=want.tobytes(), 'caller input must not be overwritten'


def test_decoding_contract_does_not_waive_other_observation_changes():
    module=preparer();raw,x,_,entry=decoding_fixture(module)
    x[0,0]=2.
    with pytest.raises(ValueError,match='no decoding waiver'):
        module.restore_frozen_decoding(raw,x,[entry])


@pytest.mark.parametrize('field,value',[
    ('literal','wrong literal'),('row_index_zero_based',999),
    ('original_frozen_binary64_hex','0x1.77de8b7b94752p+1')])
def test_decoding_requires_exact_literal_index_and_adjacent_value(field,value):
    module=preparer();raw,x,_,entry=decoding_fixture(module)
    entry[field]=value
    with pytest.raises(ValueError):
        module.restore_frozen_decoding(raw,x,[entry])
