**Four of six evidence gates are directly supported for this combined snapshot; gate 4 awaits fresh combined execution, and the aggregate three-review requirement in gate 5 is unverified by this blind reviewer. Next: complete the already launched reproduction and make the narrow algorithmic contribution and its workload consequence the center of the revision.**

# Independent mock PVLDB review: exact metric evaluation

Review date: 24 October 2026. Target: **PVLDB Volume 20, Regular Research, Foundations and Algorithms**. Intended cycle: abstract **25 November 2026**, paper **1 December 2026**, both **17:00 America/Los_Angeles**. Author: Youngmin Ko, Independent Researcher.

**Recommendation: Revise. Internal surrogate score: 6/10. Confidence: 4/5.** This is a new assessment of the combined manuscript, not a replacement for the earlier VUS-only review. The score is my internal research-review surrogate: 5 is borderline below a convincing contribution, 6 is a promising contribution warranting a bounded revision, 7 is an accept recommendation, and 8 or above would require a stronger contribution or substantially broader demonstrated value. This is **not the confidential CMT numeric form, a PVLDB score, an acceptance probability, or the project's separate 5/6 investment scale**.

**Largest weakness:** the conceptual advance is a narrow specialization of established event sweeps and component connectivity, while the strongest newly demonstrated consequence comes from a reused, author-generated eight-profile panel. There is now a substantive exact-operator result, but the manuscript does not establish a general metric-evaluation framework or a broad improvement to complete evaluation applications. The paper generally acknowledges these limits. My remaining reservation is significance and reach, rather than an identified correctness failure.

I did not inspect other internal reviews, scores, aggregate decisions, or agent listings. I used only the permitted public calibration files and my own earlier source-audit work. I preserved the old manuscript and `blind-final-review.md`. I did not run new timing experiments. I read the new method, its producers and record auditors, reconstructed both new audit reports, performed separate small direct-set correctness checks, and visually inspected PDF pages 1, 4, 5, 9, 10, 11 and 12. CodeGraph was unavailable.

## Reviewed version and venue basis

The reviewed PDF is `paper/exact_metrics_pvldb20261024.pdf`, SHA-256 **`da132c602e81b38e7908143309a3d4b5ba7ffbf362445e2a92aaf22279ef3338`**. It supersedes the task's initial `c87e9ad8...` PDF through a method/results rearrangement, which the coordinator confirmed did not change results. It has 13 total pages: substantive text extends onto page 12 and references start on that page. Thus it fits a 12-page content limit; it is not an 11-page-content paper. The inspected pages have readable equations and tables, and the first page identifies the author and affiliation.

