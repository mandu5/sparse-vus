# Advancement experiment review

Date: 20 October 2026. Reviewer: independently assigned automated agent in the
same development session. Scope: read-only review of
`experiments/benchmark_advancement.py`, `experiments/analyze_advancement.py`,
their input-selection artifacts, the fast-VUS adapter, and the result interface
of `src/sparse_vus/certified.py`. No timing kernels or CPU-heavy tests were
executed during this review. This is not external scientific peer review.

## Initial findings requiring closure

1. **Important: aggregate PASS can coexist with wrong certified decisions.**
   `analyze_advancement.py` initially initializes `report["status"] = "PASS"`
   and never rejects positive `incorrect_certified_pairs` or
   `incorrect_certified_winners`. Those counts are recomputed by
   `certify_rankings`, but they do not gate the final report. Reject the report
   if either count is nonzero. This is a validation defect, not evidence that an
   actual measured decision is wrong.

2. **Important: the analysis gate trusts stored correctness checks.**
   Initial `read_run` checks the raw-result hash, number and uniqueness of cases,
   selection hash, repetitions, positive finite call durations, and medians.
   It does not read `environment.json`, verify its protocol/source bindings,
   require the mode-specific method set, or independently recompute parity,
   interval ordering, containment, tolerance, midpoint error and width metadata.
   A raw hash establishes identity with a receipt, not the truth of its PASS
   label. Recompute these conditions before reporting outcomes.

3. **Important: numeric ranking margin is smaller than the combined audit
   allowance.** Containment permits `1e-10` error per model, while pair decisions
   use a `1e-10` interval gap. Two allowed errors can add to `2e-10`.
   For example, exact A = `0.50000000001`, singleton interval A =
   `0.49999999992`, exact B = `0.5`, singleton interval B =
   `0.50000000008` pass the individual containment check but falsely certify B
   above A. Use a decision margin at least twice the containment allowance, or
   retain a strictly empirical interpretation and reject any observed wrong
   decision. The real-arithmetic theorem and a floating-point validation margin
   are different guarantees.

4. **Important provenance gap: baseline inputs are not yet bound to the
   original release locks.** Initial `Corpus` verifies score bytes against
   download receipts and labels against old benchmark row hashes, but does not
   first verify those receipts or the original benchmark against the recorded
   release locks. Bind the original JSONL/receipt, model manifests, download
   receipts, data hash locks and 42-series selection artifact. Verifying the
   sorted score-member manifest hashes in `data_hashes.json` is sufficient;
   do not claim a whole-archive digest for partially downloaded ZIP files.

5. **Minor: platform names are taken from argument positions.** Initial analysis
   labels runs `macOS-arm64` and `Linux-x86` without validating the environment's
   platform and architecture fields. Reject a mismatched environment or derive
   the labels from observed metadata.

These findings were sent to the implementer before result reporting. They are
fail-closed artifact-validation improvements; they do not identify a timing
measurement or arithmetic aggregation error in the planned comparison.

## Coverage and timing review

A separate stdlib-only metadata reconstruction confirms:

- Baseline: 2,100 unique model/width cases, 350 series, 23 families.
- Certified evaluation: 42 unique selected series × three models × widths
  30, 100 and 300 = 378 unique cases; 126 cases at each width.
- Each tolerance is evaluated on every selected case; the two tolerances do
  not create additional independent datasets.
- Per width, ranking analysis has 42 three-model selection cases and 126
  unordered model pairs.

The selection is the previously recorded shortest/median-length source-family
selection, without score-based replacement. It is appropriate for a bounded
cross-family evaluation, but it is not a representative random sample of all
series lengths. Larger selected maximum widths are deliberately different from
the original public benchmark; comparisons at those widths must use the fresh
same-input exact calls, as the harness does.

The timing loop randomizes method order within each repetition, uses three
repetitions, sets one thread before importing numerical packages, excludes
warmup and serialization, and includes validation/preparation inside each timed
call. It passes the same labels/scores/width to competing methods. The sparse
exact and certified methods both start from raw arrays, so reusable prepared
objects do not give only one method an unreported advantage.

The fast-VUS adapter executes the pinned upstream module unchanged. The
benchmark explicitly supplies `max_samples=len(y)` rather than its approximate
250-threshold default. The external implementation returns PR only, whereas
sparse exact returns both ROC and PR. This extra sparse work must be disclosed;
the comparison does not advantage sparse evaluation by reducing its output.
Full-array score sorting, support work and integration remain inside the
external timed call.

The input cache is outside timing for all methods. That supports a metric-only
evaluation claim. It does not measure I/O, model inference or complete anomaly
detection workflows. Three repetitions provide a limited timing sample; all
losses and per-case values should remain visible.

## Aggregation review

The ratio orientations are correct:

- Baseline: comparator seconds divided by sparse-exact seconds.
- Certified: sparse-exact seconds divided by certified-method seconds.

In each case values above one favor the proposed method. `fastest_tested`
uses the minimum competing median separately for each input, which is a
conservative comparator selection. It is distinct from selecting one global
baseline by its aggregate speed.

