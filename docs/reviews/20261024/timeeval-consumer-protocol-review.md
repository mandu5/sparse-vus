# Native TimeEval consumer protocol: implementation self-review

Prepared during the frozen run, without reading its numerical outcomes. This is an implementation/protocol self-review, not an independent scientific review or an output audit.

## Bound consumer and workload

- Upstream: TimeEval `7c3622757b1a3afa9a84cbc97ce132d9e379f715`, original `scripts/recalculate_metrics.py` and `MetricComputor` implementation.
- Actual script defaults: `ROC_AUC`, `PR_AUC`, `RANGE_PR_AUC`; the first two metric implementations and the outer consumer remain unchanged. The range adapter accepts only zero existence weights, flat positional bias and cardinality one.
- Inputs: 26 selected real recordings, 52 newly generated public FFT/COPOD score vectors, packaged in the native input layout. They are not claimed to be archived historical TimeEval runs. The generation receipt and independent native read-back receipt are hash-bound.
- Batches: all 52 rows combined, MSL 4 rows, Stock 24 rows and WSD 24 rows. All input result statuses are `Status.OK`; the template contains no previous output metric columns.
- Global frozen protocol reported by the parent: SHA256 `aefba85eea77cc3e50ce33e9f9f640881f38909e82cb342820e366ffa741f6bb`, source/protocol commit `c99ce6b`. Timed execution started 2026-10-24 08:07:39 UTC. No numerical result is asserted here.

## Comparisons and boundary

Two separate consumer contracts are evaluated: the original nominal `max_samples=50`, and an explicitly configured `max_samples=inf` contract that evaluates every observed nonminimum score. Within each contract, public prts, compiled raster and compiled bucket implementations compute the same three metric outputs. There are no cross-contract speed ratios or threshold-accuracy claims.

The source sampler is not a hard 50-query cap. Frozen query plans contain 2,776 queries in total for the nominal-50 combined workload and 71,749 for all-observed. Per-profile counts range from 2 to 90 and 2 to 5,819, respectively. These counts were derived from scores and source sampling alone before consumer timing.

The interval includes the native constructor and complete forced recalculation: dataset/results/score/optional-metric reads, all three metrics, and final results.csv serialization and close. One deadline-arming call is included; signal-handler setup/cleanup is excluded. Imports, tiny JIT warmup, source/input audits, metric-object creation, fresh trial-template copies/filtering, and later output comparisons are excluded. The workflow does not claim cold-disk, fsync or detector-training performance.

Every contract/batch uses all six permutations of the three methods, with one numeric thread and `n_jobs=1`. The combined workflow is the primary complete-application comparison. Family batches retain the same consumer and metric list. Their row counts and score distributions differ; family results are not treated as interchangeable independent recordings.

## Failure and uncertainty handling

A `WorkflowTimeout` derives from `BaseException` so the upstream per-metric `except Exception` cannot silently consume it. After the first 600-second censor for a method/contract/batch, the remaining attempts for that key are retained as `notrun_due_to_prespecified_censor`; other keys continue. A Python signal can be delivered after control returns from a native extension, so the recorded interrupted elapsed time is preserved rather than forced to exactly 600 seconds.

Each completed result must retain every expected row in order and all three finite metric outputs. Scalar differences must be at most `1e-10` with zero relative tolerance against the available reference. Public parity is separately marked unavailable if no public attempt completes. Agreement between two compiled methods does not substitute for a missing public reference.

Only six complete paired orders receive a geometric speed ratio and approximate paired-order bootstrap interval. Those intervals describe observed execution/order variation for the fixed input workload; they are not recording-population or deployment confidence intervals. A single censored baseline can provide only the explicitly recorded same-round lower bound, and skipped attempts do not become measurements.

## Verification before freezing and remaining audit

The adapter/runner targeted suite passed 39 tests before freezing. It includes native tiny whole-consumer execution for both contracts and all methods, threshold ties/endpoints/sampling, wrapper exception behavior, deadline escape, censor summaries, receipt-score bindings, and detection of added optional metric caches. The manifest was regenerated and its source, input, package and receipt bindings were verified without computing real metric outcomes.

No blocking implementation defect was identified in this self-review. This statement is limited to the reviewed source and tiny checks. After execution, a separate read-only output audit should verify 144 planned records, all six orders, every censor/skip dependency, artifact coverage, all 52/4/24/24 row identities and three outputs, cross-method scalar parity where available, and reconstructed per-contract ratios/intervals. Any failure must preserve this run and use a newly versioned correction rather than editing frozen sources or replacing selected inputs.
