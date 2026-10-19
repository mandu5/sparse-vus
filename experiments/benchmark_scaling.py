"""Frozen fixed-support scaling experiment, including the strongest dense kernels."""
import os
for key in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"]:
    os.environ[key] = "1"
from pathlib import Path
import hashlib
import json
import sys
import time
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sparse_vus import sparse_vus, dense_vus
from sparse_vus.compiled import sparse_vus_jit, dense_vus_jit, dense_vus_direct_jit


if __name__ == "__main__":
    spec = json.loads((ROOT / "experiments/protocol.json").read_text())["synthetic_scaling"]
    methods = {"sparse_numpy": sparse_vus, "sparse_numba": sparse_vus_jit,
               "dense_numpy": dense_vus, "dense_numba": dense_vus_jit,
               "dense_direct_numba": dense_vus_direct_jit}
    for function in methods.values():
        function([0, 1, 0], [0, 2, 1], 2)
    rng = np.random.default_rng(spec["seed"])
    order_rng = np.random.default_rng(spec["seed"] + 1)
    rows = []
    for n in spec["n"]:
        y = np.zeros(n, np.int8)
        for start, end in spec["intervals_inclusive"]:
            y[start:end + 1] = 1
        s = rng.normal(size=n)
        times, values = {name: [] for name in methods}, {}
        for _ in range(spec["repetitions"]):
            order = list(methods)
            order_rng.shuffle(order)
            for name in order:
                begin = time.perf_counter()
                values[name] = methods[name](y, s, spec["max_buffer"])
                times[name].append(time.perf_counter() - begin)
        row = {"n": n, "max_buffer": spec["max_buffer"], "Q": 102, "seconds": times,
               "median_seconds": {name: float(np.median(v)) for name, v in times.items()},
               "results": values, "max_error": max(float(np.max(np.abs(np.asarray(v) - values["sparse_numba"]))) for v in values.values())}
        row["speedup_vs_fastest_dense"] = min(v for k, v in row["median_seconds"].items() if k.startswith("dense")) / row["median_seconds"]["sparse_numba"]
        if not np.isfinite(row["max_error"]) or row["max_error"] > 1e-11:
            raise RuntimeError("Scaling parity failed")
        rows.append(row)
        print(json.dumps(row), flush=True)
    out = {"protocol": spec, "jit_warmup_excluded": True, "threads": 1, "rows": rows,
           "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT / "src/sparse_vus/core.py", ROOT / "src/sparse_vus/compiled.py", Path(__file__)]}}
    (ROOT / "artifacts/scaling_final.json").write_text(json.dumps(out, indent=2))
