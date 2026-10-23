# Unified Sparse VUS: use and reproduction

This guide accompanies `paper/sparse_vus.tex`, the unified working manuscript prepared on 23 October 2026. Commands were checked against the current source entrypoints and CI definitions; preparing this guide did not execute tests, data acquisition, benchmarks, or a build. Run computational commands outside any controlled timing window. The collection workflow is complete; the section below provides the public-record audit and fresh-run procedure.

## Checkout, environment, and scope

Use the exact research revision supplied with the manuscript, including unmerged candidate files if evaluating a working checkout. The historical `v0.3.0` tag alone does not contain every new file. Record the checkout state before reproduction:

```sh
git rev-parse HEAD
git status --short
python3.12 -m venv .venv-unified
source .venv-unified/bin/activate
python -m pip install '.[accelerate,research]' numpy==1.26.4 numba==0.59.1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMBA_NUM_THREADS=1
mkdir -p artifacts/local-unified-reproduction
```

Run commands from the repository root unless stated otherwise. Python 3.12 with NumPy 1.26.4/Numba 0.59.1 matches the new Mac tie-study core stack, but the recorded environment files remain authoritative for every experiment. The earlier whole-evaluator Linux run used different NumPy/Numba versions. The project declares Python >=3.10 and NumPy >=1.24; Numba is optional for the base package but required for accelerated candidate APIs. Other research dependencies installed above are not a fully locked historical environment.

The target is the pinned exhaustive dynamic VUS definition: binary labels containing both classes, finite scores after binary64 conversion, all complete numerical score ties, all integer widths `0..L`, square-root half-width ramps with sum-and-clip overlap, overlap-merged components, right-step PR, and signed trapezoidal ROC with its terminal point. “Exact” describes the real-arithmetic target and identities; finite-precision parity and runtime are separate claims.

## Candidate API example

The complete-tie evaluator requires exactly one contiguous original-positive interval. It is available by explicit module import; do not assume a package-root re-export.

```python
import numpy as np
from sparse_vus.tie_runs import (
    interval_pr_tie_runs_jit,
    interval_vus_tie_runs_jit,
    profile_tie_runs,
)

y = np.array([0, 0, 1, 1, 0, 0, 0], dtype=np.uint8)
scores = np.array([2, 2, 1, 1, 0, 0, 0], dtype=np.float64)
roc, pr = interval_vus_tie_runs_jit(y, scores, 30)
pr_only = interval_pr_tie_runs_jit(y, scores, 30)
profile = profile_tie_runs(y, scores, 30)
# profile: values, events, run_queries, positions_aggregated, groups, runs
```

Validation and preparation belong to each public call. First calls can include JIT compilation. Profiling returns per-width diagnostic arrays and must stay outside metric timers. The integer stopping certificate is independent of mass-rounding errors, but the final floating-point integrals are not certified correctly rounded. For multiple intervals, use the support-event or position-prefix APIs described in [`active_prefix_reproduction_20261021.md`](active_prefix_reproduction_20261021.md).

## Evidence inventory and expected interpretation

| Retained location | Unit and coverage | Interpretation |
|---|---|---|
| `artifacts/pr-engine/mac-holdout/` | 924 tasks; 308 series; three score vectors per task | Whole-evaluator five-control primary PASS |
| `artifacts/reproductions/linux-pr-engine-39523992616/` | Same task/input manifest on the recorded Linux environment | Both whole-evaluator five-control primary decisions PASS |
| `artifacts/saturation/mac-development/` | 378 single-score calls | Incremental width-30 primary FAIL |
| `artifacts/saturation/mac-external/` | 144 single-score calls | Incremental width-30 primary FAIL |
| `artifacts/reproductions/linux-saturation-39546569039/benchmark/` | 144 regenerated-input calls | Incremental width-30 primary FAIL; 37/48 score arrays differ from Mac |
| `artifacts/saturation/mac-external-baselines/` | Paired-output supplement; 48 prescribed vectors | DTAI completes ten of twelve prescribed series; censored cases have no inferred ratios |
| `artifacts/saturation/mac-structural/` | 16 constructed position-prefix cases | Mechanism/work checks, not population evidence |
| `artifacts/tie-runs/mac-20261023/` | 20 constructed plus 111 reused single-score cases; five repetitions, four PR-only methods | Parity/work assertions PASS; timings descriptive, losses retained |
| `artifacts/tie-runs/independent-audit-20261023.json` | 650 dense cases; 36 Decimal-80 integrals; 150,000 integer prefixes; 20,009 synthetic subtractions; 6,569 counter widths | Untimed internal implementation checks, separate from benchmark cases |
| Collection workflow | `artifacts/collection-workflow/mac-20261023/` | All nine passes complete; numerical, selected-set and whole-runtime criteria PASS |

