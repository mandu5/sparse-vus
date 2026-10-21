# Independent PR protocol and radix source review — 2026-10-21

Result: the two concrete protocol/audit issues identified below are resolved in the final source inspected at commit `06a14d04e59a62ef0840aae837107bfd85c4400b`. No remaining concrete blocker was found within this review's scope. This is an in-session source review by a separate AI agent in the same project and environment. It is not external peer review, an independent laboratory reproduction, a formal floating-point proof, or a claim of performance superiority.

The review covered the paired experiment driver, independent receipt auditor, their targeted tests, radix preparation and its tests, and the radix preparation dispatch in the fast racer. The original review preceded formal development timing. This document was written during the formal development run using only source reads, small-file hashing, Git object comparison, and this text write. No tests or benchmarks were run during that active timing period, and no development or holdout outcomes were inspected for this review.

## Findings and resolutions

| Finding | Original evidence | Resolution in the reviewed commit | Regression evidence inspected |
| --- | --- | --- | --- |
| Completion work could be reported without fallback models. | In the existing tiny receipt fixture, replacing `fast_race.fallback_models` with `[]` left `adaptive_curve_evaluations=0` and `completion_curve_evaluations=93`. The independent auditor accepted the receipt and reconstructed zero fallback models. This was reproduced by this reviewer before formal timing, without invoking metric kernels. | `audit_records` now requires completion evaluations to be no greater than the sum of queried widths of the declared fallback models. Every nonfallback model must also stay within its adaptive width cap. These augment the existing exact-completion, phase-sum, and no-recomputation checks. | `test_reject_false_claims_even_when_basic_coverage_is_plausible[hidden_fallback]` in `tests/test_pr_engine_audit.py` preserves the counterexample and expects rejection. The final checks were inspected at `experiments/audit_pr_engine.py:247–250`. |
| A method's timer could include destruction of the preceding method's result. | The original loop assigned a new return value to `result` between the start and stop timestamps. In CPython, replacing that reference can release the preceding racer's richer result during the next method's timer. This was a source-level finding; its latency effect was not estimated. | Each call now uses `timed_call`. It stops the timer, converts the receipt, and explicitly deletes the raw result before returning. The next randomized method starts after that cleanup. | `test_previous_result_cleanup_cannot_be_charged_to_next_method` verifies two calls produce `clock, metric, clock, serialize, cleanup` in that order. The helper and regression were inspected at `experiments/benchmark_pr_engine.py:211` and `tests/test_pr_engine_audit.py:364`. |

The initial audit counterexample produced this output:

```json
{"audit_accepted": true, "reported_fallback_models": 0, "completion_curve_evaluations": 93, "adaptive_curve_evaluations": 0}
```

The root agent subsequently reported **3,012 full-suite tests passed**, and the experiment implementer reported **196 targeted tests passed** after the fixes. These counts are attributed team reports, not test executions independently repeated by this reviewer. This reviewer directly inspected the final fixes and regression definitions. The existing all-adapter integration test covers the optional thirteenth development method as well as the twelve mandatory methods.

## Protocol and arithmetic assessment

The twelve mandatory methods are `sparse_pr`, `dense_pr_direct`, `sparse_both`, `dense_nearest_both`, `klein_pr`, `benchopt_both`, `radix_pr`, `radix_both`, `v02_race`, `fast_race`, `fast_exact_completion`, and `fast_race_radix`. The additional `fast_full_budget` variant is restricted to development. Exact method wrappers evaluate all three models and construct the winner set inside the timed call. Racer preparation, control work, exact remainder, and API result construction are also timed. Input loading, warmed imports/JIT compilation, receipt serialization, and raw-result cleanup are outside that interval. The paired-output controls and Benchopt perform additional ROC work; the PR-only controls make that distinction visible.

