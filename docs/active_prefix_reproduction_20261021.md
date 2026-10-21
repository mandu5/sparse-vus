# Active-prefix VUS: use and reproduction

This document describes the research branch `research/saturation-20261021`,
not an already published package release or an accepted paper. Commands below
were checked against the current entrypoints. The recorded Linux workflow and
local studies provide execution receipts; writing this document did not rerun
data acquisition, the full benchmark, or a fresh-environment installation.
Record `git rev-parse HEAD` and retain the frozen source hashes when reproducing.

## Environment and public API

From a fresh checkout, use Python 3.12. The following dependency versions match
the recorded Linux workflow; timings and generated floating-point score bytes
can still differ across machines.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install '.[accelerate,research]' numpy==1.26.4 numba==0.59.1 pandas==3.0.1 scipy==1.17.1 scikit-learn==1.8.0 threadpoolctl==3.6.0
```

Numba is optional for the base package, but required by this research API.
The explicit module import works from this source checkout after installation:

```python
import numpy as np
from sparse_vus.saturation import (
    profile_saturation,
    sparse_pr_saturation_jit,
    sparse_vus_saturation_jit,
)

y = np.array([0, 1, 0, 0, 1, 0], dtype=np.uint8)
scores = np.array([0.0, 4.0, 3.0, 2.0, 1.0, 0.0], dtype=np.float64)
L = 6

roc, pr = sparse_vus_saturation_jit(y, scores, L)
pr_only = sparse_pr_saturation_jit(y, scores, L)
last_positive_pr = sparse_pr_saturation_jit(y, scores, L, stop="last_positive")
full_active_pr = sparse_pr_saturation_jit(y, scores, L, stop=False)
profile = profile_saturation(y, scores, L)
# profile: values={roc,pr}, visited[L+1], active[L+1], Q, K
```

The default `stop=True` uses mass plus component coverage. The two alternate
stop modes are exact ablations, with the same preparation. `profile_saturation`
also accepts either mode. Scalar timing APIs stream the width average; profiling
adds `O(L)` diagnostic storage and should remain outside their timers. The
public validators require aligned one-dimensional binary labels containing both
classes, finite scores after binary64 conversion, and a nonnegative integer
maximum width. Numerical ties include collisions caused by conversion and
signed-zero equality. First calls can include JIT compilation.

## Target and theorem scope

The target is the original dynamic-denominator, sum-and-clip VUS definition:
all distinct global score thresholds and all integer widths `0..L`, with
half-width square-root ramps, overlap-merged expanded intervals, right-step PR,
and trapezoidal ROC including its terminal point. Merely adjacent expansions
remain separate. At a threshold, `A` counts admitted originals, `B` is admitted
non-original buffer mass, and the positive denominator is `P0+B/2`.
Permanent recall saturation requires both `A+B/2 >= P0` and every expanded
component hit. Completing the whole score tie is necessary.

The instance-sensitive full-call bound is
`O(n + L + alpha(K) * sum_w J_w)` time and `O(n+Q)` auxiliary words, where
`J_w` counts all active positions through the first complete saturated tie.
It assumes fixed binary64 ranking, word-sized indices, and unit-cost exact
metric arithmetic. It is not a bit-complexity or universal floating-point
rounding guarantee. The implementation's floating-point agreement is tested
separately.

For one original interval and distinct converted scores on the maximum
support, `J_w <= min(Q_w, ceil(2*sqrt(2)*P0))`. Consequently the full evaluator
takes `O(n+L*P0)` time. A singleton has `J_w<=3` and `O(n+L)` time; for `L<=n`
this is linear and matches a deterministic score-coordinate query lower bound
on the stated feasible distinct-binary64 subclass. Arbitrary active ties can
force quadratic total visits even for a singleton. Multiple components can
delay complete coverage despite sufficient mass. See
[`paper/saturation_method.tex`](../paper/saturation_method.tex) and
[`paper/saturation_mass_bound.tex`](../paper/saturation_mass_bound.tex) for the
full restrictions, tie-rounding statement, proofs, and finite-key caveat.

## Recorded evidence and decisions

| Record | Path | Scope |
| --- | --- | --- |
| Mac development | `artifacts/saturation/mac-development/` | 378 cases; 42 previously studied series, 23 source families, three score models, three widths |
| Mac external | `artifacts/saturation/mac-external/` | 144 cases; 12 series from nine additional source families, four generated scores, three widths |
| Linux external regeneration | `artifacts/reproductions/linux-saturation-39546569039/` | Regenerated inputs and 144-case experiment; benchmark records in `benchmark/` |
| Paired external-library supplement | `artifacts/saturation/mac-external-baselines/` | 48 paired ROC/PR cases at `L=30`; Benchopt and paired radix complete; DTAI prescribed for 12 Isolation Forest vectors, ten complete and two watchdog-censored |
| Structural witnesses | `artifacts/saturation/mac-structural/` | 16 synthetic cases, four families and four widths; all profiles and raw timings; `summary.md` and `case-table.md` retain limitations and losses |
| Independent dense oracle | `artifacts/saturation/independent-oracle-20261021.json` | 8,606 bounded exhaustive/strided cases, 51,636 public calls, three stop modes and both API targets |
| Independent receipt reconstruction | `artifacts/saturation/evidence-review/` | Main-study statistics, source/receipt chains, Linux provenance and supplement audit receipts |

**The frozen primary runtime criterion at `L=30` failed in all three main
runs.** An audit `PASS_RECORDED_EVIDENCE`, passing numerical parity, a completed
workflow, and successful paper compilation do not reverse that outcome.
Secondary-width improvements, external-library ratios, and structural
witnesses answer different questions. The supplement and structural study
have no new runtime success criterion. DTAI timeouts receive no invented
duration or speed ratio. None of these records establishes global SOTA,
firstness, independent laboratory confirmation, or publication acceptance.

Linux raw-data and label hashes match the Mac reference. Only 11 of the 48
generated score vectors match byte for byte; the other 37 differ after
regeneration. Preserve that distinction: this is procedure regeneration, not
an identical-array replay. Environment receipts describe the actual hosts;
they do not make timings portable.

## Audit recorded results without rerunning timings

The main evidence auditor uses the standard library plus NumPy and reads the recorded
JSON/JSONL files. It imports neither the benchmark driver nor metric kernels
and does not require ignored raw-data or external-source caches. It checks
recorded identity chains, coverage, parity outputs, work counters and
statistical reconstruction, rather than recomputing metrics from raw data.
Choose a new output directory:

```sh
python experiments/summarize_saturation_evidence.py --study Mac-development=artifacts/saturation/mac-development --study Mac-external=artifacts/saturation/mac-external --study Linux-external=artifacts/reproductions/linux-saturation-39546569039/benchmark --output artifacts/saturation/local-evidence-recheck
```

Its expected main runtime decisions remain false. A separate actual metric
check can rerun the bounded dense oracle; use a new receipt filename:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python experiments/audit_saturation_oracle.py --max-length 5 --atol 2e-12 --output artifacts/saturation/local-oracle-recheck.json
```

