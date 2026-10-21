"""Freeze and acquire external evaluator inputs without computing any metric."""
from __future__ import annotations

import os
for _thread_var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_thread_var] = "1"

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import re
import sys
import time
import urllib.request

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import NearestNeighbors
from threadpoolctl import threadpool_limits, threadpool_info

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache/saturation-external"
OUT = ROOT / "artifacts/saturation/external-inputs"
SCRIPT = "experiments/fetch_saturation_external.py"
DESIGN = "docs/saturation_external_design_20261021.md"
OLD = "artifacts/selected_series.json"
CODE_REV = "0ebf90da7642e103192e05971fdb44e3149bcd51"
DATA_REV = "8dea9af65a9895f39e9e76f118cf23a94d2d4d0a"
METADATA_URL = f"https://raw.githubusercontent.com/PLAN-Lab/mTSBench/{CODE_REV}/Datasets/data_summary.csv"
TREE_URL = f"https://huggingface.co/api/datasets/PLAN-Lab/mTSBench/tree/{DATA_REV}?recursive=true&limit=1000"
BASE_URL = f"https://huggingface.co/datasets/PLAN-Lab/mTSBench/resolve/{DATA_REV}/"
SEED = 20261021
MODELS = ("isolation_forest", "pca_reconstruction", "knn_distance", "robust_marginal_z")
ALIASES = {
    "nasamsl": "msl", "nasasmap": "smap", "kddtsad": "ucr",
    "ucranomalyarchive": "ucr", "webscopes5": "yahoo", "yahoos5": "yahoo",
    "roomoccupancy": "occupancy", "occupancydetection": "occupancy",
    "sensorscope": "ssa", "cicids2017": "cicids", "swansf": "swan",
    "metrointerstatetrafficvolume": "metro", "calit2buildingpeoplecounts": "calit2",
}
PARAMETERS = {
    "seed": SEED,
    "preprocessing": "all rows, no labels; finite-column median imputation; population standardization",
    "isolation_forest": {"n_estimators": 100, "max_samples": "min(256,n)",
        "max_features": 1.0, "contamination": "auto", "bootstrap": False,
        "random_state": SEED, "n_jobs": 1, "score": "negative decision_function"},
    "pca_reconstruction": {"n_components": "min(5,d-1)", "svd_solver": "full",
        "whiten": False, "score": "mean squared reconstruction residual", "rank_zero": "zero reconstruction"},
    "knn_distance": {"reference": "np.linspace(0,n-1,min(2048,n),dtype=np.int64)",
        "n_neighbors": "min(20,reference_count)", "algorithm": "brute",
        "metric": "euclidean", "n_jobs": 1, "query_batch_rows": 512,
        "score": "distance to kth neighbor; self is included where present"},
    "robust_marginal_z": {"center": "median", "scale": "1.4826*MAD",
        "zero_scale_fallback": "population std if positive, otherwise 1", "score": "max absolute standardized deviation"},
}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def array_sha(array):
    return sha(np.ascontiguousarray(array).tobytes())


def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sparse-vus-research-inputs/1"})
    with urllib.request.urlopen(req, timeout=120) as response:
        if response.headers.get("Link") and 'rel="next"' in response.headers["Link"]:
            raise ValueError("Metadata listing is paginated; refuse partial selection")
        return response.read()


def canonical_family(value):
    key = re.sub(r"[^a-z0-9]", "", value.casefold())
    return ALIASES.get(key, key)


def environment():
    return {"python": sys.version, "executable": sys.executable,
            "platform": platform.platform(), "machine": platform.machine(),
            "packages": {name: importlib.metadata.version(name) for name in
                         ("numpy", "scipy", "scikit-learn", "pandas", "threadpoolctl")}}


