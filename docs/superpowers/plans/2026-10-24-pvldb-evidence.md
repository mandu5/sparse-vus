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
- [ ] Compute per-collection paired confidence intervals, selection agreement, failure tails and resource costs.
- [ ] Independently reconstruct results and provide one reproduction command.

## Task 4: Scientific decision and review

- [ ] Update all six gates with evidence; never count a prepared artifact as a result.
- [ ] Obtain three independent reviews using verified venue criteria and public-review calibration.
- [ ] For each remaining scientific failure, try three materially different remedies before changing the claim or target.
- [ ] Select the supported research-score band and venue; only supported results enter the manuscript.
- [ ] Prepare the final submission path if gates pass; preserve actual submission/acceptance receipts separately.

## Execution ledger

2026-10-24: User explicitly renewed sparse-vus research; previous stop recommendation is superseded. Existing linked worktree is clean at baseline. New branch `research/pvldb-20261024`. Existing goal replacement rejected because an unfinished goal exists; no false completion/resume recorded. Standard `python3` lacks Numba; use existing `/opt/anaconda3/bin/python` (NumPy 1.26.4, Numba 0.59.1) consistently and record versions.

2026-10-24, primary completion: 73 complete cases, eight unrounded score procedures, two widths and complete collection workflows passed their recorded numerical comparisons. The supplementary Benchopt/matched-pair and sampled accuracy-cost study retains a separate freeze. Source files used in timing are now immutable.

Independent reviews identified nine shared-label SMD blocks (18 cases also share a development label sequence), a public-call `Mn` memory temporary, and missing strongest-baseline/current-paper integration. These are explicit revision conditions. The initial label-block sensitivity is positive, but does not establish physical-recording independence.

Reproduction code review found four verification gaps: unverified principal-table intervals/tails/workflows, missing immutable input/run bindings, absent supplement-design comparison, and no independent supplement report. A tiny adversarial fixture reproduces them. Preserve audit v1 as history, fix outside frozen producers, add corruption regression tests, and require a new audit receipt before promoting the result.
