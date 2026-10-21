"""Exact active-prefix VUS with monotone support activation.

The finite-binary64 ranking contract is shared with ``radix``. At each width,
only active support positions are traversed, and complete ties are processed.
Once every expanded component has been hit and A+B/2 >= P0, recall stays one:
PR's remaining area is zero and ROC's remaining area is 1-current_FPR.

Preparation uses radix order, a linear nearest-interval scan and offline linked
list insertion. Incremental union-find maintains expanded components. Under the
fixed-word and unit-cost metric model, the full call costs
O(n+L+alpha(K)*sum_w J_w), where J_w counts visited active positions INCLUDING
all positions in the terminating tie. Auxiliary storage is O(n+Q); the optional
profile additionally stores O(L) counts. This does not assert a universal speedup
or symbolic floating-point exactness. ``stop=False`` and ``'last_positive'`` are
research ablations using exactly the same active-list preparation.
"""
from __future__ import annotations

import numpy as np
from numba import njit

from .core import _validate_inputs, expanded_ranges, ranges
from .radix import _descending_keys, _radix_argsort, _support_ranks

__all__ = ["sparse_pr_saturation_jit", "sparse_vus_saturation_jit",
           "profile_saturation"]


@njit(cache=True)
def _nearest_owners(pos, starts, ends):
    """Nearest two distances and one nearest interval in O(Q+K)."""
    first = np.empty(len(pos), dtype=np.int64)
    second = np.empty(len(pos), dtype=np.int64)
    owner = np.empty(len(pos), dtype=np.int64)
    pointer = 0
    # All finite interval distances are < n. This integer sentinel therefore
    # cannot activate a nonexistent second interval at any permitted radius.
    infinity = np.iinfo(np.int64).max
    for i in range(len(pos)):
        point = pos[i]
        while pointer < len(starts) and starts[pointer] <= point:
            pointer += 1
        d1, d2, nearest = infinity, infinity, -1
        for k in range(max(0, pointer - 2), min(len(starts), pointer + 2)):
            distance = max(starts[k] - point, point - ends[k], 0)
            if distance < d1:
                d2, d1, nearest = d1, distance, k
            elif distance < d2:
                d2 = distance
        first[i], second[i], owner[i] = d1, d2, nearest
    return first, second, owner


@njit(cache=True)
def _support_order(order, support_index, size):
    result = np.empty(size, dtype=np.int64)
    write = 0
    for p in order:
        i = support_index[p]
        if i >= 0:
            result[write] = i
            write += 1
    return result


@njit(cache=True)
def _activation_schedule(distance, starts, ends, radius_limit):
    """Count-sort activation radii, then undo insertions by reverse deletion."""
    size = len(distance)
    offsets = np.zeros(radius_limit + 2, dtype=np.int64)
    for d in distance:
        offsets[d + 1] += 1
    for r in range(radius_limit + 1):
        offsets[r + 1] += offsets[r]
    cursor = offsets[:-1].copy()
    activation_order = np.empty(size, dtype=np.int64)
    for i in range(size):
        d = distance[i]
        activation_order[cursor[d]] = i
        cursor[d] += 1

    previous = np.arange(-1, size - 1, dtype=np.int64)
    following = np.arange(1, size + 1, dtype=np.int64)
    following[-1] = -1
    saved_previous = np.empty(size, dtype=np.int64)
    saved_following = np.empty(size, dtype=np.int64)
    for k in range(size - 1, -1, -1):
        i = activation_order[k]
        left, right = previous[i], following[i]
        saved_previous[i], saved_following[i] = left, right
        if left >= 0:
            following[left] = right
        if right >= 0:
            previous[right] = left

    merge_head = np.full(radius_limit + 1, -1, dtype=np.int64)
    merge_next = np.full(len(starts) - 1, -1, dtype=np.int64)
    for k in range(len(starts) - 1):
        gap = starts[k + 1] - ends[k]
        # Overlap, not mere adjacency: 2*r >= start_next-end_previous.
        radius = gap // 2 + gap % 2
        if radius <= radius_limit:
            merge_next[k] = merge_head[radius]
            merge_head[radius] = k
    return (offsets, activation_order, saved_previous, saved_following,
            merge_head, merge_next)