The [current research call](https://www.vldb.org/2027/call-for-research-track.html) treats formal algorithms as the primary contribution of the selected category and encourages prototype evaluation. It explicitly includes time-series analytics. The [submission guidelines](https://www.vldb.org/2027/submission-guidelines.html) require a substantive data-management connection, appropriate evaluation context, and accessible supplementary artifacts; regular papers have at most 12 non-reference pages and are single blind. The [deadline page](https://www.vldb.org/2027/important-dates.html) confirms the monthly 25th/1st cycle and 5 p.m. Pacific time. The disclosed unrefereed software precursor does not by itself turn this into a resubmission of a previously refereed publication.

There is a defensible scope argument: this paper changes the cost of recurring aggregates over stored detector scores, and its VUS operator directly builds on the [PVLDB VUS paper](https://www.vldb.org/pvldb/vol15/p2774-paparrizos.pdf) and the subsequent VLDB Journal efficiency work. That is a substantive connection, not merely a citation to an unrelated database paper. A DBMS integration is not necessary for this category. Conversely, being an anomaly-detection metric does not automatically establish significance for data management; the repeated-query workload and the amount of work removed must carry that argument.

At the PDF cutoff, section 10 displayed only the old VUS reproduction command. During this review, I reported that ambiguity. The subsequently inspected source and README now give `python experiments/reproduce_range_sweep.py --include-vus --output /tmp/exact-replica`. The helper actually composes original VUS primary/supplement execution and the range main/public/validation stages using the same freshly generated scores. This corrects the command's scope in source and documentation. The PDF has not yet incorporated that change at this review's hash cutoff, and no completed fresh combined or fresh range-only Linux receipt was available to this reviewer. Launching those jobs is not their completion.

## Summary and surviving contribution

The paper evaluates two existing metrics without proposing a new detector or a new quality measure. The original VUS part removes zero-contribution PR events, retains the necessary ROC predecessor rectangle, respects global ties, and shares label-related work across score columns. Its public software precursor and its modest additional sharing gains remain disclosed.

The new range part maintains flat, reciprocal-cardinality Tatbul precision and recall under point activations. For each true interval it maintains active mass and the number of intersecting prediction components. For each predicted component it maintains its precision contribution, using fixed truth-prefix counts to recover overlap mass and true-interval cardinality. In one dimension an inactive point's active neighbors are component endpoints, so a merge needs only endpoint arrays. Sorting and activating scores produces all observed strict-threshold values in `O(n log n + n)` time; a known set of `H` ordered queries can instead be processed in `O(n log(H+1) + n + H)` through ordinary offline bucketing.

The useful distinction is **metric-specific maintenance of the overlap/cardinality aggregate while its component partition changes**, not the invention of descending connectivity, union-find, endpoint merging, sorting, or query bucketing. False-label activations still matter to precision, and recall can decrease when an additional fragment raises its cardinality penalty. Therefore this is a different exact reduction from the earlier support-only VUS reduction. It is more than another loop-ordering change to the released VUS implementation.

In my assessment this is a **substantive, independently supported specialization**, enough to justify the research continuation and a revision-level paper. It does not establish a new general component-tree algorithm. The magnitude of its practical benefit must also remain separated from the ease of deriving it after writing down the appropriate sufficient statistics.

## Novelty and closest comparisons

[Tatbul et al.](https://papers.neurips.cc/paper_files/paper/2018/hash/8f468c873a32bb0619eaeb2050ba45d1-Abstract.html) already define range precision/recall and its customization factors. [Najman and Couprie's component-tree work](https://doi.org/10.1109/TIP.2006.877518) already processes connected upper level sets efficiently. Neither the interval metric nor the connectivity sweep should be claimed as new. The current paper credits both.

The most important software comparator is [TimeSeAD classic at `bb8efa9ce17f9cfb0bab77df08c32d986de8429e`](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/evaluator.py), not only prts. It already enumerates all observed strict score thresholds. Its scalar interval routine uses moving pointers and flat-bias sums, making the relevant repeated computation linear per threshold; its outer loop does not maintain components across thresholds. The contribution is reducing that repeated work, not making exhaustive threshold selection possible for the first time. Its classic maximum uses alpha zero and float32 PR/F storage, which are material differences from the primary alpha-.2 float64 study.

My separate [prior-art/source inspection](range-sweep-novelty-feasibility.md), with the [retrieval manifest](../../../artifacts/pvldb-research-20261024/range-sweep-novelty/retrieval-manifest.json), inspected pinned paths in TimeSeAD, prts, current aeon, TimeEval, TSB-AD, a preserved C++ TSAD-Evaluator copy, and recent evaluation repositories. I found no equivalent complete Tatbul threshold sweep in those inspected paths. That is a bounded negative search result, **not a proof of novelty**. The original Intel repository was unavailable, a notebook implementation was not fully audited, and a global exhaustive code search was not performed. The surviving C++ scalar copy was inspected but not timed; TimeSeAD should therefore be described as the strongest selected public all-threshold API comparator, not a proved fastest public implementation under every input regime.

The recent-literature coverage is adequate for the user's ten-paper comparison gate. The combined manuscript's comparisons and the source audit collectively distinguish at least the following 2024–2026 primary works: the 2025 VUS efficiency paper, TSB-AD, PATE, TAB, TSB-AutoAD, RAMSAD, mTSBench, the foundation-model pipeline analysis, the formal metric study/LARM-ALARM, CCE, the problem-oriented metric taxonomy, and adversarial metric/seed-shopping analysis. The source audit additionally examines the metric-maze review, DQE, MTAD, TimeSeriesBench and the October 2026 methodological review, with inspection depth stated. These are not ten equivalent competing algorithms: some motivate the workload or qualify metric interpretation. The old Tatbul and component-tree sources and the pinned TimeSeAD implementation remain closer to the new computation than most of those recent papers.

One precise surviving distinction is: **the candidate computes the existing dynamic VUS aggregate through support events and the existing flat reciprocal range PR/F aggregate through constant-time local overlap/cardinality updates, whereas the inspected nearest exact range evaluator reconstructs threshold-specific interval statistics.** Counting papers, code files or passing checks does not establish the importance of this difference.

## Correctness and semantics

I find the local-statistics proposition sound within its stated domain. Inserting a true point changes only its own contiguous true interval's active mass and fragment count; the change in that count is one minus the number of active same-truth-interval neighbors. Inserting a false point cannot join two fragments lying inside the same contiguous true interval. Precision removes at most two adjacent component terms and adds the merged component term. The component count used in the outer mean changes with the merge. Prefix counts handle a true interval already in progress at a component's left boundary. Interior endpoint-array entries can be stale because only a component boundary adjacent to an inactive point is queried.

Complete eligibility at a query, including all equal scores, is essential. The implementation activates strictly greater scores, not `>=`; it does not expose intermediate tied states. Bucketing preserves this eligibility without sorting all scores. Query-order restoration and repeated queries are implemented. The strict observed-score domain excludes the below-minimum all-active state, so the returned maximum is not an unrestricted optimum over every threshold mask. The manuscript now states this distinction and supports a lower sentinel when requested.

The mathematical default uses zero for empty collections. TimeSeAD has different empty-mask conventions, and TSB-AD has an all-one parser corner case. The separate TSB compatibility flag does not make every public package semantically identical. The evaluated real panel contains positives, negatives and nonconstant score vectors, so these differences do not invalidate the reported comparisons. The public TimeSeAD experiment checks its maximum F value within its declared float32 tolerance; it does **not** establish identical returned thresholds, PR arrays or numerical tie sets for every input.

I reran the main and public auditors. Both returned objects exactly equal to their archived JSON reports:

- Main: 2,628 records covering 73 series; 438 canonical curve archives; maximum reconstructed cross-method curve discrepancy **2.9976021664879227e-15**; zero model-winner-set disagreements across methods at the fixed tolerance.
- Public: 72 records; maximum completed scalar discrepancy **6.661338147750939e-16** for TSB grid and **5.6508299595137146e-8** for TimeSeAD classic; **two censored public calls** retained.

These audits check recorded arrays, provenance bindings, coverage and numerical summaries. They cannot authenticate wall-clock measurements or substitute for a mathematical oracle. I additionally wrote a separate direct set-intersection check in a temporary process. It covered all binary-label/ternary-score pairs through length four, followed by 300 cases from an independent seed, with alpha in `{0,.2,1}`, arbitrary query order, repeated queries, infinite sentinels, and degenerate labels. Across **1,854 input cases and 13,524 threshold states**, raster, sweep and bucket agreed with that oracle within **2.2898349882893854e-15**. No new timing conclusion follows from these checks.

The archived public binary-prediction validation checks all 584 profiles at both recorded maximizing cuts: 1,168 values with maximum error **4.614364446098307e-16**. This independently checks the value at each cut, not maximality over untested cuts. The three million-point numerical stress inputs give maximum discrepancy **2.2250185795861794e-12**, with the recorded maximizing query index preserved in each comparison. Those stress outcomes are empirical, not a length-independent rounding certificate. Compensated summation and finite real binary64 input restrictions do not imply bitwise agreement or an all-input floating-point proof.

I found no unresolved mathematical or numerical validity defect in the stated operator claims.

## Experimental support, baselines and limitations

The strongest new evidence is the comparison against a fused, compiled `O(Hn)` raster with constant reducer workspace. It returns the same curves and maxima, includes validation and query construction, and uses the same compiler/runtime family. It therefore addresses the objection that the entire advantage is a Python-versus-compiled comparison. Prefix recomputation is a secondary, weaker control, not the headline baseline.

| Collection | Grid100 raster/bucket, geometric ratio [familywise 95% CI] | All-observed raster/sweep, geometric ratio [familywise 95% CI] | All-observed case wins |
|---|---:|---:|---:|
| NAB | 1.719 [1.625, 1.814] | 27.80 [18.74, 41.94] | 20/20 |
| SMAP | 1.994 [1.817, 2.252] | 21.44 [8.57, 43.14] | 16/17 |
| SMD | 1.969 [1.884, 2.095] | 128.08 [95.09, 154.61] | 36/36 |

The confidence intervals are paired resampling summaries of case medians, adjusted across three collections separately per comparison. They are not a population generalization guarantee or a joint correction over every analysis. Eight balanced grid orders are stronger protection against ordering effects than the two all-observed repetitions. The large all-observed ratios are nevertheless difficult to explain as small timing noise alone. Equal weighting of SMD's nine label blocks retains an all-observed ratio of **112.34 [46.21,167.79]**.

Absolute operator costs make the benefit more concrete. From the raw records, the median eight-profile SMD case costs about **4.436 s** for exhaustive raster and **0.0310 s** for sweep. The corresponding grid costs are **0.0193 s** and **0.00989 s**. These are medians across complete case calls, not measured collection-workflow latencies. Their interpretation is a cheaper repeated metric query; they do not imply faster detector training or inference.

The exactness consequence is also real within this panel: grid100 versus observed thresholds changes 24/73 winner sets, with **15 disjoint winner sets** and **12 cases of best-grid-winner regret at least .01**. The per-collection disjoint counts are 6/20, 3/17 and 6/36; maximum regrets are .4391, .1498 and .1275. The regret takes the best exhaustive value among the grid winners, avoiding an arbitrary tie-index penalty. This is a useful measured evaluation consequence. It is not new evidence that metric approximation can affect rankings in principle, nor proof that an oracle threshold improves deployable detection. The .01 level is a metric-scale reporting cutoff, not a validated application loss.

The external comparisons are sensibly separated. Unchanged TSB-AD grid100 has alpha .2; unchanged TimeSeAD classic has alpha zero and different storage precision. The nine-record panel is chosen by length, not representative sampling. For TimeSeAD, the two calls on SMD187 exceed the 60-second budget and have no completed public-output validation; the candidate's approximately 33.65-ms median cannot turn those censorings into exact speedups. The public-library factors combine algorithmic and runtime differences. They support relevance to actual public APIs, while the compiled raster supports the algorithmic claim. I would not require timing every slow public threshold loop on all 73 cases merely to reproduce the same asymptotic comparison, given the complete compiled panel and selected-cut public checks.

The following adverse results and limits remain material:

- **Low cardinality loses.** On SMAP534, the eight profiles have only 3–11 distinct scores; exhaustive raster is 0.838 ms versus sweep's 2.012 ms, a ratio of .4166. Sorting/state maintenance is not universally faster. At grid100, the score-sorted sweep is geometrically 1.39/1.41/1.87 times slower than bucketing, although one SMAP case favors it.
- **Reused, limited score workload.** The range extension uses the same 73 recordings and 584 generated profiles. Sixty-two recordings were previously measured by name. SMD has nine label geometries, and 18 cases share a development-file label geometry. The eight CPU procedures use fixed trailing windows and transductive fits; they are not eight tuned public detector pipelines. No constant profile occurs in this real panel. This weakens claims about the frequency or practical importance of the selection effects outside the panel.
- **No new complete-consumer result.** The measured nine-metric consumer remains 34.260 to 33.234 seconds, about **1.03088x**, despite VUS itself improving about 66.07x. VUS was about 2.7% of that baseline. Affiliation remains the dominant unmodified stage. Range-operator speed cannot be substituted into an unmeasured total-workflow speed claim.
- **The old VUS negative control survives.** A matched compiled conventional support control beats the released scalar evaluator on all 73 cases, with control/released ratios about .910/.960/.978. Its remaining control/stream gains are only 1.357/1.201/1.166. There is no isolated primary-panel demonstration that the nearest-distance geometry itself is superior to conventional ramp construction; multiple implementation details differ.
- **The original incremental threshold still fails.** The original SMD released/stream ratio is 1.207, below the prospectively specified 1.25 target; the newer compiled-control study's corresponding ratio is about 1.193. The extension does not retroactively change those outcomes.
- **Other VUS limits remain.** Dense support narrows the advantage, and at positive fraction .9 the dense control slightly beats released sparse. The retained batch representation raises peak RSS; one synthetic study has stream about 225 MiB versus released 175 MiB. Long real series support the whole-method benefit, but sharing uncertainty includes one on part of that panel. The certificate-plus-fallback development policy costs 33.93x with no early certification, and prefix activation can visit essentially the entire input.
- **Host differences are real.** The original VUS has completed two-CPU reproduction, but generated score arrays can differ. The SVM diagnostic has identical standardized inputs yet 104 versus 105 support vectors and VUS-PR about .3093 versus .3329. Saved same-host metric checks reproduce the difference; the later Linux arrays are not recovered bytes from the original runner. The range extension's new timing evidence reviewed here is still Apple-host evidence.
- **Scope and resources.** The range theorem covers flat reciprocal-cardinality variants with the stated alpha parameter, not all Tatbul biases, arbitrary interval metrics, other VUS ramps, multivariate event definitions or streaming updates to the score/label database. Sweep/bucket add `O(n)` state versus the raster reducer's constant workspace, plus curve output. The range extension lacks a fresh process-level memory comparison. Million-point stress checks numerical behavior, not real-domain or latency generalization.

These are not reasons to discard successful results, but they constrain the paper's conclusion.

## Public-review calibration and recommendation rationale

I used [public-calibration.md](public-calibration.md) and its hash-identified note metadata. These are adjacent ICLR reviews obtained through a public mirror; original OpenReview bytes were not live-compared. The accepted and rejected cases are useful analogies, not a numerical mapping to PVLDB.

The accepted *When Foundation Models are One-Liners* case warns against extending a pipeline-specific observation to all models and shows why statistics and strong simple controls matter. This manuscript now addresses that objection better: it exposes its actual compiler-matched control, ties, dependencies and failed regimes. The accepted *Unsupervised Model Selection* case demonstrates that a useful specialized combination of known ideas can be a contribution. It supports evaluating the practical value of these local statistics instead of demanding a new general-purpose data structure.

The rejected subsequence-GNN case's missing-baseline and component-attribution objections are substantially answered for the new range result by the fused raster and the separate public contracts. The older VUS geometry attribution remains limited and is disclosed. The rejected dynamical-system case's unclear-contribution objection remains the best caution: many correct proofs and extensive artifacts do not, by themselves, establish an important research contribution. The new local-statistics result makes that contribution identifiable, but its reach remains modest.

I therefore move the **new combined paper** to **Revise, surrogate 6/10**, without revising the old paper's assessment. The range result is sufficient to warrant a serious bounded revision. A rejection based only on the old batch increment or the 1.031x consumer result would ignore the new exact-operator contribution. An unconditional strong-accept assessment would overstate what two specialized operators, a reused score panel and a short-record public comparison establish.

## Falsifiable revision conditions and what would change this judgment

1. **Finish and accurately scope fresh reproduction.** A successful isolated run must regenerate score inputs, run both original VUS studies and the new range stages, and produce complete matching-design audit receipts. Report host-specific scores, censorings and unfavorable timings rather than pooling them. A source/README correction alone does not meet this condition. Failure of those checks would reopen validity, whereas a successful run closes an artifact gap; it does not independently prove novelty.
2. **Make the claimed novelty assessable from the paper.** The introduction's contribution list still describes three VUS contributions while the new title and abstract promise two operators. Revise it to identify the range statistic update as a separate result, state the ordinary component-tree machinery it assumes, and present the nearest TimeSeAD/compiled-raster comparison next to the range method. The paper should let a reader tell exactly which repeated work is eliminated and why support-only or monotone-recall shortcuts are invalid. A broader claim about a family of arbitrary interval metrics would require an additional theorem; no such claim is established here.
3. **Keep consequence and application claims falsifiable.** Preserve the distinction between the grid100 target, the exhaustive strict observed-score target and the alpha-zero public target. Preserve the low-cardinality loss, the two public censorings and the 1.031x consumer result. A stronger significance claim would need a predeclared workload from a separate public score-producing pipeline, or a directly measured repeated-query consumer whose dominant cost is this operator. If the new workload has negligible absolute savings and no material fidelity consequence, that is evidence against the stronger claim. I do not require a new detector, a GPU system, or a universal multi-metric speedup for the current narrow paper.

These are bounded conditions, not a request for indefinitely increasing test counts. I have no concrete counterexample to the local-update identity and no detected invalid timing comparison in the new principal table. Further work is scientifically justified because there is now an exact computational reduction with matched-compiler evidence and a measured fidelity consequence. Repeating the same 73-case timings without resolving a new uncertainty would add little.

## Six evidence gates, assessed separately from the venue recommendation

The thresholds below are those in `docs/superpowers/specs/2026-10-24-pvldb-evidence-design.md`; I have not revised them.

| Gate | Status at this review cutoff | Evidence and qualification |
|---|---|---|
| 1. At least ten recent primary comparisons and a surviving distinction | **Pass, bounded** | Recent-paper comparisons exceed ten without counting software as papers. Tatbul, component trees and TimeSeAD are explicitly credited. The local overlap/cardinality update survives the inspected comparisons; global novelty remains a bounded-search judgment. |
| 2. Strong eligible public baseline on three collections, paired uncertainty and ablations | **Pass for the combined, scoped claim** | Original exact VUS public comparisons on all three collections and strongest internal controls remain. The new range result has an all-73 compiled control with paired adjusted intervals, plus unchanged public APIs on three length-selected cases per collection. Do not describe the author raster as public SOTA or equate the alpha-.2 main study with the alpha-zero public study. |
| 3. Real full-precision inputs, eight families, explicit failures | **Pass within declared scope** | Complete real recordings, eight fixed procedures, ties and unfavorable cases retained. The range study is reused exploratory data, not a new held-out panel; it is not an accuracy evaluation of tuned detector pipelines. |
| 4. One command reconstructs the principal table from fixed sources/inputs; fresh execution distinguished from audit | **Partial; not yet passed for the new combined package** | Original VUS has fresh two-host evidence. New range record audits reproduce exactly. The corrected combined command is implemented and documented, but its fresh execution and the new range-only Linux run were pending. |
| 5. Three independent venue-form internal reviews with public accepted/rejected calibration | **Unverified aggregate; this review's part completed** | This is an independent criteria-based review with explicit surrogate score, confidence, largest weakness and calibration. I intentionally did not inspect other reviews or count their recommendations. The coordinator must verify the aggregate requirement without treating one reviewer as three. |
| 6. Venue, category, scope, deadline and exact contribution | **Pass** | PVLDB v20 Regular Research / Foundations and Algorithms, the November-25/December-1 cycle, and the two exact operator contributions are specified. Content fits 12 pages. This is a target, not a submission receipt. |

Thus **4/6 are directly supported, one is pending and one is deliberately unverified** in this blind assessment. This is a statement about evidence closure, not a rule that four passes mathematically imply a referee score of six.

## Original project 5/6 investment criteria

**Project 5:** The underlying scientific/numerical conditions remain supported: an identifiable contribution, three real full-precision collections, paired lower bounds above one against eligible exact baselines, and stored-score collection-workflow gains above 1.5x, with no mathematical or measurement-invalidity defect identified here. For the new combined artifact, an unconditional claim that every evidence gate is closed should wait for gate 4's receipt and the coordinator's independent-review accounting.

**Project 6, original batch branch:** **Not met.** The original SMD 1.207 result is below 1.25. Neither a later host's favorable value nor a changed baseline replaces that prospective result.

**Project 6, alternate-generalization branch:** **Supported by this independent assessment.** The range result is not present in the released VUS evaluator, targets a different native metric contract, requires different local statistics including off-label events and fragmentation penalties, removes the repeated `Hn` scan term, and has large paired gains against a conventional same-compiler control on all three collections plus a measured exactness consequence. This is comparably substantive as a specialized operator generalization, even though its connectivity machinery is classical. It does not become a general metric framework merely because the alternative branch is supported.

The other fixed project-6 conditions must not be silently rewritten. The original directly measured stored-score collection workflows exceed 2x against the strongest eligible public baseline, and the project has two CPU environments through the completed VUS reproduction. The 1.031x nine-metric consumer is a different, adverse application workload and stays visible; it does not retroactively redefine the original stored-score workflow threshold. The new range mechanism itself has only one completed timing host at this cutoff. Finally, **I cannot certify “no unresolved major scope, novelty, baseline or validity objection in three internal reviews” while remaining blind to the other reviews**. In my own technical assessment, no major validity or baseline defect was found; the outstanding scientific reservation is the narrow significance of the specialization. Full project-6 closure is therefore conditional on the remaining artifact/review evidence, not established by my score alone.

## Exact artifact identities

SHA-256 values below identify the inspected scientific snapshot. The canonical curve-tree digest is computed from 438 `.npz` files sorted by filename, concatenating `sha256 + two spaces + filename + newline` for each file, then hashing that UTF-8 text. The record auditors additionally check each archive's individual recorded digest.

```text
paper/exact_metrics_pvldb20261024.pdf
  da132c602e81b38e7908143309a3d4b5ba7ffbf362445e2a92aaf22279ef3338
paper/exact_metrics_pvldb20261024.tex
  7dcc10616bcdec73e225800e7f58c22d32a5d5d71d03701c372a56f530d6fa72
paper/exact_metrics_pvldb20261024_body.tex (PDF snapshot source)
  03b6fe471fe2c799693783a153690a247f0a71f0c6fc7c5124e1788c6aff6504
paper/exact_metrics_pvldb20261024_references.bib
  c4be4de01c41394d63036d1993694c33da39fd2a1f1636f1d43e55a8bc2dae0d
paper/range_sweep_method.tex
  dd10de84b9fbc899182853b246d837df8219ebdabe45e072706ec37a45392719
paper/range_sweep_extension.tex
  4768e66c824da56bc2da8cfd92b534e8d19799f04ad22b386ed1ede91ec7ea83
paper/pvldb20261024_tables.tex
  6e41e18f56568848453e91d53599799a2f93ebd73f2fb0ea14b8427585d24b84
src/sparse_vus/range_sweep.py
  2e75e1afd2b86d4450afc43aaba3a892fd998f4fd5cfe7edda2b155bba479ccb
experiments/range_sweep_study.py
  74ea8b546ef1de8384a15e675d6584616011092e4b2eb887c0b3531ed237e57c
experiments/audit_range_sweep_study.py
  4216ff9a37df4e6c4cf7507fba3ec95b4e061e0584c68f155ffc6e3119a88876
experiments/range_sweep_public.py
  19cd498100297d42b4b45e150e0f1b6343b52c0e4cea1823bd56b7965689d985
experiments/audit_range_sweep_public.py
  17fc2817253c26acd1f8e644b3212d19cd1e0c36307cfb88c9fe46619006f405
experiments/range_sweep_validation.py
  5453f30e8af5056fd71844203c5d214cf322dba0bd5e39bd9e8e60176064038e

artifacts/pvldb-research-20261024/range-sweep/main-study/protocol.json
  de4d4778c7fc7a25a7f54a221e5434cd506cf5c643f9f6202f867269bddc20cf
artifacts/pvldb-research-20261024/range-sweep/main-study/records.jsonl
  cb174dfc14e830730a3a7f95d889d76f4c7919f3113fc642ba6f3adda2185e47
artifacts/pvldb-research-20261024/range-sweep/main-study/independent-report.json
  82bc379cb16ec8c3bba64a823279f4f0e71270e083459f410118cb71f4d590b2
artifacts/pvldb-research-20261024/range-sweep/main-study/complete.json
  983eed9546d2c19166e9a590976a5431c8767aaaa4524426ec88cf2d66fba37d
artifacts/pvldb-research-20261024/range-sweep/main-study/curves (438-file tree digest)
  1507a380817597fcf3ef2df5c344ff5dea2c79a30c366a3e31d3e5e213e3d548
artifacts/pvldb-research-20261024/range-sweep/public-study-v2/protocol.json
  ceb5befda804e15da0df5fd02e75c3e6d517ac8eae8cf634a34153a1f6f3dc11
artifacts/pvldb-research-20261024/range-sweep/public-study-v2/records.jsonl
  d40a70798766314a70217dfd5df895970acc3909498b86100f32caf11caa9958
artifacts/pvldb-research-20261024/range-sweep/public-study-v2/independent-report.json
  21f7bbd74fbae5bb100596464cab4be215bb7701b9ddf2ea947e4e692c452472
artifacts/pvldb-research-20261024/range-sweep/validation/protocol.json
  4d526f0c70706890ee8b1838bf7d73d9bde71bd26bd7706ff0c7125ab0caa24f
artifacts/pvldb-research-20261024/range-sweep/validation/report.json
  ab00d5378b4f7e67cf9c9f1981331748f589f660551a8aa83686c98d88c13273
artifacts/pvldb-research-20261024/full-precision/inputs.json
  9b1dc600e9f13052408c69a796064742236a12de8435ec32d897f7d9a04117b0
artifacts/pvldb-research-20261024/full-precision/independent-audit-v3.json
  b6ed65bbc88f69fe6edd3e0ca2ed578881888368301899bbdff83479cf06bdcf
artifacts/pvldb-research-20261024/supplement/independent-report-v3.json
  99396de3367f579cc55380c85c75526a7297b0157ff399e968d1779d49b2b7c2
artifacts/pvldb-research-20261024/linux-reproduction/verification-summary.json
  944fd9a55303ff49ccc155182f38661682804f0dd239ebcf53a0100e04410506
artifacts/pvldb-research-20261024/linux-reproduction/reproduction-complete.json
  cf5c8681954499f317e35efd4bca7b84442318a6b324732a0bac0d4e20e1899e

docs/superpowers/specs/2026-10-24-pvldb-evidence-design.md
  b25223764a5291a1144e060493d4a2217802a2a3b0469394644b35d05756289f
docs/reviews/20261024/public-calibration.md
  20ac021012eaffa354a45c312f6172e4e394a5e2f8bb5d756a5ce07fed9245f2
artifacts/pvldb-research-20261024/public-review-calibration/verified-note-metadata.json
  6747875eec0a7baff778094643550be3542aca6c899643788ec562c7f55852ba
artifacts/pvldb-research-20261024/range-sweep-novelty/retrieval-manifest.json
  dcfb83dae4c921b73b4b28874519564b87adfeddad08eb83b4c91605d0a9f1b5
docs/reviews/20261024/blind-final-review.md (unchanged earlier review)
  bcac317c06f758190a382bdd740812c13feed1a936b7f05f7d82654fcd00e114
```

Later documentation changes separately inspected before this review was written:

```text
paper/exact_metrics_pvldb20261024_body.tex (combined-command correction)
  23e76668b5af3f0174bc26a46451dbc59c11e173a73f650eb5a9014f4e08bafe
experiments/reproduce_range_sweep.py (includes --include-vus)
  7d8da9481ce2ab2d3835d6015625b983cff10f646c8dfdcd07dca51bbda302b8
docs/REPRODUCE_PVLDB_20261024.md (combined-command instructions)
  93bfc9fec406849a45bae48aa400046e9d603d26a7abe72feb42223b18298dc5
```

These later file identities do not change the reviewed PDF hash or turn an executing reproduction into a completed one. A completed receipt or subsequent manuscript revision should receive a dated addendum, not overwrite this assessment.

## Addendum: packaging revision inspected on 24 October 2026

After the assessment above was written, I inspected PDF **`434331a309a87b20d6079797c69c0d306143089db6ccf578532131fa32cd6cb6`** and its changed source. The initial assessment is preserved as the first 36,530 bytes of this file, SHA-256 `881ddf8d3c79087355d33508bc90c7b4ce7a344e281d4c61971c747275b07ec2`.

The new PDF has **12 total pages**, with substantive text and the start of references on page 12; it remains within the regular-paper content limit. The introduction now explains both operators and names the local-statistics identity in its contribution list. It explicitly credits sorting and connectivity as prior machinery. The combined reproduction command is also now in the PDF. These changes resolve the presentation mismatch in revision condition 2 and the displayed-command ambiguity; they do not add a general-family theorem or new experimental evidence.

The large original VUS operating-range plot has been replaced in the paper by a descriptive range-case plot, while the relevant original controlled results remain in prose and the artifact. I inspected the new plotting source, independently reconstructed all **73** plot-data rows from the already audited raw records, and visually checked the resulting PDF page. The plotted quantities are case-median raster/sweep or raster/bucket ratios. The low-cardinality SMAP534 loss remains visible, and the caption correctly describes the observations as a fixed panel rather than controlled interventions on query count or length. The method source, frozen kernel, numerical producers and numerical results are unchanged.

**Recommendation remains Revise, internal surrogate 6/10, confidence 4/5 at this cutoff.** The identified contribution and the project-6 alternate-generalization assessment remain supported. The packaging correction is credited as completed; I am not carrying it forward as an unresolved defect. The fresh range-only and combined Linux executions were still pending, so gate 4 remains partial and the six-gate count remains 4 directly supported, one pending and one aggregate-review requirement unverified. The principal scientific reservation remains the modest reach of a specialized operator contribution and its reused score workload. A completed receipt would close the reproduction issue; it would not by itself determine the venue recommendation.

Additional inspected hashes:

```text
paper/exact_metrics_pvldb20261024.pdf
  434331a309a87b20d6079797c69c0d306143089db6ccf578532131fa32cd6cb6
paper/exact_metrics_pvldb20261024_body.tex
  d47c67d378c76e65465b190aa71aeb3b9103c9176b2b1a3a800f463191ab97f2
paper/range_sweep_extension.tex
  f9e18646b643ab73b1583edf450b3a6d843241e53546d5d5f2673afbdeff9efa
paper/range_sweep_method.tex (unchanged)
  dd10de84b9fbc899182853b246d837df8219ebdabe45e072706ec37a45392719
experiments/plot_range_sweep_results.py
  cd11e485551b811209a854d5f58a307fae3b68bf0cbabc159fe799f79d56136f
paper/figures/range_sweep_cases.pdf
  348927109f509219aba3878575a532176da115b07d511a318ed81eba1a8617f3
artifacts/pvldb-research-20261024/range-sweep/figure-data.json
  df245b538c7dab4eec8fb1c4e19b6b2e80b78aecf411f6d294e06d730733981f
```

## Addendum: auxiliary Linux evidence and prior-art clarification, 24 October 2026

**Five of six gates are now addressed if the coordinator's three-review count is accepted; gate 4 remains pending for the prospectively selected combined execution. Next: inspect that run's completed receipt and the final compiled manuscript.** Four gates are directly supported by my scientific review, and the fifth is a process-count attestation. I have not inspected other reviewers' files, scores, objections or the coordinator's decision document. The preceding 39,738 bytes, SHA-256 `a25e68e30c97d018d08c1b2e917c150c62b750e5e351b101d91c28639c22a564`, are preserved unchanged.

**Current recommendation: Revise; internal surrogate 6/10; confidence 4/5.** This is an interim evidence addendum, not a review of a final PDF or a completed combined run. The largest remaining scientific limitation is the modest breadth of the metric-specific specialization and the reused score workload. **For the narrowed claim actually supported here, I classify that as a limitation compatible with the frozen project-6 “no unresolved major scope, novelty, baseline or validity objection” condition, not as a major objection that blocks my own part of that condition.** This classification does not certify the other two reviews, and a project gate is not a venue-acceptance rule.

### Completed auxiliary execution

The range-only run `40061935240`, source commit `d4eb3eddd0d441757ee31e149466528e41905c7d`, completed at `2026-10-24T04:31:15.408357+00:00` on a hosted Linux AMD EPYC 9V45 environment. Its receipt covers fresh raw-data download and score generation, the range main and public studies, validation and audits. It does not cover the combined VUS-plus-range command. The selection record names run `40062043152`, commit `e2405e39ec23486a3d228240569b48785de32cb4`, as canonical before either timing report was inspected; auxiliary success had already been observed when this choice was recorded. The canonical run was still executing at this cutoff. Neither the auxiliary run nor a more favorable timing replaces it.

I checked the completion receipt's report digests, main-study completion/protocol/raw-record bindings, unchanged kernel/producer pins, the complete 2,628-record method/order structure, recorded value/winner consistency, all 24 case/block timing summaries and all selection-detail rows. I independently reconstructed the paired bootstrap summaries from the saved raw timings; they agree to last-bit numerical precision. This check did not reload the auxiliary curve files or fresh score arrays. The archived local re-audit separately reports those checks; it is evidence supplied with the artifact, not a claim that I independently reran fresh experiments. Its derived-summary tolerance of relative/absolute `1e-12` was chosen after observing `exp`/`log` roundoff, and is explicitly not an experimental endpoint. Its maximum recorded relative summary discrepancy is below `1e-15`. That statement concerns reconstruction of the **same saved timing statistics**, not differences between independently generated host scores.

The reconstructed auxiliary principal comparisons are:

| Collection | All-observed raster/sweep, adjusted 95% interval | Grid100 raster/bucket, adjusted 95% interval |
|---|---|---|
| NAB | 30.921 [20.184, 47.726] | 2.121 [1.871, 2.402] |
| SMAP | 28.640 [12.100, 54.848] | 3.123 [2.748, 3.579] |
| SMD | 164.655 [124.795, 195.877] | 3.606 [3.399, 3.873] |

All-observed sweep wins on 72/73 case medians, with the same low-cardinality SMAP534 failure retained: its raster/sweep ratio is 0.7214. Grid bucket wins on 73/73. These are same-host ratios with uncertainty over the fixed panel; they are not pooled Mac/Linux intervals or estimates of arbitrary deployed workloads. The supplied curve audit reports a maximum cross-method discrepancy of `2.9976021664879227e-15` and zero winner-set disagreements at its declared tolerance. The unchanged-public-API study completes all 72 calls on this host, with no censored calls; maximum completed discrepancies remain `6.661338147750939e-16` for TSB grid and `5.6508299595137146e-8` for TimeSeAD classic. The original Mac study's two censored calls remain censored in that study. The validation report retains 1,168 public selected-cut checks, maximum discrepancy `4.614364446098307e-16`, and the three million-point stress cases, maximum discrepancy `2.2250185795861794e-12`.

### Cross-host differences and the cost of exhaustive queries

The supplied score-comparison report binds both input manifests and both main audit reports. All 73 observation/label identities match, but **none of the 73 complete eight-profile score matrices is byte-identical across hosts**; only 9/584 individual profile arrays are exactly equal. Differences are not uniformly small: for example, the reported largest LOF absolute score difference is approximately `3.61e9`. That value alone does not establish its cause or its effect on rank order.

The auxiliary aggregate selection counts match the Mac counts: 24 winner-set changes, 15 nonoverlapping choices and 12 regrets at least .01. These equal counts conceal different cases. SMD188 changes from no winner/nonoverlap change on Mac to both on Linux, with regret approximately .03187; SMD200 changes in the opposite direction, from regret approximately .12748 to zero. The maximum SMD regret becomes .07966. Thus this is replication of the qualitative consequence and aggregate counts on freshly generated inputs, not reproduction of every decision or score byte. No causal explanation of these host differences is established. Fixed-input numerical agreement is a separate claim.

I also independently reconstructed every row of the post-review query-fidelity comparison from the existing Mac raw timings. Exhaustive sweep costs **2.1898/2.1355/3.0127 times** the fastest grid100 bucket evaluator on NAB/SMAP/SMD, using the geometric mean of case-median ratios. The new manuscript correctly identifies this as a descriptive comparison between different query contracts, not a same-output speedup or a prespecified endpoint. The favorable same-contract complexity reduction does not make exhaustive fidelity free. This qualification makes the measured selection consequence more interpretable; .01 remains a metric-scale cutoff rather than a demonstrated application-utility threshold.

### Closest prior art and my remaining objection classification

The added Menotti citation is materially closer than citing only general-graph union-find. The original [Menotti, Najman and Araújo paper](https://www.researchgate.net/publication/228747458_1D_Component_tree_in_linear_time_and_space_and_its_application_to_gray-level_image_multithresholding), inspected through its author-uploaded full text, gives linear-time one-dimensional component-tree construction. Its presented integer-weight structure has `O(max(n,m))` space, and section 3.4 already maintains attributes such as component cardinality during construction. Neither one-dimensional connectivity nor generic attribute augmentation is new here. The source now explicitly disclaims a new component tree or faster tree construction. The defensible additional result remains the particular label-conditioned overlap and fragmentation rewards for Tatbul range precision/recall, with constant-time updates and exact queried states. I found no equivalent Tatbul all-threshold implementation in the previously inspected pinned software; this remains a bounded search judgment, not proof of priority. Sorting is an implementation choice for ordered queries, not an inherent connectivity lower bound.

The archival TimeSeAD citation now accompanies the pinned software citation. Its [official pinned README](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/README.md) identifies the 2023 TMLR paper. The relevant performance comparison is still the **classic**, alpha-zero, observed-strict-threshold code path, not every alternative metric proposed by TimeSeAD. The stronger conventional same-compiler raster control continues to carry the algorithmic comparison; public Python/PyTorch speed ratios alone do not establish its cause.

My explicit classification for the frozen condition is:

| Dimension | My current classification for the narrowed claim |
|---|---|
| Scope | **No major unresolved objection.** Repeated aggregates over stored scores and an existing PVLDB metric give a defensible data-management workload. General detector accuracy, every Tatbul customization and complete-application acceleration remain outside the demonstrated result. |
| Novelty | **No major unresolved objection, with modest significance.** Classical component trees and their attribute maintenance must receive credit. The metric-specific state/update reduction survives the inspected closest sources and is independently supported; no claim of a general component-tree advance is justified. |
| Baseline | **No major unresolved objection for this claim.** Pinned public all-threshold and grid APIs plus a conventional same-compiler raster control answer different comparison questions. The public study is small and length-selected, and no proof of the globally fastest possible C++ baseline exists. Those are limitations, not evidence that the tested comparison is invalid. |
| Validity | **No major unresolved scientific defect identified.** The proof, separate small oracle, full recorded curves, selected-cut public checks and second-host results support the stated numerical contract. Bitwise cross-host scores, a length-independent error certificate and unrestricted threshold optimization are not established. The canonical combined receipt remains a concrete verification condition. |

### Gates and project criteria at this cutoff

Gates **1, 2, 3 and 6 remain passed within the stated scope**. Gate **4 remains pending** for the canonical combined command despite the now-completed auxiliary range execution. Gate **5's count is coordinator-attested as three independent combined-paper reviews**; my own public-calibrated, venue-criteria review is complete, but I have intentionally not inspected the other reviews' contents. Under that attestation the process count is 5/6; independently inspected scientific evidence alone still accounts for four completed gates plus the new auxiliary support.

The scientific conditions underlying **project 5 remain supported**, with unconditional all-gate closure still awaiting gate 4. The original **project-6 batch branch still fails** at SMD 1.207 below 1.25. The **alternate-generalization branch remains supported**: this is a distinct native metric contract with substantive maintained statistics, a removed repeated-scan term, matched-compiler gains and a measured fidelity consequence. The new mechanism itself now also has completed evidence on a second CPU. The previously measured stored-score workflow threshold, the adverse 1.031x nine-metric consumer result and the memory/certificate/low-cardinality failures remain as previously assessed; none is silently replaced.

**My own remaining scope/novelty/baseline/validity reservation does not block the frozen no-major-objection condition for this narrowed paper.** Full project-6 closure still requires the canonical evidence and the coordinator's assessment of the other independent reviews. The referee recommendation remains my judgment about this review cutoff, not a forced mapping from project criteria. A final recommendation should be recorded after inspecting the actual final receipt and PDF rather than promised in advance.

Further work is scientifically justified to complete that bounded verification and present the established result. Repeating timings on the same panel is not currently justified by an unresolved uncertainty. A broader impact claim would require a separate consumer or independent workload with measured operator importance; it is not established by this auxiliary execution. Falsifiers remain concrete: a source/record mismatch, a counterexample within the stated metric contract, an equivalent earlier maintained-statistics implementation, a failure of the selected fresh command, or renewed claims that contradict the retained negative results would reopen the relevant condition.

Additional inspected SHA-256 identities (source snapshot, not a final PDF claim):

```text
paper/exact_metrics_pvldb20261024_body.tex
  5922c47d75aef83b129c75435dae4a81403e9878b1926b03cabc656ef5381343
paper/range_sweep_method.tex
  9bb42203627b35f1c33bef6e079734005260ac61b5c7bc63b979305126a5463d
paper/range_sweep_extension.tex
  5f2b695f703e0fc098fbea592cd681468aa700b646b3592bfcf208b53b92af80
paper/exact_metrics_pvldb20261024_references.bib
  b9f3ad7d5b95d1bf05cd920c3b2790b211c396cda4b7207be2ad7628906787f3
artifacts/pvldb-research-20261024/range-sweep/query-fidelity-tradeoff.json
  ca7ed868feb53ff34f55d1111f3883b64e3f0ef9d6e33094e48c95999f39b122
artifacts/pvldb-research-20261024/range-sweep/linux-reproduction-selection.json
  a413908c69079b2a98a6ec660e402966f2ee027f24d171a5259fa1eb96f8a77f
artifacts/pvldb-research-20261024/range-sweep/linux-range-only/github-artifact.json
  30db2ec06b979056027f72fede844cfa8d484432acbe06a00a038c24f0f218de
artifacts/pvldb-research-20261024/range-sweep/linux-range-only/range-reproduction-complete.json
  c8b7e298122062729a6d5ff047530636b313afedc327cbb08184388311c6cd25
artifacts/pvldb-research-20261024/range-sweep/linux-range-only/local-reaudit.json
  b2f9271d3f7a1ef590410a7e6ed35e37fb9dab2d89f16be4a0be36d258f16141
artifacts/pvldb-research-20261024/range-sweep/linux-range-only/main-study/protocol.json
  30aff0472dd10033fccf4e34004ed39a2ad021d6aa1fa85c90770fd3537d9dbc
artifacts/pvldb-research-20261024/range-sweep/linux-range-only/main-study/records.jsonl
  f92b9e49b709c8d837e00a1e5502a6968cb0e579fcdd1c70369f35dd1b953bf2
artifacts/pvldb-research-20261024/range-sweep/linux-range-only/main-study/independent-report.json
  149cca1decf0f236694c823ed513476ed3ad7c8869ccd146e6945f85cad5b000
artifacts/pvldb-research-20261024/range-sweep/linux-range-only/public-study-v2/independent-report.json
  9c22d7c2133b5e12a389bfdabd868d0cb2a62a791bbbd76f1149d80abb5a98f7
artifacts/pvldb-research-20261024/range-sweep/linux-range-only/validation/report.json
  eb8117ade7bb3221f963a3e08e68933065ff1951674633a4f6598c61bc262cf9
artifacts/pvldb-research-20261024/range-sweep/linux-range-only/score-comparison-v2.json
  cf51864af547e60f52a84785e51dbb60cadafec8c564c31ecd946688392d35dc
```

## Final addendum: canonical combined execution and final PDF, 24 October 2026

**All six evidence gates are now addressed for the narrowed combined paper: five are directly supported in this review, and gate 5's three-review count is coordinator-attested. Next: preserve this scientific snapshot for submission preparation; no further experiment is needed to resolve my stated revision conditions.** I remain blind to the other reviewers' contents, scores and aggregate decision. The preceding 54,279 bytes, SHA-256 `627dec40f4e468ec511873dcbfd20a346b85f3a7fb74944a600efed1cd33f61b`, are preserved unchanged, including my earlier Revise recommendations and their evidence cutoffs.

**Final recommendation: Accept. Internal surrogate score: 7/10. Confidence: 4/5.** This is a modest-strength acceptance recommendation for the specific exact-operator contribution, not a prediction of PVLDB's decision and not its confidential CMT numeric form. It is also separate from the project's 5/6 investment scale. **Largest weakness remains limited conceptual breadth and application reach:** the range result specializes classical component-tree/event machinery, and its selection consequences come from the reused eight-procedure workload. The paper does not establish a general metric framework, improved detector accuracy or substantial acceleration of the complete public nine-metric consumer.

I change my recommendation because the final paper now presents the defensible contribution clearly, credits the closer prior art, retains the unfavorable controls and application result, and completes the particular reproducibility condition I requested. The positive scientific reason to accept is the useful exact maintained-statistics reduction with matched-compiler evidence and a measured query-fidelity consequence. A completed audit alone would not supply that reason. The bounded contribution was already identified in the original review; its remaining verification and presentation conditions are now closed. The modest novelty and narrow workload prevent a stronger score.

### Final artifact and verification

The reviewed final PDF is **`6646c1f497273f2e4731d158761568c26b7cf04b3b06978813aa1962518e3a11`**. It has **13 total pages**, with substantive text and the start of references on page 12, within the current 12-page non-reference limit. I visually inspected final pages 1, 5, 10, 11 and 12 and checked the changed source. The main range table separates the original Apple study from the canonical combined Linux study; its numerical values match the corresponding reports. The final abstract says “numerically matching outputs,” and the method credits Menotti's component attributes as well as linear-time one-dimensional tree construction. The combined command, the source-generation caveat and the limits on complete-application impact are present and readable. I found no material presentation defect in those pages.

The canonical [GitHub execution](https://github.com/mandu5/sparse-vus/actions/runs/40062043152) has a supplied completed-success receipt for source commit `e2405e39ec23486a3d228240569b48785de32cb4`. The numerical completion receipt records `include_vus: true`, AMD EPYC 7763, and completion at `2026-10-24T05:07:05.682988+00:00`; the job completed at `05:07:13Z`. The supplied GitHub artifact digest and local manifest identify archive SHA-256 **`cf9e0531b3ab00bc9f3f6d28113d62497f1ebe1c66b5eae2fe0fae915c898ec7`**. This is the prospectively selected combined run, not the more favorable auxiliary EPYC 9V45 run.

I independently verified all **568** extracted manifest entries by file length and SHA-256, including all **73 generated score NPZ files** and **438 canonical range-curve NPZ files**. I then reran all four record auditors in a temporary verification workspace bound to the archived data, the pinned raw-data ZIP and the unchanged source identities. The VUS primary v3 audit, VUS supplement audit, range main audit and range public audit each produced **byte-identical JSON reports**, not merely equal rounded table values. I separately checked the validation receipt's source/protocol/parent bindings and selected-cut arithmetic. These are my own record reconstructions, distinct from the separately evidenced fresh Linux execution; no new timing or detector-generation experiment was run by me.

The completed command covers VUS primary/supplement and range main/public/validation. It regenerates the numerical tables as JSON; TeX rendering remains a separate step. The operating-range, resource, conventional-support-control and complete public-consumer studies retain their separate protocols and commands. The operating-range wrapper has not received a second complete fresh execution. That accurately stated supplementary boundary does not leave the principal-table one-command requirement open.

### What the canonical results establish

The canonical range raster/sweep geometric ratios are **29.348 [18.809, 46.079]**, **27.764 [11.632, 53.745]** and **163.597 [125.923, 193.025]** on NAB, SMAP and SMD. Grid raster/bucket ratios are **1.900 [1.616, 2.239]**, **2.898 [2.624, 3.260]** and **3.574 [3.412, 3.789]**. These are the report's collection-adjusted 95% intervals, reconstructed by the auditor, with no host pooling. The exhaustive sweep again wins on 72/73 cases; SMAP534 remains a loss, ratio **0.66066**. Bucket wins on all 73 grid cases. Equal-label-block SMD raster/sweep is **146.450 [67.704, 208.301]** over nine blocks, a dependence sensitivity rather than proof of independent physical sources.

The canonical complete-curve discrepancy is approximately `3.00e-15`, with no cross-method winner-set disagreement under the stated policy. The public study again retains **two censored TimeSeAD SMD187 calls**, unlike the auxiliary run; no completed-call parity is imputed for them. Completed public scalar errors remain at most `6.661338147750939e-16` for TSB grid and `5.6508299595137146e-8` for TimeSeAD classic. The selected-cut validation maximum is `4.614364446098307e-16`; the million-point stress maximum is `2.2250185795861794e-12`. These numerical checks remain empirical evidence within the explicit contract, not a proof of bitwise identity or an error bound for arbitrary length.

The regenerated VUS primary and supplement also pass their full v3 source/input/record reconstructions. Their maximum PR discrepancy is `8.881784197001252e-16`; supplementary complete-workflow ROC discrepancy is at most `4.884981308350689e-15`. For context, canonical stored-score collection workflows are **20.116/20.423/15.727 times** faster than Klein exact on NAB/SMAP/SMD. These corroborate the stored-score workload benefit; they do not replace the original project's frozen outcomes or the adverse nine-metric application result.

I independently loaded and compared both hosts' actual observation, label and score arrays. All 73 observation/label pairs match. No full eight-profile score matrix matches bitwise, while **83/584 individual profile arrays do match** in this canonical comparison, including all 73 HBOS profiles. This differs from the auxiliary comparison's 9/584 and must not be conflated with it. Canonical raw-score differences are not uniformly small: the largest LOF absolute difference is about `5.34e10`; that does not by itself identify a cause or quantify ranking impact. The manuscript's statement is appropriately qualitative.

I also verified the cross-host selection-summary bindings. Counts remain 24 changed winner sets, 15 nonoverlapping choices and 12 regrets at least .01, but SMD188 and SMD200 exchange change/nonoverlap status. Maximum SMD regret is .07966 rather than the original .12748. The final paper reports this. It therefore supports a qualitative fidelity consequence on regenerated inputs, not byte-identical detector generation or replication of every selected model. It is not an isolated CPU intervention.

### Remaining limits, not newly erased conditions

The final positive assessment retains the earlier adverse evidence:

- The original SMD sharing result **1.207** remains below the frozen 1.25 branch threshold. A new host's larger ratio does not rescue that branch. The compiled conventional-support control beats the released scalar evaluator on all 73 primary cases; residual sharing gains over that control remain modest.
- The only measured complete nine-metric consumer improvement remains **1.031x**, with the accelerated VUS stage only about 2.7% of its original runtime. There is no measured new whole-consumer speedup from the range addition.
- Exhaustive queries still cost **2.19/2.14/3.01 times** the fastest measured grid bucket evaluation on the original panel; the low-cardinality loss and public-call censoring remain. The .01 regret cutoff has metric-scale meaning, not established application utility.
- The panel is reused, short-to-moderate, univariate and dependent; the eight procedures are evaluator inputs, not independently validated tuned detector pipelines. New scores do not turn old recordings into held-out data. The separate long/controlled evidence does not establish broad real-domain generality.
- Higher memory, unsuccessful certification, unfavorable prefix/dense-support regimes and preparation costs remain relevant. The method covers the specified dynamic VUS and flat reciprocal-cardinality range contracts, not arbitrary weighting/cardinality variants, all empty-mask conventions or every component-merging rule. Strict observed-score maxima omit the below-minimum all-active state unless explicitly requested. Numerical matching does not imply unrestricted real-arithmetic or cross-host byte equality.

These limits constrain the claim enough that I do not regard them as unresolved major scope, novelty, baseline or validity defects in the final paper. A stronger claim would change that judgment. In particular, known connectivity and generic attribute maintenance cannot be repackaged as a newly invented data structure, nor can public-library speedups alone isolate algorithmic gain.

### Final six-gate and project-5/6 assessment

The frozen thresholds in `docs/superpowers/specs/2026-10-24-pvldb-evidence-design.md` are unchanged.

| Gate | Final status | Basis and boundary |
|---|---|---|
| 1. Recent primary comparison and surviving distinction | **Pass, bounded** | More than ten related 2024–2026 primary comparisons plus older indispensable Tatbul/component-tree sources; the surviving contribution is the metric-specific exact state/update representation. Bounded source search is not proof of global priority. |
| 2. Eligible public baselines, three collections, uncertainty and ablation | **Pass for the stated claim** | Same-contract VUS public comparisons, explicit range public contracts, and the all-73 conventional same-compiler range control with positive adjusted intervals on three collections. The author control is not mislabeled public SOTA. |
| 3. Real, full-precision, eight-family scope with failures | **Pass within its declared workload** | Complete real inputs and actual detector scores, with source reuse/dependence, low-cardinality loss, negative conventional control, censoring and application limits retained. |
| 4. One-command principal-table reproduction | **Pass; former condition closed** | The selected fresh combined command completed; all generated arrays/curves are retained, five report bindings check, and my own rerun of four record auditors yields byte-identical reports. Fresh execution and record reconstruction remain distinct. |
| 5. Three calibrated independent venue-criteria reviews | **Pass on coordinator-attested process count** | The coordinator reports three combined-paper reviews. This review's criteria, public accepted/rejected calibration, score/confidence and weaknesses are directly inspectable. I have not inspected or inferred the other reviewers' ratings or objections. |
| 6. Target, track, scope and deadline | **Pass** | PVLDB Volume 20 Regular Research, Foundations and Algorithms; abstract 25 November 2026 and paper 1 December 2026, both 17:00 America/Los_Angeles. The specific data-management contribution and content limit are addressed. No submission or external acceptance is claimed. |

**Project 5: supported.** With the now-completed principal reproduction and the attested review count, the six evidence gates are addressed. The identifiable contribution, real full-precision three-collection comparisons, paired lower bounds above one and stored-score workflow benefit satisfy the fixed scientific/measurement conditions in my assessment. I find no unresolved mathematical or measurement-invalidity defect.

**Project 6: supported through the alternate-generalization branch in my independent assessment; the original numerical batch branch remains failed.** The range mechanism is absent from the released VUS implementation, uses a different native target and non-support-only event state, removes repeated threshold scans, and has strong matched-compiler evidence plus a measured fidelity consequence. It is comparably substantive as a specialized operator generalization. The stored-score workflow threshold and two-CPU condition are supported, adverse tails and memory costs remain visible, and **I have no unresolved major scope, novelty, baseline or validity objection to the narrowed final claim**. I cannot certify the other two reviewers' lack of major objections while remaining blind to them. Therefore aggregate project-6 closure across all three reviews remains the coordinator's responsibility, not a conclusion about their contents made by this reviewer.

The venue recommendation is nevertheless my own **Accept, surrogate 7/10**, without relying on the other reviews or equating gate completion with acceptance. The prior public-review calibration remains the same adjacent-venue calibration described above; I did not introduce a score target or treat passing checks as research merit.

All bounded revision requests from my combined-paper review are now closed. No further timing on this panel is required to support this recommendation. Scientifically justified future work would address a new uncertainty: a separate score-producing pipeline or consumer where the exact range operator has measured importance, or a genuinely broader metric family. Such work is required for those stronger claims, not retrospectively imposed as a new condition on the current narrow paper. A counterexample within the stated contract, a material source/record mismatch, an equivalent earlier all-threshold maintained-statistics algorithm, or an invalid same-contract comparison would reopen the corresponding major condition. None was found in this review.

Final inspected SHA-256 identities:

```text
paper/exact_metrics_pvldb20261024.pdf
  6646c1f497273f2e4731d158761568c26b7cf04b3b06978813aa1962518e3a11
paper/exact_metrics_pvldb20261024_body.tex
  f88d8618fc772bba3047658281adc0bf5890e6aa9dd81994bab10b38f7bca005
paper/range_sweep_method.tex
  eba5a76cd8cf89183bdde8559a321bc0464cef3c4beccce58a436e5658860092
paper/range_sweep_extension.tex
  125372417c7940ebd8ae298d14d943d152a02552431870ff666015bcadcbe1e7
paper/exact_metrics_pvldb20261024_references.bib
  b9f3ad7d5b95d1bf05cd920c3b2790b211c396cda4b7207be2ad7628906787f3

artifacts/pvldb-research-20261024/range-sweep/linux-combined/github-run.json
  753365ec600fc0e497bc1cfcb7a4fe7b94db9bd49befff18437e69d0e48e7121
artifacts/pvldb-research-20261024/range-sweep/linux-combined/github-artifact.json
  ed3ae7f24841f8fb31b2d8e3c02ed5bd3bc57617e51ac57dfe39b4b2fa0b013e
artifacts/pvldb-research-20261024/range-sweep/linux-combined/manifest.json
  9e5babcc17b75f2dcb9879625966b16f17e734ea0a18b95b87f6e9160588c0d5
artifacts/pvldb-research-20261024/range-sweep/linux-combined/local-reaudit.json
  55e3d7f7439bf133982b7106c2c881144b077460ed9c2e2dd3b151a0c549232d
artifacts/pvldb-research-20261024/range-sweep/linux-combined/score-comparison.json
  691f6d8e07a5e6a81bbc3e6a144186d75bc199e73dcb79f62766bcc7b7b0ea2d
```

The following paths are relative to `artifacts/pvldb-research-20261024/range-sweep/linux-combined/replica/artifacts/pvldb-research-20261024/`:

```text
range-reproduction-complete.json
  0457f8271d18d060f1bd3143ae957ff9ea76e599e965384ef8aab0f3d3ea0553
full-precision/inputs.json
  67bd9404520342d0d97d00cb55beca284ef50a522f395e18c48cbd3d4e65330e
full-precision/independent-audit.json
  9fe355ecfcb8a27f13cad90d8d6da7ad1ae1acadc66c4a9df5bf8363687ba6b0
supplement/independent-report.json
  9e17112f09676514e689079203ae2534bf0dcac6a8267e7cbf3f42b1271bcee8
range-sweep/main-study/protocol.json
  0dca6c76363d3a1f682260f6a1f12478f8c8d5dac3f790b2ae0462f49b8cdf00
range-sweep/main-study/records.jsonl
  0c6caff5d9f761cad48ce8c6a448f630b3b7ffd82f3644bd609eca028c085565
range-sweep/main-study/independent-report.json
  b934652c89b067af465bf40b301d3e555e69f74d289a4fc5ac7796cc65471ae8
range-sweep/public-study-v2/protocol.json
  06e377fd5229406a055854a3e8720cb13d4e2e5e88b2e7a1b5d96706b41c0afc
range-sweep/public-study-v2/records.jsonl
  f29883a314c08019c65e38d6f30606e28a1db32b8f1287209c908e6481b6b2c7
range-sweep/public-study-v2/independent-report.json
  82e234cd72a60c71b0a90fb1a333ecc9ff90e3794a10917661c4a8449a6329f8
range-sweep/validation/protocol.json
  e381b0af0e14638eeafa2711b49e8c9b881464fac7bfe0e998003e1ab192dff9
range-sweep/validation/report.json
  f74dd276d66847c60f63a07a57688324536215b53bf0e992caba5dde82fba4a4
```