def freeze():
    if (OUT / "selection.json").exists():
        raise FileExistsError("Selection is already frozen")
    metadata = get(METADATA_URL)
    tree_raw = get(TREE_URL)
    files = {r["path"]: r for r in json.loads(tree_raw) if r["type"] == "file"}
    old_raw = (ROOT / OLD).read_bytes()
    old_names = sorted({s.split("_")[1] for s in json.loads(old_raw)["ordered_series"]})
    old_canonical = {canonical_family(f) for f in old_names}
    eligible = {}
    for row in csv.DictReader(io.StringIO(metadata.decode())):
        family = row["Folder"].split("/")[-1]
        if canonical_family(family) in old_canonical:
            continue
        if not row["File"].endswith("_test.csv") or int(row["NumRows"]) > 100000:
            continue
        eligible.setdefault(family, []).append(row)
    selected = []
    for family, rows in sorted(eligible.items()):
        for row in sorted(rows, key=lambda r: r["File"])[:2]:
            source_path = family + "/" + row["File"]
            info = files[source_path]
            selected.append({"series": Path(row["File"]).stem, "family": family,
                "canonical_family": canonical_family(family), "source_path": source_path,
                "url": BASE_URL + source_path, "expected_n": int(row["NumRows"]),
                "expected_bytes": info["size"], "git_blob_oid": info["oid"],
                "lfs": info.get("lfs"), "metadata": row})
    if len(selected) != 12 or len(eligible) != 9 or len(old_names) != 23:
        raise ValueError("Unexpected source-family/series counts")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mTSBench-data-summary.csv").write_bytes(metadata)
    (OUT / "mTSBench-file-tree.json").write_bytes(tree_raw)
    (OUT / "previous-selected-series.json").write_bytes(old_raw)
    selection = {"schema_version": 1, "frozen_utc": now(), "stage": "before selected data download and score generation",
        "source": "mTSBench", "source_code_revision": CODE_REV, "source_data_revision": DATA_REV,
        "metadata_url": METADATA_URL, "file_tree_url": TREE_URL,
        "metadata_sha256": sha(metadata), "file_tree_sha256": sha(tree_raw),
        "previous_manifest_sha256": sha(old_raw), "previous_families": old_names,
        "previous_canonical_families": sorted(old_canonical), "family_aliases": ALIASES,
        "rule": "exclude prior canonical source families; test files n<=100000; first two filenames lexicographically per family",
        "scope": "new source families relative to this project's previous 350-series corpus; generated classical control scores, not original detector reproduction",
        "selected_count": len(selected), "family_count": len(eligible),
        "expected_download_bytes": sum(r["expected_bytes"] for r in selected),
        "models": list(MODELS), "parameters": PARAMETERS, "environment": environment(),
        "source_sha256": {p: file_sha(ROOT / p) for p in (SCRIPT, DESIGN)}, "series": selected,
        "metric_outcomes_computed": False}
    write_json(OUT / "selection.json", selection)
    print(json.dumps({"status": "FROZEN", "selection_sha256": file_sha(OUT / "selection.json"),
                      "series": len(selected), "families": len(eligible), "bytes": selection["expected_download_bytes"]}), flush=True)


def read_selection(check_environment=True):
    selection = json.loads((OUT / "selection.json").read_text())
    for path, expected in selection["source_sha256"].items():
        if file_sha(ROOT / path) != expected:
            raise ValueError(f"Frozen source changed: {path}")
    for name, key in (("mTSBench-data-summary.csv", "metadata_sha256"),
                      ("mTSBench-file-tree.json", "file_tree_sha256"),
                      ("previous-selected-series.json", "previous_manifest_sha256")):
        if file_sha(OUT / name) != selection[key]:
            raise ValueError(f"Frozen metadata changed: {name}")
    if check_environment and selection["environment"] != environment():
        raise ValueError("Generation environment differs from frozen environment")
    return selection


