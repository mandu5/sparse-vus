"""Compiled comparisons. Both kernels preserve the same dynamic-label metric.

Numba warm-up is excluded from benchmark timings and reported separately.
The dense kernel scans every score position for every buffer width.
The sparse kernel scans only maximum-support positions and support-score events.
"""
from __future__ import annotations
import numpy as np
from numba import njit
from .core import _prepare, _validate_inputs, ranges, nearest_two_interval_distances


@njit(cache=True)
def _segments(starts, ends, n, w):
    lo, hi = np.empty(len(starts), np.int64), np.empty(len(starts), np.int64)
    a, k, radius = max(starts[0] - w // 2, 0), 0, w // 2
    for i in range(len(starts) - 1):
        if ends[i] + radius < starts[i + 1] - radius:
            lo[k], hi[k] = a, ends[i] + radius
            k += 1
            a = starts[i + 1] - radius
    lo[k], hi[k] = a, min(ends[-1] + radius, n - 1)
    return lo[:k + 1], hi[:k + 1]


@njit(cache=True)
def _weight(original, d1, d2, w):
    if original:
        return 1.0
    if d1 > w // 2 or w == 0:
        return 0.0
    if d2 <= w // 2:
        return 1.0
    return np.sqrt(1.0 - d1 / w)


@njit(cache=True)
def _dense_kernel(y, scores, starts, ends, d1, d2, order, max_buffer):
    n, p = len(y), float(np.sum(y))
    auc_total, ap_total = 0.0, 0.0
    for w in range(max_buffer + 1):
        lo, hi = _segments(starts, ends, n, w)
        segment = np.full(n, -1, np.int64)
        for j in range(len(lo)):
            for i in range(lo[j], hi[j] + 1):
                segment[i] = j
        seen = np.zeros(len(lo), np.bool_)
        hits = 0
        tp, buf, prev_fpr, prev_tpr, auc, ap = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        for rank in range(n):
            i = order[rank]
            weight = _weight(y[i], d1[i], d2[i], w)
            tp += weight
            if not y[i]:
                buf += weight
            sid = segment[i]
            if sid >= 0 and not seen[sid]:
                seen[sid] = True
                hits += 1
            if rank + 1 < n and scores[i] == scores[order[rank + 1]]:
                continue
            positive = p + buf / 2.0
            tpr = min(tp / positive, 1.0) * hits / len(lo)
            fpr = (rank + 1 - tp) / (n - positive)
            precision = tp / (rank + 1)
            auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2.0
            ap += (tpr - prev_tpr) * precision
            prev_fpr, prev_tpr = fpr, tpr
        auc += (1.0 - prev_fpr) * (1.0 + prev_tpr) / 2.0
        auc_total += auc
        ap_total += ap
    return auc_total / (max_buffer + 1), ap_total / (max_buffer + 1)


@njit(cache=True)
def _dense_direct_kernel(y, scores, starts, ends, order, max_buffer):
    """Direct independent sum-and-clip construction; no nearest-two lemma."""
    n, p = len(y), float(np.sum(y))
    auc_total, ap_total = 0.0, 0.0
    for w in range(max_buffer + 1):
        weights = y.astype(np.float64)
        for j in range(len(starts)):
            a, b = starts[j], ends[j]
            for i in range(max(0, a - w // 2), a):
                weights[i] += np.sqrt(1.0 - (a - i) / w)
            for i in range(b + 1, min(n, b + w // 2 + 1)):
                weights[i] += np.sqrt(1.0 - (i - b) / w)
        lo, hi = _segments(starts, ends, n, w)
        segment = np.full(n, -1, np.int64)
        for j in range(len(lo)):
            for i in range(lo[j], hi[j] + 1):
                segment[i] = j
        seen = np.zeros(len(lo), np.bool_)
        hits = 0
        tp, buf, prev_fpr, prev_tpr, auc, ap = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        for rank in range(n):
            i = order[rank]
            weight = min(weights[i], 1.0)
            tp += weight
            if not y[i]:
                buf += weight
            sid = segment[i]
            if sid >= 0 and not seen[sid]:
                seen[sid] = True
                hits += 1
            if rank + 1 < n and scores[i] == scores[order[rank + 1]]:
                continue
            positive = p + buf / 2.0
            tpr = min(tp / positive, 1.0) * hits / len(lo)
            fpr = (rank + 1 - tp) / (n - positive)
            auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2.0
            ap += (tpr - prev_tpr) * tp / (rank + 1)
            prev_fpr, prev_tpr = fpr, tpr
        auc += (1.0 - prev_fpr) * (1.0 + prev_tpr) / 2.0
        auc_total += auc
        ap_total += ap
    return auc_total / (max_buffer + 1), ap_total / (max_buffer + 1)


@njit(cache=True)
def _sparse_kernel(n, p, starts, ends, pos, original, d1, d2, group, before, after, max_buffer):
    groups = len(before)
    auc_total, ap_total = 0.0, 0.0
    for w in range(max_buffer + 1):
        lo, hi = _segments(starts, ends, n, w)
        tp_group, buf_group = np.zeros(groups), np.zeros(groups)
        first = np.full(len(lo), groups, np.int64)
        sid = 0
        for i in range(len(pos)):
            g = group[i]
            weight = _weight(original[i], d1[i], d2[i], w)
            tp_group[g] += weight
            if not original[i]:
                buf_group[g] += weight
            while sid < len(lo) and pos[i] > hi[sid]:
                sid += 1
            if sid < len(lo) and pos[i] >= lo[sid]:
                first[sid] = min(first[sid], g)
        hit_group = np.zeros(groups, np.int64)
        for j in range(len(first)):
            hit_group[first[j]] += 1
        tp, buf, hits = 0.0, 0.0, 0
        old_tp, old_tpr, old_negative, old_count = 0.0, 0.0, n - p, 0
        auc, ap = 0.0, 0.0
        for g in range(groups):
            tp += tp_group[g]
            buf += buf_group[g]
            hits += hit_group[g]
            positive = p + buf / 2.0
            negative = n - positive
            tpr = min(tp / positive, 1.0) * hits / len(lo)
            fpr = (after[g] - tp) / negative
            fpr_before = (before[g] - old_tp) / old_negative
            auc += (before[g] - old_count) * old_tpr / old_negative
            auc += (fpr - fpr_before) * (tpr + old_tpr) / 2.0
            ap += (tpr - old_tpr) * tp / after[g]
            old_tp, old_tpr, old_negative, old_count = tp, tpr, negative, after[g]
        terminal_fpr = (n - tp) / old_negative
        auc += (n - after[-1]) * old_tpr / old_negative
        auc += (1.0 - terminal_fpr) * (1.0 + old_tpr) / 2.0
        auc_total += auc
        ap_total += ap
    return auc_total / (max_buffer + 1), ap_total / (max_buffer + 1)


def sparse_vus_jit(y, scores, max_buffer):
    values = _prepare(y, scores, max_buffer)
    y, scores, starts, ends, pos, original, d1, d2, group, before, after, _ = values
    return _sparse_kernel(len(y), float(y.sum()), starts, ends, pos, original, d1, d2, group, before, after, max_buffer)


def dense_vus_jit(y, scores, max_buffer):
    # Independent dense preprocessing: every score is sorted; interval-distance
    # calculation runs on all n positions, with no sparse event histogram.
    y, scores = _validate_inputs(y, scores, max_buffer)
    starts, ends = ranges(y)
    d1, d2 = nearest_two_interval_distances(np.arange(len(y)), starts, ends)
    order = np.argsort(-scores)
    return _dense_kernel(y, scores, starts, ends, d1, d2, order, max_buffer)


def dense_vus_direct_jit(y, scores, max_buffer):
    """Dense comparison with independent direct ramp construction."""
    y, scores = _validate_inputs(y, scores, max_buffer)
    starts, ends = ranges(y)
    order = np.argsort(-scores)
    return _dense_direct_kernel(y, scores, starts, ends, order, max_buffer)