The structural report can be replayed from its retained synthetic NPZ inputs
without running metrics or timings. It additionally requires the current
runner, protocol document, and kernels to match the frozen source hashes:

```sh
python experiments/benchmark_saturation_structural.py report artifacts/saturation/mac-structural
```

This exact structural replay passed in a fresh process after the recorded run.
The supplement's separate independent audit receipt is
`artifacts/saturation/evidence-review/supplement-independent-audit.json`.
A reusable standard-library-only auditor reconstructs its receipt chains,
seeded order, worker lifecycle, completed-output parity, censoring and timing
statistics without source caches or input arrays:

```sh
python experiments/audit_saturation_supplement.py --output artifacts/saturation/local-supplement-recheck.json
```

It checks recorded source identities, not unavailable cached source bytes or
NPZ contents. The separately saved reproducible audit is
`artifacts/saturation/evidence-review/supplement-independent-audit-reproducible.json`.
For new supplementary measurements, use the fresh-run sequence below rather
than rewriting historical `report.json` files.

## Rebuild tables, figures, and the focused paper

The checked renderer rereads the recorded main-study evidence, independently
reconstructs it, and generates the main results table plus PDF/SVG/PNG figures.
It does not regenerate numerical outcomes or edit the prose. With Matplotlib
installed, run outside controlled timing windows:

```sh
python experiments/render_saturation_paper_results.py --evidence artifacts/saturation/evidence-review/evidence.json --paper-directory paper
```

`paper/active_prefix.tex` is the focused manuscript. Tectonic must be installed
separately and available on `PATH`; a first build may download TeX resources.
The template is the pinned, unmodified PVLDB/ACM template. To verify or fetch
missing template files without rebuilding the older generic manuscript:

```sh
python - <<'PY'
import sys
sys.path.insert(0, "experiments")
from build_vldb import verify_styles
verify_styles(fetch=True)
PY
cd paper
tectonic --keep-intermediates --keep-logs active_prefix.tex
cd ..
```

Changed template bytes are rejected. The final command is the focused-paper
build entrypoint used in this session. `build_vldb.py --build` instead builds
the older `main.tex` and `vldb.tex`; it is not a substitute for this command.
Figures can be regenerated from relocated checkouts because the renderer
resolves recorded artifact-relative paths. A successful PDF build alone does
not verify the manuscript's mathematical or empirical claims.

## Regenerate external inputs in a disposable fresh checkout

The executed automated route is
`.github/workflows/saturation-external-benchmark.yml`, which pins the Python
dependencies and invokes `experiments/run_saturation_external_reproduction.py`.
The wrapper intentionally rejects direct local execution before mutation.
Use GitHub Actions workflow dispatch on the research revision; do not spoof
`GITHUB_ACTIONS` locally. It preserves reference receipts, freezes a new
environment binding, verifies selection identities before model fitting,
checks raw/label identities after regeneration, and keeps all 144 cases.

