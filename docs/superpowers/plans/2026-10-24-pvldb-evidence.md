# Sparse VUS PVLDB Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish or falsify the fixed research-score 5/6 conditions using complete, exact VUS collection workloads.

**Architecture:** Preserve all frozen prior evidence. Add a shared-label batch evaluator and an independent full-precision experimental panel, comparing complete calls and complete stored-score selection workflows. Keep the sampling-certificate route as a separately measured alternative, with exact fallback.

**Tech Stack:** Python 3.12, NumPy, Numba, scikit-learn, standard-library provenance and JSONL records.

**Spec:** `docs/superpowers/specs/2026-10-24-pvldb-evidence-design.md`

## Global Constraints

- Baseline commit `92319eafd0f937a152edf3a5c7e4355b2114acce`; prior frozen artifacts and sources unchanged.
- All methods preserve complete global ties and the original dynamic, right-step PR target.
- At least three public collections, eight genuinely different detector families, unrounded stored scores.
- Full validation, preparation, allocation and selection included; no simultaneous timing workers on one host.
- Claims of rigorous real-arithmetic certification require integer bounds; floating-point parity alone does not supply them.
- No favorable outcome changes the frozen cohort, baseline, primary width, or decision threshold.

## Review Focus

- Off-support points tied with support affect global denominators and must never be dropped.
- Signed zero, negative scores, large ties, nearly dense support and boundary anomalies must preserve the scalar contract.
- Shared geometry may save time while materializing excessive memory; report both preparation and peak live arrays.
- Near-tied model winners need a declared numerical tie policy; certificate claims use strict rational comparisons.
- Regenerated score arrays can reuse old physical recordings; receipts must not call them unseen data.

## Task 1: Literature and venue contract

Files: `docs/pvldb_research_case_20261024.md`, `artifacts/pvldb-research-20261024/literature.json`.
- [x] Inspect >=10 primary 2024-2026 papers; retain precise comparisons and sources.
- [x] Read official PVLDB categories, scope and deadlines; explain the prior TMLR branch.
- [x] Define strongest eligible baselines and exact source revisions.
- [x] Review the design before promoting a new publication claim.

## Task 2: Batch evaluator and three measured alternatives

Files: `src/sparse_vus/batch.py`, `tests/test_batch.py`, `experiments/pvldb_development.py`.
Interface: `batch_pr(y, scores, max_buffer, strategy='stream') -> np.ndarray`, where scores is model-by-time.
- [x] Write failing correctness tests against independent dense evaluation, including complete ties, boundaries and input validation.
- [x] Implement geometry-only reuse and width-major streaming without changing existing evaluators.
- [x] Test fixed randomized, adversarial and exact rational fixtures.
- [x] Run development comparisons: direct full-distinct evaluation, shared batch computation, and certificate-plus-fallback selection; retain losses.
- [x] Freeze the implementation chosen for prospective evaluation before inspecting its confirmatory results.

## Task 3: Full-precision panel and primary experiment

Files: `experiments/pvldb_full_precision.py`, `tests/test_pvldb_full_precision.py`, `artifacts/pvldb-research-20261024/`.
- [x] Freeze cohort and detector parameters without evaluating metrics; bind original archive/input hashes and reused-source identities.
- [x] Generate eight detector-family scores on complete real inputs, with no output rounding or manufactured jitter.
- [x] Freeze balanced trial orders and source hashes, then measure public exact baselines, ablations and stored-score workflow.
- [x] Compute per-collection paired confidence intervals, selection agreement, failure tails and resource costs.
- [x] Independently reconstruct results and provide one reproduction command.

## Task 4: Scientific decision and review

- [x] Update all six gates with evidence; never count a prepared artifact as a result.
- [x] Obtain three independent reviews using verified venue criteria and public-review calibration.
- [x] For each remaining scientific failure, try three materially different remedies before changing the claim or target.
- [x] Select the supported research-score band and venue; only supported results enter the manuscript.
- [x] Prepare the final submission path if gates pass; preserve actual submission/acceptance receipts separately.

## Execution ledger

2026-10-24: User explicitly renewed sparse-vus research; previous stop recommendation is superseded. Existing linked worktree is clean at baseline. New branch `research/pvldb-20261024`. Existing goal replacement rejected because an unfinished goal exists; no false completion/resume recorded. Standard `python3` lacks Numba; use existing `/opt/anaconda3/bin/python` (NumPy 1.26.4, Numba 0.59.1) consistently and record versions.

2026-10-24, primary completion: 73 complete cases, eight unrounded score procedures, two widths and complete collection workflows passed their recorded numerical comparisons. The supplementary Benchopt/matched-pair and sampled accuracy-cost study retains a separate freeze. Source files used in timing are now immutable.

Independent reviews identified nine shared-label SMD blocks (18 cases also share a development label sequence), a public-call `Mn` memory temporary, and missing strongest-baseline/current-paper integration. These are explicit revision conditions. The initial label-block sensitivity is positive, but does not establish physical-recording independence.

Reproduction code review found four verification gaps: unverified principal-table intervals/tails/workflows, missing immutable input/run bindings, absent supplement-design comparison, and no independent supplement report. A tiny adversarial fixture reproduces them. Preserve audit v1 as history, fix outside frozen producers, add corruption regression tests, and require a new audit receipt before promoting the result.

## Post-review closure (03:00 UTC onward)

The fourth, unexposed review requests three concrete additions. They do not change
the primary panel, width, score thresholds or five/six-point investment rules.

- [x] Compiled conventional-support attribution control: same validation/radix/global
  ties, direct ramps, all 73 cases, six balanced orders. Frozen before own timings.
  Result: control/released 0.910/0.960/0.978; control/stream 1.357/1.201/1.166.
  This falsifies an isolated nearest-geometry runtime advantage at width 30.
- [x] Run a pinned public nine-metric consumer with both exact ROC and PR backends.
  Select the largest primary recording by length, eight profiles, ABBA order;
  retain total-time and VUS-time traces, including small or negative total gains.
- [x] Archive an inspectable Mac/Linux pair for the diagnosed SMAP SVM difference,
  including standardized inputs, support vectors, coefficients and backend metadata.
- [x] Revise manuscript and all score decisions using these results, then ask the
  existing independent reviewers to reassess without reading each other's scores.

Final closure of this fixed-evidence phase: three unexposed independent reviewers
read the same 11-page PDF and returned Accept 7 / Revise 5 / Reject 5. Six evidence
items are addressed and the frozen project-5 definition is met. Project-6 and
strong PVLDB merit are not established. Three substantive post-review remedies
were completed, including adverse findings: compiled control wins all73 scalar
cases, public nine-metric total gain is 1.031x, and host fitting diagnostics explain
the observed score difference without claiming its precise backend cause.
The submission package is prepared, not submitted. The separate range-sweep
plan pursues a new falsifiable generalization; it does not erase these decisions
or complete the historical broader SOTA/external-acceptance goal.