An audit or CI PASS does not reverse a failed runtime criterion. Ratios use comparator time divided by candidate time. Sums of independently timed case medians are not measured batch wall times. The current candidate is faster on structured compressible ties but loses against active prefix on most reused width-300 cases.

## Fetch pinned external source caches

The following network-enabled commands obtain and verify the source references used by optional parity tests and report-source checks:

```sh
python experiments/fetch_reference.py
python experiments/dtaianomaly_adapter.py --fetch
python experiments/fast_vus_adapter.py --fetch
python experiments/benchopt_vus_adapter.py --fetch
```

These are source downloads, not benchmark data/model downloads. They require upstream availability. External source files remain in ignored caches; fetching does not grant permission to redistribute them. See [`THIRD_PARTY.md`](../THIRD_PARTY.md) and [`saturation_data_licenses_20261021.md`](saturation_data_licenses_20261021.md).

## Reconstruct recorded evidence without rerunning timings

These commands read retained measurements. They do not reproduce host performance or recompute metrics from the original score arrays.

```sh
python experiments/report_pr_engine.py artifacts/pr-engine/mac-holdout \
  --output artifacts/local-unified-reproduction/mac-pr-engine --tex
python experiments/report_pr_engine.py artifacts/reproductions/linux-pr-engine-39523992616 \
  --output artifacts/local-unified-reproduction/linux-pr-engine --tex
python experiments/summarize_saturation_evidence.py \
  --study Mac-development=artifacts/saturation/mac-development \
  --study Mac-external=artifacts/saturation/mac-external \
  --study Linux-external=artifacts/reproductions/linux-saturation-39546569039/benchmark \
  --output artifacts/local-unified-reproduction/active-prefix
python experiments/benchmark_saturation_structural.py report artifacts/saturation/mac-structural
python experiments/audit_saturation_supplement.py \
  --output artifacts/local-unified-reproduction/supplement.json
python experiments/benchmark_tie_runs.py report \
  --output artifacts/tie-runs/mac-20261023 \
  > artifacts/local-unified-reproduction/tie-recorded-report.json
```

The PR-engine reporter checks current pinned source identities, original bound audits, and raw records; it requires Klein and Benchopt source caches but not the large observation/score ZIPs. It reuses confidence intervals from the bound audit rather than independently bootstrapping them again. The stronger `audit_pr_engine.py` additionally rereads source ZIP members and therefore requires those large input archives:

```sh
python experiments/audit_pr_engine.py artifacts/pr-engine/mac-holdout \
  --output artifacts/local-unified-reproduction/mac-pr-engine-full-audit.json
```

The saturation evidence/supplement auditors work without ignored source/input caches. The tie `report` command needs the pinned source cache and historical manifest bytes, but not the raw NPZ inputs; it validates coverage, recorded ordering, repetitions, outputs, work assertions, and receipt hashes. It compares an existing `report.json` without replacing it; if no report exists, it creates one. A source-hash failure is a meaningful mismatch, not a reason to rewrite the frozen protocol to match modified code.

## Run numerical checks, separately from timing

The focused tests and independent candidate verifier execute actual kernels. They require the accelerated environment but no downloaded observational arrays:

```sh
python -m pytest -q tests/test_tie_runs.py tests/test_tie_run_protocol.py
python experiments/audit_tie_runs.py \
  > artifacts/local-unified-reproduction/tie-independent-audit.json
python -m pytest -q
```

Do not run the audit with `python -O`: assertions are required and the script rejects optimized mode. The verifier tests strided/read-only/byte-swapped inputs, signed zeros, extreme finite scores, widths beyond sequence length, counter reconstruction, and fixed-point arithmetic. The Decimal-80 checks are high-precision reference calculations, not symbolic exact arithmetic or a proof of all-input error. The full suite can skip optional upstream comparisons when references are unavailable; inspect the skip report instead of equating skips with verified parity.

## Rebuild generated manuscript fragments and PDF

Run in a reproduction checkout after source-cache setup. The following two generators have fixed output paths and rewrite only their generated unified/tie fragments and receipts; preserve the frozen older result fragment:

```sh
python experiments/render_unified_context.py
python experiments/render_tie_run_results.py
```

`render_unified_context.py` verifies fixed raw-measurement hashes, recomputes absolute task-cost summaries, checks the frozen engine fragment, and produces a layout-only copy plus `paper/sparse_vus_context.receipt.json`. `render_tie_run_results.py` reconstructs the 131-case report, checks the separate audit and source hashes, and produces `paper/tie_run_results.tex` plus its receipt. These are evidence reconstructions, not timing runs.

Tectonic must be installed separately. Verify or fetch the pinned template, then build the unified entrypoint:

