# Research direction audit: sampling, semantic portability, and decision fidelity

Date: 2026-10-23. This is a new literature/design audit, not a completed experiment, external review, or acceptance prediction. Inspected current `paper/sparse_vus_body.tex`, the earlier `paper/main.tex`, and `docs/active_prefix_novelty_audit_20261023.md`; browsed the primary sources linked below. No code, data, manuscript, or frozen result was changed.

## Recommendation

The strongest attainable extension is **one exact support-event calculus for explicitly different published VUS contracts, coupled to a fresh multi-detector study that separates semantic disagreement from threshold approximation**. Keep the existing original-target speed result; demonstrate that its central representation generalizes beyond that one contract, and measure the downstream decisions for which exact evaluation matters. A subsequent theory-agent finding adds a stronger central failure mechanism: sampled PR can be severely inflated by soft-label mass admitted after exact recall saturation. The focused novelty search for that finding is recorded below.

Do not promote another synthetic sampling counterexample as the needed advance. The earlier `paper/main.tex` already proves near-unit fixed-grid PR error for every fixed maximum width and reports 84/2,100 pair reversals, only five with both gaps at least 0.01. The original Go semantic audit is also already in `artifacts/native_go_audit.json`. Those are prior project results. Repeating them cannot resolve the significance objection.

A new same-transcript impossibility result can sharpen the sampling argument, and a mass-based certificate can support a safe fallback. Neither, by itself, makes this a substantially stronger paper. Broad useful effect sizes, native-contract correctness, and competitive complete costs are the decisive new evidence.

## Primary-source boundary

