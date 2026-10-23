"""Integer-directed certificates for exhaustive, real-arithmetic VUS-PR.

The certified target uses exact square-root weights, not the bit pattern of a
particular floating-point evaluator. Score conversion/ties follow sampling.py.
Every weight and all subsequent arithmetic are enclosed with integer floor or
ceiling operations. No epsilon or libm sqrt accuracy assumption is used.

The fixed weight scale is 2**32 and n must be below 2**31, ensuring that every
compiled signed-int64 mass sum is below 2**63. Python integers implement the
nonlinear bounds and final accumulation without overflow. Requires Numba.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from numba import njit

from .pr_compiled import _expanded_segments
from .sampling import _prepare_sampled

__all__ = ["PRCertificate", "certified_sampled_pr"]
_WEIGHT_BITS = 32
_OUTPUT_BITS = 56


def _ceildiv(a: int, b: int) -> int:
    return (a+b-1)//b


def _sqrt_bracket(width: int, distance: int, bits: int = _WEIGHT_BITS):
    squared = (width-distance) << (2*bits)
    lower = math.isqrt(squared//width)
    upper = lower if lower*lower*width == squared else lower+1
    return lower, upper


def _outward(numerator: int, scale: int, upper: bool) -> float:
    value = numerator/scale
    p, q = value.as_integer_ratio()
    comparison = p*scale-numerator*q
    if (upper and comparison < 0) or (not upper and comparison > 0):
        value = float(np.nextafter(value, np.inf if upper else -np.inf))
    return value


@dataclass(frozen=True)
class PRCertificate:
    lower_numerator: int
    upper_numerator: int
    scale: int
    thresholds_retained: int
    weight_bits: int = _WEIGHT_BITS
    output_bits: int = _OUTPUT_BITS
    target: str = "exhaustive original dynamic VUS-PR in real arithmetic"

    def __post_init__(self):
        for name in ("lower_numerator", "upper_numerator", "scale",
                     "thresholds_retained", "weight_bits", "output_bits"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
                raise TypeError(f"{name} must be an integer")
            object.__setattr__(self, name, int(value))
        if not (self.scale > 0 and 0 <= self.lower_numerator <= self.upper_numerator <= self.scale):
            raise ValueError("invalid certificate endpoints or scale")

    @property
    def lower(self) -> float:
        return _outward(self.lower_numerator, self.scale, False)

    @property
    def upper(self) -> float:
        return _outward(self.upper_numerator, self.scale, True)

    def certifies_greater_than(self, other: PRCertificate) -> bool:
        """Strictly compare certified intervals using exact integers."""
        return self.lower_numerator*other.scale > other.upper_numerator*self.scale


@njit(cache=True)
def _integer_states(n, starts, ends, pos, original, d1, d2, bins, groups,
                    width, root_lo, root_hi, scale):
    left = np.empty(len(starts), dtype=np.int64)
    right = np.empty(len(starts), dtype=np.int64)
    segments = _expanded_segments(starts, ends, n, width, left, right)
    first = np.full(segments, groups, dtype=np.int64)
    aa = np.zeros(groups, dtype=np.int64)
    blo = np.zeros(groups, dtype=np.int64)
    bhi = np.zeros(groups, dtype=np.int64)
    hits = np.zeros(groups, dtype=np.int64)
    segment = 0
    for i in range(len(pos)):
        event = bins[i]
        if original[i]:
            aa[event] += 1
        elif width >= 2 and d1[i] <= width//2:
            if d2[i] <= width//2:
                blo[event] += scale
                bhi[event] += scale
            else:
                distance = int(d1[i])
                blo[event] += root_lo[distance]
                bhi[event] += root_hi[distance]
        while segment < segments and pos[i] > right[segment]:
            segment += 1
        if segment < segments and pos[i] >= left[segment]:
            first[segment] = min(first[segment], event)
    for segment in range(segments):
        hits[first[segment]] += 1
    for event in range(1, groups):
        aa[event] += aa[event-1]
        blo[event] += blo[event-1]
        bhi[event] += bhi[event-1]
        hits[event] += hits[event-1]
    return aa, blo, bhi, hits, segments


def _recall_bounds(a, blo, bhi, hits, components, positives, D, S):
    low_den, high_den = 2*positives*D+blo, 2*positives*D+bhi
    low_num = S*hits*min(2*(a*D+blo), low_den)
    high_num = S*hits*min(2*(a*D+bhi), high_den)
    return low_num//(components*low_den), _ceildiv(high_num, components*high_den)


def _block_bounds(previous, current, D, S, positives, no_omission):
    # State order: count, original_count, buffer_lo, buffer_hi, recall_lo, recall_hi.
    ca, aa, bal, bah, ral, rah = previous
    cb, ab, bbl, bbh, rbl, rbh = current
    if cb == ca:
        return 0, 0
    drlo, drhi = max(0, rbl-rah), max(0, rbh-ral)
    if drhi == 0:
        return 0, 0
    tal, tah = aa*D+bal, aa*D+bah
    tbl, tbh = ab*D+bbl, ab*D+bbh
    if no_omission:
        return drlo*tbl//(cb*D), _ceildiv(drhi*tbh, cb*D)
    # Both endpoint mass envelopes are increasing in each endpoint mass.
    ln, ld = tal, cb*D-tbl+tal
    un, ud = tbh, ca*D-tah+tbh
    if ld == 0:
        ln, ld = 1, 1
    if ud == 0:
        un, ud = 0, 1
    lower, upper = drlo*ln//ld, _ceildiv(drhi*un, ud)
    # Integrate max(ell, P0*r/Cb) only over [Ra_upper,Rb_lower], which
    # lies inside the actual recall interval. Everything below is exact.
    if rbl > rah:
        cross_num, cross_den = ln*cb*S, ld*positives
        if cross_num >= cross_den*rbl:
            refined = (rbl-rah)*ln//ld
        elif cross_num <= cross_den*rah:
            refined = positives*(rbl*rbl-rah*rah)//(2*cb*S)
        else:
            CS = cb*S
            numerator = (positives*rbl*ld)**2
            numerator -= 2*ln*rah*CS*ld*positives
            numerator += (ln*CS)**2
            refined = numerator//(2*CS*ld*ld*positives)
        lower = max(lower, refined)
    return lower, upper


def certified_sampled_pr(y, scores, max_buffer, thresholds=250) -> PRCertificate:
    """Enclose exhaustive real PR using uniformly sampled endpoint states.

    At all retained thresholds all positions with that score are included.
    Bounds can remain wide when omitted thresholds hide recall increments;
    requesting enough thresholds to retain every distinct score removes this
    ambiguity, leaving only the explicitly enclosed integer-grid error.
    All preparation and all integer widths are included in this call.
    """
    # Validate the overflow guard before any compiled fixed-point accumulation.
    if np.size(y) >= 1 << 31:
        raise ValueError("certification requires n < 2**31 for int64 mass sums")
    (y, _, starts, ends, pos, original, d1, d2, bins, counts, ordinals) = (
        _prepare_sampled(y, scores, max_buffer, thresholds))
    max_buffer = int(max_buffer)
    D, S, positives = 1 << _WEIGHT_BITS, 1 << _OUTPUT_BITS, int(y.sum())
    lower = upper = 0
    for width in range(max_buffer+1):
        radius = min(width//2, len(y)-1)
        root_lo = np.zeros(radius+1, dtype=np.int64)
        root_hi = np.zeros(radius+1, dtype=np.int64)
        root_lo[0] = root_hi[0] = D
        for distance in range(1, radius+1):
            root_lo[distance], root_hi[distance] = _sqrt_bracket(width, distance)
        aa, blo, bhi, hits, components = _integer_states(
            len(y), starts, ends, pos, original, d1, d2, bins, len(counts),
            width, root_lo, root_hi, D)
        previous = (0, 0, 0, 0, 0, 0)
        previous_ordinal = -1
        for i in range(len(counts)):
            a, bl, bh, hit = int(aa[i]), int(blo[i]), int(bhi[i]), int(hits[i])
            rl, rh = _recall_bounds(a, bl, bh, hit, components, positives, D, S)
            current = (int(counts[i]), a, bl, bh, rl, rh)
            no_omission = int(ordinals[i])-previous_ordinal == 1
            lo, hi = _block_bounds(previous, current, D, S, positives, no_omission)
            lower += lo
            upper += hi
            previous, previous_ordinal = current, int(ordinals[i])
    widths = max_buffer+1
    return PRCertificate(max(0, lower//widths), min(S, _ceildiv(upper, widths)),
                         S, len(counts))