The freeze operation constructs the 42-series development partition and the exact 308-series complement from released metadata and input hashes. It does not load new metric inputs or execute metric adapters. Execution validates the frozen protocol hash, complete input identities, and measured source hashes before input loading; it also checks source hashes after warmup and after measurements. The completed-run auditor separately reconciles actual label and score archive members against the immutable release bindings. These are integrity and consistency checks; hashes alone do not independently prove the historical time of a freeze. The 308 series were used in earlier exact-metric studies and are held out only from this new policy-development process, not unseen external data.

The driver and auditor agree on the arithmetic: the per-case ratio is comparator median time divided by method median time, with each median taken over three serial repetitions. The geometric mean averages log ratios; the aggregate ratio divides the sum of comparator medians by the sum of method medians. It is not the mean or median of ratios. The family bootstrap samples the observed family clusters with replacement and retains all cases in every sampled cluster. Its 2,000 replicates preserve pairing and cluster multiplicities, including both widths for the descriptive combined 30/100 report. The producer uses NumPy aggregation and the auditor reconstructs it with standard-library arithmetic. The uncertainty statement correctly excludes uncertainty from having only three timing repetitions, and separately reports within-case timing spread.

All three decision rules use L=30, require the lower bounds of both the geometric-mean and aggregate-ratio 95% family-bootstrap intervals to exceed one against every named control, and require semantic checks to pass. The controls are:

| Evaluated method | Required controls |
| --- | --- |
| `fast_race` | `sparse_pr`, `dense_pr_direct`, `radix_pr` |
| `radix_pr` | `sparse_pr`, `dense_pr_direct`, `dense_nearest_both` |
| `fast_race_radix` | `sparse_pr`, `dense_pr_direct`, `radix_pr` |

L=100 is secondary and L=300 is stress evidence. The separate decisions do not establish a global SOTA result. This review checks their implemented definitions and reconstruction, not whether measured outcomes satisfy them.

## Radix exactness and complexity assessment

For finite float64 inputs, the key transform reverses the positive ordering, preserves the correct descending ordering among negative bit patterns, and maps both signed zeros to one key. Eight stable byte-counting passes therefore order every global score group without splitting equal numeric thresholds. The shared validator retains the previous float64 conversion contract; integer values that convert to the same float64 remain tied.

The support-rank scan advances through complete global tie groups. It records the ranks before and after the entire group, including off-support scores, and creates a metric event only when the group contains a support point. Consequently the group IDs and global counts have the same meaning as the original preparation. The nearest-two scan advances monotonically through ordered intervals and checks the two immediate intervals on either side of each support position; more distant intervals on either side cannot displace those candidates. The resulting arrays feed the existing metric kernels.

The test source covers all twelve preparation outputs, oracle parity, complete off-support ties, signed zeros, extreme finite/subnormal values, big-endian conversion, strided and reversed arrays, read-only arrays, unsigned integers, input preservation, single intervals, clipping, adjacency, and overlap. The racer dispatch selects `_prepare_radix` before preparing each model and retains the same controller and result accounting. This assessment was read-only; the test sources were inspected rather than rerun by this reviewer.

The stated preparation bound O(n+Q+K) is consistent with the scans and eight fixed radix passes under the declared fixed-64-bit word-RAM model. The exhaustive kernels take O(n+(L+1)Q), using G,K ≤ Q. Input-sized keys, permutations, and scratch arrays justify O(n+Q+L) auxiliary space rather than support-only storage. These bounds apply to the exact radix evaluator; they do not remove the separate adaptive racer's controller overhead or establish a constant-factor wall-clock overhead guarantee. Generic radix sorting is prior art, and this source review does not establish novelty.

## Exact source versions

All files below were hashed when this document was prepared and compared byte-for-byte with their Git objects at commit `06a14d04e59a62ef0840aae837107bfd85c4400b`. Every comparison matched. The three final protocol/audit files include both fixes above. The core and metric-kernel files were inspected as dependency context; this document does not claim a fresh comprehensive audit of those older kernels.

