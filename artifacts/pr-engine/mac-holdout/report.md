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
| sparse_pr | PR only | 6.066328 | 1.774 | 1.620 [1.421, 1.920] | 1.960 [1.511, 2.323] | 271/37 | 1.883x |
| dense_pr_direct | PR only | 13.167399 | 3.331 | 3.160 [2.772, 3.506] | 4.255 [3.349, 5.112] | 306/2 | 1.417x |
| sparse_both | paired ROC+PR | 6.230853 | 1.865 | 1.676 [1.455, 2.009] | 2.014 [1.536, 2.396] | 277/31 | 2.545x |
| dense_nearest_both | paired ROC+PR | 18.998347 | 5.050 | 4.840 [4.356, 5.368] | 6.140 [4.974, 7.181] | 308/0 | 1.000x |
| klein_pr | PR only | 60.186223 | 20.925 | 22.360 [19.764, 24.238] | 19.450 [17.910, 20.623] | 308/0 | 1.000x |
| benchopt_both | paired ROC+PR | 117.555336 | 35.420 | 37.572 [34.754, 41.101] | 37.990 [34.728, 42.965] | 308/0 | 1.000x |
| radix_pr | PR only | 3.094410 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 3.470864 | 1.063 | 1.076 [1.034, 1.131] | 1.122 [1.053, 1.202] | 241/67 | 3.819x |
| dense_pr_direct_radix | PR only | 11.125646 | 2.677 | 2.617 [2.318, 2.870] | 3.595 [2.752, 4.514] | 303/5 | 1.401x |
| dense_pr_nearest_radix | PR only | 10.204247 | 2.599 | 2.519 [2.297, 2.726] | 3.298 [2.624, 3.980] | 307/1 | 1.482x |
| v02_race | PR selection | 7.384401 | 2.110 | 2.081 [1.700, 2.788] | 2.386 [1.741, 3.098] | 287/21 | 1.792x |
| fast_race | PR selection | 5.936008 | 2.009 | 1.757 [1.536, 2.088] | 1.918 [1.495, 2.282] | 281/27 | 1.524x |
| fast_exact_completion | PR selection | 5.932886 | 2.029 | 1.762 [1.540, 2.100] | 1.917 [1.494, 2.270] | 285/23 | 1.704x |
| fast_race_radix | PR selection | 3.148834 | 1.110 | 1.168 [1.064, 1.316] | 1.018 [0.981, 1.077] | 217/91 | 3.065x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.
Comparator/radix_pr ratios: median 1.709, geomean 1.582, aggregate 1.924; radix_pr faster/slower 268/40; worst radix_pr slowdown 1.883x.
Winning-control counts: `sparse_pr`=279, `dense_pr_direct`=1, `klein_pr`=0, `dense_pr_direct_radix`=23, `dense_pr_nearest_radix`=5.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## L=100

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 7.692176 | 1.565 | 1.520 [1.446, 1.632] | 1.769 [1.495, 1.979] | 290/18 | 1.618x |
| dense_pr_direct | PR only | 32.656894 | 5.422 | 5.235 [4.006, 6.319] | 7.511 [4.872, 9.810] | 307/1 | 1.021x |
| sparse_both | paired ROC+PR | 8.529562 | 1.848 | 1.689 [1.572, 1.868] | 1.962 [1.632, 2.188] | 295/13 | 1.505x |
| dense_nearest_both | paired ROC+PR | 38.635733 | 7.151 | 6.804 [5.336, 8.071] | 8.886 [6.078, 11.072] | 308/0 | 1.000x |
| klein_pr | PR only | 161.122238 | 46.685 | 45.789 [34.272, 56.637] | 37.056 [28.045, 45.929] | 308/0 | 1.000x |
| benchopt_both | paired ROC+PR | 247.125679 | 56.887 | 58.796 [47.724, 69.983] | 56.836 [46.154, 68.704] | 308/0 | 1.000x |
| radix_pr | PR only | 4.348025 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 6.239035 | 1.217 | 1.244 [1.160, 1.385] | 1.435 [1.220, 1.741] | 261/47 | 2.226x |
| dense_pr_direct_radix | PR only | 29.888946 | 5.110 | 4.834 [3.728, 5.802] | 6.874 [4.488, 8.943] | 307/1 | 1.076x |
| dense_pr_nearest_radix | PR only | 26.506627 | 4.637 | 4.551 [3.602, 5.370] | 6.096 [4.117, 7.577] | 305/3 | 1.378x |
| v02_race | PR selection | 11.279054 | 1.881 | 2.176 [1.783, 2.954] | 2.594 [1.979, 3.307] | 293/15 | 1.366x |
| fast_race | PR selection | 7.426722 | 1.540 | 1.546 [1.433, 1.724] | 1.708 [1.443, 1.943] | 286/22 | 1.914x |
| fast_exact_completion | PR selection | 7.634104 | 1.709 | 1.629 [1.532, 1.775] | 1.756 [1.501, 1.964] | 299/9 | 1.473x |
| fast_race_radix | PR selection | 4.255161 | 1.071 | 1.090 [0.939, 1.222] | 0.979 [0.888, 1.072] | 195/113 | 2.268x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.
Comparator/radix_pr ratios: median 1.557, geomean 1.500, aggregate 1.734; radix_pr faster/slower 286/22; worst radix_pr slowdown 1.618x.
Winning-control counts: `sparse_pr`=296, `dense_pr_direct`=0, `klein_pr`=0, `dense_pr_direct_radix`=5, `dense_pr_nearest_radix`=7.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## L=300

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 14.379505 | 1.278 | 1.309 [1.242, 1.372] | 1.406 [1.269, 1.530] | 293/15 | 1.640x |
| dense_pr_direct | PR only | 93.476279 | 7.111 | 6.725 [4.370, 9.190] | 9.138 [5.340, 13.035] | 308/0 | 1.000x |
| sparse_both | paired ROC+PR | 18.997056 | 1.706 | 1.658 [1.579, 1.759] | 1.857 [1.636, 1.995] | 305/3 | 1.587x |
| dense_nearest_both | paired ROC+PR | 101.950071 | 8.461 | 7.899 [5.192, 10.723] | 9.967 [5.947, 13.872] | 305/3 | 1.135x |
| klein_pr | PR only | 479.670120 | 59.076 | 62.558 [40.400, 88.763] | 46.892 [31.412, 68.485] | 308/0 | 1.000x |
| benchopt_both | paired ROC+PR | 679.831780 | 70.368 | 70.196 [47.469, 95.789] | 66.460 [45.752, 95.799] | 308/0 | 1.000x |
| radix_pr | PR only | 10.229209 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 17.868154 | 1.397 | 1.421 [1.302, 1.605] | 1.747 [1.493, 2.070] | 292/16 | 1.686x |
| dense_pr_direct_radix | PR only | 90.525759 | 6.916 | 6.534 [4.259, 8.903] | 8.850 [5.163, 12.681] | 308/0 | 1.000x |
| dense_pr_nearest_radix | PR only | 80.733295 | 6.294 | 6.000 [3.902, 8.163] | 7.892 [4.670, 11.080] | 300/8 | 1.487x |
| v02_race | PR selection | 25.640018 | 1.337 | 1.631 [1.265, 2.153] | 2.507 [1.722, 3.309] | 223/85 | 2.547x |
| fast_race | PR selection | 12.862485 | 1.146 | 1.064 [0.915, 1.180] | 1.257 [1.070, 1.378] | 184/124 | 2.513x |
| fast_exact_completion | PR selection | 14.456460 | 1.339 | 1.350 [1.282, 1.408] | 1.413 [1.267, 1.534] | 302/6 | 1.589x |
| fast_race_radix | PR selection | 8.559594 | 0.890 | 0.790 [0.614, 0.926] | 0.837 [0.711, 0.932] | 109/199 | 5.410x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.
Comparator/radix_pr ratios: median 1.278, geomean 1.293, aggregate 1.375; radix_pr faster/slower 285/23; worst radix_pr slowdown 1.640x.
Winning-control counts: `sparse_pr`=295, `dense_pr_direct`=0, `klein_pr`=0, `dense_pr_direct_radix`=0, `dense_pr_nearest_radix`=13.
No CI is computed for this retrospective oracle; frozen decisions are unchanged. Exact timing ties use lexicographic attribution, with all tied controls retained in JSON.

