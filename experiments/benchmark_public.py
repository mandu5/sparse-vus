"""Frozen all-common-series evaluation on released ICLR 2026 model scores."""
from __future__ import annotations
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for key in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"]:
    os.environ[key] = "1"
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / "cache/numba-public-benchmark"))

import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import platform
import subprocess
import sys
import time
import zipfile
import numpy as np
import pandas as pd
import numba
from threadpoolctl import threadpool_info, threadpool_limits
sys.path.insert(0, str(ROOT / "src"))
from sparse_vus import sparse_vus, dense_vus, sampled_vus
from sparse_vus.compiled import sparse_vus_jit, dense_vus_jit, dense_vus_direct_jit
from dtaianomaly_adapter import dtaianomaly_vus

CACHE, OUT = ROOT / "cache", ROOT / "artifacts"
TOL = 1e-11


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def timed(function, *args):
    begin = time.perf_counter()
    result = function(*args)
    return np.asarray(result, dtype=float), time.perf_counter() - begin


def official():
    spec = importlib.util.spec_from_file_location("pinned_official", CACHE / "official_metrics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.metricor()


def main():
    started = datetime.now(timezone.utc).isoformat()
    protocol = json.loads((ROOT / "experiments/protocol.json").read_text())
    manifest = json.loads((ROOT / "experiments/data_manifest.json").read_text())
    methods = {"sparse_numpy": sparse_vus, "sparse_numba": sparse_vus_jit,
               "dense_numpy": dense_vus, "dense_numba": dense_vus_jit,
               "dense_direct_numba": dense_vus_direct_jit}
    numba.set_num_threads(1)
    threadpool_limits(1)
    warmup = {}
    yy, ss = np.array([0, 1, 0, 0, 1, 0]), np.arange(6, dtype=float)
    for name, function in methods.items():
        _, elapsed = timed(function, yy, ss, 4)
        warmup[name] = elapsed
    _, warmup["dtaianomaly"] = timed(dtaianomaly_vus, yy, ss, 4, 6)
    environment = {"started_utc": started, "python": sys.version, "executable": sys.executable,
        "platform": platform.platform(), "machine": platform.machine(), "numpy": np.__version__, "numba": numba.__version__,
        "numba_threads": numba.get_num_threads(), "threadpool_info": threadpool_info(),
        "first_call_seconds_excluded_from_timings": warmup, "numba_cache_dir": os.environ["NUMBA_CACHE_DIR"],
        "cpu": subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip(),
        "memory_bytes": int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)),
        "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in [ROOT / "src/sparse_vus/core.py", ROOT / "src/sparse_vus/compiled.py", ROOT / "experiments/benchmark_public.py", ROOT / "experiments/protocol.json", ROOT / "experiments/protocol_addendum.json", ROOT / "experiments/data_manifest.json"]}}
    (OUT / "benchmark_environment.json").write_text(json.dumps(environment, indent=2))
    reference = official()
    label_zip = zipfile.ZipFile(CACHE / "TSB-AD-U.zip")
    score_zips = {m["name"]: zipfile.ZipFile(CACHE / (m["name"] + ".score-range.zip")) for m in manifest["models"]}
    evaluation = pd.read_csv(CACHE / "TSB-AD-U-Eva.csv")["file_name"].tolist()
    available = [set(Path(p).stem for p in z.namelist() if p.startswith("scores/") and p.endswith(".npy")) for z in score_zips.values()]
    common = sorted(set(Path(p).stem for p in evaluation).intersection(*available))
    label_names = {Path(n).stem: n for n in label_zip.namelist() if n.endswith(".csv")}
    exclusions = [{"series": Path(p).stem, "reason": "not common to all score archives"} for p in evaluation if Path(p).stem not in common]
    selection = {"evaluation_series": len(evaluation), "common_score_series": len(common), "ordered_series": common,
                 "models": list(score_zips), "exclusions_before_loading": exclusions}
    (OUT / "selected_series.json").write_text(json.dumps(selection, indent=2))
    rng = np.random.default_rng(protocol["public_data"]["timing_order_seed"])
    row_path = OUT / "public_benchmark.jsonl"
    records, crop_records, strong_records = [], [], []
    with row_path.open("w") as log:
        for series_index, stem in enumerate(common):
            if stem not in label_names:
                exclusions.append({"series": stem, "reason": "missing raw labels"}); continue
            raw_labels = label_zip.read(label_names[stem])
            data = pd.read_csv(io.BytesIO(raw_labels))
            y = data["Label"].to_numpy()
            scores, bad = {}, None
            for model, archive in score_zips.items():
                raw_score = archive.read("scores/" + stem + ".npy")
                s = np.load(io.BytesIO(raw_score), allow_pickle=False)
                if s.ndim != 1 or len(s) != len(y) or not np.isfinite(s).all():
                    bad = {"series": stem, "model": model, "reason": "shape, length, or nonfinite score", "score_shape": s.shape, "labels": len(y)}
                    break
                scores[model] = s
            if bad is None and (not np.isin(y, [0, 1]).all() or not 0 < y.sum() < len(y)):
                bad = {"series": stem, "reason": "labels lack exactly two binary classes"}
            if bad:
                exclusions.append(bad); continue
            y = y.astype(np.int8)
            first_positive = int(np.flatnonzero(y)[0])
            crop_start = min(max(0, first_positive - 128), max(0, len(y) - 256))
            crop_slice = slice(crop_start, crop_start + 256)
            crop_y = y[crop_slice]
            for model, s in scores.items():
                for width in protocol["public_data"]["max_buffer"]:
                    values, durations = {}, {name: [] for name in methods}
                    for repeat in range(protocol["public_data"]["timing_repetitions"]):
                        order = list(methods)
                        rng.shuffle(order)
                        for name in order:
                            value, elapsed = timed(methods[name], y, s, width)
                            values[name] = value
                            durations[name].append(elapsed)
                    exact = values["sparse_numba"]
                    approximate, approximate_time = timed(sampled_vus, y, s, width, 250)
                    _, _, _, support = sparse_vus(y, s, width, return_per_buffer=True)
                    row = {"series": stem, "family": stem.split("_id_")[0].split("_", 1)[1], "model": model,
                           "n": len(y), "positive_points": int(y.sum()), "max_buffer": width, **support,
                           "exact": exact.tolist(), "sampled250": approximate.tolist(),
                           "sampled250_delta": (approximate - exact).tolist(), "sampled_numpy_seconds": approximate_time,
                           "results": {k: v.tolist() for k, v in values.items()}, "seconds": durations,
                           "median_seconds": {k: float(np.median(v)) for k, v in durations.items()},
                           "max_parity_error": max(float(np.max(np.abs(v - exact))) for v in values.values()),
                           "label_member_sha256": hashlib.sha256(raw_labels).hexdigest()}
                    dense_best = min(row["median_seconds"][k] for k in methods if k.startswith("dense"))
                    row["speedup_vs_fastest_dense"] = dense_best / row["median_seconds"]["sparse_numba"]
                    records.append(row)
                    log.write(json.dumps(row) + "\n"); log.flush()
                    if 0 < crop_y.sum() < len(crop_y):
                        crop_score = s[crop_slice]
                        expected = np.asarray(reference.RangeAUC_volume_opt(crop_y, crop_score, width, thre=len(crop_y))[-2:])
                        expected250 = np.asarray(reference.RangeAUC_volume_opt(crop_y, crop_score, width, thre=250)[-2:])
                        full = np.asarray(sparse_vus_jit(crop_y, crop_score, width))
                        sample = np.asarray(sampled_vus(crop_y, crop_score, width))
                        crop_records.append({"series": stem, "model": model, "width": width, "start": crop_start,
                            "n": len(crop_y), "exact_error": float(np.max(np.abs(full - expected))),
                            "sampled_error": float(np.max(np.abs(sample - expected250)))})
                    else:
                        crop_records.append({"series": stem, "model": model, "width": width, "skipped": "fixed crop has only one class"})
                    # Prespecified bounded external comparisons on 12 series.
                    if series_index < 12:
                        strong = {"series": stem, "model": model, "width": width, "n": len(y)}
                        ref250, elapsed = timed(lambda: reference.RangeAUC_volume_opt(y, s, width, thre=250)[-2:])
                        strong["official250"] = {"result": ref250.tolist(), "seconds": [elapsed], "sampled_error": float(np.max(np.abs(ref250 - approximate)))}
                        for resolution in [250, len(y)]:
                            tt = []
                            for _ in range(3):
                                vv, elapsed = timed(dtaianomaly_vus, y, s, width, resolution)
                                tt.append(elapsed)
                            target = exact if resolution == len(y) else approximate
                            strong["dtaianomaly_exact" if resolution == len(y) else "dtaianomaly250"] = {
                                "result": vv.tolist(), "seconds": tt, "median_seconds": float(np.median(tt)),
                                "target_error": float(np.max(np.abs(vv - target)))}
                        strong_records.append(strong)
            print(json.dumps({"completed_series": series_index + 1, "total_series": len(common), "metric_evaluations": len(records),
                              "max_error": max(x["max_parity_error"] for x in records)}), flush=True)
    (OUT / "crop_parity.json").write_text(json.dumps(crop_records, indent=2))
    (OUT / "public_external_baselines.json").write_text(json.dumps(strong_records, indent=2))
    (OUT / "public_exclusions.json").write_text(json.dumps(exclusions, indent=2))
    errors = [r["max_parity_error"] for r in records]
    errors += [r[k] for r in crop_records if "skipped" not in r for k in ["exact_error", "sampled_error"]]
    receipt = {"started_utc": started, "completed_utc": datetime.now(timezone.utc).isoformat(),
               "unique_series": len(set(r["series"] for r in records)), "score_vectors": len(set((r["series"], r["model"]) for r in records)),
               "metric_evaluations": len(records), "family_count": len(set(r["family"] for r in records)),
               "max_parity_error": max(errors), "parity_failures": sum(e > TOL for e in errors),
               "crop_evaluations": len(crop_records), "external_evaluations": len(strong_records),
               "exclusions": len(exclusions), "records_sha256": digest(row_path)}
    (OUT / "public_benchmark_receipt.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    main()