def prepare(frame):
    if "is_anomaly" not in frame:
        raise ValueError("Missing exact label column is_anomaly")
    labels_raw = pd.to_numeric(frame["is_anomaly"], errors="raise").to_numpy(dtype=np.float64)
    if not np.isin(labels_raw, [0.0, 1.0]).all() or not 0 < labels_raw.sum() < len(labels_raw):
        raise ValueError("Labels must be binary and contain both classes")
    columns, arrays, dropped, imputed = [], [], [], {}
    for name in frame.columns:
        if name == "is_anomaly":
            continue
        if re.sub(r"[^a-z0-9]", "", str(name).casefold()) in {"timestamp", "datetime", "date", "time", "index"}:
            dropped.append({"column": name, "reason": "declared timestamp/index name"})
            continue
        column = pd.to_numeric(frame[name], errors="raise").to_numpy(dtype=np.float64, copy=True)
        if str(name).startswith("Unnamed:"):
            if not (np.array_equal(column, np.arange(len(frame))) or np.array_equal(column, np.arange(1, len(frame) + 1))):
                raise ValueError("Unnamed column is not a consecutive row index")
            dropped.append({"column": name, "reason": "verified consecutive row index"})
            continue
        finite = np.isfinite(column)
        if not finite.any():
            dropped.append({"column": name, "reason": "no finite feature values"})
            continue
        imputed[name] = int((~finite).sum())
        column[~finite] = np.median(column[finite])
        columns.append(name)
        arrays.append(column)
    if not arrays:
        raise ValueError("No finite numeric features")
    features = np.ascontiguousarray(np.column_stack(arrays), dtype=np.float64)
    return labels_raw.astype(np.uint8), features, {"feature_columns": columns, "dropped_columns": dropped,
        "nonfinite_replacements": imputed, "row_order": "unchanged", "feature_count": len(columns)}


def generate_scores(features):
    """Only features enter fitting/scoring; labels are deliberately not accepted."""
    n, d = features.shape
    mean, std = features.mean(axis=0), features.std(axis=0)
    standardized = np.ascontiguousarray((features - mean) / np.where(std > 0, std, 1.0))
    if not np.isfinite(standardized).all():
        raise ValueError("Feature standardization overflow")
    scores, timings = {}, {}
    start = time.perf_counter()
    forest = IsolationForest(n_estimators=100, max_samples=min(256, n), max_features=1.0,
        contamination="auto", bootstrap=False, random_state=SEED, n_jobs=1)
    forest.fit(standardized)
    scores[MODELS[0]] = -forest.decision_function(standardized)
    timings[MODELS[0]] = time.perf_counter() - start
    start = time.perf_counter()
    rank = min(5, d - 1)
    if rank:
        pca = PCA(n_components=rank, svd_solver="full", whiten=False)
        reconstruction = pca.inverse_transform(pca.fit_transform(standardized))
    else:
        reconstruction = np.zeros_like(standardized)
    scores[MODELS[1]] = np.mean((standardized - reconstruction) ** 2, axis=1)
    timings[MODELS[1]] = time.perf_counter() - start
    start = time.perf_counter()
    reference_indices = np.linspace(0, n - 1, min(2048, n), dtype=np.int64)
    k = min(20, len(reference_indices))
    neighbors = NearestNeighbors(n_neighbors=k, algorithm="brute", metric="euclidean", n_jobs=1)
    neighbors.fit(standardized[reference_indices])
    distances = np.empty(n, dtype=np.float64)
    for first in range(0, n, 512):
        last = min(first + 512, n)
        distances[first:last] = neighbors.kneighbors(standardized[first:last], return_distance=True)[0][:, -1]
    scores[MODELS[2]] = distances
    timings[MODELS[2]] = time.perf_counter() - start
    start = time.perf_counter()
    median = np.median(features, axis=0)
    mad = np.median(np.abs(features - median), axis=0)
    scale = np.where(mad > 0, 1.4826 * mad, np.where(std > 0, std, 1.0))
    scores[MODELS[3]] = np.max(np.abs(features - median) / scale, axis=1)
    timings[MODELS[3]] = time.perf_counter() - start
    for name, score in scores.items():
        if score.shape != (n,) or score.dtype != np.float64 or not np.isfinite(score).all():
            raise ValueError(f"Invalid generated scores: {name}")
    return scores, timings, {"pca_rank": rank, "knn_reference_count": len(reference_indices),
        "knn_reference_indices_sha256": array_sha(reference_indices), "knn_k": k,
        "constant_feature_count": int((std == 0).sum())}


