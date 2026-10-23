"""Independent stdlib-only spike: integer-directed threshold PR certificates.

All certificate arithmetic is integer. Fractions are used only by the
independent tiny-instance oracle. This is not a production implementation.
"""
import itertools
import hashlib
import json
import math
import random
from fractions import Fraction
from pathlib import Path


def ceildiv(a, b):
    assert a >= 0 and b > 0
    return (a + b - 1) // b


def sqrt_bracket(w, d, b=32):
    assert w > 0 and 0 <= d <= w // 2
    D = 1 << b
    scaled = (w - d) << (2 * b)
    q = math.isqrt(scaled // w)
    upper = q if q * q * w == scaled else q + 1
    assert q * q * w <= scaled <= upper * upper * w
    return q, upper


def recall_bracket(a, blo, bhi, hit, components, positives, D, S):
    def ratio(bb):
        denominator = 2 * positives * D + bb
        numerator = min(2 * (a * D + bb), denominator)
        return S * hit * numerator, components * denominator
    ln, ld = ratio(blo)
    un, ud = ratio(bhi)
    return ln // ld, ceildiv(un, ud)


def block_bounds(a, b, D, S, positives, no_omission=False):
    """States: c,a,blo,bhi,h,k,rlo,rhi. Return integers divided by S."""
    if a['c'] == b['c']:
        return 0, 0
    drlo = max(0, b['rlo'] - a['rhi'])
    drhi = max(0, b['rhi'] - a['rlo'])
    if drhi == 0:
        return 0, 0
    tal, tah = a['a'] * D + a['blo'], a['a'] * D + a['bhi']
    tbl, tbh = b['a'] * D + b['blo'], b['a'] * D + b['bhi']
    if no_omission:
        return (drlo * tbl // (b['c'] * D),
                ceildiv(drhi * tbh, b['c'] * D))
    ln, ld = tal, b['c'] * D - tbl + tal
    un, ud = tbh, a['c'] * D - tah + tbh
    if ld == 0:
        ln, ld = 1, 1  # All predicted weights equal one.
    if ud == 0:
        un, ud = 0, 1  # No true-positive mass.
    assert 0 <= ln <= ld and 0 <= un <= ud
    lower = drlo * ln // ld
    upper = ceildiv(drhi * un, ud)
    # Stronger lower integral over [Ra_upper, Rb_lower], a subset of true
    # recall interval. Integrate max(ell, P0*r/Cb) using exact integer cases.
    left, right = a['rhi'], b['rlo']
    if right > left:
        constant_cross = ln * b['c'] * S
        denom_cross = ld * positives
        if constant_cross >= denom_cross * right:
            refined = (right - left) * ln // ld
        elif constant_cross <= denom_cross * left:
            refined = positives * (right * right - left * left) // (2 * b['c'] * S)
        else:
            CS = b['c'] * S
            numerator = (positives * right * ld) ** 2
            numerator -= 2 * ln * left * CS * ld * positives
            numerator += (ln * CS) ** 2
            denominator = 2 * CS * ld * ld * positives
            refined = numerator // denominator
        lower = max(lower, refined)
    return lower, upper


def labels_and_states(y, scores, width, weight_bits, output_bits, choice):
    D, S = 1 << weight_bits, 1 << output_bits
    n, positives = len(y), sum(y)
    ranges = []
    for i, value in enumerate(y):
        if value and (i == 0 or not y[i - 1]):
            ranges.append([i, i])
        elif value:
            ranges[-1][1] = i
    components = []
    for a, b in ranges:
        lo, hi = max(0, a - width // 2), min(n - 1, b + width // 2)
        if components and lo <= components[-1][1]:
            components[-1][1] = max(components[-1][1], hi)
        else:
            components.append([lo, hi])
    bounds, weights = [], []
    for i in range(n):
        ds = sorted(max(a - i, i - b, 0) for a, b in ranges)
        if y[i] or (len(ds) > 1 and ds[1] <= width // 2):
            lo = hi = D
        elif width >= 2 and ds[0] <= width // 2:
            lo, hi = sqrt_bracket(width, ds[0], weight_bits)
        else:
            lo = hi = 0
        bounds.append((lo, hi))
        # Exact rational values within the bracket; no numerical sqrt oracle.
        weights.append(Fraction(lo * (2 - choice) + hi * choice, 2 * D))
    k = len(components)
    states = [dict(c=0, a=0, blo=0, bhi=0, h=0, k=k, rlo=0, rhi=0)]
    exact = [(Fraction(0), Fraction(0))]
    for threshold in sorted(set(scores), reverse=True):
        pred = [s >= threshold for s in scores]
        aa = sum(v * p for v, p in zip(y, pred))
        blo = sum(lo for (lo, hi), yi, p in zip(bounds, y, pred) if p and not yi)
        bhi = sum(hi for (lo, hi), yi, p in zip(bounds, y, pred) if p and not yi)
        hit = sum(any(pred[a:b + 1]) for a, b in components)
        rlo, rhi = recall_bracket(aa, blo, bhi, hit, k, positives, D, S)
        c = sum(pred)
        states.append(dict(c=c, a=aa, blo=blo, bhi=bhi, h=hit, k=k, rlo=rlo, rhi=rhi))
        mass = sum((v for v, p in zip(weights, pred) if p), Fraction(0))
        buffer = sum((v for v, yi, p in zip(weights, y, pred) if p and not yi), Fraction(0))
        recall = min(mass / (positives + buffer / 2), Fraction(1)) * Fraction(hit, k)
        assert Fraction(rlo, S) <= recall <= Fraction(rhi, S)
        exact.append((recall, mass / c))
    target = sum((right[0] - left[0]) * right[1] for left, right in zip(exact, exact[1:]))
    return states, target


def verify():
    checks = 0
    rng = random.Random(20261023)
    fixtures = []
    for n in range(2, 5):
        for y in itertools.product((0, 1), repeat=n):
            if 0 < sum(y) < n:
                for scores in itertools.product((0, 1), repeat=n):
                    fixtures.append((y, scores))
    for _ in range(120):
        n = rng.randrange(2, 13)
        y = [rng.randrange(2) for _ in range(n)]
        y[0], y[-1] = 0, 1
        fixtures.append((y, [rng.randrange(-2, 3) for _ in range(n)]))
    for y, scores in fixtures:
        for width in (0, 2, 5, 16):
            for choice in (0, 1, 2):
                # Low precision deliberately stresses interval arithmetic.
                bits, outbits = 3, 12
                D, S = 1 << bits, 1 << outbits
                states, exact = labels_and_states(y, scores, width, bits, outbits, choice)
                for budget in (2, 3, 5):
                    counts = [1 + j * (len(y) - 1) // (budget - 1) for j in range(budget)]
                    indices = [0] + [next(i for i, s in enumerate(states) if s['c'] >= c) for c in counts]
                    lower = upper = 0
                    for ia, ib in zip(indices, indices[1:]):
                        lo, hi = block_bounds(states[ia], states[ib], D, S, sum(y), no_omission=ib <= ia + 1)
                        lower += lo
                        upper += hi
                    assert Fraction(lower, S) <= exact <= Fraction(upper, S), (y, scores, width, exact, lower, upper)
                    checks += 1
    for b in (0, 1, 3, 32, 63):
        for w in range(2, 101):
            for d in range(1, w // 2 + 1):
                sqrt_bracket(w, d, b)
    return {'status': 'PASS_EXACT_RATIONAL_ORACLE',
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'enclosure_checks': checks,
            'weight_bits_for_stress': 3, 'output_bits_for_stress': 12,
            'sqrt_integer_bracket_checks': 5 * sum(w // 2 for w in range(2, 101)),
            'certificate_uses_only_integer_arithmetic': True,
            'oracle': 'Exact Fraction evaluations of lower, midpoint and upper admissible weights',
            'scope': 'Independent arithmetic spike, not production certification or a timing claim'}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
