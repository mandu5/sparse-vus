"""Independent untimed arithmetic, layout, counter, and high-precision audit.

Run from the repository: python experiments/audit_tie_runs.py > receipt.json.
Assertions are required; no metric implementation is changed by this script.
"""
from pathlib import Path
import sys
import hashlib
from decimal import Decimal, localcontext
if not __debug__:
    raise RuntimeError("This audit requires assertions; do not use python -O")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import math
import json
import numpy as np
from sparse_vus.tie_runs import (_sqrt_prefix, _sqrt_range,
    interval_vus_tie_runs_jit, interval_pr_tie_runs_jit, profile_tie_runs)
from sparse_vus.compiled import dense_vus_direct_jit
from sparse_vus.core import dense_vus

rng = np.random.default_rng(2026102303)
mask = (1 << 64)-1
summary = {}

def table_pair(left, right):
    table = np.zeros((3, 3), dtype=np.uint64)
    for k in range(3):
        table[k, 1] = (left >> (64*k)) & mask
        table[k, 2] = (right >> (64*k)) & mask
    return table

# Prefix subtraction: constructed limb transitions, then arbitrary increasing
# 192-bit prefixes. Compare exact integer difference scaled by a power of two.
max_ulp = 0.
pairs = [(0, 0), (0, 1), ((1<<64)-1, 1<<64),
         ((1<<128)-1, 1<<128), ((1<<128)+(1<<64)-1, 2<<128),
         ((1<<128)+3, (2<<128)+1),
         ((1<<192)-2, (1<<192)-1),
         ((1<<128)-1, (1<<128)+(1<<64)),
         ((1<<64)+1, (3<<64))]
for _ in range(20000):
    a = int.from_bytes(rng.bytes(24), 'little')
    b = int.from_bytes(rng.bytes(24), 'little')
    pairs.append((min(a,b), max(a,b)))
for left, right in pairs:
    got = _sqrt_range(table_pair(left,right), 2, 2)
    expected = math.ldexp(float(right-left), -52)
    ulp = abs(got-expected)/math.ulp(expected)
    max_ulp = max(max_ulp, ulp)
    assert ulp <= 2, (left, right, got, expected, ulp)
summary['synthetic_subtractions'] = len(pairs)
summary['synthetic_max_ulp_from_single_rounding'] = max_ulp

# Real prefixes include many low-limb carries. Walk every table entry against
# Python integer oracle; test cancellation-sensitive singleton ranges at end.
limit = 150000
prefix = _sqrt_prefix(limit)
total = 0
low_carries = 0
for j in range(1, limit+1):
    num, den = math.sqrt(j).as_integer_ratio()
    total += (num << 52)//den
    got = sum(int(prefix[k,j]) << (64*k) for k in range(3))
    assert total == got, (j, total, got)
    low_carries += prefix[0,j] < prefix[0,j-1]
for j in range(limit-1000, limit+1):
    assert _sqrt_range(prefix,j,j) == math.sqrt(j), j
summary['real_prefix_entries'] = limit
summary['low_limb_carries'] = int(low_carries)
summary['high_prefix_limb_nonzero'] = bool(prefix[2,-1])

# The public score view contract includes negative strides, larger strides,
# read-only arrays, byte-swapped arrays converted by validator, and signed zero.
base_y = np.array([0,0,1,1,1,0,0,0,0,0,0], dtype=np.uint8)
base_s = np.array([0.,-0.,2.,-2.,1.,0.,2.,1.,-2.,3.,0.])
layouts = [(base_y,base_s), (base_y[::-1],base_s[::-1]),
  (np.repeat(base_y,3)[::3], np.repeat(base_s,3)[::3]),
  (base_y, base_s.astype('>f8'))]
readonly = base_s.copy(); readonly.flags.writeable=False
layouts.append((base_y,readonly))
for y,s in layouts:
    for L in (0,1,2,3,4,31,10000):
        got = interval_vus_tie_runs_jit(y,s,L)
        ref = dense_vus_direct_jit(y,s,L)
        assert np.max(np.abs(np.subtract(got,ref))) <= 1e-11, (y,s,L,got,ref)
summary['layout_width_cases'] = len(layouts)*7

