# Sampling consequences and certified evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Establish whether coarse threshold integration can materially distort VUS model comparisons, with rigorous witnesses, independently validated error bounds, and a new published detector panel.

**Architecture:** Keep the existing exact evaluators and frozen evidence unchanged. Add a matched compiled sampled evaluator using the same radix preparation primitives, and a separate integer-arithmetic enclosure of the real-valued target. Evaluate the twelve published MSAD score configurations on a metadata-selected, identity-filtered 128-series panel, with a protocol frozen before outcome computation.

**Tech Stack:** Python 3.11+, NumPy, optional Numba, exact Python integers; existing pytest and manuscript tooling.

**Spec:** `docs/sampling_theory_challenge_20261023.md`, `docs/sampling_unseen_workload_design_20261023.md`, and `docs/msad_score_corpus_design_20261023.md`.

## Global Constraints

- Preserve the dynamic positive mass, sum-and-clip square-root ramps, overlap-only range merging, complete numerical ties, and every width from 0 through L.
- Match the pinned upstream `np.linspace(0,n-1,H).astype(int)` sample rule, including repeated thresholds and signed-zero ties.
- Separate real-arithmetic certification from approximate binary64 evaluation. An epsilon-tolerant check is not a certificate.
- Never edit previously frozen protocols, results, or exact kernels to improve new results.
- Keep raw source data and scores in ignored cache; publish provenance, selection decisions, numerical results, code and analyses.
- No outcome-based data selection. Report every exclusion, timeout, regression, and failed scientific gate.
- User has authorized autonomous implementation and review; no further plan-approval pause.

## Review Focus

- All-score ties and repeated sampled ranks must preserve complete-threshold integrals.
- Boundary/overlapping/adjacent ranges must retain the pinned existence semantics.
- Exact integer bounds must include zero denominators, saturated recall, integer overflow and outward conversion.
- Strong stored-score quantization must be measured as source data, not silently repaired.
- Correlated channels/models/widths must not be treated as independent statistical replicates.

### Task 1: Matched sampled PR evaluator

**Files:** create `src/sparse_vus/sampling.py`; create `tests/test_sampling.py`.

**Interfaces:** `sampled_pr_radix_jit(labels, scores, max_buffer, thresholds=250) -> float`; private prepared endpoint states consumed by the certificate.

- [x] Write parity tests against independent dense sampled curves and unchanged pinned upstream, including H>n, complete ties, signed zeros, overlap, boundary labels, width zero, invalid budgets, and constructed overestimation witnesses.
- [x] Run the new tests and verify the missing-module failure.
- [x] Implement radix-ranked complete sampled groups and a compiled width loop; count all original positions and buffer mass separately.
- [x] Run the new tests and existing exact-evaluator regressions.

### Task 2: Integer enclosure

**Files:** create `src/sparse_vus/sampling_bounds.py`; create `tests/test_sampling_bounds.py`.

**Interfaces:** `certified_sampled_pr(labels, scores, max_buffer, thresholds=250) -> certificate`, with exact dyadic integer endpoints and scale, plus outward float endpoints for display.

- [x] Independently review the mass-envelope theorem and derive conservative formulas for uncertain endpoint mass/recall.
- [x] Write tests against an independent high-precision dense oracle, fixed-point root identities, saturation/zero-mass blocks and complete-tie blocks.
- [x] Verify tests fail, then implement integer square-root weight brackets and exact floor/ceiling arithmetic. Declare and validate any finite-size limits.
- [x] Verify containment without an added epsilon and verify the full-threshold case contracts to only arithmetic enclosure width.
- [x] Measure cost and certificate usefulness separately; do not assume a useful certificate or speedup.

### Task 3: Frozen empirical protocol and new panel

**Files:** create `experiments/msad_sampling_study.py`; create `tests/test_msad_sampling_study.py`; new `artifacts/msad-sampling-20261023/` only.

**Interfaces:** consume the acquisition manifest and all twelve original stored score arrays; produce append-only per-case numerical/timing records and deterministic report reconstruction.

- [x] Freeze widths 30 (primary), 100 and 300; H=250 primary and 32/64/128/500/1000 secondary; exact target and both upstream/matched sampled controls.
- [x] Freeze tie tolerance 1e-10, regret threshold 0.01, source-family clustered summaries, outcome-independent timing subset, five paired repetitions and timeout policy before the first corpus metric.
- [x] Test tied winner sets, best/worst tied-winner regret, pair reversals, hash validation and report reconstruction using fixtures.
- [x] Run all numerical cases, validate upstream parity and full-threshold controls, then run serial randomized timings on the fixed subset.
- [x] Report pooled/equal-family/per-family outcomes and correlation limitations; record weak or absent practical effects unchanged.

### Task 4: Adversarial assessment and manuscript

**Files:** new review/evidence reports; modify manuscript only after all scientific results are known.

- [x] Obtain independent adversarial review of proofs, implementation and significance, without requesting a favorable rating.
- [x] Repair concrete defects and rerun only affected checks.
- [x] Integrate defensible results with full counterevidence and compare current primary-source prior art/venue criteria.
- [ ] Render and inspect the final manuscript; verify artifact hashes, tests and public reproducibility before any completion claim.

## Scientific promotion rule

The theory claim requires a valid proof and independent executed witnesses. A practically consequential default-sampling finding requires nontrivial exact regret (at least 0.01) on at least 5% of the fixed panel and in at least three source families, at primary L=30/H=250. These are declared study decision thresholds, not universal utility cutoffs or a venue acceptance rule. Failing them is retained as a negative result. Cost claims must name the matched output, width, hardware, panel and control; a new compiled approximation is included to prevent attributing Python overhead to exactness. An internal favorable review is not external acceptance.

## Executed evidence update

The matched evaluator, integer certificates, frozen128-series study and adversarial assessments are complete. Primary H250/L30 has eight rigorous regret>=0.01 cases across four families; all128 full-grid winners are certified. Numerical/control/main-timing calls46,584 and certificate-cost calls5,400 complete; the full local suite passes3,517 tests. The20 physical-source overlaps and4/108 nonmatching sensitivity result remain visible. Final public snapshot/CI and rendered-PDF checks are the remaining packaging gate. See `docs/certified_sampling_reproduction_20261023.md`; no publication outcome is inferred from these checks.
