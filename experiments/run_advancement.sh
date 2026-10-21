#!/usr/bin/env bash
# Reproduce v0.2.0 follow-up experiments without overwriting published records.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${VIRTUAL_ENV:-}" ]; then
  echo 'Activate a dedicated Python 3.12 virtual environment first.' >&2
  exit 1
fi
if [ "$#" -ne 1 ] || [ -e "$1" ]; then
  echo 'Usage: bash experiments/run_advancement.sh NEW_OUTPUT_DIRECTORY' >&2
  exit 1
fi
research_output="$1"
mkdir -p "$research_output"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMBA_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
python -m pip install -r experiments/requirements-benchmark.txt
python -m pip install -e .
python experiments/fetch_reference.py
python experiments/dtaianomaly_adapter.py --fetch
python experiments/fast_vus_adapter.py --fetch
python experiments/benchopt_vus_adapter.py --fetch
python -m pytest -q
python experiments/verify_width_theory.py --output "$research_output/width-theory.json"
# The downloader writes receipt JSONs. Stage its unchanged sources so those
# receipts go under this rerun, while the benchmark can read the shared cache.
python - "$research_output" <<'PY'
from pathlib import Path
import subprocess
import sys
from experiments.create_reproduction_workspace import prepare_data_fetch
root = Path.cwd()
staging = prepare_data_fetch(root, Path(sys.argv[1]))
subprocess.run([sys.executable, str(staging / 'experiments/fetch_score_ranges.py')], check=True)
PY
python experiments/benchmark_advancement.py --mode baseline \
  --output "$research_output/baseline" --cpu-clearance 'Sequential reproduction; no concurrent research task.'
python experiments/benchmark_advancement.py --mode certified \
  --output "$research_output/certified" --cpu-clearance 'Sequential reproduction after baseline.'
python experiments/benchmark_selection.py \
  --output "$research_output/selection" --cpu-clearance 'Sequential reproduction after width evaluation.'
python experiments/benchmark_racing.py \
  --output "$research_output/racing" --cpu-clearance 'Sequential reproduction after fixed-tolerance selection.'
python experiments/audit_selection.py "$research_output/selection" \
  --output "$research_output/selection-audit.json"
python experiments/audit_racing.py "$research_output/racing" \
  --output "$research_output/racing-audit.json"
echo 'New records are separate from the published two-platform measurements.'
echo 'Run the analysis with a matching second-platform baseline to reconstruct the cross-platform figure.'
