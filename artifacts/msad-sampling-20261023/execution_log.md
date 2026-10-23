# MSAD sampling study execution log

2026-10-23: Task 3 of `docs/superpowers/plans/2026-10-23-sampling-consequences.md`. Existing research branch retained; independent files only.

- Protocol frozen before corpus metric calls, SHA256 `c778699fe9393ba4f5a6bb9e54362bb9327bcdc1efb3aca4b2cad6deb3cdc2cb`.
- Initial test collection failed because the runner did not exist. Implemented runner: 12 tests passed. Added two adversarial tests; both failed as intended (missing control coverage could promote effects, incorrect timed outputs were unchecked). Repaired before source freeze; 14 tests passed.
- Synthetic isolated-worker smoke passed: exact result 1.0, deliberately tiny watchdog caused a terminated call, restarted worker returned sampled result 1.0. This is non-study input.
- Timing subset independently matches acquisition proposal, 30/30 series.
- Source manifest frozen before study metrics, SHA256 `dae17c7e3e370c5d4d1206762ab201435f1c693d1ececf80f506972b72b0e96d`.
- Numerical pass started with all 128 series and all methods/resolutions. Append-only records; no outcome-dependent replacement. Main numerical wall times are not performance evidence because independent tests/certificate accuracy may run concurrently.
- Timing is deferred until all acquisition, tests, and certificate accuracy work is idle.

- All prescribed numerical calls finished: 36,864/36,864 OK. Independent controls: 720/720 OK. All4,608 upstream H250 comparisons pass.
- Timing completed serially after all accuracy jobs released CPU:9,000/9,000 OK, five repetitions for every declared method/case. No timeout or error in any phase.
- Final report: `report-283ccfafa5b712e2.json`; source/protocol unchanged. Records now closed; host handed to the separate certificate-cost study.
- Full primary finding8/128/fourfamilies is preserved alongside the independent one-endpoint-overlap audit (20/128 matches; nonmatching108 subgroup4/108/twofamilies).
- Read-only independent primary table audit passed; all input/score precision and overlap limitations are in README.md.
