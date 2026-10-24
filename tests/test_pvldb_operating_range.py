import importlib.util
from pathlib import Path
import numpy as np
import pytest


def module():
    path=Path(__file__).resolve().parents[1]/"experiments/pvldb_operating_range.py"
    spec=importlib.util.spec_from_file_location("operating_range",path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


@pytest.mark.parametrize("n,k,p",[(1000,1,.9),(1000,10,.1),(100000,1000,.01)])
def test_controlled_labels_keep_exact_density_and_component_count(n,k,p):
    y,s=module().controlled(n,2,p,k,None)
    assert len(y)==n and y.sum()==int(n*p)
    assert np.count_nonzero(np.diff(np.r_[0,y,0])==1)==k
    assert s.shape==(2,n) and np.isfinite(s).all()


def test_synthetic_ties_are_explicit_and_design_has_no_duplicate_cases():
    m=module();y,s=m.controlled(1000,8,.01,1,16)
    assert len(np.unique(s))==16
    assert len(m.controlled_cases())==len({tuple(sorted(c.items())) for c in m.controlled_cases()})
    assert max(c['n'] for c in m.controlled_cases())==1000000


def test_invalid_density_component_contract_is_rejected():
    with pytest.raises(ValueError):module().controlled(100,2,.01,20,None)
