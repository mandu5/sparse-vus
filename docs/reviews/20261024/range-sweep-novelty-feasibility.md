# Independent feasibility and prior-art review: exact range-metric threshold sweep

**24 October 2026 — Feasibility is supported; novelty remains unresolved. Next: compare the endpoint sweep with unchanged TimeSeAD classic and a compiled linear-per-threshold raster control, using identical threshold and metric contracts.** No publication score or recommendation is assigned to this new candidate. The previous `blind-final-review.md`, including its original assessment and addendum, is unchanged.

This is an independent assessment of the proposed computation, not a review of prototype performance. I did not inspect other internal reviews, reviewer scores, or agent listings. I did not implement the candidate or run timing. I inspected primary papers and pinned public source, and ran six small semantic checks against the unchanged TimeSeAD scalar operator. CodeGraph was unavailable. Firecrawl retrieval could not run because the connected account was out of credits; web search, author/proceedings pages, GitHub APIs, and raw pinned source were used instead.

## Finding and novelty boundary

I did **not find an equivalent implementation of the complete Tatbul flat-bias, reciprocal-cardinality threshold sweep** in the specific public paths inspected below. This is a bounded search result, not evidence that no equivalent exists. The clearest immediately eligible all-distinct-threshold public comparator is **TimeSeAD's `Evaluator.best_ts_f1_score_classic` / `best_ts_fbeta_score_classic`**, with alpha zero. It already searches every observed score using strict `>`, caches the true intervals, and uses a substantially better scalar overlap implementation than prts. No timings were run here, so I cannot honestly certify it as the fastest available implementation.

The proposed descending-activation/union-find skeleton is **established prior art**. Najman and Couprie's component-tree algorithm processes level sets of a vertex-weighted graph with union-find; its graph-processing bound is quasi-linear, with ordering assumptions accounted for separately. It applies to more general graphs than a one-dimensional path. Their [author-hosted paper, beginning on PDF page 4](https://perso.esiee.fr/~najmanl/habilitation/publications.pdf) and [published DOI](https://doi.org/10.1109/TIP.2006.877518) are direct prior art. Current [scikit-image `max_tree` documentation](https://scikit-image.org/docs/stable/api/skimage.morphology.html#skimage.morphology.max_tree) also exposes this established family and cites later component-tree algorithms. It is not an equivalent Tatbul evaluator, but prevents a claim that the threshold-connectivity mechanism itself is new.

Moreover, on a path the candidate does not need union-find. Immediately before activating position `x`, an active neighbor `x-1` is the right endpoint of its component, and an active neighbor `x+1` is the left endpoint of its component. Arrays storing the opposite endpoint at each live endpoint support extension and merging in constant time. This gives **O(n log n + n + H) time and O(n + H) space**, including comparison sorting and materialized results at H distinct thresholds. A union-find implementation has no asymptotic advantage here. I sent this observation before learning that the implementer had adopted endpoint arrays.

The candidate difference that remains worth testing is narrower: **maintain the exact macro-averaged range rewards, including fragmentation penalties, with local sufficient statistics throughout a tie-complete threshold sweep, instead of recomputing them for each threshold**. Whether that specialization is sufficiently non-obvious or useful for an archival contribution is still open. A speedup over slow Python alone would not answer it.

## Exact contract and a feasibility derivation