```sh
python - <<'PY'
import sys
sys.path.insert(0, "experiments")
from build_vldb import verify_styles
verify_styles(fetch=True)
PY
cd paper
tectonic --keep-intermediates --keep-logs sparse_vus.tex
cd ..
```

Template/resource downloads may require network access. `build_vldb.py --build` targets older manuscript entrypoints and is not a substitute for the final command above. Inspect the PDF, embedded fonts, citation resolution, and content-page count. A successful compilation does not validate the proofs or infer venue acceptance.

## Fresh measurements and input limitations

Fresh timing uses new output directories, frozen protocols, serial methods, warmed calls, and no concurrent test suite, model fitting, audit, or PDF build. Preserve every loss and timeout. Do not overwrite the dated historical run or reuse a protocol hash from another output directory.

The new tie runner currently reads the original development and Mac-external manifests. Development loading needs `cache/TSB-AD-U.zip`, the three `cache/*.score-range.zip` archives, and their retained download receipts. External loading requires the exact NPZ files bound by `artifacts/saturation/mac-external/inputs.json`, including container and array hashes. Those observational caches are not bundled with the artifact.

**Historical 131-case replay:** regenerated external scores on another host generally do not reproduce the historical Mac NPZ bytes. The unchanged original runner reads its original manifests. Therefore the following full 131-case sequence requires the historically bound caches. A separate 68-case regeneration path is provided below; it does not relabel new measurements as the original 131-case run:

```sh
python experiments/fast_vus_adapter.py --fetch
python experiments/benchmark_tie_runs.py freeze \
  --output artifacts/tie-runs/local-new-timing
python - <<'PY'
import hashlib
from pathlib import Path
import subprocess
import sys
output = Path("artifacts/tie-runs/local-new-timing")
protocol_hash = hashlib.sha256((output / "protocol.json").read_bytes()).hexdigest()
subprocess.run([
    sys.executable, "experiments/benchmark_tie_runs.py", "run",
    "--output", str(output), "--protocol-sha256", protocol_hash,
], check=True)
PY
python experiments/benchmark_tie_runs.py report \
  --output artifacts/tie-runs/local-new-timing
```

The output must lie inside the repository because input paths are recorded relative to its root. Both that output and `.cache/local-new-timing` must be new. The freeze creates them before loading all inputs, so a prerequisite failure can leave a partial fresh directory; inspect it and choose another fresh name instead of reusing the frozen historical run. A new timing report characterizes that host, not the published host's speed ratios.

For the earlier external position-prefix experiment, [`active_prefix_reproduction_20261021.md`](active_prefix_reproduction_20261021.md) provides the actual staged acquisition, local freeze/generate/verify, and fresh benchmark commands. Its full remote route is `.github/workflows/saturation-external-benchmark.yml`; the wrapper deliberately requires GitHub Actions, so do not spoof that environment locally. That route regenerates a new input population with preserved selection identity, not byte-identical Mac scores.

For the whole-evaluator workload, `.github/workflows/pr-engine-benchmark.yml` shows the executed staging route: `fetch_score_ranges.py` runs in a disposable staging tree, its cache is linked, and `benchmark_pr_engine.py --split holdout --output NEW_PATH --freeze-only` precedes `--execute-frozen HASH --cpu-clearance DESCRIPTION`. The staging protects checked-in download receipts. Do not run acquisition directly over historical evidence merely to recreate the cache. Those older workflows are separate from the new 131-case tie study.

## CI coverage and its boundary

The current `.github/workflows/tests.yml` defines:

- Python 3.11/3.12 numerical-parity jobs, pinned external-source fetches, and the full test suite.
- On Python 3.12, recorded saturation/supplement/tie-report reconstruction and the new independent tie arithmetic/metric audit, plus older PR-engine report checks.
- A separate wheel job that builds distributions, checks the base installation without Numba, and checks accelerated radix/active-prefix and complete-tie APIs with source-byte identity through `check_installed_package.py`, `check_installed_accelerated_package.py`, and `check_installed_tie_runs.py`.

