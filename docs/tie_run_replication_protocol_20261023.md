# Portable complete-tie structural/external replication protocol

This new protocol preserves the frozen 131-case Mac study and reuses its unmodified metric methods, timing runner, and report code. It defines a separate, portable **68-case** experiment: the original 20 source-bound synthetic fixtures plus all 48 one-interval score-vector/width cases regenerated from the same fixed twelve external series. The 63 historical development cases are excluded, so no foundation-model score archives are needed.

The input population is previously studied. Regeneration is not unseen-domain confirmation or an assumed identical-score replay. The four generators, pinned source selection, preprocessing, and parameters remain those of `fetch_saturation_external.py`. All twelve series are regenerated before selecting every one-interval case. Raw CSV and label identities must match the original metadata; score hashes are compared explicitly and may differ across platforms.

## Preparation, storage, and identity

`experiments/reproduce_tie_runs.py prepare` requires a new output directory under `artifacts/tie-runs/` and reserves a new ignored `.cache/tie-replication/<output-name>/` directory. It refuses existing outputs/caches and repository escapes. The historical external selection, manifest, tie protocol, and input manifest are read without modification. The pinned Klein source is fetched/verified using its existing adapter.

The original acquisition module is called with new `CACHE` and `OUT` locations. Selection is compared before raw observation downloads or score generation; only `environment` and `frozen_utc` may differ. Source revisions, metadata identities, exact series selection, generator parameters, and generator/design hashes must match. Generation writes raw observations and arrays only beneath the ignored cache and public provenance receipts beneath the new output's `generation/` directory. Module globals are restored afterwards.

Preparation verifies raw-data, labels, preprocessing, actual parameter identities, and complete twelve-series/four-generator coverage. It records all 48 score-hash comparisons against Mac without demanding their equality. Every new NPZ and numerical array is hashed and validated. Structural fixtures are copied byte-for-byte from the original bound NPZ files into the new public `inputs/` directory; regenerated scalar fixtures remain in ignored cache. Every qualifying external vector enters widths 30, 100, and 300. The expected labels give four one-interval series, sixteen vectors, and 48 timed cases; mismatches fail instead of silently reducing coverage.

The final compatible `protocol.json` binds the new orchestrator and this protocol, the original generator/design, all measured sources, the old reference manifests, and new selection/input-comparison receipts. Preparation computes no VUS metric. Failed preparation leaves its fresh partial directory for inspection; retry with a new name rather than overwriting any historical output.

## Timing and analysis

Methods remain `tie_runs`, `saturation`, `radix`, and `klein`, all PR-only. Repetitions remain five with the original fixed seed `202610234`, one untimed warm call per method/case, seeded randomized serial method order, one compute thread, and absolute parity tolerance `1e-11`. Full public-call validation, ranking, geometry, and root-table preparation are timed. Input loading, score generation, imports/JIT warmup, and diagnostic profiles stay outside the timer. No concurrent tests, input generation, builds, or other benchmarks should run during timing.

The `run` command requires the exact new protocol hash and delegates to unchanged `benchmark_tie_runs.run`; reporting uses its unchanged `report`. Report groups call the new population `external_regenerated`. All methods, repetitions, losses, and work counts are retained. Numerical/work assertions are the only pass/fail criteria; timings remain descriptive. The new study changes no old primary runtime decision and must not be pooled with the original 131 cases or rendered as its historical tables.

## Commands

Use the accelerated research environment and dependency/setup instructions in `docs/sparse_vus_reproduction_20261023.md`. Preparation needs network access and CPU time for the existing four score generators. Run from the repository root, replacing the example output name with a fresh name:

```sh
python experiments/reproduce_tie_runs.py prepare --output artifacts/tie-runs/portable-example
python experiments/reproduce_tie_runs.py run --output artifacts/tie-runs/portable-example --protocol-sha256 HASH_PRINTED_BY_PREPARE
python experiments/benchmark_tie_runs.py report --output artifacts/tie-runs/portable-example
```

The first command acquires public sources and generates inputs; the second performs timing; the third reconstructs the recorded report without new timings. Source hashes must stay unchanged between prepare and run. The ignored cache is needed for timing but not report reconstruction. The new protocol and comparison receipts remain bound for reconstruction.

Meaningful guard tests live in `tests/test_tie_run_reproduction.py`. After the active timing window ended and CPU clearance was granted, all 11 guard tests passed and the CLI help check passed. These checks cover selection/source/input drift, score-comparison retention, path/output isolation, scalar-input construction, and coverage. Full acquisition, generation, and timing have not yet been run through this new entrypoint. No successful full reproduction result is claimed merely because the protocol, CLI, and fixture tests exist.
