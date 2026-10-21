"""Dense PR-only controls with the same fixed-word radix ranking as sparse VUS.

Both public calls include validation, Float64 conversion, global radix ranking
and exhaustive width evaluation. Every input position is visited at every
width, including positions outside maximum buffer support. No support-event
compression, ROC calculation, width bounds or adaptive stopping is used.

The direct control reuses the independent sum-and-clip ramp kernel. The nearest
control uses the same linear two-interval geometry and weight formula as the
sparse radix evaluator, but retains an all-position threshold sweep. This
separates gains from generic radix/geometry improvements from event elimination.

Under the fixed-64-bit word model, nearest preparation takes O(n+K) time and
its full call takes O(n+(L+1)(n+K)) = O((L+1)n) time with O(n+K) auxiliary
memory. The direct ramp construction can add O(K*w) work at width w; its
unchanged existing direct kernel clips each ramp to the input bounds. Both kernels
reuse width scratch and stream the scalar width average.

Requires the optional ``accelerate`` dependency. Importing the base package
does not import this module automatically.
"""
from __future__ import annotations

import numpy as np
from numba import njit

from .compiled import _weight
from .core import _validate_inputs, ranges
from .pr_compiled import _dense_pr_direct_kernel, _expanded_segments
from .radix import _descending_keys, _nearest_two_linear, _radix_argsort

__all__ = ["dense_pr_direct_radix_jit", "dense_pr_nearest_radix_jit"]


@njit(cache=True)
def _dense_pr_nearest_radix_kernel(y, scores, starts, ends, d1, d2, order,
                                   max_buffer):
    """PR-only full-rank sweep, with scratch reused over all integer widths."""
    n, intervals = len(y), len(starts)
    positives = float(np.sum(y))
    segment_id = np.empty(n, dtype=np.int64)
    left = np.empty(intervals, dtype=np.int64)
    right = np.empty(intervals, dtype=np.int64)
    seen = np.zeros(intervals, dtype=np.bool_)
    total_pr = 0.0
    for width in range(max_buffer + 1):
        segments = _expanded_segments(starts, ends, n, width, left, right)
        segment_id.fill(-1)
        seen.fill(False)
        for segment in range(segments):
            for i in range(left[segment], right[segment] + 1):
                segment_id[i] = segment
        tp, buf, hits, previous_recall, pr = 0.0, 0.0, 0, 0.0, 0.0
        for rank in range(n):
            i = order[rank]
            weight = _weight(y[i], d1[i], d2[i], width)
            tp += weight
            if not y[i]:
                buf += weight
            segment = segment_id[i]
            if segment >= 0 and not seen[segment]:
                seen[segment] = True
                hits += 1
            # Thresholds admit complete numerical ties, including signed zero.
            if rank + 1 < n and scores[i] == scores[order[rank + 1]]:
                continue
            recall = min(tp / (positives + buf / 2.0), 1.0) * hits / segments
            pr += (recall - previous_recall) * tp / (rank + 1)
            previous_recall = recall
        total_pr += pr
    return total_pr / (max_buffer + 1)


def dense_pr_direct_radix_jit(y, scores, max_buffer) -> float:
    """Return full-threshold PR using radix ranks and direct sum-and-clip ramps."""
    y, scores = _validate_inputs(y, scores, max_buffer)
    starts, ends = ranges(y)
    order = _radix_argsort(_descending_keys(scores))
    return float(_dense_pr_direct_kernel(y, scores, starts, ends, order,
                                        max_buffer))


def dense_pr_nearest_radix_jit(y, scores, max_buffer) -> float:
    """Return full-threshold PR using radix ranks and all-position geometry."""
    y, scores = _validate_inputs(y, scores, max_buffer)
    starts, ends = ranges(y)
    order = _radix_argsort(_descending_keys(scores))
    d1, d2 = _nearest_two_linear(np.arange(len(y)), starts, ends)
    return float(_dense_pr_nearest_radix_kernel(y, scores, starts, ends, d1, d2,
                                               order, max_buffer))
