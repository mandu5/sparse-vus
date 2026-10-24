# Independent feasibility review: exact threshold sweeps for range PR/F1

Date: 2026-10-24, evidence inspected through 03:49 UTC. Reviewer: independent theory reviewer. This is an exploratory review of a new hypothesis, not a reassessment of the frozen PVLDB paper. No other internal reviews or scores were read. No publication score is assigned and no previous gate judgment is changed.

**Finding: the proposed update rules are mathematically valid for the stated one-dimensional, flat, reciprocal-cardinality metric. Union-find is unnecessary: endpoint bookkeeping gives constant work per point activation after ordering. The principal unresolved objection is scientific novelty and practical significance, not a counterexample to these invariants.** An existing public implementation already computes the same family of all-observed-threshold range F-scores; the defensible candidate improvement is avoiding repeated evaluation. Faster execution of the complete consumer remains an empirical question.

## 1. Precisely defined target

Let `y[0:n]` be binary labels, with `n >= 1`. Let the true intervals `I_j=[a_j,b_j]` be the disjoint maximal runs of ones, and let `K` be their number. Their lengths are `ell_j=b_j-a_j+1`. Scores are finite ordered numbers; NaN handling is outside this theorem. For a threshold `t`, the predicted mask is `p_i(t)=1{s_i>t}`. Its maximal connected intervals on the path are the predicted components `C`.

For each true interval maintain

\[
m_j=\sum_{i\in I_j}p_i,
\qquad
r_j=\#\{C:C\cap I_j\ne\varnothing\}.
\]

Define `u_j=0` when `m_j=0`, and otherwise `u_j=m_j/(ell_j*r_j)`. For a fixed `alpha` in `[0,1]`, the target recall is

\[
R=\frac{\alpha E+(1-\alpha)U}{K},\qquad
E=\sum_j\mathbf1\{m_j>0\},\quad U=\sum_j u_j.
\]

For a predicted component `C=[l,r]`, define `z(C)=sum_{i=l}^r y_i` and `d(C)=#{j:I_j intersects C}`. Its precision contribution is

\[
q(C)=\begin{cases}
z(C)/((r-l+1)d(C)),&d(C)>0,\\
0,&d(C)=0.
\end{cases}
\qquad
P=\frac{S}{B},\quad S=\sum_C q(C),\quad B=\#\{C\}.
\]

All predicted components, including components with no true points, count in `B`. This is the unweighted mean over ranges, not ordinary point precision. Set `R=0` for `K=0`, `P=0` for `B=0`, and `F1=0` if `P+R=0`; otherwise `F1=2PR/(P+R)`. Other empty-case conventions require explicit adapters. `F_beta` follows by its usual scalar combination after obtaining `P` and `R`.

