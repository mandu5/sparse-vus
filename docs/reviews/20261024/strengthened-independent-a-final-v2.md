# Independent reviewer A: final v2 scientific delta review

**Recommendation: Accept. Internal research-quality rating: 7/10. No must-fix scientific blocker identified for this exact snapshot.** The completed process-session study strengthens the evidence for a useful exhaustive-query operator. It does not add conceptual novelty or establish broad practical impact, so my categorical recommendation and internal rating remain unchanged from v1.

24 October 2026. **AI-simulated scientific review**, not external human peer review, an official PVLDB rating, an acceptance probability, or a venue decision. This is a separate assessment of the complete v2 submission; the [original final review A](strengthened-independent-a-final.md) remains immutable.

## Snapshot and independent checks

| Item | Immutable identity |
| --- | --- |
| Review commit | `8036526f9bea0d4a03617477b290df3302e80bb2` |
| Evidence commit | `448ad1b714a5daa13feeba617b10e02efef674fe` |
| PDF | `paper/exact_metrics_strengthened20261024.pdf` |
| PDF SHA256 | `68b0576bf38f3defba59427bebf563576942277daebd8043a7053f82dcf400e5` |
| PDF size | 201,275 bytes |
| Binding manifest | `artifacts/pvldb-research-20261024/strengthening/manuscript-review-snapshot-v2.json` |
| Manifest SHA256 | `ea4d5c616ac90c21d70f78c542f19b0ef51aa6e40e8b87c4dab24ec818c9218f` |
| Affinity experiment source | `d8494c25a8c6fe44616a34bdded375dc3993d048` |
| Completed affinity execution | GitHub Actions run `40091476529`, attempt 1 |

I verified the PDF size and full digest, the manifest, all nine bound manuscript sources and three style files against both their recorded hashes and the review commit. The evidence commit is an ancestor of the review commit. I read the full v2 PDF, examined every source change from v1, reread the mathematical arguments, and inspected all 13 rendered pages. The two mathematical method fragments are byte-identical to v1. References begin on page 12; page 13 contains references only. I observed no clipping, illegible table, or unresolved-reference marker. I did not rebuild the paper; the manifest's build-warning counts are not my independently reproduced compiler result.

My earlier independent proof, implementation, weighted-curve and native-output checks remain documented in the original A review. For this extension I independently audited the failed preparation, the prospective design change, and the completed saved archive. I wrote a standard-library-only result checker that imports no producer code and calculated the four affinity comparisons before reading the producer summary. The [result audit](affinity-v2-independent-result-audit.md), [reconstruction JSON](../../../artifacts/pvldb-research-20261024/strengthening/affinity-independent-a-v2.json), and [standalone checker](../../../experiments/audit_affinity_v2_saved_a.py) are byte-identical to their copies in evidence commit `448ad1b7`. Their SHA256 values are respectively:

- `2279095bcdebc913892fa5dc97fedbcb93c677408d14d8ebf65922d07c537d91`;
- `7018d63a50794fc9ddbc0ea660e8e0140fae805982f4ef5168c278c965b2db3e`;
- `1925239ba3ccf4cbbc4c03b354b7c42dc5588de5fb1126329a5e757c5102652b`.

For the final manuscript comparison, I checked every displayed affinity estimate and interval against that independent reconstruction. I also recomputed the eight original/supplemental combined-native rows' medians and paired ratios from their actual trial files, verified those files against the evidence commit, and checked the expanded weighted table against the saved interval and exploratory-raster reports. Older interval endpoints were cross-checked, not newly bootstrapped; the affinity endpoints were independently reconstructed. One minor displayed-median discrepancy is recorded below.

Independence here means independent calculations and scientific judgment, without consulting peer simulated-review recommendations or scores. I previously audited the proposed protocol and identified implementation fixes, but did not implement the timing runtime. I consulted only my A lineage and objective evidence, not `docs/STRENGTHENED_RESEARCH_RESULT_20261024.md`. I conducted no new detector fitting, metric evaluation, or timing in this review. The original final A review still has SHA256 `2a33f88ac68819acdf4381d4306f2f043a56ef06ce70b7d4076564baeeff3a32`.

## Adapted historical PVLDB form

