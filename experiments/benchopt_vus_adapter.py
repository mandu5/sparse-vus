"""Run hash-pinned Benchopt VUS functions without unrelated forecasting imports.

The four VUS function bodies are compiled unchanged from the upstream AST.
The source is fetched into ignored cache; it is not redistributed in this repo.
Both ROC and PR are calculated by the upstream kernel, even for PR consumers.
"""
from __future__ import annotations

import ast
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/benchopt_vus"
REVISION = "2b55ccb1fd77b7bd2846ecb4fdb14f609502ed94"
SOURCE_HASH = "298c746c84a28f9296b015bd70eac984d27be5452e3ca42c853de05328c194a8"
SOURCE_URL = (f"https://raw.githubusercontent.com/benchopt/benchmark_tsfm/{REVISION}/"
              "benchmark_utils/metrics.py")


def source_receipt():
    return {
        "repository": "https://github.com/benchopt/benchmark_tsfm",
        "revision": REVISION,
        "upstream_commit_date": "2026-09-29T21:02:26Z",
        "vus_introduction_revision": "2283ad02a6e4546430ea9611fd336d65f4297638",
        "vus_introduction_date": "2026-05-29T12:20:37Z",
        "source_url": SOURCE_URL,
        "source_sha256": SOURCE_HASH,
        "license": "No license file detected at this revision; upstream source is cache-only.",
        "adapter": "Unchanged AST for _segments, _extend_labels, _merge_segments, _range_auc_volume; NumPy dependency only.",
        "output": "ROC and PR pair, also when the consumer selects PR only.",
        "threshold_contract": "250 by default; max_samples=len(scores) includes all score thresholds.",
        "timing_contract": "Includes upstream score sorting, full-array ramps, cumulative sweeps, segment maxima and both integrals; cached source loading excluded after warm-up.",
    }


def fetch_reference():
    """Download public source to ignored cache and reject any hash mismatch."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / "metrics.py"
    if not path.exists():
        temporary = path.with_suffix(".download")
        try:
            subprocess.run(["curl", "-fsSL", "--retry", "2", "--max-time", "60",
                            SOURCE_URL, "-o", str(temporary)], check=True)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != SOURCE_HASH:
                raise ValueError("Benchopt metric source hash mismatch")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_HASH:
        raise ValueError("Benchopt metric source hash mismatch")
    (CACHE / "source.json").write_text(json.dumps(source_receipt(), indent=2) + "\n")
    return path


@lru_cache(maxsize=1)
def _load_kernel():
    path = CACHE / "metrics.py"
    if not path.exists():
        raise FileNotFoundError("Run python experiments/benchopt_vus_adapter.py --fetch first.")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError("Benchopt metric source hash mismatch")
    names = {"_segments", "_extend_labels", "_merge_segments", "_range_auc_volume"}
    parsed = ast.parse(raw, filename=str(path))
    selected = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if len(selected) != len(names) or {node.name for node in selected} != names:
        raise ValueError("Pinned Benchopt source AST structure changed")
    namespace = {"np": np, "__name__": "pinned_benchopt_vus", "__file__": str(path)}
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["_range_auc_volume"]


def benchopt_vus(labels, scores, max_buffer, max_samples=250):
    """Return upstream (ROC, PR); set max_samples=len(scores) for exact sweep."""
    return _load_kernel()(labels, scores, max_buffer, thre=max_samples)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        print(fetch_reference())
