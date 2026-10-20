# Incremental PR model racing

This extension was designed after inspecting the fixed-tolerance width
evaluation results. It is a disclosed post-hoc follow-up, with separate source
hashes and measurements. It does not replace those earlier experiments or
their negative results.

Implementation: `src/sparse_vus/racing.py`.
Tests: `tests/test_racing.py`.
The width-enclosure proof and p-box attribution remain in
`docs/theory_advancement_20261020.md`.

## Decision-directed computation

The fixed-tolerance selection pipeline first asks every detector to meet
an absolute tolerance and then may evaluate unresolved models again using
an exact evaluator. The incremental race instead retains one
`PreparedEvaluator` and one PR-width state per detector. It stops when the
model ordering is resolved, without a predetermined scalar-error target.

Initialization queries the endpoints of every merge-free width block.
For model `k`, the state stores:

- exact PR scalars at already evaluated widths;
- a heap of unresolved width interiors, each with valid PR bounds;
- the summed lower and upper contributions of those interiors;
- a bounded endpoint-curve cache inside its prepared evaluator.

For an interior `(a,b)`, its priority is
`(b-a-1) * (PR_upper(a,b)-PR_lower(a,b))`.
Refinement evaluates the previously unseen integer midpoint and replaces
the parent interior with its two children. No score preparation is repeated.
ROC is still computed by the reused endpoint oracle, but ROC uncertainty
never controls the stopping decision or refinement allocation.

After initialization and after every refinement:

1. A model wins by interval separation only when its PR lower bound exceeds
   **every other model's** upper bound plus `3e-10`.
2. With pruning enabled, a model remains competitive unless its upper bound
   is strictly below the greatest lower bound minus `3e-10`.
3. If every competitive model has been evaluated at every width, return all
   exact PR values within `1e-10` of their maximum.
4. Otherwise refine the competitive nonexact model with the widest global
   PR interval. Ties use lexicographic model order.

`prune=False` retains the same separated-winner check, but keeps every model
competitive when that check fails. This is the pruning ablation.

Screening takes linear time in the number of models. Any separated winner
must have the greatest lower bound: a model with a smaller lower bound
cannot exceed the greater-bound model's upper bound. Thus only the model
with the greatest lower bound needs to be checked against all competitor
upper bounds.

## Correctness and finite exact resolution

Write `V_k` for the exact pinned VUS-PR and `[l_k,u_k]` for a model's current
real-arithmetic enclosure.

**Separated winner.** If `l_k > u_j + 3e-10` for every `j != k`, then
`V_k - V_j > 3e-10`. Hence no other model is within the `1e-10` exact-tie
tolerance, and the correct selected set is the singleton `{k}`.

**Pruning.** If `u_j < max_k l_k - 3e-10`, some model has true PR exceeding
`V_j` by more than `3e-10`. Since the global maximum is at least that model's
value, `j` cannot be in the final `1e-10` tie set. This remains true if the
model that supplied the lower bound is later surpassed.

**Exact resolution.** Every active heap item represents a nonempty integer
interior disjoint from all other active interiors. Its midpoint has not
previously been evaluated. Every successful refinement therefore adds
exactly one unique width. With `M` models and `N=L+1` widths, there are at
most `MN` unique evaluations. If no singleton separates, repeated refinement
eventually makes every remaining candidate exact. Their scalar PR means are
computed from the already observed widths using `math.fsum`; no second
exact evaluator or second preparation is required. The exact tie rule then
terminates the algorithm. A valid lower/upper collection cannot eliminate
every candidate.

These statements assume the real-arithmetic width enclosures. Float64
execution retains the existing `1e-12` empirical guard and `3e-10` ordering
margin. Neither is a proved directed-rounding error bound. The implemented
ordering is **numerically audited**, not a formal machine-arithmetic
certificate or a statistical claim about detector quality.

## Work accounting and interface

```python
from sparse_vus.racing import race_pr_models

result = race_pr_models(labels, scores_by_model, max_buffer=300)
result.selected
result.bounds["model_name"].pr_lower
result.bounds["model_name"].pr_upper
result.total_unique_widths
result.total_curve_evaluations
result.refinement_steps
result.exact_pr
```

Model keys must be strings and are processed lexicographically. The result
records both unique width queries and actual curve computations, including
recomputation after cache eviction. The accounting identity is

\[
\text{total unique widths}
=\text{initial unique widths}+\text{refinement steps}.
\]

With the default eight-curve cache, a refinement computes its midpoint and
at most two evicted endpoint curves. Thus actual curve computations are at
most initial curve computations plus three times the number of refinements.
This is an operation-count statement, not an elapsed-time result.

`exact_pr` includes every fully evaluated model, including an excluded
model if it was completed before exclusion. `full_evaluation_count` is its
size. `early_winner` identifies the interval-separation return path; it does
not itself imply that fewer widths were evaluated, because separation may
also occur after full evaluation.

If `m_k` widths are queried for model `k`, endpoint work is
`O(sum_k m_k Q)`, plus one existing sparse preparation per model.
Heap maintenance adds `O(T log(L+1))` and model screening adds `O(MT)`,
where `T` is the number of refinements. Retained endpoint arrays use a
constant number of curves per model, while heap entries and exact scalar
values use `O(sum_k m_k)` space. There is no width-by-support matrix.

No favorable query or runtime bound is asserted for close detector scores.
Ties, small score gaps, dense support, many merge blocks, and certificate
overhead can force full evaluation or make racing slower. Controlled
measurements must include initialization, all preparations, all refinements,
and any repeated endpoint calculations.

## Validation scope

The new tests cover:

- each refinement adds one unseen width and maintains an exact-value enclosure;
- separated models stop at initial endpoints;
- exact tied models reuse accumulated width values;
- pruning and no-pruning return the same tie set with different work;
- width-zero and merge-boundary initialization;
- 40 seeded comparisons against existing exact evaluation of every model;
- insertion-order independence and linear-screening policy equivalence.

These are numerical implementation checks. The independent racing audit
additionally compares model orders and reported work against exact all-model
evaluation. Test and benchmark receipts establish the executed scope; this
document alone does not claim that an unexecuted check passed.