| Source inspected | Relevant established result | Consequence |
|---|---|---|
| [Boniol et al., final VLDBJ 2025 paper](https://www.paparrizos.org/papers/BoniolVLDBJ25.pdf) | Defines and evaluates VUS, compares measures, and supplies two optimized implementations with static/dynamic region reuse. | Neither fast VUS nor the idea that metric choice changes conclusions is new. The inspected algorithms retain threshold-wise support work; a reusable compressed event representation remains a distinct candidate. |
| [Klein fast-VUS source](https://github.com/tomlouisklein/fast-VUS/blob/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py) and [repository](https://github.com/tomlouisklein/fast-VUS) | Global rank sampling defaults to 250; weighted cumulative sums remove threshold-wise dot products. Its claimed exactness is equality to the reference at the same configured threshold grid. | Compare `H=n` to exhaustive results, and default 250 separately on the accuracy/cost frontier. Do not portray the repository's stated sampled-reference equivalence as a false exactness claim. |
| [TimeEval 1.5 documentation](https://timeeval.readthedocs.io/en/latest/api/timeeval.metrics.html#timeeval.metrics.RangePrAUC) | Explicitly documents different overlap combination, existence counting, slope symmetry, and slope shape; compatibility mode reproduces the authors' implementation. It warns that too few sampled thresholds degrade quality. | Semantic differences and approximation are already acknowledged by a maintainer. The possible new result is their measured decision-level consequences and an efficient common exact engine, not discovering undocumented differences. |
| [FF-VUS NumPy at aVUSi `facf4362`](https://github.com/doanthihoaithu/aVUSi/blob/facf4362092525671215031048a75842b9d6d632/3_metric_calculator/metrics/ffvus/vus_numpy.py), [Torch](https://github.com/doanthihoaithu/aVUSi/blob/facf4362092525671215031048a75842b9d6d632/3_metric_calculator/metrics/ffvus/vus_torch.py), [wrapper](https://github.com/doanthihoaithu/aVUSi/blob/facf4362092525671215031048a75842b9d6d632/3_metric_calculator/metrics/ffvus/ffvus_metrics.py) | Prior audit identifies max-linear ramps, dynamic mass, batching, wrapper rounding, and an optional existence interpolation fallback. Current repository head is still this revision, dated June 23, 2026. | Preserve native semantics. Separate core arithmetic, score rounding, and approximation fallback. A CPU comparison cannot establish GPU superiority. |
| [Sylligardos, VLDB PhD Workshop 2025](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf) | Reports preliminary efficient CPU/GPU evaluation and connects metric evaluation to detector selection. | Large speedups and the evaluation-cost motivation predate this work; no universal fastest-VUS claim follows from the present CPU study. |
| [Go adscore source](https://github.com/stergiotis/boxer/blob/f94098c37d27f8c3db7fd85495c7421e5a069a11/public/analytics/timeseries/adscore/adscore.go), [introducing commit](https://github.com/stergiotis/boxer/commit/11596d8d446a836114ae7237d18469cc6296040d) | July 30, 2026 implementation already uses exact complete-tie dense incremental sweeps. Source has static positive mass, max overlaps, original-range coverage, and trapezoidal PR. | Rank sweeps and complete ties are established software techniques. This source is already audited in the project and computes a different native target. |
| [Keras AUC documentation](https://keras.io/api/metrics/classification_metrics/#auc-class) | Documents potentially poor finite-threshold approximation and minoring/majoring estimates. | Generic warnings about discretization and the general idea of an error interval are not novel. Its interpolation conventions do not automatically prove bounds for unsampled dynamic VUS curves. |
| [Lyu, arXiv:2607.11969v2](https://arxiv.org/html/2607.11969v2) | Audits TSAD metrics across six benchmarks, studies ranking/top-1 changes, and uses VUS threshold resolution 250. The revised paper distinguishes a single random run from best-of-many reporting. | A generic metric-robustness or winner-disagreement study is already occupied. Isolate same-name VUS contracts and computational approximations. Cite v2; v1's headline interpretation changed substantially. |
| [TSB-AutoAD, PVLDB 2025](https://www.vldb.org/pvldb/vol18/p4364-liu.pdf) and [RAMSAD, October 2026 preprint](https://arxiv.org/html/2610.20243v2) | Detector selection uses performance profiles over a broad candidate pool; TSB-AutoAD describes 32 univariate models, and RAMSAD also uses 32. | Three detector vectors are a small practical panel. A frozen panel of at least eight genuinely different detectors is a defensible minimum expansion; released broad detector outputs are preferable where available. |

This search found no paper establishing the proposed complete native-contract event calculus and its decision-fidelity study. This is a scoped negative search result, not proof that no laboratory has done it. Search terms included combinations of VUS, threshold sampling, approximation, ranking stability, semantics, implementation differences, FF-VUS, and precision-recall discretization bounds. Multiclass ROC-surface papers concern a different VUS and must not be presented as TSAD prior algorithms.

## New mathematical extension worth implementing

For each width, fix continuous label weights and the coverage rule. Let the support include **every position that can change any non-count state**, including a coverage-only position if a contract allows one. Between support-score events, weighted true-positive mass, auxiliary positive mass, coverage, recall, and the negative denominator stay constant. Global predicted count changes.

For active complete-score class `j`, retain both global counts `c_j^>` and `c_j^>=`, as well as the old and new states. This allows exact integration of published right-step **and trapezoidal** PR conventions. The latter is not obtained by simply dropping zero-recall increments:

```
right-step active contribution = (R_j - R_prev) * T_j / c_j^>=
trapezoid active contribution  = (R_j - R_prev)
                                * (T_prev / c_j^> + T_j / c_j^>=) / 2
```

The second expression applies when `c_j^> > 0`; handle the contract's initial precision separately. If no inactive group intervenes, `c_j^>` is exactly the preceding event's end count. If inactive groups intervene, their zero recall increments still change the precision used by the next trapezoid. ROC uses the existing horizontal rectangle followed by the active trapezoid. Preserve each contract's terminal point and width averaging convention.

**Minimal counterexample to naive trapezoidal compression.** At width zero, one contiguous original anomaly `y=[1,1,0]`, scores `s=[3,1,2]`, and first-precision origin convention, the full PR trapezoid area is `19/24`. Keeping only active endpoints gives `11/12`, an error of `1/8`. The middle negative has zero recall increment, yet changes the next trapezoid's left precision from `1` to `1/2`. This fixture isolates the correction without ramp or component ambiguity.

The resulting generic theorem should state complexity as `preparation + sum_w support_state_cost(w)`, then instantiate it for specific contracts. Do not assert `O(n+(L+1)Q)` for arbitrary kernels unless their weight and coverage generation has the required cost. Max-combined monotone nearest-interval kernels and the existing clipped square-root geometry are reasonable concrete instances. Original-range coverage, overlapping expanded ranges, and adjacency merging need separate proofs and pinned native comparisons.

This is a candidate new extension of this project's representation. The proof is short; its importance comes from correct reuse across real contracts and the experiment, not from relabeling a standard sweep as a new paradigm.

## A stronger sampling limitation, with a precise information model

### Focused update: overestimation after recall saturation

The theory agent subsequently constructed an additional, qualitatively different failure. In the original dynamic-denominator VUS, a singleton original positive can produce full recall before any buffer position is admitted. Later buffer positions add weighted true-positive mass and can increase precision while exact recall stays one. The exact right-step integral assigns them zero further area. A coarse grid can skip the saturation event and instead assign the entire recall jump to the later, increased precision. This produces overestimation, whereas the earlier project theorem demonstrates underestimation. The parent reports separately verified large-regret constructions at ordinary widths 30, 100, and 300; their numerical receipts belong to the theory/experiment artifacts, not this literature audit.

The mechanism is not merely the ordinary all-positive-prefix AP corner case. After full recall in ordinary binary AP, all remaining labels are negative, so precision cannot rise. In VUS, unreached buffer positions can still have positive weight after clipped recall reaches one. This distinction should be explicit in the theorem and explanation. State it for the pinned dynamic contract; static-denominator or differently clipped variants need their own analysis.

Focused searches included `VUS-PR overestimation`, `VUS-PR sampling error`, `VUS post-saturation`, `VUS recall saturation`, `VUS-PR rank reversal`, `VUS-PR threshold sampling`, and `VUS-PR approximation error`, including searches restricted to arXiv, OpenReview, and GitHub. Exact-term queries often returned no relevant match and broadened to unrelated genetics or multiclass-VUS literature; those are not evidence either way.

The closest inspected primary material does not disclose this specific construction or a two-sided sampling-error guarantee:

- The final [Boniol 2025 paper](https://www.paparrizos.org/papers/BoniolVLDBJ25.pdf), Section 5.7 and Table 4, varies the threshold count for runtime sensitivity. The inspected discussion does not quantify sampled-versus-exhaustive PR error, post-saturation inflation, or selection regret.
- [TimeEval's introduction of VUS, PR 34](https://github.com/TimeEval/TimeEval/pull/34), its comments, and its current documentation discuss changed metric assumptions and compatibility tests. They acknowledge low-threshold quality degradation, not this post-saturation mechanism.
- Issue searches in the original VUS, TSB-AD, and TSB-UAD repositories found no relevant threshold-approximation construction. The searches are bounded issue searches, not a complete archive of all conversations.
- [Yang et al., taxonomy v2](https://arxiv.org/html/2511.18739v2) studies genuine/random/oracle outcomes and tolerance trade-offs. Its VUS description uses a max-linear soft-label formulation. The inspected relevant sections do not compare sampled and exhaustive versions of one pinned dynamic contract.
- [Lyu's v2 stress test](https://arxiv.org/html/2607.11969v2) fixes VUS resolution at 250 and analyzes best-of-many reporting and inter-metric ranks. The inspected methods/results do not isolate the grid's numerical fidelity or post-saturation soft mass.

**Supported novelty wording:** “We exhibit and analyze a post-saturation soft-mass mechanism by which the standard finite rank grid can overestimate the original dynamic VUS-PR and reverse detector selection; the checked VUS optimization and evaluation studies do not analyze this computational failure.” Do not claim that VUS as a mathematical metric is thereby invalid, or that this is the first possible approximation counterexample. The new contribution is the explicit mechanism, proved construction, ordinary-width witnesses, sound remedy, and measured fresh-workload consequences.

### Same-transcript limitation

The existing theorem shows that one sampled scalar can be badly wrong. A sharper statement is: **the entire sampled curve transcript can be identical for two score assignments whose exact PR values differ arbitrarily close to one, simultaneously at all widths in a fixed range**.

Fix `L`, an original interval of length `m`, and a rank grid whose first two sampled ranks are 1 and `q`. Choose `q` large compared with `m+L`; the maximum support has size `Q<=m+L`. Keep the highest-scored negative outside that support. In assignment A, place original positives at ranks `2,...,m+1`, then all halo positions. In assignment B, place all maximum-support positions among the final `Q` ranks up to `q`. Permute only within ranks `2,...,q`, preserving every support position's score-bin membership and all scores outside the bin.

At rank 1 both assignments have zero weighted mass and coverage. At rank `q` both include exactly the same support, and at every later sampled rank their non-count states and global counts agree. Thus all sampled `(C,T,B,H,R,F,precision)` states agree at every width. In A, exact PR is `1-(H_(m+1)-1)/m`. In B, every positive recall increment has precision at most `Q/(q-Q)`, so exact PR is at most that quantity. Taking `m` large and then `q` sufficiently large makes the difference approach one.

Therefore any interval inferred **only from that sampled transcript** and valid for all compatible inputs must sometimes have width nearly one. This is not a lower bound for algorithms allowed to inspect the original full scores/labels; those inputs reveal the hidden ordering. It also does not rule out useful data-dependent certificates or adaptive refinement. The construction extends the older project theorem, but still inherits a simple ranking-information argument and should be a supporting proposition, not the principal novelty claim.

## A valid coarse-bin certificate to consider, not yet implemented

Let consecutive sampled endpoints have predicted counts `C_a<C_b`, weighted true-positive masses `T_a<=T_b`, and recalls `R_a<=R_b`. Every admitted position has weight in `[0,1]`; write `M=T_b-T_a`. At any interior count `c`,

```
max(T_a, T_b - (C_b-c)) <= T(c) <= min(T_b, T_a + (c-C_a)).
```

Optimizing `T(c)/c` over the interval gives

```
p_lo = T_a / (C_b-M)
p_hi = T_b / (C_a+M).
```

Use `p_lo=1` in the all-unit-weight zero-denominator lower-bound case and `p_hi=0` when its denominator is zero. The interval's exact right-step PR contribution lies in `[(R_b-R_a)*p_lo, (R_b-R_a)*p_hi]`. Proof: every complete-event precision lies in these bounds and every recall increment is nonnegative. Recall monotonicity for the original dynamic metric follows from `A<=P0`, increasing `A,B`, and nondecreasing coverage: the derivative of `(A+B)/(P0+B/2)` with respect to B is `(P0-A/2)/(P0+B/2)^2>=0` before clipping.

Sum bounds over bins and average over widths. A model is a certified winner if its lower bound exceeds every competitor's upper bound; otherwise refine or evaluate exactly. Complete-tie endpoints are essential. Zero-recall-increment bins contribute zero and can be eliminated. A generic coverage rule could change recall without changing weighted mass, so zero mass alone is not a universal elimination criterion. This is a real-arithmetic derivation; floating-point implementations require outward rounding or an explicit validated error envelope before advertising a machine certificate.

The bound is a promising inexpensive check, but its algebra is generic weighted-PR reasoning. Search did not establish whether this precise bound is novel. More importantly, the existing exact engine may already be cheaper than sampling plus certification. Measure the entire selector, not the number of requested thresholds.

## Disconfirmable experiment to freeze before outcomes

1. **Population and freshness.** Enumerate all previously measured series and score hashes. Choose a source-defined new split, or new detector outputs on old series with that reuse stated. Do not call score regeneration a new population. Freeze exclusions and family weights before computing metric differences. Keep source licenses and complete timeout receipts.
2. **Detector panel.** Use at least eight substantively different detectors, ideally the released 32-detector TSB-AutoAD panel. Avoid eight parameterizations of the same method. Keep the full time series and all labeled intervals; prohibit anomaly-centered cropping. Freeze score orientation, normalization, and any missing/nonfinite policy. Score computation is outside evaluator timing but separately documented.
3. **Two experimental axes.** For each supported native VUS contract evaluate exhaustive events and threshold grids `32,64,128,250,512,1024` plus all distinct scores. Report wrapper-rounded and unrounded scores separately. First match native software exactly; then perform controlled one-factor changes to ramp, overlap, positive denominator, coverage, integration, and origin convention. These are different scientific targets, not errors relative to one universal true VUS.
4. **Width fairness.** Report each native width interpretation. A radius parameter and a full buffer width are not interchangeable. Include a harmonized-support comparison, and retain native defaults as a separate application condition. Choose widths from training-free series properties or fixed external conventions, never from observed ranking changes.
5. **Decisions and effect sizes.** Compute exact winner sets with a fixed numerical tie rule. Report winner disagreement, regret measured under the particular exact contract, pair reversals with both gaps above `0.001,0.01,0.05`, family-level distributions, and changes in aggregate detector ranks. Give bootstrap intervals clustered by source family. Per-series winner flips with negligible regret are not sufficient significance evidence.
6. **Cost and correctness.** Compare against each unmodified native CPU evaluator at its same contract and grid. Include preprocessing, sorting, ramp preparation, certification/refinement, and fallback. Freeze five randomized warmed repetitions plus a separate cold measurement; do not mix JIT compilation into only one method. Any GPU claim needs a real same-contract GPU execution. Use exhaustive tiny cases, random multi-interval cases, ties, overlap/adjacency, boundaries, and independent native spot checks before timing.
7. **Mechanism.** Explain each semantic effect using one-factor ablations. Test whether sparse-support fraction and support fragmentation predict runtime; test whether missed early positive mass predicts sampled regret. Separate fitting/development from evaluation. Do not report a post-hoc fastest-method oracle as a deployable dispatcher.
8. **Failure branches.** If most discrepancies have tiny regret, report computational efficiency as the contribution and do not claim important changed scientific conclusions. If certification costs more than exact evaluation, retain it as a diagnostic, not acceleration. If native-contract equality fails, quarantine that variant rather than silently adapting its reference.

## What would justify raising the research assessment

A successful extension would establish all three of the following: (i) one proved representation and independently validated implementation computes several actually published contracts, including the trapezoidal correction; (ii) a genuinely expanded detector workload shows a useful, quantified evaluation or selection benefit, with substantial effects separated from numerical ties; and (iii) exact evaluation has a credible measured cost advantage at matched semantics, not only versus a slow or different metric. This would directly address generality, practical importance, and baseline fairness.

The experiment can falsify that stronger story. Merely obtaining more tests, a larger synthetic speed ratio, a new terminology, or another internal favorable score cannot establish it. The existing evidence supports a real narrow algorithm contribution; the new work must earn a broader contribution through results.
