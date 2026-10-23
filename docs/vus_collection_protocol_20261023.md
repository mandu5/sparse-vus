# Stored-score collection workflow protocol — 2026-10-23

Status: protocol designed before this collection experiment's timings. The
`freeze` command materializes inputs and writes a machine-readable protocol;
it never calls a metric. Execution requires review of the frozen digest and
an explicit CPU-clearance statement. Prior per-series runtime results are
already known and motivated this experiment; this is not a claim of blind
method development or retrospective preregistration of those results.

## Question and scope

Does released SparseVUS reduce the elapsed time of a concrete stored-score
collection operation: load every series from disk, evaluate all three stored
models, select the best-model set for each series, and write the decisions as
JSON? The unit of timing is the entire collection operation, including file
reads and serialization. The operation supports repeated model comparison on
a locally stored evaluation collection; it is implemented here as an operator
workflow, not presented as evidence of an existing production deployment.

This tests a data-processing use of the full released PR algorithm. It does
not establish a new database system, new detector quality, user adoption,
multi-user service behavior, or new-domain generalization. It excludes
detector training/inference, network transfer, first-use compilation, and
cold-cache storage performance. The new active-prefix and tie-run candidates
are outside this experiment. Results must retain these limits when integrated
into a manuscript.

## Immutable population and array preparation

- Use exactly the 308-series complement of the original metadata-selected
  42-series development set, covering the previously studied 17 families.
  Every series appears once per pass, in sorted series order. Use all three
  original score vectors: `TimeMoE-200M_64`, `bolt_base_64`, and
  `timesfm-1.0-200m_64`, in sorted model order.
- Set `max_buffer=30`, evaluating widths 0 through 30 inclusively. No series
  sampling, artificial duplication, workload extrapolation, or extra widths.
- Reconcile metadata with the immutable v0.1 input chain through
  `released_metadata`, and exactly match the L=30 projection of
  `artifacts/pr-engine/mac-holdout/inputs.json` (SHA-256
  `783d6ec769682c8b0735fe4f4a17591ab4de042b2f2907e8ffbecbcc74690cd6`).
  The prior protocol hash is
  `5417a38ec43cc4471e17a0ca7d6af0b11ef448689042a1c5dec4fa8ef2dffb07`.
- Read the existing label and score ZIP archives. Check the pinned source-file
  locks, ZIP member CRCs, all 308 original label-member SHA-256 hashes, and all
  924 original score-member SHA-256 hashes. Check label length, binary classes
  and positive count, and score length and finiteness. Record observed whole
  score-archive hashes as transport identities; original score identity is
  established by the older immutable member hashes, not a newly observed hash.
- Decode CSV labels and cast to `int8`, exactly as existing `Corpus.load`
  does. Verify value equality before and after conversion and record both
  decoded and stored label identities. Preserve every score array's dtype,
  shape and exact bits, including original documented leading-zero padding;
  introduce no score normalization, padding, reordering or recalculation.
- Write one uncompressed NPZ per series under ignored `.cache`, with keys
  `labels`, `score_0`, `score_1`, and `score_2`. Verify a read-back by dtype,
  shape, and SHA-256 of C-order bytes, then freeze each NPZ file hash and size.
  Raw arrays and ZIP archives are not redistributed. Public manifests contain
  identifiers, hashes, shapes and sizes only.

The frozen protocol binds the driver, protocol text, metadata verifier,
complete transitive local metric modules, the unchanged Klein adapter and
upstream source/license. All runtime source files that appeared in the older
PR-engine protocol must still match that older protocol. The metric engines
are released implementations, not newly optimized replacements.

## Methods and measured workflow

| ID | Exact operation for each stored model |
| --- | --- |
| `radix_pr` | Released `sparse_pr_radix_jit(labels, scores, 30)` |
| `dense_pr_nearest_radix` | Matched `dense_pr_nearest_radix_jit(labels, scores, 30)` |
| `klein_pr` | Unchanged pinned upstream `vus_pr`, via `fast_vus_pr(..., max_samples=len(scores))` |

Every method returns full PR only and includes public input validation and
preparation. All score thresholds are exhaustive; Klein's threshold parameter
equals the series length. No cached model metric, cross-pass array cache,
cross-model preparation reuse, racing, or early winner termination is used.

For each method and trial, the whole monotonic clock starts before the first
NPZ is opened. The driver then performs the following sequence for every
series: open the NPZ and materialize all four arrays; close it; make the three
full metric calls; select all models within `tie_atol=1e-10` of the largest PR
value; append that series' numeric values and selected set to the result.
Arrays are discarded before the next series. After the last selection, write
one compact JSON file and close it. Stop the whole clock after that close.
The output write uses ordinary buffered file I/O without `fsync`; this measures
completion through the OS write path, not durable storage latency.

