"""Incremental, numerically audited PR model racing.

This is a disclosed follow-up to fixed-tolerance width evaluation.  Models
share no scores or outcomes, but each model reuses its own preparation and
endpoint cache throughout the race.  Only PR uncertainty controls refinement.
Float64 bounds are not formal machine-arithmetic interval certificates.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import heapq
import math

import numpy as np

from .certified import PreparedEvaluator, width_bounds
from .selection import ORDER_MARGIN, TIE_ATOL, _tied_winners


NUMERICAL_GUARD = 1e-12


def _screen_race(names, pairs, prune):
    """The selection policy in O(M), with names already sorted.

    Any separated winner must have the largest lower bound: a model with a
    smaller lower bound cannot exceed the larger-bound model's upper bound.
    """
    best = max(names, key=lambda name: pairs[name][0])
    maximum_lower = pairs[best][0]
    if all(maximum_lower > pairs[other][1] + ORDER_MARGIN
           for other in names if other != best):
        return best, (best,)
    if not prune:
        return None, names
    return None, tuple(name for name in names
                       if not pairs[name][1] < maximum_lower - ORDER_MARGIN)


@dataclass(frozen=True)
class PRRaceBound:
    pr_lower: float
    pr_upper: float
    exact: bool
    evaluated_widths: tuple[int, ...]
    curve_evaluations: int
    numerical_guard: float


@dataclass(frozen=True)
class PRRaceResult:
    selected: tuple[str, ...]
    early_winner: bool
    candidate_models: tuple[str, ...]
    pruned_models: tuple[str, ...]
    bounds: dict[str, PRRaceBound]
    exact_pr: dict[str, float]
    full_evaluation_count: int
    initial_curve_evaluations: int
    initial_unique_widths: int
    refinement_steps: int
    total_curve_evaluations: int
    total_unique_widths: int
    total_models: int
    prune: bool
    order_margin: float = ORDER_MARGIN
    tie_atol: float = TIE_ATOL
    ordering_scope: str = "numerically_audited_not_formal_float_certification"

    @property
    def candidate_count(self) -> int:
        return len(self.candidate_models)


class PRWidthState:
    """A reusable, incremental PR-width enclosure for one detector.

    Initialization evaluates both endpoints of every merge-free block.
    ``refine`` evaluates exactly one previously unseen width, at the midpoint
    of the interior contributing the largest PR-bound span.  It can recompute
    evicted endpoint curves, which are counted by ``curve_evaluations``.
    All exact scalar values are retained; no exact fallback repeats preparation.
    """

    def __init__(self, y, scores, max_buffer, *, cache_size=8):
        self.evaluator = PreparedEvaluator(y, scores, max_buffer, cache_size=cache_size)
        self.total_widths = int(max_buffer) + 1
        self._observed = {}
        self._known_sum = 0.0
        self._lower_pending = 0.0
        self._upper_pending = 0.0
        self._heap = []
        self.refinement_steps = 0
        for left, right in self.evaluator.merge_free_intervals:
            self._read_curve(left)
            self._read_curve(right)
            self._add_interval(left, right)
        self.initial_curve_evaluations = self.evaluator.curve_evaluations
        self.initial_unique_widths = len(self._observed)

    def _read_curve(self, width):
        curve = self.evaluator.evaluate(width)
        if width not in self._observed:
            self._observed[width] = curve.pr
            self._known_sum = math.fsum((self._known_sum, curve.pr))
        return curve

    def _add_interval(self, left, right):
        if right - left <= 1:
            return
        lower, upper = width_bounds(self._read_curve(left), self._read_curve(right))
        lower_pr, upper_pr = lower[1], upper[1]
        remaining = right - left - 1
        self._lower_pending = math.fsum((self._lower_pending, remaining * lower_pr))
        self._upper_pending = math.fsum((self._upper_pending, remaining * upper_pr))
        priority = remaining * max(0.0, upper_pr - lower_pr)
        heapq.heappush(self._heap, (-priority, left, right, lower_pr, upper_pr))

    @property
    def evaluated_count(self):
        return len(self._observed)

    @property
    def exact(self):
        return len(self._observed) == self.total_widths

    @property
    def exact_pr(self):
        if not self.exact:
            return None
        return math.fsum(self._observed.values()) / self.total_widths

    @property
    def pr_interval(self):
        if self.exact:
            value = self.exact_pr
            return value, value
        lower = (self._known_sum + self._lower_pending) / self.total_widths
        upper = (self._known_sum + self._upper_pending) / self.total_widths
        return max(0.0, lower - NUMERICAL_GUARD), min(1.0, upper + NUMERICAL_GUARD)

    def refine(self):
        """Refine one width; return False only when every width is known."""
        if self.exact:
            return False
        if not self._heap:
            raise RuntimeError("unresolved widths have no enclosing interval")
        _, left, right, lower, upper = heapq.heappop(self._heap)
        remaining = right - left - 1
        self._lower_pending = math.fsum((self._lower_pending, -remaining * lower))
        self._upper_pending = math.fsum((self._upper_pending, -remaining * upper))
        middle = (left + right) // 2
        if middle in self._observed:
            raise RuntimeError("refinement must query a previously unseen width")
        self._read_curve(middle)
        self._add_interval(left, middle)
        self._add_interval(middle, right)
        self.refinement_steps += 1
        return True

    def snapshot(self):
        lower, upper = self.pr_interval
        return PRRaceBound(
            pr_lower=lower, pr_upper=upper, exact=self.exact,
            evaluated_widths=tuple(sorted(self._observed)),
            curve_evaluations=self.evaluator.curve_evaluations,
            numerical_guard=0.0 if self.exact else NUMERICAL_GUARD,
        )


def race_pr_models(y, scores_by_model: Mapping[str, object], max_buffer, *, prune=True) -> PRRaceResult:
    """Race PR enclosures until the winner or exact tie set is determined.

    A strict winner needs lower > every other upper + 3e-10.  Otherwise,
    ``prune=True`` excludes upper < largest lower - 3e-10.  Among competitive
    nonexact models, refine the one with the widest PR interval; ties use
    lexicographic model order.  Its next width bisects the interval with the
    largest count-weighted PR span.  ROC tolerance is never a stopping gate.

    If all survivors are exact, return every exact PR within 1e-10 of their
    maximum.  Each refinement adds one unique width, so termination takes at
    most M*(L+1) unique width evaluations.  ``prune=False`` preserves the
    separated-winner check, but refines all models when no winner separates.

    ``early_winner`` identifies the separation return path, even if all
    widths happened to have been evaluated.  ``exact_pr`` includes every
    fully evaluated model, including excluded models.  No second exact
    evaluator call occurs: exact PR is summed from already observed widths.
    """
    if not isinstance(scores_by_model, Mapping) or not scores_by_model:
        raise ValueError("scores_by_model must be a nonempty mapping with string model names")
    if any(not isinstance(name, str) for name in scores_by_model):
        raise ValueError("scores_by_model must be a mapping with string model names")
    if not isinstance(prune, (bool, np.bool_)):
        raise ValueError("prune must be a boolean")
    names = tuple(sorted(scores_by_model))
    states = {name: PRWidthState(y, scores_by_model[name], max_buffer) for name in names}

    while True:
        pairs = {name: state.pr_interval for name, state in states.items()}
        winner, candidates = _screen_race(names, pairs, bool(prune))
        if not candidates:
            raise RuntimeError("valid interval screening cannot eliminate every candidate")
        if winner is not None:
            selected = (winner,)
            early_winner = True
            break
        nonexact = tuple(name for name in candidates if not states[name].exact)
        if not nonexact:
            selected = _tied_winners({name: states[name].exact_pr for name in candidates})
            early_winner = False
            break
        # max preserves the first lexicographically sorted name on equal spans.
        chosen = max(nonexact, key=lambda name: pairs[name][1] - pairs[name][0])
        states[chosen].refine()

    bounds = {name: state.snapshot() for name, state in states.items()}
    exact_pr = {name: state.exact_pr for name, state in states.items() if state.exact}
    return PRRaceResult(
        selected=selected, early_winner=early_winner,
        candidate_models=candidates,
        pruned_models=tuple(name for name in names if name not in candidates),
        bounds=bounds, exact_pr=exact_pr,
        full_evaluation_count=len(exact_pr),
        initial_curve_evaluations=sum(state.initial_curve_evaluations for state in states.values()),
        initial_unique_widths=sum(state.initial_unique_widths for state in states.values()),
        refinement_steps=sum(state.refinement_steps for state in states.values()),
        total_curve_evaluations=sum(state.evaluator.curve_evaluations for state in states.values()),
        total_unique_widths=sum(state.evaluated_count for state in states.values()),
        total_models=len(names), prune=bool(prune),
    )
