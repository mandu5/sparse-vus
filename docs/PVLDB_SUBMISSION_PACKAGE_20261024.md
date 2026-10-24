# PVLDB submission package

Prepared for the exact-evaluator manuscript, not the separate threshold-sampling
manuscript. This file contains prepared submission text and verified metadata;
it is not a CMT registration or submission receipt.

## Paper and author

- Title: **Exact Evaluation of Time-Series Anomaly Metrics by Local Event Statistics**
- Author: **Youngmin Ko**
- Affiliation: **Independent Researcher, Republic of Korea**
- Contact: **rhdudals0505@naver.com**
- Manuscript: `paper/exact_metrics_pvldb20261024.pdf`
- Source: `paper/exact_metrics_pvldb20261024.tex`
- Artifact: <https://github.com/mandu5/sparse-vus/tree/research/pvldb-20261024>
- Reproduction instructions: `docs/REPRODUCE_PVLDB_20261024.md`
- Public combined fresh-execution receipt: <https://github.com/mandu5/sparse-vus/actions/runs/40062043152>
- Reproduction source commit: `e2405e39ec23486a3d228240569b48785de32cb4`
- Final PDF SHA-256: `6646c1f497273f2e4731d158761568c26b7cf04b3b06978813aa1962518e3a11`
- PDF extent: 13 total pages, references begin on page 12; 12-page content limit satisfied.

The author metadata follows the author's already-confirmed personal research
status and prior confirmation. Alumni status is not represented as a current
university research appointment. No new authorship/contribution question is
needed for preparation of this package.

## Venue choice and schedule

**PVLDB volume 20, Regular Research, Foundations and Algorithms** is the selected
category. The central contribution is an exact operator and its theoretical
representation, evaluated through a stored-profile query workload. The paper
is not framed as a new detector or an industry deployment. The public
[research call](https://www.vldb.org/2027/call-for-research-track.html) expressly
identifies conceptual/algorithmic contributions with prototype evidence in
this flavor of Regular Research.

The established target cycle is abstract **25 November 2026, 17:00
America/Los_Angeles**, and paper **1 December 2026, 17:00** in that zone, or
**26 November / 2 December, 10:00 KST**. The abstract portal for that cycle
opens on 20 November under the published rules. An earlier November paper
cycle has an abstract deadline of 25 October; adopting it would be an explicit
schedule change, not a change to the frozen experiments.

CMT: <https://cmt3.research.microsoft.com/PVLDBv20_2027/>

The [submission rules](https://www.vldb.org/2027/submission-guidelines.html)
allow 12 content pages excluding references and require single-blind author
metadata, supplemental artifacts, conflict declarations, and disclosure of
related concurrent submissions. The paper uses the current official template;
`artifacts/pvldb-research-20261024/template-check.json` records byte equality of
the three style files against upstream revision `39c95f5c` on 24 October.

## Self-Assessment of Relevance: prepared text

This paper addresses repeated exact analytical evaluation over stored time-series
anomaly-detector profiles. A query combines labels with score columns, evaluates
an established metric over threshold states, and selects the maximizing profile.
The first contribution represents dynamic VUS with support events, complete
score ties and the ROC predecessor correction. The second maintains flat
reciprocal-cardinality range precision/recall by constant-time local updates to
overlap and fragmentation statistics during point activation. Sorting,
component-tree connectivity and query bucketing are credited prior techniques;
the additional contribution is the metric-specific exact state representation.

The work builds directly on VUS and its optimized evaluators in PVLDB and the
VLDB Journal, and on established range metrics and exact analytical processing.
The prototype preserves each operator's output contract and compares complete
calls against public implementations and conventional same-compiler controls.
The range result removes repeated raster scans at observed thresholds, with
three public collections, paired uncertainty, full numerical curves and explicit
low-cardinality losses. The original stored-profile VUS workflow includes array
reads, metric computation, selection and decision writes. A separate actual
nine-metric public consumer improves only 1.031 times; this adverse whole-system
result is not replaced with a partial-operator speedup.

The claimed scope is exact analytical operator evaluation. It is not a new
anomaly detector, a label-free model selector, a new metric or a full database
execution engine. Scientific value rests on the exact reductions, fair compiled
controls and measured cost/selection consequences, not on using database
terminology for an otherwise unrelated task.

## Related-work and submission declarations

The unrefereed Sparse VUS 0.3.0 software/working-paper precursor is cited in the
manuscript. Whole-method gains and the later sharing increment are separately
reported. The exact-evaluator and narrower sampling manuscripts must not be
submitted concurrently with overlapping claims. Existing related submission
status and author conflicts must be verified in CMT from their actual records;
this package does not invent or pre-attest those author declarations.

The reviewer-nomination field can identify Youngmin Ko as the best-qualified
available author under the explicit single-author/no-qualified-reviewer provision.
This does not assert the separate two-database-paper qualification. CMT conflict
and related-submission declarations must reflect actual records, including the
venue's five-year institution/collaboration rule; they are not pre-attested by
this preparation document.

## Upload contents

Use the final compiled PDF and the publicly accessible artifact branch or its
final immutable commit. The abstract should match the compiled manuscript.
The source, numerical tables, raw timing records, hashes, review-response
ledger and reproduction commands remain in the artifact. Internal reviews are
research-quality checks, not external decision letters or acceptance receipts.

## Current internal decision

Three independent AI mock reviews of the new combined manuscript have completed
initial assessments and final evidence-closure addenda. Their initial
recommendations were Weak Accept 7, Weak Accept 6 and Revise 6 on explicitly
internal surrogate scales. Final recommendations are Weak Accept 7, Weak Accept 6
and Accept 7; the last reviewer closed their stated presentation/reproduction
conditions. Remaining limitations are recorded in
`docs/EXACT_METRICS_RESULT_20261024.md`. All six evidence gates and
the prospective investment-6 generalization route are supported for the narrowed
operator contribution. The original VUS-only 7/5/5 assessments remain in the
historical record. Reviewer numbers are not an acceptance probability or a
substitute for external review.
