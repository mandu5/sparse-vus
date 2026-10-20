"""Numerically audited PR ordering with width bounds and exact fallback.

This policy uses the real-arithmetic enclosures from ``certified_vus`` with
a fixed separation margin.  Its Float64 ordering is numerically audited,
not a formal machine-arithmetic or statistical confidence certificate.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np

from .certified import CertifiedVUSResult, certified_vus
from .core import sparse_vus


ORDER_MARGIN = 3e-10
TIE_ATOL = 1e-10


@dataclass(frozen=True)
class SelectionResult:
    """Selection outcome and all evaluation work needed to obtain it.

    ``candidate_models`` is the set sent to exact fallback, or the sole early
    winner.  ``exact_pr`` contains only actual fallback evaluations.
    ``certified_unique_widths`` sums unique widths separately for each model.
    ``certified_curve_evaluations`` also includes evicted endpoint recomputation.
    """

    selected: tuple[str, ...]
    early_winner: bool
    candidate_models: tuple[str, ...]
    pruned_models: tuple[str, ...]
    exact_fallback_count: int
    certified_evaluations: int
    certified_curve_evaluations: int
    certified_unique_widths: int
    total_models: int
    bounds: dict[str, CertifiedVUSResult]
    exact_pr: dict[str, float]
    prune: bool
    atol: float
    order_margin: float = ORDER_MARGIN
    tie_atol: float = TIE_ATOL
    ordering_scope: str = "numerically_audited_not_formal_float_certification"

    @property
    def candidate_count(self) -> int:
        return len(self.candidate_models)


def _screen(bounds: Mapping[str, tuple[float, float]], prune: bool):
    """Apply only the ordering policy to lower/upper pairs, deterministically."""
    names = tuple(sorted(bounds))
    for name in names:
        lower = bounds[name][0]
        if all(lower > bounds[other][1] + ORDER_MARGIN for other in names if other != name):
            return name, (name,)
    if not prune:
        return None, names
    maximum_lower = max(bounds[name][0] for name in names)
    candidates = tuple(name for name in names
                       if not bounds[name][1] < maximum_lower - ORDER_MARGIN)
    return None, candidates


def _tied_winners(exact_pr: Mapping[str, float]) -> tuple[str, ...]:
    maximum = max(exact_pr.values())
    return tuple(sorted(name for name, value in exact_pr.items()
                        if maximum - value <= TIE_ATOL))


def select_pr_model(
    y,
    scores_by_model: Mapping[str, object],
    max_buffer,
    *,
    atol=0.01,
    prune=True,
    exact_evaluator: Callable = sparse_vus,
) -> SelectionResult:
    """Select the highest pinned VUS-PR, retaining all exact-tolerance ties.

    Every model first receives ``certified_vus(..., atol=atol)``.  A model
    wins early only if its PR lower bound exceeds every other upper bound
    plus ``3e-10``.  Otherwise, ``prune=True`` discards models whose upper
    bound is strictly below the largest lower bound minus ``3e-10``.
    All surviving models receive the provided exact evaluator.  The returned
    tuple contains every exact value within ``1e-10`` of the exact maximum.

    ``prune=False`` is an ablation: the early-winner rule is unchanged, but an
    unresolved comparison evaluates every model exactly.  Input and result
    order is lexicographic by string model identifier.

    The default exact evaluator is the package's NumPy ``sparse_vus``.  A
    caller may pass ``sparse_vus_jit`` for compiled exact fallback; it must
    accept ``(y, scores, max_buffer)`` and return ``(ROC, PR)`` with the same
    pinned semantics.  All initial preparation and fallback calls happen
    inside this function and must be included in end-to-end timings.
    """
    if not isinstance(scores_by_model, Mapping) or not scores_by_model:
        raise ValueError("scores_by_model must be a nonempty mapping with string model names")
    if any(not isinstance(name, str) for name in scores_by_model):
        raise ValueError("scores_by_model must be a mapping with string model names")
    if not callable(exact_evaluator):
        raise ValueError("exact_evaluator must be callable")
    if not isinstance(prune, (bool, np.bool_)):
        raise ValueError("prune must be a boolean")

    names = tuple(sorted(scores_by_model))
    bounds = {
        name: certified_vus(y, scores_by_model[name], max_buffer, atol=atol)
        for name in names
    }
    pairs = {name: (result.pr_lower, result.pr_upper) for name, result in bounds.items()}
    winner, candidates = _screen(pairs, bool(prune))
    pruned = tuple(name for name in names if name not in candidates)
    exact_pr = {}
    if winner is not None:
        selected = (winner,)
    else:
        for name in candidates:
            value = float(exact_evaluator(y, scores_by_model[name], max_buffer)[1])
            if not np.isfinite(value):
                raise ValueError(f"exact_evaluator returned a nonfinite PR value for {name!r}")
            exact_pr[name] = value
        selected = _tied_winners(exact_pr)
    return SelectionResult(
        selected=selected,
        early_winner=winner is not None,
        candidate_models=candidates,
        pruned_models=pruned,
        exact_fallback_count=len(exact_pr),
        certified_evaluations=len(names),
        certified_curve_evaluations=sum(result.curve_evaluations for result in bounds.values()),
        certified_unique_widths=sum(len(result.evaluated_widths) for result in bounds.values()),
        total_models=len(names),
        bounds=bounds,
        exact_pr=exact_pr,
        prune=bool(prune),
        atol=float(atol),
    )
