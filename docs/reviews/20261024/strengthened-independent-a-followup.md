# Strengthened manuscript — independent reviewer A, completed-evidence reassessment

Date: 24 October 2026. **Independent AI simulation, not external human peer review.** This follows, and does not overwrite, `strengthened-independent-a-initial.md`.

**Substantive assessment: the three major issues from my first read are now adequately addressed. I have not identified an outstanding mathematical or experimental blocker requiring another study.** The contribution remains specialized and its conceptual depth is modest; the completed evidence makes a credible case for the usefulness of that specialization. Subject to a faithful final PDF and artifact snapshot, my present judgment favors acceptance with minor clarification rather than a further major revision. This is not the requested final complete-paper recommendation or numerical rating; those await the immutable PDF, figure/layout, and appended status of the older public-reference replay.

## Independence and verification boundary

I did not read reviewers B/C, other mock-review opinions, or their scores. I used the previously supplied public OpenReview calibration only with its stated provenance and cross-venue limitations. In this reassessment I read the revised manuscript, the complete new results fragment, the updated weighted theorem and comparison, `weighted_range_control.py`, the supplemental study/reproduction drivers, and the source-bound decoding logic. I read the two specifically authorized Mac artifact-audit reports and the Linux saved-output reports. These are mechanical artifact audits, not external scientific reviews.

No local numerical execution, test, producer import, timing run, compilation, or raw-data reconstruction was performed. Experimental values below are the recorded manuscript/artifact results, cross-checked by reading their saved reports, not measurements I generated. In particular, the Linux archived-output reports explicitly do not claim local verification of raw input bytes; the native archived audit also does not claim local source-byte verification. Its completed output CSV bytes are verified. I preserve those distinctions.

