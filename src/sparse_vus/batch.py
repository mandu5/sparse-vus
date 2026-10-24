"""Complete PR evaluation of multiple scores sharing one label sequence.

This preserves the original dynamic VUS target and complete global score ties.
``geometry`` reuses label-only preparation; ``stream`` additionally interchanges
the width/model loops so weights and merged-component IDs are computed once per
width. Neither is a certificate of real-arithmetic rounding or a new metric.

For M models and maximum support Q, streaming retains O(MQ+n+Q+K) working words,
instead of a width-by-support materialization. Its asymptotic evaluation work
remains O(Mn + (L+1)MQ); reuse removes repeated geometry and square roots, not
model-dependent weighted histograms. Performance is an empirical question.
"""
from __future__ import annotations

import numpy as np
from numba import njit

from .core import _validate_inputs, expanded_ranges, ranges
from .pr_compiled import _expanded_segments, _sparse_pr_kernel
from .radix import (_descending_keys, _nearest_two_linear, _radix_argsort,
                    _support_ranks)

__all__ = ["batch_pr"]


@njit(cache=True)
def _stream_kernel(n, positives, starts, ends, pos, original, d1, d2,
                   model_groups, model_after, group_counts, max_buffer):
    models, support = model_groups.shape
    out = np.zeros(models)
    left = np.empty(len(starts), dtype=np.int64)
    right = np.empty(len(starts), dtype=np.int64)
    first = np.empty(len(starts), dtype=np.int64)
    weights = np.empty(support)
    component = np.empty(support, dtype=np.int64)
    mass = np.empty(support)
    buffer = np.empty(support)
    new_hits = np.empty(support, dtype=np.int64)
    for width in range(max_buffer + 1):
        segments = _expanded_segments(starts, ends, n, width, left, right)
        segment = 0
        for i in range(support):
            weight = 0.0
            if original[i]:
                weight = 1.0
            elif width >= 2 and d1[i] <= width // 2:
                weight = 1.0 if d2[i] <= width // 2 else np.sqrt(1.0-d1[i]/width)
            weights[i] = weight
            while segment < segments and pos[i] > right[segment]:
                segment += 1
            component[i] = segment if segment < segments and pos[i] >= left[segment] else -1
        for model in range(models):
            groups = group_counts[model]
            mass[:groups].fill(0.0)
            buffer[:groups].fill(0.0)
            new_hits[:groups].fill(0)
            first[:segments].fill(groups)
            for i in range(support):
                event = model_groups[model, i]
                mass[event] += weights[i]
                if not original[i]:
                    buffer[event] += weights[i]
                c = component[i]
                if c >= 0 and event < first[c]:
                    first[c] = event
            for c in range(segments):
                new_hits[first[c]] += 1
            tp, buf, hits, previous, pr = 0.0, 0.0, 0, 0.0, 0.0
            for event in range(groups):
                tp += mass[event]
                buf += buffer[event]
                hits += new_hits[event]
                recall = min(tp/(positives+buf/2.0), 1.0)*hits/segments
                pr += (recall-previous)*tp/model_after[model, event]
                previous = recall
            out[model] += pr
    return out/(max_buffer+1)


def batch_pr(y, scores, max_buffer, *, strategy="stream") -> np.ndarray:
    """Evaluate model-by-time scores, including validation and all preparation.

    Returns one exhaustive numerical PR value per model in input order. This
    call owns its temporary arrays and does not mutate labels or model scores.
    """
    if strategy not in ("geometry", "stream"):
        raise ValueError("strategy must be 'geometry' or 'stream'")
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 2 or len(scores) == 0:
        raise ValueError("scores must be a nonempty model-by-time matrix")
    y, _ = _validate_inputs(y, scores[0], max_buffer)
    if not np.isfinite(scores).all():
        raise ValueError("all model scores must be finite")
    max_buffer = int(max_buffer)
    starts, ends = ranges(y)
    lo, hi = expanded_ranges(starts, ends, len(y), max_buffer)
    pos = np.concatenate([np.arange(a, b+1) for a, b in zip(lo, hi)])
    original = y[pos].astype(bool)
    d1, d2 = _nearest_two_linear(pos, starts, ends)
    support_index = np.full(len(y), -1, dtype=np.int64)
    support_index[pos] = np.arange(len(pos))
    positives = float(y.sum())
    if strategy == "geometry":
        out = np.empty(len(scores))
        for model, score in enumerate(scores):
            keys = _descending_keys(np.ascontiguousarray(score))
            order = _radix_argsort(keys)
            group, _, after = _support_ranks(keys, order, support_index, len(pos))
            out[model] = _sparse_pr_kernel(len(y), positives, starts, ends, pos,
                                         original, d1, d2, group, after, max_buffer)
        return out
    groups = np.empty((len(scores), len(pos)), dtype=np.int64)
    afters = np.empty_like(groups)
    counts = np.empty(len(scores), dtype=np.int64)
    for model, score in enumerate(scores):
        keys = _descending_keys(np.ascontiguousarray(score))
        order = _radix_argsort(keys)
        group, _, after = _support_ranks(keys, order, support_index, len(pos))
        groups[model] = group
        counts[model] = len(after)
        afters[model, :len(after)] = after
    return _stream_kernel(len(y), positives, starts, ends, pos, original, d1, d2,
                          groups, afters, counts, max_buffer)
