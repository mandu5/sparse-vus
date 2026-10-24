"""Freeze and generate the external FFT/COPOD workload; never evaluate metrics.

The private cache contains raw data. Only the protocol and provenance receipts
belong in a redistributable artifact. Each detector runs once in a subprocess.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
import zipfile

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/pvldb-research-20261024/strengthening"
MODELS = ("FFT", "COPOD")
SEED = 20261024
THREAD_ENV = {
    name: "1" for name in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS",
    )
}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def array_sha(array):
    array = np.ascontiguousarray(array)
    header = json.dumps({"dtype": array.dtype.str, "shape": list(array.shape)},
                        sort_keys=True).encode()
    return sha_bytes(header + b"\0" + array.tobytes())


def observation_hashes(values):
    values = np.asarray(values, dtype=np.float64)
    scale = float(np.std(values))
    normalized = (values - float(np.mean(values))) / scale if scale else np.zeros_like(values)
    normalized = np.round(normalized, 10)
    normalized[normalized == 0] = 0.0
    return [array_sha(values), array_sha(normalized)]


def write_new_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def verify_files(root, entries):
    for entry in entries:
        if file_sha(Path(root) / entry["path"]) != entry["sha256"]:
            raise ValueError("Changed pinned file: " + entry["path"])


def parse_raw(raw):
    frame = pd.read_csv(io.BytesIO(raw))
    if "Label" not in frame or frame.shape[1] != 2:
        raise ValueError("Expected exactly one observation column and Label")
    x = frame.drop(columns=["Label"]).to_numpy(dtype=np.float64)
    labels = frame["Label"].to_numpy()
    if not np.isfinite(x).all() or not np.isin(labels, [0, 1]).all():
        raise ValueError("Nonfinite observations or nonbinary labels")
    labels = labels.astype(np.int8)
    if not 0 < labels.sum() < len(labels):
        raise ValueError("Both label classes are required")
    return np.ascontiguousarray(x), np.ascontiguousarray(labels)


def validate_score(value, n):
    if not isinstance(value, np.ndarray):
        raise ValueError("Public detector returned a non-array: " + str(value))
    if value.ndim != 1 or len(value) != n or not np.issubdtype(value.dtype, np.floating):
        raise ValueError("Invalid public score shape, length or dtype")
    if not np.isfinite(value).all():
        raise ValueError("Public score contains nonfinite values")
    return np.ascontiguousarray(value)


def write_native_score(path, score):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(path, score, fmt="%.17g")
    native = np.genfromtxt(path, dtype=np.float64)
    expected = score.astype(np.float64)
    if native.shape != expected.shape or native.tobytes() != expected.tobytes():
        raise ValueError("TimeEval text serialization changed score values")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def child_environment():
    environment = dict(os.environ)
    environment.update(THREAD_ENV)
    environment.update({
        "PYTHONHASHSEED": str(SEED), "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join([
            str(ROOT / ".cache/strengthening-tsbad"),
            str(ROOT / ".cache/pvldb-consumer-deps"),
        ]),
    })
    return environment


def environment_receipt(python):
    code = """
import json, sys, importlib.metadata as m
from TSB_AD.models.FFT import FFT
from TSB_AD.models.COPOD import COPOD
import statsmodels
print(json.dumps({'python':sys.version,'executable':sys.executable,
 'packages':{p:m.version(p) for p in ['numpy','pandas','scipy','scikit-learn','torch','numba','joblib','threadpoolctl']},
 'statsmodels':statsmodels.__version__, 'statsmodels_file':statsmodels.__file__}))
