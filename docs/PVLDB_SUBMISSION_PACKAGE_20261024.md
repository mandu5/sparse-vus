# PVLDB submission package

Prepared for the exact-evaluator manuscript, not the separate threshold-sampling
manuscript. This file contains prepared submission text and verified metadata;
it is not a CMT registration or submission receipt.

## Paper and author

- Title: **Exact VUS Evaluation by Support Events and Shared Interval Geometry**
- Author: **Youngmin Ko**
- Affiliation: **Independent Researcher, Republic of Korea**
- Contact: **rhdudals0505@naver.com**
- Manuscript: `paper/sparse_vus_pvldb20261024.pdf`
- Source: `paper/sparse_vus_pvldb20261024.tex`
- Artifact: <https://github.com/mandu5/sparse-vus/tree/research/pvldb-20261024>
- Reproduction instructions: `docs/REPRODUCE_PVLDB_20261024.md`
- Public fresh-execution receipt: <https://github.com/mandu5/sparse-vus/actions/runs/40049786600>

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

This paper addresses the cost of repeated exact analytical evaluation over
stored time-series detector profiles. A query joins a shared binary label
sequence with several score columns, integrates the original dynamic VUS
operator over score thresholds and tolerance widths, selects the maximizing
profile, and writes its result. The contribution reduces the threshold states
and width-dependent work needed for that aggregate while preserving complete
global ties, merged anomaly components, and the dynamic ROC contribution.

The technical development builds directly on VUS and its optimized evaluators
in the PVLDB/VLDB Journal literature. The formal target and support-event
identities are in Section 2; comparisons to existing evaluators and the exact
algorithm are in the subsequent algorithm sections. The prototype includes a
compiled dense control and shared-label preparation/streaming ablations, so the
operator-level gain is distinguished from compilation and conventional batching.
The evaluation measures complete public calls and collection workflows from
score-file reads through decision-file writes, with public raw-data provenance,
fixed full-precision inputs, paired uncertainty and a fresh second-CPU execution.

The work concerns analytical operator efficiency and reproducibility. Its scope
does not require a claim that the detector inputs are state-of-the-art predictors
or that the implementation is a full database engine.

## Related-work and submission declarations

The unrefereed Sparse VUS 0.3.0 software/working-paper precursor is cited in the
manuscript. Whole-method gains and the later sharing increment are separately
reported. The exact-evaluator and narrower sampling manuscripts must not be
submitted concurrently with overlapping claims. Existing related submission
status and author conflicts must be verified in CMT from their actual records;
this package does not invent or pre-attest those author declarations.

## Upload contents

Use the final compiled PDF and the publicly accessible artifact branch or its
final immutable commit. The abstract should match the compiled manuscript.
The source, numerical tables, raw timing records, hashes, review-response
ledger and reproduction commands remain in the artifact. Internal reviews are
research-quality checks, not external decision letters or acceptance receipts.
