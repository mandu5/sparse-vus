"""Statistical invariants: preserve paired orders and the geometric estimator."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest

path=Path(__file__).resolve().parents[1]/'experiments/audit_weighted_range_study.py'
spec=importlib.util.spec_from_file_location('weighted_audit_test',path)
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_paired_resampling_preserves_exact_ratio_despite_order_variation():
    # Independent method resampling would spuriously widen this interval.
    b=np.array([[[1,90,2,40,3,50]],[[40,3,60,4,70,1]]],dtype=float)
    np.testing.assert_allclose(audit.paired_order_interval(2*b,b,36,55,1000),[2,2],rtol=1e-14)


def test_geometric_case_and_semantic_weights_are_not_pooled_runtime_weights():
    b=np.array([[[1,90,2,40,3,50],[8,7,6,5,4,3]],
                [[40,3,60,4,70,1],[100,200,300,400,500,600]]],dtype=float)
    a=b*np.array([[2,8],[2,8]])[:,:,None]
    np.testing.assert_allclose(audit.paired_order_interval(a,b,3,123,1000),[4,4],rtol=1e-14)


def test_wrong_order_shape_is_rejected():
    with pytest.raises(AssertionError):
        audit.paired_order_interval(np.ones((2,1,5)),np.ones((2,1,5)),3,1,100)
