# Independent strengthening audit — 2026-10-24

The weighted Mac v2 output audit passes. The native input read-back covers all 26 recordings and 52 score profiles. The new reusable input auditor has passed static syntax and interface review; its execution is pending the clean Linux replay or an explicitly coordinated gap in Mac timing. Ongoing TimeEval consumer results were not inspected for this review.

The review covers `experiments/weighted_range_study.py`, `experiments/audit_weighted_range_study.py`, the frozen workload receipts, the new `experiments/audit_strengthening_inputs.py`, and the clean replay driver. No detector or metric implementation was imported for the separate reconstruction of weighted aggregate ratios. No frozen discovery or workload receipt was modified.

## Weighted protocol and reconstructed results

The v2 protocol binds the producer, kernel, comparator implementation and statistical auditor by SHA256, records bootstrap seed 20261024, and prefers portable cache paths. Static review found no remaining execution blocker in the paired-order interval implementation. Within each case, the same six resampled trial indices are applied to both methods and all twelve semantic settings. The method medians are recomputed before forming log ratios; case and semantic weights remain fixed. Recording reweighting is reported separately as sensitivity.

The saved-output audit at `artifacts/pvldb-research-20261024/strengthening/weighted-mac-v2/independent-report.json` verified 11,232 records, 156 curve files and all 26 cases. The maximum complete-curve discrepancy was **2.4980018054066022e-15**, with **zero method winner disagreements**. A separate calculation from `records.jsonl`, using `statistics.median` and `math.fsum`, reproduced all nine aggregate speed ratios within relative/absolute tolerance 1e-13.

Each speed ratio is control time divided by candidate time, with equal log weight across the twelve semantic settings. The intervals below are the prespecified approximate paired-order intervals with adjustment across the three collections for each comparison.

| Collection | Query contract | Control → candidate | Ratio | Paired-order interval |
|---|---|---|---:|---:|
| WSD | grid100 | compiled raster → bucket | 1.526 | [1.518, 1.530] |
| Stock | grid100 | compiled raster → bucket | 1.621 | [1.609, 1.628] |
| MSL | grid100 | compiled raster → bucket | 1.559 | [1.542, 1.573] |
| WSD | grid100 | comparison-sort sweep → bucket | 1.500 | [1.493, 1.506] |
| Stock | grid100 | comparison-sort sweep → bucket | 1.318 | [1.308, 1.327] |
| MSL | grid100 | comparison-sort sweep → bucket | 1.096 | [1.082, 1.140] |
| WSD | observed distinct | compiled raster → comparison-sort sweep | 8.801 | [8.727, 8.837] |
| Stock | observed distinct | compiled raster → comparison-sort sweep | 22.635 | [22.424, 22.810] |
| MSL | observed distinct | compiled raster → comparison-sort sweep | 1.385 | [1.362, 1.427] |

The MSL distinct-threshold comparison contains a material failure: sweep wins on only one of its two recordings. Its recording-reweighting interval is [0.558, 3.438]. The positive aggregate timing ratio therefore does not imply a per-recording win.

Grid-to-distinct detector selection differs only for one recording under middle bias with cardinality one. Its regret is 0.00141219497462175. No semantic contract has a recording with regret at least 0.01. This workload provides little evidence of a large detector-selection benefit.

The query contract uses strict `score > threshold`; observed-distinct queries exclude the below-minimum/all-positive state. Report the maximum **over all observed thresholds**, rather than an unrestricted maximum over every real threshold. Curve agreement here is a saved-output consistency check; the mathematical oracle remains a separate test suite.

The paired-order intervals condition on this panel and host. Six deliberately balanced orders provide limited execution-variability evidence. Recording-reweighting intervals do not establish population coverage. Corrections of 36 for semantic comparisons and 3 for aggregates apply separately to each prespecified control/candidate comparison, not jointly to all three comparison types. With 10,000 resamples, the most extreme Bonferroni tail uses roughly seven order statistics; finite-sample coverage is not established.

## Workload and native input provenance

The cohort was fixed before scoring: WSD 12, Stock 12 and MSL 2, totaling 386,447 rows. Original public FFT and COPOD APIs produced all 52 profiles successfully, with no replacement or repeated fit. Model order is FFT, COPOD. Original score values, including ties and zeros, were preserved. Native `anomaly_scores.ts` text uses sufficient decimal precision for exact binary64 read-back.

