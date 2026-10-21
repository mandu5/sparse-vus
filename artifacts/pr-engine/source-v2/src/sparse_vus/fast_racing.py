"""PR-only compiled model selection with bounded adaptive work.

An endpoint is evaluated at most once. Before retained coordinates exceed a
work or memory budget, the model finishes just its unseen widths. Bounds are
real-arithmetic p-box bounds with empirical Float64 guards, not directed
rounding certificates. Requires the optional ``accelerate`` dependency.
"""
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from numba import njit
from numba.typed import List

from .core import _prepare
from .compiled import _segments, _weight
from .pr_compiled import _sparse_pr_complete
from .racing import PRRaceBound


@dataclass(frozen=True)
class FastPRRaceResult:
    selected: tuple[str, ...]
    candidate_models: tuple[str, ...]
    bounds: dict[str, PRRaceBound]
    fallback_models: tuple[str, ...]
    total_unique_widths: int
    total_curve_evaluations: int
    adaptive_curve_evaluations: int
    completion_curve_evaluations: int
    retained_curve_bytes: int
    early_winner: bool
    ordering_scope: str = "numerically_audited_not_formal_float_certification"


@njit(cache=True)
def _pr_curve(args, width, recall, precision):
    n, p, starts, ends, pos, original, d1, d2, group, after = args
    lo, hi = _segments(starts, ends, n, width)
    groups = len(after)
    t_group, b_group = np.zeros(groups), np.zeros(groups)
    first = np.full(len(lo), groups, np.int64)
    sid = 0
    for i in range(len(pos)):
        g = group[i]
        weight = _weight(original[i], d1[i], d2[i], width)
        t_group[g] += weight
        if not original[i]:
            b_group[g] += weight
        while sid < len(lo) and pos[i] > hi[sid]:
            sid += 1
        if sid < len(lo) and pos[i] >= lo[sid]:
            first[sid] = min(first[sid], g)
    hit_group = np.zeros(groups, np.int64)
    for j in range(len(first)):
        hit_group[first[j]] += 1
    tp, buf, hits, previous, area, maximum_r = 0., 0., 0, 0., 0., 0.
    for g in range(groups):
        tp += t_group[g]
        buf += b_group[g]
        hits += hit_group[g]
        r = min(tp / (p + buf / 2), 1.) * hits / len(lo)
        a = tp / after[g]
        area += (r - previous) * a
        previous = r
        maximum_r = max(maximum_r, min(1., max(0., r)))
        recall[g] = maximum_r
        precision[g] = min(1., max(0., a))
    recall[-1] = 1.
    return area


@njit(cache=True)
def _pr_bounds(a, b):
    """Both p-box extrema in one quantile traversal, without break arrays."""
    groups = a.shape[1]
    qmin, qmax = np.empty(groups, np.int64), np.empty(groups, np.int64)
    hmin, tmin, hmax, tmax = 0, 0, 0, 0
    added, left, right, z, lower, upper = -1, 0, 0, 0., 0., 0.
    while z < 1.:
        while left + 1 < groups and max(a[0, left], b[0, left]) <= z:
            left += 1
        while right + 1 < groups and min(a[0, right], b[0, right]) <= z:
            right += 1
        while added < right:
            added += 1
            new_min = min(a[1, added], b[1, added])
            new_max = max(a[1, added], b[1, added])
            while tmin > hmin:
                old = qmin[tmin - 1]
                if min(a[1, old], b[1, old]) >= new_min:
                    tmin -= 1
                else:
                    break
            while tmax > hmax:
                old = qmax[tmax - 1]
                if max(a[1, old], b[1, old]) <= new_max:
                    tmax -= 1
                else:
                    break
            qmin[tmin], qmax[tmax] = added, added
            tmin += 1
            tmax += 1
        while hmin < tmin and qmin[hmin] < left:
            hmin += 1
        while hmax < tmax and qmax[hmax] < left:
            hmax += 1
        next_z = min(max(a[0, left], b[0, left]), min(a[0, right], b[0, right]))
        imin, imax = qmin[hmin], qmax[hmax]
        lower += (next_z - z) * min(a[1, imin], b[1, imin])
        upper += (next_z - z) * max(a[1, imax], b[1, imax])
        z = next_z
    return lower, upper


