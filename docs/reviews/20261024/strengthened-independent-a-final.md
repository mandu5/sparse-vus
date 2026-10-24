# Independent reviewer A: final immutable-snapshot review

**Final recommendation: Accept. Internal research-quality rating: 7/10.** This is a solid, specialized algorithmic contribution with credible exact-query benefits and unusually explicit limits. I find no remaining scientific blocker requiring another experiment. The largest uncertainty is whether the modest conceptual increment over classical threshold/component-tree machinery has sufficient breadth for the venue; my judgment is that its metric-specific content and demonstrated usefulness are sufficient.

Date: 24 October 2026. **AI-simulated scientific review, not external human peer review, an official PVLDB score, an acceptance probability, or a venue decision.** The recommendation applies to the complete snapshot below, not a prospective revision.

## Identity, independence, and verification

- Review snapshot commit: `ca8761cc40d493141511cad4bc3c184c48a681dc`.
- Evidence commit: `3a2ab2dcb6a9cbe1a83b0ce090f45d4abc4305c9`.
- PDF: [`paper/exact_metrics_strengthened20261024.pdf`](../../../paper/exact_metrics_strengthened20261024.pdf).
- PDF SHA256: `38ad66e21f7a21ab9d58f80f9b8d8499f92e55014e714c064cd467bd1cc05e54`.
- Binding manifest: [`manuscript-review-snapshot-v1.json`](../../../artifacts/pvldb-research-20261024/strengthening/manuscript-review-snapshot-v1.json).