The equivalent local entrypoints below require a disposable checkout with
no `cache/saturation-external` and no `.cache/saturation-mac-reference`.
They preserve the checked-in Mac reference receipts by moving them to a
separate reference directory. Do not perform this staging in the checkout
holding an active experiment. Existing frozen receipts bind the complete
generation environment, including the Python executable path; directly
running `--generate` against another machine's selection is expected to fail.

```sh
python - <<'PY'
from pathlib import Path
import shutil
reference = Path(".cache/saturation-mac-reference")
assert not reference.exists()
assert not Path("cache/saturation-external").exists()
reference.parent.mkdir(parents=True, exist_ok=True)
shutil.move("artifacts/saturation/external-inputs", str(reference))
PY
python experiments/fetch_saturation_external.py --freeze
python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "experiments")
from run_saturation_external_reproduction import compare_selection
output = Path("artifacts/saturation/local-input-regeneration")
output.mkdir(parents=True, exist_ok=False)
compare_selection(output)
PY
python experiments/fetch_saturation_external.py --generate
python experiments/fetch_saturation_external.py --verify
python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "experiments")
from run_saturation_external_reproduction import compare_inputs
compare_inputs(Path("artifacts/saturation/local-input-regeneration"))
PY
```

These are the acquisition CLI actions and comparison functions exercised by
the recorded wrapper; the manually staged sequence was not separately rerun
while writing this document. Comparison JSON uses historical `mac`/`linux`
field names; on another local platform the environment fields identify the
actual regeneration host. Never describe a local run as a Linux reproduction
solely because of those field names. Network availability and future access
to pinned upstream files are external requirements.

Read [`saturation_data_licenses_20261021.md`](saturation_data_licenses_20261021.md)
and [`saturation_external_design_20261021.md`](saturation_external_design_20261021.md)
before acquiring or redistributing inputs. mTSBench metadata/data are pinned
to revisions in the acquisition script; its compilation-level terms and
source-family terms differ from this project's MIT code license. In
particular, explicit GHL redistribution permission was not established.
Raw CSV and generated external NPZ files stay in ignored
`cache/saturation-external`; neither the repository receipts nor the Actions
artifact upload should include them. Reproduction uses source downloads and
local score generation, not a published external-array bundle.

## Fresh timing runs

Run serially, without another benchmark, model fit, test suite, or paper build
competing for CPU. Every named output below must be new. Replace each
`HASH_FROM_FREEZE` with the exact protocol hash printed by its preceding
freeze; do not reuse the hash from a different directory or experiment.

After successful local external-input regeneration, fetch the pinned Klein
reference and freeze the complete external scalar-PR experiment:

```sh
python experiments/fast_vus_adapter.py --fetch
python experiments/benchmark_saturation.py freeze artifacts/saturation/local-external --phase external
python experiments/benchmark_saturation.py run artifacts/saturation/local-external --phase external --protocol-sha256 HASH_FROM_FREEZE
```

The phase contains 144 cases and all nine methods, with three repetitions.
The run writes its own report; its primary decision must be reported even
when false. A new paired-output supplement requires that new primary run to
be complete and its regenerated NPZ inputs still present:

```sh
python experiments/benchopt_vus_adapter.py --fetch
python experiments/dtaianomaly_adapter.py --fetch
python experiments/benchmark_saturation_external_baselines.py freeze artifacts/saturation/local-external-baselines --primary artifacts/saturation/local-external
python experiments/benchmark_saturation_external_baselines.py run artifacts/saturation/local-external-baselines --protocol-sha256 HASH_FROM_FREEZE
```

Adapters verify pinned source hashes in ignored `.cache` directories.
Klein's reference carries Apache-2.0 and DTAI's MIT; the Benchopt adapter
records that no license file was detected at its pinned revision and leaves
the source cache-only. Fetching source is not a blanket redistribution grant.
Preserve native DTAI fast-math/parallel options and its one-compute-thread
setting, watchdogs, failures, and skipped repetitions as specified in
[`saturation_external_baseline_protocol_20261021.md`](saturation_external_baseline_protocol_20261021.md).

The synthetic structural study needs no downloaded observations or third-party
baseline source caches beyond the Python environment above:

```sh
python experiments/benchmark_saturation_structural.py freeze artifacts/saturation/local-structural
python experiments/benchmark_saturation_structural.py run artifacts/saturation/local-structural --protocol-sha256 HASH_FROM_FREEZE
python experiments/benchmark_saturation_structural.py report artifacts/saturation/local-structural
```

Its fixed 16 cases include distinct-score singleton and interval inputs,
a two-positive separator with tied middle scores, and an all-tied negative
control. See [`saturation_structural_protocol_20261021.md`](saturation_structural_protocol_20261021.md).
New timing ratios describe the new host/run; no numerical runtime value or
speed ranking is guaranteed to reproduce across environments.
