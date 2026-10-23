"""Matched uniform-rank sampled PR for the original dynamic VUS contract.

This is an approximation to exhaustive PR, not an exact evaluator. It uses
the same radix preparation primitives and compiled integration kernel as the
exhaustive control, so benchmark differences do not merely measure Python
overhead. The complete numerical score tie is always admitted. Requires the
optional accelerate dependency; the base package does not import this module.
"""
from __future__ import annotations

import numpy as np
from numba import njit

from .core import _validate_inputs, expanded_ranges, ranges
from .pr_compiled import _sparse_pr_kernel
from .radix import (_descending_keys, _nearest_two_linear, _radix_argsort,
                    _support_ranks)

__all__ = ["sampled_pr_radix_jit"]


@njit(cache=True)
def _sampled_counts(keys, order, indices):
    """Complete-tie counts and distinct-threshold ordinals on a fixed grid."""
    counts = np.empty(len(indices), dtype=np.int64)
    ordinals = np.empty(len(indices), dtype=np.int64)
    rank, slot, ordinal, out = 0, 0, 0, 0
    while rank < len(order):
        key = keys[order[rank]]
        while rank < len(order) and keys[order[rank]] == key:
            rank += 1
        selected = False
        while slot < len(indices) and indices[slot] < rank:
            selected = True
            slot += 1
        if selected:
            counts[out], ordinals[out] = rank, ordinal
            out += 1
        ordinal += 1
    return counts[:out], ordinals[:out]


def _prepare_sampled(y, scores, max_buffer, thresholds):
    if (isinstance(thresholds, (bool, np.bool_))
            or not isinstance(thresholds, (int, np.integer)) or thresholds < 2):
        raise ValueError("thresholds must be an integer >= 2")
    y, scores = _validate_inputs(y, scores, max_buffer)
    max_buffer = int(max_buffer)
    starts, ends = ranges(y)
    lo, hi = expanded_ranges(starts, ends, len(y), max_buffer)
    pos = np.concatenate([np.arange(a, b + 1) for a, b in zip(lo, hi)])
    original = y[pos].astype(bool)
    d1, d2 = _nearest_two_linear(pos, starts, ends)
    support_index = np.full(len(y), -1, dtype=np.int64)
    support_index[pos] = np.arange(len(pos))
    keys = _descending_keys(scores)
    order = _radix_argsort(keys)
    group, _, after = _support_ranks(keys, order, support_index, len(pos))
    # Match the upstream floating-point linspace rule, rather than substituting
    # an integer-ratio grid with potentially different last-bit rounding.
    indices = np.linspace(0, len(y) - 1, int(thresholds)).astype(np.int64)
    counts, ordinals = _sampled_counts(keys, order, indices)
    event_bins = np.searchsorted(counts, after, side="left")
    bins = event_bins[group]
    return (y, scores, starts, ends, pos, original, d1, d2, bins,
            counts, ordinals)


def sampled_pr_radix_jit(y, scores, max_buffer, thresholds=250) -> float:
    """Evaluate the sampled PR scalar, including validation and preparation.

    Threshold budgets larger than n and repeated/tied thresholds follow the
    upstream semantics; deduplicating identical states leaves the integral
    unchanged. Every integer width from zero through max_buffer is included.
    """
    y, _, starts, ends, pos, original, d1, d2, bins, counts, _ = (
        _prepare_sampled(y, scores, max_buffer, thresholds))
    max_buffer = int(max_buffer)
    return float(_sparse_pr_kernel(len(y), float(y.sum()), starts, ends, pos,
                                  original, d1, d2, bins, counts, max_buffer))