These are specializations of the existing Tatbul et al. range metric, with flat positional weight and reciprocal cardinality. The metric itself is not new. [Tatbul et al., NeurIPS 2018, Sections 4.1–4.3](https://proceedings.neurips.cc/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf)

The inspected public-consumer source uses `alpha=.2`, unweighted range precision, and the maximum over exactly 100 `np.linspace(min(score), max(score), 100)` thresholds with strict `>`. Replacing that maximum with a maximum over all distinct scores changes the objective. The local source inspected was `.cache/tsbad-consumer/pkg/TSB_AD/evaluation/basic_metrics.py`, SHA-256 `1fcddedf5ada1d5221f39ee568c7fddb9e7181bd7e1c19636c2cbecf40c97707`. Its relevant RF1/range routines agree in mathematical structure with the separately inspected [upstream source at commit 303dffb](https://github.com/TheDatumOrg/TSB-AD/blob/303dffbfc11612995b17b06633f8c9d0ea0e38e5/TSB_AD/evaluation/basic_metrics.py). I do not assert whole-file byte identity between those two files.

## 2. Recall update: proof and necessary qualification

Consider activating a previously inactive point `x`. If `y_x=1`, let `j` be its unique true interval. Write

\[
L_j=\mathbf1\{x>a_j\text{ and }p_{x-1}=1\},\qquad
R_j=\mathbf1\{x<b_j\text{ and }p_{x+1}=1\}.
\]

Then the exact update is

\[
m_j\leftarrow m_j+1,\qquad r_j\leftarrow r_j+1-L_j-R_j.
\]

All other true intervals retain both counts. If `y_x=0`, all true-interval counts remain unchanged.

Proof: intersecting any predicted interval with `I_j` yields either an interval or the empty set. Two disconnected active subintervals inside `I_j` cannot belong to one globally connected predicted component: the path between them lies inside `I_j`. Thus `r_j` is exactly the number of runs of active points inside `I_j`. Adding `x` creates one such run, except that each already-active neighbor inside `I_j` connects to it and removes one run boundary. The two old neighbor components are distinct because `x` was inactive. This gives the update for zero, one, or two active internal neighbors. For every other true interval, the restricted active mask is unchanged. Equivalently, two components can both intersect a single true interval across a newly joined edge only when that edge lies inside that interval.

The wording “a union reduces `r_j` when the union boundary is inside `I_j`” is correct only with the singleton-creation update included and only for a union of previously distinct active components. The displayed combined formula avoids those ambiguities. An active neighbor outside `I_j` must not decrement `r_j`.

To update recall, subtract the old `u_j` from `U`, perform the combined count update, add the new `u_j`, and increment `E` exactly when the old `m_j` was zero. There is at most one affected true interval per activation. The invariant `r_j>0` iff `m_j>0` prevents division by zero.

## 3. Precision from prefix counts

Precompute the true-point prefix count `Y(t)=sum_{i<t}y_i` and the true-start prefix count `A(t)=#{j:a_j<t}`. For any nonempty interval `[l,r]`,

\[
z([l,r])=Y(r+1)-Y(l),
\qquad
d([l,r])=y_l+A(r+1)-A(l+1).
\]

The second identity counts the true interval covering `l`, if one exists, plus every true interval starting strictly after `l` and no later than `r`. These categories are disjoint and exhaustive. Counting only starts in `[l,r]` is wrong: a component `[1,1]` intersects the true interval `[0,2]` even though it contains no true start.

Activating `x` removes zero, one, or two old adjacent components and replaces them with one merged interval. Subtract their `q` contributions from `S`, add the new interval's contribution, and update

\[
B\leftarrow B+1-\mathbf1\{p_{x-1}=1\}-\mathbf1\{p_{x+1}=1\},
\]

with out-of-bounds neighbors treated as inactive. Each component contribution is available in constant time. A new false point can change precision even though it changes no recall count.

No set of intersected true-interval identifiers needs to be maintained inside a component. The contiguous-interval geometry and prefix identity eliminate that potentially expensive set-union operation.

## 4. Endpoint variant: union-find is unnecessary

Keep `left_at_right[r]=l` and `right_at_left[l]=r` for each active component `[l,r]`, together with an active-point mask. For a previously inactive `x`, an active `x-1` must be the right boundary of its component; an active `x+1` must be the left boundary of its component. Therefore the old component endpoints can be retrieved directly:

```
left  = left_at_right[x-1] if x-1 is active else x
right = right_at_left[x+1] if x+1 is active else x
remove contributions of the old left/right components, if present
activate x and update its true-interval counts
add the contribution of [left, right]
left_at_right[right] = left
right_at_left[left] = right
```

Old entries at interior points can remain stale. Such a point can never again be queried as the boundary adjacent to an inactive point: activation is permanent, so an interior point always retains its active immediate neighbors. Inductively, all entries actually queried are current. No `find`, path compression, component scan, or amortized inverse-Ackermann argument is needed on a path.

This invariant supports arbitrary activation orders. Descending score order is required only to identify valid threshold states; it is not required by the component bookkeeping itself. That distinction gives the fixed-query corollary below.

## 5. Exact threshold semantics and complexity

Let `D<=n` be the number of distinct scores. After sorting scores in descending order, process each equal-score group atomically with respect to observations. At `t=v`, the strict mask excludes every point with score exactly `v`, so report that threshold **before** activating its group. Equivalently, for a descending sequence of query thresholds, activate all points with `score > query` before answering each query. Intermediate states inside a tied group are not realizable threshold masks and must never enter the maximization.

There are `D+1` distinct masks over all real thresholds, including the all-active state at `t<min(score)`. Evaluating only thresholds equal to observed scores produces `D` masks and omits that state. A declared all-real-threshold objective must include it; a compatibility objective may intentionally omit it. The empty state is present at `t>=max(score)`.

With constant-cost arithmetic and explicit input/output costs:

| Task | Time | Additional storage, excluding input |
|---|---:|---:|
| Score-sorted DSU sweep, `H` already ordered queries | `O(n log n + n alpha(n) + H)` | `O(n+H)` if results retained |
| Score-sorted endpoint sweep, `H` already ordered queries | `O(n log n + n + H)` | `O(n+H)` if results retained |
| All distinct-score states, endpoint sweep | `O(n log n+n)` | `O(n)` |
| Fixed ordered query set, endpoint buckets described below | `O(n log(H+1)+n+H)` | `O(n+H)` |

Retaining only a maximum rather than the output curve removes storage proportional to the curve length. The `O(n)` work includes validation, true-range construction, prefix counts, endpoint arrays, and at most `n` activations. These bounds are not claims of bit-linear exact-rational arithmetic.

**Fixed-query corollary.** If only `H` ordered thresholds are required, full score sorting is unnecessary. For each point, binary-search the first descending query `t` with `t < score`, and put the point into that query's bucket; omit points that satisfy no query. Process buckets in query order, activating all their points before reporting. Any order within a bucket gives the same final mask. A head array of length `H` and next-pointer array of length `n` suffice. The inequalities must use the actual query values: approximate arithmetic binning can change masks near a threshold. This is ordinary offline query bucketing, not a separate novelty claim.

For arbitrary unordered thresholds, charge their sorting (`O(H log H)`) and restore the requested output order; alternatively build the full state curve and pay predecessor-query costs. The unqualified `+H` bound is false for arbitrary unordered real queries in a comparison model without suitable preprocessing or an ordering promise.

For a constant `H=100`, an optimized raster costing `O(nH)` is already linear in `n`; the sorting-based sweep has no superior asymptotic dependence on `n` in that regime. Bucketing avoids the full sort but still offers no hardware-independent constant-factor guarantee. A compiled raster/prefix baseline remains essential.

## 6. Counterexamples to broader or careless claims

These are exact hand-checkable witnesses, not failures of the qualified algorithm.

| Claim to reject | Witness and consequence |
|---|---|
| Only true-support score events matter | `y=[1,0,1]`, `p=[1,0,1]` gives `P=R=1`. Activating the false middle point gives one component with `z=2`, length `3`, and `d=2`: `P=1/3`, `R=1`, `F1=1/2`. All off-truth events cannot be discarded. |
| Recall must increase as the threshold decreases | For `y=[1,1,1,1,1,0]`, change `p=[1,1,0,0,0,0]` to `[1,1,0,0,1,0]`. Overlap recall falls from `2/5` to `3/10` because cardinality rises from one to two. At `alpha=.2`, recall falls from `.52` to `.44`. |
| Unmatched predicted ranges can be omitted from the precision mean | `y=[1,0,0]`, `p=[1,0,1]`: the two contributions are `1` and `0`, so `P=1/2`, not `1`. |
| Tied points can be evaluated one at a time | For `y=[1,0]`, equal scores admit only empty/full masks over real thresholds. Reporting the intermediate mask `[1,0]` creates an unattainable perfect score. |
| All-threshold optimization preserves the public 100-grid objective | With constant scores, every public grid query produces the empty mask. Canonical all-real-threshold optimization also includes the full mask, which can have a positive F1. |
| Prefix counts of starts alone give intersection cardinality | True interval `[0,2]`, predicted interval `[1,1]`: start count inside the prediction is zero but intersection cardinality is one. |

In particular, this method does **not** inherit a bound depending only on anomalous support from the VUS support-event argument. Worst-case all-point score events matter. Reciprocal-cardinality recall is nonmonotone, so conventional monotone PR-curve integration, early stopping, or an AUC interpretation does not follow from this theorem. A curve integration rule would need its own specification.

## 7. Public parser compatibility must be a separate contract

The inspected TSB-AD parser detects starts/ends through changes in the binary vector; an all-one vector has neither and becomes an empty range list. This is a public implementation quirk, not the canonical definition of a maximal positive run. The relevant routines were inspected locally and in the linked upstream source.

The consequences follow directly by substituting that parser behavior into the inspected formulas:

* If the true labels are all ones, the public range recall is zero because its true-range list is empty. Public range precision is also zero: when predictions contain ranges, their overlap cardinality with the parsed true ranges is zero. Thus public RF1 is zero for every prediction mask. The canonical metric generally differs.
* If true labels contain both classes and predictions are all ones, public precision is zero. Public recall is `alpha`, because existence is detected from the prediction vector while overlap cardinality uses the empty parsed prediction list. Setting both recall and precision to zero would match RF1 but would not reproduce the raw recall API.
* For an all-zero true vector, the stated zero-denominator convention gives zero metrics. A different library can choose otherwise.

The public strict min-to-max grid never produces an all-one prediction mask, but all-real-threshold evaluation introduces it. This makes the compatibility decision necessary before broadening the threshold domain. Keep a named canonical mode and a pinned public-compatibility mode; do not silently present a parser correction as numerical equivalence. Endpoint maintenance itself can remain canonical, with explicit output adapters for these exceptional states.

## 8. What is already prior work

**Existing metric and exhaustive-threshold objective.** TimeSeAD's public `best_ts_fbeta_score_classic` already uses reciprocal cardinality and unweighted precision at every distinct observed-score threshold. Its helper rebuilds an `n`-point strict-`>` mask and calls the metric inside the threshold loop, establishing `Omega(nD)` mask work in that implementation. The candidate sweep removes repeated work; it does not introduce all-threshold range F1. Matching requires `alpha=0` for this wrapper, while the public consumer uses `.2`. The wrapper also omits the all-active state. Source pin: `bb8efa9ce17f9cfb0bab77df08c32d986de8429e`, commit date 2025-06-10. [TimeSeAD evaluator, lines 207–278](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/evaluator.py#L207)

TimeSeAD separately exposes the flat metric primitive and treats simultaneously empty labels/predictions as `P=R=1`. Its source explicitly identifies the reciprocal-cardinality recall inconsistency and offers a different cardinality function. These are semantic differences, not numerical tolerances. The inspected wrapper also stores intermediate metric values in `torch.float` arrays; an equality claim must account for that rounding. [TimeSeAD range metric source](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/ts_precision_recall.py)

**Existing threshold-component machinery.** Descending superlevel sets and union-find maintenance of connected components are classical component-tree algorithms. Najman and Couprie describe a quasi-linear union-find construction on general symmetric graphs. Specializing connectivity to a path and using interval endpoints should receive ordinary data-structure attribution, not be sold as a new union-find or filtration method. [Najman and Couprie, IEEE TIP 2006, DOI 10.1109/TIP.2006.877518](https://doi.org/10.1109/TIP.2006.877518); [author-affiliated publication record and abstract](https://cris.technion.ac.il/en/publications/building-the-component-tree-in-quasi-linear-time/)

**Residual candidate contribution.** The meaningful proposition is that these established range scores admit constant-size local updates under path activation, including the reciprocal true-range cardinality term and the per-predicted-component mean. This is a concrete distinction from the inspected repeated-threshold source. However, the proof is short once the score is expressed through interval counts, and the endpoint structure is elementary. A reviewer can reasonably judge it an obvious specialization of standard sweep/component techniques. Demonstrating a large speedup over Python membership loops would not answer that objection.

I searched for combinations of range precision/recall/F1 with incremental, threshold sweep, and union-find terms. I did not find a directly matching incremental range-score algorithm in that bounded search. That is not a priority proof or a comprehensive novelty clearance. The TimeSeAD paper's publication metadata/search excerpt was accessible, but opening its final OpenReview PDF reached a browser challenge; I do not claim to have read that final paper or its reviews during this feasibility task. The algorithmic comparison above rests on the inspected pinned primary code, not on an unavailable manuscript. The component-tree HAL/author PDF retrieval also failed; only the primary publication record/abstract was used for that attribution.

## 9. Scope, arithmetic, and falsifiable next conditions

The proof assumes a one-dimensional path, disjoint maximal binary true intervals, permanent activation, flat weights, reciprocal cardinality, and the explicitly stated averaging conventions. It does not prove correctness for overlapping event annotations, arbitrary graphs, gap-tolerant event merging, time-dependent labels, buffer-dependent VUS, affiliation metrics, or arbitrary positional biases. Overlapping annotations can make one activation affect many true intervals. A general graph removes both the endpoint invariant and the interval argument for local recall changes.

There is a limited algebraic extension: if each fixed-true-range contribution is a constant-time function of `(m_j,r_j,ell_j)` and each predicted-range contribution is a constant-time function of its endpoints and available prefix summaries, the same maintenance argument applies. This is a conditional corollary, not evidence that every existing metric has such summaries. It also does not establish that a changed cardinality/averaging policy is equivalent to the public consumer.

Mathematical exhaustiveness is separate from floating-point equivalence. Updating `S` and `U` by additions/subtractions changes summation order and can accumulate cancellation error. The proof neither guarantees bitwise agreement with a raster nor a fixed absolute error bound for arbitrary length. Near-equal maxima can change the selected threshold under rounding. A claimed exact implementation therefore needs a declared numerical contract, direct value checks, and a stated argmax tie policy. If bit-exact rational arithmetic is intended, denominator/bit-growth costs must be charged instead of the unit-cost arithmetic bound.

Before treating this as a successful research extension, the following conditions are falsifiable and necessary:

1. **Same target:** compare every requested PR/F1 value against a literal pinned reference with matching `alpha`, threshold values, strictness, empty cases, parser mode, and tie policy. Test full-real-threshold, observed-threshold, and fixed-grid objectives separately.
2. **Strong baselines:** include the actual public consumer, TimeSeAD's matched classic target, an optimized compiled `O(nH)` raster, and the prefix approach. Include sorting/bucketing, validation, allocation, and conversion in the end-to-end time. Report the fixed-100-query and large-`D` regimes separately.
3. **Mechanism attribution:** separate removing Python membership/range loops, compilation, prefix counting, and cross-threshold reuse. The question is how much the sweep adds beyond a compiled direct implementation.
4. **Practical importance:** profile RF1's share of the unchanged nine-metric workflow and measure the entire workflow after replacement. Isolated RF1 speedup does not imply substantial total speedup. Record regressions and the crossover with `n`, `H`, ties, event lengths, and fragmentation.
5. **Novelty clearance:** inspect TimeSeAD and other primary range-metric implementations and the relevant threshold/component literature beyond the bounded search here. A demonstrated preceding equivalent sweep defeats a first-algorithm claim even if the new code is faster.

As a small independent check, I exhaustively verified the local count/precision identities for every binary label vector, active mask, and inactive-point transition through `n=6` using exact `Fraction` arithmetic (15,474 transitions). I also checked endpoint invariants for every activation permutation through `n=7` (40,319 activation events). Both checks passed. These finite checks corroborate the written proof; they are not production implementation validation, timing evidence, or a publication result. No source implementation was modified or benchmarked for this review.

**Feasibility recommendation:** proceed to a bounded, matched implementation experiment. Confidence is high in the qualified theorem and endpoint simplification; confidence that the idea is an independently novel, publication-significant contribution is presently low. The strongest objection that survives is that this may be an elementary and useful application of established threshold-component machinery, with little incremental benefit over a compiled raster in the actual fixed-grid consumer. The experiment and prior-art comparison must be allowed to falsify that research direction.
