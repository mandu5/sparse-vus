# Prospective v2: fixed new score realization across five process sessions

Written after the v1 preparation failure and before any v2 generation or metric
execution. This is a separately scoped follow-up, not a waiver or completion of
v1. Frozen v1 source `ee3031aafb5cc30c7928d36e965d2156cf3ac2ca`, tag
`strength/affinity-blocks-linux-v1`, workflow
<https://github.com/mandu5/sparse-vus/actions/runs/40090142426> remain intact.

## Observed preparation failure

V1 completed 52 detector fits and the independent native-input audit of 26
recordings. Its strict score-identity gate then failed before any metric,
warm-up or timed workflow. Against each prior Linux realization, 25 COPOD
profiles differed in both array and native-score hashes. All 26 FFT profiles
and COPOD on MSL id7 matched. WSD id6 COPOD had 1,686 rather than 1,687 distinct
scores. No score-value distance, harmless-roundoff explanation or hardware
causation is established. All raw/native datasets, labels, rows and templates
matched. The failed archive is `strengthening/affinity-failed-v1`; its measured
block count is zero. No timing outcome was observed when revising this design.

## Revised estimand and mandatory gates

Does the compiled-control advantage persist across five fresh processes on
one runner for the same 26 recordings and one newly generated fixed set of 52
FFT/COPOD profiles? This evaluates within-host process variability for a new
score realization. It is not a replay of the prior scores, does not explain
their 1.932/2.756 ratio difference, and adds no new public-reference coverage.

- Make exactly one whole generation attempt. If any fit fails or is missing,
  abort preparation; no retry-until-complete, replacements, exclusions,
  rounding, or selection using hashes, cardinalities, outcomes or runtimes.
- Preserve the pinned source/dependency versions, raw-archive SHA, source-bound
  typed-input decoder and independent no-metric native input audit. Require
  selection, ordered recordings, labels, shapes, model order, native dataset
  bytes/index, result-template bytes and row layout to match both priors.
- Require the identical native input-file key set. Only the existing 52
  `anomaly_scores.ts` contents and their derived array/query identities may
  differ from the priors. Retain every score/hash and complete old/new query
  plan difference diagnostically; no acceptance threshold uses their values.
- Freeze the actual fresh score-file hashes, generation/input-audit hashes,
  exact threshold hashes/counts, runtime sources and orchestration before any
  warm-up. The unchanged runtime verifies those frozen files before and after
  every block; every method/block uses the same current score realization.

## Unchanged finite experimental design

Use the same native flat/cardinality-one range PR-AUC, ROC-AUC and PR-AUC
CSV-read/metric-compute/result-CSV-write boundary. Raster, interval and bucket
controls, both native-default50 and all-observed contracts, and all five
blocks use exactly v1's seed2026102405 schedule: six balanced method orders
per contract, 36 timed workflows/block, 180 total. In each fresh process pin
the same lowest permitted logical CPU before numerical imports; verify all
live threads and one-thread numerical pools. This is not an exclusive core.
Use the unchanged tiny JIT warm-up and six full untimed method/contract
warm-ups per block. No fit is repeated inside the five blocks.

Keep all observations/outliers/failures. Attempt all five blocks, with no
replacement or additional study after seeing a result. Retain the 600-second
call deadline and 90-minute overall job cap. Missing final receipts, invalid
output, affinity/hash violations or incomplete processes invalidate the
affected whole block. Timeouts suppress affected incomplete contrasts. Saved
CSV scalar parity includes warm-ups, all methods/orders and all five blocks;
cross-block failure prevents five-block inference.

For the four frozen contrasts (raster/bucket and interval/bucket under each
contract), average six paired log ratios within each block and equally average
five block means. Enumerate all 3,125 empirical block-bootstrap sequences,
with tails .025/4 and 1-.025/4. Report all five estimates. These are descriptive
small-sample intervals, with no guaranteed coverage or new-host inference.

New files, schema, protocol name, output namespace and dedicated tag
`strength/affinity-blocks-linux-v2` distinguish the revision. Require an
independent code audit, commit/source freeze, then one explicitly tagged
execution. Preserve a negative/incomplete result as well as a positive one.
After independent result reconstruction and the final manuscript audit,
proceed to the authorized PVLDB submission; do not seek a larger ratio.