def verify_series(row, receipt):
    raw = CACHE / "raw" / row["source_path"]
    target = CACHE / "arrays" / (row["series"] + ".npz")
    if file_sha(raw) != receipt["raw_sha256"] or file_sha(target) != receipt["npz_sha256"]:
        raise ValueError("Input artifact hash mismatch")
    with np.load(target, allow_pickle=False) as data:
        if set(data.files) != {"labels", *MODELS}:
            raise ValueError("Unexpected NPZ keys")
        y = data["labels"]
        if y.shape != (row["expected_n"],) or y.dtype != np.uint8 or not np.isin(y, [0, 1]).all() or not 0 < y.sum() < len(y):
            raise ValueError("Invalid saved labels")
        for name in data.files:
            a = data[name]
            if a.shape != y.shape or not np.isfinite(a).all() or array_sha(a) != receipt["array_sha256"][name]:
                raise ValueError(f"Invalid saved array: {name}")
            if name != "labels" and a.dtype != np.float64:
                raise ValueError("Saved score dtype is not float64")


def acquire(row):
    raw_path = CACHE / "raw" / row["source_path"]
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    downloaded = False
    if not raw_path.exists():
        data = get(row["url"])
        downloaded = True
    else:
        data = raw_path.read_bytes()
    if len(data) != row["expected_bytes"]:
        raise ValueError("Pinned file size mismatch")
    raw_hash = sha(data)
    if row["lfs"]:
        if raw_hash != row["lfs"]["oid"]:
            raise ValueError("LFS SHA256 mismatch")
    else:
        blob_hash = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if blob_hash != row["git_blob_oid"]:
            raise ValueError("Pinned Git blob SHA1 mismatch")
    if downloaded:
        temporary = raw_path.with_suffix(".csv.part")
        temporary.write_bytes(data)
        temporary.replace(raw_path)
    frame = pd.read_csv(io.BytesIO(data))
    if len(frame) != row["expected_n"]:
        raise ValueError("Pinned row count mismatch")
    labels, features, preprocessing = prepare(frame)
    scores, timings, actual = generate_scores(features)
    arrays = {"labels": labels, **scores}
    target = CACHE / "arrays" / (row["series"] + ".npz")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".npz.part")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    temporary.replace(target)
    receipt = {"series": row["series"], "family": row["family"], "canonical_family": row["canonical_family"],
        "completed_utc": now(), "url": row["url"], "raw_bytes": len(data), "raw_sha256": raw_hash,
        "raw_git_blob_verified": row["lfs"] is None, "raw_lfs_verified": row["lfs"] is not None,
        "npz_path": str(target.relative_to(ROOT)), "npz_bytes": target.stat().st_size, "npz_sha256": file_sha(target),
        "n": len(labels), "preprocessing": preprocessing, "actual_parameters": actual,
        "score_generation_seconds": timings, "array_sha256": {name: array_sha(a) for name, a in arrays.items()},
        "selection_sha256": file_sha(OUT / "selection.json"), "metric_outcomes_computed": False}
    write_json(OUT / (row["series"] + ".receipt.json"), receipt)
    verify_series(row, receipt)
    return receipt