| File | SHA-256 |
| --- | --- |
| `experiments/benchmark_pr_engine.py` | `7e22d6beb6e58683d467e0c4f17fb5285a51194dfe4d43aeee5c0db9d6b265c4` |
| `experiments/audit_pr_engine.py` | `2fd93ee8bb10ffd4546294d43e6e58c0bad41bcd3ae406e61dd9b13e8cd137a3` |
| `tests/test_pr_engine_audit.py` | `c7dcc1825987b20e3dbfbe8a8a96bddb699b119d6b9ebd3e38fc6e28065935cf` |
| `src/sparse_vus/radix.py` | `d8d45d3cc15105f1771aa37cf3cac95b6138a2f1ee38ee464fc940c54a55a3f5` |
| `tests/test_radix.py` | `954153ff860b5c406697873394c8bdf51c09ceecc28ebf4bd930662d39136aa5` |
| `src/sparse_vus/fast_racing.py` | `0408541b48b5306af7283c5d39df8c84ec0eec5d5b9713733112d71d1be2e4f5` |
| `tests/test_fast_racing.py` | `56812dc3219e175d60ce967bce0c963611c9861d99208ed24c2783ae335ddd41` |
| `src/sparse_vus/core.py` | `f7e227f3bfea58c72da8feba0c7daa36460695db8ab10106706f845d45374e2b` |
| `src/sparse_vus/pr_compiled.py` | `60afd9a2bc584bf670500d772552625064cdec01bb00ae76246006c163b70646` |
| `src/sparse_vus/compiled.py` | `3b73ea67e23d92c00018d9a31646bac3bc03b781caca3dfa5ef9155fa47c2f32` |

Floating-point bounds remain numerically audited rather than outward-rounded formal certificates. Retained curve bytes are not peak process memory. Benchmark results, held-out execution, independent post-run data reconciliation, external review, and publication acceptance are separate evidence gates.

## Pre-holdout fairness addendum

During the active v2 development run, the root agent requested an additional assessment of matched dense controls. This reviewer agrees that two stronger PR-only dense controls are needed before attributing a measured advantage specifically to sparse support compression. The current `dense_pr_direct` uses comparison sorting and direct ramp construction; `dense_nearest_both` also uses comparison sorting and computes ROC. Generic radix ordering, linear nearest-interval preparation, and omission of ROC can benefit a dense implementation too. The v2 experiment remains valid for its explicitly named comparators and frozen decision definitions; it does not isolate those generic gains from the sparse representation's contribution.

The agreed amendment is to add `dense_pr_direct_radix` and `dense_pr_nearest_radix` in a separate module after v2 execution finishes. The direct control should use the actual shared radix key/order helpers and the unchanged direct PR kernel. The nearest control should use the same radix ordering, the linear nearest-two scan over all n positions, and a compiled PR-only sweep over every position at every width, with reusable scratch arrays. It must not construct and discard sparse support ranks. Both controls must include their validation, ordering, geometry, and all model evaluations in the timed call. This provides matched dense controls without assuming an unimplemented optimization or selecting a per-case oracle.

These controls and their source bindings, all-adapter parity tests, accounting rules, and decision thresholds must be incorporated in protocol v3 before measuring the 308-series policy holdout. The matched dense controls should be included in the required comparisons for any sparse/racing speedup claim. With both additions, v3 has fourteen mandatory methods and the same optional development-only full-budget method. Performance comparisons must use fresh measurements paired within the same v3 execution; old v2 timings must not be inserted as if they were concurrent controls.

The root agent agreed to preserve the complete v2 source/protocol/results history, leave the active measured source unchanged, and document v3 as a subsequent fairness amendment. No holdout-based tuning or oracle routing is authorized by this amendment. The implementation and validation of these new controls remain pending at the time of this addendum, so the source hashes above identify only the reviewed v2 snapshot and do not certify the future v3 implementation. A new frozen manifest and source review are required for that version.
