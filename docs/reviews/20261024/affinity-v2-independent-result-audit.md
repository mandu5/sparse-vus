# Independent saved-result audit A: affinity v2

**Outcome: PASS. The saved archive supports a complete five-process, 180-trial, 30-warm-up study.** Independent reconstruction gives exhaustive raster/bucket and interval/bucket geometric ratios of **1.919025** and **2.216016**. Both default-contract results are much smaller and are retained below. No new scientific recommendation is issued here; the final manuscript review must bind its eventual immutable PDF.

This is an AI-simulated independent artifact/result audit. The auditor read raw trial JSONL and reconstructed all four comparisons before opening the producer's summary. The standalone checker uses only Python's standard library, does not import producer code, and evaluates no metric or detector. No timed study, fit, source adjustment, observation removal, or rerun was performed. Other reviewers' scientific recommendations and scores were not consulted.

## Immutable evidence and audit artifacts

- Experiment source commit: `d8494c25a8c6fe44616a34bdded375dc3993d048`.
- Dedicated tag: `strength/affinity-blocks-linux-v2`.
- Workflow run: `40091476529`, attempt `1`, recorded in the saved start receipt; [run location](https://github.com/mandu5/sparse-vus/actions/runs/40091476529).
- ZIP: `/tmp/sparse-vus-affinity-v2.zip`, SHA256 `8d1fd2e2715c8eb4b28c5f1861143766498686aa072a3c72b9d539ca57b6b595`.
- Extracted evidence: `artifacts/pvldb-research-20261024/strengthening/affinity-linux-v2-replay`.
- Frozen protocol SHA256: `fe5fea9da3262e72f8b79f927db67c3b66cd0d5c1377693417d9c9e92c15536a`.
- Independent checker: `experiments/audit_affinity_v2_saved_a.py`, SHA256 `1925239ba3ccf4cbbc4c03b354b7c42dc5588de5fb1126329a5e757c5102652b`.
- Detailed reconstruction: `artifacts/pvldb-research-20261024/strengthening/affinity-independent-a-v2.json`, SHA256 `7018d63a50794fc9ddbc0ea660e8e0140fae805982f4ef5168c278c965b2db3e`.

The ZIP digest and byte equality of all **697 extracted files** were independently verified. Eleven committed preparation/orchestration bindings, fifteen protocol file bindings, and eleven native project-source bindings were checked against the frozen source commit. These groups overlap; they are not 37 distinct source files. Protocol, input-audit, generation, prepared, per-process, per-block, completion, scalar-output, and producer-summary hash links were checked. The checker refuses to overwrite its output file.

## Complete population and process controls

The artifact contains exactly five planned blocks, each with all 36 planned trials in their frozen order. Every contract/block contains all six method permutations. Every trial matches its planned block, trial, contract, round, position, method, combined batch, and 52-row population. All **180 statuses are `COMPLETE`**, with finite positive durations; there are no timeout, error, invalid-output, or missing-trial substitutions. Six full warm-up results are retained in each block, giving **30 warm-ups** and **210 scalar CSV outputs** overall. No additional unreferenced result CSV was found.

Five distinct child PIDs and process-start tick values were checked: `2466`, `2478`, `2498`, `2521`, and `2530`. Their parent, host, boot identity, successful exits, protocol arguments, and bound completion receipts agree with the supervisor. The recorded runner CPU is **AMD EPYC 9V74 80-Core Processor**. Every child uses the same permitted logical CPU **0**, chosen from the supervisor's set `{0,1,2,3}`. All **190** live-thread snapshots—before each measured trial and at every block's start/completion—contain two live threads, both confined to CPU 0. Reported numerical pools have one thread and the required thread environment is recorded. This does not reserve an exclusive physical core or control unrelated host load.

Generation completed at 11:53:10 UTC on 24 October 2026, input verification at 11:53:12, and the affinity protocol was frozen at 11:53:13. The saved run completed at 12:01:05. The bound source and receipt chronology place the freeze before child warm-ups or timings. Generation occurred once, outside the five measured process blocks.

## Score and query relationship independently checked

The realized v2 inputs were compared directly through their saved, bound metadata with **both** earlier Linux references. This conclusion was independently recomputed rather than assumed from a coordinator or producer summary:

- All **52 score-array hashes** and all **52 native-score-file hashes** match each reference: zero differences.
- The entire **80-file native input map** matches each reference, including datasets, templates, and scores.
- The complete **52-profile realized query plan** matches each reference, including exact threshold-vector hashes, counts, row identities, and constant-score shortcuts.
- The selected recordings, raw-member and typed-observation/label hashes, dataset hashes, and ordered native layout match both references.
- Independently applying the pinned sampler's count rule to the recorded distinct-score counts reproduces **2,776 nominal-default50 queries** and **71,750 all-observed queries** across the 52 profiles. These are realized counts; nominal 50 is not a hard per-profile cap.

V2 prospectively permitted a new score realization. Its first generation happened to reproduce the previous score/query identities; the frozen design did not require selecting a generation that did so. This observed equality strengthens the concrete input comparability of this execution without changing its prospective scope or proving a hardware explanation.

Raw observation and score vectors are not redistributed in this archive. Accordingly, this audit verifies their recorded hash identities, binding to the independent input-audit/generation receipts, profile cardinalities, and derived sampler counts. It **does not independently rehash unavailable score arrays or rederive nonempty threshold-vector hashes from their values**. The unchanged runtime's bound input checks before and after every block provide the recorded execution link. This distinction is retained in the JSON audit.

## Scalar output reconstruction

All **210 result CSVs** were independently rehashed and parsed with the standard-library CSV reader. Each has exactly the frozen 52 row identities in order and three finite scalar outputs, for **32,760 inspected scalar values**. The 180 measured outputs also agree with their saved metric-trace identities and scalars; the largest CSV/trace parsing difference is `1.1102230246251565e-16`.

Every same-contract output pair was compared, including all methods, orders, warm-ups, and blocks: **2,100 within-block pairs plus 8,820 cross-block pairs**, totaling **10,920**. The maximum scalar difference is **`3.3306690738754696e-16`** both within and across blocks, below the frozen absolute tolerance `1e-10`. This is parity among the three compiled implementations. No new public-implementation parity or profile coverage is supplied by this experiment.

## Independently reconstructed statistics

Ratios are control duration divided by bucket duration, so values above one favor bucket. For each contrast, six matched log ratios are averaged within a block; the five block means then receive equal weight. I reconstructed the empirical bootstrap using the **126 multinomial count configurations** with multiplicities `5! / product(count!)`, totaling **3,125** samples. This is independent of the producer's ordered-sequence enumeration. Endpoints use probabilities `0.00625` and `0.99375`, the specified four-contrast Bonferroni tail adjustment.

| Query contract | Control / bucket | Geometric ratio | Descriptive adjusted interval |
| --- | --- | ---: | --- |
| Native default50 | Raster | 1.016773 | [1.011236, 1.024668] |
| Native default50 | Interval | 1.022603 | [1.017351, 1.030162] |
| All observed | Raster | 1.919025 | [1.905810, 1.932157] |
| All observed | Interval | 2.216016 | [2.200817, 2.227253] |

All five block estimates are preserved:

| Block | Default raster/bucket | Default interval/bucket | Exhaustive raster/bucket | Exhaustive interval/bucket |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 1.009997 | 1.019485 | 1.906603 | 2.195395 |
| 1 | 1.012527 | 1.018227 | 1.904621 | 2.208974 |
| 2 | 1.016865 | 1.016767 | 1.931485 | 2.226094 |
| 3 | 1.016205 | 1.025088 | 1.933165 | 2.228830 |
| 4 | 1.028369 | 1.033538 | 1.919437 | 2.220960 |

The detailed JSON preserves every paired-order ratio and per-block geometric workflow duration. Both exhaustive controls favor bucket in **30/30 matched orders**. Each default control favors bucket in **26/30 orders**; the four contrary orders in each contrast remain included. The exhaustive raster block range is `[1.904621, 1.933165]`, while the interval range is `[2.195395, 2.228830]`. No extreme block or order was trimmed.

Only after these independent estimates were obtained did I read and compare the producer summary. All four point estimates, block estimates/ranges, and interval endpoints agree to a maximum absolute difference of **`4.440892098500626e-16`**. A separate synthetic known-ratio check verified the auditor's means and endpoints against direct ordered enumeration, including retention of an extreme fifth block.

These are nominally adjusted **descriptive small-sample percentile intervals**. Five sequential processes on one shared runner are not independent hosts or workload populations. The bootstrap enumeration is exact for its empirical resampling distribution; it does not establish exact or guaranteed confidence coverage.

## Interpretation and preserved limits

The finite result supports a consistent exhaustive-workflow advantage over both compiled controls on this fixed runner and workload. It also preserves the practical limitation: default-contract gains are only about **1.017× and 1.023×**. The controlled exhaustive ratios are smaller than the earlier supplemental Linux aggregate, so the manuscript must retain the full range of executions and avoid presenting this study as confirmation of a universal 2.756× or 3.190× gain. No causal attribution for earlier variation is supported.

V1 remains **failed preparation with zero measured blocks**. Its ZIP, thirteen extracted failure files, four original source files, and the immutable original final review A were rechecked and remain unchanged. V2's realized score equality does not retroactively complete v1 or erase the earlier cross-environment regeneration failure. The v1 failure/design audit remains `docs/reviews/20261024/affinity-v1-failure-v2-design-audit.md`.

This completes the saved-result check for the authorized finite v2 execution. It supplies no new conceptual novelty and is not a final review of an as-yet-unfrozen manuscript. No additional timing run is required to validate this completed protocol's saved result.

## Reproduction of this audit

Use a new output filename; the command reads the evidence and writes only the audit JSON:

```sh
python3 -B experiments/audit_affinity_v2_saved_a.py \
  --archive artifacts/pvldb-research-20261024/strengthening/affinity-linux-v2-replay \
  --zip /tmp/sparse-vus-affinity-v2.zip \
  --out /tmp/affinity-independent-a-v2-recheck.json
```

The executed audit returned `PASS_COMPLETE_SAVED_ARTIFACT_RECONSTRUCTION`. The original evidence and runtime files were not edited.
