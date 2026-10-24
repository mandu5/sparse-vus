# Sparse VUS: the PVLDB research case

Evidence cut: 24 October 2026. This is a research decision record, not an editorial
decision. The prospective protocol is in
[`superpowers/specs/2026-10-24-pvldb-evidence-design.md`](superpowers/specs/2026-10-24-pvldb-evidence-design.md).

## Why PVLDB, and why TMLR appeared

There are two manuscripts in this repository, with different contributions.
`paper/sparse_vus.tex` studies the exact VUS operator: support-event elimination,
complete global ties, interval geometry, and active-prefix extensions. It was
prepared for **PVLDB volume 20, Regular Research, Foundations and Algorithms**.
`paper/certified_sampling.tex` studies numerical threshold sampling, selection
regret, and integer certificates. Its narrower evaluation-reliability result was
considered for TMLR. A judgment about the latter's limited selection benefit is
not a review of the entire former algorithmic contribution.

This session returns to the complete exact-evaluator paper. The public Sparse
VUS software precursor remains disclosed; its already measured improvements are
not called new October 24 improvements. There is no verified prior refereed
publication of this exact-evaluator manuscript. Neither manuscript is treated as
submitted or accepted, and they will not be submitted concurrently with
overlapping claims.

The [PVLDB research call](https://www.vldb.org/2027/call-for-research-track.html)
explicitly includes formal algorithms, time-series analytics and data management
for ML. The scientific connection is substantive: we preserve and improve the
operator introduced and optimized in the VLDB/VLDB Journal VUS line, and measure
stored-score collection queries through model selection and output. A speedup
in a Python function alone does not settle the venue's significance requirement.
EA&B is appropriate only for a genuinely comprehensive comparative study; it is
not a category chosen to avoid an algorithmic novelty objection.

[TMLR's criteria](https://jmlr.org/tmlr/acceptance-criteria.html) concern supported
claims and whether readers can learn something. The sampling analysis fits that
question, but TMLR is neither an automatic fallback acceptance nor the same
publication credential as a VLDB research-track paper.

Target cycle, from the [official submission rules](https://www.vldb.org/2027/submission-guidelines.html)
and [dates](https://www.vldb.org/2027/important-dates.html): abstract **25 November
2026, 17:00 America/Los_Angeles**; paper **1 December 2026, 17:00** in that zone
(26 November / 2 December, 10:00 Korea). Regular Research allows 12 content pages,
excluding references. The core data-management advance and relevance statement
must be explicit. Single-blind author metadata remains Youngmin Ko, Independent
Researcher, Republic of Korea, with the supplied personal contact email.

## Surviving distinction, and what is not new

**One-sentence proposed contribution:** for the pinned dynamic VUS operator,
eliminate threshold states with no active support while analytically retaining
their ROC contribution, preserving complete global score ties and merged-component
coverage, yielding an exhaustive support-sensitive evaluator with proved bounds
and measured collection-level cost.

Sorted threshold sweeps, weighted precision/recall, buffer caching, standard
binary64 radix sorting, batched loop interchange and anomaly model selection are
prior techniques. The new batch implementation is an engineering refinement of
this exact operator; it is not by itself a new asymptotic algorithm. The support
theorem, the ROC predecessor correction, and the complete-tie/component handling
are the objects for an adversarial novelty and correctness review.

The bounded primary-source comparison comprises the following twelve 2024–2026
papers. Full source URLs and precise distinctions are preserved in
[`literature.json`](../artifacts/pvldb-research-20261024/literature.json). Software
baselines are additional evidence, not counted as papers.

| Work | Existing result | Remaining distinction / restriction |
|---|---|---|
| Boniol et al., VUS, VLDB Journal 2025 | The metric, static/dynamic reuse and optimized computation | Exact support-event transitions and the full integral must improve on these algorithms, not merely rename support caching. |
| PATE, KDD 2024 | Proximity-weighted PR with temporal buffers | We compute an existing different operator; no claim to invent weighted PR. |
| TSB-AD, NeurIPS Datasets and Benchmarks 2024 | Broad detector benchmark and VUS-PR evaluation | Our claim concerns evaluator fidelity and cost, not detection accuracy or a new dataset. |
| TAB, PVLDB 2025 | Unified benchmarking and evaluation pipelines | Our operator can be a component; benchmark orchestration is not new. |
| TSB-AutoAD, PVLDB EA&B 2025 | Selection, ensemble and generation comparison | Offline labeled evaluation is distinct from selecting a detector without labels. |
| Formally Exploring TSAD Evaluation Metrics, 2025 preprint | Formal metric properties and LARM/ALARM | Its formal scope excludes score-based volume-under-surface metrics; our result is computational, not a new metric axiom. |
| CCE, 2025 preprint | A different efficient metric and RankEval | Its linear-time result cannot be compared as the same returned VUS quantity. |
| Problem-Oriented Taxonomy, 2025 preprint | Metric utility and application-oriented taxonomy | Semantic choice differs from numerical approximation of a fixed target. |
| Did We Actually Fix It?, 2026 preprint | Adversarial seed-shopping and inter-metric ranking | We hold score vectors, labels and target fixed; no claim to discover seed-shopping. |
| Retrieval Over Training / RAMSAD, 2026 preprint | Retrieval-based detector selection | Exact profile evaluation supplies inputs; it is not a superior deployment selector. |
| Fast or Accurate?, VLDB PhD Workshop 2025 | Efficient CPU/GPU metric evaluation | Fast VUS implementation already exists; native metric contracts must be checked before runtime comparisons. |
| mTSBench, TMLR February 2026 | 344 multivariate series, 24 detectors and selection evaluation | Our 8-detector study is narrower and univariate; no state-of-the-art benchmark breadth claim. |

Recent work is supplemented by indispensable older ROC/PR integration and
range-metric papers in the manuscript. Finding a surviving distinction in this
bounded search is not proof that nobody has ever used it.

## Baselines and comparison eligibility

The primary task returns exhaustive **PR only**, for the original dynamic
square-root, sum-and-clip, right-step VUS target, over every integer width and
complete score classes. All methods receive the same float64 score vectors.

| Implementation | Role and configuration | Qualification |
|---|---|---|
| Klein fast-VUS, revision `1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00` | Unchanged public external PR baseline, `thre=n` | `thre=250` is sampled and belongs on a separate accuracy–cost frontier. |
| Benchopt VUS, revision `2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94` | Public cumulative-sum baseline, `thre=n` | Computes both ROC and PR. The completed supplement includes both native-consumer and matched two-output comparisons; Klein is faster on the measured panel, not asserted universally fastest. |
| Official VUS, revision `467bace0c103f5c2bdb4900306d82939bcac8ff9` | Semantic reference and prior algorithm | Python threshold loop is not the sole performance competitor. |
| Matched dense radix PR | Compiled internal algorithmic control | Same arithmetic and output; isolates support compression from Numba and sorting. |
| Released sparse radix PR | Strong internal/public precursor | A batch improvement must beat it, separately from whole-method gains over external software. |
| Active-prefix saturation | Strong internal alternative | Retain losses at default width; do not select widths after results. |
| Geometry-only batch | Ablation | Shares preparation but retains independent width integration. |
| Width-major stream batch | Prospectively selected new candidate | Shares per-width geometry and weights; allocates model-by-support ranks. |
| FF-VUS / aVUSi | Adjacent public implementation | The inspected native metric contract differs; exclusion from a same-output speed ratio is not evidence of superior runtime. |

The kernel claim is exact in the mathematical target; floating-point parity is
reported as a numerical check. It is not an integer enclosure certificate.

## Fixed investment criteria

The user's 1–6 gates remain the reporting rubric. Internal **5/10** means all six
are addressed with an identifiable scientific result, three real full-precision
collections, lower paired 95% speedup bounds above one, whole-workflow median
speedup at least 1.5 over the strongest eligible external baseline, and no open
validity defect. Internal **6/10** additionally requires a useful new mechanism
(prospectively: at least 1.25 geometric speedup over the released method, lower
bounds above one per collection, or an independently supported comparably
substantive generalization), at least 2x whole-workflow external speedup, two CPU
environments, and no unresolved major objection in three independent reviews.

These are investment thresholds fixed before new results, not PVLDB's score
scale, an acceptance probability, or a substitute for the user's six gates.

## Three tested directions and the new measurement

The development study compared (A) direct full-distinct evaluation on full-
precision outputs, (B) shared label computation and (C) partial integer
certification followed by exact fallback. Across six identified development
series and three existing detector outputs, width-major sharing had a 1.193x
geometric speedup over the released method. The certificate policy took 33.93x
as long, with zero early certified selections. The latter is retained as a
negative result and removed from the speedup claim.

The confirmatory study selected full NAB, SMAP and SMD collections by a frozen
rule, excluding the six development names, source-labelled synthetic files and
exact within-panel observation/label duplicates. It contains 73 series
(20/17/36) and eight fixed unsupervised detector families, giving 584 unrounded
score vectors. **62 series were previously measured by name**; new score
generation does not make the physical recordings unseen. Cross-catalogue
normalized or shifted duplicates have not been exhaustively ruled out.

Of these 584 outputs, 569 have more than 101 distinct scores. Thus the earlier
MSAD panel's <=101-score property does not describe this workload. This does not
by itself show approximation regret, detector superiority or runtime benefit.
The stored-score evaluation excludes training; its inputs were generated using
offline, unlabeled, transductive fitting. It is not an online detection protocol.

The fixed experiment measures full validation, preparation, allocation,
evaluation and winner selection, then separately measures complete file reads
through decision JSON writes. There are twelve balanced method orders, primary
width 30 and secondary width 100. Hashes bind the protocol, sources and scores.
All successes and adverse tails must enter the final report.

## Completed primary evidence and remaining review condition

The primary Apple M1 Pro run and its independent v3 record audit are complete.
At width 30, case geometric Klein/stream ratios are 30.51, 25.77 and 25.17;
whole-collection workflow ratios are 23.03, 22.16 and 22.57 for NAB, SMAP and
SMD. All exact numerical winner sets match. The matched compiled dense control
is 3.54--3.96 times slower than stream; removing batching, dense/released ratios
are 2.368, 2.905 and 3.279. These ablations identify support compression rather
than only a language/runtime advantage. Released/stream is 1.496, 1.271 and
1.207, so the SMD Mac result misses the prospective 1.25 incremental threshold.

The completed separately frozen supplement compares Benchopt on the same inputs.
Matched ROC+PR workflow ratios are 25.32, 32.06 and 40.92. The sampled 250-point
API changes 14/73 winner sets, four with regret at least 0.01, whereas 1,000
thresholds change three sets and incur no losses of 0.01. Exact stream also
beats the 250-threshold workflow by 11.25, 9.68 and 7.27. These are conditional
accuracy-cost results; they do not claim widespread approximation harm.

SMD dependence sensitivity explicitly uses nine unique label blocks, including
18 cases sharing development geometry. Removing these 18 cases still gives
released/stream 1.220 with an unadjusted 95% block interval [1.191,1.253]. This
does not establish physical-source independence. Resource measurements retain
the adverse dense-memory result: at n=500,000, M=8 and positive fraction 0.5,
stream uses 225.0 MiB peak process RSS versus 175.2 released and 210.6 dense.

The [fresh Linux execution](https://github.com/mandu5/sparse-vus/actions/runs/40049786600)
completed on AMD EPYC 7763, with data download, new score generation, primary and
supplemental timings and both independent audits. Its primary external workflow
ratios are 20.06, 20.28 and 16.17; released/stream case ratios are 1.886, 1.580
and 1.340. No CPU intervals are pooled and the hosted-runner outlier is retained.
New detector scores differ across hosts: sampled winner changes are 13/73,
with three losses of 0.01. The raw score-generation cause is not diagnosed from
timing records. Receipts, raw records and audit outputs are retained in
`artifacts/pvldb-research-20261024/linux-reproduction/`; generated Linux NPZ
arrays were not uploaded and must be regenerated for a new input-file audit.

Three independent scientific reviews are stored in `docs/reviews/20261024/`.
Actual public accepted/rejected OpenReview notes were retrieved through a
hash-recorded research-data mirror after direct requests failed. They calibrate
qualitative objections, not an acceptance probability. The confidential PVLDB
CMT form is not publicly retrieved; the internal format follows the verified
public PVLDB criteria and discloses that limit.

The operating-range condition now has a separately frozen, completed and
independently audited experiment: all nine MITDB/SWaT recordings
(419,919--650,000 points), sixteen controlled n/density/K/M/L/tie regimes,
matched public outputs and independently reconstructed prefix counts. MITDB
workflow latency is 53.14 seconds for Klein versus 2.30 seconds for stream;
SWaT is 4.34 versus 0.245 seconds. Matched ROC+PR workflow ratios are 29.50 and
25.66. Whole-method gains persist while released/stream workflow intervals
include one on both collections. At 90% positive density, dense/released is
0.980 under the paired-geometric estimator, so support compression itself
loses its runtime advantage. These retained limits distinguish a measured
operating range from universal superiority. Synthetic cases are not counted
as public datasets. Final independent review and the minimal Klein
support-threshold ablation determine the final score band.
