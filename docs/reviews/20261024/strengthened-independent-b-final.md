# Final independent review B — AI simulation

**Recommendation: Accept. Internal research-quality score: 7/10.**

This is an AI-simulated research review, not human peer review, an official
PVLDB rating, or an acceptance-probability estimate. It assesses the exact
snapshot below. My recommendation is positive but qualified: the contribution
is a useful, supported specialization of established algorithmic tools, not a
new general data-structure paradigm. The strongest contribution is the joint
weighted range trajectory and its measured exhaustive-query benefit. The VUS
sharing refinement alone would not support this recommendation.

The internal scale is defined here: 1–3 denotes fundamental problems or little
established research value; 4–5 denotes promising work requiring substantial
correction or evidence; 6 denotes a borderline contribution; 7 denotes solid,
publishable research with material limitations; 8 denotes a strong and more
widely consequential contribution; 9–10 denotes exceptional work. These are
reviewer-defined quality anchors, not a translation of any venue's scores.

**Snapshot and independence.** Reviewed on 24 October 2026:

- Manuscript commit: `ca8761cc40d493141511cad4bc3c184c48a681dc`.
- Evidence commit: `3a2ab2dcb6a9cbe1a83b0ce090f45d4abc4305c9`.
- PDF: `paper/exact_metrics_strengthened20261024.pdf`.
- Verified PDF SHA-256:
  `38ad66e21f7a21ab9d58f80f9b8d8499f92e55014e714c064cd467bd1cc05e54`.

I verified HEAD and the PDF hash before assessment, checked all eight source
hashes in `manuscript-review-snapshot-v1.json`, read the complete manuscript and
its includes/bibliography, and rendered and inspected all 13 PDF pages.
References begin on page 12. I used my earlier static source analysis and
rechecked the current source bindings, conventional interval control, native
adapter, and reproduction driver. I read the specifically permitted artifact
audits and public calibration documents. I did not read other simulated
reviewers' opinions, scores, or the working decision document. No target score
was supplied or used.

**Synopsis and justification.** The paper identifies sufficient local state
for two existing anomaly-evaluation operators. For dynamic VUS, inactive
threshold runs have zero PR contribution but require a ROC predecessor
rectangle; global ties and width-dependent support must remain exact. For
Tatbul range precision/recall, score activations maintain recall overlap and
fragmentation together with the contributions of changing predicted
components. Endpoint-dependent positional weights are recovered from fixed
feature prefixes, including weights split at a moving midpoint. The resulting
complete canonical trajectory takes O(n log n) arithmetic operations under the
stated model. Same-compiler raster and closed-form interval controls establish
an increment beyond compilation and ordinary per-query optimization. Native
TimeEval measurements show a useful whole-workflow effect when exhaustive
queries are requested. The manuscript confines that result to its actual
contracts and retains the unhelpful default-consumer and VUS-only outcomes.

## Three strengths

1. **The mathematical state is explicit and checkable.** The paper provides
   actual invariants, update identities, arithmetic assumptions, and
   counterexamples to insufficient state. In particular, it explains why an
   off-label bridge can change precision without changing recall, why a
   component's unsplit count and first moment do not suffice for middle bias,
   and why dropping inactive ROC transitions changes the target. This is more
   informative than presenting a faster implementation without identifying
   the work that can be removed.
2. **The decisive comparisons are now credible.** Tatbul's conventional
   ordered-interval/closed-form method is represented by a separately frozen
   same-compiler control that discovers intervals anew at each query. Raster
   is retained when it is faster. The native consumer includes loading,
   three metrics, and result writing. These controls directly answer the
   concern that a large public-Python speedup is merely implementation
   overhead. Exhaustive benefits survive both controls and both hosts.
3. **Negative results and provenance substantially improve interpretability.**
   The low-cardinality losses, two-recording MSL sensitivity, tiny separate-panel
   selection regret, 1.031-fold nine-metric VUS consumer gain, failed
   certificate route, and unfavorable direct-ramp VUS control remain visible.
   Raw timing records and metric curves allow independent reconstruction.
   The partial pilot, parser correction, host-dependent scores, censors, and
   post-hoc contrasts are disclosed rather than presented as wholly
   prospective or universally replicated findings.

