"""Independent production certificate audit; no mutation of metric sources."""
import hashlib
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import random
import sys
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import sampling_bigint_certificate_20261023 as oracle
from sparse_vus import sampling_bounds as production
from sparse_vus.sampling import _prepare_sampled


def decimal_truth(y, scores, limit):
    with localcontext() as ctx:
        ctx.prec = 120
        n, positives = len(y), sum(map(int, y))
        intervals = []
        for i, v in enumerate(y):
            if v and (not i or not y[i-1]):
                intervals.append([i, i])
            elif v:
                intervals[-1][1] = i
        total = Decimal(0)
        for w in range(limit+1):
            weights = [Decimal(int(v)) for v in y]
            components = []
            for start, end in intervals:
                left, right = max(0, start-w//2), min(n-1, end+w//2)
                for j in range(left, right+1):
                    if not start <= j <= end:
                        distance = max(start-j, j-end)
                        weights[j] += (Decimal(1)-Decimal(distance)/Decimal(w)).sqrt()
                if components and left <= components[-1][1]:
                    components[-1][1] = max(components[-1][1], right)
                else:
                    components.append([left, right])
            weights = [min(v, Decimal(1)) for v in weights]
            prior = Decimal(0)
            for threshold in sorted(set(map(float, scores)), reverse=True):
                active = [float(s) >= threshold for s in scores]
                mass = sum((v for v, a in zip(weights, active) if a), Decimal(0))
                buffer = sum((v for v, a, yi in zip(weights, active, y) if a and not yi), Decimal(0))
                hit = sum(any(active[a:b+1]) for a,b in components)
                recall = min(mass/(Decimal(positives)+buffer/2), Decimal(1))
                recall *= Decimal(hit)/Decimal(len(components))
                total += (recall-prior)*mass/Decimal(sum(active))
                prior = recall
        return total/Decimal(limit+1)


def state_tuple(s):
    return s['c'],s['a'],s['blo'],s['bhi'],s['rlo'],s['rhi']


def check():
    paths = ['src/sparse_vus/sampling.py','src/sparse_vus/sampling_bounds.py',
             'src/sparse_vus/core.py','src/sparse_vus/radix.py',
             'src/sparse_vus/pr_compiled.py',
             'experiments/exploration/sampling_bigint_certificate_20261023.py',
             'experiments/exploration/audit_sampling_certificate_20261023.py']
    before = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    old = oracle.block_bounds
    oracle.block_bounds = lambda a,b,D,S,p,no_omission=False: production._block_bounds(
        state_tuple(a),state_tuple(b),D,S,p,no_omission)
    try:
        exact = oracle.verify()
    finally:
        oracle.block_bounds = old
    rng = np.random.default_rng(2026102307)
    decimal_checks = state_checks = ordinal_checks = 0
    for case in range(120):
        n = int(rng.integers(2,25))
        y = rng.integers(0,2,n);y[0],y[-1]=0,1
        scores = rng.integers(-4,5,n).astype(float)
        if case%7 == 0:
            scores = rng.normal(size=n)
        if case%11 == 0:
            scores[:2] = [-0.,0.]
        limit = int(rng.integers(0,42))
        truth = decimal_truth(y,scores,limit)
        for budget in (2,5,n+5):
            cert = production.certified_sampled_pr(y,scores,limit,budget)
            with localcontext() as ctx:
                ctx.prec=130
                assert Decimal(cert.lower_numerator)/Decimal(cert.scale) <= truth
                assert truth <= Decimal(cert.upper_numerator)/Decimal(cert.scale)
            decimal_checks += 1
            prepared = _prepare_sampled(y,scores,limit,budget)
            yy,_,starts,ends,pos,original,d1,d2,bins,counts,ordinals=prepared
            unique = sorted(set(scores),reverse=True)
            sorted_scores = np.sort(scores)[::-1]
            requested=sorted_scores[np.linspace(0,n-1,budget).astype(int)]
            retained=sorted(set(requested),reverse=True)
            assert list(counts)==[sum(scores>=s) for s in retained]
            assert list(ordinals)==[unique.index(s) for s in retained]
            ordinal_checks+=1
            for width in sorted(set((0,limit//2,limit))):
                states,_=oracle.labels_and_states(list(map(int,y)),list(map(float,scores)),width,32,56,1)
                roots=[production._sqrt_bracket(width,d) if d else (2**32,2**32)
                       for d in range(min(width//2,n-1)+1)]
                rl=np.array([r[0] for r in roots],dtype=np.int64)
                rh=np.array([r[1] for r in roots],dtype=np.int64)
                aa,bl,bh,hits,k=production._integer_states(n,starts,ends,pos,original,d1,d2,bins,len(counts),width,rl,rh,2**32)
                for i,c in enumerate(counts):
                    reference=next(s for s in states if s['c']==c)
                    assert (int(aa[i]),int(bl[i]),int(bh[i]),int(hits[i]),int(k)) == (
                        reference['a'],reference['blo'],reference['bhi'],reference['h'],reference['k'])
                    state_checks+=1
    scalar_checks=0
    for scalar in (int,np.int32,np.int64,np.uint32,np.uint64):
        for width in (0,30):
            one=production.certified_sampled_pr([0,1,0],[0,2,1],scalar(width),3)
            two=production.certified_sampled_pr([0,1,0],[2,0,1],scalar(width),3)
            for cert in (one,two):
                assert type(cert.lower_numerator) is int and type(cert.upper_numerator) is int
            if width==0:
                assert one.certifies_greater_than(two)
                assert not two.certifies_greater_than(one)
            scalar_checks+=1
    with patch.object(production.np,'size',return_value=2**31):
        try:
            production.certified_sampled_pr([0,1],[0,1],0)
        except ValueError as e:
            assert 'int64' in str(e)
        else:
            raise AssertionError('Missing overflow guard')
    py_rng=random.Random(20261023)
    display_checks=0
    for bits in (1,8,56,128,4096):
        scale=1<<bits
        for _ in range(1000):
            numerator=py_rng.randrange(scale+1)
            f=Fraction(numerator,scale)
            assert Fraction.from_float(production._outward(numerator,scale,False)) <= f
            assert f <= Fraction.from_float(production._outward(numerator,scale,True))
            display_checks+=1
    after = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    assert before==after,'Sources changed during audit'
    return {'status':'PASS_INDEPENDENT_PRODUCTION_AUDIT','source_sha256':after,
            'exact_fraction_block_enclosures':exact['enclosure_checks'],
            'decimal120_full_api_checks':decimal_checks,
            'independent_integer_endpoint_states':state_checks,
            'global_tie_ordinal_checks':ordinal_checks,
            'numpy_scalar_regression_cases':scalar_checks,
            'outward_float_display_checks':display_checks,
            'overflow_guard_checked':True,
            'target':'Ideal real-arithmetic original dynamic VUS-PR; decimal checks supplementary to integer proof'}


if __name__=='__main__':
    print(json.dumps(check(),indent=2))
