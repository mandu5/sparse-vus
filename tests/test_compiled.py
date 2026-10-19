"""Accelerated kernels must satisfy the same independently seeded cases."""
import numpy as np
import pytest
from sparse_vus import sparse_vus, sampled_vus
from sparse_vus.compiled import sparse_vus_jit, dense_vus_jit, dense_vus_direct_jit
from test_parity import case, reference


@pytest.mark.parametrize("index", range(1000))
def test_compiled_parity(index, reference):
    y, s, width = case(index)
    expected = reference.RangeAUC_volume_opt(y, s, width, thre=len(y))[-2:]
    np.testing.assert_allclose(sparse_vus_jit(y, s, width), expected, atol=1e-11, rtol=0)
    np.testing.assert_allclose(dense_vus_jit(y, s, width), expected, atol=1e-11, rtol=0)
    np.testing.assert_allclose(dense_vus_direct_jit(y, s, width), expected, atol=1e-11, rtol=0)


@pytest.mark.parametrize("index", range(50))
def test_sampled_thresholds(index, reference):
    y, s, width = case(index)
    expected = reference.RangeAUC_volume_opt(y, s, width, thre=250)[-2:]
    np.testing.assert_allclose(sampled_vus(y, s, width), expected, atol=1e-11, rtol=0)
