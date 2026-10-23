# MSAD threshold-sampling study, 2026-10-23

The frozen study is complete: **36,864 numerical calls, 720 independent exact-control calls, and 9,000 timing calls**, all successful. The immutable final report is [report-283ccfafa5b712e2.json](report-283ccfafa5b712e2.json). The original stored scores, metric contract, and selected panel were retained throughout.

The primary setting is original dynamic VUS-PR, averaged over every integer width from zero through 30, with the published rank-uniform 250-threshold grid. Among the twelve published model/configuration scores on each of 128 selected series, the approximate winner set has best-case exact regret at least 0.01 on **8/128 series (6.25%), across four source families**. Maximum regret is **0.3985750302**. There are 106 strict pair reversals, including 22 with both margins at least 0.01. These meet the declared finite-panel effect threshold; this is an offline metric-fidelity finding, not a claim about deployable label-free model selection.

Family-cluster bootstrap resampling gives a pooled practical-regret fraction interval of **[1.086%, 13.197%]**; the observed 6.25% should not be described as a population lower bound above 5%. Equal-family weighting gives 5.278%. Both signed error directions occur: across 1,536 primary scalars, maximum overestimation is 0.1616922812 and maximum underestimation is 0.5601231694; 15 and 150 scalars respectively have error magnitude at least 0.01 in those directions. The eight empirical reversals are not all attributed to the constructed post-saturation mechanism.

## Complete sensitivity results

Entries are numbers of series whose sampled winner set has best-case exact regret at least 0.01; every denominator is 128.

| Maximum width | H=32 | H=64 | H=128 | H=250 | H=500 | H=1000 |
|---|---:|---:|---:|---:|---:|---:|
| 30 (primary) | 21 | 16 | 11 | 8 | 1 | 0 |
| 100 | 20 | 15 | 12 | 7 | 2 | 0 |
| 300 | 20 | 15 | 11 | 6 | 2 | 1 |

At H=250, affected-family counts are 4, 5, and 3 for widths 30, 100, and 300. Width 300's 6/128 fraction is below the frozen 5% promotion threshold. Increasing H to 1000 removes practical selection regret at widths 30 and 100 in this panel; width 300 retains one case with regret 0.0952019723. Scalar metric error and model-selection regret are distinct outcomes.

## Controls and timings

All **4,608** unchanged pinned Klein comparisons at H=250 and all **720** independent exact controls pass. The latter comprise dense exact and unchanged Klein at H=n on the fixed first two retained series per family, all twelve models, at L=30. Maximum absolute discrepancy across these controls is **4.440892098500626e-15**; floating parity at this scale is not a formal real-arithmetic certificate.

Timings use the same fixed thirty-series subset, all twelve models, five independently randomized paired repetitions, one thread, a 30-second per-call process watchdog, and non-study warmup. The other research computation jobs were stopped during this phase. All **9,000/9,000** declared calls returned successfully with output parity. Preparation and public-API input validation are inside each timed scalar call; source decode, process setup, winner aggregation, and record writing are outside the scalar-call timer. Collection wall-time logs have a separate broader scope and are not scalar latency measurements.

Ratios below are geometric means of comparator time divided by radix-exact time, over 360 complete paired series/model cases; intervals resample source families.

| Comparator | Time ratio | Family bootstrap 95% interval | Output/work scope |
|---|---:|---|---|
| Matched compiled H=250 | 1.0441 | [1.0294, 1.0623] | PR only, same preparation family |
| Saturation exact | 1.0111 | [0.9986, 1.0261] | PR only; interval includes one |
| Unchanged Klein H=250 | 5.0773 | [4.1860, 6.4031] | PR only |
| Independent dense exact | 13.4808 | [12.5054, 14.5828] | Computes ROC and PR internally |

The matched compiled comparison supports a modest latency advantage for exact evaluation on this quantized panel. The larger Python/NumPy comparator ratios are not an intrinsic orders-of-magnitude exact-versus-approximate advantage. The extra ROC work in the dense comparator must remain visible whenever its ratio is cited.

## Data scope and audit findings

All 1,536 released score vectors contain at most **101 distinct values**; five LOF vectors are constant. These are the original stored scores, with no added rounding or repair. A rank-uniform grid with 250 samples can still omit rare distinct threshold classes, so its sample count exceeding the number of unique scores does not imply exhaustive integration. Runtime generalization to unquantized model outputs requires separate evidence. See [score-precision-summary.json](score-precision-summary.json).

The original pre-outcome identity filter excluded exact canonical observation/label duplicates. A later bounded audit found **20/128** joint observation-and-label matches to earlier data after dropping one endpoint. The unchanged 128 remains the prespecified panel; it is not wholly unseen physical recordings. The 108 nonmatching series form a **post-acquisition descriptive subgroup**, with 4 practical-regret cases in two families and maximum regret 0.2362084785. This subgroup does not satisfy the primary panel's frozen promotion criterion. The audit does not establish absence of other crops or transformations. See the independent [one-point overlap audit](../msad-score-provenance-20261023/one-point-overlap-audit.json) and [primary recomputation audit](../msad-score-provenance-20261023/independent-primary-audit.json).

Source files and raw arrays remain in the ignored corpus cache. Data attribution and source provenance are in [the acquisition package](../msad-corpus-20261023/ATTRIBUTION.md). The repository's code license is not a blanket license for third-party datasets.

## Receipts and reproduction

- [protocol.json](protocol.json) was frozen before any study metric computation, SHA256 `c778699fe9393ba4f5a6bb9e54362bb9327bcdc1efb3aca4b2cad6deb3cdc2cb`.
- [source_manifest.json](source_manifest.json) binds the driver, implementations, protocol, acquisition manifest, and independent input audit before metric calls, SHA256 `dae17c7e3e370c5d4d1206762ab201435f1c693d1ececf80f506972b72b0e96d`.
- Final [records.jsonl](records.jsonl) is append-only and now closed, SHA256 `283ccfafa5b712e2a7316b344b4c75ae8f528359bbb42725fd48fc3963224023`.
- Final report SHA256 is `b193de60aade226e99491a16b18b50084591984b78a246c925f51ba3b1428e4d`.
- [primary-first-scheduler.json](primary-first-scheduler.json) documents the authorized execution-order change: finish the primary width first, validate it, then resume the remaining widths. No retained numerical result, method, selected input, or statistical criterion changed. One potentially in-flight unrecorded call was rerun after an ordinary interrupt; every durable key was retained.
- [primary-validated-claim-table.json](primary-validated-claim-table.json) contains the eight affected cases, exact/sample values, all primary controls, and a canonical hash of the complete primary/validation subset.
- [certificate-ledger-independent-audit.json](certificate-ledger-independent-audit.json) independently checks the separate certificate study's integer winner/regret arithmetic; it does not replace the certificate construction proof.

The driver is [experiments/msad_sampling_study.py](../../experiments/msad_sampling_study.py); its fourteen analysis/provenance tests are [tests/test_msad_sampling_study.py](../../tests/test_msad_sampling_study.py). They cover tied winner sets, both tied-winner regrets, pair reversals, input/source mutation, append conflicts, report reconstruction, missing controls, and incorrect timed outputs. An isolated non-study smoke separately checked successful evaluation, a hard process timeout, and successful restart.

With the pinned inputs and research dependencies available, `PYTHONPATH=src python experiments/msad_sampling_study.py report` verifies frozen sources and reconstructs the immutable report. The `numerical`, `validate`, and `timing --idle-host-confirmed` commands resume missing declared keys. Do not run new appending phases against this finalized ledger; use a separately named/versioned study directory for a new execution environment or changed implementation.
