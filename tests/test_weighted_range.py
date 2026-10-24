"""Independent finite-set/point-weight oracle for the generalized operator.

Breaks caught: wrong window-relative coordinates, missed middle split, stale
normalizers after off-label merges, cardinality confusion, and partial ties.
"""
from fractions import Fraction
import itertools

import numpy as np
import pytest


def oracle(labels, pred, alpha, pbias, rbias, cardinality, weighted_precision=False):
    def windows(values):
        out, current = [], set()
        for i, value in enumerate(values):
            if value:
                current.add(i)
            elif current:
                out.append(current)
                current = set()
        if current:
            out.append(current)
        return out

    def weight(offset, length, bias):
        if bias == 'flat': return 1
        if bias == 'front': return length-offset
        if bias == 'back': return offset+1
        return min(offset+1, length-offset)

    def average(base, other, bias, existence, weighted):
        if not base: return Fraction(0)
        total, denom = Fraction(0), 0
        for interval in base:
            length, start = len(interval), min(interval)
            multiplier = length if weighted else 1
            denom += multiplier
            overlaps = [interval & candidate for candidate in other if interval & candidate]
            if not overlaps: continue
            hit = set.union(*overlaps)
            omega = Fraction(sum(weight(i-start, length, bias) for i in hit),
                             sum(weight(i-start, length, bias) for i in interval))
            count = len(overlaps)
            if cardinality == 'one': gamma = Fraction(1)
            elif cardinality == 'reciprocal': gamma = Fraction(1, count)
            else: gamma = Fraction(length-1, length)**(count-1)
            total += multiplier*(existence+(1-existence)*gamma*omega)
        return total/denom

    true, predicted = windows(labels), windows(pred)
    p = average(predicted, true, pbias, Fraction(0), weighted_precision)
    r = average(true, predicted, rbias, Fraction(str(alpha)), False)
    f = 2*p*r/(p+r) if p+r else Fraction(0)
    return [float(p), float(r), float(f)]


@pytest.mark.parametrize('method', ['raster', 'sweep', 'bucket'])
def test_off_label_merge_changes_weighted_precision(method):
    from sparse_vus.weighted_range import weighted_range_metrics
    actual = weighted_range_metrics(method, [1,0,1], [3.,1.,2.], [1.,0.],
                                    precision_bias='middle', recall_bias='middle')
    np.testing.assert_allclose(actual, [[1,1,1],[.25,1,.4]], atol=2e-14, rtol=0)


@pytest.mark.parametrize('method', ['raster', 'sweep', 'bucket'])
@pytest.mark.parametrize('bias', ['flat','front','back','middle'])
@pytest.mark.parametrize('cardinality', ['reciprocal','one','improved'])
def test_all_short_tied_inputs_against_exact_rational_oracle(method, bias, cardinality):
    from sparse_vus.weighted_range import weighted_range_metrics
    thresholds = np.array([np.inf,0.,-np.inf,1.,-1.,0.])
    for n in range(1,4):
        for y in itertools.product([0,1], repeat=n):
            for x in itertools.product([-1.,0.,1.], repeat=n):
                scores = np.array(x)
                expected = [oracle(y,scores>t,.2,bias,bias,cardinality) for t in thresholds]
                actual = weighted_range_metrics(method,y,scores,thresholds,
                    precision_bias=bias,recall_bias=bias,cardinality=cardinality)
                np.testing.assert_allclose(actual,expected,atol=3e-13,rtol=0)


@pytest.mark.parametrize('method', ['raster', 'sweep', 'bucket'])
def test_mixed_biases_cardinalities_and_window_lengths(method):
    from sparse_vus.weighted_range import weighted_range_metrics
    rng=np.random.default_rng(202610240723)
    biases=['flat','front','back','middle']
    for _ in range(100):
        n=int(rng.integers(1,130));y=rng.integers(0,2,n);x=rng.integers(-5,6,n).astype(float)
        t=np.r_[rng.uniform(-7,7,7),np.inf,-np.inf]
        pb,rb=rng.choice(biases,2);card=str(rng.choice(['one','reciprocal','improved']))
        alpha=float(rng.choice([0,.2,1]));weighted=bool(rng.integers(2))
        expected=[oracle(y,x>v,alpha,pb,rb,card,weighted) for v in t]
        actual=weighted_range_metrics(method,y,x,t,alpha=alpha,precision_bias=pb,
            recall_bias=rb,cardinality=card,weighted_precision=weighted)
        np.testing.assert_allclose(actual,expected,atol=3e-12,rtol=0)


