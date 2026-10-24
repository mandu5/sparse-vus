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
| Benchopt VUS, revision `2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94` | Public cumulative-sum baseline, `thre=n` | Computes both ROC and PR; preserve that fact. Needs contemporaneous full-precision comparison before calling Klein universally strongest. |
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

## Outstanding decisions

- Reconstruct the primary experiment independently, including paired intervals
  and recording-family sensitivity. Repeated timings do not create new datasets.
- Check the complete eligible public baseline set on the new workload, including
  Benchopt, without changing the primary frozen study.
- Measure input preparation and memory; establish a second CPU result before a
  6-point claim.
- Obtain three independent reviews of the whole paper, with actual public
  accepted/rejected review evidence where accessible. Direct OpenReview API and
  forum reads currently return 403/browser verification; this is recorded, not
  replaced with invented review scores.
- Integrate only supported claims into a new manuscript revision and maintain
  the distinction between prepared, submitted, reviewed and accepted.
