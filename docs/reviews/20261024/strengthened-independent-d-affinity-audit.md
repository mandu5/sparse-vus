# Independent reviewer D: saved affinity-v2 evidence audit

Date: 2026-10-24. This is an independent read-only reconstruction of saved evidence, not a new execution, detector fit, implementation audit, or final scientific recommendation. I did not read other reviewers' reports or scores. The final paper recommendation remains pending its immutable PDF.

## Evidence identity

- Archive: `artifacts/pvldb-research-20261024/strengthening/affinity-linux-v2-replay`.
- Original ZIP: `/tmp/sparse-vus-affinity-v2.zip`, SHA-256 `8d1fd2e2715c8eb4b28c5f1861143766498686aa072a3c72b9d539ca57b6b595`.
- I independently hashed the ZIP and verified that all 697 extracted files exactly match its members.
- Frozen execution source: `d8494c25a8c6fe44616a34bdded375dc3993d048`, tag `strength/affinity-blocks-linux-v2`, run [40091476529](https://github.com/mandu5/sparse-vus/actions/runs/40091476529).
- Frozen protocol SHA-256: `fe5fea9da3262e72f8b79f927db67c3b66cd0d5c1377693417d9c9e92c15536a`.
- All 15 opaque source/document/prior-evidence file bindings match their bytes at the frozen commit. I checked hashes without inspecting the new extension's implementation. The prepared receipt binds the actual protocol, generation, native-input audit, design, and identity-receipt bytes correctly.

## Reconstruction from raw durations

I parsed each block's `trials.jsonl`, matched all 36 entries against the frozen schedule, and independently formed the six paired log time ratios for each contrast. I averaged within each block, then equally across five blocks. I enumerated all 3,125 ordered bootstrap samples of five blocks and took the prospectively specified quantiles 0.00625 and 0.99375. These calculations preceded reading `summary.json`; its reported results subsequently matched.

All ratios below are control time divided by bucket time. The intervals describe this empirical five-session sample; they do not establish finite-sample coverage or generalize to new hosts or workloads.

| Block | Exhaustive raster | Exhaustive interval | Default50 raster | Default50 interval |
|---|---:|---:|---:|---:|
| 0 | 1.906602687 | 2.195395270 | 1.009996920 | 1.019485226 |
| 1 | 1.904621212 | 2.208974038 | 1.012526508 | 1.018226914 |
| 2 | 1.931485113 | 2.226093831 | 1.016864998 | 1.016767379 |
| 3 | 1.933165489 | 2.228829597 | 1.016205321 | 1.025087962 |
| 4 | 1.919437104 | 2.220960003 | 1.028369460 | 1.033537691 |
| Geometric mean | **1.919024946** | **2.216015946** | **1.016773168** | **1.022602648** |
| Adjusted descriptive interval | [1.905809850, 1.932157088] | [2.200816732, 2.227253451] | [1.011235558, 1.024668408] | [1.017350941, 1.030161644] |

All 180 scheduled timed workflows completed. Each block/contract contains all six permutations of the three methods exactly once. Five distinct process IDs (2466, 2478, 2498, 2521, 2530), distinct start ticks, and sequential start/completion receipts substantiate five fresh processes, not five hosts. All report AMD EPYC 9V74 80-Core Processor on the same runner/boot. Every recorded live-thread affinity before each timed call and at block endpoints is `[0]`; every recorded numerical pool has one thread. Process return codes are zero, trace-parse issues and launch errors are empty, and receipt/evidence hashes match actual files. The last child completed at 12:01:04 UTC, after the first launched at 11:53:13 UTC.

For context, medians across the 30 recorded calls per contract/method are 3.070586827, 3.538153466, and 1.595389168 seconds for exhaustive raster, interval, and bucket; corresponding default50 values are 1.601169992, 1.615376983, and 1.571508472 seconds. These are descriptive medians, not the paired-ratio estimator.

## Actual CSV verification

I hashed and parsed all 210 saved `results/results.csv` files: 180 timed outputs plus all 30 full-workflow warm-ups. Each has exactly the same ordered 52 unique identifiers as the frozen protocol, successful status, and finite ROC-AUC, PR-AUC, and range PR-AUC values. Across 32,760 scalar cells, maximum discrepancy within the same contract, over methods, repetitions, warm-ups, and blocks, is:

- Exhaustive: `2.7755575615628914e-16`.
- Default50: `3.3306690738754696e-16`.

All 210 CSV hashes match their recorded bindings. The 180 JSON metric-row records have matching identifiers and values within `1.1102230246251565e-16` of direct standard-library decimal parsing of the CSVs. That tiny parse difference does not affect the cross-CSV parity conclusion. This establishes agreement among the three compiled methods on these outputs; it adds no completed public-reference comparison.

## Input and query identity, including the unexpected result

I directly compared the saved generation/protocol objects with both prior Linux archives, rather than accepting the new identity report's Boolean labels. All 52 per-profile score NPY-file, score-array, and native text-score hashes match both priors. All 26 ordered case identities, label and combined-score hashes, shapes and model order match. All 80 native input-file hashes, including 26 dataset files, their index, 52 score files, and the result template, match. All 52 complete query-plan records and ordered result-row identifiers match. Totals are 2,776 emitted default50 queries and 71,750 exhaustive queries. WSD id6 COPOD has 1,687 distinct values and 1,686 exhaustive nonminimum queries.

Thus v2's one fresh score-generation attempt happened to reproduce both prior Linux realizations exactly, despite its prospectively relaxed score-identity requirement. It should not be described as an observed different score realization. This finding does not retroactively change the design, erase v1, or identify the reason for earlier timing differences.

Scope of direct bytes verification: the private Linux raw-score files are not redistributed in this ZIP. For their full identity I checked the complete bound saved hash/query records. In the available local cache, all 28 non-score native input files and 27 exact matching score files are byte-identical to v2's hashes. I independently reconstructed both native query contracts from those 27 actual score vectors: all 54 threshold counts and binary64 threshold hashes match. The remaining 25 local COPOD files are a different cached realization, so I did not represent their bytes as v2 inputs or fit replacements.

I also inspected the preserved v1 failure receipt and independently compared its profile records: 25 COPOD array/native-score identities differ from the prior Linux realization; WSD id6 changes from 1,687 to 1,686 distinct values. The v1 archive contains no `trials.jsonl`; its recorded failure is in the preparation/freeze command. Its failure remains separately visible. No metric timing from that attempt was used to select v2.

## Scientific implication

This bounded check supports a stable exhaustive native-workflow gain on this runner and these fixed 52 profiles, approximately 1.92× over the strongest raster control and 2.22× over the interval control. The default50 benefit is small even though these particular descriptive intervals lie above one. The experiment does not explain the earlier 1.932× versus 2.756× Linux difference, isolate affinity causally, add detector/domain coverage, establish an exclusive CPU, or validate population-level confidence coverage. No new correctness or evidence-consistency blocker was found in the inspected saved-data scope.
