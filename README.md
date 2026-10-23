# Sparse VUS

## Unified research manuscript (23 October 2026)

[Sparse Events and Complete-Tie Prefixes for Exact VUS Evaluation (PDF)](paper/sparse_vus.pdf)
presents the support-event evaluator and its active-prefix and complete-tie
extensions as one research article. The public v0.3.0 software precursor is
cited with its actual date; its measurements are not assigned to new code.
[Reproduction guide](docs/sparse_vus_reproduction_20261023.md) ·
[Submission packet](docs/sparse_vus_submission_packet_20261023.md) ·
[Prior-art audit](docs/active_prefix_novelty_audit_20261023.md).

The whole-evaluator study passes its frozen five-control primary criterion on
both CPU platforms. Across 308 series, primary-width median ratios against
Klein fast-VUS are **20.925× (Mac)** and **14.538× (Linux)**; against matched
nearest-distance dense radix PR they are **2.599×** and **4.791×**. These are
complete three-model evaluation tasks, with imports, JIT and I/O excluded.
The separate incremental active-prefix primary failures remain reported below.

A separate **directly timed disk-to-JSON workflow** reads 308 stored NPZ files
(379 MB), evaluates all 924 scores at `L=30`, selects the best-model sets, and
writes the results. Across three repetitions per method, whole-operation
medians are **3.187 s (sparse radix), 11.298 s (matched dense radix), and
63.647 s (Klein)**: descriptive ratios of **3.545×** and **19.973×**. All nine
passes return identical selected-model sets, with maximum pairwise PR
difference `1.333e-15`. This uses warmed filesystem/JIT state on the active
Mac desktop; detector inference and durable-storage latency are outside the
operation. All nine times and the frozen order are in
[the collection report](artifacts/collection-workflow/mac-20261023/report.json).

The new `sparse_vus.tie_runs` module aggregates complete numerical score classes
by contiguous temporal runs for **one original anomaly interval**. An integer
stopping certificate bounds the number of visited classes by `3*P0`; bounded
fragmentation gives `O(n+L)` time for a singleton even with large ties. Exact
three-limb prefix subtraction avoids cancellation in sums of rounded roots.
The theorem distinguishes exact metric arithmetic from the implemented local
mass-error bound and measured scalar parity.

All 131 prespecified run-study cases pass parity and work-count checks. A
separate verifier checks 650 random metric cases, 36 complete integrals using
80-digit Decimal arithmetic, and exact prefix/carry/borrow operations. At
`L=2048`, the all-tied singleton examines 2,049 runs instead of 2,099,201
active positions and is 8.816× faster than the position-prefix implementation.
Alternating ties are a negative control, and real-score results do not support
replacing active prefix broadly. Full timings and losses are retained in
[the frozen report](artifacts/tie-runs/mac-20261023/report.json).

