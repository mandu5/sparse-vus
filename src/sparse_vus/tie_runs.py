"""Run-sensitive exhaustive VUS for one original anomaly interval.

Complete score classes are activated in score order and represented by temporal
runs. Ramp sums use exact integer differences of fixed-point prefixes of rounded
square roots. This avoids cancellation of floating prefix sums. Termination
uses an integer sufficient certificate, never a rounded mass comparison.

Ideal-arithmetic work: O(n+L+sum of visited score-class run counts), with
O(n+L) auxiliary words under the fixed-binary64/unit-cost model. At most 3*P0
active score events are visited per width. Runs outside the current width still
count as inspected runs. This API explicitly rejects multiple original intervals.
Numerical values are floating approximations of the exhaustive target, not
symbolic values or a certificate of the final integral's rounding error.
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit

from .core import _validate_inputs, ranges
from .radix import _descending_keys, _radix_argsort, _support_ranks
from .saturation import _activation_schedule

__all__ = ["interval_vus_tie_runs_jit", "interval_pr_tie_runs_jit", "profile_tie_runs"]


@njit(cache=True)
def _sqrt_prefix(limit):
    """Exact prefixes of rounded sqrt(j)*2**52 in three unsigned limbs."""
    table = np.zeros((3, limit + 1), dtype=np.uint64)
    low, middle, high = np.uint64(0), np.uint64(0), np.uint64(0)
    mask = (np.uint64(1) << np.uint64(52)) - np.uint64(1)
    for j in range(1, limit + 1):
        bits = np.float64(np.sqrt(float(j))).view(np.uint64)
        exponent = (bits >> np.uint64(52)) - np.uint64(1023)
        mantissa = (bits & mask) | (np.uint64(1) << np.uint64(52))
        add_low = mantissa << exponent
        add_middle = np.uint64(0)
        if exponent > 0:
            add_middle = mantissa >> (np.uint64(64) - exponent)
        new_low = low + add_low
        carry = np.uint64(new_low < low)
        new_middle = middle + add_middle
        high += np.uint64(new_middle < middle)
        middle = new_middle + carry
        high += np.uint64(middle < new_middle)
        low = new_low
        table[0, j], table[1, j], table[2, j] = low, middle, high
    return table


@njit(cache=True, inline="always")
def _sqrt_range(table, lo, hi):
    """Sum rounded sqrt(j), inclusive; integer subtraction precedes conversion."""
    if lo > hi:
        return 0.0
    left = lo - 1
    low = table[0, hi] - table[0, left]
    borrow = np.uint64(table[0, hi] < table[0, left])
    mid = table[1, hi] - table[1, left]
    high_borrow = np.uint64(table[1, hi] < table[1, left])
    middle = mid - borrow
    high_borrow += np.uint64(mid < borrow)
    high = table[2, hi] - table[2, left] - high_borrow
    return (math.ldexp(float(high), 76) + math.ldexp(float(middle), 12)
            + math.ldexp(float(low), -52))


@njit(cache=True)
def _group_runs(group, first_position, start, end, group_count):
    """Bucket temporal runs by score class in O(Q+G)."""
    counts = np.zeros(group_count, dtype=np.int64)
    distance = np.full(group_count, np.iinfo(np.int64).max, dtype=np.int64)
    for i in range(len(group)):
        g = group[i]
        if i == 0 or group[i-1] != g:
            counts[g] += 1
        p = first_position + i
        distance[g] = min(distance[g], max(start-p, p-end, 0))
    offsets = np.zeros(group_count + 1, dtype=np.int64)
    for g in range(group_count):
        offsets[g+1] = offsets[g] + counts[g]
    cursor = offsets[:-1].copy()
    low = np.empty(offsets[-1], dtype=np.int64)
    high = np.empty(offsets[-1], dtype=np.int64)
    i = 0
    while i < len(group):
        j = i + 1
        g = group[i]
        while j < len(group) and group[j] == g:
            j += 1
        k = cursor[g]
        low[k], high[k] = first_position+i, first_position+j-1
        cursor[g] += 1
        i = j
    return offsets, low, high, distance


def _prepare(y, scores, max_buffer):
    y, scores = _validate_inputs(y, scores, max_buffer)
    starts, ends = ranges(y)
    if len(starts) != 1:
        raise ValueError("tie-run evaluation requires exactly one original interval")
    n, start, end = len(y), int(starts[0]), int(ends[0])
    radius = min(int(max_buffer)//2, n-1)
    lo, hi = max(0, start-radius), min(n-1, end+radius)
    index = np.full(n, -1, dtype=np.int64)
    index[lo:hi+1] = np.arange(hi-lo+1, dtype=np.int64)
    keys = _descending_keys(scores)
    order = _radix_argsort(keys)
    group, before, after = _support_ranks(keys, order, index, hi-lo+1)
    offsets, run_low, run_high, distance = _group_runs(group, lo, start, end, len(before))
    activation = _activation_schedule(distance, starts, ends, radius)
    return (n, start, end, before, after, offsets, run_low, run_high,
            *activation[:4], _sqrt_prefix(int(max_buffer)))


@njit(cache=True)
def _evaluate(n, start, end, before, after, run_offsets, run_low, run_high,
              activation_offsets, activation_order, saved_previous,
              saved_following, sqrt_table, limit, compute_roc, diagnostics):
    following = np.empty(len(before), dtype=np.int64)
    head = -1
    positives = end-start+1
    events = np.empty(limit+1 if diagnostics else 0, dtype=np.int64)
    queries = np.empty(limit+1 if diagnostics else 0, dtype=np.int64)
    aggregated = np.empty(limit+1 if diagnostics else 0, dtype=np.int64)
    roc_total, pr_total = 0.0, 0.0
    for width in range(limit+1):
        radius = width//2
        if width % 2 == 0 and radius+1 < len(activation_offsets):
            for k in range(activation_offsets[radius], activation_offsets[radius+1]):
                g = activation_order[k]
                left, right = saved_previous[g], saved_following[g]
                following[g] = right
                if left < 0:
                    head = g
                else:
                    following[left] = g
        original_count, buffer_count = 0, 0
        mass, pr, roc = 0.0, 0.0, 0.0
        old_tp, old_recall = 0.0, 0.0
        old_negative, old_count = float(n-positives), 0
        event_count, query_count = 0, 0
        denominator = np.sqrt(float(width))
        g = head
        while g >= 0:
            event_count += 1
            for k in range(run_offsets[g], run_offsets[g+1]):
                query_count += 1
                lo, hi = run_low[k], run_high[k]
                original_count += max(0, min(hi, end)-max(lo, start)+1)
                # Left ramp, distances start-position.
                a, b = max(lo, start-radius), min(hi, start-1)
                if a <= b:
                    buffer_count += b-a+1
                    mass += _sqrt_range(sqrt_table, width-(start-a), width-(start-b))/denominator
                # Right ramp, distances position-end.
                a, b = max(lo, end+1), min(hi, end+radius)
                if a <= b:
                    buffer_count += b-a+1
                    mass += _sqrt_range(sqrt_table, width-(b-end), width-(a-end))/denominator
            tp = original_count + mass
            positive = positives + mass/2.0
            recall = min(tp/positive, 1.0)
            pr += (recall-old_recall)*tp/after[g]
            if compute_roc:
                negative = n-positive
                fpr = (after[g]-tp)/negative
                fpr_before = (before[g]-old_tp)/old_negative
                roc += (before[g]-old_count)*old_recall/old_negative
                roc += (fpr-fpr_before)*(recall+old_recall)/2.0
            # Each admitted buffer contributes >1/3 to A+B/2.
            # Counts stay integer; no rounded mass can trigger early stopping.
            if buffer_count//3 >= positives-original_count:
                if compute_roc:
                    roc += 1.0-fpr
                break
            old_recall = recall
            if compute_roc:
                old_tp, old_negative, old_count = tp, negative, after[g]
            g = following[g]
        roc_total += roc
        pr_total += pr
        if diagnostics:
            events[width], queries[width] = event_count, query_count
            aggregated[width] = original_count+buffer_count
    return roc_total/(limit+1), pr_total/(limit+1), events, queries, aggregated


def interval_vus_tie_runs_jit(y, scores, max_buffer):
    """Return exhaustive (ROC, PR); requires one contiguous positive interval."""
    prepared = _prepare(y, scores, max_buffer)
    result = _evaluate(*prepared, int(max_buffer), True, False)
    return float(result[0]), float(result[1])


def interval_pr_tie_runs_jit(y, scores, max_buffer):
    """Return exhaustive PR with ROC arithmetic omitted."""
    prepared = _prepare(y, scores, max_buffer)
    return float(_evaluate(*prepared, int(max_buffer), False, False)[1])


def profile_tie_runs(y, scores, max_buffer):
    """Values and measured event/run/aggregated-position counts at every width."""
    prepared = _prepare(y, scores, max_buffer)
    roc, pr, events, queries, aggregated = _evaluate(*prepared, int(max_buffer), True, True)
    return {"values": {"roc": float(roc), "pr": float(pr)},
            "events": events.tolist(), "run_queries": queries.tolist(),
            "positions_aggregated": aggregated.tolist(),
            "groups": len(prepared[3]), "runs": len(prepared[6])}
