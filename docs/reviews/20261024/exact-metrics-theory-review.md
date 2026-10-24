# Independent theory and significance review: Exact Evaluation of Time-Series Anomaly Metrics by Local Event Statistics

**Research gates: 4/6 pass within the stated whole-manuscript scope; gates 4 and 5 remain unverified for the new manuscript. Next: inspect the completed fresh combined reproduction and obtain the three independent reviews of this manuscript.**

**Recommendation: Accept, weak. Internal surrogate: 6/10. Confidence: 3/5 overall, 4/5 on the mathematical assessment.** These numbers are my assessment, not an official PVLDB score, a calibrated acceptance probability, or a project milestone. The largest weakness is the modest conceptual novelty of two narrowly specified metric operators: their useful sufficient statistics specialize familiar sorting, prefix counting, and component processing. The substantial new range experiment establishes a real algorithmic consequence of that specialization; it does not establish a new general evaluation framework or a large application-wide improvement.

## Independence, manuscript and cutoff

This is a fresh review of the separate **Exact Evaluation** manuscript, not another score update to the earlier VUS-only manuscript. I did not inspect other internal reviews, other reviewers' scores, or an aggregate recommendation. Earlier reviews remain separate historical records. I reviewed the whole manuscript, its two mathematical developments, the range implementation and audit sources, the prospective evidence design, the shared public calibration material and its underlying review records. I did not run timing experiments or modify scientific sources, records, or other reviews.

The scientific assessment was formed on 24 October 2026 from the 13-page PDF with SHA-256 `da132c602e81b38e7908143309a3d4b5ba7ffbf362445e2a92aaf22279ef3338` and current source, including the clarified combined reproduction command. A final packaging check below records the subsequent 12-page PDF. Neither pending Linux job is counted as completed: range-only run **40061935240** and combined run **40062043152**. The completed older VUS reproduction, run **40049786600**, supports only its actual scope.

