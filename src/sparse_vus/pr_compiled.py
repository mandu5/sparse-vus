"""Exhaustive PR-only compiled controls for the pinned VUS definition.

These return the discrete mean over every width from zero through
``max_buffer``. They compute no ROC coordinates or interval bounds, and do
not call the racing implementation. Like ``sparse_vus.compiled``, this module
requires the optional ``accelerate`` dependency; importing the base package
does not import it. Public calls include validation and preparation.
"""
from __future__ import annotations

import numpy as np
from numba import njit

from .core import _prepare, _validate_inputs, ranges

__all__ = ["sparse_pr_jit", "dense_pr_direct_jit"]


@njit(cache=True)
def _expanded_segments(starts, ends, n, width, left, right):
    """Write merged bounds into reusable arrays; adjacent ranges stay separate."""
    radius = width // 2
    first, count = max(0, starts[0] - radius), 0
    for j in range(len(starts) - 1):
        if ends[j] + radius < starts[j + 1] - radius:
            left[count], right[count] = first, ends[j] + radius
            count += 1
            first = starts[j + 1] - radius
    left[count], right[count] = first, min(n - 1, ends[-1] + radius)
    return count + 1


@njit(cache=True)
def _sparse_pr_complete(n, positives, starts, ends, pos, original, d1, d2,
                        group, after, values):
    """Fill only NaN width slots using prepared inputs; return new query count.

    The caller owns preparation and the validity of existing entries. Scratch
    storage is reused across all missing widths; no curves or bounds are built.
    """
    groups, intervals = len(after), len(starts)
    left = np.empty(intervals, dtype=np.int64)
    right = np.empty(intervals, dtype=np.int64)
    first_hit = np.empty(intervals, dtype=np.int64)
    true_mass = np.zeros(groups)
    buffer_mass = np.zeros(groups)
    new_hits = np.zeros(groups, dtype=np.int64)
    completed = 0
    for width in range(len(values)):
        if not np.isnan(values[width]):
            continue
        segments = _expanded_segments(starts, ends, n, width, left, right)
        true_mass.fill(0.0)
        buffer_mass.fill(0.0)
        new_hits.fill(0)
        first_hit.fill(groups)
        radius, segment = width // 2, 0
        for i in range(len(pos)):
            weight = 0.0
            if original[i]:
                weight = 1.0
            elif width >= 2 and d1[i] <= radius:
                weight = 1.0 if d2[i] <= radius else np.sqrt(1.0 - d1[i] / width)
            event = group[i]
            true_mass[event] += weight
            if not original[i]:
                buffer_mass[event] += weight
            while segment < segments and pos[i] > right[segment]:
                segment += 1
            if segment < segments and pos[i] >= left[segment]:
                first_hit[segment] = min(first_hit[segment], event)
        for segment in range(segments):
            new_hits[first_hit[segment]] += 1
        tp, buf, hits, previous_recall, pr = 0.0, 0.0, 0, 0.0, 0.0
        for event in range(groups):
            tp += true_mass[event]
            buf += buffer_mass[event]
            hits += new_hits[event]
            recall = min(tp / (positives + buf / 2.0), 1.0) * hits / segments
            pr += (recall - previous_recall) * tp / after[event]
            previous_recall = recall
        values[width] = pr
        completed += 1
    return completed


@njit(cache=True)
def _sparse_pr_kernel(n, positives, starts, ends, pos, original, d1, d2,
                      group, after, max_buffer):
    values = np.full(max_buffer + 1, np.nan)
    _sparse_pr_complete(n, positives, starts, ends, pos, original, d1, d2,
                        group, after, values)
    return np.sum(values) / len(values)


@njit(cache=True)
def _dense_pr_direct_kernel(y, scores, starts, ends, order, max_buffer):
    """Independent dense construction: explicitly add and clip each ramp."""
    n, intervals = len(y), len(starts)
    positives = float(np.sum(y))
    weights = np.empty(n)
    segment_id = np.empty(n, dtype=np.int64)
    left = np.empty(intervals, dtype=np.int64)
    right = np.empty(intervals, dtype=np.int64)
    seen = np.zeros(intervals, dtype=np.bool_)
    total_pr = 0.0
    for width in range(max_buffer + 1):
        for i in range(n):
            weights[i] = y[i]
        radius = width // 2
        for j in range(intervals):
            a, b = starts[j], ends[j]
            for i in range(max(0, a - radius), a):
                weights[i] += np.sqrt(1.0 - (a - i) / width)
            for i in range(b + 1, min(n, b + radius + 1)):
                weights[i] += np.sqrt(1.0 - (i - b) / width)
        segments = _expanded_segments(starts, ends, n, width, left, right)
        segment_id.fill(-1)
        seen.fill(False)
        for j in range(segments):
            for i in range(left[j], right[j] + 1):
                segment_id[i] = j
        tp, buf, hits, previous_recall, pr = 0.0, 0.0, 0, 0.0, 0.0
        for rank in range(n):
            i = order[rank]
            weight = min(weights[i], 1.0)
            tp += weight
            if not y[i]:
                buf += weight
            segment = segment_id[i]
            if segment >= 0 and not seen[segment]:
                seen[segment] = True
                hits += 1
            # A threshold admits the entire tied group at once.
            if rank + 1 < n and scores[i] == scores[order[rank + 1]]:
                continue
            recall = min(tp / (positives + buf / 2.0), 1.0) * hits / segments
            pr += (recall - previous_recall) * tp / (rank + 1)
            previous_recall = recall
        total_pr += pr
    return total_pr / (max_buffer + 1)


def sparse_pr_jit(y, scores, max_buffer) -> float:
    """Exact PR-only sparse evaluation, including validation and preparation.

    Scores use the same float64 conversion and tie semantics as ``sparse_vus``.
    The width loop and reusable scratch buffers stay inside one compiled call.
    """
    y, _, starts, ends, pos, original, d1, d2, group, _, after, _ = _prepare(
        y, scores, max_buffer)
    return float(_sparse_pr_kernel(len(y), float(y.sum()), starts, ends, pos,
                                  original, d1, d2, group, after, max_buffer))


def dense_pr_direct_jit(y, scores, max_buffer) -> float:
    """Exact PR-only dense direct-ramp control with its own score sorting.

    This path uses no sparse-support ranks, nearest-interval formula, endpoint
    bounds, or adaptive selection policy. It preserves sum-and-clip overlap.
    """
    y, scores = _validate_inputs(y, scores, max_buffer)
    starts, ends = ranges(y)
    order = np.argsort(-scores)
    return float(_dense_pr_direct_kernel(y, scores, starts, ends, order, max_buffer))