@njit(cache=True)
def _add_interval(m, left, right, slots, curves, rights, lower, upper):
    if right - left <= 1:
        rights[m, left] = -1
        return
    a, b = curves[m][slots[m, left]], curves[m][slots[m, right]]
    lower[m, left], upper[m, left] = _pr_bounds(a, b)
    rights[m, left] = right


@njit(cache=True)
def _read_endpoint(m, width, args, scalars, slots, used, curves, evaluations):
    if not np.isnan(scalars[m, width]):
        return
    slot = used[m]
    scalars[m, width] = _pr_curve(args[m], width, curves[m][slot, 0], curves[m][slot, 1])
    evaluations[m] += 1
    slots[m, width] = slot
    used[m] += 1


@njit(cache=True)
def _finish_model(m, args, scalars, rights, fallback, evaluations):
    n, p, starts, ends, pos, original, d1, d2, group, after = args[m]
    evaluations[m] += _sparse_pr_complete(n, p, starts, ends, pos, original,
                                         d1, d2, group, after, scalars[m])
    for w in range(scalars.shape[1]):
        rights[m, w] = -1
    fallback[m] = True


@njit(cache=True)
def _all_bounds(scalars, rights, lower, upper):
    models, total = scalars.shape
    bounds = np.empty((models, 2))
    counts = np.zeros(models, np.int64)
    for m in range(models):
        known, pending_lo, pending_hi = 0., 0., 0.
        for w in range(total):
            if not np.isnan(scalars[m, w]):
                known += scalars[m, w]
                counts[m] += 1
            right = rights[m, w]
            if right >= 0:
                pending_lo += (right - w - 1) * lower[m, w]
                pending_hi += (right - w - 1) * upper[m, w]
        if counts[m] == total:
            bounds[m, 0] = known / total
            bounds[m, 1] = known / total
        else:
            bounds[m, 0] = max(0., (known + pending_lo) / total - 1e-12)
            bounds[m, 1] = min(1., (known + pending_hi) / total + 1e-12)
    return bounds, counts


@njit(cache=True)
def _race_kernel(args, blocks, capacities, curves, total, prune):
    models = len(args)
    scalars = np.full((models, total), np.nan)
    slots = np.full((models, total), -1, np.int64)
    used = np.zeros(models, np.int64)
    rights = np.full((models, total), -1, np.int64)
    lower, upper = np.zeros((models, total)), np.zeros((models, total))
    fallback = np.zeros(models, np.bool_)
    evaluations = np.zeros(models, np.int64)
    endpoint_count = 0
    for i in range(len(blocks)):
        endpoint_count += 1 if blocks[i, 0] == blocks[i, 1] else 2
    for m in range(models):
        if capacities[m] < endpoint_count:
            _finish_model(m, args, scalars, rights, fallback, evaluations)
        else:
            for i in range(len(blocks)):
                left, right = blocks[i]
                _read_endpoint(m, left, args, scalars, slots, used, curves, evaluations)
                _read_endpoint(m, right, args, scalars, slots, used, curves, evaluations)
                _add_interval(m, left, right, slots, curves, rights, lower, upper)
    selected = np.zeros(models, np.bool_)
    candidates = np.ones(models, np.bool_)
    while True:
        bounds, counts = _all_bounds(scalars, rights, lower, upper)
        best = np.argmax(bounds[:, 0])
        separated = True
        for m in range(models):
            if m != best and bounds[best, 0] <= bounds[m, 1] + 3e-10:
                separated = False
            candidates[m] = (not prune) or bounds[m, 1] >= bounds[best, 0] - 3e-10
        if separated:
            selected[best] = True
            return scalars, bounds, counts, fallback, selected, candidates, evaluations, used
        chosen, largest = -1, -1.
        for m in range(models):
            if candidates[m] and counts[m] < total:
                span = bounds[m, 1] - bounds[m, 0]
                if span > largest:
                    chosen, largest = m, span
        if chosen < 0:
            maximum = -1.
            for m in range(models):
                if candidates[m]:
                    maximum = max(maximum, bounds[m, 0])
            for m in range(models):
                selected[m] = candidates[m] and maximum - bounds[m, 0] <= 1e-10
            return scalars, bounds, counts, fallback, selected, candidates, evaluations, used
        if used[chosen] >= capacities[chosen]:
            _finish_model(chosen, args, scalars, rights, fallback, evaluations)
            continue
        left, priority = -1, -1.
        for w in range(total):
            right = rights[chosen, w]
            if right >= 0:
                span = (right - w - 1) * max(0., upper[chosen, w] - lower[chosen, w])
                if span > priority:
                    left, priority = w, span
        if left < 0:
            raise RuntimeError("unresolved widths have no enclosing interval")
        right = rights[chosen, left]
        middle = (left + right) // 2
        _read_endpoint(chosen, middle, args, scalars, slots, used, curves, evaluations)
        _add_interval(chosen, left, middle, slots, curves, rights, lower, upper)
        _add_interval(chosen, middle, right, slots, curves, rights, lower, upper)