## Three weaknesses

1. **Novelty and conceptual breadth are moderate.** Sorting, offline
   activation, component-tree attributes, prefix moments, and caching are
   established techniques. The new content is a specialized metric
   augmentation, not a new tree, new metric, or generally faster sorting
   method. The sorting lower bound is a correct standard reduction, not a
   separate source of deep novelty. The general finite-feature theorem is
   broader than the implemented canonical family.
2. **Practical significance is concentrated in exhaustive evaluation.** The
   default native workflow has only small effects, with three of four
   combined intervals crossing one; the fourth supports approximately 1.4%.
   The separate public-detector panel has maximum selection regret only
   0.001412, and the earlier nine-metric consumer gains 1.031-fold. The work
   therefore establishes cheaper exact evaluation more clearly than a
   consequential change to ordinary detector selection or every benchmark
   pipeline. MSL id7 remains a real counterexample to uniform acceleration.
3. **Uncertainty and workload diversity remain limited.** Six balanced orders
   are not six independent workload draws. The narrow within-run intervals do
   not cover between-run variation: the original and supplemental Linux
   exhaustive native ratios are 1.932 and 2.756 despite identical score hashes.
   Only two new MSL recordings and two public detectors are present, while
   the original panel has known reuse and label dependence. All results are
   author-controlled executions, not external scientific replications.

## Correctness and technical merit

I found no substantive mathematical counterexample to the stated results.
My main checks were as follows.

- The inactive-run ROC rectangle telescopes while the dynamic denominator
  and recall remain fixed; the complete global tie then supplies the next
  transition. PR's zero contribution on that run follows separately. The
  explicit ROC tail and signed horizontal increments are retained.
- The two-distance VUS lemma follows from the restricted ramp: every active
  ramp is at least 1/sqrt(2), so two active contributions clip to one. This
  is a property of the pinned target, not arbitrary VUS implementations.
- Within a contiguous true interval, active runs correspond to intersecting
  predicted components. The insertion update for c_j is therefore valid.
  An off-label insertion cannot join two fragments of the same true interval
  along a one-dimensional path outside that interval.
- Removing adjacent precision contributions and inserting the merged
  component is sufficient. The true-start prefix formula for h([a,b]) handles
  both starting inside a true interval and starting at its first point.
  Moving middle weights require the two prefix pieces described in the paper.
- The claimed bound now includes cardinality evaluation through C_gamma(n).
  Repeated squaring supports the O(log n) exact-arithmetic cost claimed for
  the improved factor. The text correctly separates arithmetic-operation
  complexity from exact-rational bit complexity and from the implemented
  floating-point exp/log1p evaluation.
- The padded sorting reduction uses both label classes and query-associated
  outputs. It establishes the comparison lower bound asserted in the final
  text. It does not establish optimality for maximum-only output, anonymous
  output multisets, unrestricted algebraic computation, or binary64 radix
  algorithms; the manuscript explicitly excludes these readings.

The conventional interval control really performs a complete per-query scan
and ordered overlap traversal using closed-form sums. It does not reuse
cross-threshold metric state. Its shared formula helpers reduce implementation
independence, but the separate raster formulation, rational-oracle work,
public implementations, and full saved curves provide other checks.
The native adapter preserves the declared threshold selection, inclusive mask
via predecessor binary64 threshold, synthetic endpoints, sorting, and AUC
integration. Its supported configuration is explicitly narrower than the
general weighted operator.

Correctness evidence remains empirical for binary64 accumulation; there is
no all-input rounding certificate. I did not rerun the oracle tests or
regenerate detector profiles for this review.

## Novelty, significance, and strongest eligible comparators

