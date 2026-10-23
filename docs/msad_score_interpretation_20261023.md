# Interpretation of the released MSAD score corpus

This note supplements the immutable acquisition protocol. It does not modify the selected panel, stored arrays, historical manifests, or any primary experimental denominator.

## Score direction and detector provenance

The pinned MSAD configuration names are `AE, CNN, HBOS, IFOREST, IFOREST1, LOF, LSTM, MP, NORMA, OCSVM, PCA, POLY`. Its loader reads all twelve stored vectors unchanged with `header=None`, then applies ROC/PR metrics directly to each column; its VUS threshold test is `score >= threshold`. Thus our higher-is-more-anomalous interpretation matches the public MSAD consumer, with no inferred model-specific sign corrections. [Configuration](https://github.com/boniolp/MSAD/blob/8141b94eb3d2b1811f81ffcf7bc8aa5dcbd6c204/utils/config.py#L28), [loader/evaluation](https://github.com/boniolp/MSAD/blob/8141b94eb3d2b1811f81ffcf7bc8aa5dcbd6c204/utils/scores_loader.py), [threshold implementation](https://github.com/boniolp/MSAD/blob/8141b94eb3d2b1811f81ffcf7bc8aa5dcbd6c204/utils/metrics.py#L398).

The related TSB-UAD repository at revision `313f0fdeba14292b9db4e1aa94c74a983a25de31` corroborates the direction in its open detector wrappers. AE, CNN, LSTM, MP, PCA, and POLY document larger anomaly scores; IForest negates sklearn `score_samples`, LOF negates `negative_outlier_factor_`, and HBOS/OCSVM invert normality scores. The example feeds the resulting `decision_scores_` through increasing min-max scaling. This revision is supporting implementation evidence, not a recovered historical generation revision for the MSAD archive. [TSB-UAD model sources](https://github.com/TheDatumOrg/TSB-UAD/tree/313f0fdeba14292b9db4e1aa94c74a983a25de31/TSB_UAD/models), [example](https://github.com/TheDatumOrg/TSB-UAD/blob/313f0fdeba14292b9db4e1aa94c74a983a25de31/example/scripts/anomaly_detectors.py#L35).

`IFOREST1` is a separately published configuration; do not describe it as a twelfth distinct architecture. The NORMA code is in an encrypted upstream ZIP whose public notice asks users to contact its authors and describes academic/industrial licensing conditions. We neither accessed that implementation nor contacted anyone. Its released-vector direction is supported by MSAD’s common consumer and the benchmark description, not an inspected NORMA fit implementation. [NORMA source notice](https://github.com/TheDatumOrg/TSB-UAD/blob/313f0fdeba14292b9db4e1aa94c74a983a25de31/TSB_UAD/models/norma.txt).

## Stored precision: all models, not a sample

`artifacts/msad-score-provenance-20261023/audit_stored_precision.py` rechecked each member’s SHA256 and lexical decimal precision, bound to the earlier independent full-line/array parser audit. All **1,536 score files / 189,522,168 scalar values** have at most two digits after the decimal point: 128 files and 15,793,514 values for each configuration. Some files omit trailing zeroes; the claim is decimal precision, not one identical serialization format.

Receipt: `artifacts/msad-score-provenance-20261023/stored-precision-audit.json`. Its scope is the actual released text. The generic source writer uses `%.2f`, but the audit does not infer that every file was produced by that function. No score was rounded, rescaled, negated, repaired, or regenerated. Conclusions concern released quantized vectors and do not estimate what unavailable full-precision outputs would have produced.

## One-point overlap audit and fixed-panel sensitivity

Exact whole-array hashes alone missed a plausible transformation: MSAD series often have one fewer observation than related TSB releases. The supplemental `audit_one_point_overlap.py` checked removal of either the first or last point from all prior 350 TSB-AD and twelve mTSBench inputs. It compared labels plus exact observations or standardized observations rounded at ten decimals, using the same hashing definitions as acquisition. Twenty selected series had a **joint observation and label match** under this bounded test. The receipt lists all matches and preserves the frozen panel.

This does not exhaustively detect cropping, resampling, channel reuse, or other transformed-source overlap. The other 108 cases are “without a match under this bounded test,” not proved independent physical recordings. Appropriate terminology is a previously unmeasured published-score workload, with explicit source overlap, rather than an unseen-domain benchmark.

An independent calculation of the width-30/budget-250 primary result imports neither the metric implementations nor the study’s ranking/report functions. It reads a hash-bound complete-line prefix of the append-only metric log and checks all primary oracle comparisons. The overlap subgroup was defined after acquisition and is descriptive; it does not replace the primary analysis.

| Population | Cases | Best-case exact regret ≥0.01 | Affected source families | Maximum regret |
| --- | ---: | ---: | --- | ---: |
| Frozen primary panel | 128 | 8 (6.25%) | YAHOO 4; KDD21 2; MGAB 1; GHL 1 | 0.3985750302 |
| No joint match in the bounded audit | 108 | 4 (3.70%) | YAHOO 3; GHL 1 | 0.2362084785 |
| Joint one-point overlap | 20 | 4 (20.0%) | KDD21 2; MGAB 1; YAHOO 1 | 0.3985750302 |

All 1,536 matched/upstream budget-250 comparisons pass (maximum absolute difference `1.0548e-15`). The 360 dense and 360 upstream full-grid exact controls pass, with maxima `4.4409e-15` and `3.3307e-16`. These are numerical parity checks, not the integer certificate proof. Receipt: `artifacts/msad-score-provenance-20261023/independent-primary-audit.json`.

The original practical promotion rule passes on its declared 128-case panel. Its 5%/three-family threshold does not pass on the descriptive 108-case subset, so the manuscript must not transfer the primary claim to physically unseen recordings. Both the subgroup and the remaining transformation uncertainty should accompany the broader claim.

## Metric and bibliographic interpretation

MSAD’s pinned metric code uses an older static extended-label normalization and trapezoidal PR integration. This study reevaluates the released detector vectors with the explicitly declared dynamic/right-step contract. It does not reproduce or revise the published MSAD metric tables, and it does not show that the original MSAD paper’s reported conclusions are wrong.

The pinned README supplies the bibliography: Emmanouil Sylligardos, Paul Boniol, John Paparrizos, Panos Trahanias, and Themis Palpanas. “Choose Wisely: An Extensive Evaluation of Model Selection for Anomaly Detection in Time Series.” *Proceedings of the VLDB Endowment* 16(11), 2023, 3418–3432. [DOI 10.14778/3611479.3611536](https://doi.org/10.14778/3611479.3611536), [pinned README](https://github.com/boniolp/MSAD/blob/8141b94eb3d2b1811f81ffcf7bc8aa5dcbd6c204/README.md#L47).
