# Experimental-validity audit and padding sensitivity

Date: 20 October 2026. Scope: independently assigned automated audit in the same
development session. This is not external scientific review, an independent
laboratory reproduction, or publication acceptance.

The existing release supports a focused claim: sparse event integration returns
the pinned scalar VUS values and can reduce the cost of evaluating fixed anomaly
scores. It does not yet establish a general model-selection improvement,
end-to-end anomaly-detection speedup, or superiority to every published fast VUS
implementation.

## Falsifiable weaknesses

| Issue | Why it matters | Evidence or test |
|---|---|---|
| Released scores contain a documented padding discrepancy | Model-order changes can depend on preprocessing and evaluation support. | The pinned source README says Chronos-Bolt and TimeMoE use zero padding and describes replacing it with the first available score. All 350 selected vectors for each of these two models have exactly 64 leading zeros. |
| Common-suffix evaluation changes the task | Removing 64 positions changes prevalence, threshold ranks and boundary expansion, as well as padding. | 21 of 350 series contain positive labels among the first 64 positions. Every resulting suffix retains both classes. The fixed crop is label-independent. |
| A strict sign reversal may be practically tiny | Counts at a numerical tolerance of `1e-10` do not by themselves establish material model-selection consequences. | Report all pairs and prespecified minimum margins `1e-4`, `1e-3`, `1e-2`, plus unique-top changes and no-change cases. |
| Source families are heterogeneous and unequal | Six model/width conditions per series are dependent; 70 UCR series should not silently stand in for 70 independent source domains. | Retain complete series clusters. Report each family, equal-family prevalence, singleton-family limitations and negative cases. |
| The main dense comparators are implemented in this repository | A careful in-repository baseline can still miss optimization choices available in other software. | Keep the approximately twofold main comparison distinct from actual pinned dtaianomaly results and unavailable comparators. |
| External speed ratios are completion-conditioned | Dropping right-censored cases would bias an all-input runtime claim. | Existing external supplement has 35 completed exact pairs and seven timeouts. Do not substitute the completed-pair median for a full-corpus runtime estimate. |
| Evaluator speed is not pipeline speed | Reusing released scores omits detector inference and other pipeline costs. | Report absolute evaluation costs from original medians and explicitly hypothetical Amdahl scenarios; inference and full-pipeline times remain unknown. |
| Novelty and correctness are different questions | Replicated exact values and a working release do not prove the event-elimination idea is new. | Require a direct prior-art comparison and external scientific assessment; these are outside this computational audit. |

## Frozen sensitivity protocol

Executable: [`experiments/ranking_robustness.py`](../experiments/ranking_robustness.py).
The protocol was written after seeing the released results and zero-prefix
inventory, and before evaluating either transformation. It is a post-publication
sensitivity analysis, not preregistration.

The original 350-series intersection, three selected models, widths 10 and 30,
all three unordered model pairs, and both metrics are retained. The variants are:

1. `released`: original source bytes and hash-bound original results.
2. `first_score_fill64`: replace the first 64 scores of the two documented
   zero-padded models with their score at index 64. Preserve labels and TimesFM.
3. `common_suffix64`: evaluate `labels[64:]` and `scores[64:]` for every model.

The prefix is determined by the documented context size and validated against
score values; labels never choose the crop. Scores after index 64 are not
modified. Original archives are read-only. Leading nonzero values alone would
not establish a model's full valid-score mask. In particular, this protocol does
not claim to reconstruct every preprocessing detail of the source paper.

All newly computed exact outputs are compared with the separate dense
direct-ramp implementation at absolute tolerance `1e-11`. Small transformed
fixtures are additionally checked against the pinned upstream exact and
250-threshold code. Original-result reuse is explicitly flagged per record.
All eligible series are included, with one-class exclusions logged if they occur.

For a pair, a strict reversal requires opposite exact/sample signs and both
absolute gaps above `1e-10`. Material counts additionally require both gaps to
meet the stated margin. Unique-top changes require a single best model in both
calculations. Persistent reversals match the same series, width, metric and
unordered pair; their direction is checked separately.

Within each family, 5,000 bootstrap draws resample whole series while retaining
all models, widths and pairs. The macro analysis gives source families equal
weight and resamples families. These intervals describe this fixed collection;
they are not evidence of population representativeness or statistical
significance. A one-series family necessarily has a degenerate within-family
interval and does not support a precise population estimate.