The portable regeneration route also completed **68 cases and 1,360 timed
calls per host** on Mac and a fresh Linux runner. Both pass parity and work
checks; maximum discrepancy from radix is `2.23e-16`. This is procedural
replication on previously studied data: all 48 generated Mac score vectors
match historical bytes, but only 9 of 48 Linux vectors do. See the
[Mac report](artifacts/tie-runs/mac-regenerated-20261023-retry1/report.json),
[Linux report](artifacts/tie-runs/linux-39900063718/report.json), and
[executed Linux workflow](https://github.com/mandu5/sparse-vus/actions/runs/39900063718).
The 63 historical development cases are outside this portable subset.

## Active-prefix research branch (21 October 2026)

This branch adds an evaluator whose complete-call bound is
`O(n + L + alpha(K) * sum(J_w))`, where `J_w` counts the visited active
positions through a complete terminating score tie. For one original anomaly
interval and distinct support scores it takes `O(n + L*P0)` time for any
score ordering. A singleton with `L <= n` has optimal `Theta(n)` worst-case
time under the stated deterministic score-query and fixed-binary64 model.

[Focused manuscript (PDF)](paper/active_prefix.pdf) ·
[Reproduce and inspect the evidence](docs/active_prefix_reproduction_20261021.md) ·
[Mathematical review](docs/saturation_math_review_20261021.md)

The three frozen main studies retain **all 666 cases**. Their width-30
primary runtime criterion **fails on each run**. At the prespecified width-300
stress condition, the external median speedups over released sparse radix
are **1.506× on Mac and 1.627× on Linux**, with all 48 cases faster per host.
Other matched controls still win some cases. The 16-case structural study
checks the predicted linear/quadratic traversal separation and the all-tied
counterexample. The paper reports the complete comparisons and limitations.

```python
# Install this research branch with .[accelerate], rather than the older tag.
from sparse_vus.saturation import sparse_pr_saturation_jit, sparse_vus_saturation_jit

labels = [0, 1, 0, 0, 1, 0]
scores = [1, 2, 3, 4, 5, 6]
pr = sparse_pr_saturation_jit(labels, scores, max_buffer=4)
roc, pr = sparse_vus_saturation_jit(labels, scores, max_buffer=4)
```

The manuscript is a research artifact; publication and editorial status are
tracked separately from test, numerical-parity and timing results. The
previous v0.3.0 release and its distinct experiments remain documented below.

## Released support-event evaluator

Exact scalar VUS-ROC and VUS-PR through support-event elimination. The new
radix evaluator combines this reduction with established fixed-width score
ordering and linear interval geometry. For finite binary64 scores it takes
`O(n + (L+1)Q)` time under the stated word-RAM and unit-cost metric-arithmetic
assumptions: `n` is sequence length, `L` the maximum buffer width, and `Q` the
number of positions in maximum expanded anomaly support. Complete global
score ties and the integral contributions of omitted events are preserved.

**[v0.3.0 research release](https://github.com/mandu5/sparse-vus/releases/tag/v0.3.0).**
Both the Linux and Mac v3 holdouts are complete, with independent audits
passing all 924 tasks on each platform. The release contains verified Python
packages, the working manuscript, research and computational archives, and
SHA-256 provenance. [Release CI](https://github.com/mandu5/sparse-vus/actions/runs/39538283378)
passes; all eight published assets were downloaded and verified after upload.
Earlier [v0.2.0 assets](https://github.com/mandu5/sparse-vus/releases/tag/v0.2.0)
remain unchanged; their earlier measurements are separated below.

The target is a pinned official VUS definition, including dynamic label mass
and expanded-interval existence. The contribution is its exact support-event
representation and composition with existing ranking techniques. See the
[event proof](docs/theory.md), [radix argument and prior techniques](docs/radix_prior_art_20261021.md),
[attribution and licenses](THIRD_PARTY.md), and [working manuscript source](paper/main.tex).

## Install and use the exact radix APIs

Use the v0.3.0 release for these entry points. Numerical CI covers Python
3.11 and 3.12.

```bash
git clone --branch v0.3.0 --depth 1 https://github.com/mandu5/sparse-vus.git
cd sparse-vus
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install '.[accelerate]'
```

The `accelerate` extra supplies Numba. Add `research` when running the experiment
suite. The base `import sparse_vus` remains NumPy-only; compiled APIs are imported
explicitly from their submodules.

```python
from sparse_vus.radix import sparse_pr_radix_jit, sparse_vus_radix_jit

labels = [0, 1, 0, 0, 1, 0]
scores = [1, 2, 3, 4, 5, 6]  # Higher scores indicate more anomalous points.
vus_pr = sparse_pr_radix_jit(labels, scores, max_buffer=4)
vus_roc, vus_pr = sparse_vus_radix_jit(labels, scores, max_buffer=4)
```

`sparse_pr_radix_jit` returns one Python float and computes PR only.
`sparse_vus_radix_jit` returns `(ROC, PR)`. Both return the exhaustive
score-threshold integral averaged over all integer widths from zero through `max_buffer`.
They accept the same finite float64-convertible scores and binary labels as
the existing APIs, including negative scores and ties. Signed zeros form one
tie; integer values indistinguishable after float64 conversion also form one
tie. Inputs must be one-dimensional, equally long, and contain both label
classes; `max_buffer` must be a nonnegative integer. Neither API returns
per-width arrays or a full surface.

The first call includes Numba compilation/cache initialization. Repeated calls
still include input validation and preparation; there is no reusable prepared
object in these public signatures. Numerical agreement is tolerance-based,
not a promise of bitwise-identical floating-point sums.

The paired radix kernel uses `O(n+Q)` auxiliary space. The PR-only completion
interface stores `L+1` scalar values and uses `O(n+Q+L)` space. The earlier
comparison-based evaluator takes `O(n log(Q+1) + (L+1)Q)` time and remains
available as `sparse_vus.sparse_vus` (NumPy) or
`sparse_vus.compiled.sparse_vus_jit` (Numba), both returning `(ROC, PR)`.
`Q` counts positions, not distinct scores.

## V3 holdout: audited Linux and Mac results

The frozen workload contains **308 series from 17 represented families** of
the original 23-family corpus, with the same three released model score vectors.
Each task evaluates all three models and returns the best-PR model set,
retaining numerical ties. Width 30 is primary, 100 secondary, and 300 a stress
regime: **924 tasks per platform**. These series were held out from this new
procedure's 42-series development run, but were studied in earlier corpus
experiments; this is a policy holdout within known families.

Measurements use one compute thread, warmed JIT code, three repetitions, and
randomized method order within each task. Each timed whole task includes
validation, ranking/preparation, metric/controller work, and winner construction.
Detector inference, input loading, compilation, and downloads are excluded.
Hosted Linux hardware/background load is not controlled. The Mac was an active
user machine; its [starting process snapshot](artifacts/pr-engine/mac-holdout/background-load-start.json)
recorded an unrelated worker at roughly 100% CPU. That snapshot does not establish
continuous load throughout the run. Each platform is reported separately;
earlier versions and cross-platform times are never pooled.

| Platform | Independent audit | Exact-radix primary decision | Maximum exact PR discrepancy |
|---|---|---|---:|
| Hosted Linux x86_64 | PASS, all 924 tasks | PASS | 1.3322676295501878e-15 |
| Mac arm64 | PASS, all 924 tasks | PASS | 1.5543122344752192e-15 |

The discrepancy is relative to the exhaustive comparison-based sparse PR
control across audited exact methods, not an error against symbolic real
arithmetic. On each platform, the frozen decision requires both geometric-mean and
aggregate-ratio lower 95% family-cluster bounds above one against all five
marked controls, plus correctness. Klein and Benchopt comparisons are
descriptive and are outside that decision.

**Primary width, L=30:** ratios are comparator time / exact sparse-radix
PR time; values above one favor radix PR. Brackets are audited 95%
family-cluster intervals. Aggregate ratios divide sums of per-case median
times, not observed batch wall times. F/S counts all 308 cases where radix PR
is faster/slower; these rows have no timing ties. Decisions use unrounded bounds.

**Linux**

| Comparator | Work | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | F/S |
|---|---|---:|---:|---:|---:|
| Comparison-based sparse † | PR only | 1.987 | 1.916 [1.839, 2.013] | 1.955 [1.745, 2.095] | 304/4 |
| Direct dense † | PR only | 4.894 | 4.161 [3.170, 5.008] | 5.385 [4.241, 6.191] | 308/0 |
| Nearest-distance dense † | **ROC+PR** | 6.917 | 5.890 [4.639, 6.923] | 7.214 [5.688, 8.187] | 308/0 |
| Direct dense radix † | PR only | 4.419 | 3.756 [2.904, 4.486] | 4.708 [3.794, 5.276] | 308/0 |
| Nearest-distance dense radix † | PR only | 4.791 | 4.047 [3.142, 4.821] | 5.010 [3.933, 5.643] | 306/2 |
| Klein fast-VUS | PR only | 14.538 | 13.814 [11.639, 15.930] | 11.232 [10.034, 12.514] | 308/0 |
| Benchopt VUS | **ROC+PR** | 21.493 | 20.973 [18.481, 23.617] | 22.991 [19.193, 30.937] | 308/0 |

**Mac**

| Comparator | Work | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | F/S |
|---|---|---:|---:|---:|---:|
| Comparison-based sparse † | PR only | 1.774 | 1.620 [1.421, 1.920] | 1.960 [1.511, 2.323] | 271/37 |
| Direct dense † | PR only | 3.331 | 3.160 [2.772, 3.506] | 4.255 [3.349, 5.112] | 306/2 |
| Nearest-distance dense † | **ROC+PR** | 5.050 | 4.840 [4.356, 5.368] | 6.140 [4.974, 7.181] | 308/0 |
| Direct dense radix † | PR only | 2.677 | 2.617 [2.318, 2.870] | 3.595 [2.752, 4.514] | 303/5 |
| Nearest-distance dense radix † | PR only | 2.599 | 2.519 [2.297, 2.726] | 3.298 [2.624, 3.980] | 307/1 |
| Klein fast-VUS | PR only | 20.925 | 22.360 [19.764, 24.238] | 19.450 [17.910, 20.623] | 308/0 |
| Benchopt VUS | **ROC+PR** | 35.420 | 37.572 [34.754, 41.101] | 37.990 [34.728, 42.965] | 308/0 |

† Five frozen primary controls. The two dense radix PR-only controls match
fixed-width ranking and avoid extra ROC work, while retaining full dense
evaluation. All exhaustive methods evaluate the same all-threshold,
all-integer-width target. The intervals describe variation across families, not timing
uncertainty from three repetitions.

The **post-protocol descriptive PR-only oracle** selects the fastest control
per case from comparison-based sparse PR, direct dense PR, Klein PR, and both
dense radix PR-only controls. It has no confidence intervals and changes no
frozen decision. All cases, including losses, are retained:

| Platform | Width | Median ratio | Geomean | Aggregate | Radix faster/slower | Worst radix slowdown |
|---|---:|---:|---:|---:|---:|---:|
| Linux | 30 | 1.986 | 1.879 | 1.928 | 302/6 | 1.239× |
| Linux | 100 | 1.715 | 1.655 | 1.612 | 301/7 | 1.227× |
| Linux | 300 | 1.275 | 1.309 | 1.235 | 294/14 | 1.299× |
| Mac | 30 | 1.709 | 1.582 | 1.924 | 268/40 | 1.883× |
| Mac | 100 | 1.557 | 1.500 | 1.734 | 286/22 | 1.618× |
| Mac | 300 | 1.278 | 1.293 | 1.375 | 285/23 | 1.640× |

Both frozen racing decisions at width 30 failed on each platform. Racing results vary
by width; the full reports include their costs, exact completion work, and
negative cases. The study evaluates computation of the pinned metric; it
does not establish detector quality, a global CPU/GPU speed record, or venue
acceptance.

See the complete [Linux report](artifacts/reproductions/linux-pr-engine-39523992616/report.md),
[machine-readable report](artifacts/reproductions/linux-pr-engine-39523992616/report.json),
[independent audit](artifacts/reproductions/linux-pr-engine-39523992616/audit.json),
[raw task records](artifacts/reproductions/linux-pr-engine-39523992616/measurements.jsonl),
and [report CI receipt](artifacts/reproductions/linux-pr-engine-39523992616/report-ci-receipt.json).
The corresponding Mac [report](artifacts/pr-engine/mac-holdout/report.md),
[machine-readable report](artifacts/pr-engine/mac-holdout/report.json),
[independent audit](artifacts/pr-engine/mac-holdout/audit.json), and
[raw task records](artifacts/pr-engine/mac-holdout/measurements.jsonl) retain all cases.
The [Linux environment receipt](artifacts/reproductions/linux-pr-engine-39523992616/environment.json)
and [Mac environment receipt](artifacts/pr-engine/mac-holdout/environment.json)
record their actual dependency versions. The older
[benchmark requirements file](experiments/requirements-benchmark.txt) pins the
historical Mac environment and is not the environment of this Linux run.

## Optional width and model-selection APIs

`sparse_vus.fast_racing.race_pr_models_fast` adds a compiled PR-only selection
controller. It retains each computed width once and completes only unseen
widths when its endpoint budget is reached. `preparation="radix"` selects the
new preparation; the default is `"histogram"`. The memory budget limits retained
curve coordinates per model, not process RSS or total runtime. Its guarded
Float64 bounds carry the same numerical limitation as the width API below.

For bounds on the discrete width average:

```python
from sparse_vus.certified import certified_vus

result = certified_vus(labels, scores, max_buffer=100, atol=0.01)
print(result.estimate, result.pr_lower, result.pr_upper)
print(result.evaluated_count, result.total_widths)
```

The half-width tolerance applies to both ROC and PR. The theorem is in real
arithmetic; the implementation uses ordinary float64 with an empirical guard,
not formal outward-rounded interval arithmetic. `atol=0` evaluates every width.
In the earlier v0.2.0 study, bounds could cost more than exact evaluation:
at tolerance 0.01, median speed
ratios on the 42-series subset are 0.83×, 0.90×, and 1.31× for maximum widths
30, 100, and 300. Width 300 is a stress regime. All 378 measured intervals
contain the exact values within the stated numerical audit tolerance.
The [width proof](docs/theory_advancement_20261020.md) explains why PR needs
p-box bounds even between interval merges.

The v0.2.0 compiled exact entry point remains `sparse_vus_jit`. The optional
`sparse_vus.racing.race_pr_models(labels, scores_by_model, max_buffer)` selects
the highest PR model by refining width bounds. In that earlier study, its
decisions matched exact selection in all 126 tasks on each platform, but its aggregate measured cost
is **1.65× higher on macOS and 1.49× higher on Linux**. Positive median speed
ratios occur only at width 300, and total time is still higher there. The
fixed-tolerance selector is also slower in the median at all tested widths.
These optional methods support investigation; fewer width queries do not
imply lower runtime. See the [complete selection results](artifacts/advancement/selection-analysis/analysis.json)
and [scientific assessment](docs/scientific_review_20261020.md).

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
python -m pip install '.[accelerate,research]'
python experiments/fetch_reference.py
python experiments/dtaianomaly_adapter.py --fetch
python experiments/fast_vus_adapter.py --fetch
python experiments/benchopt_vus_adapter.py --fetch
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python -m pytest -q
python experiments/independent_review_check.py
```

The main suite includes 1,000 distinct randomized cases, six structured edge
cases, input validation, independently implemented dense baselines, sampled
threshold checks, and a real compiled dtaianomaly adapter. Test counts are
not counts of independent datasets. A separately authored in-session AI check
also exercised 1,960 exhaustive tiny-domain cases and 120 additional randomized cases.

## Reconstruct the completed v3 reports

After installing the research extra and fetching the pinned references above:

```bash
python experiments/report_pr_engine.py \
  artifacts/reproductions/linux-pr-engine-39523992616 \
  --output ../sparse-vus-linux-v3-report/report --tex
python experiments/report_pr_engine.py \
  artifacts/pr-engine/mac-holdout \
  --output ../sparse-vus-mac-v3-report/report --tex
```

Each command reconstructs a report from its recorded tasks, audited intervals, and
source bindings. It does not rerun metric kernels, bootstrap resampling, or
the source-member audit. The latter additionally requires the verified score
and label cache and is implemented in
[audit_pr_engine.py](experiments/audit_pr_engine.py).

For new timings, the [v3 benchmark workflow](.github/workflows/pr-engine-benchmark.yml)
contains the complete staged-download, freeze, execution, and audit sequence.
Its runner uses `--freeze-only`, then `--execute-frozen` with the new protocol's
SHA-256, and writes to a new run directory. Preserve the tracked original
release anchors and the separate `source-v2` snapshot. Fetch datasets through
the staging helper/workflow so fresh download receipts cannot replace those
anchors. Use the newly recorded environment and never substitute old timings.
The next section reproduces the earlier v0.1.0 workload instead.

## Reproduce the original v0.1.0 public-score experiments

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
and public data, reruns the original v0.1.0 experiments, validates the results,
and regenerates their tables and figures. The advancement experiments below
are a separate follow-up. Python 3.12 must be available. Run timings without
other CPU-intensive work.

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

These original timings use three randomized-order repetitions and one compute thread.
Compilation, source download, and data download are excluded and reported
separately. The principal exact baseline is the fastest of NumPy dense,
Numba dense with nearest distances, and independent Numba direct-ramp dense,
chosen separately for each input. The actual dtaianomaly implementation is
also tested at 250 and all thresholds on a frozen 12-series NAB subset.
The official 250-threshold baseline is a different-resolution computation.

## Earlier comparison-based evidence: v0.2.0 and v0.1.0

These measurements predate the radix implementation and evaluate individual
score-vector calls, rather than the v3 three-model selection task. They are
retained separately and are not pooled with the new holdout ratios.

**v0.2.0:** against pinned, unmodified
[Klein fast-VUS](https://github.com/tomlouisklein/fast-VUS/tree/1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00)
at all thresholds, the earlier paired Sparse VUS evaluator was faster on all
2,100 cases on each of two platforms: median **8.38× on Apple M1 Pro** and
**4.55× on AMD EPYC x86**. Klein returns PR only; this Sparse VUS path returns
both ROC and PR. Against the per-case fastest tested exact comparator,
medians were **2.04×** and **1.35×**, with 209 and 574 slower cases respectively.
This historical oracle is separate from the v3 PR-only oracle above.
See the [v0.2.0 raw measurements and verified analysis](artifacts/advancement/analysis/analysis.json)
and [historical Linux run](https://github.com/mandu5/sparse-vus/actions/runs/39422191526).

**v0.1.0:** on **350 public series from 23 dataset families**, with three released model
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

Public Sylligardos-attributed FF-VUS CPU/GPU code has been located. Its native
metric differs from this pinned target, so it is relevant acceleration prior
art but is not an exact-target timing comparator. The public code does not
establish which revision produced the workshop's reported speedups. See the
[source and semantic audit](docs/prior_art_update_20261021.md).
The public Go `adscore` implementation was executed natively,
but computes different semantics and is not used as an exact-target speed
baseline. See `artifacts/native_go_audit.json`.

## Build the manuscript

To regenerate the v3 two-platform fragment and figure from the complete audited
reports, then typeset the working manuscript:

```bash
python experiments/build_pr_engine_paper.py \
  --mac artifacts/pr-engine/mac-holdout/report.json \
  --linux artifacts/reproductions/linux-pr-engine-39523992616/report.json
python experiments/plot_pr_engine.py \
  --mac artifacts/pr-engine/mac-holdout/report.json \
  --linux artifacts/reproductions/linux-pr-engine-39523992616/report.json \
  --output-prefix paper/figures/pr-only-oracle-ecdf
cd paper
tectonic main.tex
```

To regenerate the original v0.1.0 tables and figures from recorded measurements, fetch the
pinned references first, then run `python experiments/analyze_results.py`.
The analysis verifies the recorded input and source hashes before reading them.
The v3 workflow instead uses [report_pr_engine.py](experiments/report_pr_engine.py),
[plot_pr_engine.py](experiments/plot_pr_engine.py), and
[build_pr_engine_paper.py](experiments/build_pr_engine_paper.py). The two-platform
plot/manuscript builders require both complete audited v3 reports and matching
input identities. All values are derived from the recorded reports; no new
timings are created by these commands.

The supplied PDF is a working research manuscript. Source, executable protocols,
raw measurements, and separately authored in-session validation are included.
The [official-format counterpart](paper/vldb.pdf) uses the same scientific
sources and can be rebuilt with `python experiments/build_vldb.py --build`.
Both manuscripts are unsubmitted; the [submission packet](docs/submission_packet.md)
records the author metadata, completed checks, and remaining venue decisions.

## Reproduce the v0.2.0 follow-up

Use the cloned repository with its original frozen manifests and measurements
present. Activate a dedicated Python 3.12 virtual environment, then run:

```bash
bash experiments/run_advancement.sh ../sparse-vus-v2-reproduction
```

The output directory must be new. The script reruns tests, the independent
width verifier, the actual fast-VUS comparison, adaptive width evaluation,
complete model selection, and incremental PR racing in sequence. It includes
exact fallback/refinement costs and records all losses. The final two audits
reconstruct model decisions, times, and corpus hashes from raw records.
Fresh data-download receipts are written under the new output directory;
the original release bindings remain in place. Downloaded input cache files
are shared with the benchmark checkout.
The original padding sensitivity is separately checked with
`python experiments/ranking_robustness.py --verify`.

To reconstruct the published two-platform figure and all enclosure decisions:

```bash
python experiments/analyze_advancement.py \
  --mac-baseline artifacts/advancement/mac-baseline \
  --linux-baseline artifacts/advancement/linux-baseline \
  --certified artifacts/advancement/mac-certified \
  --output artifacts/advancement/analysis

python experiments/analyze_selection.py \
  --selection artifacts/advancement/mac-selection \
  --mac-racing artifacts/advancement/mac-racing \
  --linux-racing artifacts/advancement/linux-racing \
  --output artifacts/advancement/selection-analysis
```

This checks measured source hashes and actual cached data bytes, so fetch the
pinned references and score/label data first. A new source revision requires
new measurement records; do not silently relabel old timings.

## Attribution

The metric is due to Paparrizos et al. (PVLDB 2022) and its optimized official
implementations to Boniol et al. (VLDB Journal 2025). Scores are from Zhu,
Carpentier, and Verbeke (ICLR 2026),
[KU Leuven RDR DOI 10.48804/MCVI4N](https://doi.org/10.48804/MCVI4N), CC BY 4.0.
Raw labels are from [TSB-AD](https://github.com/TheDatumOrg/TSB-AD).
Full attribution, prior-art boundaries, and license handling are in
[THIRD_PARTY.md](THIRD_PARTY.md).
