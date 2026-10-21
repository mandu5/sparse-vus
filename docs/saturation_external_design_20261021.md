# External inputs for the saturation confirmation experiment

This document specifies input acquisition, not a timing or efficacy protocol.
The main experiment owner must freeze the saturation implementation and its
confirmation decision before using these inputs for VUS evaluation. This script
never imports or runs any VUS implementation and never evaluates detector quality.

## Sources and metadata-only selection

Use mTSBench metadata from GitHub revision
`0ebf90da7642e103192e05971fdb44e3149bcd51` and data from Hugging Face revision
`8dea9af65a9895f39e9e76f118cf23a94d2d4d0a`. Sources:

- https://github.com/PLAN-Lab/mTSBench
- https://huggingface.co/datasets/PLAN-Lab/mTSBench
- https://openreview.net/attachment?id=8LfB8HD1WU&name=pdf

Before downloading any selected data CSV, preserve the exact metadata bytes,
their SHA-256 hashes, the public file listing, and `selection.json`. Canonicalize
family names by case folding, removing punctuation, and the explicit alias map
in the script. Exclude every canonical family in the existing 350-series corpus;
that existing selected-series manifest and its hash are preserved as evidence.
Keep test files of at most 100,000 rows, then select the first two filenames
lexicographically per remaining family. This yields 12 series in nine new source
families: CalIt2, GECCO, GHL, Genesis, GutenTAG, PSM, metro, room-occupancy and swan.
The frozen selection must contain exactly those counts or acquisition aborts.
No performance, score, label-density or timing outcome selects or replaces a file.
Being absent from this project's old corpus does not prove independence from
every data source or previous experiment in the wider literature.

## Input contract

Preserve all CSV rows in their released order; never sort, crop, resample, join or
drop rows. Require the exact `is_anomaly` column, numeric labels strictly in
{0,1}, and both classes. Exclude columns whose normalized names are timestamp,
datetime, date, time or index. Exclude pandas-style `Unnamed:` index columns only
when they equal consecutive 0-based or 1-based row indices. All remaining
columns must parse numerically; otherwise abort that series and the acquisition.
Replace nonfinite feature entries with the median of the finite values in that
column. Drop a feature with no finite values; abort if no features remain.
Record every dropped column and every imputation count. No feature computation,
fit, parameter selection or score uses the labels.

Compute population mean/std on these feature rows and standardize; constant
columns have scale one and become zero. This is an explicitly unsupervised
whole-series operation. It is not the original benchmark's train/validation
pipeline and makes no claim about deployment-time generalization.

## Four deterministic generated classical controls

These score vectors are evaluator inputs, not a reproduction of the mTSBench
detector results. All scores use higher values for greater anomalousness.

1. `isolation_forest`: sklearn IsolationForest, 100 trees, max_samples=min(256,n),
   max_features=1.0, contamination=auto, bootstrap=False, random_state=20261021,
   n_jobs=1, on standardized features; negate `decision_function`.
2. `pca_reconstruction`: sklearn PCA with full SVD, rank=min(5,d-1), on
   standardized features; mean squared reconstruction residual across features.
   For d=1 use rank-zero reconstruction (zero standardized vector).
3. `knn_distance`: sklearn NearestNeighbors, brute Euclidean distance, n_jobs=1;
   fit to min(2048,n) uniformly spaced row indices from `np.linspace` with int64
   dtype. Query all rows in batches of 512. Score is distance to neighbor
   min(20,reference_count), including self where present in the reference.
4. `robust_marginal_z`: max across features of absolute deviation from the
   whole-series feature median, divided by 1.4826 times median absolute
   deviation. A zero MAD uses population std if positive, otherwise one.

Use one compute thread (BLAS/OpenMP and threadpoolctl), serial series execution,
and record exact Python/library/platform versions. Scores must be aligned,
finite one-dimensional float64 arrays. No label-aware hyperparameter tuning,
metric evaluation, threshold selection or model ranking is performed.

## Artifacts and verification

Downloaded CSVs and arrays live only in ignored `cache/saturation-external`;
the worktree's existing cache is a symlink to the main repository cache. Do not
modify other cache entries. Save one NPZ per series with `labels` and the four
score keys above. Small tracked receipts live in
`artifacts/saturation/external-inputs/`: selection, metadata copies, source and
environment hashes, per-series receipt, and the final machine-readable manifest.
Check downloaded bytes against the pinned Git blob or LFS SHA and byte count;
record their SHA-256 plus each NPZ and constituent-array SHA-256. Do not
redistribute the source data in tracked artifacts. Underlying dataset licenses
remain those specified by the original sources.

Execution order:

1. Run tiny input-contract tests (invalid labels, index handling, imputation,
   label independence and deterministic scores).
2. `python experiments/fetch_saturation_external.py --freeze`
3. `python experiments/fetch_saturation_external.py --generate`
4. `python experiments/fetch_saturation_external.py --verify`

Freeze refuses to overwrite a prior selection. Generation checks the frozen
script/design/environment and metadata identities before any input download.
Each completed series is persisted atomically with a receipt, permitting
verified resume without silently replacing prior arrays. A failure is retained
as a failure receipt; no series replacement is allowed. Verification reads
hashes, shapes and finite/binary conditions only, with no VUS outcomes.
