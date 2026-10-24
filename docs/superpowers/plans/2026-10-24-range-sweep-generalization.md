# Exact range-metric sweep: falsifiable generalization study

Status: exploratory successor, 2026-10-24. Earlier VUS protocols, results and reviewer decisions remain immutable. User authorized continuation toward a substantively stronger research result.

## Motivation and boundary

Three independent final assessments of the 11-page VUS manuscript are Accept 7, Revise 5, Reject 5 on internal surrogate scales. All requested evidence exists, but representation significance is disputed. The public nine-metric consumer gained only 1.031x. An exploratory breakdown of that same input found Affiliation 18.37s, PA-F1 3.44s, range-F1 3.09s and event-F1 2.06s. This is not a population timing estimate. Range-F1 is a tractable additional operator, not the largest bottleneck and not an excuse to claim a large whole-consumer gain.

## Hypothesis and three methods

For flat positional weights and reciprocal cardinality, exact range precision/recall can be maintained across descending score activations. Predicted intervals are disjoint components. Fixed true intervals maintain active mass and intersecting predicted-component count. Only an activation's own true interval changes those counts. Component precision is recoverable from fixed prefix arrays. Union-find therefore supports all thresholds in O(n log n + n alpha(n) + H) when requested thresholds are sorted; arbitrary query order additionally costs O(H log H). Standard union-find and sorting are credited, not claimed invented.

1. Vectorized prefix/interval evaluation independently recomputed per threshold.
2. Compiled linear raster per threshold, with shared preprocessing and no Python interval membership bottleneck.
3. Compiled incremental component sweep, with the same preprocessing and numeric domain.

Measure all three; do not use Python-vs-JIT speed as the algorithmic claim. Public TSB-AD, aeon and other closest code are separately screened. Run exhaustive short tie/boundary tests before timing. Standard mathematical semantics and TSB-AD compatibility (all-one range parser) are explicit. Full distinct thresholds and public 100 evenly spaced thresholds are separate contracts. All-threshold maximum is an oracle evaluation, not a deployable anomaly threshold learned without labels.

## Stages and decision

- [ ] Independent mathematical and prior-code feasibility reviews.
- [ ] Three implementations plus independently computed oracle checks.
- [ ] Freeze protocol and source hashes before 73-case NAB/SMAP/SMD outcomes; reuse is explicit, no held-out generalization claim.
- [ ] Compare grid-100 runtime/parity and exact all-threshold runtime against compilation-matched linear baseline; complete all 584 profiles and retain losses. Paired collection-level uncertainty; disclose SMD label dependence.
- [ ] Measure grid-vs-full metric and selection changes without counting them as detector improvements.
- [ ] Review substantive novelty, complexity, real effect and venue significance; keep the current VUS manuscript separate unless evidence supports a coherent revised research story.

A positive speed result alone is insufficient for a new archival contribution. A pre-existing equivalent implementation defeats a novelty claim. A loss against the compiled baseline defeats acceleration at that threshold count. No fixed 5/6-point score is awarded before these checks.


## Pre-timing design refinements

Independent review removed unnecessary union-find: active neighbors of an inactive
point are current component endpoints, so endpoint arrays give O(1) merges and O(n)
activation work. A fourth method, exact query bucketing, assigns points to their
first strictly eligible threshold by binary search and counting buckets. With
ordered queries it costs O(n log(H+1)+n+H); arbitrary query order additionally
costs O(H log(H+1)). The raster baseline is fused, with O(1) reducer workspace,
no per-threshold K arrays, and no unused prefix preparation. All public-query and
all-observed-threshold domains are distinguished from the all-mask optimum.

Before timing the four implementations passed the independent set-overlap oracle
on exhaustive tied short inputs plus randomized alpha/query order/boundary cases.
The frozen main study retains canonical complete curves for each method and every
repeat's output hash. Eight balanced cyclic/reverse grid orders and two AB/BA
all-observed-threshold orders are used. All controls are retained regardless of loss.

The first public-comparator protocol was never executed. Before any public timing,
v2 added a60-second per eight-profile public API-call limit. Any timeout remains
an explicit censored lower bound and is not a parity success or an excluded case.
The fixed external panel is the three shortest recordings per collection, all eight
profiles. Its length selection limits generalization; the compiled panel uses all73.
