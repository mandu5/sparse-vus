"""Adaptive width evaluation with deterministic real-arithmetic VUS bounds.

The mathematical bounds enclose every skipped integer width.  Float64
execution uses a small numerical guard, not directed rounding: this module
does not claim a formal machine-arithmetic interval certificate.  ``exact``
means all widths were evaluated, not bitwise equality with the reference.

See docs/theory_advancement_20261020.md for proofs and the p-box prior art.
Numba is optional; when installed, the two linear-time kernels are compiled.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import heapq
import math

import numpy as np

from .core import _prepare

try:
    from numba import njit
except ImportError:  # The base package requires only NumPy.
    def njit(*args, **kwargs):
        def decorate(function):
            return function
        return decorate


@dataclass(frozen=True)
class BufferCurve:
    width: int
    roc: float
    pr: float
    recall: np.ndarray
    precision: np.ndarray
    fpr: np.ndarray
    segments: int
    _owner: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class CertifiedVUSResult:
    roc_lower: float
    roc_upper: float
    pr_lower: float
    pr_upper: float
    evaluated_widths: tuple[int, ...]
    total_widths: int
    curve_evaluations: int
    exact: bool
    numerical_guard: float

    @property
    def estimate(self) -> tuple[float, float]:
        return ((self.roc_lower + self.roc_upper) / 2,
                (self.pr_lower + self.pr_upper) / 2)

    @property
    def evaluated_count(self) -> int:
        return len(self.evaluated_widths)

    @property
    def max_half_width(self) -> float:
        return max(self.roc_upper - self.roc_lower,
                   self.pr_upper - self.pr_lower) / 2


@njit(cache=True)
def _curve_kernel(n, p, starts, ends, pos, original, d1, d2, group,
                  before, after, width):
    """One exact sparse event sweep; no other widths are constructed."""
    radius = width // 2
    lo = np.empty(len(starts), dtype=np.int64)
    hi = np.empty(len(starts), dtype=np.int64)
    first_start, count = max(0, starts[0] - radius), 0
    for j in range(len(starts) - 1):
        if ends[j] + radius < starts[j + 1] - radius:
            lo[count], hi[count] = first_start, ends[j] + radius
            count += 1
            first_start = starts[j + 1] - radius
    lo[count], hi[count] = first_start, min(n - 1, ends[-1] + radius)
    count += 1

    groups = len(before)
    t_group, b_group = np.zeros(groups), np.zeros(groups)
    first = np.full(count, groups, dtype=np.int64)
    sid = 0
    for i in range(len(pos)):
        g = group[i]
        weight = 0.0
        if original[i]:
            weight = 1.0
        elif width >= 2 and d1[i] <= radius:
            weight = 1.0 if d2[i] <= radius else np.sqrt(1.0 - d1[i] / width)
        t_group[g] += weight
        if not original[i]:
            b_group[g] += weight
        while sid < count and pos[i] > hi[sid]:
            sid += 1
        if sid < count and pos[i] >= lo[sid]:
            first[sid] = min(first[sid], g)
    hits_group = np.zeros(groups, dtype=np.int64)
    for j in range(count):
        hits_group[first[j]] += 1

    recall, precision, fpr = np.empty(groups), np.empty(groups), np.empty(groups)
    tp, buf, hits = 0.0, 0.0, 0
    old_t, old_r, old_n, old_c = 0.0, 0.0, n - p, 0
    roc, pr = 0.0, 0.0
    for g in range(groups):
        tp += t_group[g]
        buf += b_group[g]
        hits += hits_group[g]
        positive = p + buf / 2
        negative = n - positive
        r = min(tp / positive, 1.0) * hits / count
        a = tp / after[g]
        f = (after[g] - tp) / negative
        f_before = (before[g] - old_t) / old_n
        roc += (before[g] - old_c) * old_r / old_n
        roc += (f - f_before) * (r + old_r) / 2
        pr += (r - old_r) * a
        recall[g], precision[g], fpr[g] = r, a, f
        old_t, old_r, old_n, old_c = tp, r, negative, after[g]
    terminal_f = (n - tp) / old_n
    roc += (n - after[-1]) * old_r / old_n
    roc += (1 - terminal_f) * (1 + old_r) / 2
    return roc, pr, recall, precision, fpr, count


@njit(cache=True)
def _pbox_extremum(lower_recall, upper_recall, precision, maximize):
    """Extremal expectation over a finite CDF p-box, in O(G) time.

    Each recall level z permits quantile indices from the first upper CDF
    reaching z through the first lower CDF reaching z.  Those index windows
    move only right, so a monotone deque supplies all range minima/maxima.
    """
    groups = len(precision)
    breaks = np.empty(2 * groups + 1)
    breaks[0] = 0.0
    i, j, size = 0, 0, 1
    while i < groups or j < groups:
        if j == groups or (i < groups and lower_recall[i] <= upper_recall[j]):
            value = lower_recall[i]
            i += 1
        else:
            value = upper_recall[j]
            j += 1
        if value > breaks[size - 1]:
            breaks[size] = value
            size += 1
    # Exact recall ends at one.  Protect the breakpoint from an ulp of drift.
    breaks[size - 1] = 1.0
    queue = np.empty(groups, dtype=np.int64)
    head, tail, added, left, right = 0, 0, -1, 0, 0
    result = 0.0
    for k in range(size - 1):
        z0, z1 = breaks[k], breaks[k + 1]
        while left + 1 < groups and upper_recall[left] <= z0:
            left += 1
        while right + 1 < groups and lower_recall[right] <= z0:
            right += 1
        while added < right:
            added += 1
            while tail > head:
                old = precision[queue[tail - 1]]
                new = precision[added]
                if (maximize and old <= new) or ((not maximize) and old >= new):
                    tail -= 1
                else:
                    break
            queue[tail] = added
            tail += 1
        while head < tail and queue[head] < left:
            head += 1
        result += (z1 - z0) * precision[queue[head]]
    return result


class PreparedEvaluator:
    """Reuse score ranks/label geometry for arbitrary integer width queries.

    At most ``cache_size`` complete endpoint curves are retained (default 8).
    Scalar values and queried width IDs are retained separately.  This avoids
    allocating a width-by-support matrix; evicted curves may be recomputed.
    """

    def __init__(self, y, scores, max_buffer, *, cache_size=8):
        if not isinstance(cache_size, (int, np.integer)) or cache_size < 1:
            raise ValueError("cache_size must be a positive integer")
        prepared = _prepare(y, scores, max_buffer)
        labels, _, starts, ends, pos, original, d1, d2, group, before, after, _ = prepared
        self.max_buffer = int(max_buffer)
        self.support_points = len(pos)
        self.support_scores = len(before)
        self._arguments = (len(labels), float(labels.sum()), starts, ends, pos,
                           original, d1, d2, group, before, after)
        self._cache_size = int(cache_size)
        self._cache = OrderedDict()
        self._scalars = {}
        self._owner = object()
        self.curve_evaluations = 0
        # The reference merges overlapping expansions, but not adjacent ones.
        cuts = sorted({2 * ((int(a) - int(b) + 1) // 2)
                       for a, b in zip(starts[1:], ends[:-1])})
        boundaries = [0] + [c for c in cuts if c <= max_buffer] + [max_buffer + 1]
        self.merge_free_intervals = tuple((a, b - 1) for a, b in zip(boundaries[:-1], boundaries[1:]))

    @property
    def evaluated_widths(self):
        return tuple(sorted(self._scalars))

    def evaluate(self, width) -> BufferCurve:
        if not isinstance(width, (int, np.integer)) or not 0 <= width <= self.max_buffer:
            raise ValueError("width must be an integer in [0, max_buffer]")
        width = int(width)
        if width in self._cache:
            self._cache.move_to_end(width)
            return self._cache[width]
        roc, pr, recall, precision, fpr, segments = _curve_kernel(*self._arguments, width)
        # These normalizations only suppress floating-point monotonicity drift;
        # the proof uses the unrounded real-arithmetic coordinates.
        recall = np.maximum.accumulate(np.clip(recall, 0.0, 1.0))
        recall[-1] = 1.0
        precision = np.clip(precision, 0.0, 1.0)
        for array in (recall, precision, fpr):
            array.setflags(write=False)
        result = BufferCurve(width, float(roc), float(pr), recall, precision,
                             fpr, int(segments), self._owner)
        self._scalars[width] = (result.roc, result.pr)
        self._cache[width] = result
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        self.curve_evaluations += 1
        return result


def width_bounds(left: BufferCurve, right: BufferCurve):
    """Bound both integrals for all integer widths between two endpoints.

    Endpoints must belong to the same prepared evaluator and to one merge-free
    interval.  The output is ``((roc_lower, pr_lower), (roc_upper, pr_upper))``.
    The precision–recall bound is a CDF p-box extremum, not an assumption that
    PR area is monotone with width.
    """
    if left._owner is not right._owner:
        raise ValueError("endpoint curves must belong to the same evaluator")
    if left.width > right.width:
        raise ValueError("endpoint widths must be in ascending order")
    if left.segments != right.segments:
        raise ValueError("endpoint widths must not cross an interval merge")
    if left.width == right.width:
        value = (left.roc, left.pr)
        return value, value
    lower_r = np.minimum(left.recall, right.recall)
    upper_r = np.maximum(left.recall, right.recall)
    lower_a = np.minimum(left.precision, right.precision)
    upper_a = np.maximum(left.precision, right.precision)
    pr_lower = float(_pbox_extremum(lower_r, upper_r, lower_a, False))
    pr_upper = float(_pbox_extremum(lower_r, upper_r, upper_a, True))
    return ((min(left.roc, right.roc), pr_lower),
            (max(left.roc, right.roc), pr_upper))


def certified_vus(y, scores, max_buffer, atol=1e-3) -> CertifiedVUSResult:
    """Evaluate VUS to a joint absolute tolerance by refining buffer widths.

    ``atol`` is the maximum interval half-width for *each* metric.  The estimate
    is its interval midpoint.  Zero requests all widths.  The adaptive result
    adds a 1e-12 numerical guard, which is an empirical float64 allowance, not
    a proven directed-rounding error bound.

    A strict ordering is certified in real arithmetic when one result's lower
    bound exceeds another result's upper bound for the metric of interest.
    """
    if not np.isscalar(atol) or not np.isfinite(atol) or atol < 0:
        raise ValueError("atol must be a finite nonnegative number")
    evaluator = PreparedEvaluator(y, scores, max_buffer)
    total = int(max_buffer) + 1
    guard = 1e-12
    heap = []

    def push(a, b):
        if b - a <= 1:
            return
        lower, upper = width_bounds(evaluator.evaluate(a), evaluator.evaluate(b))
        remaining = b - a - 1
        priority = remaining * max(upper[0] - lower[0], upper[1] - lower[1])
        heapq.heappush(heap, (-priority, a, b, lower, upper))

    if atol == 0:
        for width in range(total):
            evaluator.evaluate(width)
    else:
        for a, b in evaluator.merge_free_intervals:
            evaluator.evaluate(a)
            evaluator.evaluate(b)
            push(a, b)
        # The cumulative uncertain span depends only on active scalar bounds.
        uncertain = np.array([
            math.fsum((b - a - 1) * (hi[j] - lo[j]) for _, a, b, lo, hi in heap)
            for j in range(2)
        ])
        while heap and float(np.max(uncertain)) / (2 * total) + guard > atol:
            _, a, b, lower, upper = heapq.heappop(heap)
            uncertain -= (b - a - 1) * (np.asarray(upper) - lower)
            middle = (a + b) // 2
            evaluator.evaluate(middle)
            for aa, bb in ((a, middle), (middle, b)):
                if bb - aa > 1:
                    lo, hi = width_bounds(evaluator.evaluate(aa), evaluator.evaluate(bb))
                    remaining = bb - aa - 1
                    span = remaining * (np.asarray(hi) - lo)
                    uncertain += span
                    priority = float(np.max(span))
                    heapq.heappush(heap, (-priority, aa, bb, lo, hi))

    known = [math.fsum(value[j] for value in evaluator._scalars.values()) for j in range(2)]
    lower = [(known[j] + math.fsum((b - a - 1) * lo[j] for _, a, b, lo, _ in heap)) / total
             for j in range(2)]
    upper = [(known[j] + math.fsum((b - a - 1) * hi[j] for _, a, b, _, hi in heap)) / total
             for j in range(2)]
    exact = len(evaluator._scalars) == total
    applied_guard = 0.0 if exact else guard
    lower = [max(0.0, value - applied_guard) for value in lower]
    upper = [min(1.0, value + applied_guard) for value in upper]
    return CertifiedVUSResult(
        roc_lower=lower[0], roc_upper=upper[0],
        pr_lower=lower[1], pr_upper=upper[1],
        evaluated_widths=evaluator.evaluated_widths,
        total_widths=total, curve_evaluations=evaluator.curve_evaluations,
        exact=exact, numerical_guard=applied_guard,
    )
