# PR-engine report: v2 development

Independent audit: **PASS**. 126 cases, 42 series, 23 families.

Speed ratios are comparator time / radix_pr time; values above 1 favor radix_pr. All timing summaries use three-repetition case medians. Brackets contain audited 95% family-cluster intervals.

- **primary_decision: FAIL** at L=30; reference `fast_race`, controls: `sparse_pr`, `dense_pr_direct`, `radix_pr`.
- **radix_primary_decision: PASS** at L=30; reference `radix_pr`, controls: `sparse_pr`, `dense_pr_direct`, `dense_nearest_both`.
- **radix_racing_decision: FAIL** at L=30; reference `fast_race_radix`, controls: `sparse_pr`, `dense_pr_direct`, `radix_pr`.

Each decision requires both geomean and aggregate-ratio lower interval bounds above 1 against every listed control, plus correctness.

## L=30

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 1.686208 | 1.919 | 1.914 [1.757, 2.083] | 2.554 [2.018, 2.855] | 41/1 | 1.151x |
| dense_pr_direct | PR only | 2.976107 | 3.306 | 2.958 [2.432, 3.535] | 4.507 [3.175, 5.264] | 40/2 | 1.093x |
| sparse_both | paired ROC+PR | 1.760454 | 2.085 | 2.024 [1.806, 2.246] | 2.666 [2.144, 2.978] | 40/2 | 1.419x |
| dense_nearest_both | paired ROC+PR | 4.174757 | 5.216 | 4.604 [3.868, 5.418] | 6.322 [4.827, 7.077] | 42/0 | 1.000x |
| klein_pr | PR only | 12.115243 | 20.372 | 19.619 [16.312, 23.574] | 18.347 [15.439, 20.417] | 42/0 | 1.000x |
| benchopt_both | paired ROC+PR | 24.808262 | 37.957 | 39.964 [34.855, 46.244] | 37.570 [33.525, 46.059] | 42/0 | 1.000x |
| radix_pr | PR only | 0.660329 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 0.761411 | 1.102 | 1.123 [1.056, 1.201] | 1.153 [1.084, 1.214] | 36/6 | 1.403x |
| v02_race | PR selection | 2.287733 | 2.558 | 2.715 [2.298, 3.226] | 3.465 [2.418, 4.701] | 41/1 | 1.193x |
| fast_race | PR selection | 1.633308 | 2.170 | 2.039 [1.823, 2.251] | 2.473 [2.004, 2.747] | 39/3 | 1.600x |
| fast_exact_completion | PR selection | 1.627385 | 2.272 | 2.053 [1.858, 2.254] | 2.465 [2.016, 2.734] | 40/2 | 1.156x |
| fast_race_radix | PR selection | 0.678299 | 1.143 | 1.196 [1.087, 1.332] | 1.027 [0.951, 1.088] | 32/10 | 1.444x |
| fast_full_budget | PR selection | 1.816228 | 2.310 | 2.252 [2.022, 2.512] | 2.750 [2.118, 3.133] | 41/1 | 1.237x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`.
Comparator/radix_pr ratios: median 1.844, geomean 1.795, aggregate 2.495; radix_pr faster/slower 39/3; worst radix_pr slowdown 1.151x.
Winning-control counts: `sparse_pr`=35, `dense_pr_direct`=7, `klein_pr`=0.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## L=100

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 2.239007 | 1.651 | 1.686 [1.595, 1.787] | 1.963 [1.677, 2.168] | 42/0 | 1.000x |
| dense_pr_direct | PR only | 7.771562 | 5.162 | 4.416 [3.340, 5.708] | 6.814 [4.095, 8.606] | 42/0 | 1.000x |
| sparse_both | paired ROC+PR | 2.555373 | 1.900 | 1.922 [1.842, 2.011] | 2.241 [1.886, 2.476] | 42/0 | 1.000x |
| dense_nearest_both | paired ROC+PR | 8.999971 | 6.656 | 5.602 [4.224, 7.224] | 7.891 [4.901, 9.771] | 42/0 | 1.000x |
| klein_pr | PR only | 31.751579 | 33.314 | 34.575 [25.804, 45.286] | 27.839 [20.520, 34.694] | 42/0 | 1.000x |
| benchopt_both | paired ROC+PR | 54.215085 | 53.693 | 55.187 [45.929, 66.319] | 47.535 [38.115, 66.289] | 42/0 | 1.000x |
| radix_pr | PR only | 1.140524 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 1.639139 | 1.320 | 1.366 [1.264, 1.488] | 1.437 [1.313, 1.655] | 41/1 | 1.107x |
| v02_race | PR selection | 4.589329 | 2.602 | 2.981 [2.419, 3.713] | 4.024 [2.579, 5.674] | 42/0 | 1.000x |
| fast_race | PR selection | 2.368580 | 1.803 | 1.766 [1.621, 1.924] | 2.077 [1.600, 2.423] | 41/1 | 1.023x |
| fast_exact_completion | PR selection | 2.203176 | 1.792 | 1.770 [1.693, 1.852] | 1.932 [1.675, 2.119] | 42/0 | 1.000x |
| fast_race_radix | PR selection | 1.315762 | 1.116 | 1.203 [1.055, 1.379] | 1.154 [0.905, 1.312] | 33/9 | 1.983x |
| fast_full_budget | PR selection | 2.531464 | 1.930 | 1.989 [1.790, 2.200] | 2.220 [1.705, 2.549] | 42/0 | 1.000x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`.
Comparator/radix_pr ratios: median 1.639, geomean 1.664, aggregate 1.949; radix_pr faster/slower 42/0; worst radix_pr slowdown 1.000x.
Winning-control counts: `sparse_pr`=38, `dense_pr_direct`=4, `klein_pr`=0.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## L=300

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 4.442118 | 1.256 | 1.293 [1.231, 1.365] | 1.398 [1.270, 1.492] | 41/1 | 1.060x |
| dense_pr_direct | PR only | 22.387710 | 5.022 | 4.818 [3.637, 6.437] | 7.044 [3.921, 9.429] | 41/1 | 1.003x |
| sparse_both | paired ROC+PR | 5.936236 | 1.682 | 1.675 [1.596, 1.760] | 1.868 [1.653, 2.047] | 42/0 | 1.000x |
| dense_nearest_both | paired ROC+PR | 24.190789 | 6.187 | 5.170 [3.583, 7.247] | 7.612 [4.191, 10.197] | 41/1 | 1.070x |
| klein_pr | PR only | 91.475490 | 38.366 | 37.510 [28.589, 49.774] | 28.782 [19.283, 41.655] | 42/0 | 1.000x |
| benchopt_both | paired ROC+PR | 138.509702 | 53.476 | 52.175 [40.655, 67.360] | 43.581 [30.443, 73.342] | 42/0 | 1.000x |
| radix_pr | PR only | 3.178185 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 5.101922 | 1.450 | 1.512 [1.388, 1.669] | 1.605 [1.490, 1.816] | 41/1 | 1.159x |
| v02_race | PR selection | 10.717285 | 1.509 | 2.029 [1.494, 2.762] | 3.372 [1.802, 5.286] | 31/11 | 1.998x |
| fast_race | PR selection | 4.326031 | 1.252 | 1.187 [1.009, 1.381] | 1.361 [1.104, 1.554] | 29/13 | 1.924x |
| fast_exact_completion | PR selection | 4.408093 | 1.298 | 1.327 [1.266, 1.397] | 1.387 [1.259, 1.486] | 42/0 | 1.000x |
| fast_race_radix | PR selection | 3.055387 | 0.988 | 0.857 [0.705, 1.027] | 0.961 [0.777, 1.118] | 19/23 | 4.615x |
| fast_full_budget | PR selection | 4.281681 | 1.239 | 1.208 [1.007, 1.438] | 1.347 [1.079, 1.549] | 27/15 | 2.276x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`.
Comparator/radix_pr ratios: median 1.256, geomean 1.290, aggregate 1.397; radix_pr faster/slower 40/2; worst radix_pr slowdown 1.060x.
Winning-control counts: `sparse_pr`=40, `dense_pr_direct`=2, `klein_pr`=0.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## Combined L=30/100 (descriptive)

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 3.925214 | 1.789 | 1.796 [1.694, 1.912] | 2.180 [1.819, 2.419] | 83/1 | 1.151x |
| dense_pr_direct | PR only | 10.747669 | 3.846 | 3.614 [2.878, 4.453] | 5.968 [3.799, 7.312] | 82/2 | 1.093x |
| sparse_both | paired ROC+PR | 4.315827 | 1.990 | 1.973 [1.845, 2.108] | 2.397 [1.996, 2.657] | 82/2 | 1.419x |
| dense_nearest_both | paired ROC+PR | 13.174728 | 5.622 | 5.079 [4.078, 6.190] | 7.316 [4.893, 8.731] | 84/0 | 1.000x |
| klein_pr | PR only | 43.866822 | 24.902 | 26.045 [20.651, 32.210] | 24.359 [18.832, 28.943] | 84/0 | 1.000x |
| benchopt_both | paired ROC+PR | 79.023347 | 44.534 | 46.963 [40.519, 54.741] | 43.881 [36.510, 58.745] | 84/0 | 1.000x |
| radix_pr | PR only | 1.800853 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 2.400550 | 1.190 | 1.238 [1.159, 1.335] | 1.333 [1.233, 1.481] | 77/7 | 1.403x |
| v02_race | PR selection | 6.877062 | 2.579 | 2.845 [2.399, 3.438] | 3.819 [2.524, 5.351] | 83/1 | 1.193x |
| fast_race | PR selection | 4.001888 | 2.023 | 1.898 [1.762, 2.049] | 2.222 [1.767, 2.538] | 80/4 | 1.600x |
| fast_exact_completion | PR selection | 3.830562 | 1.907 | 1.906 [1.799, 2.014] | 2.127 [1.809, 2.344] | 82/2 | 1.156x |
| fast_race_radix | PR selection | 1.994061 | 1.135 | 1.199 [1.082, 1.341] | 1.107 [0.925, 1.224] | 65/19 | 1.983x |
| fast_full_budget | PR selection | 4.347691 | 2.112 | 2.116 [1.948, 2.307] | 2.414 [1.891, 2.694] | 83/1 | 1.237x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`.
Comparator/radix_pr ratios: median 1.725, geomean 1.728, aggregate 2.149; radix_pr faster/slower 81/3; worst radix_pr slowdown 1.151x.
Winning-control counts: `sparse_pr`=73, `dense_pr_direct`=11, `klein_pr`=0.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## Scope

- The holdout was previously studied in other experiments; it is held out for this new procedure only.
- Floating-point containment is numerical, not formal outward rounding.
- Retained curve bytes exclude other working arrays; this is not peak memory.
- Ratios use paired within-run case medians; values above one favor the named reference. No cross-run or cross-version times are pooled.
- Family-cluster CIs describe case variation, not uncertainty from only three timing repetitions; intervals are copied from the bound independent audit.
- The fastest eligible PR-only exhaustive comparator is a post-protocol per-case oracle diagnostic. It has no confidence intervals and does not change the frozen decisions.
- Benchopt and paired controls compute ROC and PR; matched PR-only controls isolate the extra-work confound.
- The 308-series policy holdout belongs to the previously studied corpus and the same families; it is not a new external-domain dataset.
- DTAIAnomaly's bounded external appendix is separate. These results do not establish global SOTA.
- Retained curve bytes are not peak memory. CPU-clearance notes do not establish operating-system isolation.

Audit SHA-256: `1645dba4b2d7cb1b481f69ecb905f465c399c8cecff60e7dff19f4daad5f441c`

Raw records SHA-256: `712e9a147ac4ba8bdd3d338fda25b7ac17289a0f0ecd41f11fcf4ad20d46853b`
