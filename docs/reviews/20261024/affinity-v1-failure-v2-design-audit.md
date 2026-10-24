# Independent audit A: v1 preparation failure and prospective v2 design

**Finding: v1 failed its mandatory preparation condition and completed zero metric blocks. A separately frozen v2 addressing process variability on one new fixed score realization is scientifically legitimate. V1's condition must remain failed, without a waiver or retrospective relabeling.** This is an AI-simulated independent failure/design audit, not a new final manuscript recommendation or a complete v2 implementation approval.

The auditor used saved JSON, immutable source bytes, static call-path inspection, and pure metadata mutation checks. No detector fits, metric workflows, warm-ups, or timed studies were executed. The auditor did not edit implementation or paper files and did not consult another reviewer's scientific recommendation or score. The only auditor-authored file in this task is this receipt. The previous scientific review A and premeasurement v1 audit remain separate records.

## Evidence identity and preservation

- Frozen v1 source commit: `ee3031aafb5cc30c7928d36e965d2156cf3ac2ca`.
- V1 tag: `strength/affinity-blocks-linux-v1`.
- Workflow run: `40090142426`, attempt `1`, as recorded by the saved start receipt; [public run location](https://github.com/mandu5/sparse-vus/actions/runs/40090142426).
- Supplied artifact identifier: `12558059165`. This audit verified the downloaded ZIP bytes and their contents; the artifact identifier was supplied by the coordinator rather than independently resolved through the GitHub API.
- ZIP: `/tmp/sparse-vus-affinity-v1-failed.zip`.
- ZIP SHA256: `e21a32d960ef6f5060dfa84f0ee8105438c403d17241313ed9f1c46f18de7862`.
- Durable extraction: `artifacts/pvldb-research-20261024/strengthening/affinity-failed-v1`.

I independently verified the ZIP digest and byte equality of all **13 archived files** against the durable extraction. All eight committed-source hashes in `affinity-reproduction-start.json` match `git show` at the stated v1 source commit, including the previously audited runner, driver, tests, and workflow. The saved Linux host receipt identifies an AMD EPYC 7763 runner, with permitted logical CPUs 0–3. No measurement-affinity claim is made because preparation did not reach the block stage.

## Failure chronology and counts

The recorded UTC chronology is internally ordered:

| Stage | UTC on 24 October 2026 |
| --- | --- |
| Preparation started | 11:31:13.921271 |
| Detector-generation protocol frozen | 11:31:23.730549 |
| Generation started | 11:31:23.731529 |
| Generation completed | 11:33:52.810824 |
| Independent native-input audit completed | 11:33:55.585150 |
| Affinity freeze subprocess failed | 11:33:57.198288 |

`workload-generation.json` records 26 selected cases, 52 selected/successful profiles, and **52 `Status.OK` results**. Every profile and the aggregate receipt have `metric_evaluation_performed: false`. The native-input audit reports 26 verified datasets, 52 verified profiles, 386,447 dataset rows, no metric evaluation, and no candidate-code import. Its generation hash and protocol hash match the saved generation/protocol bytes. Native source acquisition reports verification of all 425 pinned source files.

The driver calls the freeze subprocess with `check=True` before constructing a successful prepared receipt or invoking the session runner. The failure receipt records that freeze command's nonzero exit. The frozen runner writes the input-identity diagnostic and rejects mismatching prior scores before writing the affinity protocol. Static inspection of this path finds no native metric, warm-up, or session call before that rejection.

Consistently, the archive contains the failed input-identity receipt but no new frozen affinity protocol, prepared receipt, child-process/block receipts, trial traces, metric traces, or result CSVs. One older native protocol is copied reference metadata, not a new execution. Thus the conclusion of **zero metric blocks and zero native metric timing outcomes** follows from both the bound source path and the saved receipts, not merely absent files. Detector-fit and preparation subprocess durations do exist and are explicitly labeled as not metric timings.

## Exact mismatch scope

I independently compared the new generation with both `linux-original-replay` and `linux-interval-replay` generation/native manifests. Against **each** reference:

- **25 COPOD profiles** differ in both `score_array_sha256` and `native_score_sha256`.
- All **26 FFT profiles** and COPOD on `146_MSL_id_7_Sensor_tr_554_1st_1172` match.
- The saved diagnostic's **100 rows** are exactly `25 profiles × 2 hash fields × 2 references`; this is not 100 distinct affected profiles.
- Reconstructing the native input map from the saved input-audit hashes gives exactly **80 native input files**, of which **25 differ**. Every differing file is an existing COPOD `anomaly_scores.ts`; all other native input files match.
- Saved hashes agree with both references for the raw archive, selection, raw members, typed observations, labels, native dataset CSVs, dataset index, and immutable result template. Case lengths, family/recording identities, ordered profile/case metadata, and model identities also agree. This audit compared the saved hash receipts; it did not reread unarchived raw observations or score vectors.
- For `034_WSD_id_6_WebService_tr_4559_1st_8461`, COPOD has **1,686 distinct values instead of 1,687**. No other distinct-value count or zero-value count differs in the saved generation metadata.

The prior numerical-pool receipts report Cooperlake and SkylakeX dispatch architectures, while this run reports Zen. This is a recorded association, not a demonstrated cause of the hash changes. The public failure archive does not contain score vectors, so numerical distances, ULP differences, and rank-order changes were not independently measured. The distinct-count change is already sufficient to rule out treating the realization as an identical exact-query workload. Actual new threshold-vector hashes were not saved because the affinity freeze aborted.

This failure establishes that the attempted fresh regeneration did not reproduce the prior Linux score bytes under the encountered environment. It must remain visible in any broader reproducibility claim. It does not retroactively invalidate the saved measurements on their own bound inputs or establish a cause for the earlier 1.932/2.756 ratio difference.

## Prospective v2 design judgment

A finite v2 can answer a useful narrower question: whether the compiled-control advantage persists across five fresh processes on one runner while holding one newly generated realization of the same 52 profiles fixed. No v1 native metric outcome was available when making this design change, so there is no evidence of selecting a favorable timing outcome. Nevertheless, this is a changed estimand, not successful completion of v1.

The concrete design boundaries are:

1. Preserve v1's source/tag, failed evidence, strict condition, and zero-block outcome. Give v2 its own schema, source commit/tag, protocol, and output namespace, with an explicit predecessor link.
2. Make exactly one whole generation attempt for the fixed 26 recordings and 52 profiles. Abort if a fit is failed or missing. Do not regenerate until a desired hash, cardinality, runtime, or result appears; do not exclude or replace profiles.
3. Keep source/dependency versions, raw archive, typed-input decoding, selected recordings, ordered labels/shapes/models, native dataset bytes/index, immutable result template, and row layout mandatory. Compare with both prior Linux references.
4. Retain every prior score and realized-query difference diagnostically. Freeze the actual new score bytes, generation/input-audit receipts, and exact query plans before any native metric warm-up. Keep those exact current inputs mandatory across all five blocks. Prior realized query-plan equality cannot remain a requirement when new scores are explicitly permitted.
5. Preserve the three compiled methods, two contracts, full native workflow boundary, seed and balanced orders, five fresh processes, CPU/thread controls, six full warm-ups per block, 180 planned timings, scalar parity, evidence/eligibility gates, and block-level statistics.
6. Execute one bounded study and retain all negative, positive, invalid, timeout, and incomplete evidence. Do not pool it with v1 or use it to infer independent-host reproducibility, a workload-population effect, or a causal explanation of earlier runs.

The five-block experiment still has to execute and undergo independent saved-result reconstruction before any empirical conclusion is available. This design audit supplies neither a result nor a higher scientific-quality score.

## Narrow v2 reference-diagnostic inspection

After the above design judgment, I independently inspected `reference_diagnostics` and its mandatory preparation/audit/freeze call path in `scripts/run_timeeval_affinity_blocks_v2.py`, inspected the new driver and prospective specification, and read the associated reference-diagnostic tests. The inspected runner SHA256 was `db3aefe52324840d1c05c66e41bec0394197469e097cbeaa8fe5a04bf3b556fd`. This identifies the inspected source version, not a later frozen execution commit or a complete v2 code approval.

The function keeps selection, ordered case/label/model metadata, profile dtype/shape/status, native layout, native file-key sets, and row identities mandatory against both references. Only contents of score paths already present in the identical native file-key set are treated diagnostically. Unknown or missing paths remain hard differences. Complete old/new query-plan differences are retained rather than silently omitted.

Using the saved failed-v1 generation and its reconstructed 80-file native map, the new diagnostics correctly report `hard_inputs_match: true` while retaining **exactly the original 100 profile-field mismatches** and **50 native-score-file/reference differences**. This checks the intended distinction without changing the old v1 condition. Since the failure archive lacks the realized query-plan receipt, this metadata test used an explicitly empty synthetic query-plan fixture solely to verify retention; it did not fabricate or claim reconstruction of the failed run's actual threshold hashes.

Fourteen independent metadata mutations were rejected: changed native raw CSV, dataset index, result template, missing score file, extra score file, labels, selection digest, case length, case order, profile dtype, profile shape, model order, row order, and a raw mismatch only in the second reference. These were pure dictionary checks, with no metric execution.

`reference_diagnostics` is not itself a raw-data parser. Its typed-input guarantee relies on the unchanged, mandatory independent auditor: that auditor verifies the bound selection digest, raw-member hashes, float64 observations and int8 labels, raw-array bytes, and bit-preserving native CSV decoding before freeze. Native dataset byte equality against both priors then provides an additional hard check. I traced this dependency rather than treating the helper's name or passing unit tests as proof. **No additional raw/typed-input hole was found in this complete mandatory path.** Separate independent review of the full v2 implementation and the eventual saved run remains necessary.
