# Independent tie-run protocol review — 23 October 2026

Pre-timing static review of `experiments/benchmark_tie_runs.py` and
`docs/tie_run_protocol_20261023.md`, including their direct data-loader,
hash-helper, environment-capture, and Klein-adapter dependencies. No timing,
metric evaluation, corpus-wide computation, or heavy test was run by this
reviewer for this task. The driver was not edited.

Disposition: **one report-integrity issue to fix before freezing; one wording
correction. No additional blocking timing-unit or selection issue found.**
The coordinator acknowledged the report issue and is implementing a receipt
fixture and the correction. This report describes the initial reviewed driver;
it does not certify those subsequent edits until their checks pass.

## Findings requiring correction

1. **Important — standalone report reconstruction ignores frozen source and
   acceptance criteria.** In the initial driver, `report()` checks protocol,
   input-manifest, and measurement receipts, but never calls `contract()` to
   verify the frozen source map. Its final status uses global `ATOL` instead
   of `p['parity_atol']`; summary comparator enumeration uses global `METHODS`
   instead of `p['methods']`. Changing the current driver can therefore change
   reconstruction criteria without detection, despite an unchanged protocol
   receipt. The initial `run()` does verify sources before and after timing,
   so this is specifically a reconstruction/integrity gap, not evidence that
   the current measurements used the wrong methods or tolerance. Fix report
   reconstruction to verify the frozen contract and use protocol fields.
   Explicitly assert or consume the frozen seed, repetitions, and method list
   in `run()` as well. A report that requires local private source caches
   should be described as such; a separate public recorded-evidence audit
   must state any source/input identity it cannot revalidate.

2. **Minor — freeze records a result-shaped statement before outcomes.** The
   initial protocol's `decision` field begins “All numerical parity and work
   assertions pass” although `freeze()` never evaluates them. Express this
   as an acceptance criterion, such as “Accept numerical/work checks only if
   every prespecified assertion passes.” The prose protocol correctly labels
   timings descriptive and does not replace an earlier primary criterion.

## Verified by source inspection

- **Candidate freeze:** the source map binds every Python module in
  `src/sparse_vus`, the benchmark driver, imported benchmark/helper modules,
  adapter, pinned Klein source, and prose protocol. The freeze constructs
  inputs before timing and hashes both each NPZ and its typed arrays.
  `run()` checks an externally supplied protocol hash and bound sources and
  original manifests before timing and after all measured cases. Output
  creation is exclusive; a directory with run receipts cannot be replayed.
- **Structural coverage:** the explicit nested loops generate all twenty
  combinations of widths 32/128/512/2048 and the five stated families.
  Singleton and eight-positive label layouts match the prose. Alternating
  classes remain in the matrix as the fragmented-run negative control.
- **Prior-input selection and identity:** the driver iterates every row of
  both original Mac manifests and excludes only rows whose loaded labels
  have a component count other than one. It does not inspect historical
  timings, correctness outcomes, or candidate performance during selection.
  Development `Corpus.load()` checks the label member bytes against the old
  manifest and score member bytes against the download receipt; the new
  driver additionally checks that receipt's score hash against the old
  manifest. `ExternalCorpus.load()` checks the original NPZ digest, both
  typed-array hashes, sequence length, and positive count. Thus selected
  scores are copied unchanged and old source identity is not inferred merely
  from matching case names. The new typed-array hashes bind the copies used
  at timing. Both original manifests are themselves hash-bound.
- **Reuse disclosure:** the prose and JSON protocol explicitly call both real
  datasets reused evaluation. The report also rejects interpretation as
  unseen confirmation or a new primary runtime success. No new holdout is
  claimed by the label-only subset rule.
- **Storage scope:** only generated structural arrays are placed under the
  output's public `inputs` directory. Real arrays are copied under the
  repository's `.cache` path; no source real dataset is copied into public
  artifacts by this driver. The local `.cache` is a symlink, so
  `git check-ignore` on a descendant is not a valid ignore-status check.
  Publication should retain the existing cache boundary.
- **Matched task units:** all four timed functions return only exhaustive PR.
  The Klein wrapper passes `len(y)` thresholds; its source validates
  equal-length label/score inputs and enumerates all rank thresholds at that
  value, retaining ties. The pinned adapter verifies and executes the
  recorded upstream source bytes without replacing its algorithm.
- **Full-call timing:** validation, radix/preparation work, and the candidate's
  square-root prefix construction occur inside each timed public function.
  No prepared arrays are supplied across calls. NPZ loading, hash checking,
  one per-case warm call per method, and diagnostic profiles occur outside
  the timer. The Klein import is warmed before measurements. The four
  methods receive the same loaded arrays and width for each repetition.
- **Order and environment:** each of five repetitions shuffles all four
  method identifiers using seed 202610234 in one serial loop. The recorded
  order can be reconstructed from the protocol. Environment variables and
  `threadpool_limits(1)` constrain compute threads, and environment capture
  records NumPy/Numba versions, thread pools, CPU, and process snapshots.
  This is a local-host descriptive experiment, not an isolated-host or
  population timing inference. Case order is fixed; only method order is
  randomized, consistently with the prose.
- **Parity and work:** every measured scalar, including repeats of the
  reference itself, is compared with the first radix value. Work diagnostics
  are collected outside timing. The report checks the `3P0` event bound and
  all-tied singleton's one-run count against the position scan's
  `1+2*floor(w/2)` counts. Dense-geometry correctness is explicitly separate
  test evidence, not an assertion that this timing run uses a dense oracle.
- **Receipts and negative results:** completed case records are appended and
  flushed, and only a fully finished loop receives a COMPLETE measurement
  receipt. A killed in-progress case can lose its unflushed local results,
  but previously written records remain and no full-run receipt is issued.
  COMPLETE denotes execution coverage; parity/work status is separate.
  Every case is retained in `per_case`; ratios use comparator median time
  divided by candidate median time, so a value below one is correctly
  counted as a candidate loss. Aggregation separates structural families
  and reused-data phases by width. Aggregate ratios sum the per-case median
  times; they are not pooled-repetition ratios or confidence intervals.

## Scope limits

This review did not materialize a new frozen corpus, independently count the
selected K=1 subset, exercise interruption behavior, or validate a completed
measurement receipt. Those checks belong to the subsequent freeze/run/audit.
The initial implementation and test hashes remain recorded in the separate
code review; the coordinator added the recommended high-limb regression while
leaving the candidate implementation unchanged. The coordinator reported
3,318 full-suite passes before that regression and 24 targeted passes after
it; those new test counts were not independently rerun during this protocol
review.

## Pre-freeze resolution

The coordinator subsequently reported both receipt regressions reproduced
(RED) and corrected (GREEN), with 26 targeted tests passing. `report()` now
checks the actual frozen source contract and reads tolerance/methods from the
protocol; `run()` reads the protocol seed and repetition count. The freeze
`decision` text is now an acceptance criterion. On that reported evidence,
the issues above are **fixed before freeze**, with no outstanding blocker
from this review. These corrections were not independently retested by this
reviewer; the coordinator owns their test evidence. The reviewer stopped
compute work before the benchmark window.