def race_pr_models_fast(y, scores_by_model, max_buffer, *, adaptive_fraction=0.125,
                        memory_bytes=8 * 1024 * 1024, prune=True,
                        preparation="histogram"):
    """Select the exact PR winner set with bounded adaptive overhead.

    ``adaptive_fraction`` caps retained endpoints at that fraction of L+1,
    with a minimum of two when nonzero. ``memory_bytes`` further limits the
    retained coordinate arrays *per model*, excluding linear working arrays.
    Zero for either budget immediately uses exact completion. Limits are
    policy parameters, not learned from test outcomes. The default budget is
    one eighth of widths and 8 MiB per model. All preprocessing is per call.
    ``preparation`` selects the support histogram or fixed-width float64 radix
    implementation. Both retain every global tie and have identical semantics.
    """
    if not isinstance(preparation, str) or preparation not in ("histogram", "radix"):
        raise ValueError("preparation must be 'histogram' or 'radix'")
    prepare = _prepare
    if preparation == "radix":
        from .radix import _prepare_radix
        prepare = _prepare_radix
    if not isinstance(scores_by_model, Mapping) or not scores_by_model or any(
            not isinstance(k, str) for k in scores_by_model):
        raise ValueError("scores_by_model must be a nonempty mapping with string names")
    if (not np.isscalar(adaptive_fraction) or not np.isfinite(adaptive_fraction)
            or not 0 <= adaptive_fraction <= 1):
        raise ValueError("adaptive_fraction must be finite in [0, 1]")
    if not isinstance(memory_bytes, (int, np.integer)) or memory_bytes < 0:
        raise ValueError("memory_bytes must be a nonnegative integer")
    if not isinstance(prune, (bool, np.bool_)):
        raise ValueError("prune must be boolean")
    names = tuple(sorted(scores_by_model))
    arguments, curves = List(), List()
    capacities = []
    for name in names:
        prepared = prepare(y, scores_by_model[name], max_buffer)
        labels, _, starts, ends, pos, original, d1, d2, group, before, after, _ = prepared
        arguments.append((len(labels), float(labels.sum()), starts, ends, pos,
                          original, d1, d2, group, after))
        total = int(max_buffer) + 1
        work_cap = min(total, max(2, int(total * adaptive_fraction))) if adaptive_fraction else 0
        capacity = min(work_cap, memory_bytes // (16 * len(after)))
        capacities.append(capacity)
        curves.append(np.empty((capacity, 2, len(after))))
    cuts = sorted({2 * ((int(a) - int(b) + 1) // 2)
                   for a, b in zip(starts[1:], ends[:-1])})
    boundaries = [0] + [c for c in cuts if c <= max_buffer] + [total]
    blocks = np.array([(a, b - 1) for a, b in zip(boundaries[:-1], boundaries[1:])], dtype=np.int64)
    scalars, pairs, counts, fallback, selected, candidates, evaluations, used = _race_kernel(
        arguments, blocks, np.asarray(capacities, np.int64), curves, total, bool(prune))
    bounds = {name: PRRaceBound(float(pairs[i, 0]), float(pairs[i, 1]),
                              bool(counts[i] == total),
                              tuple(map(int, np.flatnonzero(~np.isnan(scalars[i])))),
                              int(evaluations[i]), 0. if counts[i] == total else 1e-12)
              for i, name in enumerate(names)}
    return FastPRRaceResult(
        tuple(name for i, name in enumerate(names) if selected[i]),
        tuple(name for i, name in enumerate(names) if candidates[i]), bounds,
        tuple(name for i, name in enumerate(names) if fallback[i]),
        int(np.sum(counts)), int(np.sum(evaluations)), int(np.sum(used)),
        int(np.sum(evaluations - used)), sum(c.nbytes for c in curves),
        bool(np.sum(selected) == 1 and np.any(counts < total)),
    )
