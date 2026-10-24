# Mac native TimeEval output audit, 2026-10-24

Independent artifact audit passed. Of 144 planned workflow records, 120 completed, four reached the prespecified 600-second deadline, and 20 were skipped under the frozen first-censor rule. All completed outputs contain all three finite metric values. The maximum available scalar discrepancy is 3.3306690738754696e-16.

The public range implementation supplied complete output vectors for 28 of 52 profiles in each contract (four MSL profiles and 24 WSD profiles). The 24 Stock profiles have compiled-to-compiled checks only in this study. A completed family output can validate the same profile in the combined batch, but it cannot recover the censored combined workflow duration.

The table reports absolute median workflow times across six completed runs where available. Ratios are geometric means of six matched-order ratios with the frozen approximate paired-order 95% bootstrap interval; they are not ratios of the displayed medians. A `>` cell is the sole same-round lower bound from the first public timeout, with no confidence interval. These intervals describe execution variability/order sensitivity on this fixed workload, not a recording or deployment population.

| Contract | Batch (profiles) | Public median s | Raster median s | Bucket median s | Public / bucket | Raster / bucket | Public / raster |
|---|---|---:|---:|---:|---|---|---|
| native_default50 | combined (52) | censored >600 | 1.084799 | 1.078313 | >553.1930 (round 0; no CI) | 1.0168 [0.9982, 1.0392] | >552.3972 (round 0; no CI) |
| native_default50 | family-0-MSL (4) | 0.080078 | 0.031768 | 0.032914 | 2.2188 [1.7075, 2.5760] | 0.8603 [0.6394, 1.0142] | 2.5790 [2.4745, 2.7017] |
| native_default50 | family-1-Stock (24) | censored >600 | 0.489308 | 0.481691 | >1239.8890 (round 0; no CI) | 1.0426 [1.0130, 1.0831] | >1166.6319 (round 0; no CI) |
| native_default50 | family-2-WSD (24) | 5.227309 | 0.554748 | 0.543214 | 9.5982 [9.4378, 9.7738] | 1.0194 [1.0033, 1.0368] | 9.4154 [9.1541, 9.6725] |
| all_observed | combined (52) | censored >600 | 2.946046 | 1.080682 | >563.2614 (round 0; no CI) | 2.7281 [2.6487, 2.8015] | >201.7923 (round 0; no CI) |
| all_observed | family-0-MSL (4) | 0.481519 | 0.033516 | 0.030383 | 15.7406 [14.9038, 16.5752] | 1.0882 [1.0445, 1.1359] | 14.4650 [14.0376, 15.0669] |
| all_observed | family-1-Stock (24) | censored >600 | 1.860338 | 0.504955 | >1107.0931 (round 0; no CI) | 3.5568 [3.3540, 3.7147] | >315.8303 (round 0; no CI) |
| all_observed | family-2-WSD (24) | 234.800625 | 1.075227 | 0.584776 | 407.0986 [398.6492, 416.7125] | 1.8657 [1.8320, 1.9014] | 218.1986 [216.6117, 219.6902] |

The practical boundary is clear: the nominal-default combined workflow shows no supported speed advantage over the compiled raster control (interval includes one). Exhaustive observed-threshold evaluation shows a 2.7281-fold combined advantage over that raster control. A new conventional closed-form interval control is being implemented and must be evaluated separately before attributing this gain to the proposed data structure rather than a weaker compiled baseline.

The two contracts have different threshold sets. Native default `max_samples=50` is nominal and emits 2,776 queries across all profiles; exhaustive observed thresholds emit 71,749. There is no cross-contract speed ratio or threshold-accuracy claim. Each workflow recalculates native ROC_AUC, PR_AUC, and RANGE_PR_AUC and includes dataset/results/score CSV reading and final results.csv writing. Training, imports, tiny compilation warmup, copying, and post-run audits are excluded.

Evidence: `artifacts/pvldb-research-20261024/strengthening/timeeval-mac-v1/independent-output-audit.json`, the frozen global protocol `timeeval-consumer-global-v1.json`, and the run directory’s trial, metric, completion, and summary receipts. The audit re-hashed original source, inputs, trial score copies, and all completed result CSVs; it recomputed the summaries from raw timing records without importing the candidate or running any metric.