def generate():
    selection = read_selection()
    CACHE.mkdir(parents=True, exist_ok=True)
    started = now()
    receipts = []
    with threadpool_limits(limits=1):
        pools = threadpool_info()
        for row in selection["series"]:
            path = OUT / (row["series"] + ".receipt.json")
            try:
                if path.exists():
                    receipt = json.loads(path.read_text())
                    if receipt["selection_sha256"] != file_sha(OUT / "selection.json"):
                        raise ValueError("Resume receipt belongs to another selection")
                    verify_series(row, receipt)
                else:
                    receipt = acquire(row)
                receipts.append(receipt)
                print(json.dumps({"status": "INPUT_READY", "series": row["series"], "n": receipt["n"],
                    "generation_seconds": sum(receipt["score_generation_seconds"].values())}), flush=True)
            except Exception as exc:
                write_json(OUT / (row["series"] + ".failure.json"), {"utc": now(), "series": row["series"],
                    "error": repr(exc), "selection_sha256": file_sha(OUT / "selection.json"), "replacement": False})
                raise
    manifest = {"schema_version": 1, "status": "INPUTS_VERIFIED_NO_METRIC_OUTCOMES", "started_utc": started,
        "completed_utc": now(), "selection_sha256": file_sha(OUT / "selection.json"), "environment": environment(),
        "parameters": selection["parameters"], "threadpools": pools, "models": list(MODELS),
        "series_count": len(receipts), "family_count": len({r["canonical_family"] for r in receipts}),
        "score_vectors": len(receipts) * len(MODELS), "total_rows": sum(r["n"] for r in receipts),
        "metric_outcomes_computed": False, "series": receipts}
    write_json(OUT / "manifest.json", manifest)
    verify()


def verify():
    selection = read_selection(check_environment=False)
    manifest = json.loads((OUT / "manifest.json").read_text())
    if manifest["selection_sha256"] != file_sha(OUT / "selection.json"):
        raise ValueError("Manifest selection identity mismatch")
    records = {r["series"]: r for r in manifest["series"]}
    if len(records) != len(selection["series"]) or set(records) != {r["series"] for r in selection["series"]}:
        raise ValueError("Incomplete/duplicated selection coverage")
    for row in selection["series"]:
        verify_series(row, records[row["series"]])
    print(json.dumps({"status": "VERIFIED", "series": len(records), "scores": len(records) * len(MODELS),
        "manifest_sha256": file_sha(OUT / "manifest.json"), "metric_outcomes_computed": False}), flush=True)


def self_test():
    frame = pd.DataFrame({"timestamp": ["a", "b", "c", "d"], "Unnamed: 0": range(4),
        "a": [1, np.nan, 3, np.inf], "constant": [2, 2, 2, 2], "empty": [np.nan] * 4,
        "is_anomaly": [0, 1, 0, 1]})
    labels, features, receipt = prepare(frame)
    np.testing.assert_array_equal(features[:, 0], [1, 2, 3, 2])
    assert features.shape == (4, 2) and receipt["nonfinite_replacements"]["a"] == 2
    for invalid in ([0, 0, 0, 0], [0, 1, 2, 0], [0, 1, np.nan, 0]):
        try:
            prepare(frame.assign(is_anomaly=invalid))
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid labels accepted")
    flipped, same_features, _ = prepare(frame.assign(is_anomaly=1 - labels))
    np.testing.assert_array_equal(features, same_features)
    assert not np.array_equal(labels, flipped)
    with threadpool_limits(limits=1):
        first, _, _ = generate_scores(features)
        second, _, _ = generate_scores(same_features)
        singleton, _, details = generate_scores(features[:, :1])
    for name in MODELS:
        np.testing.assert_array_equal(first[name], second[name])
        assert singleton[name].shape == (4,)
    assert details["pca_rank"] == 0
    assert canonical_family("NASA-MSL") == canonical_family("msl")
    assert canonical_family("room-occupancy") == canonical_family("Occupancy")
    print(json.dumps({"status": "SELF_TEST_PASS", "checks": ["imputation", "binary_labels", "label_independence", "determinism", "rank_zero", "family_aliases"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for action in ("freeze", "generate", "verify", "self-test"):
        group.add_argument("--" + action, action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.freeze:
        freeze()
    elif args.generate:
        generate()
    else:
        verify()