"""
    result = subprocess.run([str(python), "-c", code], env=child_environment(),
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    return json.loads(result.stdout.strip().splitlines()[-1])


def worker(args):
    """The only function which fits a detector; its protocol already exists."""
    protocol_path = Path(args.protocol)
    protocol = json.loads(protocol_path.read_text())
    if protocol["status"] != "FROZEN_BEFORE_FIRST_DETECTOR_FIT":
        raise ValueError("A frozen protocol is required before fit")
    verify_files(ROOT, protocol["pinned_files"])
    case = next(c for c in protocol["cases"] if c["id"] == args.case_id)
    if file_sha(case["raw_npz_path"]) != case["raw_npz_sha256"]:
        raise ValueError("Raw case changed after freezing")
    if args.model not in MODELS:
        raise ValueError("Unselected model")
    receipt = {"case_id": args.case_id, "model": args.model,
               "started_utc": now(), "protocol_sha256": file_sha(protocol_path),
               "metric_evaluation_performed": False}
    try:
        import torch
        from threadpoolctl import threadpool_limits, threadpool_info
        from TSB_AD.model_wrapper import run_Unsupervise_AD
        random.seed(SEED)
        np.random.seed(SEED)
        torch.manual_seed(SEED)
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        with np.load(case["raw_npz_path"], allow_pickle=False) as source:
            x = source["observations"]
        kwargs = {} if args.model == "FFT" else {"n_jobs": 1}
        with threadpool_limits(limits=1):
            receipt["threadpools"] = threadpool_info()
            start = time.perf_counter()
            output = run_Unsupervise_AD(args.model, x, **kwargs)
            receipt["detector_fit_wall_seconds_not_metric_time"] = time.perf_counter() - start
        score = validate_score(output, case["n"])
        score_path = Path(args.score_output)
        score_path.parent.mkdir(parents=True, exist_ok=True)
        with score_path.open("xb") as stream:
            np.save(stream, score, allow_pickle=False)
        receipt.update({"status": "Status.OK", "score_path": str(score_path),
                        "score_sha256": file_sha(score_path), "score_array_sha256": array_sha(score),
                        "dtype": score.dtype.str, "shape": list(score.shape),
                        "distinct_values": int(len(np.unique(score))),
                        "zero_values": int(np.count_nonzero(score == 0))})
    except Exception as error:
        receipt.update({"status": "Status.ERROR", "error_type": type(error).__name__,
                        "error": str(error)[:4000]})
    receipt["completed_utc"] = now()
    write_new_json(args.worker_receipt, receipt)


def prepare(args):
    discovery_path = ARTIFACT / "source-discovery.json"
    discovery = json.loads(discovery_path.read_text())
    selection = discovery["selection"]
    selection_sha = sha_bytes(json.dumps(selection, sort_keys=True, separators=(",", ":")).encode())
    if selection_sha != discovery["selection_sha256"]:
        raise ValueError("Frozen selection hash mismatch")
    source_manifest_path = ROOT / ".cache/strengthening-tsbad/source-manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text())
    if source_manifest["upstream_commit"] != discovery["score_contract"]["upstream_commit"]:
        raise ValueError("Unexpected upstream score source commit")
    verify_files(ROOT, source_manifest["files"])
    archive_path = Path(args.archive).resolve()
    archive_sha = file_sha(archive_path)
    original = json.loads((ROOT / "artifacts/pvldb-research-20261024/full-precision/protocol.json").read_text())
    if archive_sha != original["archive_sha256"]:
        raise ValueError("Raw archive differs from the previously pinned archive")
    output = Path(args.output).resolve()
    if output.exists():
        raise FileExistsError("Refusing to replace an existing workload cache: " + str(output))
    protocol_path = Path(args.protocol).resolve()
    generation_path = Path(args.generation).resolve()
    if protocol_path.exists() or generation_path.exists():
        raise FileExistsError("Protocol/generation receipt already exists; use a fresh named run")
    candidate_python = ROOT / ".cache/strengthening-env/bin/python"
    attempts = []
    for python in dict.fromkeys([str(candidate_python), sys.executable]):
        try:
            environment = environment_receipt(python)
            chosen_python = python
            attempts.append({"python": python, "status": "IMPORT_OK"})
            break
        except Exception as error:
            attempts.append({"python": python, "status": "IMPORT_FAILED", "error": str(error)})
    else:
        raise RuntimeError("No interpreter can import the pinned detector closure")
    output.mkdir(parents=True)
    cases, dataset_rows = [], []
    with zipfile.ZipFile(archive_path) as archive:
        by_id = {Path(name).stem: name for name in archive.namelist() if name.endswith(".csv")}
        for selected in selection["cases"]:
            raw = archive.read(by_id[selected["id"]])
            if sha_bytes(raw) != selected["raw_sha256"]:
                raise ValueError("Raw source identity mismatch: " + selected["id"])
            x, labels = parse_raw(raw)
            if (len(labels) != selected["n"] or array_sha(labels) != selected["label_hash"]
                    or observation_hashes(x[:, 0]) != selected["observation_hashes"]):
                raise ValueError("Parsed array identity mismatch: " + selected["id"])
            raw_npz = output / "raw-arrays" / (selected["id"] + ".npz")
            raw_npz.parent.mkdir(parents=True, exist_ok=True)
            with raw_npz.open("xb") as stream:
                np.savez_compressed(stream, observations=x, labels=labels)
            relative_csv = selected["family"] + "/" + selected["id"] + ".test.csv"
            test_csv = output / "datasets" / relative_csv
            test_csv.parent.mkdir(parents=True, exist_ok=True)
            frame = pd.DataFrame({"timestamp": np.arange(len(labels)),
                                  "value": x[:, 0], "is_anomaly": labels})
            frame.to_csv(test_csv, index=False, float_format="%.17g")
            check = pd.read_csv(test_csv, float_precision="round_trip")
            if (check["value"].to_numpy(np.float64).tobytes() != x[:, 0].tobytes()
                    or not np.array_equal(check["is_anomaly"].to_numpy(np.int8), labels)):
                raise ValueError("Native raw serialization changed data")
            cases.append({**selected, "archive_member": by_id[selected["id"]],
                          "raw_npz_path": str(raw_npz), "raw_npz_sha256": file_sha(raw_npz),
                          "native_test_path": str(test_csv), "native_test_sha256": file_sha(test_csv)})
            dataset_rows.append({"collection_name": selected["family"],
                                 "dataset_name": selected["id"], "test_path": relative_csv,
                                 "train_path": ""})
    datasets_csv = output / "datasets/datasets.csv"
    write_csv(datasets_csv, ["collection_name", "dataset_name", "test_path", "train_path"], dataset_rows)
    pinned = list(source_manifest["files"])
    for path in [Path(__file__).resolve(), source_manifest_path, discovery_path]:
        pinned.append({"path": str(path.relative_to(ROOT)), "sha256": file_sha(path)})
    protocol = {
        "status": "FROZEN_BEFORE_FIRST_DETECTOR_FIT", "frozen_utc": now(),
        "selection_sha256": selection_sha, "source_manifest_sha256": file_sha(source_manifest_path),
        "pinned_files": pinned, "raw_archive": {"path": str(archive_path), "sha256": archive_sha,
                                                "bytes": archive_path.stat().st_size},
        "source_commit": source_manifest["upstream_commit"], "cases": cases,
        "models": list(MODELS), "seed": SEED, "environment": environment,
        "interpreter_import_attempts": attempts, "thread_environment": THREAD_ENV,
        "threads": 1, "per_model_subprocess_timeout_seconds": 120,
        "native_defaults": {"FFT": {"ifft_parameters": 5, "local_neighbor_window": 21,
                            "local_outlier_threshold": 0.6, "max_region_size": 50,
                            "max_sign_change_distance": 10, "normalize": True},
                            "COPOD": {"n_jobs": 1, "contamination": 0.1, "normalize": True}},
        "raw_contract": "Original CSV order; X(n,1)float64; labels int8; no crop, row dropping or extra normalization.",
        "score_contract": "Unchanged public API and upstream zscore including native nan_to_num. No adapter repair, rounding or jitter. Preserve native dtype in npy, %.17g native text with bit-preserving float64 read-back.",
        "failure_policy": "One attempt per selected case/model. Retain every error or120s subprocess timeout. No replacement, dropping, retries, or imputation. All-tied and zero outputs are valid. Invalid raw/source identity aborts before any fit.",
        "time_scope": "detector_fit_wall_seconds_not_metric_time excludes imports and serialization; subprocess wall time separately labeled. No metric evaluation or benchmarking.",
        "redistribution": "Raw observations and scores stay in private cache. WSD/Stock raw license unresolved; publish only source IDs, hashes and acquisition code.",
        "native_datasets_csv": str(datasets_csv), "native_datasets_sha256": file_sha(datasets_csv),
    }
    write_new_json(protocol_path, protocol)
    protocol_sha = file_sha(protocol_path)
    result_rows, profiles = [], []
    started = now()
    for case in cases:
        for model in MODELS:
            score_path = output / "scores" / model / (case["id"] + ".npy")
            worker_receipt = output / "worker-receipts" / model / (case["id"] + ".json")
            command = [chosen_python, str(Path(__file__).resolve()), "--worker",
                       "--protocol", str(protocol_path), "--case-id", case["id"], "--model", model,
                       "--score-output", str(score_path), "--worker-receipt", str(worker_receipt)]
            begin = time.perf_counter()
            try:
                completed = subprocess.run(command, capture_output=True, text=True,
                                           env=child_environment(), timeout=120)
                if completed.returncode or not worker_receipt.exists():
                    profile = {"case_id": case["id"], "model": model, "status": "Status.ERROR",
                               "error": completed.stderr[-4000:], "returncode": completed.returncode}
                else:
                    profile = json.loads(worker_receipt.read_text())
                profile["stdout"] = completed.stdout[-4000:]
                profile["stderr"] = completed.stderr[-4000:]
            except subprocess.TimeoutExpired:
                profile = {"case_id": case["id"], "model": model, "status": "Status.TIMEOUT",
                           "timeout_seconds": 120}
            profile["subprocess_wall_seconds_not_metric_time"] = time.perf_counter() - begin
            native = output / "results" / model / "public-default" / case["family"] / case["id"] / "1/anomaly_scores.ts"
            native.parent.mkdir(parents=True, exist_ok=True)
            if profile["status"] == "Status.OK":
                score = validate_score(np.load(score_path, allow_pickle=False), case["n"])
                write_native_score(native, score)
                profile.update({"native_score_path": str(native), "native_score_sha256": file_sha(native),
                                "native_float64_bit_roundtrip": True})
            profiles.append(profile)
            result_rows.append({"algorithm": model, "hyper_params_id": "public-default",
                                "collection": case["family"], "dataset": case["id"],
                                "repetition": 1, "status": profile["status"]})
            print(json.dumps({"progress": len(profiles), "total": 52, "case": case["id"],
                              "model": model, "status": profile["status"]}), flush=True)
    results_csv = output / "results/results.csv"
    write_csv(results_csv, ["algorithm", "hyper_params_id", "collection", "dataset", "repetition", "status"], result_rows)
    combined = []
    for case in cases:
        statuses = {p["model"]: p["status"] for p in profiles if p["case_id"] == case["id"]}
        entry = {"id": case["id"], "family": case["family"], "n": case["n"],
                 "model_order": list(MODELS), "model_status": statuses,
                 "npz_path": None, "npz_sha256": None}
        if all(statuses.get(model) == "Status.OK" for model in MODELS):
            with np.load(case["raw_npz_path"], allow_pickle=False) as raw:
                labels = raw["labels"]
            scores = np.stack([np.load(output / "scores" / model / (case["id"] + ".npy"),
                                      allow_pickle=False) for model in MODELS])
            target = output / "arrays" / (case["id"] + ".npz")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                np.savez_compressed(stream, labels=labels, scores=scores)
            entry.update({"npz_path": str(target), "npz_relative_path": str(target.relative_to(ROOT)),
                          "npz_sha256": file_sha(target), "labels_sha256": array_sha(labels),
                          "scores_sha256": array_sha(scores)})
        combined.append(entry)
    all_ok = all(p["status"] == "Status.OK" for p in profiles)
    receipt = {"status": "ALL_SELECTED_PROFILES_GENERATED" if all_ok else "COMPLETED_WITH_RETAINED_FAILURES",
               "started_utc": started, "completed_utc": now(), "protocol_path": str(protocol_path),
               "protocol_sha256": protocol_sha, "selection_sha256": selection_sha,
               "models": list(MODELS), "selected_cases": len(cases), "selected_profiles": len(profiles),
               "successful_profiles": sum(p["status"] == "Status.OK" for p in profiles),
               "metric_evaluation_performed": False, "profiles": profiles, "cases": combined,
               "native_layout": {"datasets_directory": str(output / "datasets"),
                                 "datasets_csv": str(datasets_csv), "datasets_sha256": file_sha(datasets_csv),
                                 "results_directory": str(output / "results"),
                                 "results_csv": str(results_csv), "results_sha256": file_sha(results_csv),
                                 "immutable_template": True},
               "environment": environment}
    write_new_json(generation_path, receipt)
    print(json.dumps({"status": receipt["status"], "successful_profiles": receipt["successful_profiles"],
                      "receipt": str(generation_path)}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default=str(ROOT / "cache/TSB-AD-U.zip"))
    parser.add_argument("--output", default=str(ROOT / ".cache/strengthening-workload"))
    parser.add_argument("--protocol", default=str(ARTIFACT / "workload-protocol.json"))
    parser.add_argument("--generation", default=str(ARTIFACT / "workload-generation.json"))
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--case-id")
    parser.add_argument("--model")
    parser.add_argument("--score-output")
    parser.add_argument("--worker-receipt")
    args = parser.parse_args()
    worker(args) if args.worker else prepare(args)


if __name__ == "__main__":
    main()