At code checkpoint `ac7f5f4f4314340c5204ffc3504243d1ad001148`,
[remote run 39900069998](https://github.com/mandu5/sparse-vus/actions/runs/39900069998)
completed successfully: Python 3.11 and 3.12 each reported **3,363 passed and
2 optional skips**. Base and accelerated installed-wheel checks, including
complete-tie source identity, passed. Recorded-report reconstruction and
independent numerical audits also passed. This identifies the tested code
checkpoint; consult the PR checks for any later document/artifact revision.
Ordinary parity CI does not rerun the large datasets or timed 131-case study,
reconstruct all excluded input archives, build this PDF, or independently
replicate performance. Benchmark workflows are explicit separate jobs and
produce new run-specific evidence.

The source/hash manifests for older releases describe their own snapshots. For example, the historical active-prefix checksum list includes files that the unified revision extends; a whole-list check on a later modified checkout is not an appropriate claim of unchanged historical-release identity. Use each experiment's source bindings and the exact released snapshot when checking its historical manifest.

## Direct collection workflow: public-record audit and fresh runs

All nine measured passes and selected sets are retained in
`artifacts/collection-workflow/mac-20261023/`. A separate standard-library
verifier reconstructs the decision without loading raw arrays or source caches:

```sh
python experiments/audit_vus_collection.py artifacts/collection-workflow/mac-20261023 --protocol-sha256 69ee646b505297e0feb124cb3206b0d600a6ad2a0a021c8fcea1c195dd4f56ea --output /tmp/sparse-vus-collection-recheck.json
python experiments/render_collection_results.py
```

The output receipt must not already exist. The auditor verifies repository
source bytes and public output chains; it records external cache hashes without
pretending to reread unavailable raw NPZ or upstream source files. The original
`benchmark_vus_collection.py report` additionally checks the 308 local NPZ hashes.

For a fresh timing run, acquire the original revision-pinned label and score
archives described by the whole-evaluator reproduction instructions, then use
new output/cache paths with the `freeze`, `run`, and `report` commands in
[`vus_collection_protocol_20261023.md`](vus_collection_protocol_20261023.md).
Every run includes disk input, 924 full metric calls, 308 selections and one
JSON output; imports, synthetic JIT warmup and filesystem warming are untimed.
Do not replace historical outputs or call a warm-filesystem run a cold-disk run.

## Portable structural and regenerated-external replication

`experiments/reproduce_tie_runs.py` provides a separate acquisition-to-timing
path without the historical development score archives. It regenerates all
48 score vectors for the original 12 external series using the frozen input
procedure, verifies raw observations and labels, records every score-byte
comparison, and selects all 48 one-interval series/model/width cases. It also
copies the 20 source-bound constructed fixtures. The 63 historical development
cases are explicitly excluded. This is a 68-case procedural replication on
previously studied data, not a new domain or a replacement for the original run.

Use fresh paths and the actual protocol digest printed after preparation:

```sh
python experiments/reproduce_tie_runs.py prepare --output artifacts/tie-runs/local-regenerated-new
python experiments/reproduce_tie_runs.py run --output artifacts/tie-runs/local-regenerated-new --protocol-sha256 HASH_FROM_PREPARATION
python experiments/benchmark_tie_runs.py report --output artifacts/tie-runs/local-regenerated-new
```

Preparation downloads pinned external sources and generates scores without
metric calls. Run timing only when other local computational work is stopped.
Inputs are preserved under ignored `.cache`; public receipts contain hashes,
scalar results and constructed fixtures, never the observational arrays.
The original timing/report functions are reused unchanged and validate the new
protocol's own source and input identities. Interrupted preparations or timings
are preserved; retries require a new path.

The dedicated `Complete-tie input regeneration and reproduction` GitHub Actions
workflow installs Python 3.12 with NumPy 1.26.4, Numba 0.59.1, pandas 3.0.1,
SciPy 1.17.1, scikit-learn 1.8.0 and threadpoolctl 3.6.0. Its serial job runs
preparation, all 68 cases and report reconstruction, retaining public receipts
on success or failure. Actual execution outcomes must be read from the
run-specific completion/report and CI receipts.

Executed on 23 October 2026:

| Host and public evidence | Cases / timed calls | Status | Maximum absolute difference from radix | Score vectors byte-identical to historical Mac |
|---|---:|---|---:|---:|
| [Mac](../artifacts/tie-runs/mac-regenerated-20261023-retry1/report.json) | 68 / 1,360 | PASS_PARITY_AND_WORK | 2.220446049250313e-16 | 48/48 |
| [Fresh Linux runner](../artifacts/tie-runs/linux-39900063718/report.json) | 68 / 1,360 | PASS_PARITY_AND_WORK | 2.220446049250313e-16 | 9/48 |

The executed Linux job is
[39900063718](https://github.com/mandu5/sparse-vus/actions/runs/39900063718),
on code revision `ac7f5f4f4314340c5204ffc3504243d1ad001148`.
Raw observations and labels matched their frozen identities. The different
score bytes make the Linux run a procedural replication, not an identical-input
replay. Neither run is new-domain confirmation or a substitute for the
historical 131-case study. Every slower case remains in each report.

The first Mac preparation failed before protocol freeze or timing because
two existing array-hash conventions had been conflated. Its
[failure receipt](../artifacts/tie-runs/mac-regenerated-20261023/preparation-failure.json)
is preserved. The corrected driver has separate raw-array and dtype/shape-bound
hash functions and regression coverage against the unchanged timing runner;
the completed retry uses a new directory. A shared-cache symlink integration
fix preserves containment checks and the repository-relative input paths.