def test_window_coordinates_are_relative_after_large_zero_prefix():
    from sparse_vus.weighted_range import weighted_range_metrics
    y=np.r_[np.zeros(10000),[1,0,1,1,0,1]]
    x=np.r_[np.full(10000,-5.),[6.,1.,5.,3.,2.,4.]]
    t=np.array([4.,2.,0.])
    for bias in ['front','back','middle']:
        expected=[oracle(y,x>v,.2,bias,bias,'reciprocal') for v in t]
        np.testing.assert_allclose(weighted_range_metrics('sweep',y,x,t,
            precision_bias=bias,recall_bias=bias),expected,atol=2e-13,rtol=0)


@pytest.mark.parametrize('options', [{'cardinality':'unknown'}, {'precision_bias':'unknown'},
    {'recall_bias':'unknown'}, {'alpha':float('nan')}, {'alpha':-1}])
def test_invalid_semantic_options(options):
    from sparse_vus.weighted_range import weighted_range_metrics
    with pytest.raises(ValueError):
        weighted_range_metrics('sweep',[0,1],[0.,1.],[.5],**options)


@pytest.mark.parametrize('y,x,t', [([],[],[0]),([1,2],[0,1],[0]),
    ([0,1],[0,np.inf],[0]),([0,1],[0,1],[np.nan]),([0],[1+1j],[0]),
    ([0,1],[2**54,2**54+1],[0])])
def test_invalid_numeric_domain(y,x,t):
    from sparse_vus.weighted_range import weighted_range_metrics
    with pytest.raises(ValueError):weighted_range_metrics('sweep',y,x,t)


def test_middle_needs_two_sides_and_empty_queries_are_valid():
    from sparse_vus.weighted_range import weighted_range_metrics
    x=[1.,1.,1.,1.]
    a=weighted_range_metrics('sweep',[1,0,0,1],x,[0.],cardinality='one',precision_bias='middle')
    b=weighted_range_metrics('sweep',[0,1,1,0],x,[0.],cardinality='one',precision_bias='middle')
    # Four-position weights are [1,2,2,1], denominator 6.
    np.testing.assert_allclose([a[0,0],b[0,0]],[1/3,2/3],atol=1e-15,rtol=0)
    for method in ['raster','sweep','bucket']:
        assert weighted_range_metrics(method,[0,1],[0.,1.],[]).shape==(0,3)


def test_pinned_timesead_public_api_on_nonempty_label_contract():
    import importlib.util
    from pathlib import Path
    from sparse_vus.weighted_range import weighted_range_metrics
    torch=pytest.importorskip('torch')
    source=Path(__file__).resolve().parents[1]/'.cache/range-sweep-timesead/timesead/evaluation/ts_precision_recall.py'
    if not source.exists():pytest.skip('pinned external source not fetched')
    spec=importlib.util.spec_from_file_location('weighted_range_public_oracle',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    biases={'flat':module.constant_bias_fn,'front':module.front_bias_fn,
            'back':module.back_bias_fn,'middle':module.middle_bias_fn}
    cards={'one':lambda c,l:1.,'reciprocal':module.inverse_proportional_cardinality_fn,
           'improved':module.improved_cardinality_fn}
    rng=np.random.default_rng(202610240729)
    for pb,rb in itertools.product(biases,repeat=2):
        for card in cards:
            y=rng.integers(0,2,45);y[0]=1;x=rng.integers(-4,5,45).astype(float)
            t=np.array([np.inf,3.,1.,-2.,-np.inf])
            expected=[]
            for threshold in t:
                p,r=module.ts_precision_and_recall(torch.tensor(y,dtype=torch.float64),
                    torch.tensor(x>threshold,dtype=torch.float64),alpha=.2,
                    recall_bias_fn=biases[rb],precision_bias_fn=biases[pb],
                    recall_cardinality_fn=cards[card],precision_cardinality_fn=cards[card])
                expected.append([p,r,2*p*r/(p+r) if p+r else 0.])
            actual=weighted_range_metrics('sweep',y,x,t,alpha=.2,precision_bias=pb,
                recall_bias=rb,cardinality=card)
            np.testing.assert_allclose(actual,expected,atol=3e-13,rtol=0)


def test_improved_cardinality_does_not_amplify_near_one_base_rounding():
    from decimal import Decimal, localcontext
    from sparse_vus.weighted_range import _gamma
    with localcontext() as ctx:
        ctx.prec=80
        for length,count in [(1_000_000,500_000),(100_000_000,50_000_000),(1,1)]:
            expected=float((Decimal(length-1)/Decimal(length))**(count-1)) if count>1 else 1.
            assert abs(_gamma(count,length,2)-expected)<=2e-16
