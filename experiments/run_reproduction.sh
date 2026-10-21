#!/usr/bin/env bash
# Run inside a new workspace made by create_reproduction_workspace.py.
# Timings are deliberately sequential. Downloads total approximately 451 MB.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f artifacts/public_benchmark.jsonl ]; then
  echo 'Use a new reproduction workspace; preserve existing experiment records.' >&2
  exit 1
fi
if [ -z "${VIRTUAL_ENV:-}" ]; then
  echo 'Activate a dedicated Python 3.12 virtual environment first.' >&2
  exit 1
fi
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMBA_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
python -m pip install -r experiments/requirements-benchmark.txt
python -m pip install -e .
python experiments/fetch_reference.py
python experiments/dtaianomaly_adapter.py --fetch
python experiments/fast_vus_adapter.py --fetch
python experiments/benchopt_vus_adapter.py --fetch
python -m pytest -q
python experiments/independent_review_check.py --output artifacts/independent_core_review.json
python experiments/fetch_score_ranges.py
python experiments/benchmark_public.py
python experiments/verify_artifact.py
python experiments/benchmark_scaling.py
python experiments/mechanism_ablation.py --run --cpu-clearance 'Sequential reproduction after completed main and scaling timings'
python experiments/external_supplement.py
python experiments/check_fixed_grid_pr.py
python experiments/illustrate_event.py
python experiments/analyze_results.py
# This runner reproduces the original v0.1.0 experiments. The current paper
# additionally uses the separately recorded v0.2.0 advancement experiments.
echo 'Original experiment tables and figures reproduced under paper/ and artifacts/.'
