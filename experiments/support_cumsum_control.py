"""Author-created compiled attribution control, not an upstream release.

Use the candidate's validation and fixed-word global tie ranking, but construct
each width by direct sum-and-clip ramps and per-component support maxima, as in
the support-cumsum approach of Klein. No nearest-interval geometry or sharing.
This is an optimized reimplementation, not a literal JIT of upstream NumPy.
Support-local scratch avoids artificial whole-series clears at each width.
"""
import numpy as np
from numba import njit
from sparse_vus.core import _validate_inputs, ranges, expanded_ranges
from sparse_vus.radix import _descending_keys, _radix_argsort, _support_ranks
from sparse_vus.pr_compiled import _expanded_segments


@njit(cache=True)
def _direct_support_kernel(y, starts, ends, pos, index, group, after, width_max):
    q, g, k = len(pos), len(after), len(starts)
    p = float(np.sum(y))
    soft = np.empty(q)
    original_mass = np.zeros(g)
    for i in range(q):
        original_mass[group[i]] += y[pos[i]]
    left, right = np.empty(k, np.int64), np.empty(k, np.int64)
    buffer_mass = np.empty(g)
    new_hits = np.empty(g, np.int64)
    total = 0.
    for width in range(width_max + 1):
        soft.fill(0.)
        buffer_mass.fill(0.)
        new_hits.fill(0)
        radius = width // 2
        for j in range(k):
            a, b = starts[j], ends[j]
            for t in range(max(0, a - radius), a):
                soft[index[t]] += np.sqrt(1. - (a - t) / width)
            for t in range(b + 1, min(len(y), b + radius + 1)):
                soft[index[t]] += np.sqrt(1. - (t - b) / width)
        for i in range(q):
            if not y[pos[i]]:
                buffer_mass[group[i]] += min(soft[i], 1.)
        count = _expanded_segments(starts, ends, len(y), width, left, right)
        for j in range(count):
            first = g
            for t in range(left[j], right[j] + 1):
                first = min(first, group[index[t]])
            new_hits[first] += 1
        b_mass, a_mass, hits, prev, ap = 0., 0., 0, 0., 0.
        for event in range(g):
            b_mass += original_mass[event]
            a_mass += buffer_mass[event]
            hits += new_hits[event]
            tp = b_mass + a_mass
            recall = min(tp / (p + a_mass / 2.), 1.) * hits / count
            ap += (recall - prev) * tp / after[event]
            prev = recall
        total += ap
    return total / (width_max + 1)


def support_cumsum_pr(labels, scores, max_buffer):
    y, x = _validate_inputs(labels, scores, max_buffer)
    starts, ends = ranges(y)
    lo, hi = expanded_ranges(starts, ends, len(y), max_buffer)
    pos = np.concatenate([np.arange(a, b + 1) for a, b in zip(lo, hi)])
    index = np.full(len(y), -1, dtype=np.int64)
    index[pos] = np.arange(len(pos))
    keys = _descending_keys(x)
    order = _radix_argsort(keys)
    group, _, after = _support_ranks(keys, order, index, len(pos))
    return float(_direct_support_kernel(y, starts, ends, pos, index, group, after, max_buffer))