The fields follow the university-published [historical PVLDB initial reviews for DogQC](https://dbis.cs.tu-dortmund.de/publikationen/2020/data-parallel-query-processing-on-non-uniform-data/vldb-2020-reviews/), supplemented by the current public criteria. This is not the current private 2027 CMT form.

| Field | Assessment |
| --- | --- |
| Overall recommendation | **Accept** |
| Relevant for PVLDB | **Yes**, Regular Research / Foundations and Algorithms |
| Specific achievable revision needed to change the category? | **No** scientific revision is a condition of acceptance in this review |
| Novelty | Some new metric-specific identities; modest conceptual increment |
| Significance | Useful exact-query acceleration in a specialized analytics workload |
| Technical depth and quality | Solid; assumptions and nonclaims are explicit |
| Experimental support | Strong for the declared fixed-input/operator claims; limited for broader practical generality |
| Presentation | Improved contract navigation and comparison visibility; still dense |

The internal scale is defined as follows: 1 means fundamentally invalid or absent research; 3 major unresolved deficiencies; 5 borderline work with material unresolved questions; 7 solid publishable specialized work; 9 a major broadly significant advance; 10 an exceptional contribution. Intermediate integers interpolate these descriptions. **7/10** credits soundness, a useful operating range and strong controls, while discounting limited novelty and workload-dependent importance. Additional audit volume or repetitions do not mechanically raise this rating.

## Synopsis, three strengths, and three weaknesses

The paper accelerates two existing evaluation operators by identifying the state that must change across score thresholds. Dynamic VUS needs complete ties and predecessor rectangles for omitted inactive ROC events. Weighted range precision/recall needs coupled overlap and fragmentation statistics, with prefix queries handling precision weights whose normalization moves as components merge. The theoretical and measured contribution is to reuse this metric-specific work without changing the requested numerical query. V2 adds a finite controlled repeatability study and clearer attribution; it does not replace the original results.

The three strongest points are:

1. **Explicit sufficient state and convincing local arguments.** The off-label bridge and moving-middle examples expose actual requirements beyond component sizes. The VUS counterexample similarly identifies why simply omitting thresholds is wrong. The formulas, implementation and experimental contracts are connected.
2. **Credible comparisons against conventional compiled work.** Both raster and closed-form interval controls remain visible, including the faster control. Native measurements cover score reads, all three requested metrics, and result writing. Exhaustive benefit survives those controls and the additional five-process execution.
3. **Negative evidence constrains the claims.** Low-cardinality losses, the small default benefit, small selection effect on the public-detector panel, older 1.031-fold nine-metric result, failed preparation, partial-pilot history, public-call censoring and all earlier Linux timings remain disclosed.

The three strongest weaknesses are:

1. **The conceptual increment remains narrow.** Component trees, label-conditioned attributes, offline ordering, prefix moments and bucketing are established. The sorting lower bound is standard. The contribution is their specific coupled metric state, with short local recurrences, rather than a general new data structure. More repeatability cannot resolve this significance judgment.
2. **The compelling gains require complete queries.** Native default gains remain about one to three percent. The separate panel's maximum reported selection regret is only `0.00141219497462175`; no practical-cutoff `.01` case occurs there. Thus the paper does not demonstrate that the typical benchmark user incurs substantial model-selection harm from sampling, or that detector training and broader evaluation pipelines become materially faster.
3. **Generality remains conditional.** Two MSL recordings are a very small sample, much older data was reused, and five consecutive processes on one runner are not five independent machines or datasets. Binary64 parity is empirical, and the broader finite-feature weight interface is theorem-only. Raw generated vectors are not redistributed, limiting an auditor without reacquisition to their saved bindings.

## Detailed scientific evaluation

**D1. Correctness is unchanged and remains credible.** The v2 proof fragments preserve the support-event derivation, two-distance geometry, recall-run update, true-interval intersection count, moving-weight prefixes, explicit cardinality-evaluation cost, and query-associated comparison lower bound. I found no new flaw on rereading. My prior independent exact-arithmetic and small-mask checks still apply to these unchanged statements; they were not rerun for this delta review. In particular, the four-point ROC example is `5/8`, not the naive `13/16`, and the off-label bridge changes precision from `3/4` to `2/9` while leaving recall state unchanged.

The lower bound recovers input-associated positive-score ranks from recall and is valid in the stated comparison model. It does not apply to an anonymous output multiset, a scalar optimum, or fixed-width radix sorting. The arithmetic theorem does not claim a bit-complexity or all-input floating-error guarantee. The final abstract and numerical-scope text preserve these necessary qualifications.

**D2. The new antecedent improves the novelty boundary.** I read the full primary [Naegel–Passat 2014 article](https://www.ipol.im/pub/art/2014/71/article_lr.pdf). Its Section 3.2 explicitly permits incremental component attributes relative to a fixed binary marker during tree construction. Its objective is a weighted false-positive/false-negative cost for a union of selected tree nodes. It does not present the joint Tatbul fragmentation and moving positional-normalization trajectory claimed here. Therefore label conditioning itself deserves no novelty credit, and v2 correctly says so. This is a closer antecedent than an unlabeled component tree; adding it narrows the argument without eliminating the specific remaining result.

Together with the ordered closed-form overlap evaluation already in [Tatbul et al.](https://papers.neurips.cc/paper_files/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf) and the component-size-based threshold evaluation in [Ranefall–Wählby](https://onlinelibrary.wiley.com/doi/full/10.1002/cyto.a.22806), the reasonable novelty statement is: **metric-specific support-event accounting and coupled overlap/fragmentation state preserve the exact dynamic-VUS integrals and weighted range trajectories while reusing threshold work.** An appropriately augmented component tree belongs to the same algorithmic class. The manuscript explicitly acknowledges that equivalence. I do not certify universal priority over every implementation or all recent literature.

**D3. The preparation failure and design change are legitimate and visible.** The [failure/design audit](affinity-v1-failure-v2-design-audit.md) verifies that v1 completed 52 detector fits and input auditing, then stopped at its strict prior-score identity gate. Twenty-five COPOD profiles differed; one distinct-score count changed. No metric warm-up, timed metric workflow, or process block ran. Detector-fit durations are not metric timing outcomes.

V2 did not retroactively waive that failed condition. It prospectively changed the estimand to five process sessions sharing the first new, frozen 52-profile realization, with raw/typed-label/template identity still mandatory and prior score/query differences diagnostic. The source/design freeze preceded metric outcomes. The realized generation happened to match both earlier Linux references, but matching was not a selection criterion. There is no observed timing-based favorable-run selection in this transition. I found the final disclosure consistent with the saved chronology.

**D4. The new results are independently supported, with a small scope.** The saved archive's ZIP SHA256 is `8d1fd2e2715c8eb4b28c5f1861143766498686aa072a3c72b9d539ca57b6b595`. My reconstruction verified all 697 extracted members, five distinct child processes, all 180 timed workflows and 30 full warm-ups, and all 210 result CSVs. Every timed status is `COMPLETE`; no failed or slow observation was substituted or removed. Every same-contract CSV pair was checked, including warm-ups and cross-block pairs. Maximum scalar spread is `3.3306690738754696e-16`.

All 52 recorded score-array hashes, 52 native-score hashes and complete realized query plans agree with both previous Linux references. Native query totals are 2,776 and 71,750. Because the vectors themselves are not redistributed, these are independent checks of hash identities, binding receipts, cardinalities and sampler counts; I did not independently derive unavailable threshold-vector hashes from raw score values. Affinity receipts confine every observed live thread to logical CPU 0. They do not establish exclusive physical-core access or remove unrelated host load.

| Contract | Control / bucket | Independent geometric ratio | Independent descriptive interval |
| --- | --- | ---: | --- |
| Native default50 | Raster | 1.016773 | [1.011236, 1.024668] |
| Native default50 | Interval | 1.022603 | [1.017351, 1.030162] |
| All observed | Raster | 1.919025 | [1.905810, 1.932157] |
| All observed | Interval | 2.216016 | [2.200817, 2.227253] |

I independently averaged six paired log ratios within each block and equally weighted the five blocks. The bootstrap used 126 multinomial configurations with their multiplicities, reproducing all `5^5 = 3,125` empirical samples and the four-contrast adjusted endpoints. This differs computationally from the producer's ordered enumeration; the largest summary discrepancy was `4.44e-16`. All 32 numbers printed in Table 8 agree after rounding.

Exhaustive raster block estimates span `1.904621–1.933165`, with all 30 matched orders favoring bucket against either compiled control. Each default comparison retains four losing orders out of 30. The new empirical distribution supports repeatability on this fixed shared runner, not guaranteed confidence coverage or new-host generalization. It also does not explain why the older Linux studies differed. The paper's explicit limitations and separate reporting are appropriate.

**D5. V2 preserves the materially important older evidence.** Table 7 now exposes all four original/supplemental Apple/Linux combined results together. Their raw-trial exhaustive raster ratios remain `2.728143`, `1.931818`, `2.731695`, and `2.756131`. The new `1.919025` is separately reported, not hidden in that older four-execution span or pooled into it. Default results and the native flat/cardinality-one restriction remain explicit. The native study supplies no new public-implementation parity: earlier successful public calls still cover only 28/52 profiles per contract.

The expanded weighted table accurately distinguishes prospective interval comparisons from exploratory raster comparisons. Its 24 aggregate point estimates and 48 displayed interval endpoints match the saved reports; the raster intervals adjust six contrasts per host but do not correct post-hoc selection. The descriptive faster-control figure has no confidence interval. MSL **recording id7**, not a semantic-setting identifier, loses against the faster exhaustive control on both hosts; id3 wins. This correct distinction preserves the failure rather than averaging it away. The 1.031-fold older consumer result and negative support-control ablation also remain intact.

**D6. Presentation improves, with one minor numerical-display error.** The new study-to-output map distinguishes strict-query curves, integrated VUS values and native inclusive-query scalars. The expanded tables and native configuration wording resolve useful navigation issues from my v1 review. The text remains demanding because it presents several protocols and two algorithmic families within 12 content pages, but the visual layout is readable.

One Table 7 cell is double-rounded: Apple O / All observed / Raster prints **2.9461 s**, while the six raw durations give median **2.946046354 s**, which rounds directly to **2.9460 s** at four decimals. Table 4's **2.94605 s** is correct at five decimals. Every other Table 7 median and all its paired ratios agree with the actual trial files at the displayed precision; ratios are correctly computed from matched orders rather than these medians. Correcting this single last-place display is desirable and has no effect on any result, interval, claim, or recommendation. I do not treat it as a must-fix scientific blocker.

## Venue fit and public calibration

The [current Regular Research call](https://www.vldb.org/2027/call-for-research-track.html) recognizes Foundations and Algorithms contributions. Under the [current scope policy](https://www.vldb.org/2027/submission-guidelines.html), this paper's substantive efficiency problem is repeated analytics over stored detector-score columns; its VUS derivation directly engages the database metric literature, and native read-to-result execution supplies a concrete data-processing context. That is a credible fit. This judgment does not depend merely on a metric's prior appearance at PVLDB or on inserting a database citation.

I used the supplied [historical-form calibration](public-pvldb-form-calibration.md) and [public-case calibration](public-calibration.md). The [DogQC revision reviews](https://dbis.cs.tu-dortmund.de/publikationen/2020/data-parallel-query-processing-on-non-uniform-data/vldb-2020-revision-reviews/) show why whole-workflow impact, conventional comparators and attribution matter even when reviewers accept an adaptation of established ideas. Its multi-operator system is broader than this manuscript, so its decision does not determine this one.

The adjacent-field cases calibrate objections, not score targets:

- Accepted [When Foundation Models are One-Liners](https://openreview.net/forum?id=H27kvyG4qf), decision `XfBOGU95OS`: conclusions must match the tested pipelines and controls. V2's restricted native configuration and repeatability claims answer that analogous concern.
- Accepted [Unsupervised Model Selection for Time Series Anomaly Detection](https://openreview.net/forum?id=gOZ_pKANaPW), decision `HRD5hna4dy`: a specialized combination can be useful when the problem and evidence justify it. This supports examining practical value, not granting novelty by analogy.
- Rejected [Time Series Subsequence Anomaly Detection via Graph Neural Networks](https://openreview.net/forum?id=73U_NlKaNx), decision `GMS-BMZmsG`: limited novelty and weak attribution are serious objections. The conventional controls address attribution here, but limited conceptual breadth remains.
- Rejected [Time Series Anomaly Detection via Hypothesis Testing for Dynamical Systems](https://openreview.net/forum?id=G-dM79m_EXd), decision `GYaqYZtEQU`: an unclear increment and weak theory/system connection can outweigh extensive work. Here the exact local state is implemented and compared on equal outputs, making the connection inspectable.

The OpenReview texts are hash-verified records from a **public research-data mirror**, not origin-byte-verified current downloads. Accepted cases have separate official publication/program corroboration in the calibration record; rejected outcomes come from explicit mirrored decision notes. Different venues and yearly scales, small purposive case selection, and unavailable current-origin bytes rule out an acceptance-probability interpretation or numerical score conversion. AC speculation about hypothetical revised ratings is not an actual rating update.

## Required revisions, further measurement, and remaining uncertainty

**Must-fix scientific blockers: none identified.** No further experiment is a condition of this recommendation. The one displayed-median correction above is nonblocking. The v2 manuscript already makes the material qualifications that this evidence needs.

The finite five-session experiment was scientifically useful: it tested controlled process repeatability rather than merely reproducing a favorable within-process estimate. Its completion increases confidence in that bounded operating range. Another repetition of the same runner/workload until the ratio approaches the earlier 2.756 would be outcome-chasing. A prospectively fixed different complete-query consumer or independent stronger equal-output evaluator could still change the practical assessment, especially if it eliminated the measured advantage; that would be a distinct extension, not an identified missing requirement. Neither more timing trials nor narrower conditional intervals would make the local identities more original.

**Largest remaining uncertainty:** whether specialists assign enough significance to this modest metric-specific augmentation of established machinery. I judge that the explicit exact identities, useful complete-query acceleration beyond both conventional compiled controls, and faithful treatment of unfavorable evidence clear the bar for a specialized Regular Research / Foundations and Algorithms paper. My final judgment on the exact v2 PDF is **Accept, internal 7/10**.
