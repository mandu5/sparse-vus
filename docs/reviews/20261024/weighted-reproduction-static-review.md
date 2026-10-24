# Fresh weighted/TimeEval reproduction: independent static review

Reviewed 24 October 2026. Scope: `experiments/reproduce_strengthening.py`, `.github/workflows/weighted-range-reproduce.yml`, the input-audit CLI, and the directly called producer/consumer routines needed to trace source, input, and artifact boundaries. No numerical tests, detector fits, metric evaluations, TeX, or benchmarks were run during the active Mac timing window. Source reads and one official package-metadata read were used.

## Finding resolved during review

**P1 — the cross-host native design comparison includes regenerated query counts.** At the reviewed version, `experiments/reproduce_strengthening.py:125` compares the complete `batches` value to the Mac manifest. `scripts/run_timeeval_strengthening.py:211–221` adds each host's score-derived `query_counts` to those batches. Legitimate host-dependent score changes can change distinct-score counts and therefore the actual query counts while the selected rows, methods, parameters, sampling rule, and design remain identical. The runner explicitly permits host-dependent generated scores, so this check can reject a valid fresh reproduction.

Compare the fixed batch fields (`name`, `families`, `row_count`) across hosts; keep each host's full query plan/counts in its own frozen manifest and report any differences. Do not remove the batch-identity check altogether. This is a conditional failure mechanism established by static control flow, not an observed Linux failure. The parent was notified before the proposed CI run.

The parent subsequently changed the reproduction runner to compare the batches after removing only `query_counts`, retaining the full fresh counts in each host's manifest. A text re-read confirmed this change. The identified cross-host rejection mechanism is resolved; no numerical execution was used to make that assessment.

## Nonblocking reproducibility limits

- The dependency closure is not completely locked. The requirements file pins the listed packages, but the workflow installs `torch==2.10.0` separately with dependency resolution enabled. Torch's official metadata lists unpinned `filelock`, `sympy>=1.13.3`, and `networkx>=2.5.1`, which are absent from `requirements-strengthening.txt`. Core numerical packages and Torch itself are pinned; do not describe the whole transitive/build environment as locked. Pin or record the remaining installed versions if a complete environment lock is claimed. [Official Torch 2.10.0 package metadata](https://pypi.org/pypi/torch/2.10.0/json)
- The optional TimeSeAD differential test in `tests/test_weighted_range.py:136–163` skips when `.cache/range-sweep-timesead/...` is absent. The fresh runner downloads TSB-AD and TimeEval, not this TimeSeAD source. Therefore a green selected test suite does not establish that this optional external parity test ran. The exact-oracle tests and TimeEval source tests are separate checks.
- `reproduction-complete.json` means the configured replay completed. The native study can finish with its prespecified censoring, and its separate independent cross-host audit is explicitly deferred by the runner. Preserve the native completion status and public-reference coverage when reporting the result; the top-level marker is not an uncensored-public-parity claim.

## Source and fresh-generation checks

No additional static blocker was found in the following paths:

| Boundary | Evidence and conclusion |
|---|---|
| Fresh destination | `reproduce_strengthening.run` requires a previously nonexistent output directory. It copies project source/test directories and the named discovery/source/protocol metadata. It does not copy the old workload, detector-score cache, or old metric results. |
| Detector source identity | Each TSB-AD closure file is downloaded from its recorded commit URL and checked against its recorded SHA256. The producer verifies the closure, discovery hash, raw archive, and selected member/array identities; workers recheck the frozen source files before fitting. |
| Raw archive identity | Both downloaded and optional supplied archives must match `RAW_SHA`. The producer additionally checks the prior pinned archive identity and each selected member hash. Optional archive reuse reuses raw public inputs, not generated scores. |
| TimeEval source identity | The codeload URL uses the full fixed revision and checks the full archive SHA256 before extraction with the data filter. The input auditor checks twelve source anchors; the native consumer checks its metric/consumer anchors and records the full source tree. |
| Installed versus selected source | TimeEval is installed from the extracted local tree with `--no-deps`. The input auditor and native runner then explicitly put that tree on the import path and reject imports outside it. Detector workers put the downloaded TSB-AD closure first; a fresh destination has no old detector virtual environment/cache to select. |
| Fresh detector generation | The current producer refuses existing workload/protocol/receipt paths, freezes before fitting, launches the FFT/COPOD workers, and writes scores exclusively. The documented historical Mac packaging-recovery branch is not invoked for a clean generation receipt. |
| Input-audit CLI | The runner's `--generation`, `--timeeval-source`, and `--out` arguments exactly match the current required CLI. The auditor rejects an existing output receipt and verifies all 26 cases/52 successful profiles, raw/native/combined identities, native TimeEval labels, worker chronology, and thread records. |
| Weighted same-design comparison | The check permits new timestamps and generated input hashes, while retaining source hashes, all metric/query/timing settings, and ordered case/model identities. Original raw/cohort identity is separately checked by the input audit. |
| Native same-design comparison | Schema, source revision, design, row identifiers, record count, and project source hashes are compared. Per-host dependencies, imported `prts` tree, sources, inputs, and generation/audit receipts are bound by the new manifest and rechecked by the runner. The batch query-count issue above is the exception. |
| Stale consumer outputs | Native workload rows reject preexisting output metric columns. Each timed trial begins from a copy of the new input results tree, and the original template/input hashes are rechecked after the study. |

## Artifact boundary

The upload patterns select research receipts, metric traces, native scalar `results.csv` files, and logs. Raw observations and detector scores remain under the fresh `.cache`/`cache` directories, which are outside the uploaded paths. In native trial copies, `anomaly_scores.ts` files are excluded by the explicit `results.csv`/log patterns. The complete `weighted-linux-v2` directory is uploaded; its current writer stores metric curves (`H x 3` precision/recall/F1 arrays), protocols, metric records, and audit receipts, not the source labels or detector-score arrays.

The inspected successful producer/consumer logging statements print status, identifiers, counts, and exceptions, rather than raw observation or detector-score vectors. Generation receipts contain paths/hashes and bounded stdout/stderr; this review does not claim a universal log sanitizer. The current output writers and allowlist do not redistribute raw input or detector-score files. If the weighted directory's writers change, recheck its contents because that one pattern allows the entire directory rather than named file classes.

This reviewer did not modify any reviewed implementation or workflow. This note records a static review; the clean Linux execution remains the evidence needed for dependency installation, source downloads, generation, and execution success.
