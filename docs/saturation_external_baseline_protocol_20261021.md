# Separate paired-output external-baseline supplement — 21 October 2026

This is a new, descriptive supplement written **after** the development and
external primary studies were inspected. Both primary `L=30` decisions failed.
Nothing here changes those frozen rules, promotes `L=300` to primary, combines
old timings with new timings, or creates a replacement success criterion.
No supplemental timing was run while authoring this protocol.

## Fixed workload and output

- Use all 48 externally generated score vectors: 12 series, nine source
  families, the same four models, and `L=30` only. Copy input identity fields
  from the completed external primary run; verify NPZ and individual array
  hashes. Existing raw observations and scores remain in ignored caches.
- Compare `sparse_vus_saturation_jit`, released `sparse_vus_radix_jit`, and the
  actual hash-pinned Benchopt `_range_auc_volume(..., thre=n)` implementation.
  All three return **both ROC and PR**. The existing Benchopt AST adapter
  retains the four upstream function bodies unchanged; no new metric clone
  or vendored source is introduced.
- Add the native DTAIAnomaly full-threshold evaluator on exactly the 12
  `isolation_forest` vectors, also at `L=30`, with `max_samples=n`. Its existing
  AST adapter preserves metric method/kernel bodies and obtains both outputs
  from shared curves. Upstream `parallel=True, fastmath=True` remains enabled;
  the process has one Numba thread. This is a numerical parity comparison,
  not a claim of identical floating-point operation ordering.

Source pins are enforced independently of output-directory hashes:

| Comparator | Revision | Source SHA256 |
|---|---|---|
| Benchopt | `2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94` | `298c746c84a28f9296b015bd70eac984d27be5452e3ca42c853de05328c194a8` |
| DTAIAnomaly | `557b435790bebc57307d8e7f22047273ac923f36` | `728045cd8ddf0caa6aab10a9ab66f5f876ee77e5d0ae80dfbce5029eab9ed5b7` |

The adapters fetch sources into ignored caches. Benchopt has no detected
repository license at the pin and its source must not be redistributed.
[Benchopt source](https://github.com/benchopt/benchmark_tsfm/blob/2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94/benchmark_utils/metrics.py),
[DTAIAnomaly source](https://github.com/ML-KULeuven/dtaianomaly/blob/557b435790bebc57307d8e7f22047273ac923f36/dtaianomaly/evaluation/_volume_under_surface_metrics.py).

## Timing and bounded censoring

Use three serial, randomized method-order repetitions per case, with Python
`random.Random(2026102127)`. Each method owns a persistent spawn worker. All
workers set NumPy/BLAS/OpenMP/Numba thread environments before numerical
imports and apply `threadpool_limits(1)`. Only the selected worker computes
during a measurement; the others wait on their pipes.

A small array with the exact generated label/score dtypes warms each worker.
Imports, source loading, compilation, input loading, source/array hash checks,
IPC and result conversion occur outside the internal `perf_counter_ns` timer.
The timer surrounds the complete public metric call, including its validation
and preparation as implemented. The native Benchopt kernel performs less
generic input validation than the candidate API; it receives valid arrays,
and this asymmetry is disclosed rather than padded with extra work.

Warm-up (including process startup/import/compilation) has a separate **120 s**
parent watchdog. Each DTAI timed call has a **30 s** watchdog; every other
method has a **300 s** operational watchdog. Input loading has **120 s**.
These are parent wall-clock deadlines, not recorded evaluator durations.
No timeout value enters a timing median, speed ratio or claimed numerical
result. A warm-up timeout is never described as a timed-call lower bound.

After the first DTAI timed timeout or error on a case, terminate and reap its
worker, retain any earlier completed repetitions, and mark remaining
repetitions on that case `NOT_ATTEMPTED`. Start and warm a fresh worker for the
next prescribed DTAI case. A warm-up/load failure similarly leaves that case
incomplete. Never retry a timed call on the same case until it passes. The
candidate/radix/Benchopt repetitions continue; a failure of one of those
required comparators terminates the supplement with a failure receipt.

Only cases with **three completed, parity-valid repetitions for both compared
methods** receive a ratio of per-case median runtimes. Enumerate incomplete
DTAI cases, completed repeats, timeout stages and errors separately. Keep all
completed outputs available for parity checking even for an incomplete case.
Report the DTAI completion fraction; completed cases are a censored subset,
not evidence for the entire 12-series workload.

## Analysis and receipts

Use absolute tolerance `1e-11`, relative tolerance zero, for both ROC and PR
against the paired candidate result, including agreement between repeated
candidate calls. Report every parity violation. Ratios greater than one mean
the reference took longer. Report per-case ratios and times, median,
geometric mean, aggregate time ratio, all win/loss/tie counts and minimum
ratio. These summaries are descriptive: no new PASS label, confidence-bound
selection rule, or global SOTA interpretation is introduced.

`freeze` requires the completed primary external run's protocol, input,
measurement, completion and report receipts to agree. It records their hashes,
the supplement input hash, all package Python source hashes, both adapters,
both external metric sources, this protocol, the runner, and the Git revision.
No primary file is modified. The supplement's `run` and `report` require the
externally recorded frozen protocol SHA256 and reject source/input drift.

The run writes its start receipt before worker startup, appends/flushes each
complete case and worker startup record, and keeps a terminal receipt on
ordinary exceptions and interrupts. An OS kill cannot guarantee a final
receipt; a remaining `RUNNING` receipt means incomplete, never success.
Successful completion binds the raw measurement and worker-log digests.
Standalone reporting verifies those bindings and exact method/repeat/input
coverage before producing a complete report. Existing run directories cannot
be replayed. Worker metadata includes Python/package versions, CPU model,
platform, Numba thread count and live threadpool configuration.

Example commands, **only after the owner confirms controlled timings are
clear** (replace the printed hash literally):

```sh
python experiments/benchopt_vus_adapter.py --fetch
python experiments/dtaianomaly_adapter.py --fetch
python experiments/benchmark_saturation_external_baselines.py freeze artifacts/saturation/mac-external-baselines
python experiments/benchmark_saturation_external_baselines.py run artifacts/saturation/mac-external-baselines --protocol-sha256 FROZEN_SHA256
```

No arrays, CSV observations, NPZ files, or cached third-party source need to be
published with the JSON/JSONL receipts. The supplemental timing environment
uses several persistent idle worker processes and differs from the earlier
in-process main study; only within-supplement paired ratios are compared.
