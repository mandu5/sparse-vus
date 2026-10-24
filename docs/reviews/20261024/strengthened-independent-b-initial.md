# Independent review B — initial findings, 24 October 2026

This is an **AI-simulated research review**, not human peer review or an editorial decision. The target is PVLDB Volume 20, Regular Research, Foundations and Algorithms. No overall score or recommendation is assigned at this stage: the supplied manuscript explicitly leaves the fresh Linux and native TimeEval studies unfinished, and the author requested evaluation of the complete audited version before a final verdict.

I read `paper/exact_metrics_strengthened20261024.tex`, its body, `support_events_method.tex`, `weighted_range_method.tex`, `strengthening_results.tex`, its bibliography, and the relevant range/VUS kernels, adapters, experiment producers, auditors and test definitions. I read only `public-calibration.md` among other review-related files; I did not read another internal review, prior verdict or score. All inspection was static or through public primary web sources. **No local numerical execution, tests, detector fits, benchmarks, plotting or TeX compilation was performed.** Reported experimental values remain reported values rather than independently rerun measurements.

## Summary and preliminary assessment

The manuscript compresses dynamic VUS integrals to support events with full global tie counts and ROC predecessor rectangles, and maintains a Tatbul range-metric trajectory through local interval merges. The latter includes endpoint-dependent positional weights and local fragmentation penalties. The main identities are plausible and, in the portions checked, correct. The precise novelty is the coupled label-conditioned overlap/fragmentation state; sorting, component-tree topology, prefix moments, query bucketing, and shared-label loop interchange are established machinery.

