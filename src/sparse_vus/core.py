"""Exact scalar VUS_opt evaluation; score thresholds are all distinct values.

Semantics target: thedatumorg/VUS commit 467bace, RangeAUC_volume_opt.
The reference's repeated tied thresholds do not change either integral.
This is independent prototype code, not a claimed new metric.
"""
from __future__ import annotations
import numpy as np


def ranges(y):
    padded = np.r_[False, np.asarray(y, dtype=bool), False]
    d = np.diff(padded.astype(np.int8))
    return np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1


def expanded_ranges(starts, ends, n, window):
    """Keep adjacent ranges separate, as official new_sequence does."""
    lo, hi = [], []
    a = max(int(starts[0]) - window // 2, 0)
    for i in range(len(starts) - 1):
        if ends[i] + window // 2 < starts[i + 1] - window // 2:
            lo.append(a)
            hi.append(int(ends[i]) + window // 2)
            a = int(starts[i + 1]) - window // 2
    lo.append(a)
    hi.append(min(int(ends[-1]) + window // 2, n - 1))
    return np.asarray(lo), np.asarray(hi)


def nearest_two_interval_distances(pos, starts, ends):
    """Two nearest *distinct intervals*. Distances within an interval are zero."""
    k = np.searchsorted(starts, pos, side="right")
    result = np.full((4, len(pos)), np.inf)
    for row, offset in enumerate((-2, -1, 0, 1)):
        j = k + offset
        valid = (j >= 0) & (j < len(starts))
        jj = np.clip(j, 0, len(starts) - 1)
        result[row, valid] = np.maximum(
            np.maximum(starts[jj[valid]] - pos[valid], pos[valid] - ends[jj[valid]]), 0
        )
    result.sort(axis=0)
    return result[0], result[1]


def _validate_inputs(y, scores, max_buffer):
    y = np.asarray(y)
    scores = np.asarray(scores, dtype=float)
    if y.ndim != 1 or scores.ndim != 1:
        raise ValueError("one-dimensional inputs required")
    n = len(y)
    if n != len(scores) or n < 2 or not np.isfinite(scores).all():
        raise ValueError("equal-length finite inputs with n >= 2 required")
    if not np.isin(y, [0, 1]).all() or not 0 < y.sum() < n:
        raise ValueError("binary labels with both classes required")
    if not isinstance(max_buffer, (int, np.integer)) or max_buffer < 0:
        raise ValueError("max_buffer must be a nonnegative integer")
    y = y.astype(np.int8)
    return y, scores


def _prepare(y, scores, max_buffer):
    y, scores = _validate_inputs(y, scores, max_buffer)
    n = len(y)
    starts, ends = ranges(y)
    lo, hi = expanded_ranges(starts, ends, n, max_buffer)
    pos = np.concatenate([np.arange(a, b + 1) for a, b in zip(lo, hi)])
    # The intervals are disjoint even when adjacent.
    original = y[pos].astype(bool)
    d1, d2 = nearest_two_interval_distances(pos, starts, ends)
    values, inverse = np.unique(scores[pos], return_inverse=True)
    # Histogram every score relative to Q support values. This does not sort n
    # scores: time O(n log(Q+1)), followed by O(Q) cumulative counts.
    insertion = np.searchsorted(values, scores, side="left")
    left_bins = np.bincount(insertion, minlength=len(values) + 1)
    safe_insertion = np.minimum(insertion, len(values) - 1)
    equal = scores == values[safe_insertion]
    equal_counts = np.bincount(insertion[equal], minlength=len(values))
    before_ascending = n - np.cumsum(left_bins)[:-1]
    before = before_ascending[::-1]
    after = (before_ascending + equal_counts)[::-1]
    group = len(values) - 1 - inverse
    support_index = np.full(n, -1, dtype=np.int64)
    support_index[pos] = np.arange(len(pos))
    return y, scores, starts, ends, pos, original, d1, d2, group, before, after, support_index


def sparse_vus(y, scores, max_buffer, return_per_buffer=False):
    prepared = _prepare(y, scores, max_buffer)
    y, scores, starts, ends, pos, original, d1, d2, group, before, after, support_index = prepared
    n, p, groups = len(y), float(np.sum(y)), len(before)
    aucs, aps = [], []
    for window in range(max_buffer + 1):
        weights = original.astype(float)
        if window >= 2:
            active = (~original) & (d1 <= window // 2)
            weights[active] = np.sqrt(1.0 - d1[active] / window)
            # Every nonzero ramp is >= sqrt(1/2); two overlapping ramps
            # saturate the official sum-and-clip rule at one.
            weights[(~original) & (d2 <= window // 2)] = 1.0
        lo, hi = expanded_ranges(starts, ends, n, window)
        sid = np.full(len(pos), -1, dtype=np.int64)
        for j, (a, b) in enumerate(zip(lo, hi)):
            sid[support_index[a]:support_index[b] + 1] = j
        inside = sid >= 0
        first = np.full(len(lo), groups, dtype=np.int64)
        np.minimum.at(first, sid[inside], group[inside])
        hits = np.cumsum(np.bincount(first, minlength=groups + 1)[:groups])
        tp = np.cumsum(np.bincount(group, weights=weights, minlength=groups))
        buffer_mass = np.cumsum(np.bincount(group, weights=weights * (~original), minlength=groups))
        positives = p + buffer_mass / 2.0
        negatives = n - positives
        tpr = np.minimum(tp / positives, 1.0) * hits / len(lo)
        fpr = (after - tp) / negatives
        precision = tp / after
        old_tp = np.r_[0.0, tp[:-1]]
        old_tpr = np.r_[0.0, tpr[:-1]]
        old_negative = np.r_[n - p, negatives[:-1]]
        old_count = np.r_[0, after[:-1]]
        fpr_before = (before - old_tp) / old_negative
        rectangles = (before - old_count) * old_tpr / old_negative
        trapezoids = (fpr - fpr_before) * (tpr + old_tpr) / 2.0
        terminal_fpr = (n - tp[-1]) / negatives[-1]
        terminal = (n - after[-1]) * tpr[-1] / negatives[-1]
        terminal += (1.0 - terminal_fpr) * (1.0 + tpr[-1]) / 2.0
        aucs.append(float(np.sum(rectangles + trapezoids) + terminal))
        aps.append(float(np.dot(tpr - old_tpr, precision)))
    result = (float(np.mean(aucs)), float(np.mean(aps)))
    if return_per_buffer:
        return result, np.asarray(aucs), np.asarray(aps), {"n": n, "support_points": len(pos), "support_scores": groups}
    return result


def dense_vus(y, scores, max_buffer, thresholds=None):
    """Independent dense rank sweep with official dynamic-label semantics.

    Shares interval helper only, and constructs the original sum-and-clip
    weights directly. O(n log n + n*max_buffer + K*max_buffer**2).
    """
    y, scores = _validate_inputs(y, scores, max_buffer)
    n, p = len(y), y.sum()
    starts, ends = ranges(y)
    order = np.argsort(-scores, kind="stable")
    if thresholds is None:
        group_last = np.r_[np.flatnonzero(np.diff(scores[order]) != 0), n - 1]
    else:
        chosen = scores[order][np.linspace(0, n - 1, thresholds).astype(int)]
        group_last = np.searchsorted(-scores[order], -chosen, side="right") - 1
    counts = group_last + 1
    rank = np.empty(n, dtype=np.int64)
    rank[order] = np.arange(n)
    aucs, aps = [], []
    for w in range(max_buffer + 1):
        weights = y.astype(float).copy()
        for a, b in zip(starts, ends):
            left = np.arange(max(0, a - w // 2), a)
            right = np.arange(b + 1, min(n, b + w // 2 + 1))
            if w:
                weights[left] += np.sqrt(1.0 - (a - left) / w)
                weights[right] += np.sqrt(1.0 - (right - b) / w)
        weights = np.minimum(weights, 1.0)
        lo, hi = expanded_ranges(starts, ends, n, w)
        hit_rank = [np.min(rank[a:b + 1]) for a, b in zip(lo, hi)]
        existence = np.cumsum(np.bincount(hit_rank, minlength=n))[group_last] / len(lo)
        tp = np.cumsum(weights[order])[group_last]
        buf = np.cumsum((weights * (1 - y))[order])[group_last]
        positive = p + buf / 2.0
        tpr = np.minimum(tp / positive, 1.0) * existence
        fpr = (counts - tp) / (n - positive)
        precision = tp / counts
        x, z = np.r_[0.0, fpr, 1.0], np.r_[0.0, tpr, 1.0]
        aucs.append(np.dot(np.diff(x), (z[1:] + z[:-1]) / 2))
        aps.append(np.dot(np.diff(np.r_[0.0, tpr]), precision))
    return float(np.mean(aucs)), float(np.mean(aps))


def sampled_vus(y, scores, max_buffer, thresholds=250):
    """Independent dense evaluation of the official sampled-threshold variant."""
    return dense_vus(y, scores, max_buffer, thresholds=thresholds)
