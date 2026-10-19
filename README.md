# Sparse VUS

Exact scalar VUS-ROC and VUS-PR by eliminating threshold events that cannot
change weighted anomaly state. The implementation targets a pinned official
VUS definition, including dynamic label mass and expanded-interval existence.

For sequence length `n`, maximum buffer width `L`, and `Q` positions in the
maximum expanded anomaly support, the algorithm takes
`O(n log(Q+1) + (L+1)Q)` time. The compiled scalar implementation uses
`O(n+Q)` space. The NumPy diagnostic version additionally retains `O(L)`
per-width areas. `Q` counts positions, not distinct scores.

The contribution is support-event elimination with exact integration and
off-support rank counting. Fast VUS and large CPU/GPU speedups have prior art,
which we distinguish from this support-sensitive reduction. See [the proof](docs/theory.md),
[prior art and licenses](THIRD_PARTY.md), and [the manuscript](paper/main.pdf).

## Install and use

Python 3.11 or 3.12 is recommended for the tested research environment.

```bash
git clone https://github.com/mandu5/sparse-vus.git
cd sparse-vus
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install '.[accelerate,research]'
```

The measured Python 3.12.4 environment is recorded in
[requirements-benchmark.txt](experiments/requirements-benchmark.txt) and the
benchmark environment receipts. Use that pin file when recreating the measured
dependency versions; the package itself supports the ranges in `pyproject.toml`.

```python
from sparse_vus import sparse_vus

labels = [0, 1, 0, 0, 1, 0]
scores = [1, 2, 3, 4, 5, 6]
vus_roc, vus_pr = sparse_vus(labels, scores, max_buffer=4)
# (0.6892652251673258, 0.6834092121537311)
```

For the compiled implementation:

```python
from sparse_vus.compiled import sparse_vus_jit

vus_roc, vus_pr = sparse_vus_jit(labels, scores, max_buffer=4)
```

The first compiled call includes JIT initialization. Inputs must be finite,
one-dimensional score values, binary labels with both classes, and a
nonnegative integer maximum buffer width. Scores are converted to float64;
arbitrary-precision integer ranking is outside the API contract. All integer
widths from zero through `max_buffer` are averaged. Scalar integrals are
returned; the full surface is not materialized.

## Verify numerical correctness

The official reference is fetched into ignored cache rather than vendored.
Its SHA-256 and commit are pinned.

```bash
python experiments/fetch_reference.py
python experiments/dtaianomaly_adapter.py --fetch
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python -m pytest -q
python experiments/independent_review_check.py
```

The main suite includes 1,000 distinct randomized cases, six structured edge
cases, input validation, independently implemented dense baselines, sampled
threshold checks, and a real compiled dtaianomaly adapter. Test counts are
not counts of independent datasets. The independent reviewer also exercised
1,960 exhaustive tiny-domain cases and 120 additional randomized cases.

## Reproduce public-score experiments

The frozen corpus consists of all 350 common TSB-AD-U evaluation series for
three released score vectors: Chronos-Bolt base, Time-MoE 200M, and TimesFM
1.0 200M, all with context length 64. No model training or inference is run.

```bash
python experiments/create_reproduction_workspace.py --output ../sparse-vus-reproduction
cd ../sparse-vus-reproduction
python3.12 -m venv .venv
source .venv/bin/activate
bash experiments/run_reproduction.sh
```

Use a new output directory. This preserves the published measurements and
creates a separate workspace containing source and frozen protocols. The
serial script installs the measured dependencies, fetches pinned references
and public data, runs tests and all experiments, validates the results, and
regenerates figures and the manuscript. Python 3.12 and `tectonic` must be
available. Run timings without other CPU-intensive work.

To rerun only the external comparison while retaining the published main
records, use `python experiments/reproduce_external_supplement.py`; it writes
to a new timestamped directory.

The range downloader fetches approximately 378 MB of score records and a
73 MB label archive. It checks every selected ZIP member's CRC and SHA-256.
The score ZIPs contain sparse holes for unused forecast records; their apparent
file sizes exceed downloaded bytes. Whole-archive MD5 verification is not
claimed. Do not use `testzip()` over unrequested forecast members of these
partial archives. Raw data are ignored by Git and are not redistributed.

`experiments/protocol.json`, `data_manifest.json`, and `protocol_addendum.json`
fix selection and analysis before evaluation. All released score vectors are
used unchanged, including the source README's documented zero padding. This
tests metric computation and does not reproduce the source model leaderboard.

Main timings use three randomized-order repetitions and one compute thread.
Compilation, source download, and data download are excluded and reported
separately. The principal exact baseline is the fastest of NumPy dense,
Numba dense with nearest distances, and independent Numba direct-ramp dense,
chosen separately for each input. The actual dtaianomaly implementation is
also tested at 250 and all thresholds on a frozen 12-series NAB subset.
The official 250-threshold baseline is a different-resolution computation.

## Results and limits

On **350 public series from 23 dataset families**, with three released model
score vectors and two width ranges (2,100 evaluations), compiled Sparse VUS
has a **2.06× median speedup** over the fastest of three dense implementations
chosen separately for each input. It is faster in 1,916 cases and slower in
184; the full ratio range is 0.27–7.50×. Maximum numerical disagreement is
`3.70e-13`.

Using 250 thresholds instead of all thresholds produces a maximum absolute
VUS-PR error of **0.583** on this corpus and **84 strict ordering reversals
among 2,100 paired model comparisons**, affecting 55 series. The unique best
of the three models changes in 50 of 700 series/width cases. Exact evaluation
removes this sampling approximation; it does not change the underlying metric.

A separate full-length comparison uses 42 series spanning all 23 families.
Against the actual pinned dtaianomaly implementation, sparse exact evaluation
has median speed ratio 143.85× on the 35 completed all-threshold comparisons;
seven baseline calls are right-censored at ten seconds and receive no speed
ratio. All 42 default 250-threshold comparisons complete, with median ratio
8.17×. These medians have different completion scopes.

Machine-readable outcomes live in `artifacts/public_benchmark_receipt.json`
and `artifacts/analysis_summary.json`; individual paired measurements are in
`artifacts/public_benchmark.jsonl`. The artifact verification gate enforces finite
results and numerical agreement, including all external baselines.
The manuscript reports dense-support slowdowns, approximation error, ranking
reversals, and the external-comparison scope. A faster synthetic case alone
does not establish a better algorithm on every real input.

The Sylligardos 2025 fast VUS implementation could not be located and is not
benchmarked. The public Go `adscore` implementation was executed natively,
but computes different semantics and is not used as an exact-target speed
baseline. See `artifacts/native_go_audit.json`.

## Build the manuscript

The tracked result tables and figures can be typeset directly:

```bash
cd paper
tectonic main.tex
```

To regenerate tables and figures from the recorded measurements, fetch the
pinned references first, then run `python experiments/analyze_results.py`.
The analysis verifies the recorded input and source hashes before reading them.

The supplied PDF is a working research manuscript. Source, executable protocols,
raw measurements, and separately authored in-session validation are included.

## Attribution

The metric is due to Paparrizos et al. (PVLDB 2022) and its optimized official
implementations to Boniol et al. (VLDB Journal 2025). Scores are from Zhu,
Carpentier, and Verbeke (ICLR 2026),
[KU Leuven RDR DOI 10.48804/MCVI4N](https://doi.org/10.48804/MCVI4N), CC BY 4.0.
Raw labels are from [TSB-AD](https://github.com/TheDatumOrg/TSB-AD).
Full attribution, prior-art boundaries, and license handling are in
[THIRD_PARTY.md](THIRD_PARTY.md).
