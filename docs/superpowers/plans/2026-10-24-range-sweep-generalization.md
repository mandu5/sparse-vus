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

- [x] Independent mathematical and prior-code feasibility reviews.
- [x] Four implementations plus independently computed oracle checks.
- [x] Freeze protocol and source hashes before 73-case NAB/SMAP/SMD outcomes; reuse is explicit, no held-out generalization claim.
- [x] Compare grid-100 runtime/parity and exact all-threshold runtime against compilation-matched linear baseline; complete all 584 profiles and retain losses. Paired collection-level uncertainty; disclose SMD label dependence.
- [x] Measure grid-vs-full metric and selection changes without counting them as detector improvements.
- [x] Review substantive novelty, complexity, real effect and venue significance; keep the current VUS manuscript separate unless evidence supports a coherent revised research story.

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
v2 added a 60-second per eight-profile public API-call limit. Any timeout remains
an explicit censored lower bound and is not a parity success or an excluded case.
The fixed external panel is the three shortest recordings per collection, all eight
profiles. Its length selection limits generalization; the compiled panel uses all 73.

## Completed local evidence and remaining validation

The frozen source produced all 2,628 complete eight-profile calls, with all
canonical PR/recall/F1 curves retained. The independent curve reconstruction
reports maximum discrepancy 2.998e-15 and no cross-method model-winner change.
Against the fused compiled raster, the exhaustive sweep has collection case
geometric speedups 27.802 / 21.441 / 128.081; the three adjusted lower bounds
are 18.735 / 8.572 / 95.087. One low-distinct SMAP case loses (0.417 ratio).
For the public 100-query contract, bucketing wins all 73 case medians, with
collection ratios 1.719 / 1.994 / 1.969. Thus sorting, query bucketing and the
conventional scan have measured, distinct operating regimes.

Changing grid100 to exact observed thresholds changes 24/73 winning sets;
15 have no overlapping winner, and 12 have optimistic tie-aware regret >=.01.
The maximum regrets are .439/.150/.127. These are oracle metric-selection
effects on the reused panel, not new detector accuracy.

The public panel completes 72 recorded calls, including two explicit 60-second
TimeSeAD censorings on SMD187. Completed public scalar discrepancies are
6.66e-16 for TSB-AD grid100 and 5.65e-8 for TimeSeAD's float32-output classic
contract. Public-library speedups include interpreter/implementation effects;
the compiled raster comparison supports the algorithmic claim. Validation
also checks 1,168 recorded maximizing cuts against unchanged TSB-AD and three
one-million-point numerical stress cases, all within predeclared tolerances.

The combined manuscript is `paper/exact_metrics_pvldb20261024.pdf`, preserving
the old VUS-only PDF. Three new independent calibrated manuscript assessments
are in progress. Fresh Linux range-only execution (40061935240) and a separately
launched combined one-command VUS+range execution (40062043152) are in progress;
neither has been reported as complete at this checkpoint. No new score is
awarded from a pending run.

## Final closure, 05:22 UTC

The preceding paragraph records the earlier cutoff, not the final state.
Canonical combined run 40062043152 completed successfully at 05:07:05 UTC from
e2405e39ec23486a3d228240569b48785de32cb4. It executed VUS primary/supplement and
range main/public/validation using one fresh set of generated scores. The archive
digest matches GitHub; 568 retained scientific files include all inputs and
canonical curves. Four local saved-record reconstructions exactly equal the
archived reports. The blinded reviewer independently repeated those four audits
and obtained byte-identical outputs as well. The auxiliary range-only run is
separate; the combined run was selected before timing-report inspection.

On canonical AMD EPYC 7763, exhaustive raster/sweep ratios are 29.348 / 27.764 /
163.597, with adjusted lower bounds 18.809 / 11.632 / 125.923. Grid raster/bucket
ratios are 1.900 / 2.898 / 3.574. The low-cardinality loss and two public-call
censorings remain. Score matrices differ across hosts; two SMD selection
indicators exchange despite equal aggregate 24/15/12 counts. The manuscript
reports the original and Linux results separately.

Three completed independent AI reviews of the final combined manuscript return
Weak Accept 7 / Weak Accept 6 / Accept 7 on internal surrogate scales. Each
supports the prospective substantive-generalization route and states that their
own review has no remaining major scope/novelty/baseline/validity objection to
the narrowed claim. The reviewer scores are not coordinated or converted into
acceptance odds. All six evidence gates and the prospective investment-6 route
are now supported. The original SMD 1.207 batch-route failure and 1.031 whole
consumer result remain unchanged.

The final PDF SHA-256 is
6646c1f497273f2e4731d158761568c26b7cf04b3b06978813aa1962518e3a11,
13 total pages with references beginning on page 12. All pages were rendered
and inspected. The final result ledger is `docs/EXACT_METRICS_RESULT_20261024.md`.
The current milestone is complete; future broader scope or actual external
acceptance is a distinct milestone, not implied by this closure.
