# Certified VUS research implementation plan

**Goal:** Test a distinct, mathematically justified reduction along the buffer
width axis and audit the newly discovered fast-VUS baseline before making
stronger research claims.

**Architecture:** Retain the released exact evaluator and raw records. Add a
merge-aware width evaluator with endpoint bounds, independent audit scripts,
and append-only experiment outputs. The original benchmark is not overwritten.

**Tech stack:** Python, NumPy, Numba, pytest, LaTeX, GitHub Actions.

**Authorization:** The user requested continued execution through research,
implementation, experiments, validation, and a concrete result. Routine choices
below are agent decisions; no additional design approval is requested.

## Constraints and review focus

- Preserve the pinned dynamic-label VUS semantics and equal-score ties.
- A real-arithmetic theorem is not a directed-rounding numerical certificate.
- Split width intervals at every expanded-segment merge; global monotonicity
  must not be assumed.
- PR precision can oscillate. Bounds must permit all recall distributions
  between the endpoint curves, not assume monotone PR area.
- Benchmark whole calls, include preprocessing, exclude and record JIT warmup,
  use one thread and paired randomized method order.
- Record negative results, unknown algorithm overlap, source hashes, and every
  selected case. No conference acceptance or unqualified SOTA claims.

## Tasks

- [x] Prior-art audit: current official VUS, dtaianomaly, Sylligardos, and the
  independently discovered `tomlouisklein/fast-VUS`; pin actual code and test
  semantics before timing.
- [x] Width theorem and implementation: add `src/sparse_vus/certified.py`;
  expose `certified_vus(y, scores, max_buffer, atol=1e-3)` and
  `PreparedEvaluator.evaluate(width)`.
- [x] Independent correctness: tiny exhaustive instances, random continuous
  and tied scores, zero/one widths, merging/adjacent intervals, exact fallback,
  bound containment, requested half-width, and invalid inputs.
- [x] Score-data sensitivity: documented context-64 padding correction and
  common valid suffix; all 350 series, all three models, both original widths.
- [x] Fresh comparison: all 350 series against actual fast-VUS plus strong
  dense baselines; a fixed 42-series cross-family width-certificate experiment.
- [x] Independent x86 Linux experiment through the public repository CI,
  retaining environment and raw paired timings.
- [x] Review mathematical claims and experiment records, revise manuscript
  and public artifacts to match only supported conclusions, render and inspect.

## Acceptance and decision rules

Every selected exact evaluation must agree within `1e-11`. Certificate tests
must contain the independently computed exact result within the separately
reported float64 audit tolerance, and terminate with requested interval width.
Scientific novelty and submission readiness require a separate assessment;
passing tests or releasing code does not satisfy either by itself.
