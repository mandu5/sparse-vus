"""Exact sparse VUS with fixed-width float64 rank preparation.

Eight stable counting-radix passes sort transformed 64-bit score keys. Signed
zeros share one key, and the existing finite-score validator/conversion defines
the input contract. Temporal interval distances use a linear pointer scan.

For n positions, Q maximum-buffer positions, G distinct support scores and K
original intervals, preparation takes O(n+Q+K) time under a fixed-64-bit word-RAM
model. Exhaustive evaluation takes O(n+(L+1)Q), since G,K <= Q. This is not a
comparison-model result for arbitrary real numbers, and generic radix sorting
is prior art. Input-sized keys, permutation and scratch arrays mean auxiliary
memory is O(n+Q+L), not support-only. Floating-point arithmetic has the same
numerical rather than symbolic exactness as the existing compiled evaluators.

Requires the optional ``accelerate`` dependency. The base package does not
import this module automatically.
"""
from __future__ import annotations

import numpy as np
from numba import njit

from .compiled import _sparse_kernel
from .core import _validate_inputs, expanded_ranges, ranges
from .pr_compiled import _sparse_pr_kernel

__all__ = ["sparse_pr_radix_jit", "sparse_vus_radix_jit"]


@njit(cache=True)
def _descending_keys(scores):
    """Map finite float64 scores to uint64 keys ordered by decreasing score."""
    bits = scores.view(np.uint64)
    keys = np.empty(len(scores), dtype=np.uint64)
    sign = np.uint64(1) << np.uint64(63)
    for i in range(len(scores)):
        # Numerical equality groups both signed zeros into one threshold.
        word = np.uint64(0) if scores[i] == 0.0 else bits[i]
        ascending = ~word if word & sign else word ^ sign
        keys[i] = ~ascending
    return keys


@njit(cache=True)
def _radix_argsort(keys):
    """Stable eight-pass LSD counting sort; no comparison-sort dispatch."""
    n = len(keys)
    order = np.arange(n, dtype=np.int64)
    scratch = np.empty(n, dtype=np.int64)
    counts = np.zeros(256, dtype=np.int64)
    for shift in range(0, 64, 8):
        counts.fill(0)
        for i in range(n):
            digit = int((keys[order[i]] >> np.uint64(shift)) & np.uint64(255))
            counts[digit] += 1
        offset = 0
        for digit in range(256):
            count = counts[digit]
            counts[digit] = offset
            offset += count
        for i in range(n):
            index = order[i]
            digit = int((keys[index] >> np.uint64(shift)) & np.uint64(255))
            scratch[counts[digit]] = index
            counts[digit] += 1
        order, scratch = scratch, order
    return order


@njit(cache=True)
def _nearest_two_linear(pos, starts, ends):
    """Two nearest distinct intervals, with O(Q+K) monotone temporal scans."""
    nearest = np.empty(len(pos), dtype=np.float64)
    second = np.empty(len(pos), dtype=np.float64)
    right = 0
    for i in range(len(pos)):
        point = pos[i]
        while right < len(starts) and starts[right] <= point:
            right += 1
        first_distance, second_distance = np.inf, np.inf
        # More distant intervals on either side cannot beat these candidates.
        for interval in range(max(0, right - 2), min(len(starts), right + 2)):
            distance = float(max(starts[interval] - point, point - ends[interval], 0))
            if distance < first_distance:
                second_distance, first_distance = first_distance, distance
            elif distance < second_distance:
                second_distance = distance
        nearest[i], second[i] = first_distance, second_distance
    return nearest, second


@njit(cache=True)
def _support_ranks(keys, order, support_index, support_size):
    """Count complete global ties; retain only groups containing support."""
    group = np.empty(support_size, dtype=np.int64)
    before = np.empty(support_size, dtype=np.int64)
    after = np.empty(support_size, dtype=np.int64)
    rank, event, n = 0, 0, len(order)
    while rank < n:
        first = rank
        key = keys[order[rank]]
        has_support = False
        while rank < n and keys[order[rank]] == key:
            index = support_index[order[rank]]
            if index >= 0:
                group[index] = event
                has_support = True
            rank += 1
        if has_support:
            before[event], after[event] = first, rank
            event += 1
    return group, before[:event], after[:event]


def _prepare_radix(y, scores, max_buffer):
    """Return the same twelve prepared arrays as ``core._prepare``.

    All public validation and float64 conversion rules remain unchanged.
    Positions remain in temporal order; event groups follow decreasing scores.
    ``before`` counts strictly higher global scores and ``after`` also includes
    every off-support score tied with the current support event.
    """
    y, scores = _validate_inputs(y, scores, max_buffer)
    starts, ends = ranges(y)
    lo, hi = expanded_ranges(starts, ends, len(y), max_buffer)
    pos = np.concatenate([np.arange(a, b + 1) for a, b in zip(lo, hi)])
    original = y[pos].astype(bool)
    d1, d2 = _nearest_two_linear(pos, starts, ends)
    support_index = np.full(len(y), -1, dtype=np.int64)
    support_index[pos] = np.arange(len(pos))
    keys = _descending_keys(scores)
    order = _radix_argsort(keys)
    group, before, after = _support_ranks(keys, order, support_index, len(pos))
    return y, scores, starts, ends, pos, original, d1, d2, group, before, after, support_index


def sparse_pr_radix_jit(y, scores, max_buffer) -> float:
    """Return exhaustive PR only, including validation and radix preparation."""
    prepared = _prepare_radix(y, scores, max_buffer)
    y, _, starts, ends, pos, original, d1, d2, group, _, after, _ = prepared
    return float(_sparse_pr_kernel(len(y), float(y.sum()), starts, ends, pos,
                                  original, d1, d2, group, after, max_buffer))


def sparse_vus_radix_jit(y, scores, max_buffer) -> tuple[float, float]:
    """Return exhaustive (ROC, PR), including radix preparation and all ties."""
    prepared = _prepare_radix(y, scores, max_buffer)
    y, _, starts, ends, pos, original, d1, d2, group, before, after, _ = prepared
    return _sparse_kernel(len(y), float(y.sum()), starts, ends, pos, original,
                          d1, d2, group, before, after, max_buffer)