Historical identities:

- Selection SHA256: `ed9eb0e9d906c3bd321bf6446cb4bfbbabdeddef154e17fa8ef1fb2f9e5e196c`.
- Workload protocol SHA256: `b1134f125ab7eba4c5acb6b8c2f1450f44b215de3b5860456592d79a99708a71`, frozen before the first fit.
- Generation receipt SHA256: `4177f82b6bfe404f82439d75b749adb16b21a416321425326da2611115f02568`.
- Completed native input read-back SHA256: `f906252900d53e74b3479a04fd600f0475a7061dda07c3f366bb64ff273069c6`, archived as `strengthening/provenance/native-input-audit.json`.

That completed read-back verified all combined NPZ hashes and portable paths, all 26 labels through actual TimeEval `MultiDatasetManager` and `load_labels_only`, all 52 result identifiers, and bitwise equality of native score text with the combined score arrays. It evaluated no metrics.

The last metadata assembly in the original Mac run failed because the shared `.cache` symlink resolves outside the worktree. All detector fits and native score serialization had already finished. The exact producer was preserved with SHA256 `ddd84a1fa99db2f9aa240acfc1292abc31bd668f8a522e68e66ef9947deb7b65`; only relative-path serialization was fixed. Metadata was assembled from existing verified outputs, without fitting again. The immutable generation receipt documents the recovery, including the loss of in-memory parent subprocess durations/stdout/stderr. Worker fit durations and score identities remain available.

`strengthening/provenance/mapping.json` connects historical cache paths to tracked producer, recovery, source-manifest and native-audit artifacts. `workload-replay-descriptor.json` verifies those retained identities and invokes the current fixed generator with fresh cache/protocol/generation paths. New runs pin their current producer prospectively and execute no historical recovery script.

## Clean replay checks and remaining gate

The new reusable auditor independently checks original archive/member bytes, raw observation and label hashes, frozen selection, all upstream sources, all raw/combined NPZs, worker receipts, templates, and all native score vectors. It imports actual TimeEval dataset readers from the supplied complete source tree, verifies twelve pinned source anchors, and records the full source-tree hashes. Historical generation uses the preserved producer with a hash-bound mapping fallback; clean generation verifies the current producer. Its status, coverage and generation-hash fields match the frozen consumer runner interface.

Five targeted boundary tests cover changed source bytes, signed-zero score corruption, historical archive fallback and tampering, clean-producer substitution, and duplicate input identifiers. The tests were written before implementation; post-implementation execution is pending the coordinated validation window. The full new auditor has likewise not yet been executed, so its added original-archive checks are not reported as a completed independent replay.

Static review of `experiments/reproduce_strengthening.py` found the expected clean source, archive, generation and native-reader paths compatible with this auditor. The reported no-pip fallback defect is resolved: the driver now selects matching `pip` or `uv pip` commands for both installation and environment capture. Copying the complete small tracked provenance directory also preserves the historical recovery in the generated output bundle; retaining only its source-manifest leaves the other historical artifacts in the source checkout.

The first fresh Linux attempt, [CI run 40078063128](https://github.com/mandu5/sparse-vus/actions/runs/40078063128) from commit `f67c27e9890317eab8ac2f6fbf2f8a7836db44b0`, failed at 08:27:47 UTC on the compressed TimeEval archive SHA256 check. Source extraction, installation, tests, score generation and metrics had not started. This supplies no input-auditor pass or failure evidence. The acquisition repair replaces the compressed-transport assumption with exact source-tree path membership and file-byte validation against the frozen 425-file manifest, while retaining the actual downloaded transport hash. The pinned `_version.py` was independently fetched from the public revision and matches the frozen source hash, so it is not a Mac-only generated file. The input-auditor tests and full fresh input audit remain required before any fresh-host timed studies.

The previously recorded exact-label, exact-observation and rounded z-normalized observation reuse checks exclude array identity matches against earlier panels. Source families overlap earlier work, and shared physical recordings, crops, channels or dependent sources are not ruled out. MSL has only two recordings. WSD and Stock raw licenses remain unresolved; raw observations and generated score arrays stay in the private cache. Fresh host results should retain their own score identities and timing receipts, without pooling host timings.