def _prepare_saturation(y, scores, max_buffer):
    y, scores = _validate_inputs(y, scores, max_buffer)
    n = len(y)
    starts, ends = ranges(y)
    lo, hi = expanded_ranges(starts, ends, n, max_buffer)
    pos = np.concatenate([np.arange(a, b + 1) for a, b in zip(lo, hi)])
    distance, second, owner = _nearest_owners(pos, starts, ends)
    support_index = np.full(n, -1, dtype=np.int64)
    support_index[pos] = np.arange(len(pos))
    keys = _descending_keys(scores)
    order = _radix_argsort(keys)
    group, before, after = _support_ranks(keys, order, support_index, len(pos))
    support_order = _support_order(order, support_index, len(pos))
    original = y[pos[support_order]].astype(np.bool_)
    distance, second, owner = (a[support_order] for a in (distance, second, owner))
    group = group[support_order]
    # Distances never exceed n-1; large L does not require length-L buckets.
    radius_limit = min(int(max_buffer) // 2, n - 1)
    schedule = _activation_schedule(distance, starts, ends, radius_limit)
    return (n, int(y.sum()), len(starts), original, distance, second, owner,
            group, before, after, *schedule)


@njit(cache=True, inline="always")
def _root(parent, node):
    while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = parent[node]
    return node


@njit(cache=True)
def _active_prefix_kernel(n, positives, interval_count, original, distance,
                          second, owner, group, before, after, offsets,
                          activation_order, saved_previous, saved_following,
                          merge_head, merge_next, max_buffer, stop_mode,
                          compute_roc, diagnostics):
    size = len(original)
    following = np.empty(size, dtype=np.int64)
    parent = np.arange(interval_count, dtype=np.int64)
    tree_size = np.ones(interval_count, dtype=np.int64)
    seen = np.full(interval_count, -1, dtype=np.int64)
    visited = np.empty(max_buffer + 1 if diagnostics else 0, dtype=np.int64)
    active = np.empty(max_buffer + 1 if diagnostics else 0, dtype=np.int64)
    components, active_count, head = interval_count, 0, -1
    roc_total, pr_total = 0.0, 0.0
    for width in range(max_buffer + 1):
        radius = width // 2
        if width % 2 == 0 and radius < len(merge_head):
            for k in range(offsets[radius], offsets[radius + 1]):
                i = activation_order[k]
                left, right = saved_previous[i], saved_following[i]
                following[i] = right
                if left >= 0:
                    following[left] = i
                else:
                    head = i
                active_count += 1
            edge = merge_head[radius]
            while edge >= 0:
                a, b = _root(parent, edge), _root(parent, edge + 1)
                if a != b:
                    if tree_size[a] < tree_size[b]:
                        a, b = b, a
                    parent[b] = a
                    tree_size[a] += tree_size[b]
                    components -= 1
                edge = merge_next[edge]

        # No component-array clearing or maximum-support scan occurs here.
        original_count, buffer_mass, hits, visit_count = 0, 0.0, 0, 0
        old_tp, old_recall = 0.0, 0.0
        old_negative, old_count = float(n - positives), 0
        roc, pr, saturated = 0.0, 0.0, False
        i = head
        while i >= 0:
            event = group[i]
            while i >= 0 and group[i] == event:
                if original[i]:
                    original_count += 1
                elif second[i] <= radius:
                    buffer_mass += 1.0
                else:
                    buffer_mass += np.sqrt(1.0 - distance[i] / width)
                root = _root(parent, owner[i])
                if seen[root] != width:
                    seen[root] = width
                    hits += 1
                visit_count += 1
                i = following[i]

            # Global before/after counts retain every inactive/off-support tie.
            tp = original_count + buffer_mass
            positive = positives + buffer_mass / 2.0
            recall = min(tp / positive, 1.0) * hits / components
            pr += (recall - old_recall) * tp / after[event]
            if compute_roc:
                negative = n - positive
                fpr = (after[event] - tp) / negative
                fpr_before = (before[event] - old_tp) / old_negative
                roc += (before[event] - old_count) * old_recall / old_negative
                roc += (fpr - fpr_before) * (recall + old_recall) / 2.0

            saturated = ((stop_mode == 1 and hits == components
                          and original_count + buffer_mass / 2.0 >= positives)
                         or (stop_mode == 2 and original_count == positives))
            if saturated:
                if compute_roc:
                    roc += 1.0 - fpr
                break
            old_recall = recall
            if compute_roc:
                old_tp, old_negative, old_count = tp, negative, after[event]
        if compute_roc and not saturated:
            terminal_fpr = (n - old_tp) / old_negative
            roc += (n - old_count) * old_recall / old_negative
            roc += (1.0 - terminal_fpr) * (1.0 + old_recall) / 2.0
        roc_total += roc
        pr_total += pr
        if diagnostics:
            visited[width], active[width] = visit_count, active_count
    return roc_total / (max_buffer + 1), pr_total / (max_buffer + 1), visited, active


def _stop_mode(stop):
    if stop is True:
        return 1
    if stop is False:
        return 0
    if isinstance(stop, str) and stop == "last_positive":
        return 2
    raise ValueError("stop must be True, False, or 'last_positive'")


def sparse_pr_saturation_jit(y, scores, max_buffer, *, stop=True) -> float:
    """Return exhaustive PR; optional stop modes are exact research ablations."""
    mode = _stop_mode(stop)
    prepared = _prepare_saturation(y, scores, max_buffer)
    result = _active_prefix_kernel(*prepared, int(max_buffer), mode, False, False)
    return float(result[1])


def sparse_vus_saturation_jit(y, scores, max_buffer, *, stop=True) -> tuple[float, float]:
    """Return exhaustive (ROC, PR), including validation and preparation."""
    mode = _stop_mode(stop)
    prepared = _prepare_saturation(y, scores, max_buffer)
    roc, pr, _, _ = _active_prefix_kernel(*prepared, int(max_buffer), mode, True, False)
    return float(roc), float(pr)


def profile_saturation(y, scores, max_buffer, *, stop=True):
    """Return values and actual per-width work, using O(L) diagnostic storage."""
    mode = _stop_mode(stop)
    prepared = _prepare_saturation(y, scores, max_buffer)
    roc, pr, visited, active = _active_prefix_kernel(
        *prepared, int(max_buffer), mode, True, True)
    return {"values": {"roc": float(roc), "pr": float(pr)},
            "visited": visited.tolist(), "active": active.tolist(),
            "Q": len(prepared[3]), "K": int(prepared[2])}
