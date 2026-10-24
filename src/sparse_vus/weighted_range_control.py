"""Compiled conventional interval control for weighted Tatbul range metrics.

This implements the ordered interval/closed-form strategy described by Tatbul
et al. (2018), Section 5.5. Fixed-label intervals and prefix moments are prepared
once per call. Every threshold scans all scores to rebuild predicted intervals;
precision uses fixed-label prefixes, and recall uses ordered interval overlaps.
No metric state is updated or reused across thresholds. Reusable scratch storage
does not avoid threshold-mask discovery, which is included in the public call.

The semantic/numeric domain matches weighted_range.weighted_range_metrics.
Shared private helpers implement the same normalizers, cardinality factors and
precision closed forms; tests use a separate finite-set Fraction oracle.
"""
import numpy as np
from numba import njit

from .range_sweep import _prepare
from .weighted_range import _BIASES, _CARDINALITIES, _component, _gamma, _normalizer


@njit(cache=True)
def _interval_weight_sum(a, b, lo, hi, bias):
    """Integer positional mass on nonempty [lo,hi] within scored [a,b]."""
    count = hi - lo + 1
    if bias == 0:
        return count
    if bias == 1:
        return ((b - lo + 1) + (b - hi + 1)) * count // 2
    if bias == 2:
        return ((lo - a + 1) + (hi - a + 1)) * count // 2
    mid = (a + b) // 2
    mass = 0
    if lo <= mid:
        end = min(hi, mid)
        mass += ((lo - a + 1) + (end - a + 1)) * (end - lo + 1) // 2
    if hi > mid:
        start = max(lo, mid + 1)
        mass += ((b - start + 1) + (b - hi + 1)) * (hi - start + 1) // 2
    return mass


@njit(cache=True)
def _interval_control(x, t, ids, starts, ends, pref, moments, spref,
                      alpha, pbias, rbias, cardinality, weighted):
    n, k = len(x), len(starts)
    out = np.zeros((len(t), 3))
    if not k:
        return out
    # At most ceil(n/2) disjoint nonempty predicted intervals. These buffers
    # hold only the current query; no prior-query endpoints or aggregates count.
    pred_starts = np.empty((n + 1) // 2, np.int64)
    pred_ends = np.empty((n + 1) // 2, np.int64)
    true_normalizers = np.empty(k, np.int64)
    for j in range(k):
        true_normalizers[j] = _normalizer(ends[j] - starts[j] + 1, rbias)

    for q in range(len(t)):
        pc, ps, denominator, i = 0, 0., 0, 0
        while i < n:
            if x[i] <= t[q]:
                i += 1
                continue
            a = i
            while i < n and x[i] > t[q]:
                i += 1
            b = i - 1
            pred_starts[pc], pred_ends[pc] = a, b
            pc += 1
            ps += _component(a, b, pref, moments, spref, ids,
                             pbias, cardinality, weighted)
            denominator += b - a + 1 if weighted else 1
        if not pc:
            continue

        rs, cursor = 0., 0
        for j in range(k):
            a, b = starts[j], ends[j]
            while cursor < pc and pred_ends[cursor] < a:
                cursor += 1
            current, mass, count = cursor, 0, 0
            while current < pc and pred_starts[current] <= b:
                lo = max(a, pred_starts[current])
                hi = min(b, pred_ends[current])
                mass += _interval_weight_sum(a, b, lo, hi, rbias)
                count += 1
                # A predicted interval spanning later true intervals must remain
                # the candidate there. Every other prediction advances once.
                if pred_ends[current] > b:
                    break
                current += 1
            cursor = current
            if count:
                rs += (alpha + (1 - alpha) * mass / true_normalizers[j]
                       * _gamma(count, b - a + 1, cardinality))
        precision, recall = ps / denominator, rs / k
        out[q, 0], out[q, 1] = precision, recall
        out[q, 2] = (2 * precision * recall / (precision + recall)
                     if precision + recall else 0.)
    return out


def weighted_range_interval_control(labels, scores, thresholds, *, alpha=.2,
                                    precision_bias='flat', recall_bias='flat',
                                    cardinality='reciprocal', weighted_precision=False):
    """Return H-by-3 precision/recall/F1 using independent interval evaluation.

    Predictions use binary64 ``score > threshold``, with complete ties, arbitrary
    query order, and zero empty-base averages. Supports four canonical biases,
    three cardinalities, and macro or all-window length-weighted precision.
    Preparation and every threshold's prediction discovery are included in this
    call: O(n + H*n) time and O(n + H) space, without score/query sorting.
    """
    if precision_bias not in _BIASES or recall_bias not in _BIASES:
        raise ValueError('unknown positional bias')
    if cardinality not in _CARDINALITIES:
        raise ValueError('unknown cardinality')
    if not isinstance(weighted_precision, (bool, np.bool_)):
        raise ValueError('weighted_precision must be boolean')
    try:
        y, x, t = np.asarray(labels), np.asarray(scores), np.asarray(thresholds)
        if (y.ndim != 1 or x.ndim != 1 or t.ndim != 1
                or not len(y) or len(y) != len(x)):
            raise ValueError('aligned nonempty vectors required')
        if len(y) > 2**31 - 1:
            raise ValueError('integer-moment domain exceeded')
        if y.dtype.kind not in 'biuf' or x.dtype.kind not in 'biuf' or t.dtype.kind not in 'biuf':
            raise ValueError('real numeric arrays required')
        if not np.all((y == 0) | (y == 1)):
            raise ValueError('binary labels required')
        for value in (x, t):
            if value.dtype.kind in 'iu' and (np.any(value > 2**53) or np.any(value < -(2**53))):
                raise ValueError('integer score/threshold cannot be silently rounded')
        y, x, t = y.astype(np.int8), x.astype(np.float64), t.astype(np.float64)
        alpha = float(alpha)
        if not np.isfinite(x).all() or np.isnan(t).any():
            raise ValueError('finite scores and non-NaN queries required')
        if not np.isfinite(alpha) or not 0 <= alpha <= 1:
            raise ValueError('alpha must lie in [0,1]')
    except (TypeError, OverflowError) as exc:
        raise ValueError('invalid numeric domain') from exc

    y, x, t, ids, starts, ends, pref, spref = _prepare(y, x, t)
    moments = np.r_[0, np.cumsum(np.arange(len(y), dtype=np.int64) * y, dtype=np.int64)]
    return _interval_control(
        x, t, ids, starts, ends, pref, moments, spref, alpha,
        _BIASES[precision_bias], _BIASES[recall_bias],
        _CARDINALITIES[cardinality], weighted_precision)