I independently opened the public [Linux control CI run 40081512476](https://github.com/mandu5/sparse-vus/actions/runs/40081512476): it reports **Success**, commit `b0063f5`, duration 15m 3s, and a 34.8 MB artifact with digest `dfbd5aa2025b6b938e8a007c0d470d53206cb204410c09a197ec7e5af95ff56e`. This corroborates the public workflow status; it is not my own rerun or verification of every archived file. Direct web-tool fetching of the branch URL was restricted, so I do not infer either availability or absence of the latest manuscript bytes from that failed fetch.

## Resolution of the first-read issues

| Initial issue | New evidence and assessment |
|---|---|
| The increment over classical component trees and one-mask Tatbul evaluation was unclear. | The manuscript now lists the additional precision prefixes/sums and per-true-interval recall state, gives activation pseudocode, and explicitly admits that an augmented component tree implements the same algorithmic class. It distinguishes Ranefall's size-based per-threshold precision/recall from label-conditioned overlap and fragmentation. The moving-middle and off-label bridge examples make the required state concrete. This is an adequate constructive novelty boundary. |
| Weighted/native evidence was incomplete and the comparator did not isolate closed-form per-mask optimization. | Both hosts now have complete frozen supplemental interval controls and complete compiled native controls. The conventional interval code really reconstructs predicted intervals per query, computes precision from fixed-label prefixes, and traverses ordered intersections for closed-form recall masses. The stronger comparator is therefore substantive. |
| Headline contribution risked exceeding what VUS ablations established. | The introduction and abstract foreground exact support-event accounting and coupled weighted state. Classical ordering, component trees, work sharing and loop interchange are explicitly disclaimed as inventions. The old conventional-support advantage, small default-native gains, and 1.031-fold nine-metric result remain. I see no new attribution overclaim. |

The initial smaller issues are also substantially resolved: `DefaultMetrics.RANGE_PR_AUC` is named; strict observed-score queries explicitly exclude the below-minimum all-active state; canonical implementation scope is separated from the broader theorem; and a closed-form interval control is actually measured rather than merely discussed.

## Correctness and novelty after revision

The explicit `C_gamma(n)` term repairs the cardinality-cost ambiguity. The general theorem now charges `n(qd + C_gamma(n))`; its space and evaluation assumptions are stated. For the improved factor, repeated squaring gives an exact-arithmetic logarithmic operation count, while the implementation's fixed-format exponential evaluation is separately described. The paper expressly declines a rational bit-complexity or universal floating-point certificate. I find the revised bound coherent.

The padded lower-bound instance contains both label classes: `n-1` consecutive positives with distinct positive scores, followed by a zero-score negative. At a positive point's own strict query, recall identifies the number of higher positive scores and hence that point's rank. Query association preserves the sorting information. The resulting comparison lower bound is valid for the stated full-curve problem; it is a standard sorting reduction, not a new lower-bound technique, and the text correctly excludes scalar maximization, anonymous output multisets and fixed-width radix models.

The new bridge witness is correct by hand: with labels `(1,1,0,0,1,1)` and predictions `(0,1,1,0,1,1)`, the two predicted components have reciprocal/middle precision `1/2` and `1`. Activating position 3 produces middle weights `(1,2,3,2,1)` on `[1,5]`, label mass 4, normalizer 9 and cardinality 2, giving precision `2/9`. Recall overlap and fragmentation do not change. This demonstrates the concrete reason that support-only activations fail for the range operator.

The closest literature remains the material identified in my first report. [Tatbul et al., Section 5.5](https://papers.neurips.cc/paper_files/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf) already provide efficient ordered-overlap evaluation for one mask. Component-tree construction and attributes are classical. [Ranefall and Wählby, “Global gray-level thresholding based on object size,” Cytometry Part A 89(4):385–390, 2016](https://onlinelibrary.wiley.com/doi/full/10.1002/cyto.a.22806), Methods pp. 386–387, already use component sizes for per-threshold precision and estimated recall. Their positive pixels are selected by a prescribed object-size interval and recall is normalized by a maximum such count; that state does not itself supply labeled Tatbul overlap, label fragmentation, or moving positional normalization. I found no primary antecedent in this review that already publishes the same joint recurrence. This is a bounded literature finding, not a universal precedence guarantee.

The algorithmic novelty should therefore be assessed as an exact, metric-specific combination of label-conditioned state and local identities. The constructive augmentation is fairly short once stated, and the lower bound does not independently supply much novelty. Still, it is not fair to equate “can be expressed as a component-tree augmentation” with “already established for this metric.” The manuscript now exposes enough detail for readers to judge that increment directly.

## What the completed experiments do and do not establish

The new interval control shares the canonical arithmetic helpers but does not reuse metric state across thresholds. Its recall overlap summation is an ordered interval traversal; it does not enumerate all true/predicted pairs. A single predicted interval spanning several true intervals remains at the cursor as needed. Its full score scan, prediction discovery, prefixes and curve construction are included in the timed public call. This is a reasonable conventional control for testing the benefit of cross-threshold maintenance. Sharing elementary arithmetic does not independently certify correctness, but the paper also supplies derivations and separately implemented finite-set oracle checks; my review did not execute those checks.

Recorded interval-control speed ratios for distinct observed queries are:

| Host | WSD | Stock | MSL |
|---|---:|---:|---:|
| Mac | 7.323 [7.277, 7.342] | 26.339 [26.244, 26.387] | 1.706 [1.679, 1.728] |
| Fresh Linux | 12.945 [12.396, 12.991] | 36.149 [35.977, 36.224] | 2.381 [2.347, 2.418] |

These are paired timing-order uncertainty intervals on a fixed panel, not population coverage. All 12 semantics remain in the reports. The Mac MSL semantic-7 interval comparison loses on both recordings, with aggregate ratio about 0.775. The separate MSL recording-reweighting range spans below one. The raster is faster than the interval control in most aggregate cells, so the interval implementation must not displace the raster as the sole practical baseline. The manuscript retains both controls and the losses.

For the native three-metric read-to-result workflow, the all-observed combined control study reports approximately 2.732-fold (Mac) and 2.756-fold (Linux) gains over compiled raster, and 3.034-fold and 3.190-fold over the interval control. Default-query combined gains remain about 1.026 and 1.016 over raster with intervals crossing one. This supports useful exact-query acceleration, not a claim that the default native consumer generally becomes much faster. The compiled control's completed coverage does not extend the censored public-reference parity coverage; the manuscript explicitly preserves that distinction.

The maximum weighted curve discrepancy is recorded as `2.3869795029440866e-15`, with no same-contract winner disagreement. Native scalar discrepancy is `3.3306690738754696e-16`. These support empirical numerical equivalence over the audited outputs, not an all-input error theorem. The new panel's largest grid-selection regret is only 0.001412, with no 0.01 events; that weakens a broad claim about practical selection instability but does not undermine the speed result for the stated exact target. The paper correctly keeps the smaller effect visible.

The fresh-host comparison is not an isolated CPU intervention. Although the frozen detector inputs are restored identically, 25 of 52 score hashes differ, all belonging to COPOD, and the native all-observed query counts differ by one. The paper reports hosts separately and discloses that generation difference. This is the appropriate interpretation.

## Input reconstruction and reproducibility

The one-ULP compatibility map is a disclosed reconstruction of the originally frozen typed input, not a change to scores or an unnoticed selection waiver. Static inspection found guards on the raw member digest, decimal token, column and row, adjacent binary64 values, complete parsed-vector hash, and complete original-vector hash. Unexpected differences are rejected. A separately written audit path verifies the same identity against the original selected-case record. The altered parser behavior remains a portability limitation, but the remedy is scientifically defensible for reproducing the fixed original input.

The supplemental protocol explicitly states that it follows the first study and reviewer feedback; it does not claim original preregistration. The selected recordings, semantic family and query contracts are retained. The reproduction driver obtains raw/source inputs, regenerates detector profiles, checks the original design, executes all compiled controls, and audits saved results. I read this flow but did not execute it. The public CI status and archived reports increase reproducibility confidence within those limits.

## Remaining concerns and final checks

1. **Research significance is still the main judgment call.** This is a specialized evaluation-operator contribution using familiar offline techniques. The strongest case is the coupling of an explicit exact result with useful complete-query performance, not a breakthrough in generic dynamic connectivity or a universally faster default workload. The current wording mostly reflects that distinction.
2. **The abstract's lower-bound phrase could be slightly more explicit.** “Matching its comparison lower bound” is correct under the body’s restrictions, but “comparison-optimal for query-associated complete curves” would make the scope immediately visible. This is a clarity suggestion, not a mathematical blocker.
3. **The final figure and narrative must preserve the units of inference.** Six timing orders are repeatability observations, not six independent datasets; MSL has two recordings; no hosts should be pooled. The current text is careful. Check that the figure is equally careful and does not conceal the default-query null result or the MSL loss.
4. **Freeze the reviewed artifact and PDF.** Verify the final main-content page count, readable tables/figure, references, and that the public artifact snapshot contains the exact reviewed sources and completed outputs. I have not verified those final packaging facts and will assess the supplied immutable PDF separately.

I do not request another favorable-data search, another detector panel, or another timing rerun to close this review. The pending older public-reference replay should be appended with its own censoring/coverage, as planned; it should not replace the stronger completed control study or silently revise earlier negative results.

## Venue and calibration assessment

The current [PVLDB research call](https://vldb.org/2027/call-for-research-track.html) accepts formal/algorithmic papers and lists time-series analytics, while the [scope policy](https://vldb.org/2027/submission-guidelines.html) requires concrete data-management advancement, substantive database-literature engagement and application-grounded evaluation. Optimizing repeated evaluation over stored score columns, deriving an exact representation for the VUS/VLDB Journal operator, and measuring a native stored-profile consumer make a credible scope case. An additional database engine is not necessary to repair that case.

The adjacent public calibration supports taking strong controls, honest failure cases and a clear contribution boundary seriously. It does not justify transferring ICLR scores to PVLDB or estimating an acceptance probability. Against those substantive objections, this revision is materially improved. My current scientific concern is the limited breadth of the novelty, rather than an uncorrected flaw or an unsupported practical claim. A final recommendation remains reserved for the immutable complete-paper snapshot.