## Reproduction and evidence

```sh
/opt/anaconda3/bin/python experiments/ranking_robustness.py --freeze
/opt/anaconda3/bin/python experiments/ranking_robustness.py --run
/opt/anaconda3/bin/python experiments/ranking_robustness.py --verify
```

`--freeze` and `--run` intentionally refuse to overwrite prior protocol or result
records. Preserve the existing evidence directory before running a fresh
reproduction. If redirecting stdout, write the log outside the top level of
`artifacts/robustness` (for example its `runtime/` subdirectory). The receipt
binds top-level output artifacts.

The protocol binds source code and input manifests by SHA-256. Every score
member passes its ZIP CRC and the published local member-hash lock. It does
not claim verification of whole source ZIP MD5 values when only selected
members were downloaded.

The raw results, all pair comparisons, family effects, inventory, exclusions,
self-test evidence and reconstruction receipt are retained under
[`artifacts/robustness`](../artifacts/robustness/).

## Completed results

All 350 series and all 23 families remain eligible in every variant: 6,300
model/width records and 12,600 metric/pair comparisons in total. There are no
exclusions. Of these records, 2,800 reuse identical original inputs/results and
3,500 are newly computed. The largest new exact-versus-dense discrepancy is
`2.3636648194269583e-13`; including reused original rows gives
`3.6914915568786455e-13`. All 144 small transformed upstream-code checks pass
(maximum exact discrepancy `3.33e-16`, sampled discrepancy `2.22e-16`).

The driver's coverage/hash/reconstruction verification and the separate
stdlib-only count checker both pass. The latter independently reconstructs
counts from raw metric records; it does not rerun the numerical kernels or
independently regenerate bootstrap draws.

| Fixed variant | PR reversals / 2,100 pairs | Affected series / 350 | Affected families / 23 | Unique-top changes / 700 | ROC reversals |
|---|---:|---:|---:|---:|---:|
| Released | 84 | 55 | 13 | 50 | 5 |
| First-score fill64 | 93 | 59 | 16 | 52 | 12 |
| Common suffix64 | 95 | 61 | 14 | 48 | 8 |

Of the original 84 PR reversals, 75 persist after first-score filling and 74
persist on the common suffix, all in the same direction as before. Filling
removes nine original reversals and introduces 18; cropping removes ten and
introduces 21. Thus the phenomenon survives both interventions, while its
individual cases depend on the evaluation convention.

| Required minimum gap in both exact and sampled PR | Released | Fill64 | Suffix64 |
|---|---:|---:|---:|
| Above numerical tie tolerance `1e-10` | 84 | 93 | 95 |
| At least `1e-4` | 62 | 64 | 68 |
| At least `1e-3` | 38 | 41 | 44 |
| At least `1e-2` | 5 | 5 | 5 |

Most reversals therefore involve small margins. The count of 95 must not be
described as 95 substantial changes in model quality. On suffix64, the median
absolute PR approximation error is `0.002489`, its 95th percentile is `0.177261`,
and its maximum is `0.582639`. The mean signed error is `-0.032641`; the exact
integral is higher on average for these fixed inputs, not necessarily on every
input. No monotonic underestimate theorem is inferred from this average.

Giving each source family equal weight, PR reversal prevalence is 2.44%
(descriptive family-bootstrap interval 1.12–4.06%) on released scores,
5.45% (2.12–10.32%) after filling, and 4.31% (1.84–7.59%) on suffix64.
These are different estimands from the pooled pair fractions 4.00%, 4.43% and
4.52%, respectively. The singleton Power family contributes a relatively large
equal-family effect; it must not be treated as a precise domain estimate.

All families, including zero-effect cases, are below. The last column is the
suffix64 within-family pair reversal rate with a whole-series bootstrap interval.
Zero-width intervals at zero report no observed reversals in this fixed set;
they do not establish zero incidence in an unobserved population.

