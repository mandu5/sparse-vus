# Three focused additions after the fourth blind review

These follow-ups were defined after the original results and before their own
measurements. They do not replace the primary width, corpus, comparator,
confidence intervals or five/six-point investment criteria. Earlier reviews and
the initial `Revise` recommendation remain in their original files.

## 1. Compilation-matched conventional support control — complete

The new control shares validation, radix ordering and global tie counts. It
constructs each width using direct summed/clipped ramps and component scans,
with support-local scratch and cached original-positive group mass. It does
not use nearest-distance geometry. This is an optimized author-created
reimplementation of the support-cumsum approach, not upstream Klein.

Six balanced orders cover all 73 original recordings and eight score vectors;
six balanced full-workflow passes cover each collection. An independent auditor
reconstructed 1,314 calls and 54 workflows with maximum PR discrepancy
`4.44e-16`. The following are case geometric ratios, with familywise 95% bounds
across three collections per comparator.

| Collection | Control / released | Control / stream | Workflow control / stream |
| --- | --- | --- | ---: |
| NAB | 0.910 [0.905, 0.915] | 1.357 [1.291, 1.427] | 1.177 |
| SMAP | 0.960 [0.945, 0.973] | 1.201 [1.180, 1.224] | 1.126 |
| SMD | 0.978 [0.969, 0.985] | 1.166 [1.158, 1.174] | 1.152 |

**The conventional control beats the released scalar method on all 73 cases.**
This rules out a separate nearest-geometry runtime advantage on the primary
panel. The stream result retains a smaller gain over this authored control.
The large unchanged-public-API ratios remain correct, but cannot be interpreted
as an isolated geometric effect. The manuscript now makes this negative result
explicit. The exact event identity/ROC correction and complexity statement are
separate from an empirical assertion that one implementation of that identity
is always fastest.

Evidence: `artifacts/pvldb-research-20261024/compiled-support-control/`.

## 2. Public repeated-profile consumer — complete, small total benefit

The fixed consumer is TSB-AD `get_metrics` at revision
`303dffbfc11612995b17b06633f8c9d0ea0e38e5`, with all nine metric outputs.
Only the scalar VUS callback is replaced: both backends return exact ROC and
PR, using unchanged public Benchopt or the sparse radix implementation. Seven
non-VUS metrics, including the upstream threshold-search loops, remain intact.
The public width estimator also remains unchanged. All fourteen source/license
files were re-downloaded from the pinned revision, byte-compared, and assigned
fixed hashes checked even for cache hits.

The largest primary recording is selected by input length, with lexicographic
tie break, before consumer outcomes. Eight stored profiles are evaluated in
four complete read-to-CSV-close passes, ABBA order. The trace records total,
per-profile and VUS time. This is stored-profile re-evaluation, not the full
upstream training script, a service deployment or a population benchmark.

The first attempt failed during import, before any measurement, because the
base statsmodels 0.14.2 uses a pandas decorator signature incompatible with
pandas 3.0.1. Its traceback is preserved. A local `--no-deps` overlay pins
statsmodels 0.14.6; the numerical packages used by earlier experiments are
unchanged. The frozen producer and public source bytes are unchanged.

The recording is `182_SMD_id_5_Facility_tr_7174_1st_21230` (28,696 points);
the public estimator selects width 125. All 32 nine-metric calls and four
workflows completed. The independent trace audit checks the input-length choice,
width, eight profiles, ABBA order, source hashes, nested timings and paired
outputs (maximum difference `3.44e-15`). It does not reimplement the seven
non-VUS metrics.

| Exact VUS backend | Median whole nine-metric time | Median VUS time |
| --- | ---: | ---: |
| Public Benchopt | 34.2603 s | 0.928865 s |
| Sparse radix pair | 33.2340 s | 0.014060 s |

VUS itself improves 66.07-fold, but the complete consumer improves only
**1.03088-fold**. VUS is 2.70–2.72% of baseline time; other metrics dominate.
This is an explicit limitation on application significance, not a successful
demonstration of large whole-benchmark acceleration. Two fixed-input timings
per backend support a descriptive result, not a population confidence interval.
The large earlier VUS-only workflow ratios retain their narrower scope.

## 3. Inspectable second-host score diagnosis — complete

Fresh Mac/Linux runs preserve observations, labels, all eight score arrays,
standardized matrices, fit indices, SVM support vectors/coefficients/intercept,
package versions and loaded numerical-backend information. The independent
analysis also evaluates both sets of saved arrays on one Mac evaluator host
against unchanged exact Klein.

- Raw inputs and standardized matrices are byte-identical.
- Fitted SVM support-vector counts are 104 on Mac and 105 on Linux. Both fits
  have status 0 and 133 iterations; maximum SVM score difference is 0.000119587.
- The same evaluator host reproduces the two SVM PR values, 0.3092648648 and
  0.3329318469. Public-comparator error is at most `5.56e-17`.
- Mac's full score hash equals the original experiment. The new Linux full
  eight-model hash differs from the earlier Linux runner; other exact metric
  differences reach 0.000582135. The SVM value and 250-threshold winner change
  reproduce the previously observed discrepancy. This is a diagnostic repeat,
  not recovery of missing original arrays.

The observed SVM difference is localized after standardization to fitted-state
and score generation, not the VUS evaluator. This is not an intervention proving
that a particular BLAS library, compiler flag or CPU instruction caused it.

Evidence: `artifacts/pvldb-research-20261024/score-host-probe/`, including
the [completed Linux diagnostic](https://github.com/mandu5/sparse-vus/actions/runs/40057467287).
