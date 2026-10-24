import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


def module():
    path=Path(__file__).resolve().parents[1]/'experiments/klein_support_control.py'
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location('klein_support_control',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_source_patch_rejects_unexpected_or_duplicate_anchor():
    m=module()
    with pytest.raises(ValueError):m.patch('unrelated code')
    with pytest.raises(ValueError):m.patch(m.OLD+'\n'+m.OLD)


@pytest.mark.parametrize('width',[0,1,2,8,30])
def test_minimal_support_threshold_change_preserves_complete_global_ties(width):
    from sparse_vus.radix import sparse_pr_radix_jit
    m=module();rng=np.random.default_rng(20261024)
    for _ in range(12):
        y=rng.integers(0,2,24,dtype=np.int8);y[0]=0;y[1]=1
        scores=rng.integers(-3,5,len(y)).astype(float)
        got=m.klein_support_pr(y,scores,width)
        assert got==pytest.approx(sparse_pr_radix_jit(y,scores,width),abs=1e-12)


def test_off_support_predictions_remain_in_global_denominator():
    m=module()
    assert m.klein_support_pr([0,1,0,0],[3.,3.,3.,3.],0)==pytest.approx(.25)