The review uses the public [PVLDB 2027 research call](https://www.vldb.org/2027/call-for-research-track.html) and [submission guidelines](https://www.vldb.org/2027/submission-guidelines.html), checked on the review date. The intended category is Regular Research, Foundations & Algorithms. I have not verified the confidential current CMT review form, so the sections and numerical scale below are an explicitly internal surrogate.

## Summary and contributions

The paper studies exact evaluation of stored time-series anomaly score profiles under two existing metric definitions. For dynamic VUS, it compresses threshold events while preserving the scalar integral, including the ROC rectangle preceding an active event and complete global score ties. Interval geometry yields support-sensitive work across widths. For flat reciprocal-cardinality range precision and recall, it maintains overlap and fragmentation contributions as predicted intervals merge. On a path, component endpoints suffice for constant work per activation. This removes repeated full scans from exhaustive observed-threshold evaluation; an ordinary offline bucket implementation avoids unnecessary score sorting for a small supplied query set.

The distinction from the public software precursor matters. The complete VUS evaluator may be a first archival contribution even though an unrefereed implementation and working manuscript were already public. Its public-release status does not make the subsequent batch optimization the sole admissible contribution. Conversely, first archival presentation does not automatically make every existing implementation choice scientifically novel. The new range operator and its local-statistic proof were not in that precursor and are the main reason my assessment of this separate manuscript is favorable.

There are three substantive contributions of different strength:

1. Exact VUS scalar event identities, especially the ROC predecessor correction and global ties. These are more specific than generic support pruning and require the actual dynamic metric definition.
2. A correct, small state representation for the existing range operator, with a useful asymptotic consequence: all observed thresholds in sorting time plus linear updates, and ordered fixed queries in `O(n log(H+1) + n + H)` time.
3. A unusually explicit attribution study separating complete public calls, matched compiled scans, conventional support implementations, batching, query sorting and bucketing. Negative attribution and application results materially constrain the claims.

## Mathematical validity and exact scope

I found no critical mathematical defect in the declared contracts.

For the new range operator, the key recall identity is sound. Let `m_j` be active points inside one maximal true interval and `r_j` the number of predicted components intersecting it. Activating a point inside that interval increments `m_j` and changes `r_j` by one minus the number of its active immediate neighbors inside the same interval. The two neighbors, if present, belong to distinct components because the newly activated point previously separated them on a path. Inserting outside all true intervals cannot reconnect two fragments of any one contiguous true interval; hence it changes no recall term. This is why only one true interval's contribution needs replacement.

The precision update is also sound: remove the terms for adjacent predicted components, add the term for their union with the new point, and update the number of predicted components. True-point and true-interval-start prefixes recover the overlap and number of intersected true intervals in constant time, with the necessary correction when the component's left boundary falls inside an already started true interval. An active neighbor of an inactive point is an endpoint of its component. Thus storing a component's left endpoint at its right boundary, and vice versa, is sufficient; stale interior entries cannot be queried during an insertion. This endpoint representation is elementary but valid.

The formula includes false-only components in the outer precision average. Tied scores are processed as complete query states under strict `>` semantics. The VUS `>=` convention is separately stated. The bucket variant can activate points in arbitrary order inside a bucket because it returns no intermediate state. Its complexity accounts for label preparation, assigning points to ordered queries and emitting answers; arbitrary query sorting has an additional explicitly stated cost. The source implementation follows these invariants.

Several scope boundaries are essential and are now stated correctly:

- The proof concerns maximal disjoint true intervals on a one-dimensional path, flat positional weights and reciprocal cardinality. It does not establish arbitrary weighted range metrics, overlapping annotations or graph domains.
- Exhaustive **observed-score** strict queries omit the all-active state below the minimum score. The paper correctly avoids claiming an unrestricted maximum over every binary mask or every possible threshold; a lower sentinel can be requested separately.
- Recall need not be monotone under activation because another fragment can increase its cardinality penalty. The algorithm does not rely on monotonicity.
- Off-label insertions cannot be discarded. The paper's `(1,0,1)` witness correctly shows precision changing from one to one-third when the middle point joins the prediction.
- TSB-AD's all-one parsing behavior is a separate compatibility mode, not the mathematical definition. TimeSeAD's comparison uses its own `alpha=0` convention; the main experiment uses `alpha=.2`.
- Exactness is an algebraic identity with empirical floating-point agreement under the stated finite real binary64 input contract. Compensated summation and successful million-point checks do not establish a length-independent rounding certificate or bitwise equality.

The retained VUS arguments also survive review. An inactive threshold changes the prediction count but not weighted positive mass, dynamic denominators or component hits. Its ROC increments telescope horizontally; directly joining retained active endpoints is insufficient. Keeping counts strictly above and at each active score handles inactive observations tied with an active event. The two-distance geometry is valid for the specified summed-and-clipped ramps, rather than for every conceivable range dilation. Linear binary64 radix preparation is a machine-representation result, not a comparison-sorting lower-bound violation. The complete batch memory discussion now includes score-array validation/conversion and its `Mn` term.

## Novelty, prior work and venue fit

The strongest objection is not correctness but how much intellectual distance separates the method from familiar tools. Descending connected level sets and component trees predate this work. Endpoint maintenance on a path, prefix interval counts, caching, loop interchange and query bucketing are standard techniques. The paper appropriately attributes them instead of presenting a new connectivity structure. [Najman and Couprie's component-tree work](https://doi.org/10.1109/TIP.2006.877518) is relevant conceptual prior work; my current accessible verification of that reference includes the author-affiliated publication record, not a newly retrieved full publisher PDF.

Likewise, [Tatbul et al.](https://proceedings.neurips.cc/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf) define the range metric, and the pinned [TimeSeAD classic implementation](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/evaluator.py) already searches observed thresholds. Exhaustiveness and optimizing range-F1 are not new. What I did not find in the inspected sources is the particular maintained precision/recall state that avoids rebuilding the predictions and interval statistics at each threshold. That is a bounded literature finding, not proof of priority over every published or unpublished implementation. The paper should also cite the archival TimeSeAD paper alongside the exact source revision.

For VUS, [Boniol et al.'s VLDB Journal article](https://www.paparrizos.org/papers/BoniolVLDBJ25.pdf), including its algorithms, is much closer than a generic dense-threshold implementation. It already uses support and reuses work. The paper's remaining distinction is the exact scalar event reduction, including ROC behavior and global ties, plus its explicit geometry and complexity analysis. The minimal Klein support-threshold patch and conventional compiled support control prevent a claim that every large library speedup reflects these mathematical contributions.

The manuscript compares twelve recent primary papers and explicitly distinguishes metric redesign, benchmark construction, approximation and this exact computational problem. The recent [formal metric analysis](https://arxiv.org/html/2510.17562) addresses metric properties rather than the same incremental evaluation identity. Not all twelve papers are direct algorithmic competitors; the most decisive comparisons remain Boniol, the public fast-VUS sources, TimeSeAD and the classical component processing literature. This is adequate bounded positioning, provided the claim remains the operator-specific state representation rather than discovery of exact threshold evaluation in general.

I regard this as a plausible Foundations & Algorithms submission: evaluating and selecting among stored score columns is a recurring analytical operation, and the algorithmic contribution can be assessed without claiming a DBMS engine. The actual gain over a fused compiled raster makes the range result stronger than a translation of slow Python into compiled code. Nonetheless, the connection to a general database abstraction is limited. A reviewer could reasonably regard two elementary specializations as below PVLDB's novelty threshold. My weak acceptance rests on their exactness, useful asymptotic consequence, nontrivial metric interactions and controlled empirical evidence; it does not assume that simple techniques become novel when packaged together.

## Evidence and practical significance

I independently reran the saved-artifact auditors for the range main study and public study. Both returned PASS. This reconstructs bindings, curve comparisons, maxima, winners and statistical summaries from saved records; it is not a new timed execution or a full independent mathematical oracle on all real inputs.

The primary range evidence is all 73 reused real recordings and eight fixed score procedures, with complete precision/recall/F1 curves. The compiler-matched results are substantial:

| Collection | Fixed 100 queries: raster/bucket | Observed distinct queries: raster/sweep |
| --- | --- | --- |
| NAB | 1.719 [1.625, 1.814] | 27.80 [18.74, 41.94] |
| SMAP | 1.994 [1.817, 2.252] | 21.44 [8.57, 43.14] |
| SMD | 1.969 [1.884, 2.095] | 128.08 [95.09, 154.61] |

These are case geometric ratios with familywise 95% intervals over the three collections **separately for each comparison**. The main comparison includes validation, query construction, preparation, sorting, curve output and maximizing-value selection. It excludes training and file I/O. The fused raster has constant reducer workspace and does not allocate an interval representation at every threshold. These choices make the compiled control credible. The exhaustive timings have only two complete calls per method and case; the bootstrap primarily describes case variability, not a rich assessment of machine-level timing variability.

The reconstructed maximum cross-method full-curve discrepancy is `2.9976021664879227e-15`, with identical model-winner sets. Independent set-intersection oracle tests and unchanged public values provide complementary checks, but shared mathematical assumptions between implementations are still possible. The saved validation report checks 1,168 unchanged-public values at the recorded maximizing cuts, with maximum discrepancy below `4.62e-16`; these are value checks at chosen cuts, not an independent proof that every maximum is global. Three million-point numerical stress inputs have maximum curve error about `2.23e-12`, under their prospectively declared tolerance.

The failure case is informative: SMAP534 has only 3–11 distinct scores across its eight profiles; the compiled raster takes 0.838 ms and the sweep 2.012 ms. Full sorting need not win at tiny query cardinality. Bucketing also materially outperforms the score-sorted sweep on the fixed grid. These results support the stated algorithmic explanation more than a uniform-win claim would.

The exhaustive threshold choice changes 24 numerical winner sets; 15 have no overlap with the grid winner set, and 12 incur range-F1 regret at least .01 under the stated oracle comparison. These are real evaluation consequences for the fixed eight-profile panel. They are not improved deployed anomaly detection, evidence for a label-free selector, or a newly discovered general fact that approximate metrics can alter rankings.

Unchanged public range comparisons cover only the three shortest recordings in each collection, with two calls per case. Their large factors include runtime differences. Both TimeSeAD calls for SMD187 remain censored at 60 seconds; no exact public latency or completed output parity is available for that case. The `alpha=0` TimeSeAD and `alpha=.2` primary targets must remain distinct. The large all-73 compiled comparison is the stronger mechanism evidence; the nine-record public panel does not establish an all-73 public-comparator confidence interval.

The older negative results remain decisive constraints on the whole manuscript. A conventional compiled direct-ramp support control beats the released scalar evaluator on every original case, with control/released ratios .910/.960/.978. Thus the special two-distance geometry has no isolated empirical speed advantage here. The streaming batch is only 1.357/1.201/1.166 faster than that control. The original Mac SMD stream/released result is 1.207, so the prospective new-batch 1.25 criterion still fails.

Most importantly, VUS alone improves about 66.07-fold in the actual unchanged nine-metric consumer, while the whole consumer improves only **1.03088-fold** because VUS occupied about 2.7% of baseline runtime. Affiliation remains the largest measured stage. No integrated range-enabled whole-nine-metric acceleration is measured. The new operator study earns its own algorithmic significance, but cannot replace that application-wide observation with its larger operator ratios.

Generality is adequate for a scoped algorithm paper, not broad workload superiority. The real range panel reuses the original records, has lengths approximately 1,000–28,696 and three univariate collections. SMD label-block sensitivity is useful but does not make every recording an independent physical source. Long real VUS tests up to 650,000 points are not long-real-range tests. The new million-point range inputs provide synthetic numerical stress only. At this cutoff, the new range timings come from one CPU environment.

## Public-review calibration

I used actual review contents, not average-score imitation. I read the shared calibration document and parsed the cached original-note records using `ast.literal_eval` for string-encoded `related_notes`, handling both plain and `value`-wrapped content. The four raw record hashes matched their metadata. Original OpenReview APIs remained inaccessible through the available route; the records came through the public WENJINLIU/Paper-Review-Dataset mirror. This is an explicit provenance limitation. These are adjacent ICLR examples, not a sample of PVLDB decisions.

- The accepted [One-Liners paper](https://openreview.net/forum?id=H27kvyG4qf), including its decision and reviews, shows the importance of limiting a conclusion to the tested metric and pipeline. The present paper addresses that analogous problem by separating oracle selection, operator speed, public-library factors and whole-consumer benefit. The concern would return immediately if those boundaries were blurred.
- The accepted [unsupervised model-selection paper](https://openreview.net/forum?id=gOZ_pKANaPW) received credit for an important problem, an understandable method and substantial real-data evaluation despite questions about combinations of familiar ideas. This supports considering usefulness and explanation alongside technical novelty; it does not imply that the present combination deserves acceptance automatically.
- The rejected [GraphSAD submission](https://openreview.net/forum?id=73U_NlKaNx) had objections about weak novelty, missing strong competitors and insufficiently separated component effects. The current compiled raster, bucket alternative, direct-ramp control and explicit loss case answer analogous attribution concerns. Modest novelty remains the common unresolved vulnerability.
- The rejected [DyAD submission](https://openreview.net/forum?id=G-dM79m_EXd) illustrates that useful data and a formal presentation do not compensate for unclear new principles or a theory/system disconnect. Here the range theorem predicts removal of repeated scans, and a matched compiled control observes that consequence. Merely counting lemmas or experiments would not have done so.

I did not infer unrecorded reviewer score changes from an area chair's conjecture, average these examples into a numerical threshold, or treat their outcomes as a probability model for this submission.

## Six user gates and prospective project thresholds

| User gate | Assessment at this cutoff | Evidence and boundary |
| --- | --- | --- |
| 1. Novelty against at least ten recent primary papers | **Pass, scoped** | Twelve recent primary-paper comparisons, plus the directly relevant older metric/component work and pinned public code. New distinction: exact metric-specific event statistics rather than a new metric, exhaustive objective or connectivity technique. Priority beyond the inspected literature remains unverified. |
| 2. Strong public baselines, three collections, uncertainty and ablation | **Pass for the whole paper** | Existing VUS studies compare eligible public baselines on three collections with paired intervals. New range evidence has all-73 same-compiler causal controls and adjusted intervals; public range comparisons are a smaller length-selected panel with censoring, not a new all-73 strongest-public result. |
| 3. Real generality and failures | **Pass, scoped** | Three real collections, eight score procedures, low-cardinality loss, dense-support and memory limits, label-block sensitivity and the limited consumer gain. No broad multivariate/general-range-metric claim. |
| 4. One-command fresh reproduction of main tables | **Pending for this manuscript** | Existing VUS reproduction is complete. The combined command now includes VUS and range studies on freshly generated arrays; the successor hosted executions are still running. A command's existence and saved-artifact audit do not establish its completed fresh execution. |
| 5. Three independent calibrated target reviews | **Not verified here** | This review supplies one independent assessment using public venue criteria and actual public review contents. I did not inspect the other reviews or infer collective completion/closure. |
| 6. Venue, track and deadline | **Pass** | PVLDB 2027 Regular Research, Foundations & Algorithms; prospective December cycle: abstract 25 November 2026 and paper 1 December 2026, both 17:00 America/Los_Angeles, under the current official monthly rules. These are 26 November and 2 December at 10:00 KST. |

The prospective **project 5** and **project 6** rules are not reviewer ratings. The numerical and scientific components of the five-point candidate rule have strong evidence, including the existing external VUS workflows. Formal completion of its requirement that all six evidence gates be addressed still depends on the current reproduction and collective review receipts.

The old batch arm of the six-point rule remains **failed**: Mac SMD 1.207 is below its prospective 1.25 requirement. Neither the Linux batch ratio nor the new range ratios can retroactively repair that exact test. However, the new range result **does earn a credible case for the separately allowed “comparably substantive generalization” arm**: a different existing operator needs different statistics, the proof removes a full per-query scan, and same-compiler experiments establish the resulting advantage on real data while retaining failures. This is more than another implementation constant or a restatement of the VUS result.

I would not mark the entire six-point project rule complete at this cutoff. New range and combined reproduction on the second environment remain pending, and this reviewer cannot certify that three independent reviews have no remaining major objection. The favorable scientific rating above is deliberately separate from those unclosed procedural/project conditions.

## Revision conditions and remaining weaknesses

There is no identified fatal proof error that requires a different algorithm. Before presenting the new package as fully reproduced, retain the completed combined-run source/input bindings, output curves, parity audits and raw timing receipts. If that run fails parity or produces a material failure of the main effect, the assessment must be reopened. A fresh run may legitimately generate different detector arrays; those arrays need their own identifiers rather than being represented as recovery of the first host's bytes. The command regenerates JSON scientific results; TeX packaging is a separate step.

For scientific claims, the following are concrete conditions, not requests to obtain a preferred score:

1. Keep the new contribution precisely at the metric-state level. An earlier exact implementation maintaining the same range statistics in comparable complexity would materially weaken the novelty claim and likely lower this recommendation unless another substantial contribution survived. Add the archival TimeSeAD citation alongside its pinned source.
2. Preserve the same-compiler control and full query contracts. A stronger reasonable compiled control that erased the exhaustive advantage would undermine the main significance argument. The public-library factors alone would not rescue it.
3. Keep low-cardinality loss, direct-ramp control wins, distinct `alpha` conventions, censored calls and the 1.031 whole-consumer result visible in the submitted version. Do not infer unrestricted threshold optimality or large application-wide acceleration from these measurements.
4. For a stronger recommendation, independently test longer real range workloads or controlled variation in length, distinct-score count and query count, including memory and repeated timing variability. Alternatively, measure a real range-enabled analytical workflow. These would establish the operating envelope more convincingly; they are not grounds to invent an already demonstrated full-consumer benefit.

The manuscript is now coherent enough to review as a whole first-archival paper. Its weakest point is not a missing theorem fix but whether a program committee values an exact, useful yet elementary operator specialization highly enough. I place it just above the acceptance boundary because the new range mechanism survives a fair compiled control and demonstrably reduces the cost of an existing exhaustive computation. I do not place it comfortably above that boundary because the state representation is narrow, the real range evidence reuses a modest-length panel, and the demonstrated application-wide gain remains small.

## Evidence identifiers

SHA-256 identifiers for the reviewed scientific inputs and saved reports:

| Input | SHA-256 |
| --- | --- |
| Initial reviewed PDF | `da132c602e81b38e7908143309a3d4b5ba7ffbf362445e2a92aaf22279ef3338` |
| Main TeX | `7dcc10616bcdec73e225800e7f58c22d32a5d5d71d03701c372a56f530d6fa72` |
| Body with combined-command clarification, before final packaging | `23e76668b5af3f0174bc26a46451dbc59c11e173a73f650eb5a9014f4e08bafe` |
| Range method | `dd10de84b9fbc899182853b246d837df8219ebdabe45e072706ec37a45392719` |
| Range results before final packaging | `4768e66c824da56bc2da8cfd92b534e8d19799f04ad22b386ed1ede91ec7ea83` |
| `src/sparse_vus/range_sweep.py` | `2e75e1afd2b86d4450afc43aaba3a892fd998f4fd5cfe7edda2b155bba479ccb` |
| `experiments/reproduce_range_sweep.py` | `7d8da9481ce2ab2d3835d6015625b983cff10f646c8dfdcd07dca51bbda302b8` |
| Prospective evidence design | `b25223764a5291a1144e060493d4a2217802a2a3b0469394644b35d05756289f` |
| Range main-study protocol | `de4d4778c7fc7a25a7f54a221e5434cd506cf5c643f9f6202f867269bddc20cf` |
| Range main-study records | `cb174dfc14e830730a3a7f95d889d76f4c7919f3113fc642ba6f3adda2185e47` |
| Range main-study independent audit | `82bc379cb16ec8c3bba64a823279f4f0e71270e083459f410118cb71f4d590b2` |
| Public-study-v2 records | `d40a70798766314a70217dfd5df895970acc3909498b86100f32caf11caa9958` |
| Public-study-v2 independent report | `21f7bbd74fbae5bb100596464cab4be215bb7701b9ddf2ea947e4e692c452472` |
| Range validation report | `ab00d5378b4f7e67cf9c9f1981331748f589f660551a8aa83686c98d88c13273` |
| Completed older VUS Linux verification | `944fd9a55303ff49ccc155182f38661682804f0dd239ebcf53a0100e04410506` |
| Compiled-support-control independent report | `ba8ea76283d68aa0d888673006c7a10743704137ceb4f700d6f9724ddc339330` |
| Public-consumer independent report | `ad2cb5ee149283e1ebb37e3d4cbfc8b0ba733f4be3a23e8852e8e1b1d15d5612` |
| Shared public-calibration document | `20ac021012eaffa354a45c312f6172e4e394a5e2f8bb5d756a5ce07fed9245f2` |

## Final packaging check, 24 October 2026

The later compiled PDF has SHA-256 **`434331a309a87b20d6079797c69c0d306143089db6ccf578532131fa32cd6cb6`**. Text extraction confirms **12 total pages, references starting on page 12**, and the `--include-vus` command. The corresponding body hash is `d47c67d378c76e65465b190aa71aeb3b9103c9176b2b1a3a800f463191ab97f2`; the range-results fragment is `f9e18646b643ab73b1583edf450b3a6d843241e53546d5d5f2673afbdeff9efa`. The range-method hash is unchanged. The introduction now explicitly integrates both operators, and the descriptive range-case figure retains the low-cardinality loss. This packaging check does not add a scientific result or close either pending Linux execution. The initial **6/10 weak Accept** judgment, its confidence and its largest weakness remain unchanged.

## Independent evidence addendum — 24 October 2026, 05:06 UTC

**Updated gate status: 5/6 at the documented process level; the canonical combined reproduction remains pending. Recommendation remains 6/10, weak Accept; confidence remains 3/5 overall and 4/5 on mathematics.** I verified that three separate combined-manuscript review files exist by counting filenames only. I did not read their contents, scores, or a coordinator decision. Consequently, the three-review count is now established, while my content-level verification of independence, calibration and scientific conclusions applies only to my own review.

### Prior work and claim boundary

I inspected the changed manuscript and directly read the author-uploaded primary text of [Menotti et al., *1D Component Tree in Linear Time and Space*](https://www.researchgate.net/publication/228747458_1D_Component_tree_in_linear_time_and_space_and_its_application_to_gray-level_image_multithresholding), including Algorithm 1 and Sections 3.1–3.4. This is closer prior work than the generic component-tree citation: it constructs the one-dimensional hierarchy by a spatial scan and stack, and discusses computing component attributes alongside construction. Its presented per-weight array has space proportional to integer amplitude, with stated complete space `O(max(n,m))`. The new manuscript correctly disclaims a novel or faster component-tree construction. I found no Tatbul overlap/cardinality aggregate in those inspected sections; that is not a claim of exhaustive absence throughout the literature.

This citation narrows attribution but does not remove the contribution on which my recommendation already rested: maintaining the **label-conditioned range metric**, including fragmentation-dependent recall and the component-average precision, under queried activations. A generic component hierarchy is not itself an evaluator for those formulas. The exact state is simple and its novelty remains modest. I would not present endpoint arrays, sorting or bucketing as independent inventions, nor assert a universal sorting lower bound. The revised text respects these boundaries. I also verified the archival TimeSeAD citation against the [official project documentation](https://timesead.readthedocs.io/en/latest/). The OpenReview PDF/forum route was browser-gated in this check; I do not claim to have newly retrieved that archival PDF. The source-level TimeSeAD comparison remains tied to the separately pinned implementation.

The added cost/fidelity paragraph is useful and numerically correct. From the original saved case timing records, I independently recomputed exhaustive-sweep/grid-bucket geometric cost ratios **2.189789, 2.135537 and 3.012701** for NAB, SMAP and SMD. This is a descriptive comparison of different query contracts, not another same-output speedup or a prospectively specified endpoint. Exact coverage remains more expensive than the fastest tested fixed-grid implementation; its value is eliminating that grid's omission of threshold states. This clarification improves scope without changing the underlying result.

### Completed auxiliary Linux evidence

I inspected the downloaded auxiliary range-only run **40061935240**, commit `d4eb3eddd0d441757ee31e149466528e41905c7d`. Its completion receipt describes fresh raw downloads, 73-case score generation and the range main/public/validation studies on an **AMD EPYC 9V45** hosted Linux runner. I independently checked that the three report hashes match that completion receipt. The local re-audit receipt reports agreement of provenance, discrete results and numerical reconstructions. Its approximately last-bit differences in derived exponential/logarithmic summaries are explicitly recorded; the post-observation `1e-12` re-audit comparison allowance is not a changed scientific metric-parity or timing endpoint. I did not rerun timing or metric evaluation for this addendum.

| Auxiliary Linux comparison | NAB | SMAP | SMD |
| --- | --- | --- | --- |
| Grid100 raster/bucket | 2.121 [1.871, 2.402] | 3.123 [2.748, 3.579] | 3.606 [3.399, 3.873] |
| Distinct raster/sweep | 30.92 [20.18, 47.73] | 28.64 [12.10, 54.85] | 164.66 [124.79, 195.88] |

Intervals retain the original per-comparison, three-collection familywise interpretation. The 2,628-record main audit passes, has maximum full-curve disagreement `2.9976021664879227e-15`, and has no cross-method winner-set disagreements. The low-cardinality SMAP loss persists. All public calls in this auxiliary run complete; this does not erase the two censored Mac calls. Public-value and million-point validation checks also pass within their declared tolerances. The new data support the direction of the range result on a second CPU architecture, but hosted background load, short records and reused collections remain limitations.

The score-comparison report prevents an overstatement of exact cross-host replication. Observation and label identities match, but **none of the 73 complete eight-profile score arrays is byte-identical across the two hosts**. Total grid-to-distinct counts happen to remain 24 changed winner sets, 15 nonoverlaps and 12 regrets at least .01, while two case-level change indicators and two nonoverlap indicators differ. SMD's maximum regret is approximately .080 here rather than .127 on the Mac. These are fresh-input runs with separate outputs, not identical numeric replicas or additional independent datasets. Hosts should not be pooled.

The selection record dated 04:32 UTC identifies **40062043152** as the canonical combined run, with a stated selection before either timing report was inspected. It retains the auxiliary run and prohibits selecting the faster host result. I respect that declared role: the successful auxiliary range-only execution does **not** close the pending combined VUS-plus-range command. The original completed VUS run and this new auxiliary run do establish two-host evidence for their respective methods; they do not substitute for the selected combined receipt.

### Explicit decision on the frozen project-6 review condition

**For this reviewer, no unresolved major scope, novelty, baseline or mathematical-validity objection blocks the narrowed substantive-generalization contribution.** My remaining novelty and application-significance concerns are acknowledged limitations compatible with that condition, not unresolved requests to invent a new tree algorithm or demonstrate a universal whole-consumer speedup. This judgment is specific to exact dynamic VUS plus the defined flat reciprocal-cardinality range operator, supported by the retained same-compiler controls and failures. It would not extend to a claimed general range-metric framework, new connectivity machinery, universally superior evaluation, or large nine-metric acceleration.

The new range mechanism therefore continues to satisfy my assessment of the **substantive-generalization alternative**. The auxiliary reproduction removes my earlier single-host reservation about the direction of its measured effect. It does not raise the score: the underlying conceptual contribution is unchanged. The old Mac SMD batch **1.207 < 1.25** failure remains a failure of that distinct prospective arm. The actual nine-metric workflow result remains **1.03088-fold**. The canonical combined run still needs its receipt, and the all-reviewers condition cannot be inferred from my assessment or from merely counting three files.

### Addendum evidence identities

| Reviewed input | SHA-256 |
| --- | --- |
| PDF at this check, before canonical completion | `8a33610506abcf11c6f06a2fc306d2c91d966cfb4005584657c0c549bc1c094b` |
| Body | `5922c47d75aef83b129c75435dae4a81403e9878b1926b03cabc656ef5381343` |
| Range method | `9bb42203627b35f1c33bef6e079734005260ac61b5c7bc63b979305126a5463d` |
| Range results | `5f2b695f703e0fc098fbea592cd681468aa700b646b3592bfcf208b53b92af80` |
| Bibliography | `b9f3ad7d5b95d1bf05cd920c3b2790b211c396cda4b7207be2ad7628906787f3` |
| Canonical/auxiliary selection | `a413908c69079b2a98a6ec660e402966f2ee027f24d171a5259fa1eb96f8a77f` |
| Auxiliary completion receipt | `c8b7e298122062729a6d5ff047530636b313afedc327cbb08184388311c6cd25` |
| Auxiliary local re-audit receipt | `b2f9271d3f7a1ef590410a7e6ed35e37fb9dab2d89f16be4a0be36d258f16141` |
| Auxiliary main independent report | `149cca1decf0f236694c823ed513476ed3ad7c8869ccd146e6945f85cad5b000` |
| Auxiliary public independent report | `9c22d7c2133b5e12a389bfdabd868d0cb2a62a791bbbd76f1149d80abb5a98f7` |
| Auxiliary validation report | `eb8117ade7bb3221f963a3e08e68933065ff1951674633a4f6598c61bc262cf9` |
| Auxiliary score comparison | `cf51864af547e60f52a84785e51dbb60cadafec8c564c31ecd946688392d35dc` |

## Final canonical-evidence assessment — 24 October 2026, 05:17 UTC

**Final documented gate status: 6/6 for the narrowed whole manuscript. Recommendation remains 6/10, weak Accept; confidence remains 3/5 overall and 4/5 on mathematics.** The previously pending reproduction gate is now supported by the selected combined execution and its retained evidence. The three-review count is verified without reading the other reviews; judgments about their content and their own remaining objections must come from those reviewers, not from me. This gate status is an evidence-checklist result, not an external decision or an assertion that every reviewer will accept the paper.

### What I independently checked

The canonical [GitHub run 40062043152](https://github.com/mandu5/sparse-vus/actions/runs/40062043152) is recorded as completed successfully at source commit `e2405e39ec23486a3d228240569b48785de32cb4`. Its fresh source-to-table step completed at 05:07 UTC, and the completion receipt explicitly has `include_vus: true`. It covers newly generated scores, the VUS primary and supplement, and the range main/public/validation studies on an **AMD EPYC 7763** host. This is the run selected in the prior selection record; the faster auxiliary EPYC 9V45 result has not replaced it.

I hashed the actual downloaded ZIP and obtained `cf9e0531b3ab00bc9f3f6d28113d62497f1ebe1c66b5eae2fe0fae915c898ec7`, matching the GitHub artifact digest. I also checked every listed durable replica file against the manifest: all **568 entries, 147,330,993 bytes**, matched both size and SHA-256. Those counts describe the verification boundary, not scientific merit. All four archived audit-report hashes match their declared reconstructed-report hashes exactly, and the completion receipt binds those reports and the validation report. The local re-audit receipt records PASS, exact reconstructed report hashes and no last-bit differences for this canonical run. The earlier permissive post hoc floating-summary comparison therefore is not needed to explain agreement in this instance. I inspected these receipts and bindings; I did not independently rerun the four reconstruction programs again in this final addendum or run new timings.

The primary and supplement audits have maximum PR discrepancies `8.88e-16`; the supplement's maximum workflow ROC discrepancy is `4.89e-15`. The range audit again has maximum full-curve discrepancy `3.00e-15` and no cross-method winner-set disagreements. Source/parent-bound selected-cut and stress validation pass. This is sufficient to close the promised fresh principal-study execution, beyond reconstructing the original saved outputs.

The canonical compiled-control range results are:

| Collection | Grid100 raster/bucket | Observed-distinct raster/sweep |
| --- | --- | --- |
| NAB | 1.900 [1.616, 2.239] | 29.35 [18.81, 46.08] |
| SMAP | 2.898 [2.624, 3.260] | 27.76 [11.63, 53.75] |
| SMD | 3.574 [3.412, 3.789] | 163.60 [125.92, 193.02] |

The same scope applies to the adjusted intervals as in the original experiment. Bucketing wins all 73 case medians; the exhaustive sweep retains its one low-cardinality loss, with SMAP534 raster/sweep approximately .661. Two public SMD187 calls are censored on this canonical host. The auxiliary host's completed calls do not erase this censoring. All 73 complete generated score matrices differ bitwise from the original Mac matrices; the unchanged observation/label identities and separate score hashes remain important. Aggregate 24/15/12 selection counts persist while two case-level indicators change. Thus this is reproduction of the declared pipeline and result direction on regenerated inputs, not a bitwise replay or an isolated CPU experiment.

I also inspected the final PDF, SHA-256 **`6646c1f497273f2e4731d158761568c26b7cf04b3b06978813aa1962518e3a11`**. Text extraction confirms **13 total pages, references beginning on page 12**: the main content fits the current twelve-page allowance excluding references. The Linux table, `--include-vus` command, score-generation caveats and Menotti attribution are present. Menotti's simultaneous height, surface and volume attributes are now explicitly credited, so generic component-attribute maintenance is not implicitly claimed as new. The new label-conditioned precision/recall identity remains the candidate distinction. The theorem's substance and my mathematical assessment have not changed.

### Final gate and prospective-rule assessment

1. **Novelty: pass within the stated scope.** Recent primary-paper comparison, direct older range-metric/component-tree work and pinned public implementations support a precise surviving difference. This is bounded evidence for modest operator-specific novelty, not proof of global priority.
2. **Main result: pass for the whole paper.** Existing same-contract external VUS comparisons cover three collections with uncertainty and ablations. The new range result survives a fused same-compiler control on both principal hosts. The smaller public range panel and its censoring remain visible.
3. **Generality: pass within the stated scope.** Real full-length profiles from three collections and eight score procedures, plus declared failures, are present. Reuse, univariate scope and the difference between real long VUS tests and synthetic long range tests remain unchanged.
4. **Reproduction: pass for the principal VUS and range studies.** The selected combined command now has a successful fresh execution, retained generated arrays/curves and auditable receipts. Separately frozen resource, long-recording/control, minimal-patch and public-consumer studies have their own commands; they are not represented as rerun by this command. TeX rendering is separate from numerical table generation.
5. **Mock reviews: pass at the documented process/count level.** Three review files exist. This review independently used verified public venue criteria and actual adjacent accepted/rejected review contents. I remain blind to the other two contents and scores and do not manufacture an aggregate scientific conclusion from their existence.
6. **Venue: pass.** The stated PVLDB 2027 Regular Research / Foundations & Algorithms scope and November 25 / December 1 prospective abstract/paper deadlines remain the target; no submission or acceptance is implied.

Under the frozen **project-5 rule**, I judge the required scientific and operational evidence supported: a surviving exact-evaluation contribution, three-collection full-precision results, positive paired lower bounds, complete stored-profile workflows exceeding the 1.5 threshold against the eligible external comparator, and no unresolved mathematical or measurement-invalidity defect. The new canonical primary workflow external/stream median ratios are approximately **20.09, 20.41 and 16.21** for NAB, SMAP and SMD. These are the defined stored-profile evaluation/selection workflows, not the public nine-metric consumer.

Under the frozen **project-6 rule**, the substantive-generalization alternative, the at-least-two-CPU condition and the at-least-twofold external stored-profile workflow condition are supported. **My own review has no unresolved major scope, novelty, baseline or validity objection to the narrowed contribution.** On those independently assessable conditions I would allow the six-point candidate milestone through the generalization route. The rule's conjunction over all three reviewers still requires each reviewer's own statement; this review cannot certify that conjunction while remaining blind to their contents.

This is not a retrospective repair of the original batch test: **Mac SMD 1.207 remains below 1.25**. Nor is the final evidence a new whole-consumer result: **1.03088-fold** remains the measured nine-metric improvement. The strongest weakness is still limited conceptual novelty and application-wide significance. Those limitations keep my recommendation weak rather than strong; completed reproduction does not itself increase the score.

### Final evidence identities

| Input | SHA-256 |
| --- | --- |
| Final PDF | `6646c1f497273f2e4731d158761568c26b7cf04b3b06978813aa1962518e3a11` |
| Final body | `f88d8618fc772bba3047658281adc0bf5890e6aa9dd81994bab10b38f7bca005` |
| Final range method | `eba5a76cd8cf89183bdde8559a321bc0464cef3c4beccce58a436e5658860092` |
| Final range results | `125372417c7940ebd8ae298d14d943d152a02552431870ff666015bcadcbe1e7` |
| GitHub run receipt | `753365ec600fc0e497bc1cfcb7a4fe7b94db9bd49befff18437e69d0e48e7121` |
| GitHub artifact receipt | `ed3ae7f24841f8fb31b2d8e3c02ed5bd3bc57617e51ac57dfe39b4b2fa0b013e` |
| Downloaded archive | `cf9e0531b3ab00bc9f3f6d28113d62497f1ebe1c66b5eae2fe0fae915c898ec7` |
| Durable replica manifest | `9e5babcc17b75f2dcb9879625966b16f17e734ea0a18b95b87f6e9160588c0d5` |
| Canonical completion receipt | `0457f8271d18d060f1bd3143ae957ff9ea76e599e965384ef8aab0f3d3ea0553` |
| Canonical local re-audit receipt | `55e3d7f7439bf133982b7106c2c881144b077460ed9c2e2dd3b151a0c549232d` |
| Canonical primary audit | `9fe355ecfcb8a27f13cad90d8d6da7ad1ae1acadc66c4a9df5bf8363687ba6b0` |
| Canonical supplement audit | `9e17112f09676514e689079203ae2534bf0dcac6a8267e7cbf3f42b1271bcee8` |
| Canonical range main audit | `b934652c89b067af465bf40b301d3e555e69f74d289a4fc5ac7796cc65471ae8` |
| Canonical public range audit | `82e234cd72a60c71b0a90fb1a333ecc9ff90e3794a10917661c4a8449a6329f8` |
| Canonical range validation | `f74dd276d66847c60f63a07a57688324536215b53bf0e992caba5dde82fba4a4` |
| Canonical score comparison | `691f6d8e07a5e6a81bbc3e6a144186d75bc199e73dcb79f62766bcc7b7b0ea2d` |