The geometric means and percentile cluster bootstrap correctly resample
complete series/family groups by log-ratio sums and group sizes. Family
resampling preserves observation-weighted contributions within each selected
family; it is not an equal-family macro mean. Intervals remain descriptive
fixed-corpus uncertainty summaries. Reusing the seeded draw pattern across
comparisons is acceptable and does not constitute independent replication.

`median_unique_width_fraction` and `median_curve_evaluation_fraction` correctly
distinguish unique queried widths from work repeated after cache eviction.
The latter can exceed the former and can exceed one. Claims of computational
savings must use actual time or total curve evaluations, not unique widths
alone.

Pair enumeration and unique-winner definitions are correct under ordered,
valid intervals. All models must be present exactly once per series/width;
three rows alone do not establish the intended three model identities, so the
input gate should enforce the prescribed model set.

## Padding claims and source attribution

The original fixed vectors come from KU Leuven RDR dataset
[`10.48804/MCVI4N`](https://doi.org/10.48804/MCVI4N), version 1, with the pinned
README available in `cache/score-archive-README.txt` (SHA-256
`595fe740b433ffe355ae7a72700a50bed4bf98e2aac7f45816eb29081b4a4e94`).
The README explicitly documents leading-zero padding for Chronos-Bolt and
TimeMoE and says the source authors corrected it to the first available score.

This audit directly verified all 350 selected vectors of each documented model
have exactly 64 initial zeros. The companion sensitivity experiment retains all
350 series under both fixed corrections:

| Variant | PR reversals / 2,100 pairs | Affected series | Unique-top changes / 700 |
|---|---:|---:|---:|
| Released | 84 | 55 | 50 |
| First-score fill64 | 93 | 59 | 52 |
| Common suffix64 | 95 | 61 | 48 |

The common suffix removes positive labels in 21 series. Thus it changes the
evaluation domain, boundary expansion and threshold ranks as well as eliminating
the initial padded region. Valid manuscript wording is:

> The approximation-induced PR order changes persisted under first-score
> padding correction and on the common context-64 suffix: 93 and 95 strict
> pair reversals, respectively, versus 84 on the released vectors.

Follow that statement with the numerical tie tolerance, common denominators,
and the fact that most differences are small: suffix64 has 44 reversals with
both exact/sample gaps at least `1e-3`, and five at least `1e-2`.
It does not reproduce the source paper's entire model leaderboard or establish
ground-truth model superiority. Refer to
[`experimental_audit_20261020.md`](experimental_audit_20261020.md) and the raw
`artifacts/robustness` records for complete family counts, negative cases and
verification.

## Initial reviewed source snapshot

```text
benchmark_advancement.py 6a3214709b45ad4fd309a4a235aadcc4ab95de33bdb41eabbdc22975d41849a4
analyze_advancement.py   6649e6464a6774921aa08b14c6e33b9e9290f40844aeb8f079173f876e540932
fast_vus_adapter.py     1f0d6c37f1ac751e9f0b0ebb5f669b197927e320bb86fb19a01d3e589769ffd3
certified.py            31135f790070a49d7480f0aa98f9696246cde13aad1410a1daeeb003fe214619
```

This snapshot review does not certify future edited scripts or results not yet
available. Closure requires inspecting the revised gate and the completed raw
receipts.

## Revised gate review

The revised analyzer at SHA-256
`6ce1ae9d450ba86501cd80236b51a7dae569c19d3fcb4a7ae305829a81f24917`
resolves initial findings 1, 2, 3 and 5 in the reviewed source:

- It reconstructs finite exact values, method coverage, ordered intervals,
  containment, tolerance, midpoint values/errors, and queried-width accounting.
- It verifies environment-to-protocol and measured-source bindings and verifies
  observed architecture/platform before assigning platform labels.
- It requires a `2e-10` interval gap and rejects any incorrect certified pair or
  winner before writing a PASS report.

A tiny stdlib-only extraction of the ranking function checked the
allowance-counterexample above: A versus B is now left undecided, neither is
claimed the unique winner, and the two clearly separated comparisons against
C = 0.1 remain certified. No benchmark function was executed.

For finding 4, the benchmark source was already frozen and timing had begun.
A separate post-run gate was therefore implemented in
[`experiments/advancement_data_gate.py`](../experiments/advancement_data_gate.py),
initial SHA-256
`0c94cb61ba42de18f9e4cc488c51319fc1bab3038ea44413ee6b93ed9abdb983`.
Its public function is `validate_advancement_data(rows, mode=...)`.

The gate pins eight original manifest/receipt files to bytes read from release
commit `7565b6657ba510e79db13e79b809b58e77feacc0`; checks the original JSONL
against the pinned receipt; reconciles every score-member receipt with
`experiments/data_hashes.json`; requires the complete mode-specific case set;
and checks every result's length, family, label hash and score hash. It then
reads the selected source ZIP members to verify CRC/SHA-256, finite score
shapes, binary labels and original positive counts.

A metadata-only smoke check passes: 350 series, three models, 1,050 locked
score hashes and the exact 42-series supplemental selection. Source ZIPs have
not yet been reopened by this new gate because controlled timings were running.
The full post-run gate and completed-result checks remain required before
claiming a verified advancement result. This addition must be called a post-run
provenance check, not a check that preceded the measurements.