The relevant mathematical starting point is [Tatbul et al., NeurIPS 2018, Sections 4.1–4.3](https://people.csail.mit.edu/tatbul/publications/NeurIPS18.pdf). Its customizable model is broader than the proposed specialization. Fix binary labels on a path, maximal contiguous true ranges `R_i`, prediction components `C`, flat positional bias, reciprocal overlap cardinality, precision existence weight zero, and a stated recall existence weight `a`. Let `A` be the currently active prediction mask.

The following is my derivation of the proposed specialization, not an algorithm attributed to the paper:

- For a true interval, maintain `m_i = |R_i ∩ A|` and `q_i`, the number of active runs intersecting it. Its recall contribution is zero if `q_i=0`; otherwise it is `a + (1-a)m_i/(|R_i| q_i)`. Maintain the sum of these contributions and divide by the fixed number of true intervals.
- For an active component `[l,r]`, let `m(l,r)` be the number of true points it contains and `c(l,r)` the number of distinct true intervals it intersects. Its precision contribution is zero when `c=0`, and otherwise `m/((r-l+1)c)`. Both statistics are obtained in constant time from fixed label prefix arrays. In particular, `c` equals the number of true-interval starts in `[l,r]`, plus one if `l` lies strictly inside a true interval.
- A new activation removes the contributions of at most two old components and adds one new contribution; the component-count denominator changes correspondingly. No list of all intersected truth intervals needs to be merged.
- If `x` is a true point in `R_i`, update only `m_i` and `q_i`. Its run-count change is `1 - I[left neighbor active and in R_i] - I[right neighbor active and in R_i]`. An activation outside every true interval cannot change a true interval's intersection-run count. This follows from contiguity on a path; it would not hold automatically for general graph regions.
- For strict `score > t` with `t` an observed value, emit the state **before** activating the complete group equal to `t`. Intermediate states inside a tie group are not legal thresholds. F1 is then computed from the current aggregate precision and recall.

These identities make the claimed complexity plausible and explain what must be proved and tested. They do not establish a broad lower bound, optimality for every input model, stability of repeated floating-point updates, or correctness of an implementation I have not reviewed. An arbitrary black-box positional-bias function is outside this argument. Sorting is a separate cost; a comparison-sort bound should not silently become a linear bound without an explicit integer/radix model.

There are important semantic traps:

1. **Observed thresholds and all achievable masks differ.** Strict `>` at all observed scores includes the empty prediction but omits the all-positive state below the minimum score. A constant-score, all-positive-label input consequently has best observed-threshold F1 zero in TimeSeAD, although the omitted all-positive mask has F1 one. Adding an endpoint changes that API contract.
2. **Recall is not monotone in the threshold.** In an unchanged TimeSeAD scalar check, labels `[0,1,1,1,1,0]` and predictions `[0,1,1,0,0,0]` give recall `0.5`; adding the isolated true positive at index 4 gives `0.375` because the cardinality changes from one to two. Thus a standard monotone PR integration routine cannot be assumed valid. A maximum-F1 result avoids choosing an AUC convention, but must still preserve tie-breaking and endpoints.
3. **The all-positive precision is not generally class prevalence.** With labels `[0,1,0,1,0]` and all-positive prediction, reciprocal-cardinality precision is `0.2`, not `0.4`. TimeEval's curve prepends prevalence as its first precision, so its entire AUC wrapper is not simply the mathematical Tatbul curve.
4. **Empty cases vary by implementation.** TimeSeAD returns `(1,1)` when both masks have no positives and `(0,0)` when only one does. Its best-F helper changes a `(0,0)` pair's stored recall to one to avoid division by zero; F remains zero. prts's preparation rejects all-zero masks. aeon's public binary functions return zero for constant predictions, including all-positive predictions. The shared contract needs explicit handling rather than a claim to match every package simultaneously.
5. **Metric parameters and precision matter.** TimeSeAD classic uses `a=0`; TSB-AD RF1 uses `a=0.2`; TimeEval's curve defaults to `a=0.5`. TimeSeAD's best-F arrays use `torch.float` (32-bit), while its scalar arithmetic includes Python floats. A float64 implementation may be mathematically equivalent without identical rounded maxima or ties. Exact threshold coverage is distinct from bitwise exact arithmetic.

The six scalar checks and the source-distribution comparison are recorded with this memo's source-audit manifest. They are semantic checks, not performance or novelty evidence.

## Public implementations inspected

Here `G` is the number of true intervals, `K_t` the prediction interval count at threshold `t`, and `H` the number of tested thresholds. Complexity descriptions are my source-based analyses, not published timing claims. Git revisions are frozen as retrieved on the date above.

| Implementation and revision | Inspected computation and semantics | Baseline implication |
|---|---|---|
| [TimeSeAD](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/evaluator.py), `bb8efa9ce17f9cfb0bab77df08c32d986de8429e` (2025-06-10) | `__best_ts_fbeta_score`, lines 237–318, enumerates unique scores with strict `>`. The [scalar operator](https://github.com/wagner-d/TimeSeAD/blob/bb8efa9ce17f9cfb0bab77df08c32d986de8429e/timesead/evaluation/ts_precision_recall.py) uses moving interval pointers and flat-bias slice sums, with true intervals cached by the outer loop. Flat unweighted scalar work is O(n); all thresholds cost O(n log n + Hn). No incremental connectivity state. Classic uses reciprocal cardinality; the non-classic path uses a different cardinality function and weighted precision. | Primary unchanged public all-threshold **best-F** baseline at `a=0`, beta one. Its AUPRC path uses `>=` and the improved cardinality function; do not substitute that different metric. |
| [CompML/prts](https://github.com/CompML/PRTS/blob/66db2ac5f83ac9182ce29dcd7afc0f678a678eed/prts/base/time_series_metrics.py), `66db2ac5f83ac9182ce29dcd7afc0f678a678eed` (2021-03-17); PyPI `1.0.0.3` | Binary scalar operator; nested prediction/true-range pairs and position loops for each overlapping pair. General per-threshold cost can be O(n²), plus array preparation. Flat bias is not specialized into interval lengths. Package default cardinality is `one`; set `reciprocal` explicitly. Four key files were byte-identical between the current PyPI sdist and this Git revision. | Useful correctness/provenance reference, inadequate as the only strong efficiency baseline. The `TimeSeriesPrecisionRecall` class itself contains a TODO; use the implemented precision/recall/F-score entry points. |
| [aeon range metrics](https://github.com/aeon-toolkit/aeon/blob/ac9abc36b1bd53aa98dc5c89062561cc7638f40b/aeon/benchmarking/metrics/anomaly_detection/_range_metrics.py) and [continuous metrics](https://github.com/aeon-toolkit/aeon/blob/ac9abc36b1bd53aa98dc5c89062561cc7638f40b/aeon/benchmarking/metrics/anomaly_detection/_continuous.py), `ac9abc36b1bd53aa98dc5c89062561cc7638f40b` (2026-10-23) | Binary-to-range conversion, nested interval overlap tests, Python overlap sets, and per-interval position loops. Scalar flat-bias work is O(n + G K_t) under normal set-operation assumptions. `rp_rr_auc_score` samples thresholds by default, repeats scalar calls, uses `>=`, and sorts computed points by recall. No reuse of dynamic components. | Current public library comparison, with explicit flags and endpoint semantics. `range_pr_auc_score` is a different, VUS-family range-AUC metric; it is not this Tatbul curve. |
| [TimeEval](https://github.com/TimeEval/TimeEval/blob/7c3622757b1a3afa9a84cbc97ce132d9e379f715/timeeval/metrics/range_metrics.py), `7c3622757b1a3afa9a84cbc97ce132d9e379f715` (2026-08-17) | `RangePrecisionRangeRecallAUC` calls prts repeatedly; `max_samples=50` by default, `r_alpha=0.5`, reciprocal/flat. Uses `>=`; skips the minimum observed threshold and prepends `(prevalence,1)`. It lexicographically sorts PR points by recall and precision before returning them. | Familiar external consumer, but default sampled AUC is not an all-threshold best-F baseline. Increasing its sample cap does not erase its endpoint/integration conventions. |
| [TSAD-Evaluator preserved C++ copy](https://github.com/locussam/TSAD-Evaluator/blob/3d88d30cb436c5c3270580f030fb091a542327f3/src/evaluator.cpp), `3d88d30cb436c5c3270580f030fb091a542327f3` (2018-11-30) | `compute_precision`/`compute_recall` loop over interval pairs and call an omega routine that scans positions. Input is already-binary label files, not scores; no all-threshold incremental operator. README defaults cardinality to `one`, although reciprocal is supported. | Native compiled public scalar comparator worth screening. Do not time a fresh process and file I/O per threshold against an in-process candidate. The original `IntelLabs/TSAD-Evaluator` URL returned 404. GitHub marks this surviving copy `fork=false`; its README identifies the paper, but I did not establish byte identity to the lost original repository. |
| [TSB-AD](https://github.com/TheDatumOrg/TSB-AD/blob/303dffbfc11612995b17b06633f8c9d0ea0e38e5/TSB_AD/evaluation/basic_metrics.py), `303dffbfc11612995b17b06633f8c9d0ea0e38e5` (2026-10-20) | `metric_RF1` evaluates 100 uniformly spaced score-value thresholds with strict `>`, recall alpha `0.2`, precision alpha zero, reciprocal cardinality, and flat bias. It rebuilds ranges and calls `w`, whose `i in p` searches a NumPy index array. The work can be quadratic per threshold. | Direct unchanged consumer component for grid100 semantics. Candidate results over every distinct score solve a different optimization problem and should be reported separately. `get_metrics` has eight other outputs: accelerating RF1 alone is not evidence of a whole-nine-metric speedup. |

Additional source searches did not reveal an equivalent in the following inspected paths:

| Source and revision | What was actually inspected / result |
|---|---|
| [Sørbø–Ruocco evaluation code](https://github.com/sondsorb/TSAD_eval/blob/e34a70968b8eb46940f92b54800e861b079ee646/metrics.py), `e34a70968b8eb46940f92b54800e861b079ee646` | `metrics.py`, `threshold_plt.py`, vendored prts base. Range precision/recall delegates to prts; no incremental sweep in these paths. |
| [PATE](https://github.com/Raminghorbanii/PATE/blob/2d358ce1b065674fcdadda115a08bbe6376273d0/pate/PATE_metric.py), `2d358ce1b065674fcdadda115a08bbe6376273d0` | Continuous PATE uses a distinct proximity-weighted metric, thresholds from `_binary_clf_curve` with optional reduction, and independent per-threshold jobs. The supplied Tatbul comparison imports prts. This is not the candidate, even when all threshold samples are enabled. |
| [DQE](https://github.com/Yueweilirepo/DQE/blob/055c23eb6e061284021b7c37ecd6615c85d61837/dqe/dqe_metric.py), `055c23eb6e061284021b7c37ecd6615c85d61837` | The current implementation rebuilds binary predictions for a score-value grid (`thresh_num=100` default). Its `metrics/Range_Based_PR.py` uses prts with `cardinality="one"`, alpha `0.2` on both precision and recall. A claim about the full threshold spectrum is not an implementation of the proposed distinct-score reciprocal-cardinality sweep. |
| [ALARM / tsadm](https://github.com/wagner-d/tsadm/blob/05491ba0e7180d1c1b902857ea102ee18fbb2008/src/tsadm/alarm.py), `05491ba0e7180d1c1b902857ea102ee18fbb2008` | `alarm.py` and `utils.py` implement a different fixed-binary metric. No all-threshold Tatbul path found. |
| [EasyTSAD](https://github.com/dawnvince/EasyTSAD/blob/a13519014c0334a26b0e74480881db503e6a8e0b/EasyTSAD/Evaluations/Protocols/EventF1PA.py), `a13519014c0334a26b0e74480881db503e6a8e0b` | EventF1PA, PointF1, and evaluation utilities inspected. Event/point adjustment is different semantics, not the candidate. |
| [Clinical time-series metrics](https://github.com/dihi/clinical-ts-metrics/blob/2b776e11a296ec1762455151b0927612d2a3d673/src/process_trajectories.nim), `2b776e11a296ec1762455151b0927612d2a3d673` | Nim evaluates episode/prediction metrics with snoozing, rescanning trajectories in a threshold loop. Compiled and relevant to evaluator engineering, but neither Tatbul semantics nor an incremental threshold sweep. |
| [TSADmetrics](https://github.com/Higashiguchi-Shingo/TSADmetrics/blob/a24276e5fc65bd3d7e0c9565932cc9b21412886a/src/TSADmetrics/metrics.py), `a24276e5fc65bd3d7e0c9565932cc9b21412886a` | Point-adjustment and VUS-family routines in the retrieved file use repeated thresholds. No exact candidate found. |

I also retrieved KurochkinAlexey/TSPrecisionRecall at `9140bd3785796c513d2d93bab21f618ec6d9792c`; its code is in a notebook. It was not fully audited, so it is a remaining coverage limitation, not a negative equivalence finding.

## Recent literature screen

The following 2024–2026 works are useful comparisons, with different levels of inspection stated. They are not ten equivalent algorithmic competitors, and counting them cannot establish novelty. The older Tatbul and component-tree papers and TimeSeAD source are closer to the exact proposed computation than several recent evaluation studies.

| Primary source | Relevance and difference from this candidate |
|---|---|
| [Sørbø and Ruocco, *Navigating the metric maze*, DMKD 2024](https://link.springer.com/article/10.1007/s10618-023-00988-8) | Metric taxonomy and empirical properties; paper and relevant public code inspected. Its Tatbul path delegates to prts. A fast evaluator preserves the chosen metric's preferences and limitations. |
| [*The Elephant in the Room / TSB-AD*, NeurIPS 2024](https://proceedings.nips.cc/paper_files/paper/2024/hash/c3f3c690b7a99fba16d0efd35cb83b2c-Abstract-Datasets_and_Benchmarks_Track.html) | Benchmark/metric reliability study and the actual multi-metric consumer; pinned RF1 implementation inspected. This is direct usage evidence, not a new evaluator algorithm equivalent. |
| [Ghorbani et al., *PATE*, KDD 2024](https://arxiv.org/abs/2405.12096) | Proximity-weighted interval evaluation; primary paper and official metric code checked. Different metric, with repeated per-threshold computation in the inspected code. |
| [Liu et al., *MTAD*, 2024 preprint](https://arxiv.org/html/2401.06175) | Evaluates accuracy, salience, delay and efficiency across methods. Paper screened, code not audited here. Detector efficiency or threshold choice should not be confused with metric-computation complexity. |
| [Si et al., *TimeSeriesBench*, 2024 version](https://arxiv.org/html/2402.10802) | Industrial evaluation and deployment-oriented metrics; paper screened. Helps assess operational relevance, but does not by itself validate maximizing test-label F1 as a deployment threshold policy. |
| [Boniol et al., *VUS: Effective and Efficient Accuracy Measures*, 2025](https://arxiv.org/html/2502.13318) | Explicit faster metric computation through static/dynamic regions and memory variants; algorithm section inspected. This is important efficiency prior art, but its soft labels, tolerance widths and metric denominators differ from Tatbul range PR/F1. |
| [Wagner et al., *Formally Exploring Time-Series Anomaly Detection Evaluation Metrics*, AISTATS 2026](https://proceedings.mlr.press/v300/wagner26a.html) | Analyses properties of 37 metrics and introduces LARM/ALARM; full-text relevant sections and official code inspected. Its formal analysis explicitly excludes score-direct metrics. Faster computation does not repair the documented semantic limitations of Tatbul variants. |
| [Li et al., *DQE*, March 2026 preprint](https://arxiv.org/html/2603.06131) | Critiques threshold-interval dependence and proposes a new semantic metric. Full relevant text and current official code inspected. Its inspected threshold grid and non-reciprocal Tatbul comparator are not this candidate. |
| [Yang et al., *A Problem-Oriented Taxonomy*, 2025 preprint / 2026 journal listing](https://arxiv.org/html/2511.18739) | Operational metric selection and random-score inflation; relevant text screened. The [journal page](https://doi.org/10.1016/j.neucom.2026.134547) lists a 7 November 2026 issue date, later than this memo; the prior preprint is available. No claim of a new threshold-sweep implementation was established here. |
| [Xu and Boström, *Addressing Methodological Challenges*, 13 October 2026](https://link.springer.com/article/10.1007/s10994-026-07183-y) | Methodology review highlighting leakage, datasets and baselines; relevant article sections screened, repository not audited. Supports demanding a strong simple control and separating oracle best-F1 from deployable threshold selection. |
| [Zhou et al., *mTSBench*, TMLR 2026](https://arxiv.org/abs/2506.21550) | Benchmark/model-selection scope verified through author and paper pages; only metadata/abstract and repository landing page screened. A possible broader consumer context, not an independently verified use of the candidate metric or an audited negative equivalence result. |

Representative exact search strings included `"range-based" "precision" "union-find"`, `"range precision" "threshold" "incremental"`, `"Tatbul" "incremental"`, `"Tatbul" "union"`, `"range-based precision" "sweep"`, `"time series" "precision" "disjoint set"`, `"Time Series" "F1" "union-find"`, `"range_f_score" "numba"`, `"ts_precision" "numba"`, `"range-based precision" "complexity"`, and `"precision recall" "max-tree"`, plus named-paper and repository searches. Many returned unrelated work. Search-index omissions, inaccessible original repositories, unaudited branches/forks, unpublished work, and terminology differences remain material limits. I did not perform an exhaustive global GitHub code search or inspect every metric in every retrieved repository.

## Strong baseline and decision requirements

For the current prototype, I recommend the following comparisons without asserting a future favorable outcome:

1. **Primary public best-F baseline:** unchanged pinned TimeSeAD classic, alpha zero, reciprocal/flat, beta one, strict observed-score thresholds, explicit float32 output tolerance, and the same device/thread settings. Compare the maximum and chosen operating point as well as scalar PR on selected thresholds; distinct maxima may tie after float32 rounding.
2. **Strong algorithmic control:** an author-compiled raster/two-pointer evaluator that caches fixed truth metadata and does O(n) work per threshold under the same numerical contract. Label it as an author control, not an external SOTA implementation. This separates elimination of repeated scans from Python/interpreter effects. Include sorting and preprocessing in the main comparison and expose amortized variants separately.
3. **Native public screening:** the preserved C++ scalar implementation is worth considering, especially for low H and short inputs, but avoid unfair repeated subprocess/I/O overhead. A wrapper that changes it needs a precise disclosure. The source search alone cannot rank its runtime against TimeSeAD.
4. **Actual consumer comparison:** unchanged TSB-AD RF1 on its own grid100 queries, separately from exact best-F over all distinct values. Keep alpha `0.2`, strict `>`, and public edge behavior explicit. Full consumer impact requires measurement of the unchanged remaining outputs; this memo claims none.

Use recordings, tie rates, interval counts and score profiles selected independently of timing outcomes. Include small H, dense and fragmented true ranges, very long single ranges, repeated scores, constant scores, and cases where a new true point decreases recall. For few requested thresholds, a direct O(Hn) vectorized/compiled scan may win because the sweep pays sorting and O(n) state costs. The sweep also uses more state than a streaming single-threshold scalar evaluator. Report those failures rather than treating an all-distinct workload as universal.

**Scientific feasibility conclusion:** a bounded prototype and controlled evaluation are justified because the exact statistic-maintenance identities remove a real repeated-computation term in inspected public implementations. **Novelty conclusion:** unresolved, and likely concentrated in a small specialization of established threshold-connectivity machinery. A stronger general result could characterize which interval metrics admit constant-time local updates and which do not, but that is a new theorem to establish, not something demonstrated by this memo. No novelty, acceptance, SOTA, or end-to-end application-benefit promise follows from the present search.

## Source identities and reproducibility

The durable [retrieval manifest](../../../artifacts/pvldb-research-20261024/range-sweep-novelty/retrieval-manifest.json) records exact raw URLs, Git revisions, local SHA-256 values, license paths/hashes where a root license exists, failed paths, the six scalar checks, and prts PyPI/Git agreement. The relative link is resolved from this review directory; the canonical repository path is `artifacts/pvldb-research-20261024/range-sweep-novelty/retrieval-manifest.json`. Downloaded source is cached at `/tmp/range-sweep-novelty-oct24`; temporary-cache persistence is not assumed. The manifest, not the cache path, provides retrieval identities.

Key hashes:

```text
TimeSeAD bb8efa9ce17f9cfb0bab77df08c32d986de8429e
  timesead/evaluation/evaluator.py
  f84495ccc62eeba905c515c8ac2d709b10302a6e20220692348ef73b6a633cea
  timesead/evaluation/ts_precision_recall.py
  d5bb774b4aab9e441e4119e957ce5fe52a4abed965d6286705836e002dd162c8
  LICENSE (MIT)
  3e3ed418d1b09a2917f4045cc49371554958fcc3337105a299adddb5805b87e2

prts 1.0.0.3 source distribution
  https://files.pythonhosted.org/packages/15/f7/2ba5af48ac7df243840dc36212690800b5eb360ad2545fe511ff1a095439/prts-1.0.0.3.tar.gz
  82baa65f3f121688e2b838b8512e6bd5d3b854bb1dcfae7dced7d78cffc095db
CompML/PRTS 66db2ac5f83ac9182ce29dcd7afc0f678a678eed
  prts/base/time_series_metrics.py
  9e029a3fff08c2603a1b30e5198484df6c833688fbc2637dae007e11e2b0bc6d
  LICENSE
  c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4

aeon ac9abc36b1bd53aa98dc5c89062561cc7638f40b
  aeon/benchmarking/metrics/anomaly_detection/_range_metrics.py
  2d1158c4fe18a4c8cbe319b6fd2cd0ce1c8eae4e7511ad473e6cbbf138669b31
  aeon/benchmarking/metrics/anomaly_detection/_continuous.py
  5544ac632bf192e5d2a9b60909ed10859708e426476349b3e58a5e83977d6ed6
  LICENSE
  dc3459a1fd14b6bcd10d13172dde23dd8c296660320dcb2b784efee5cd27c329

TimeEval 7c3622757b1a3afa9a84cbc97ce132d9e379f715
  timeeval/metrics/range_metrics.py
  ba45a0cd3994c075de1026bbbe086ba7a03d0c7a86ca894d1d0cfe854521f5c4
  LICENSE
  f047d8cf14baad94ec3d585efc35ec17ec9cecd4f95d2d95721d9bfcb91cf453

locussam/TSAD-Evaluator 3d88d30cb436c5c3270580f030fb091a542327f3
  src/evaluator.cpp
  2afd13f12a352656b5009c12cc0470ba4e64d43be72efb84827a13cba05d3eea
  LICENSE
  e3482601971706724254c616a5d13edaeeab57ba774ef6cbb24c67413ade242d

TSB-AD 303dffbfc11612995b17b06633f8c9d0ea0e38e5
  TSB_AD/evaluation/basic_metrics.py
  1fcddedf5ada1d5221f39ee568c7fddb9e7181bd7e1c19636c2cbecf40c97707
  LICENSE
  c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4

Prior blind-final-review.md preserved SHA-256
  bcac317c06f758190a382bdd740812c13feed1a936b7f05f7d82654fcd00e114
```
