# PR-engine report: v3 holdout

Independent audit: **PASS**. 924 cases, 308 series, 17 families.

Speed ratios are comparator time / radix_pr time; values above 1 favor radix_pr. All timing summaries use three-repetition case medians. Brackets contain audited 95% family-cluster intervals.

- **primary_decision: FAIL** at L=30; reference `fast_race`, controls: `sparse_pr`, `dense_pr_direct`, `radix_pr`.
- **radix_primary_decision: PASS** at L=30; reference `radix_pr`, controls: `sparse_pr`, `dense_pr_direct`, `dense_nearest_both`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.
- **radix_racing_decision: FAIL** at L=30; reference `fast_race_radix`, controls: `sparse_pr`, `dense_pr_direct`, `radix_pr`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.

Each decision requires both geomean and aggregate-ratio lower interval bounds above 1 against every listed control, plus correctness.

## L=30

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 4.530767 | 1.987 | 1.916 [1.839, 2.013] | 1.955 [1.745, 2.095] | 304/4 | 1.239x |
| dense_pr_direct | PR only | 12.479225 | 4.894 | 4.161 [3.170, 5.008] | 5.385 [4.241, 6.191] | 308/0 | 1.000x |
| sparse_both | paired ROC+PR | 4.725758 | 2.071 | 1.997 [1.905, 2.124] | 2.039 [1.812, 2.197] | 304/4 | 1.234x |
| dense_nearest_both | paired ROC+PR | 16.719669 | 6.917 | 5.890 [4.639, 6.923] | 7.214 [5.688, 8.187] | 308/0 | 1.000x |
| klein_pr | PR only | 26.031930 | 14.538 | 13.814 [11.639, 15.930] | 11.232 [10.034, 12.514] | 308/0 | 1.000x |
| benchopt_both | paired ROC+PR | 53.284829 | 21.493 | 20.973 [18.481, 23.617] | 22.991 [19.193, 30.937] | 308/0 | 1.000x |
| radix_pr | PR only | 2.317612 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 2.506050 | 1.072 | 1.084 [1.055, 1.124] | 1.081 [1.048, 1.139] | 284/24 | 1.027x |
| dense_pr_direct_radix | PR only | 10.910994 | 4.419 | 3.756 [2.904, 4.486] | 4.708 [3.794, 5.276] | 308/0 | 1.000x |
| dense_pr_nearest_radix | PR only | 11.610224 | 4.791 | 4.047 [3.142, 4.821] | 5.010 [3.933, 5.643] | 306/2 | 1.074x |
| v02_race | PR selection | 5.387037 | 2.307 | 2.500 [2.196, 3.056] | 2.324 [2.028, 2.721] | 305/3 | 1.243x |
| fast_race | PR selection | 4.549212 | 2.197 | 2.139 [2.011, 2.315] | 1.963 [1.800, 2.109] | 306/2 | 1.233x |
| fast_exact_completion | PR selection | 4.665275 | 2.232 | 2.192 [2.082, 2.353] | 2.013 [1.833, 2.161] | 306/2 | 1.225x |
| fast_race_radix | PR selection | 2.364065 | 1.188 | 1.199 [1.050, 1.359] | 1.020 [0.957, 1.101] | 261/47 | 1.549x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.
Comparator/radix_pr ratios: median 1.986, geomean 1.879, aggregate 1.928; radix_pr faster/slower 302/6; worst radix_pr slowdown 1.239x.
Winning-control counts: `sparse_pr`=286, `dense_pr_direct`=1, `klein_pr`=0, `dense_pr_direct_radix`=18, `dense_pr_nearest_radix`=3.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## L=100

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 6.419626 | 1.715 | 1.670 [1.570, 1.746] | 1.635 [1.490, 1.740] | 307/1 | 1.227x |
| dense_pr_direct | PR only | 33.879179 | 7.901 | 6.927 [4.586, 9.319] | 8.628 [5.645, 11.366] | 308/0 | 1.000x |
| sparse_both | paired ROC+PR | 7.247395 | 1.908 | 1.875 [1.812, 1.922] | 1.846 [1.734, 1.931] | 307/1 | 1.222x |
| dense_nearest_both | paired ROC+PR | 40.414267 | 10.010 | 8.500 [5.593, 11.392] | 10.292 [6.511, 13.688] | 305/3 | 1.031x |
| klein_pr | PR only | 75.284133 | 28.468 | 24.678 [18.173, 30.602] | 19.173 [13.880, 24.409] | 308/0 | 1.000x |
| benchopt_both | paired ROC+PR | 146.511384 | 36.229 | 34.450 [27.078, 41.683] | 37.312 [27.113, 50.879] | 308/0 | 1.000x |
| radix_pr | PR only | 3.926666 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 4.756616 | 1.203 | 1.195 [1.154, 1.246] | 1.211 [1.158, 1.269] | 305/3 | 1.012x |
| dense_pr_direct_radix | PR only | 32.275354 | 7.465 | 6.666 [4.438, 8.952] | 8.220 [5.435, 10.714] | 308/0 | 1.000x |
| dense_pr_nearest_radix | PR only | 33.546236 | 7.919 | 6.975 [4.574, 9.447] | 8.543 [5.360, 11.345] | 302/6 | 1.212x |
| v02_race | PR selection | 8.330746 | 1.951 | 2.256 [1.772, 2.943] | 2.122 [1.780, 2.539] | 286/22 | 1.265x |
| fast_race | PR selection | 6.038517 | 1.798 | 1.662 [1.431, 1.827] | 1.538 [1.364, 1.673] | 285/23 | 1.293x |
| fast_exact_completion | PR selection | 6.571377 | 1.918 | 1.858 [1.716, 1.964] | 1.674 [1.537, 1.778] | 307/1 | 1.212x |
| fast_race_radix | PR selection | 3.559634 | 1.027 | 0.971 [0.781, 1.116] | 0.907 [0.783, 1.027] | 179/129 | 3.150x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.
Comparator/radix_pr ratios: median 1.715, geomean 1.655, aggregate 1.612; radix_pr faster/slower 301/7; worst radix_pr slowdown 1.227x.
Winning-control counts: `sparse_pr`=295, `dense_pr_direct`=0, `klein_pr`=0, `dense_pr_direct_radix`=0, `dense_pr_nearest_radix`=13.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## L=300

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 14.161280 | 1.275 | 1.323 [1.228, 1.404] | 1.259 [1.190, 1.330] | 307/1 | 1.189x |
| dense_pr_direct | PR only | 100.976273 | 7.800 | 7.465 [4.384, 11.169] | 8.977 [5.555, 13.480] | 308/0 | 1.000x |
| sparse_both | paired ROC+PR | 17.698752 | 1.636 | 1.648 [1.567, 1.712] | 1.573 [1.518, 1.625] | 307/1 | 1.173x |
| dense_nearest_both | paired ROC+PR | 112.935573 | 9.133 | 8.428 [4.753, 12.877] | 10.040 [5.661, 15.396] | 296/12 | 1.177x |
| klein_pr | PR only | 221.036766 | 29.888 | 26.660 [18.001, 35.878] | 19.650 [13.056, 28.794] | 308/0 | 1.000x |
| benchopt_both | paired ROC+PR | 417.482056 | 32.894 | 35.391 [24.667, 47.808] | 37.114 [23.930, 57.266] | 308/0 | 1.000x |
| radix_pr | PR only | 11.248737 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 14.817211 | 1.337 | 1.321 [1.296, 1.356] | 1.317 [1.292, 1.340] | 308/0 | 1.000x |
| dense_pr_direct_radix | PR only | 99.075510 | 7.612 | 7.360 [4.333, 10.986] | 8.808 [5.506, 13.079] | 308/0 | 1.000x |
| dense_pr_nearest_radix | PR only | 100.600753 | 8.103 | 7.426 [4.155, 11.417] | 8.943 [5.047, 13.692] | 295/13 | 1.299x |
| v02_race | PR selection | 19.955502 | 1.157 | 1.332 [0.927, 1.789] | 1.774 [1.196, 2.405] | 177/131 | 3.490x |
| fast_race | PR selection | 11.020529 | 1.003 | 0.884 [0.688, 1.042] | 0.980 [0.806, 1.091] | 155/153 | 3.802x |
| fast_exact_completion | PR selection | 14.249322 | 1.372 | 1.392 [1.277, 1.490] | 1.267 [1.195, 1.348] | 307/1 | 1.184x |
| fast_race_radix | PR selection | 8.178604 | 0.557 | 0.542 [0.397, 0.670] | 0.727 [0.554, 0.864] | 69/239 | 8.605x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.
Comparator/radix_pr ratios: median 1.275, geomean 1.309, aggregate 1.235; radix_pr faster/slower 294/14; worst radix_pr slowdown 1.299x.
Winning-control counts: `sparse_pr`=295, `dense_pr_direct`=0, `klein_pr`=0, `dense_pr_direct_radix`=0, `dense_pr_nearest_radix`=13.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## Combined L=30/100 (descriptive)

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 10.950393 | 1.844 | 1.789 [1.722, 1.843] | 1.754 [1.608, 1.858] | 611/5 | 1.239x |
| dense_pr_direct | PR only | 46.358404 | 5.322 | 5.369 [3.824, 6.807] | 7.424 [5.201, 9.238] | 616/0 | 1.000x |
| sparse_both | paired ROC+PR | 11.973153 | 1.973 | 1.935 [1.879, 2.003] | 1.917 [1.771, 2.014] | 611/5 | 1.234x |
| dense_nearest_both | paired ROC+PR | 57.133936 | 7.370 | 7.076 [5.115, 8.867] | 9.150 [6.255, 11.410] | 613/3 | 1.031x |
| klein_pr | PR only | 101.316063 | 17.287 | 18.464 [14.646, 21.868] | 16.225 [12.714, 19.540] | 616/0 | 1.000x |
| benchopt_both | paired ROC+PR | 199.796213 | 24.555 | 26.880 [22.445, 30.992] | 31.997 [24.571, 42.765] | 616/0 | 1.000x |
| radix_pr | PR only | 6.244278 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 7.262666 | 1.132 | 1.138 [1.104, 1.183] | 1.163 [1.114, 1.227] | 589/27 | 1.027x |
| dense_pr_direct_radix | PR only | 43.186348 | 4.822 | 5.004 [3.603, 6.337] | 6.916 [4.919, 8.471] | 616/0 | 1.000x |
| dense_pr_nearest_radix | PR only | 45.156460 | 5.190 | 5.313 [3.784, 6.745] | 7.232 [4.905, 8.992] | 608/8 | 1.212x |
| v02_race | PR selection | 13.717783 | 2.167 | 2.375 [1.981, 2.997] | 2.197 [1.898, 2.582] | 591/25 | 1.265x |
| fast_race | PR selection | 10.587729 | 1.972 | 1.885 [1.715, 2.033] | 1.696 [1.547, 1.815] | 591/25 | 1.293x |
| fast_exact_completion | PR selection | 11.236652 | 2.083 | 2.018 [1.916, 2.124] | 1.800 [1.667, 1.902] | 613/3 | 1.225x |
| fast_race_radix | PR selection | 5.923699 | 1.120 | 1.079 [0.907, 1.228] | 0.949 [0.847, 1.054] | 440/176 | 3.150x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.
Comparator/radix_pr ratios: median 1.837, geomean 1.764, aggregate 1.729; radix_pr faster/slower 603/13; worst radix_pr slowdown 1.239x.
Winning-control counts: `sparse_pr`=581, `dense_pr_direct`=1, `klein_pr`=0, `dense_pr_direct_radix`=18, `dense_pr_nearest_radix`=16.
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

Audit SHA-256: `577dab610dd482defcdaa55996e9a71281e8ccccb9420b680790f41ab2b69708`

Raw records SHA-256: `a54fd4ec9107e2b9517b455d221c9f6dfbc7ae6f1f84070f0cb6a37ddbc62060`
