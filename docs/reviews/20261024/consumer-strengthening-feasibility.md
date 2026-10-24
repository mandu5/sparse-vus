# Consumer strengthening feasibility — 2026-10-24

Recommendation: prioritize the actual three-metric TimeEval recalculation workflow with its existing `RANGE_PR_AUC` configuration (`alpha=0`, `cardinality="one"`, `bias="flat"`). Keep the TSB-AD range-only replacement as an Amdahl-limited control. Treat Affiliation acceleration as an established-formula engineering control, not as a new metric algorithm. No timing or full consumer execution was performed in this feasibility task.

## Evidence and scope

- Existing TSB consumer: `experiments/pvldb_consumer.py`, pinned TSB-AD revision `303dffbfc11612995b17b06633f8c9d0ea0e38e5`. The current experiment substitutes the exact VUS pair at a scalar boundary while retaining all nine output keys and the seven other upstream metrics.
- Existing results: `artifacts/pvldb-research-20261024/public-consumer/workflows.jsonl`; exploratory component profile: `tmp/consumer-metric-profile.json`.
- New TimeEval source pin: `7c3622757b1a3afa9a84cbc97ce132d9e379f715`. Source, licensing and prototype hashes: `artifacts/pvldb-research-20261024/strengthening/timeeval-source-feasibility.json`; dataset schema hashes: `timeeval-schema-feasibility.json` in the same directory. The cache is selected source files, not a complete installation.
- No other reviewer scores were read. CodeGraph was not exposed in the available tool metadata; inspection was limited to the specified consumer and its direct metric dependencies.

## Three substantive routes

| Route | Output-preserving change | Scientific role | Status |
|---|---|---|---|
| 1. Replace existing range metric | Replace TSB `metric_RF1` inner evaluations on the same 100 strict thresholds with the range sweep, using `alpha=.2` and `tsb_compat=True` | Direct application of the range algorithm; retain limited whole-consumer benefit | Contract identified; nine tiny boundary fixtures agree exactly with upstream range outputs |
| 2. Accelerate Affiliation with established formulas | Cache ground-truth events and zones, omit unused distance outputs, replace all-pairs interval partitioning by an ordered interval join, retain the published probability kernels | Strong engineering control for the dominant cost; closed-form/JIT itself is not novelty | Tiny probability and scalar-oracle fixture parity is exact; no measured speedup |
| 3. Share statistics across threshold queries and metrics | Reuse a single score/threshold event schedule, point counts, true-event maxima and predicted-component state for PA/Event/range metrics; preserve each metric's own threshold and reduction contract | Potential broader algorithmic contribution if the shared-state complexity and incremental update rules are proved and compared with a fused scan | Tiny PA/Event sufficient-statistic prototype agrees exactly; unified optimized kernel not implemented here |

### Route 1: precise TSB range contract and ceiling

`basic_metrics.py:257–284` evaluates exactly `np.linspace(score.min(), score.max(), 100)` in increasing order and predicts `score > threshold`. Recall uses existence weight `.2`; precision calls the same range routine with arguments reversed and existence weight zero. Bias is flat; cardinality is reciprocal; final output is Python `max` over F1 values. The `thre` argument passed to `get_metrics` controls VUS, not these 100 threshold loops.

`range_metrics(..., alpha=.2, tsb_compat=True)[:,2]` is the appropriate replacement. Preserve the sampled threshold grid; replacing it with all unique scores changes the oracle metric. Standard mathematical handling of all-positive binary vectors also changes TSB's parser behavior: the pinned parser returns no ranges for an all-one vector. The compatibility flag is essential outside the frozen mixed-label workload.

Existing ABBA means are 34.260309354 s with the Benchopt exact pair and 33.2339995 s with the radix pair. Mean VUS times are .9288648125 s and .0140595425 s, respectively. The current whole-consumer benefit is about 1.0309×; the VUS stage is a small fraction of this consumer.

The separate exploratory profile sums across eight models are:

| Stage | Existing exploratory seconds | Ideal zero-cost speedup ceiling against 33.2339995 s |
|---|---:|---:|
| Standard-F1 | .034682 | 1.0010× |
| PA-F1 | 3.441986 | 1.1155× |
| Event-F1 | 2.057228 | 1.0660× |
| R-based-F1 | 3.085424 | 1.1023× |
| Affiliation-F | 18.370593 | 2.2360× |
| PA + Event + R-based-F1 | 8.584637 | 1.3483× |

These are conditional Amdahl projections `T/(T-S)`, not new measurements or rigorous bounds for a concurrently profiled run: component and whole-workflow observations came from different passes. The RF1 route cannot reasonably support a large whole-consumer claim on this fixed case. Its scientific value is broader range semantics and direct integration, with the negative application result retained.

### Route 2: Affiliation exactness and prior-art overlap

The pinned TSB Affiliation code already implements the closed-form interval probability integrals from Huet, Navarro and Rossi, *Local Evaluation of Time Series Anomaly Detection Algorithms*, KDD 2022. The independently fetched author implementation at `ahstat/affiliation-metrics-py@8d8449858096bbade6a6e70848d05c9cc9b846fe` differs from TSB's `_integral_interval.py` and `_affiliation_zone.py` only in import paths. A compiled translation of these formulas is an implementation baseline, not a newly derived metric.

