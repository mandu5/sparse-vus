"""Independent set-overlap oracle; no candidate preprocessing in oracle."""
import itertools

import numpy as np
import pytest

from sparse_vus.range_sweep import range_metrics


def oracle(y, pred, alpha, compat):
    def components(v):
        if compat and np.all(v):
            return []
        out, current = [], set()
        for i, x in enumerate(v):
            if x:
                current.add(i)
            elif current:
                out.append(current)
                current = set()
        if current:
            out.append(current)
        return out
    true, predicted = components(y), components(pred)
    def recall(a, b, weight):
        if not a:
            return 0.
        result = 0.
        for interval in a:
            overlaps = [len(interval & other) for other in b if interval & other]
            if overlaps:
                result += weight + (1-weight)*sum(overlaps)/len(interval)/len(overlaps)
        return result/len(a)
    p, r = recall(predicted, true, 0), recall(true, predicted, alpha)
    # TSB existence uses raster labels even if the all-one parser returns [].
    if compat and not predicted and np.all(pred) and true:
        r = alpha
    return [p, r, 2*p*r/(p+r) if p+r else 0.]


@pytest.mark.parametrize('method', ['prefix', 'raster', 'sweep', 'bucket'])
def test_exhaustive_tied_short_series(method):
    for n in range(1, 5):
        for y in itertools.product((0, 1), repeat=n):
            for s in itertools.product((-1., 0., 1.), repeat=n):
                y, s = np.asarray(y), np.asarray(s)
                thresholds = np.array([np.inf, 1., 0., -1., -np.inf])
                expected = [oracle(y, s > t, .2, False) for t in thresholds]
                np.testing.assert_allclose(range_metrics(method, y, s, thresholds), expected, atol=2e-13, rtol=0)


@pytest.mark.parametrize('method', ['prefix', 'raster', 'sweep', 'bucket'])
def test_random_arbitrary_order_and_alpha(method):
    rng = np.random.default_rng(20261024)
    for _ in range(120):
        n = int(rng.integers(1, 100))
        y, s = rng.integers(0, 2, n), rng.integers(-6, 7, n).astype(float)
        t = np.r_[rng.uniform(-8, 8, 9), np.inf, -np.inf, 0., 0.]
        alpha = float(rng.choice([0., .2, 1.]))
        expected = [oracle(y, s > x, alpha, False) for x in t]
        np.testing.assert_allclose(range_metrics(method, y, s, t, alpha=alpha), expected, atol=2e-12, rtol=0)


@pytest.mark.parametrize('method', ['prefix', 'raster', 'sweep', 'bucket'])
def test_tsb_compat_all_one_corner(method):
    for y in ([1,1,1], [1,0,1], [0,0,0]):
        s, t = np.array([2., 1., 0.]), np.array([-np.inf, 0., 1., 2.])
        expected = [oracle(np.array(y), s > x, .2, True) for x in t]
        np.testing.assert_allclose(range_metrics(method, y, s, t, tsb_compat=True), expected, atol=2e-13, rtol=0)


@pytest.mark.parametrize('y,s,t', [([],[],[0]), ([0,2],[1.,2.],[0]), ([0,1],[np.nan,0.],[0]), ([0],[1.,2.],[0]), ([0,1],[0.,1.],[np.nan])])
def test_invalid_inputs(y,s,t):
    with pytest.raises(ValueError):
        range_metrics('sweep', y, s, t)
