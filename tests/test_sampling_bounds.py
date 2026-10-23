"""High-precision oracle and integer invariants for real-target certificates."""
from decimal import Decimal, localcontext
from fractions import Fraction
import itertools
import numpy as np
import pytest

pytest.importorskip("numba")
from sparse_vus.sampling_bounds import certified_sampled_pr, _sqrt_bracket, _outward


def decimal_vus(y, scores, max_buffer):
    # Independent direct ramp construction; no production interval helpers.
    with localcontext() as ctx:
        ctx.prec = 90
        n, p = len(y), sum(map(int, y))
        original = []
        for i, flag in enumerate(y):
            if flag:
                if i and y[i-1]:
                    original[-1][1] = i
                else:
                    original.append([i, i])
        total = Decimal(0)
        for w in range(max_buffer+1):
            weights = list(map(lambda v: Decimal(int(v)), y))
            components = []
            for a, b in original:
                lo, hi = max(0, a-w//2), min(n-1, b+w//2)
                for i in list(range(lo, a)) + list(range(b+1, hi+1)):
                    d = max(a-i, i-b)
                    weights[i] += (1-Decimal(d)/w).sqrt()
                if components and lo <= components[-1][1]:
                    components[-1][1] = max(hi, components[-1][1])
                else:
                    components.append([lo, hi])
            weights = [min(v, Decimal(1)) for v in weights]
            previous = Decimal(0)
            for threshold in sorted(set(map(float, scores)), reverse=True):
                pred = [bool(s >= threshold) for s in scores]
                tp = sum((v for v, keep in zip(weights, pred) if keep), Decimal(0))
                buf = sum((v for v, keep, flag in zip(weights, pred, y) if keep and not flag), Decimal(0))
                hit = sum(any(pred[a:b+1]) for a,b in components)
                recall = min(tp/(p+buf/2), Decimal(1))*hit/len(components)
                total += (recall-previous)*tp/sum(pred)
                previous = recall
        return total/(max_buffer+1)


@pytest.mark.parametrize("seed", range(35))
def test_contains_independent_decimal_oracle_without_epsilon(seed):
    rng = np.random.default_rng(seed+20261023)
    n = int(rng.integers(3, 35))
    y = rng.integers(0, 2, n)
    y[:2] = [1, 0]
    scores = rng.integers(-2, 4, n).astype(float)
    w = int(rng.integers(0, 30))
    expected = decimal_vus(y, scores, w)
    for budget in (2, 5, n+5):
        result = certified_sampled_pr(y, scores, w, budget)
        with localcontext() as ctx:
            ctx.prec = 100
            assert Decimal(result.lower_numerator)/result.scale <= expected
            assert expected <= Decimal(result.upper_numerator)/result.scale
        assert Fraction.from_float(result.lower) <= Fraction(result.lower_numerator, result.scale)
        assert Fraction.from_float(result.upper) >= Fraction(result.upper_numerator, result.scale)


def test_width_zero_exact_rational_and_full_grid_collapse():
    for labels in itertools.product((0, 1), repeat=4):
        if sum(labels) in (0, 4):
            continue
        for scores in itertools.product((0., 1.), repeat=4):
            p, pr, old = sum(labels), Fraction(0), Fraction(0)
            for t in sorted(set(scores), reverse=True):
                pred = [s >= t for s in scores]
                tp = sum(y for y, keep in zip(labels, pred) if keep)
                # At width zero each original component must be hit.
                components = []
                for i,v in enumerate(labels):
                    if v:
                        if i and labels[i-1]: components[-1].append(i)
                        else: components.append([i])
                hits = sum(any(pred[i] for i in c) for c in components)
                recall = Fraction(tp*hits, p*len(components))
                pr += (recall-old)*Fraction(tp, sum(pred))
                old = recall
            r = certified_sampled_pr(labels, scores, 0, 20)
            assert Fraction(r.lower_numerator, r.scale) <= pr <= Fraction(r.upper_numerator, r.scale)
            assert r.upper_numerator-r.lower_numerator <= 8


def test_sqrt_brackets_exact_integer_inequalities():
    for bits in (0, 1, 3, 32, 63):
        for w in range(2, 50):
            for d in range(w//2+1):
                lo, hi = _sqrt_bracket(w, d, bits)
                squared = (w-d) << (2*bits)
                assert lo*lo*w <= squared <= hi*hi*w
                assert 0 <= hi-lo <= 1
                assert hi <= 1 << bits


def test_outward_display_and_integer_decision():
    for value in (0, 1, 2**54-1, 2**55+1, 2**56-1, 2**56):
        lo = _outward(value, 1 << 56, False)
        hi = _outward(value, 1 << 56, True)
        assert Fraction.from_float(lo) <= Fraction(value, 1 << 56) <= Fraction.from_float(hi)
    good = certified_sampled_pr([0, 1, 0], [0, 2, 1], 0, 3)
    bad = certified_sampled_pr([0, 1, 0], [2, 0, 1], 0, 3)
    assert good.certifies_greater_than(bad)
    assert not bad.certifies_greater_than(good)


def test_all_score_tie_uses_exact_observed_block():
    y = [1, 0, 0, 1, 0]
    c = certified_sampled_pr(y, np.zeros(5), 31)
    assert c.thresholds_retained == 1
    assert c.upper-c.lower < 1e-8
    expected = decimal_vus(y, np.zeros(5), 31)
    assert Decimal(c.lower) <= expected <= Decimal(c.upper)


@pytest.mark.parametrize("integer_type", [np.int64, np.uint64])
def test_numpy_width_cannot_leak_fixed_width_arithmetic(integer_type):
    y, scores = [0, 1, 0], [0., 2., 1.]
    result = certified_sampled_pr(y, scores, integer_type(30))
    expected = certified_sampled_pr(y, scores, 30)
    assert result == expected
    assert type(result.lower_numerator) is int
    assert type(result.upper_numerator) is int
    assert type(result.scale) is int
    good = certified_sampled_pr(y, scores, integer_type(0), 3)
    bad = certified_sampled_pr(y, [2., 0., 1.], integer_type(0), 3)
    assert good.certifies_greater_than(bad)