# Independently compare public scalar values and reconstruct event/run counters
# at each width from positional masks, without candidate preparation helpers.
max_delta = 0.
max_counter_widths = 0
cases = 0
for case in range(650):
    n = int(rng.integers(2, 400))
    a = int(rng.integers(n))
    b = int(rng.integers(a, n))
    if a==0 and b==n-1:
        b -= 1
    y = np.zeros(n,dtype=np.uint8); y[a:b+1]=1
    mode = case % 5
    if mode == 0:
        scores = rng.integers(-3,4,n).astype(float)
    elif mode == 1:
        scores = rng.normal(size=n)
    elif mode == 2:
        scores = np.repeat(rng.integers(-5,6,(n+10)//11),11)[:n].astype(float)
    elif mode == 3:
        scores = np.full(n,-0.); scores[rng.random(n)<.5]=0.
    else:
        scores = np.resize(np.array([-np.finfo(float).max, np.finfo(float).max,
            np.nextafter(0.,1.), -np.nextafter(0.,1.), 1., -1., 0.]),n)
        rng.shuffle(scores)
    L = int(rng.integers(0, min(2*n+10,500)))
    got = interval_vus_tie_runs_jit(y,scores,L)
    ref = dense_vus_direct_jit(y,scores,L)
    delta = float(np.max(np.abs(np.subtract(got,ref))))
    max_delta=max(max_delta,delta)
    assert delta <= 1e-11, (case,n,a,b,L,got,ref)
    p=profile_tie_runs(y,scores,L)
    assert max(p['events']) <= 3*(b-a+1)
    assert interval_pr_tie_runs_jit(y,scores,L) == got[1]
    if case < 35:
        # Derive each width's threshold groups and positional counts without
        # the candidate's radix, activation schedule, or run buckets.
        lo,hi = max(0,a-L//2),min(n-1,b+L//2)
        support_scores = np.unique(scores[lo:hi+1])[::-1]
        for w in range(L+1):
            ac=bc=ev=qr=0
            current_low,current_high = max(0,a-w//2),min(n-1,b+w//2)
            for score in support_scores:
                mask_g = scores[lo:hi+1] == score
                active_positions = np.flatnonzero(scores[current_low:current_high+1] == score)+current_low
                if not len(active_positions):
                    continue
                ev += 1
                qr += int(np.sum(mask_g & ~np.r_[False,mask_g[:-1]]))
                ac += int(np.sum((active_positions >= a)&(active_positions <= b)))
                bc += int(np.sum((active_positions < a)|(active_positions > b)))
                if bc//3 >= b-a+1-ac:
                    break
            assert (ev,qr,ac+bc)==(p['events'][w],p['run_queries'][w],p['positions_aggregated'][w]), (case,w)
            max_counter_widths += 1
        np.testing.assert_allclose(got,dense_vus(y,scores,L),rtol=0,atol=1e-11)
    cases += 1
summary['randomized_metric_cases'] = cases
summary['independent_counter_widths'] = max_counter_widths
summary['max_dense_metric_absolute_difference'] = max_delta



def decimal_oracle(y, scores, limit):
    """All global thresholds and widths, direct Decimal-80 point weights."""
    with localcontext() as context:
        context.prec = 80
        D = Decimal
        n = len(y)
        positive_positions = [i for i in range(n) if y[i]]
        a, b = min(positive_positions), max(positive_positions)
        p0 = D(len(positive_positions))
        rocs, prs = [], []
        thresholds = sorted(set(float(s) for s in scores), reverse=True)
        for width in range(limit+1):
            weights = []
            for i in range(n):
                distance = max(a-i, i-b, 0)
                if y[i]:
                    weights.append(D(1))
                elif width >= 2 and distance <= width//2:
                    weights.append((D(width-distance)/D(width)).sqrt())
                else:
                    weights.append(D(0))
            old_f = old_r = roc = pr = D(0)
            for threshold in thresholds:
                selected = [i for i in range(n) if float(scores[i]) >= threshold]
                count = D(len(selected))
                original = D(sum(int(y[i]) for i in selected))
                mass = sum((weights[i] for i in selected if not y[i]), D(0))
                tp = original+mass
                positive = p0+mass/2
                recall = min(tp/positive, D(1)) if any(weights[i] > 0 for i in selected) else D(0)
                fpr = (count-tp)/(D(n)-positive)
                roc += (fpr-old_f)*(recall+old_r)/2
                pr += (recall-old_r)*tp/count
                old_f, old_r = fpr, recall
            roc += (D(1)-old_f)*(D(1)+old_r)/2
            rocs.append(roc)
            prs.append(pr)
        return sum(rocs)/D(limit+1), sum(prs)/D(limit+1)

high_precision_cases = 0
maximum_decimal_error = Decimal(0)
for n in (3, 7, 13, 29):
    for location in ('left', 'middle', 'right'):
        for score_kind in ('all_tied', 'fragmented', 'distinct'):
            y = np.zeros(n, dtype=np.uint8)
            point = 0 if location == 'left' else (n-1 if location == 'right' else n//2)
            y[point] = 1
            scores = np.zeros(n) if score_kind == 'all_tied' else (
                (np.arange(n)%3).astype(float) if score_kind == 'fragmented'
                else rng.permutation(n).astype(float))
            limit = n+3
            actual = interval_vus_tie_runs_jit(y, scores, limit)
            expected = decimal_oracle(y, scores, limit)
            for got, want in zip(actual, expected):
                error = abs(Decimal.from_float(got)-want)
                maximum_decimal_error = max(maximum_decimal_error, error)
                assert error < Decimal('1e-11'), (n, location, score_kind, error)
            high_precision_cases += 1
summary['decimal_precision'] = 80
summary['decimal_integral_cases'] = high_precision_cases
summary['max_decimal_integral_absolute_error'] = str(maximum_decimal_error)
summary['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in [Path(__file__), ROOT/'src/sparse_vus/tie_runs.py',
              ROOT/'src/sparse_vus/compiled.py', ROOT/'src/sparse_vus/core.py',
              ROOT/'src/sparse_vus/radix.py', ROOT/'src/sparse_vus/saturation.py']}
summary['status'] = 'PASS_RECORDED_CHECKS'
summary['scope'] = 'Independent implementation checks within one agent workflow; not external peer review or an all-input floating integral error certificate.'
print(json.dumps(summary, indent=2))