I verified the checkout commit, both commit objects, evidence ancestry, the PDF digest, and the manifest and all eight manuscript-source files against both their recorded hashes and the review commit. I separately downloaded the public PDF from the [immutable GitHub snapshot](https://raw.githubusercontent.com/mandu5/sparse-vus/ca8761cc40d493141511cad4bc3c184c48a681dc/paper/exact_metrics_strengthened20261024.pdf); its full SHA256 matches. The four weighted record files and four native trial files also match the evidence commit. The supplemental weighted/native implementation files I inspected match their frozen protocol hashes.

I read all eight bound manuscript sources, including the bibliography, and inspected all 13 rendered PDF pages. The references begin on page 12; only references continue onto page 13. The equations, tables and query-regime figure are readable, and I observed no clipping or unresolved-reference markers. I did not rebuild or change the manuscript.

For this final review I independently:

- checked the support-event derivation, two-distance lemma, weighted-state invariants, cardinality-cost accounting, and query-associated sorting reduction;
- used separate small exact-arithmetic calculations to confirm the ROC counterexample and off-label bridge, and enumerated binary masks of lengths 1 through 6 to check the recall-fragment update and true-interval intersection-count identity;
- inspected the weighted incremental implementation, fused raster, closed-form interval control, both TimeEval adapters, and the native timing boundary;
- reconstructed every reported weighted aggregate point ratio from the four saved trial sets, without importing a metric producer; the largest difference from the stored aggregates was approximately `1.42e-14`;
- verified all 624 archived weighted NPZ file digests and independently reconstructed curve discrepancies, stored maxima, winner consistency, and grid-selection regret from their arrays;
- verified all 528 completed native result-CSV digests, reconstructed the combined matched-order ratios from trial records, and compared actual CSV scalar values and public-profile coverage;
- cross-checked original VUS/range table values and their negative controls against the corresponding saved result reports, including the selected original Linux range report and the older nine-metric consumer;
- read the historical PVLDB form, current scope policy, closest primary metric/component-tree antecedents discussed below, and supplied public-review calibration. I verified the four cached calibration-record digests and read their decision/meta-review content.

The artifact counts above delimit verification, not research achievement. I did **not** fit detectors, execute a metric producer, rerun timed studies, rerun the full test suite, reconstruct every raw dataset, or independently regenerate the reported bootstrap intervals. The intervals below were cross-checked against saved reports; my independent timing calculations reconstruct their point estimates. Saved Linux input-audit reports attest to raw/source verification on those executions; they are not my own fresh raw-input audit. No claim here converts saved-output consistency into an all-input correctness certificate.

I consulted only my A-lineage initial/follow-up reviews and objective artifact-audit material. I did not read the other simulated scientific reviewers or `docs/STRENGTHENED_RESEARCH_RESULT_20261024.md`. A wording error in my historical follow-up is corrected below without altering that historical file.

## Adapted historical PVLDB form

The fields follow the university-published [initial PVLDB reviews for DogQC](https://dbis.cs.tu-dortmund.de/publikationen/2020/data-parallel-query-processing-on-non-uniform-data/vldb-2020-reviews), supplemented by the [current 2027 scope policy](https://www.vldb.org/2027/submission-guidelines.html). This is an actual historical form, **not** a claim to possess the current private 2027 CMT form.

| Field | Assessment |
|---|---|
| Overall recommendation | **Accept** |
| Relevant for PVLDB | **Yes**, as Regular Research / Foundations and Algorithms |
| Specific revision needed to change the categorical judgment? | **No.** The remaining suggestions improve exposition; no further study is a condition of this recommendation. |
| Novelty | Some new, metric-specific ideas; moderate conceptual breadth |
| Significance | Useful improvement over existing exact evaluation operators |
| Technical depth and quality | Solid, with credible stated proofs and careful model restrictions |
| Experimental support | Supports the narrowed exact-query claims well; does not establish general default-workflow or detector-quality improvements |
| Presentation | Reasonable and precise, but dense |

The **internal** 1–10 rating measures research quality in this reviewer's judgment: 1 denotes a fundamentally invalid or absent contribution; 3 major unresolved deficiencies; 5 a borderline contribution with material unresolved questions; 7 solid publishable specialized work; 9 a major, broadly significant advance; and 10 an exceptional contribution. Intermediate integers interpolate these descriptions. **7/10** reflects soundness, controls and usefulness, limited by specialized novelty and workload-dependent impact. It is not derived from public-review score averages.

## Synopsis and three strongest points

The paper accelerates two existing time-series anomaly-evaluation operators without redefining their numerical queries. For dynamic VUS, it accounts exactly for omitted inactive thresholds using complete ties and predecessor rectangles. For range precision/recall, it maintains label-conditioned overlap and fragmentation as predicted intervals grow and merge, using fixed-label feature prefixes for moving positional weights. Public-detector workloads and a native TimeEval read-to-result workflow then test the benefit against compiled raster and conventional closed-form interval evaluation. The case for acceptance is the combination of a clear metric-specific state representation and a useful complete-query operating range, rather than generic sorting novelty or very large ratios against slow public Python code.

1. **The sufficient state is explicit and technically credible.** The ROC rectangle correction and joint precision/recall updates explain which events can be omitted and which must remain. Moving-middle weights and the off-label bridge expose actual requirements that component sizes or support-only updates do not satisfy by themselves.
2. **The controls address attribution.** The interval control implements ordered overlap and closed-form positional sums, and the faster raster remains visible. The native consumer includes score/label reads, all three requested metrics and result writing. The retained gains therefore demonstrate more than replacing an unoptimized public callback with compiled code.
3. **The claims track the evidence, including failures.** Low-cardinality losses, negligible default gains, the older 1.031-fold whole-consumer result, reused recordings, partial-pilot history, censored public calls, and between-run variation remain in the final PDF. The source/result bindings and complete saved curves make the reported comparisons inspectable.

## Three strongest weaknesses

1. **The novelty is narrow.** Offline activation, component trees, prefix moments, bucketing and telescoping area sums are familiar techniques. The weighted recurrence is short once the sufficient state is identified, and the sorting lower bound is standard. Nearest geometry has no independent runtime win over the conventional compiled support control on the primary panel. This is a useful specialized synthesis, not a new general dynamic-data-structure result.
2. **Practical importance depends on wanting complete queries.** Default native combined gains are approximately one to three percent and are usually unsupported by their intervals; the separate panel's maximum selection regret is only `0.00141219497462175`. The paper does not establish that typical users suffer large detector-selection losses from sampling. The nine-metric consumer also demonstrates that evaluation stages outside the optimized operator can dominate.
3. **Generality and uncertainty remain conditional.** MSL has two recordings; much of the original panel was reused; six timing orders are not independent workloads. The original and supplemental Linux executions differ materially in timing despite identical score bytes, while Mac/Linux score generation itself can differ. The finite-feature theorem extends beyond the implemented canonical family, and empirical binary64 parity is not a universal numerical-error bound. These restrictions are disclosed but still limit the result's reach.

## Technical soundness and novelty

**D1. Dynamic VUS.** At an inactive threshold only the global prediction count changes. The height and dynamic denominator stay fixed, so the horizontal area telescopes; complete global ties must nevertheless enter the next active transition together. The displayed predecessor-rectangle formula follows. My separate rational calculation gives `5/8` for the four-point example and `13/16` for naive support-endpoint connection, matching the manuscript. The two-distance claim follows because every active ramp is at least `1/sqrt(2)`, so two contributions clip to one. The comparison bound charges global tie-count queries, and the binary64 improvement explicitly changes the sorting model. I found no mathematical defect in those stated bounds.

**D2. Weighted trajectory.** Within a contiguous true interval, active runs are exactly its intersecting predicted components. An insertion changes that interval's fragment count by `1 - active-left-in-the-interval - active-right-in-the-interval`. An off-label insertion cannot join two fragments inside the same contiguous true interval. For precision, an inactive point's active neighbors are endpoints, so the stored outer boundaries identify the zero, one or two contributions to remove. The true-start-prefix expression for `h([a,b])` is correct. My small exhaustive checks support these local identities, independently of the implementation.

The moving-midpoint prefix argument is necessary: equal total count and first moment need not imply equal middle-weight mass. The bridge example evaluates to `3/4` before activation and `2/9` afterward, with recall state unchanged. The implementation follows these invariants and uses complete eligible score ties or query buckets before emitting outputs. Its use of compensated floating accumulation does not turn the real-arithmetic theorem into bitwise equality, and the manuscript correctly says so.

**D3. Cost and optimality.** The theorem now explicitly charges `C_gamma(n)` and coefficient/piece evaluation. Repeated squaring supplies the logarithmic exact-arithmetic operation bound for the improved cardinality factor; fixed-format `exp/log1p` is a separate implementation choice. The lower-bound instance has both label classes and reveals the rank of each positive score through its associated recall output. It is valid in the stated comparison model, but says nothing about scalar maximization, anonymous output multisets, or fixed-width radix sorting. The final abstract now states the query-associated restriction, resolving the earlier clarity concern.

**D4. Constructive novelty boundary.** [Tatbul et al., Section 5.5](https://papers.neurips.cc/paper_files/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf) already give ordered interval traversal and closed-form positional overlap for one mask. [Ranefall and Wählby](https://onlinelibrary.wiley.com/doi/full/10.1002/cyto.a.22806) already use component-tree size attributes for per-threshold precision and estimated recall, with size-selected positive pixels and a maximum-count recall denominator. Neither supplies, as stated there, this fixed-label Tatbul overlap/fragmentation trajectory with moving precision normalization. The manuscript constructively lists the extra state and admits that an augmented component tree implements the same algorithmic class. That is an adequate, bounded distinction. I did not independently reread every recent bibliography entry, and I do not certify universal priority over every unpublished implementation.

The novelty in one sentence is: **metric-specific support-event accounting and coupled label-conditioned overlap/fragmentation state allow exact dynamic-VUS integrals and weighted range trajectories to reuse threshold work while preserving their respective query semantics.**

## Experimental support against the actual files

**D5. Weighted curves and two conventional controls.** The four saved weighted studies reproduce maximum curve discrepancies of `2.4980018054066022e-15` for the original runs and `2.3869795029440866e-15` for the interval-control runs, with no stored/method winner disagreement. All grid winners are singletons. Only middle bias/cardinality one has a nonoverlapping sampled/exhaustive winner set, on MSL id3, and no regret reaches `.01`. These are direct saved-array checks, not merely acceptance of an audit status.

The exhaustive interval/incremental aggregate ratios independently reconstructed from trial records are:

| Host | WSD | Stock | MSL |
|---|---:|---:|---:|
| Apple | 7.322733 | 26.339148 | 1.706427 |
| Linux | 12.944875 | 36.148889 | 2.381477 |

The manuscript reports these correctly. Raster is faster than interval in five of six Apple collection/query aggregates and all six Linux aggregates. Thus interval alone would be an insufficient practical comparator; retaining both addresses that objection.

**Historical A-lineage correction:** my previous wording about “MSL semantic-7” losing on “both recordings” was wrong. `id7` is a recording identifier. In the Apple supplemental study, **id7** has interval/incremental `0.774661` and raster/incremental `0.562871`, losing all 12 exhaustive semantic settings; **id3** has `3.758922` and `3.584979`, winning all 12. On Linux, id7's interval/incremental aggregate is `1.024473` but wins only 9/12 semantic point estimates, while the faster raster/incremental aggregate is `0.683934` and loses all 12. The final manuscript and figure correctly preserve this recording-specific failure.

**D6. Native consumer.** The combined matched-order point estimates reconstructed from the actual trials are:

| Execution | Default raster/bucket | All-observed raster/bucket | All-observed interval/bucket |
|---|---:|---:|---:|
| Original Apple | 1.016841 | 2.728143 | Not measured in this study |
| Original Linux | 1.014469 | 1.931818 | Not measured in this study |
| Supplemental Apple | 1.026415 | 2.731695 | 3.034083 |
| Supplemental Linux | 1.015586 | 2.756131 | 3.190184 |

The abstract's `1.93–2.76` span therefore includes all four executions. The lower original Linux outcome has not disappeared behind the later faster ratio. The original Linux default interval `[1.007,1.027]` supports a small within-run benefit; the other combined default raster intervals cross one. The manuscript's conclusion of limited, inconsistent default benefit is appropriate.

My CSV reconstruction finds maximum scalar spread `3.3306690738754696e-16`. Each original public-comparator study contains 120 completed workflows, four timeouts and 20 prescribed skips. Public agreement covers 28/52 profiles per contract, not all 52. The supplemental studies complete 144 compiled workflows each and add no public-reference coverage. The adapter preserves the native threshold-generation formula, synthetic endpoints, ordering and integration, while using `nextafter` to map finite binary64 inclusive queries to strict masks. The timed call includes the native constructor and `recompute`; copying, warm-up and audit work remain outside the claimed interval.

The two Linux native executions bind identical hashes for all 52 score files and shared project sources, but their recorded OpenBLAS dispatch labels differ. Narrow conditional intervals do not explain the large between-run raster difference or prove a hardware cause. Retaining both executions and their provenance is the correct response; selecting the larger speedup would not be.

**D7. Older evidence and attribution.** Original VUS/range tables match the saved report values I inspected. The compiled support control/released ratios `0.910/0.960/0.978` and the small additional stream-over-geometry improvements constrain the VUS novelty claim. The original range panel's `24/15/12` changed/disjoint/large-regret counts do not transfer to the separate public-detector panel. The nine-metric report retains total medians `34.260309354` versus `33.2339995` seconds, a `1.030881` ratio. The final narrative respects each of these distinctions.

The partial Mac pilot is disclosed as preceding the final uncertainty protocol; this is not universal preregistration. The later interval comparison is explicitly a follow-up. The lower-envelope figure and direct supplemental raster contrast are labeled descriptive/post-hoc. The evidence supports an exact operator with a measured operating range, not general detector superiority or an across-population performance guarantee.

## Venue fit, public calibration, and presentation

The current [Regular Research call](https://www.vldb.org/2027/call-for-research-track.html) permits Foundations and Algorithms papers with formal or precise algorithmic contributions and encourages implementation/evaluation. Under the current scope policy, this paper has a concrete efficiency target in repeated analytics over stored score columns, substantive engagement with the PVLDB/VLDB Journal VUS operator, and a native stored-profile evaluation workload. This is a credible data-management contribution. A separate DBMS integration is not required to establish that case. The [TimeEval maintainers' issue](https://github.com/TimeEval/TimeEval/issues/22) corroborates a real repeated-threshold implementation problem, though it does not establish adoption or large user impact of this solution.

The historical DogQC initial/revision reviews calibrate my questions about marginal whole-workflow gains, adaptation of prior ideas, strong comparators and attribution. The [published revision reviews](https://dbis.cs.tu-dortmund.de/publikationen/2020/data-parallel-query-processing-on-non-uniform-data/vldb-2020-revision-reviews/) show acceptance despite a remaining attribution concern. DogQC's multi-operator system has broader scope than this paper; that case is not an acceptance template or a numerical score conversion.

The four adjacent OpenReview cases provide a second, explicitly limited calibration:

- The accepted [When Foundation Models are One-Liners](https://openreview.net/forum?id=H27kvyG4qf) illustrates why conclusions must follow the tested pipeline and controls. Here the narrow operator/query claims and failure cases substantially answer that analogous objection. Its publication is independently visible in the [official proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/cf70320e93c08b39b1b29a348097a376-Abstract-Conference.html).
- The accepted [Unsupervised Model Selection for Time Series Anomaly Detection](https://openreview.net/forum?id=gOZ_pKANaPW), decision `HRD5hna4dy`, illustrates that a specialized combination can be valuable when justified by the problem and evidence. That supports asking about usefulness; it does not supply novelty for this paper.
- The rejected [Time Series Subsequence Anomaly Detection via Graph Neural Networks](https://openreview.net/forum?id=73U_NlKaNx), decision `GMS-BMZmsG`, highlights limited novelty and inadequate component attribution. Here the support and sharing ablations prevent crediting the whole gain to geometry, while limited conceptual breadth remains my principal concern.
- The rejected [Time Series Anomaly Detection via Hypothesis Testing for Dynamical Systems](https://openreview.net/forum?id=G-dM79m_EXd), decision `GYaqYZtEQU`, highlights unclear novelty and a weak theory/system connection. Here the recurrence, actual implementation and equal-query controls are connected concretely.

Those review/decision texts come from the hash-verified **public dataset mirror** described in [`public-calibration.md`](public-calibration.md), not an origin-byte-verified current OpenReview download. The rejected decisions are recorded decisions, not inferred from scores or program absence. Cross-venue scale differences and purposive case selection preclude acceptance-rate estimation. I did not treat an AC's speculative revised score as an actual reviewer update.

The final PDF meets the observed 12-page non-reference boundary. Its principal presentation weakness is density: strict observed-score queries, native inclusive queries, scalar integrals, curve outputs, and two study generations require care to track. A compact contract/estimand map would help. The two worked examples and explicit component-tree augmentation are effective. No formatting or content defect I observed changes the recommendation.

## Revision requirements, further experiments, and final uncertainty

**Required scientific revision: none identified for this snapshot.** Two nonblocking improvements are a compact map of the distinct query contracts and a concise statement near the results that paired-order intervals quantify execution repeatability rather than workload generalization. These points are already present in the text; this is a navigation suggestion, not a request to change or hide the outcomes.

I do not request more repetitions of the same studies, a search for more favorable recordings, or replacement of the lower Linux result. Those actions would not resolve the remaining significance judgment and could become outcome-chasing. A prospectively fixed experiment in another real complete-query consumer could usefully refine practical reach; an independently implemented stronger equal-output evaluator could challenge the current operating-range claim. Neither is an identified missing condition of this acceptance recommendation. A counterexample to the exact recurrence, or a primary antecedent already providing the same joint state, would matter more than another favorable timing ratio.

**Largest remaining uncertainty:** the value assigned by a specialist PVLDB board to this modest, metric-specific augmentation of known machinery. My final judgment is **Accept, internal 7/10**, because the paper makes the increment inspectable, demonstrates useful exact-query gains beyond two conventional compiled controls, and does not overstate the default-consumer or selection benefit.