The decisive antecedent for the weighted operator is
[Tatbul et al., Section 5.5](https://papers.neurips.cc/paper_files/paper/2018/file/8f468c873a32bb0619eaeb2050ba45d1-Paper.pdf),
which already provides efficient ordered-interval overlap evaluation and
canonical positional preferences. Classical component trees already supply
threshold births and merges; size-based per-threshold precision/recall also
exists in [Ranefall and Wählby](https://doi.org/10.1002/cyto.a.22806).
The submitted augmentation additionally maintains fixed-label overlap,
fragmentation on both sides, and changing precision normalization. The paper
constructively describes how an augmented component tree could implement the
same identities and claims no asymptotic advantage over it. That boundary is
appropriate. I would not require an unaugmented component tree as a numerical
baseline for a metric it does not compute.

For experiments, the strongest eligible conventional reference is the faster
of the matched raster and interval implementations under the same target and
queries. No single control is fastest everywhere. The paper now preserves
both and labels the per-recording lower envelope as descriptive. My earlier
objection that ordinary interval optimization was omitted is resolved.

For VUS, public support cumulative sums and dense segment methods already
remove substantial work. Klein, Benchopt, the minimal support patch, the
same-compiler direct-ramp control, and geometry-only sharing are all relevant.
The direct-ramp control outperforming the released single-model evaluator
prevents attributing the public-library gap to nearest geometry. The remaining
shared-label increment is useful but modest. Excluding the differently defined
FF-VUS from equal-output speed ratios is justified by the semantic boundary;
it does not establish superiority over unmeasured CPU/GPU implementations.

My assessment is **some new ideas, solid technical work, and a bounded but
meaningful improvement over existing evaluation operators**. The detailed
weighted state and matched exhaustive consumer result together clear my
publication threshold. The numerous contextual 2024–2026 citations are not
the reason: novelty must be judged against the closest algorithms, including
older ones, rather than a reference count.

## Experimental support and independently checked facts

After all timing studies had finished, I independently reconstructed saved
results with small reader-only scripts. They imported no candidate or audit
producer and ran no detector fit, metric evaluation, new timing, bootstrap,
or benchmark. This is independent arithmetic over archived outputs, not an
independent raw-data replication.

- All eight manuscript-source hashes and the PDF hash match the snapshot.
  The frozen weighted runtime/producer source hashes also match current
  files in all four protocols.
- All 624 referenced weighted curve-archive hashes match. From the actual
  saved arrays, the largest inter-method discrepancy is
  2.4980018054066022e-15 for the two original studies and
  2.3869795029440866e-15 for the two conventional-control studies.
  Reconstructed per-profile optima and winner sets match every saved record.
- Each of the four executions has 312 singleton grid winner sets. Direct
  saved-curve reconstruction gives maximum best- and worst-tie regret
  0.00141219497462175, with one nonoverlapping case under middle/one and none
  under the other semantic choices. My earlier tie-policy evidence concern
  is resolved for this panel; the result is still explicitly post-hoc.
- I independently recomputed collection point estimates from all four sets
  of 11,232 raw timing records using the stated medians and equal log weights.
  The new original-Linux distinct raster/sweep values are
  7.459541/15.848135/1.669539 for WSD/Stock/MSL. The supplemental interval/sweep
  values are 7.322733/26.339148/1.706427 on Mac and
  12.944875/36.148889/2.381477 on Linux.
- All 528 completed native result-CSV hashes match their records. Comparing
  their scalar contents gives maximum discrepancy 3.3306690738754696e-16.
  Both original runs have 120 completed trials, four timeouts, and 20
  prescribed skips. Both compiled supplements have 144 completed trials.
  Completed public-reference coverage is 28/52 profiles per contract in
  each original run; the supplements add none.

The following combined native point estimates were independently reconstructed
from six matched-order whole-workflow trials per comparison:

| Execution | Default raster/bucket | Exhaustive raster/bucket | Exhaustive interval/bucket |
|---|---:|---:|---:|
| Original Mac | 1.016841 | 2.728143 | not measured |
| Original Linux | 1.014469 | 1.931818 | not measured |
| Supplemental Mac | 1.026415 | 2.731695 | 3.034083 |
| Supplemental Linux | 1.015586 | 2.756131 | 3.190184 |

Thus the abstract's 1.93–2.76 range is supported without pooling or selecting
only the more favorable Linux run. I inspected the archived interval results
and their calculation method but did not independently rerun the bootstrap.
Its approximate conditional interpretation is essential.

I also checked all eight Figure 1 input bindings and reconstructed its lower
envelope from the raw supplemental records. The CSV agrees within 2.2e-14.
MSL id7 has 42 summed distinct queries and lower-envelope ratios approximately
0.563 on Mac and 0.684 on Linux; its plotted losses are real. The figure
supports a workload association with query cardinality, not an isolated causal
effect or a deployable selector.

These checks used the directories `weighted-mac-v2`, `weighted-control-mac-v1`,
`linux-original-replay/weighted-linux-v2`,
`linux-interval-replay/weighted-control-linux-v1`, and their corresponding
four TimeEval archives under `artifacts/pvldb-research-20261024/strengthening/`.
The excluded `weighted-mac` pilot is retained with 5,400 records and its
chronology is disclosed. I did not pool it into any calculation.

## Reproducibility and presentation

Reproducibility is strong for a research artifact, with a remaining boundary
between archived-output verification and raw-input reproduction. The
[original Linux run](https://github.com/mandu5/sparse-vus/actions/runs/40079636938)
and [conventional-control run](https://github.com/mandu5/sparse-vus/actions/runs/40081512476)
have successful public receipts. These are fresh author-controlled CI
executions, not third-party replications. The public reproduction driver at
the evidence commit returned HTTP 200 and its bytes match the reviewed local
driver. It verifies sources and inputs, regenerates public detector outputs,
executes the frozen studies, and invokes separate output auditors. The paper
correctly uses separate drivers for the earlier evidence and the new controls;
it does not provide a single invocation for every table in the entire paper.

I did not reload the original Linux raw observations or detector-score arrays;
the corresponding raw-input identity claims rely on the bound on-host audits.
The public package's acquisition instructions and digests are useful despite
withholding raw datasets and score vectors where redistribution terms are
unconfirmed. This restriction and the one-ULP decoding contract are disclosed.

All PDF pages are legible with no visible clipping or overlapping content.
The figure, tables, theorem restrictions, loss cases, and references are
present. The document remains dense: the reader must distinguish strict
grid/observed F1 queries from native inclusive AUC queries and original from
supplemental executions. A compact contract/result map would improve reading
more than additional result volume. The sorting expression split across
pages 4–5 is a minor layout issue, not a correctness or submission blocker.

## Venue fit and public-review calibration

**Fit: yes, for PVLDB Volume 20 Regular Research / Foundations and Algorithms.**
The work addresses repeated analytics over stored score columns and
substantively optimizes a PVLDB/VLDB Journal metric lineage. Its formal
algorithms and native consumer evaluation meet the relevant kinds of
contribution described by the
[current research call](https://www.vldb.org/2027/call-for-research-track.html).
This is a narrower data-management contribution than a general query engine,
but neither a new engine nor new detector is required by that category.
The 13-page PDF has non-reference content within page 12, satisfying the
stated Regular Research page allowance. The next scheduled cycle is an
abstract by 25 October 2026 and paper by 1 November 2026, 17:00 Pacific Time;
administrative submission status is outside this review.
[Current submission guidelines](https://www.vldb.org/2027/submission-guidelines.html).

I directly read the university-hosted
[historical initial PVLDB reviews](https://dbis.cs.tu-dortmund.de/publikationen/2020/data-parallel-query-processing-on-non-uniform-data/vldb-2020-reviews/)
and [revision reviews](https://dbis.cs.tu-dortmund.de/publikationen/2020/data-parallel-query-processing-on-non-uniform-data/vldb-2020-revision-reviews/)
for *Data-Parallel Query Processing on Non-Uniform Data*. Their relevant
questions concern adaptation of known techniques, whole-query benefits,
comparison to strong complete systems, unfavorable regimes, and whether a
secondary implementation effect explains the claimed mechanism. I applied
those questions here. The matched conventional controls and retained weak
consumer results address them; they do not make this paper as broad as DogQC
or entitle it to the same editorial outcome. This report adapts the historical
form's fields; the private current CMT form was not retrieved.

For adjacent accepted/rejected calibration, I read original note contents
from the four cached public-mirror records and verified each file SHA-256
against `verified-note-metadata.json`:

- [When Foundation Models are One-Liners](https://openreview.net/forum?id=H27kvyG4qf):
  the accepted case stresses scoped conclusions, strong baselines, and
  statistical support. This paper's narrow computational claims and explicit
  negative regimes respond to analogous objections. Its accepted publication
  is independently present in the
  [official ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/cf70320e93c08b39b1b29a348097a376-Abstract-Conference.html).
- [Unsupervised Model Selection for Time Series Anomaly Detection](https://openreview.net/forum?id=gOZ_pKANaPW):
  the accepted decision credits usefulness and extensive evidence despite a
  specialized combination of existing ideas. This supports evaluating the
  actual increment rather than rejecting solely because component tools are
  classical. It does not remove this paper's significance burden.
- [Subsequence Anomaly Detection via Graph Neural Networks](https://openreview.net/forum?id=73U_NlKaNx):
  the rejection raises incomplete baselines, limited novelty, and unclear
  component attribution. The interval control, direct-ramp VUS control, and
  geometry-only ablation are decisive protections against analogous failures.
- [Hypothesis Testing for Dynamical Systems](https://openreview.net/forum?id=G-dM79m_EXd):
  the rejection highlights an unclear new contribution and a weak connection
  between theory and implementation. Here the explicit maintained state,
  implementation boundary, and matched controls make that connection clearer.

The note source is the
[public Paper-Review-Dataset mirror](https://huggingface.co/datasets/WENJINLIU/Paper-Review-Dataset).
The origin service's current bytes were not independently matched to those
records. The older accepted program corroboration is recorded in the allowed
calibration file; my fresh program-page request was inaccessible. I use these
small, purposive adjacent cases qualitatively, not as a score conversion or
statistical acceptance model.

## Remaining revisions, largest uncertainty, and finite follow-up

**No remaining substantive blocker found for the current bounded claims.**
The missing conventional baseline and tied-selection evidence raised in my
initial review are now resolved. I do not condition acceptance on collecting
more favorable recordings or eliminating genuine failure regimes.

Two nonblocking changes would improve the submission: (1) a compact map of
operator, query contract, output, and corresponding primary table; and
(2) an immediately readable four-execution native summary retaining both
conventional controls and all default-query intervals. The existing text
already supplies the relevant facts, so these are presentation revisions,
not requests for new findings.

The largest remaining uncertainty is **how frequently real users need the
exhaustive queries for which the algorithmic increment matters**. The present
paper demonstrates a worthwhile exact operator, but does not establish broad
decision-quality benefits or pervasive end-to-end savings. That uncertainty,
combined with moderate novelty, keeps my score at 7 rather than 8 or higher.

A specific finite follow-up could materially change confidence in the
portable quantitative effect: retain the same 52 Linux score profiles and
sources, run five independently started session blocks with declared CPU
affinity and fixed warm-up, randomize raster/interval/bucket order within
each block for both native query contracts, and report block-level paired
ratios including every result. This would directly test the sizeable
between-run variation that the current conditional intervals omit. A collapse
of the exhaustive gain would weaken my significance judgment; a stable gain
would strengthen its portability. It would not increase the algorithm's
conceptual novelty, and it is not required for my present Accept judgment.

**Final exact-snapshot judgment: Accept, internal quality 7/10.** Confidence is
moderately high in the mathematical and archived-output assessment, and
moderate in the significance/venue judgment. This recommendation follows
from the scoped algorithmic increment and measured consumer benefit, not the
number of experiments, audits, commits, or the desired publication outcome.