Venue fit is defensible. PVLDB explicitly includes time-series analytics and Data Management for ML/AI, and its Foundations and Algorithms flavor evaluates conceptual/algorithmic contributions with formalism or precise pseudocode. A full DBMS is not a required contribution for this flavor. The work also substantively extends a metric published in PVLDB and the VLDB Journal. This does not by itself establish sufficient novelty or significance. [PVLDB 2027 call](https://vldb.org/2027/call-for-research-track.html)

## Concrete issues requiring resolution

### B1. The weighted raster control omits a published conventional optimization

**Priority: major for runtime attribution, not a counterexample to mathematical correctness.**

`src/sparse_vus/weighted_range.py:72–99` evaluates `_point_weight` separately at labeled/active positions at every query, and revisits predicted points while computing precision. In contrast, Tatbul 2018 Section 5.5 already describes ordered interval traversal and closed-form positional-overlap evaluation. The claim in `paper/weighted_range_method.tex:100–104` that the fused raster removes that per-mask implementation overhead is therefore too broad for the weighted implementation: it eliminates interpreter overhead but does not implement the stated closed-form optimization. [Tatbul et al., Section 5.5](https://papers.neurips.cc/paper_files/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf)

The strongest immediately eligible conventional control is a same-compiler evaluator that discovers predicted intervals for each query, traverses true/predicted intervals in temporal order, and computes each weighted intersection from endpoints or prefix moments. It must retain complete per-query recomputation and include preparation in the clock. This separates incremental state maintenance from avoiding repeated point-weight arithmetic. I do not assert this unmeasured control is faster; its absence is particularly material when the reported grid100 gains are only 1.5–1.6 times. The large exhaustive gains may remain, but their ratio against this control is not yet established.

The author has been notified and is preparing a separately frozen control without modifying the completed v2 experiment. This finding remains open until its results and contract are examined.

### B2. The stated tied-winner regret scope exceeds the new report

**Priority: moderate; concrete source/report mismatch.**

The manuscript body at lines 234–237 says both minimum and maximum regret over tied winners are retained. However, `experiments/audit_weighted_range_study.py` calculates only

`max(distinct_values) - max(distinct_values[i] for i in grid_winners)`.

This is the *best* choice among sampled tied winners. The corresponding Mac report stores `best_grid_winner_regret`, `regret_ge_01`, and `max_regret`, without a worst-tie sensitivity. Thus the new-panel statement that no contract produces regret .01 is presently supported only for that best-tie convention. A tied sampled winner can have a worse exhaustive optimum even when another tied winner is exhaustive-optimal; zero best regret does not exclude that possibility.

The existing records retain enough information for a separate reconstruction. Either report both ends and label the added sensitivity appropriately, or narrow the prose. I have not numerically evaluated whether any actual new-panel conclusion changes.

### B3. Current uncertainty intervals are conditional timing summaries with limited sampling support

**Priority: moderate; mostly acknowledged, but terminology must remain precise.**

The weighted auditor resamples six fixed method-order indices and uses the same draw across all 12 semantics within a recording. This correctly retains the intended pairing. Nevertheless, each balanced permutation is observed once, sequential execution can drift, and there is no demonstrated exchangeability or finite-sample coverage theorem. With Bonferroni correction over 36 cells, 10,000 resamples estimate very extreme tails from very little observed timing variation. A narrow interval is not evidence of population robustness.

The manuscript already calls these approximate, fixed-panel conditional intervals and separately shows recording reweighting. Preserve that language in the abstract, table captions and conclusions. Do not turn six balanced orders into six independent datasets. The reported MSL loss on one of two recordings must remain prominent. This is not a request to treat a large observed speedup as nonexistent; it limits the strength and interpretation of uncertainty statements.

### B4. Native utility and fresh reproduction are pending, not established by the working text

**Priority: major evidence gate, explicitly pending rather than a hidden failure.**

`strengthening_results.tex` contains pending placeholders for both results. The public TimeEval issue confirms a real repeated-threshold bottleneck, and static comparison shows that the adapter preserves the pinned sampler, native synthetic endpoints and recall/precision ordering while replacing the range callback. The binary64 predecessor mapping correctly implements a finite-score `>= t` query through the strict kernel. [TimeEval issue 22](https://github.com/TimeEval/TimeEval/issues/22), [pinned range-curve source](https://raw.githubusercontent.com/TimeEval/TimeEval/7c3622757b1a3afa9a84cbc97ce132d9e379f715/timeeval/metrics/range_metrics.py)

Final evaluation needs the audited read-to-result timings, complete/timeout/not-run counts, per-contract public-output coverage, and fresh raw-input generation receipts. A censored combined public workflow must not acquire a completed timing or confidence interval merely because individual profile outputs complete in other batches. The separate unchanged nine-metric consumer's reported 1.031-fold benefit remains a relevant utility limit. The new consumer is an additional workload, not a replacement for that observation.

### B5. Novelty should be judged against augmented component trees and exact public VUS implementations

**Priority: substantive significance question, not an allegation of duplicated results.**

Ranefall and Wählby already use component trees to obtain per-threshold object statistics and precision/recall-like quantities. Their target uses object-size eligibility, not fixed anomaly labels or Tatbul fragmentation, so it is not a same-output baseline and does not invalidate the presented local identities. The manuscript appropriately acknowledges that an augmented component tree can implement the same algorithmic class. The remaining novelty is a specialized augmentation and its proof, not a new component-tree algorithm. [Ranefall and Wählby](https://onlinelibrary.wiley.com/doi/10.1002/cyto.a.22806)

For VUS, Klein's pinned implementation already sorts maximum-support scores and uses support cumulative sums; Benchopt already uses a dense cumulative sweep and per-segment maxima. I checked those source mechanisms directly. The support-only event representation and ROC predecessor correction are a narrower advance than “fast exact VUS.” Same-output controls and public implementations must both stay in the final comparison. [Klein source](https://raw.githubusercontent.com/tomlouisklein/fast-VUS/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00/fast_vus.py), [Benchopt source](https://raw.githubusercontent.com/benchopt/benchmark_tsfm/2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94/benchmark_utils/metrics.py)

The reported conventional support control beating released single-model nearest-geometry code on all primary cases is an especially important negative result: it prevents assigning the whole speedup to the geometric lemma. Unmeasured FF-VUS/GPU runtime cannot support a universal fastest-evaluator claim. The workshop antecedent explicitly reports preliminary CPU/GPU acceleration, so it is a real related-work concern even though a different numerical target cannot be used for an equal-output speed ratio. [Sylligardos, Section 4](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/PhD/PhD25_17.pdf)

## Correctness checks and limitations of this review

- The recall update `c_j += 1 - active_left_in_Tj - active_right_in_Tj` is valid in one dimension: two fragments within one true interval cannot be joined through an off-label position.
- The precision intersection count from true-start prefixes is correct for a component beginning inside a true interval. Component endpoint storage is sufficient because an active neighbor of the inserted point is necessarily a current component endpoint.
- Moving front/back/middle weights are correctly expressed through interval counts/moments; the split at the current midpoint matters. The provided equal-count/equal-first-moment example is a valid witness against an unsplit middle-weight summary.
- The VUS predecessor rectangle telescopes omitted zero-weight thresholds at constant recall/denominator, while complete global counts preserve mixed active/inactive ties. I found no counterexample to the real-arithmetic identity in static inspection.
- Rational finite-set tests, public API checks, and saved-curve auditors are useful distinct mechanisms. I inspected their source but did not run them. A saved-curve auditor importing no producer verifies reconstruction and agreement, not an independent mathematical computation of the metric on the full real panel.
- Canonical implementation coverage does not imply arbitrary polynomial callbacks are implemented; the text correctly calls the broader finite-feature interface theorem-only. Empirical binary64 tolerance does not imply an all-input rounding certificate.
- “Exhaustive” in the strict observed-score study excludes the below-minimum all-active mask. This is explicitly declared, so it is not a correctness defect under that query contract; claims of an unconstrained globally optimal deployment threshold would be unsupported.

## Public-review calibration and final gate

I used the permitted calibration document only for adjacent objections and its provenance limits. Its accepted ICLR cases caution against rejecting a useful specialized contribution merely because it combines established tools; its rejected cases caution against unclear novelty, missing eligible baselines, and crediting the wrong component for the gain. Here, classical-method attribution and explicit negative cases are strengths. B1 is the unresolved analogue of the missing-baseline/incorrect-attribution concern. New-panel limited detector/collection coverage and unfinished native evidence constrain broader claims.

These are adjacent-venue mirrored public-review examples, not public PVLDB reviews or an acceptance-probability model. No numerical translation between review scales is used. The official PVLDB Regular Research limit is 12 non-reference pages; that and the final artifact availability should be checked on the completed package, not inferred from this static TeX read. [PVLDB submission guidelines](https://www.vldb.org/2027/submission-guidelines.html)

The final review will reassess the concrete baseline and tie-regret responses, full audited native/Linux evidence, and whether the resulting algorithmic contribution is significant enough for the declared venue flavor. No favorable score is promised or inferred from the additional amount of work.
