# Exact VUS Saturation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove, implement and evaluate exact active-prefix VUS, then strengthen
the manuscript using reproducible evidence toward the unchanged research goal.

**Architecture:** A new optional compiled module combines complete global score
ties, activation-scheduled support traversal and monotone component merging.
Independent dense references and experimental ablations check both semantics and
the reason for any speed advantage; current v0.3 sources remain unchanged.

**Tech Stack:** Python 3.12, NumPy, Numba, pytest, existing source/data receipts.

**Spec:** `docs/superpowers/specs/2026-10-21-saturation-design.md`

## Global Constraints

- Numerical parity tolerance 1e-11; whole complete float64 numerical ties.
- Preserve original dynamic VUS, every integer width 0..L, summed/clipped ramps,
  expanded-component existence reward, terminal ROC and right-step PR.
- No false unseen-corpus, independent-laboratory, SOTA or acceptance statement.
- Do not alter frozen v0.3 sources/assets; record all negative findings.
- Full-call timing includes validation and preparation; one compute thread.

## Review Focus

- Saturation inside an incomplete tie must never terminate the computation.
- Adjacent expanded intervals remain separate until they overlap at a position.
- New activations and DSU unions at one radius must produce correct components.
- Signed zeros, integer float64 conversion ties and extreme finite scores use
  the same input semantics as the current public API.
- Poor/adversarial scores may require the whole active support; full-scan fallback
  must preserve exact outputs and expose any runtime regression.

### Task 1: theorem and independent behavioral oracle

Files: `paper/saturation_method.tex`, `tests/test_saturation.py`.

- [x] Derive permanent recall saturation, ROC telescoping and complete-tie rule;
  independently challenge derivation and activation/component data structures.
- [x] Write tests for APIs `sparse_pr_saturation_jit(y,scores,L)->float` and
  `sparse_vus_saturation_jit(y,scores,L)->tuple[float,float]`; first observe missing
  implementation failure, then retain direct-ramp numerical reference checks.
- [x] Exhaustively cover small binary labels/tied scores and all relevant widths;
  add explicit signed-zero, extreme-finite and merged-component regressions.

### Task 2: exact active-prefix kernel

Files: `src/sparse_vus/saturation.py`, `tests/test_saturation.py`.

- [x] Implement activation preprocessing, reverse deletion/insertion, nearest
  original interval mapping and DSU merge schedule with precise complexity.
- [x] Implement full-tie streaming, persistent-saturation stop and ROC tail.
  Add PR-only route plus internal diagnostic/stop-disabled ablation.
- [x] Run new tests and complete package suite; fix any semantic discrepancy
  before timing. Independent reviewer checks complexity and hidden full scans.

### Task 3: falsifiable development experiment

Files: `experiments/benchmark_saturation.py`, `artifacts/saturation/`.

- [x] Freeze 42-series development input/source hashes, widths30/100/300,
  three released scores, seeded randomized methods and repetitions before run.
- [x] Compare whole-call saturation PR, stop-disabled control, v0.3 radix PR,
  matched dense radix PR, and pinned fast-VUS PR. Record per-width visited work
  separately, outside timing; warm JIT and snapshot environment.
- [x] Report parity, every ratio/loss, geometric and aggregate speedup, work
  reductions and overhead. Do not tune on later confirmation results.

### Task 4: confirmation and scholarly integration

- [x] Verify raw labels/scores for a genuinely new corpus or explicitly state
  that any reused corpus is only a prospectively held-out policy test.
- [x] Freeze final algorithm/protocol and run complete confirmation, retaining
  failures and worst cases. Reconstruct from raw records independently.
- [x] Integrate supported theorem/measurement findings into the manuscript;
  obtain adversarial review and resolve substantive objections.
- [ ] Pursue eligible external submission using actual human/account facts;
  verify the real receipt/decision. Keep original goal until its evidence exists.

## Execution ledger

- Resumed by explicit user instruction on 2026-10-21. Isolated worktree created
  from 7f869f4; previous artifact retained. Three fresh agents independently
  investigate theory, new data and scientific weaknesses. Targeted baseline
  tests started before production changes.
- Ruling: the user explicitly authorized autonomous continued implementation
  and experiments; no additional plan-approval round is required.
- Implemented active-prefix kernel without changing v0.3 evaluators. Independent
  dense-oracle audit covers 8,606 cases / 51,636 public calls. Final complete
  suite on 21 October 2026: 3,279 passed in 73.52 seconds.
- Derived a complete-tie mass/coverage bound, uniform single-interval bound,
  and a deterministic score-query lower bound matching the singleton upper
  bound when L <= n. Explicit counterexamples retain ties and coverage limits.
- Completed 378 Mac development cases and 144 new-source external cases on
  each of Mac and Linux. All primary runtime criteria failed; all numerical
  parity checks passed. Secondary L=300 gains are reported with every loss.
- Linux hosted reproduction run 39546569039 completed at source595fb3b;
  53 downloaded artifact hashes verified. Raw/label hashes match Mac;
  11/48 score arrays match exactly and 37 differ after regenerated scoring.
- Completed separately frozen paired-source supplement (48 Benchopt cases;
  DTAI 10/12 completed, 2 censored) and 16 structural cases. Count predictions
  and completed-output parity pass; no primary criterion was rewritten.
- Built and visually inspected the nine-page focused active-prefix manuscript
  with unchanged official template bytes. Independent code/manuscript review
  found no remaining correctness blocker; factual corrections were integrated.
  Added a reusable cache-free supplement auditor with 16 integrity tests and
  installed-wheel verification of all four radix/active-prefix APIs. Requested actual human
  contribution/revision and account/COI facts against this concrete PDF.
- Opened the real PVLDB portal in local Chrome; it redirects to CMT login.
  The submission packet contains actual manuscript/abstract/relevance fields;
  author declarations and account-dependent facts are explicitly pending.
