"""Acquisition identity boundaries, independent of metric execution."""
import hashlib
import importlib.util
from pathlib import Path

import pytest


SPEC=importlib.util.spec_from_file_location('fresh_replay',Path(__file__).resolve().parents[1]/'experiments/reproduce_strengthening.py')
REPLAY=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)


@pytest.mark.parametrize('mutation',['changed','missing','extra'])
def test_complete_source_tree_rejects_changed_missing_or_extra_files(tmp_path,mutation):
    path=tmp_path/'source.py'
    path.write_bytes(b'fixed source')
    expected={'source.py':hashlib.sha256(path.read_bytes()).hexdigest()}
    assert REPLAY.verify_source_tree(tmp_path,expected)==1
    if mutation=='changed':path.write_bytes(b'other source')
    elif mutation=='missing':path.unlink()
    else:(tmp_path/'extra.py').write_bytes(b'additional executable source')
    with pytest.raises(ValueError,match='complete source tree identity'):
        REPLAY.verify_source_tree(tmp_path,expected)
