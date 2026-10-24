The original Linux native TimeEval archive passes the saved-output reconstruction audit. It has 120 completed workflows, 4 timeout attempts and 20 prespecified skips across 144 planned records. The main all-observed combined raster/bucket geometric time ratio is **1.9318177236 [1.9066147296, 1.9459591033]**. Completed public-reference outputs cover **28/52 profiles per contract**, with all 24 Stock profiles missing; complete public parity must not be claimed. There is no archived-output integrity blocker, but these coverage and timing qualifications constrain the claims.

Audited on 2026-10-24, independently of manuscript recommendations and without assigning an acceptance score. The GitHub API reports [original Linux replay 40079636938](https://github.com/mandu5/sparse-vus/actions/runs/40079636938) as completed/success at project commit `f7c900b0c1a22f965eacd859f83da2f58efd8b40`; its job completed at `2026-10-24T10:21:19Z`. The saved `reproduction-start.json` identifies the same commit, and `reproduction-complete.json` was written at `2026-10-24T10:21:11.206582+00:00`.

The archive root is `artifacts/pvldb-research-20261024/strengthening/linux-original-replay`. The newly executed command was:

```sh
.cache/strengthening-env/bin/python experiments/audit_timeeval_archived_outputs.py \
  --run artifacts/pvldb-research-20261024/strengthening/linux-original-replay/timeeval-linux-v1 \
  --protocol artifacts/pvldb-research-20261024/strengthening/linux-original-replay/timeeval-global.json \
  --manifest artifacts/pvldb-research-20261024/strengthening/linux-original-replay/timeeval-manifest.json \
  --out artifacts/pvldb-research-20261024/strengthening/linux-original-replay/native-archived-output-audit.json
```

It exited 0 with `ARCHIVED_NATIVE_OUTPUT_RECONSTRUCTION_PASSED`. The archive auditor SHA-256 is `b8a79cb122d9e6cd2bd9bd3af41cc8caa1ce9b31b03a6130dc870c266016c5db`. This audit verified saved protocol/manifest/receipt bindings, declared query metadata, completed result CSV hashes, row identities, metric parity, censor handling and timing summaries. It did **not** verify local raw-data, label, score-vector or source bytes, repeat detector fits, recompute metrics, or import the candidate/runner. Frozen absolute input/source paths were not followed. The stronger original CI input/output audit receipts are preserved and hash-verified; their original input checks are not represented as new local byte checks.

All five SHA-256 bindings in `reproduction-complete.json` independently match the downloaded files:

| Receipt field | Archived file | Matching SHA-256 |
|---|---|---|
| `weighted_report_sha256` | `weighted-linux-v2/independent-report.json` | `94e8e89f59b8ad02ce0b4ac8ba9ed13e8d69fdbd5bd85df581eed4a700967599` |
| `native_complete_sha256` | `timeeval-linux-v1/complete.json` | `9c31f42e3322433f034551fb0519d654176629d8bb51b8bc20e2551b294bf2ca` |
| `generation_sha256` | `workload-generation.json` | `df1907ed44c4c603265d0cb4bf4e1b2d56c90f2486c5814e7ee847fc049ed7dc` |
| `native_input_audit_sha256` | `native-input-audit.json` | `1b16527438e86cd79b650576e4fa7b0663ffef281878481f7e4837a69f3e0790` |
| `native_output_audit_sha256` | `native-output-audit.json` | `a0dd58f78deb27be4b870f59504cdaaac135655a224c77be4410d53bfcf2e147` |

The global protocol SHA-256 is `094f74d974a70a28acc95ab1e6b68f7ff1092278dc50092a4e03cd7988ec1595`; both run-start and completion bind it, and the bound-protocol copy agrees. The standalone manifest SHA-256 is `b2e69a8c948ce10e2807e062fbe65f11757cdea266000e0c4bab026325227bc8`. This original protocol does not carry a separate `manifest_sha256` field; exact equality to its embedded manifest payload was verified instead. Saved generation and native-input-audit receipt bytes also match their manifest bindings. The original `native-output-audit.json` remains unchanged.

The design has 52 profiles from 26 recordings: FFT and COPOD on 2 MSL, 12 Stock and 12 WSD recordings. Each contract has the combined batch and three family batches, six balanced method permutations, and public/raster/bucket methods: `2 × 4 × 6 × 3 = 144` planned records. All 48 raster and 48 bucket workflows completed; public completed 24, timed out four times, and skipped the remaining five attempts for each censored method/contract/batch key. Thus 124 attempts actually ran. Timeout trials are 0 and 36 under `native_default50`, and 72 and 108 under `all_observed`: combined and Stock public workflows in round 0. Their recorded elapsed times are respectively 600.000441903, 600.000348237, 600.000348645 and 600.000262405 seconds. No timeout template's metric cells were used as completed output, and no skipped duration was imputed.

Independent reading of all 120 completed result CSVs checked 2,832 rows and 8,496 scalar metric cells, with `Status.OK` and matching profile identities throughout. CSV-versus-JSON scalar discrepancies are at most `1.1102230246251565e-16`. Repeated outputs for a given method/profile/contract agree exactly. Across raster and bucket, ROC_AUC and PR_AUC agree exactly; maximum RANGE_PR_AUC differences are `3.3306690738754696e-16` for default and `2.7755575615628914e-16` for all-observed. Against available public outputs, the maximum is `1.1102230246251565e-16` for RANGE_PR_AUC in each contract and zero for the other two metrics. All are below the frozen absolute tolerance `1e-10`, with `rtol=0`.

Public output coverage is 4/4 MSL and 24/24 WSD profiles, but 0/24 Stock profiles, under both contracts. Raster and bucket each cover 52/52 profiles under both contracts. Public parity flags are false for combined and Stock, true for MSL and WSD. Public results from completed family batches support those same profiles in the combined compiled outputs; they do not supply Stock outputs or recover a censored combined public timing.

The following eight cells give the declared query counts and completed-workflow median times in seconds. Query min/max are per profile. `>600` marks one censored public attempt followed by five prespecified skips, not a median or completed time. Every uncensored method has six completed orders.

| Contract | Batch | Profiles | Queries total (min–max) | Public seconds | Raster median seconds | Bucket median seconds |
|---|---|---:|---:|---:|---:|---:|
| default50 | combined | 52 | 2,776 (2–90) | >600 | 1.5840834745 | 1.5679196720 |
| default50 | MSL | 4 | 97 (2–52) | 0.2596877865 | 0.0444154365 | 0.0448544155 |
| default50 | Stock | 24 | 1,282 (50–66) | >600 | 0.7102273715 | 0.7078234265 |
| default50 | WSD | 24 | 1,397 (51–90) | 14.4419548130 | 0.8354318775 | 0.8216264550 |
| all-observed | combined | 52 | 71,750 (2–5,819) | >600 | 3.0421717425 | 1.5659371275 |
| all-observed | MSL | 4 | 655 (2–610) | 1.9425139050 | 0.0473689405 | 0.0444490915 |
| all-observed | Stock | 24 | 44,059 (194–5,094) | >600 | 1.6829360765 | 0.7090699000 |
| all-observed | WSD | 24 | 27,036 (63–5,819) | 406.2409892845 | 1.3322581570 | 0.8457827215 |

`default50` means the native nominal `max_samples=50`, which is not a hard 50-query cap. The all-observed contract configures `max_samples=positive_infinity`, retaining native eligibility, synthetic endpoints and integration. The archive audit reconstructs these counts from declared distinct-score metadata and the pinned native sampling formula; it does not count newly read score-vector bytes.

Each ratio below is the geometric mean of the six matched within-round time ratios, with the frozen 10,000-resample paired-order bootstrap, seed 20261024. It is not a ratio of medians. Square brackets are the approximate 95% intervals conditional on this one fixed workload execution. For a censored public workflow, the strict lower bound is `600 / bucket_time_in_the_same_round`; there are zero complete public/bucket pairs and no interval for that cell.

| Contract | Batch | Raster / bucket [approximate CI95] | Public / bucket [approximate CI95] |
|---|---|---|---|
| default50 | combined | 1.0144691861 [1.0073271666, 1.0274286356] | >383.7460438677, round 0 only |
| default50 | MSL | 0.9921976213 [0.9862058685, 0.9996942730] | 6.0436700222 [5.7554949232, 6.4422004260] |
| default50 | Stock | 1.0197858462 [1.0031693793, 1.0464351325] | >847.8298304017, round 0 only |
| default50 | WSD | 1.0271993641 [1.0153691591, 1.0501047827] | 17.5870794300 [17.5600925162, 17.6208536545] |
| all-observed | combined | 1.9318177236 [1.9066147296, 1.9459591033] | >382.8032744012, round 0 only |
| all-observed | MSL | 0.9411189936 [0.7296368937, 1.0758702903] | 38.6137863337 [29.8984874527, 44.1643890876] |
| all-observed | Stock | 2.3421255658 [2.2798733406, 2.3766352622] | >846.0430670101, round 0 only |
| all-observed | WSD | 1.5770561640 [1.5585355218, 1.5933552750] | 480.4066556123 [474.9721651729, 485.6407994614] |

The small MSL batch prevents a universal win statement. Default MSL favors raster by a small amount. All-observed MSL is inconclusive under this interval and has a geometric ratio below one despite a lower bucket median. In its six saved bucket attempts, round 4 is 0.094967262 seconds while the other five range from 0.043421226 to 0.044908428 seconds. This observation is retained without exclusion or causal explanation.

The timed unit is the warmed native `MetricComputor` constructor plus `recompute(True)`: dataset/results/score/optional-metrics CSV reads, the native default three metrics, final results.csv write/close and one deadline arming call. Imports, hash audits, tiny JIT warmup, trial-template copying, detector fitting and post-run audits are excluded. These are serial native recalculation measurements, not cold-disk, fsync, training, arbitrary deployment or population estimates.

The original and supplemental Linux executions agree in recorded platform (`Linux-6.17.0-1022-azure-x86_64-with-glibc2.39`), Python 3.11.9, dependency-version dictionaries and warmup completion. Both pip freezes have 64 lines and differ only in the local TimeEval installation path. After normalizing archived root prefixes, declared hashes agree for all 425 TimeEval source files, 8 prts files, 80 native input files (including all 52 score text files), and all 6 shared project files. The supplemental manifest adds five project bindings for its interval adapter, controls, runner and audits. Profile identities, query plans and batch payloads agree exactly. These are comparisons of saved hash declarations, not fresh source/input byte verification.

The recorded environment is not identical in every respect: original NumPy and SciPy OpenBLAS dispatch architecture is `Cooperlake`, while the supplemental execution records `SkylakeX`. Both record one thread, NumPy OpenBLAS 0.3.23.dev and SciPy OpenBLAS 0.3.27.dev. The three-method sequence also changes from public/raster/bucket to raster/interval/bucket. The archive does not identify a causal contribution from CPU, dispatch, load, caching or sequence; no such attribution is made.

The next table preserves the separate Linux absolute medians. Each arrow is original → supplemental; all times are seconds, and the ratio column gives the separately computed raster/bucket geometric ratios. No duration or ratio is pooled across executions.

| Contract | Batch | Raster median, original → supplemental | Bucket median, original → supplemental | Ratio, original → supplemental |
|---|---|---|---|---|
| default50 | combined | 1.5840834745 → 1.4616913865 | 1.5679196720 → 1.4380566885 | 1.0144691861 → 1.0155864474 |
| default50 | MSL | 0.0444154365 → 0.0461743575 | 0.0448544155 → 0.0472678270 | 0.9921976213 → 0.9807060606 |
| default50 | Stock | 0.7102273715 → 0.6776995460 | 0.7078234265 → 0.6722585745 | 1.0197858462 → 0.9972321584 |
| default50 | WSD | 0.8354318775 → 0.7798864355 | 0.8216264550 → 0.7647796480 | 1.0271993641 → 1.0230647794 |
| all-observed | combined | 3.0421717425 → 4.1125937975 | 1.5659371275 → 1.4990302555 | 1.9318177236 → 2.7561310425 |
| all-observed | MSL | 0.0473689405 → 0.0494076965 | 0.0444490915 → 0.0464023730 | 0.9411189936 → 1.0645758151 |
| all-observed | Stock | 1.6829360765 → 2.6474358960 | 0.7090699000 → 0.6925515850 | 2.3421255658 → 3.8362802877 |
| all-observed | WSD | 1.3322581570 → 1.4259891700 | 0.8457827215 → 0.7787119700 | 1.5770561640 → 1.8228112303 |

Descriptively, the all-observed combined ratio rises by 42.6703% between these executions. Its numerator raster median rises by 35.1861%, and its denominator bucket median falls by 4.2726%. For the exact geometric-ratio decomposition, raster geometric time rises from 3.0408902072 to 4.1170760687 seconds (+35.3905%) and bucket geometric time falls from 1.5741082454 to 1.4937882144 seconds (−5.1026%): `(1.3539048726 / 0.9489742645) = 1.4267034663`. This is arithmetic description, not a controlled causal estimate. The conditional within-run intervals do not cover between-execution variation.

For comparison, combined raster/bucket results were also recalculated directly from the saved Mac original and Mac supplemental trial durations. These comparisons do not extend this report's full artifact-integrity audit beyond the original Linux archive.

| Execution | Contract | Raster median seconds | Bucket median seconds | Geometric ratio [approximate CI95] |
|---|---|---:|---:|---|
| Mac original | default50 | 1.0847992080 | 1.0783126040 | 1.0168413522 [0.9981660527, 1.0391899650] |
| Mac supplemental | default50 | 1.0685933130 | 1.0429461870 | 1.0264153776 [0.9979626906, 1.0492829382] |
| Linux original | default50 | 1.5840834745 | 1.5679196720 | 1.0144691861 [1.0073271666, 1.0274286356] |
| Linux supplemental | default50 | 1.4616913865 | 1.4380566885 | 1.0155864474 [0.9966162906, 1.0330703698] |
| Mac original | all-observed | 2.9460463540 | 1.0806823330 | 2.7281429239 [2.6486845606, 2.8014813982] |
| Mac supplemental | all-observed | 2.9473650625 | 1.0726348120 | 2.7316945387 [2.6558009198, 2.8119531650] |
| Linux original | all-observed | 3.0421717425 | 1.5659371275 | 1.9318177236 [1.9066147296, 1.9459591033] |
| Linux supplemental | all-observed | 4.1125937975 | 1.4990302555 | 2.7561310425 [2.7421314733, 2.7734271574] |

The all-observed combined ratios therefore span 1.93–2.76 across these four distinct executions. The default combined gains are small; three of the four displayed within-run intervals include one. Mac original and original Linux each have the same 120/4/20 completion/timeout/skip counts, but their saved input declarations are not identical: only 27/52 score hashes match. Linux all-observed has 71,750 declared queries versus Mac 71,749. The sole distinct-score count change is COPOD on WSD `034_WSD_id_6_WebService_tr_4559_1st_8461`, from 1,686 on Mac to 1,687 on Linux. Accordingly, no cross-host timing estimate is pooled, no public completion is inferred from compiled controls, and the higher supplemental Linux ratio does not replace the original 1.93 result.
