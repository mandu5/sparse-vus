import importlib.util
from pathlib import Path
import numpy as np
import pytest


def module():
    path=Path(__file__).resolve().parents[1]/"experiments/pvldb_resources.py"
    spec=importlib.util.spec_from_file_location("resources_study",path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_resource_stress_inputs_have_declared_support_and_deterministic_scores():
    m=module(); y,s=m.stress(1000,8,.01); y2,s2=m.stress(1000,8,.01)
    assert y.sum()==10 and s.shape==(8,1000) and s.dtype==np.float64
    np.testing.assert_array_equal(y,y2);np.testing.assert_array_equal(s,s2)
    assert np.isfinite(s).all()


def test_os_peak_rss_units_are_explicit():
    m=module()
    assert m.rss_bytes(1024,"Darwin")==1024
    assert m.rss_bytes(1024,"Linux")==1048576
    with pytest.raises(ValueError):m.rss_bytes(1,"unknown")