| Family | Series | Released PR reversals | Fill64 | Suffix64 | Suffix rate and descriptive 95% interval |
|---|---:|---:|---:|---:|---:|
| CATSv2 | 1 | 0 | 0 | 0 | 0.00% [0.00, 0.00] |
| Daphnet | 1 | 0 | 0 | 0 | 0.00% [0.00, 0.00] |
| Exathlon | 30 | 1 | 2 | 2 | 1.11% [0.00, 3.33] |
| IOPS | 15 | 10 | 9 | 8 | 8.89% [3.31, 15.56] |
| LTDB | 8 | 0 | 0 | 0 | 0.00% [0.00, 0.00] |
| MGAB | 8 | 0 | 1 | 0 | 0.00% [0.00, 0.00] |
| MITDB | 7 | 1 | 1 | 1 | 2.38% [0.00, 7.14] |
| MSL | 7 | 1 | 1 | 1 | 2.38% [0.00, 7.14] |
| NAB | 23 | 3 | 4 | 4 | 2.90% [0.00, 6.52] |
| NEK | 8 | 0 | 0 | 0 | 0.00% [0.00, 0.00] |
| OPPORTUNITY | 27 | 6 | 5 | 8 | 4.94% [1.85, 8.64] |
| Power | 1 | 0 | 3 | 2 | 33.33% [33.33, 33.33] |
| SED | 2 | 0 | 0 | 0 | 0.00% [0.00, 0.00] |
| SMAP | 17 | 5 | 4 | 3 | 2.94% [0.00, 5.88] |
| SMD | 33 | 7 | 7 | 13 | 6.57% [2.53, 11.11] |
| SVDB | 18 | 1 | 1 | 1 | 0.93% [0.00, 2.78] |
| SWaT | 1 | 0 | 0 | 0 | 0.00% [0.00, 0.00] |
| Stock | 8 | 0 | 0 | 0 | 0.00% [0.00, 0.00] |
| TAO | 2 | 0 | 2 | 1 | 8.33% [0.00, 16.67] |
| TODS | 13 | 1 | 1 | 0 | 0.00% [0.00, 0.00] |
| UCR | 70 | 26 | 27 | 27 | 6.43% [3.81, 9.29] |
| WSD | 20 | 17 | 17 | 17 | 14.17% [5.83, 24.17] |
| YAHOO | 30 | 5 | 8 | 7 | 3.89% [0.56, 8.89] |

## Absolute cost and negative runtime cases

No new timing benchmark was performed. Summing the original isolated medians
over the 2,100 original conditions gives 14.683 seconds for sparse evaluation
and 33.100 seconds for the fastest dense implementation per condition:
18.417 seconds saved, with a ratio of sums of 2.254. This differs from the median
per-condition ratio of 2.061 and is not an observed batch or pipeline wall time.
The median saved time per condition is 1.945 milliseconds; 184 conditions are
slower with sparse evaluation.

The source-family runtime exceptions are concrete:

| Family | Sparse/dense speed ratio, geometric mean | Descriptive series-bootstrap interval | Slower cases |
|---|---:|---:|---:|
| NEK | 0.896 | [0.859, 0.933] | 29 / 48 |
| Stock | 0.615 | [0.553, 0.667] | 48 / 48 |
| TAO | 0.585 | [0.524, 0.653] | 12 / 12 |

Here the ratio is dense time divided by sparse time, so values below one favor
dense evaluation. All 23 family summaries remain in `timing_context.json`.
Dense-support workloads can favor the dense algorithm; a universal acceleration
claim is contradicted by these measurements.

For illustration only, if evaluation occupied 10% of an otherwise unchanged
pipeline, a 2.254-fold evaluator improvement would imply about a 1.059-fold
pipeline improvement under Amdahl's law. At a 1% fraction it would be about
1.006-fold. The actual fraction and inference time are unknown. The demonstrated
practical contribution is affordable exact metric evaluation, with a bounded
observed cost and robust approximation-induced order changes.

## Interpretation requirements

The observed approximation sensitivity is not explained solely by the documented
64-position zero padding: it persists after both fixed interventions. Counts and
individual model orders still change across conventions, so each reported
finding must identify its variant. This evidence strengthens a numerical
evaluation claim without establishing an application-level benefit.

Neither variant compares learned detectors against ground-truth model quality.
Exact integration resolves the defined numerical approximation; it does not
prove that the resulting metric is the most useful measure of anomaly detection.
No model winner, training improvement, detector inference speedup or downstream
operational benefit is inferred.