Primary sources: [author implementation](https://github.com/ahstat/affiliation-metrics-py/tree/8d8449858096bbade6a6e70848d05c9cc9b846fe), [KDD paper](https://ahstat.github.io/images/2022-anomaly1-kdd-paper.pdf).

The consumer requests only `Affiliation_Precision` and `Affiliation_Recall`, but `pr_from_events` also computes two unused lists of distances. Ground-truth conversion and zones are invariant over the 100 thresholds. Its `affiliation_partition` iterates over every predicted interval for each zone; the nominal filtering list is not actually used to filter its `Is_j` comprehension. An ordered interval intersection removes this Cartesian work without changing the probability formulas.

Contracts to preserve:

- An anomalous point at index `i` is the continuous interval `[i,i+1)`; global range is `(0,n)`.
- Ground-truth affiliation-zone boundaries are neighboring endpoint midpoints.
- Precision averages only zones with defined precision; recall averages all true zones.
- Empty prediction produces precision NaN and recall zero. TSB's last sampled threshold always has empty prediction; Python `max` over the original order generally ignores a later NaN when an earlier finite value wins. A constant score vector produces all NaNs. Do not substitute `np.max` or `nanmax` without validating this behavior.
- F1 denominator adds `1e-15`; nonempty ground-truth events are required by the upstream function.
- Removing distance calculations preserves the consumer's scalar outputs, not the entire public `pr_from_events` dictionary API. Keep the optimization at the scalar consumer boundary.

Prototype `tmp/strengthening-consumer/prototype.py` reuses the pinned probability functions unchanged, caches truth geometry, and performs an ordered interval join. Nine tiny boundary fixtures, including first/last events, all-positive labels and constant scores, yielded zero absolute error for both the probability pair and TSB oracle scalar. This does not establish real-input parity, speed, or an all-threshold Affiliation algorithm.

An incremental Affiliation sweep is a separate research possibility: per-zone predicted length and precision integral are additive; recall is determined by the nearest predicted interval within a zone. Maintaining the changing Voronoi boundaries on insertion/merge would require a proof and matched compiled controls. Do not equate that unimplemented idea with the tested ordered-join prototype.

### Route 3: shared statistics with compatibility boundaries

For a binary label vector, a true event's maximum score determines whether it is hit at any strict threshold. Sorted point scores provide predicted count and TP count without rescanning the vector. Predicted components supply the overlap and fragmentation statistics needed by range precision/recall. A common event schedule can therefore feed several metrics, with query snapshots at their original thresholds.

The tiny shared PA/Event prototype preserves two upstream quirks that a textbook implementation would miss:

1. PA backfill uses `range(i,0,-1)`, so a detected event starting at index zero does not backfill index zero when that point itself is below threshold. For such an event, adjusted TP is its length minus one plus the original prediction at zero.
2. `_get_events` sets a terminal event's inclusive end to `tim-1`; the final point is excluded for Event-F1, while the event remains in the recall denominator. A terminal singleton is an empty detection slice.

The fixture receipt `tmp/strengthening-consumer/tiny-correctness.json` records nine fixtures × nine threshold queries, 333 comparison groups across PA, Event, range, and Affiliation, all with zero observed error. JIT was disabled. These are correctness fixtures, not performance evidence or a main result.

Do not merge metric definitions while sharing computation: TSB Standard-F1 uses scikit-learn's distinct-score `>=` PR curve and an added `1e-5` denominator, AUC-PR is average precision rather than trapezoidal PR AUC, and the other oracle metrics use 100 strict equally spaced thresholds. A shared schedule can implement these contracts, but a single substituted threshold grid cannot.

## Preferred new application: actual TimeEval default recalculation

The [pinned native script](https://github.com/TimeEval/TimeEval/blob/7c3622757b1a3afa9a84cbc97ce132d9e379f715/scripts/recalculate_metrics.py#L249) defaults to exactly `ROC_AUC`, `PR_AUC`, `RANGE_PR_AUC`. This is also the metric/configuration set documented on the [published PVLDB 2022 evaluation page](https://timeeval.github.io/evaluation-paper/#evaluation-metrics). The general library's `DefaultMetrics.default_list()` is only ROC_AUC; it must not be confused with this script's default. The eight-entry registry is a menu, not the default workload.

The default `RANGE_PR_AUC` uses `r_alpha=0`, `p_alpha=0`, `cardinality="one"`, `bias="flat"`, `max_samples=50`. The optional `FIXED_RANGE_PR_AUC` uses `.5` recall existence weight and reciprocal cardinality. Thus the original reciprocal-only sweep cannot replace the default workload without extending its cardinality operator. Selecting only the optional reciprocal metric would establish a different, configured workload.

The [native range source](https://github.com/TimeEval/TimeEval/blob/7c3622757b1a3afa9a84cbc97ce132d9e379f715/timeeval/metrics/range_metrics.py#L195) explicitly motivates threshold subsampling by the slow community implementation. This makes a semantics-preserving range sweep directly relevant. It does not establish its runtime share; measure the complete default-three consumer once the input panel is frozen.

### Adapter contract

`tmp/strengthening-consumer/timeeval_adapter.py` exports `make_curve(kernel)`. Its injected callable interface is:

```python
kernel(labels, scores, strict_thresholds, *, cardinality="one", alpha=0)
# returns H x 3 array: precision, recall, F1
```

Bind the generated method to the native range metric object; retain `Metric.__call__`, `AucMetric._auc`, ROC_AUC, PR_AUC and the outer `MetricComputor` body.

The adapter preserves these source behaviors:

1. Sort unique score values, discard the minimum threshold, and use the source stride sampler. The sampler is not an exact cap: for some inputs it retains more than `max_samples`; do not "repair" it.
2. Predict `score >= threshold`. A strict-threshold kernel receives `np.nextafter(thresholds.astype(np.float64), -np.inf)` so equal scores remain active.
3. Add the source synthetic first point `(precision=class_balance, recall=1)`, even when it differs from the actual all-positive range metric; add the final `(1,0)` point.
4. Retain `np.lexsort((-precision,recall))[::-1]` and source dtype assignment before integration. This ordering matters for nonmonotone recall and tied recall values.
5. Preserve the method name `_range_precision_recall_curve`: `AucMetric._auc` decides whether to swap axes by checking the callback name for `precision_recall`.
6. Keep source score validation/sanitization and constant-score handling. `Metric.__call__` returns zero before invoking the curve when all scores are equal.
7. Pinned `prts==1.0.0.3` permits all-positive labels but asserts on all-zero labels. For nonconstant scores, preserve that error; the outer consumer catches it and does not record the range result. With constant scores the wrapper returns zero first. Selected `>=` thresholds always retain at least one predicted point, so the analogous empty-prediction assertion is not reached on the normal curve path.

`check_timeeval_tiny.py` loads the untouched pinned metric source through a test-only package shell and injects a direct prts oracle. It checks ties, skipped minimum, all-positive labels, no-positive exception parity, constant scores, signed zero, both final-threshold sampler branches, both cardinalities, and small/default sample settings. All 28 configurations passed exact curve-array/scalar equality or expected exception parity. This validates the adapter contract only: the optimized kernel and full package are deliberately not substituted or timed in that check.

### Native input/output schema and executable API

```python
from pathlib import Path
from timeeval import DefaultMetrics
# Load scripts/recalculate_metrics.py from the pinned checkout.
metric_list = [DefaultMetrics.ROC_AUC, DefaultMetrics.PR_AUC,
               DefaultMetrics.RANGE_PR_AUC]
run = MetricComputor(Path("trial-results"), [Path("data")],
                     metric_list, save_to_dir=False, n_jobs=1)
run.recompute(recompute_existing=True)
```

This was initially a source-derived API recipe; the later tiny integration check below executes the actual full consumer. `save_to_dir=False` prevents per-experiment `metrics.csv` writes but the script still overwrites `results.csv` unconditionally. Each measured trial therefore needs a separate copy of the frozen input layout.

- `data/datasets.csv`: the reached path needs `collection_name`, `dataset_name`, `test_path`; `train_path` can be blank. The official full-header example is cached under `.cache/strengthening-timeeval/tests/example_data/datasets.csv`. Do not invent metadata such as anomaly counts or training status.
- Each referenced data CSV must contain `is_anomaly`; the native loader reads that column and casts it to float64.
- `trial-results/results.csv`: reached fields are `algorithm`, `hyper_params_id`, `collection`, `dataset`, `repetition`, `status`. Error/timeout statuses are skipped.
- Scores: `<algorithm>/<hyper_params_id>/<collection>/<dataset>/<repetition>/anomaly_scores.ts`, one floating-point value per line with no header, loaded by native `np.genfromtxt`.
- `metrics.csv` is optional; if present the native script loads it. With forced recalculation, metric keys outside the selected list may be removed; preserve this behavior in isolated trial copies.

TimeEval code is MIT licensed. The pinned source requires Python `>=3.9,<3.13`, `prts==1.0.0.3`, and `dask[distributed]==2022.12.1` among its dependencies; prts constrains NumPy `<2` and is Apache-2.0 licensed. The script also imports `multiprocessing_logging` (a TimeEval development extra). At inspection, this workspace had NumPy 1.26.4, scikit-learn 1.8.0 and prts 1.0.0.3; TimeEval and multiprocessing_logging were missing, and installed dask 2024.5.0 did not match the source's declared version. Use an isolated, recorded environment rather than silently treating the selected-source cache as a complete package.

### Real workload selection and remaining gate

The strongest archival workload would use the published TimeEval result layout and original `anomaly_scores.ts` with the complete native three-metric recalculation. The official [dataset/results share](https://timeeval.github.io/evaluation-paper/notebooks/Datasets.html) provides real data and a published summary. The independent external-workload investigation reported that its live root contained raw collection ZIPs and `tsad-evaluation-results.csv`, but no per-point score tree/archive. That is a remaining input-provenance gate, not evidence that such an archive never exists.

Accordingly, a feasible new workload is the same unchanged native three-metric consumer applied to a pre-outcome panel of fresh public real recordings with newly generated, source-pinned detector scores and an explicit input-layout adapter. Describe this as newly produced scores evaluated by the native TimeEval consumer, not a replay of historical TimeEval runs. The external-workload agent owns the recording identities, no-overlap checks and score-source selection. Do not freeze a claim of historical score replay from a summary CSV alone.

The key application result must be complete read-to-final-results.csv time and parity of all three native outputs. Include preprocessing/sorting, input reads and output close; compare range-kernel stage and whole-consumer stage. Retain a fused compiled raster/interval baseline in addition to the slow public Python/prts code. A real end-to-end gain against a competitive control is stronger evidence than a large acceleration against unused Python work.

## Immediate implementation order

1. Extend the range operator to `cardinality="one"`; preserve the native TimeEval adapter contract above. Prove and test its update formulas separately from the integration.
2. Use the independently frozen real recording/score panel, isolated package environment and native default-three consumer. Complete output parity before any timing. Keep published-history and newly generated input provenance explicit.
3. Measure range-only TSB replacement as the expected limited control; try the shared PA/Event statistics or probability-only Affiliation control only if they answer a distinct application question. Attribute any Affiliation gain to the established-formula engineering change.

## Implemented native integration and pre-timing status

`src/sparse_vus/timeeval_adapter.py` now adapts the actual compiled `weighted_range_metrics` raster or bucket kernel to the native default configuration. It keeps the original metric object class, public wrapper, callback name, sampler, synthetic endpoints, curve sorting, dtype assignments and AUC routine. The optional reciprocal configuration is rejected explicitly. There is no precision/recall rounding heuristic or source-order repair cost hidden outside the timing interval.

`tests/test_timeeval_adapter.py` passed 39 targeted tests in the isolated Python 3.11 TimeEval environment. These include tiny tied/fragmented profiles, float32 and binary64 inputs, subnormal/signed-zero eligibility, source sampling branches, all-positive/no-positive labels, constant scores, score sanitization, all observed queries, and actual native constructor/recalculation of six tiny rows for both contracts and all three methods. The runner tests also cover escaping the public per-metric `except Exception` on deadline, preserved failure artifacts, rejected unfrozen protocols, censored summary rules, added native metric-cache detection, and generated-score receipt bindings. This is correctness validation on tiny inputs, not evidence of application speedup.

`scripts/run_timeeval_strengthening.py` implements the prospective complete workflow study: the unchanged native three metrics; public, compiled raster and bucket methods; native nominal `max_samples=50` and all-observed contracts kept separate; combined 52-row workflow plus three family batches; and all six balanced method orders. Each trial uses a fresh copied input template. Imports, tiny JIT warmup, source/input audits, template copies and output checks are excluded; the native constructor and `recompute(True)`, including input reads and final results.csv write/close, are measured. The timer includes one deadline-arming call and excludes signal-handler setup/cleanup. A 600-second timeout censors the attempted workflow; later attempts for the same method/contract/batch are explicitly not run. Only six complete paired orders receive an approximate paired-order bootstrap interval, which describes execution/order variation of this fixed workload. Missing public outputs after censoring are reported as unavailable parity evidence, not silently certified by the compiled control.

The newly generated, source-pinned 26-case FFT/COPOD workload is bound by `workload-generation.json` (SHA256 `4177f82b6bfe404f82439d75b749adb16b21a416321425326da2611115f02568`) and the independent native-input audit. The read-only candidate manifest, `artifacts/pvldb-research-20261024/strengthening/timeeval-consumer-manifest-candidate-v1.json`, pins all 425 files in the native source snapshot, 80 native input files, prts source, project runtime source, package versions, generation/audit receipts, and per-profile query plans. Its SHA256 is `d58ff15fed2b9db3bc083559689425d59011ab2f7d7a76273d39ffa15676d693`. The candidate is not itself a global frozen protocol and cannot authorize timing.

Actual source-emitted query counts, derived without computing any metric, are:

| Complete native batch | Rows | Nominal-50 total H | All-observed total H |
|---|---:|---:|---:|
| Combined | 52 | 2,776 | 71,749 |
| MSL | 4 | 97 | 655 |
| Stock | 24 | 1,282 | 44,059 |
| WSD | 24 | 1,397 | 27,035 |

Nominal-50 emits between 2 and 90 queries per profile on this workload; it must not be described as a hard cap of 50. All-observed emits between 2 and 5,819. These are different evaluation contracts, so speed ratios are calculated only within the same contract.

No real native consumer timing has been run at this checkpoint. The implementation and tiny native validation establish a concrete integration path; novelty, real-input speedup and publication readiness remain separate scientific questions.