The JSON includes all four reference methods, every comparator, complete negative-case lists, oracle choices, family effects, and work accounting.

## Combined L=30/100 (descriptive)

| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse_pr | PR only | 13.758504 | 1.653 | 1.569 [1.440, 1.771] | 1.849 [1.504, 2.104] | 561/55 | 1.883x |
| dense_pr_direct | PR only | 45.824293 | 4.062 | 4.067 [3.355, 4.647] | 6.157 [4.329, 7.777] | 613/3 | 1.417x |
| sparse_both | paired ROC+PR | 14.760415 | 1.849 | 1.683 [1.513, 1.935] | 1.983 [1.596, 2.266] | 572/44 | 2.545x |
| dense_nearest_both | paired ROC+PR | 57.634080 | 5.770 | 5.739 [4.887, 6.436] | 7.744 [5.690, 9.332] | 616/0 | 1.000x |
| klein_pr | PR only | 221.308462 | 28.974 | 31.998 [26.149, 36.854] | 29.736 [24.359, 34.293] | 616/0 | 1.000x |
| benchopt_both | paired ROC+PR | 364.681014 | 45.359 | 47.000 [41.027, 52.359] | 49.000 [41.959, 56.958] | 616/0 | 1.000x |
| radix_pr | PR only | 7.442435 | reference | — | — | — | — |
| radix_both | paired ROC+PR | 9.709900 | 1.129 | 1.157 [1.098, 1.247] | 1.305 [1.153, 1.529] | 502/114 | 3.819x |
| dense_pr_direct_radix | PR only | 41.014591 | 3.495 | 3.557 [2.952, 4.034] | 5.511 [3.835, 7.040] | 610/6 | 1.401x |
| dense_pr_nearest_radix | PR only | 36.710874 | 3.343 | 3.386 [2.897, 3.764] | 4.933 [3.579, 6.021] | 612/4 | 1.482x |
| v02_race | PR selection | 18.663455 | 2.012 | 2.128 [1.753, 2.862] | 2.508 [1.894, 3.224] | 580/36 | 1.792x |
| fast_race | PR selection | 13.362730 | 1.720 | 1.648 [1.503, 1.894] | 1.795 [1.466, 2.074] | 567/49 | 1.914x |
| fast_exact_completion | PR selection | 13.566990 | 1.792 | 1.695 [1.545, 1.924] | 1.823 [1.499, 2.075] | 584/32 | 1.704x |
| fast_race_radix | PR selection | 7.403995 | 1.096 | 1.128 [1.007, 1.262] | 0.995 [0.928, 1.072] | 412/204 | 3.065x |

**Post-protocol descriptive PR-only oracle.** Minimum per-case time among `sparse_pr`, `dense_pr_direct`, `klein_pr`, `dense_pr_direct_radix`, `dense_pr_nearest_radix`.
Comparator/radix_pr ratios: median 1.623, geomean 1.541, aggregate 1.813; radix_pr faster/slower 554/62; worst radix_pr slowdown 1.883x.
Winning-control counts: `sparse_pr`=575, `dense_pr_direct`=1, `klein_pr`=0, `dense_pr_direct_radix`=28, `dense_pr_nearest_radix`=12.
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

Audit SHA-256: `a9d44deb51fa3d764a923a52217012498a574847ebee798ddf343f1e90f0d28f`

Raw records SHA-256: `499f69e0e767f0c4971b8cc9cd839e3eedec3cb20f945b1cc6221f2604dd3228`
