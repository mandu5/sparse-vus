# Mac native TimeEval compiled-control audit, 2026-10-24

Independent artifact audit passed. All 144 planned workflow records completed; there were no timeouts or prespecified skips. Every completed result contains all three finite native metric values. The maximum scalar discrepancy across available compiled outputs is 3.3306690738754696e-16. All 52 profiles are covered by raster, interval, and bucket in both query contracts.

The conventional interval baseline rebuilds predicted intervals at every query and uses closed-form overlap sums. It is a separately frozen comparator, not an unchanged public implementation. No public range implementation was evaluated in this supplemental run; every retained public-reference flag is false. This study therefore adds no public-reference coverage to the earlier 28/52-per-contract result. Native ROC_AUC and PR_AUC remain unchanged in all methods.

The table gives absolute median workflow times across six completed runs. Ratios are geometric means of six matched-order ratios, with the frozen approximate paired-order 95% bootstrap interval; they are not ratios of the displayed medians. Intervals describe execution variability and order sensitivity on this fixed workload, not new-recording or deployment populations.

| Contract | Batch (profiles) | Raster median s | Interval median s | Bucket median s | Interval / bucket | Raster / bucket | Raster / interval |
|---|---|---:|---:|---:|---|---|---|
| native_default50 | combined (52) | 1.068593 | 1.099129 | 1.042946 | 1.0434 [1.0163, 1.0675] | 1.0264 [0.9980, 1.0493] | 0.9837 [0.9734, 0.9997] |
| native_default50 | family-0-MSL (4) | 0.031096 | 0.031487 | 0.031773 | 1.0274 [0.9701, 1.1341] | 0.9797 [0.9524, 1.0130] | 0.9536 [0.8884, 0.9986] |
| native_default50 | family-1-Stock (24) | 0.499825 | 0.527677 | 0.500403 | 1.0506 [1.0217, 1.0769] | 0.9984 [0.9768, 1.0179] | 0.9503 [0.9403, 0.9593] |
| native_default50 | family-2-WSD (24) | 0.544289 | 0.553474 | 0.537515 | 1.0318 [1.0109, 1.0558] | 1.0154 [0.9960, 1.0369] | 0.9841 [0.9671, 1.0011] |
| all_observed | combined (52) | 2.947365 | 3.275430 | 1.072635 | 3.0341 [2.9897, 3.0754] | 2.7317 [2.6558, 2.8120] | 0.9003 [0.8860, 0.9153] |
| all_observed | family-0-MSL (4) | 0.033095 | 0.032963 | 0.030500 | 1.2409 [1.0633, 1.6316] | 1.1003 [1.0552, 1.1404] | 0.8867 [0.6819, 1.0370] |
| all_observed | family-1-Stock (24) | 1.872416 | 2.237153 | 0.508993 | 4.4517 [4.3488, 4.5673] | 3.7425 [3.6502, 3.8559] | 0.8407 [0.8298, 0.8535] |
| all_observed | family-2-WSD (24) | 1.053025 | 0.982892 | 0.560502 | 1.7392 [1.7061, 1.7659] | 1.8657 [1.8098, 1.9072] | 1.0727 [1.0583, 1.0837] |

At nominal default sampling, the combined interval/bucket ratio is 1.0434 [1.0163,1.0675], but the faster raster control gives only 1.0264 [0.9980,1.0493]. Thus the default workflow still supplies no supported improvement over the strongest measured combined compiled control. This is consistent with low query counts and costs outside the replaced range kernel; the study does not provide a timed stage decomposition.

At all observed thresholds, the combined ratio is 3.0341 [2.9897,3.0754] against interval and 2.7317 [2.6558,2.8120] against raster. The exhaustive workflow advantage survives the conventional interval control. Interval is not universally faster than raster: it wins the exhaustive WSD comparison (raster/interval 1.0727 [1.0583,1.0837]) but loses the combined and Stock comparisons. Report both frozen comparators rather than treating the interval baseline as uniformly stronger.

The exhaustive interval/bucket ratios are 1.2409 [1.0633,1.6316] for MSL, 4.4517 [4.3488,4.5673] for Stock, and 1.7392 [1.7061,1.7659] for WSD. MSL represents only two recordings/four profiles and remains a narrow scope claim. The same six-order protocol was applied to every batch; no cross-contract or cross-study timing ratio is computed.

Native default max_samples=50 emits 2,776 total queries, and all-observed evaluation emits 71,749. The two contracts retain their own query sets and synthetic endpoints. Whole-workflow timing includes native dataset/results/score CSV reads, ROC_AUC, PR_AUC, RANGE_PR_AUC, and final results.csv write/close. Imports, source/input audits, tiny JIT warmup, template copying/filtering, and post-run output audits are excluded.

Evidence: `artifacts/pvldb-research-20261024/strengthening/timeeval-control-mac-v1/independent-output-audit.json`, `timeeval-control-global-v1.json` (SHA-256 `7d1b8bd0528bec0d10750ba823f3f0b503dc9790959283fbe55c297cea2811be`), and all raw trial/metric/summary/completion receipts. The independent auditor re-hashed source files, original inputs, trial score copies, completed result CSVs, and both auditor sources. It reconstructed all intervals from raw records without importing the runner, metric candidates, TimeEval, or prts and without evaluating any metric. No protocol-bound source was modified.