Each pass has 308 NPZ opens/loads, 1,232 materialized arrays, 924 metric calls,
308 selections, one JSON serialization and one result-file write. Record
nanosecond clocks for reading, metric evaluation, selection/result construction,
and serialization/write, alongside the whole clock and its residual overhead.
Do not use the sum of phases as the runtime outcome. Hashing result files,
writing measurement receipts and all cross-method correctness comparisons are
outside the measured operation. Checking finite metric outputs and constructing
the selected set are part of the measured selection operator.

## Repetitions and environment

Perform three complete collection replications. In each replication execute
all three methods serially, in a seeded random order generated before outcomes
by Python `random.Random(2026102307)`. Freeze the resulting orders in JSON. Each
method/trial reopens all 308 files, with no retained inputs or computed values
from a previous pass. Retain all nine whole-collection times.

Use one process and one numerical worker thread. Set BLAS/OpenMP/Numba thread
environment variables before numerical imports, explicitly set Numba to one
thread and use `threadpool_limits(1)`. Record CPU name, OS, architecture,
Python, NumPy, Numba, discovered thread pools, actual thread counts and the
operator's CPU-clearance statement. Do not run other agent tests, builds or
benchmarks concurrently. Ordinary desktop activity is a limitation if present;
one numerical thread is not a claim of CPU affinity or machine isolation.

Warm imports and JIT outside timing with a 32-position synthetic example for
every label/score dtype signature in the frozen inputs. This does not evaluate
any real collection series before its measured pass. Immediately before every
pass, read and SHA-256-check every NPZ file outside the timer, making the
filesystem/page cache explicitly warm; the measured pass still reopens and
decodes every NPZ. No OS-cache eviction is attempted. This is a warm-filesystem
workflow, not physical-disk throughput or a cold-start benchmark. Source and
input hashes are checked again after all timings before `COMPLETE` is written.

## Decision and retained evidence

The experiment passes only if all of the following hold:

1. Every selected-model set agrees across all nine passes, for every series.
2. For each series/model, the maximum value minus the minimum value across
   all methods and repetitions is at most `1e-11`. This is the maximum
   pairwise absolute difference and checks more than comparison with a single
   reference output.
3. The median measured whole-collection time of `radix_pr` is strictly smaller
   than both the nearest-dense-radix PR median and the Klein PR median.

Report all times and phase counts, the three medians and their descriptive
ratios, every PR output and selected set, every signed difference from trial-0
radix, per-series/model pairwise spans, and every selected-set agreement flag.
Three replications do not support a confidence interval or significance claim.
Failure of either correctness condition or either runtime comparison remains a
failure; do not replace this criterion after looking at outcomes. No external
or older per-case timings enter the decision.

The public study directory contains `inputs.json`, `protocol.json`, and
`freeze_receipt.json`; the run adds `environment.json`, nine scalar-result JSON
files, `measurements.jsonl`, and `completion.json` under `run/`. A separate
report reconstructs numeric comparisons and decisions from hash-bound outputs.
The report rejects missing, duplicated or reordered passes, changed source or
inputs, wrong file hashes, inconsistent stage/whole clocks, wrong counts,
nonfinite metric values, or stored selections that disagree with stored scores.
No output directory/file may be overwritten. An interrupted or invalid run is
retained without a completion receipt; retry requires a new frozen study path
and must be disclosed, rather than silently replacing partial observations.

## Commands and compute gate

From the repository root, prepare without metric calls:

```sh
python experiments/benchmark_vus_collection.py freeze \
  artifacts/collection-workflow/mac-20261023 \
  --cache .cache/vus-collection/mac-20261023
```

After independent driver/protocol review and explicit CPU clearance, use the
exact digest emitted by freeze:

```sh
python experiments/benchmark_vus_collection.py run \
  artifacts/collection-workflow/mac-20261023 \
  --protocol-sha256 FROZEN_PROTOCOL_SHA256 \
  --cpu-clearance 'ACTUAL_CLEARANCE_AND_MACHINE_ACTIVITY_STATEMENT'
python experiments/benchmark_vus_collection.py report \
  artifacts/collection-workflow/mac-20261023 \
  --protocol-sha256 FROZEN_PROTOCOL_SHA256 \
  --report artifacts/collection-workflow/mac-20261023/report.json
```

Before execution, give the reviewing operator the driver hash, manifest hash,
protocol hash, exact NPZ byte size, observed dtype signatures and the intended
run command. Historical same-machine L=30 metric-only summed case medians were
approximately 3.09 s (radix), 10.20 s (dense), and 60.19 s (Klein) per collection;
these support only an approximate several-minute scheduling estimate. They
are not predictions, substituted measurements, or new collection results.
