# Independent automated core review

Reviewer: **automated independent agent**, dispatched separately from the implementation agent. This is not human peer review, external acceptance, an established novelty claim, or a conference-readiness verdict.

Completed: 2026-10-19T14:29:45.323920+00:00. The repository had no commit/HEAD at the recorded run; its source, tests, experiment scripts and artifacts were uncommitted. The exact `git status --porcelain` snapshot, package versions, environment and source hashes are retained in [independent_core_review.json](independent_core_review.json). Hashes below identify the reviewed bytes. No core source edits were made by this reviewer.

**Core verdict:** no unresolved Critical or Important algorithm findings in the reviewed snapshot. One Minor unsigned-score bug was reported to the implementation agent, fixed there, and independently confirmed resolved.

The independent reproducibility script is [experiments/independent_review_check.py](../experiments/independent_review_check.py), adapted from the reviewer's original `/tmp/review_sparse_vus.py`. The final rerun added the newly introduced direct-ramp compiled dense baseline to every case, rejected nonfinite outputs, verified the reference SHA-256, and checked that core source hashes did not change during execution. These cases were constructed independently of the repository's `case(index)` test generator; the numerical oracle is the unchanged external reference, not a second copy of the sparse formulas.

Run from the repository root:

```sh
/opt/anaconda3/bin/python experiments/fetch_reference.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 /opt/anaconda3/bin/python experiments/independent_review_check.py --output artifacts/independent_core_review.json
```

The fetch command is only needed when the pinned reference is absent. The completed verification used `/opt/anaconda3/bin/python`, Python 3.12.4, NumPy 1.26.4, Numba 0.59.1, SciPy 1.17.1 and scikit-learn 1.8.0 on macOS 26.6.1 arm64. All three listed thread environment variables were `1`. Total verification time was 60.742567 seconds, including reference calls and any JIT startup; this is **not a performance benchmark**.

The exact external target is `metricor.RangeAUC_volume_opt(..., thre=n)` from `thedatumorg/VUS` commit `467bace0c103f5c2bdb4900306d82939bcac8ff9`. Cached source SHA-256: `bd547c9746fc1b9bbce2895e20cb156f97d23365d5dce8c2a3fab90622ccdced`. Every original score threshold is evaluated; duplicate tied thresholds contribute zero repeated integration area. Claims concern its two scalar outputs and its specified dynamic-label semantics.

Independent cases:

- Exhaustive: sequence lengths 2, 3, and 4; every binary label array containing both classes; every binary score array, including constant scores; widths 0, 1, 2, 3, 4, 7, and 12. Total **1,960 cases**. This covers every boundary-label arrangement in this finite domain, touching/overlapping expansions and widths exceeding sequence length.
- Random: NumPy `default_rng(714099)`, indices 0 through 119; length `rng.integers(2,200)`; Bernoulli label probability independently drawn from `Uniform(.01,.99)`; one random label is flipped only if necessary to ensure both classes. Each third case uses tied values from `[-1e308,-1,-0,1,1e308]`; other cases use standard normal scores. Width is `rng.integers(0,3*n)`. Total **120 cases**. The script preserves draw order exactly.
- Regression: `y=[0,1]`, scores `[0,1]` as both uint8 and uint64, width zero, expected `(ROC,PR)=(1,1)` for all five paths.

All five paths passed all applicable cases at absolute tolerance `1e-11`. Maximum absolute discrepancies against the external oracle:

| Function | Exhaustive | Random |
|---|---:|---:|
| `sparse_vus` | 3.3306690738754696e-16 | 4.4408920985006262e-16 |
| `dense_vus` | 3.3306690738754696e-16 | 4.4408920985006262e-16 |
| `sparse_vus_jit` | 2.2204460492503131e-16 | 2.2204460492503131e-16 |
| `dense_vus_jit` | 2.2204460492503131e-16 | 3.3306690738754696e-16 |
| `dense_vus_direct_jit` | 2.2204460492503131e-16 | 2.2204460492503131e-16 |

Reviewed mathematical reasoning:

- Negative-only score events leave TP, buffer mass, the dynamic denominators, existence count and TPR fixed. Their ROC area is a horizontal rectangle and their PR contribution is zero. The implementation correctly integrates that rectangle **before** the next support-event trapezoid, rather than connecting retained support points directly.
- `before` and `after` count strict and weak score exceedances at a support value. Tied non-support points enter the same transition as tied support points.
- The positive mass is `P0 + selected_buffer_mass/2`, matching the reference's reset of original positive labels. This is threshold-dependent and is not replaced with a static expanded-label sum.
- Expanded ranges preserve the pinned reference's distinction between adjacent and overlapping ranges; first-hit events supply its existence reward.
- Two nearest distinct anomaly intervals suffice for weights: each nonzero ramp contribution is at least `sqrt(1/2)`, so any two contributions saturate the reference's sum-and-clip rule. Original positives remain one.
- The final negative-only rectangle and explicit `(1,1)` ROC endpoint are included. PR uses the reference's right-endpoint step integral.
- With `Q` equal to the number of **positions** in maximum-width expanded support, `M<=Q` distinct support scores and `L` maximum width, preprocessing is `O(n log(Q+1))`, each width costs `O(Q)`, and memory is `O(n+Q)`. Thus the bound `O(n log(Q+1)+(L+1)Q)` is justified for the reviewed algorithm. Replacing Q with distinct-score count would not justify its per-width position loops. No asymptotic gain is promised when Q approaches n.
- The compiled dense implementation traverses all score positions for each width. The added direct-ramp dense implementation constructs the original sum-and-clip ramps independently of the two-nearest lemma, strengthening numerical cross-checks and later performance comparisons.

Resolved Minor finding: `dense_vus` originally negated unsigned scores before casting, so `[0,1]` ranked backwards and returned `(0,.5)`. The implementation agent introduced common input validation and float64 score conversion. The reviewer reran the concrete uint8/uint64 counterexamples and all five paths now return `(1,1)`. Final hashes below are after that fix.

The reviewer also read the scout proof at `/Users/gosmain/Documents/output/research-frontier-20261019/vus-scout/PROOF_AND_PRIOR.md`, the frozen protocol, existing compiled-scaling receipt, and current dtaianomaly adapter/source. The adapter preserves the selected upstream metric method bodies and decorated compiled kernel, hash-checks the imported source, and computes ROC/PR from one shared curve call. This is suitable for evaluating that actual compiled baseline, subject to final parity, thread-control, warm-up and timing receipts. This review did not independently execute the adapter benchmark or establish algorithmic novelty.

Scope limitations: finite tests do not prove universal floating-point equality. The theorem is an exact-arithmetic statement about the specified target; the recorded tests establish numerical agreement on the stated domain. Final public benchmark outcomes, ranking-reversal analysis, exclusions, speed claims, manuscript text, prior-art completeness, publication readiness and acceptance were not reviewed here. No final paper was available at this stage. The later final review must assess those separately.

Source bytes exercised in the final automated check:

| File | SHA-256 |
|---|---|
| `src/sparse_vus/__init__.py` | `59eebc3b776cce8eb1d67b846964e50389515a6b95dcf3054664dbeee06c61d1` |
| `src/sparse_vus/compiled.py` | `3b73ea67e23d92c00018d9a31646bac3bc03b781caca3dfa5ef9155fa47c2f32` |
| `src/sparse_vus/core.py` | `f7e227f3bfea58c72da8feba0c7daa36460695db8ab10106706f845d45374e2b` |
| `experiments/independent_review_check.py` | `5ccd3a13284ddec3f1a91c3b67867d73da1cc50f0cb10e21beb0909c3c778c3d` |

Files inspected during this review, with their hashes when this review document was persisted (these inspection hashes are separate from the run's guarded source hashes):

| File | SHA-256 |
|---|---|
| `src/sparse_vus/core.py` | `f7e227f3bfea58c72da8feba0c7daa36460695db8ab10106706f845d45374e2b` |
| `src/sparse_vus/compiled.py` | `3b73ea67e23d92c00018d9a31646bac3bc03b781caca3dfa5ef9155fa47c2f32` |
| `src/sparse_vus/__init__.py` | `59eebc3b776cce8eb1d67b846964e50389515a6b95dcf3054664dbeee06c61d1` |
| `tests/test_parity.py` | `680f59e09620dbe4189f91c2bc2ccde25a2356c08ec50b3ad4f63d09d6dee06c` |
| `tests/test_compiled.py` | `9c9f27c1a97cbf877d148401d75e358dddfb88b863a07178492c8b2703bd446c` |
| `experiments/fetch_reference.py` | `8c9c9e255598197e42b0a48a59ef97051e456b3c0ef33024a1f4c278b8b0a4c1` |
| `experiments/dtaianomaly_adapter.py` | `7b53d095aa505567d11a9db33068977dd26697b799c1dc2ee28e2a9d14024a64` |
| `experiments/protocol.json` | `b3ce071bc93c251b73121d6c5b3c7348bca3c4f50eee1d1cb0acede87cdcee79` |
| `pyproject.toml` | `224dc7d36059b5c5ee8febd434562f19375de49c916b0c7fd26cbcf4006dbd6d` |
