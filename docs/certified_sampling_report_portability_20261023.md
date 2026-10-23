# Exact-byte portability of the certified-sampling report

The report-replay mismatch was isolated to NumPy numerical dispatch during aggregation of already recorded timing measurements. On the same Linux runner, native `X86_V4` dispatch changes five timing-summary floats by one ULP each; selecting `baseline(X86_V2)` reproduces the frozen report byte for byte. No metric result, selection decision, integer certificate, or original timing measurement is changed by this repair.

The repair is process-local: set `NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4` only for report replay. Continue to require exact serialized JSON equality. The original mismatching receipt is preserved alongside the successful replay; no tolerance was introduced and no frozen result was overwritten.

## Observed evidence

All receipts use Python 3.12.15 and NumPy 2.5.4 on Linux x86-64. The report producer, diagnostic source, protocol, input manifest, source manifest, recorded-call ledger, and frozen reference report have matching hashes across the compared executions.

| Actions run and invocation | Float64 `log` / `exp` dispatch | Exact report bytes | Changed leaves |
|---|---|---|---:|
| [39924505881](https://github.com/mandu5/sparse-vus/actions/runs/39924505881), native | `X86_V3` | match | 0 |
| 39924505881, features disabled | `baseline(X86_V2)` | match | 0 |
| [39924511661](https://github.com/mandu5/sparse-vus/actions/runs/39924511661), native | `X86_V4` | mismatch | 5 |
| [39924858264, same-runner job](https://github.com/mandu5/sparse-vus/actions/runs/39924858264/job/120318631275), native | `X86_V4` | mismatch | 5 |
| 39924858264, same job, features disabled | `baseline(X86_V2)` | match | 0 |

The final two invocations execute sequentially in one `sampling-report-portability` job. Their Python, NumPy, platform, source hashes and input hashes agree. The default invocation retains its nonzero diagnostic result; the baseline invocation is required to succeed. Both receipts are uploaded in the same `sampling-report-portability` artifact. This supplies direct intervention evidence beyond the earlier comparisons between runs.

The default `X86_V4` payload has SHA-256
`8eeed779eafa6c51efb79769482caface9cb14f615b6d25766d6c9959e617fba`.
The baseline payload exactly matches the frozen report SHA-256
`b193de60aade226e99491a16b18b50084591984b78a246c925f51ba3b1428e4d`.
Every invocation consumes the same recorded-call ledger SHA-256
`283ccfafa5b712e2a7316b344b4c75ae8f528359bbb42725fd48fc3963224023`.

## Exact differences

An independent recursive comparison of the downloaded expected and rebuilt trees reproduces the diagnostic's five paths. Every non-timing field is exactly equal. All five changed leaves are under `timing.ratios`; each differs by one binary64 representable step.

| Path within `timing.ratios` | Frozen value | Native `X86_V4` value |
|---|---:|---:|
| `dense_exact.per_family_geometric_mean_ratio.IOPS` | 14.47223817584545 | 14.472238175845447 |
| `klein250.family_bootstrap_95_percentile[1]` | 6.403125232126602 | 6.403125232126601 |
| `saturation_exact.per_family_geometric_mean_ratio.MITDB` | 0.995790801898049 | 0.9957908018980489 |
| `saturation_exact.per_family_geometric_mean_ratio.SMD` | 1.005338872832547 | 1.0053388728325467 |
| `saturation_exact.per_family_geometric_mean_ratio.SensorScope` | 1.0802803848076354 | 1.0802803848076352 |

The maximum absolute difference is `1.7763568394002505e-15`. Its small size does not turn the default replay into an exact match: the diagnostic correctly reports `MISMATCH`. The separately observed baseline invocation supplies the exact match.

These paths use logarithms/exponentials when constructing geometric means or timing bootstrap summaries. The intervention establishes dispatch dependence of this report reconstruction. It does not identify a defect in a specific NumPy transcendental kernel, nor require changing the experiment's arithmetic contract.

## Narrow repair and replay

For the standalone diagnostic, which reads preserved metric-call records without a raw-input cache:

```bash
NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4 \
  python experiments/diagnose_sampling_report_portability.py \
  --output /tmp/report-portability-baseline.json
```

The output must be a new file. Exit zero requires identical serialized JSON; any mismatch remains a failure. `numpy.show_runtime`, `numpy.show_config`, and `numpy.lib.introspect.opt_func_info(func_name='^(log|exp)$')` record the active dispatch alongside every diagnostic.

For the existing producer's report command, after its pinned source dependencies have been acquired:

```bash
NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4 PYTHONPATH=src \
  python experiments/msad_sampling_study.py report
```

The environment override belongs to these replay invocations, not to an entire benchmark workflow or the original metric/timing collection. The unchanged producer still rejects a nonidentical reconstruction. The frozen source files and original measurements remain bound by their earlier hashes.

The demonstrated byte agreement concerns the tested inputs and recorded software environments. Future NumPy versions or CPU dispatch layouts continue to face the same exact-byte check; this result is not a guarantee that all future environments will choose equivalent kernels.

## Preserved receipts

`artifacts/certified-sampling-portability-20261023/` contains five complete diagnostic receipts compressed with deterministic gzip (`mtime=0`), three Actions metadata snapshots, and `review-summary.json`. The compressed receipts total 1,957,495 bytes; each decompresses to its original complete JSON, including both full report trees. The summary records compressed and uncompressed SHA-256 hashes, dispatch details, differing paths, and the independently checked same-runner intervention.

The original mismatching receipt from run 39924511661 has uncompressed SHA-256 `7251776b07443eff36bfbb84a1a70a8fdaa03caeac5e6b294d0b223030a77120`. The same-runner default and baseline receipts have uncompressed hashes `bdb50cb43039d70f2a88df313906ff88e7023aafc870270c5c8843032619d509` and `9ce491f66cb2c31fe1978e26c2d6a67becec892c5af2a6cb19664442b826ca65`, respectively. No failed receipt was discarded or replaced by the successful baseline.
