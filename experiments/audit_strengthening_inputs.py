"""Independently verify the frozen score workload; never fit or evaluate metrics.

Run with the complete pinned TimeEval source tree and its dependencies installed.
Only the explicitly new --out receipt is written. Acquisition code is not imported.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib
import inspect
import io
import json
import math
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REVISION = "7c3622757b1a3afa9a84cbc97ce132d9e379f715"
PROVENANCE = Path("artifacts/pvldb-research-20261024/strengthening/provenance")
PRODUCER = "scripts/prepare_strengthening_workload.py"
MODELS = ["FFT", "COPOD"]
DECODING_CONTRACT = PROVENANCE / "float-decoding-contract.json"
DECODING_CONTRACT_SHA256 = "514614e9711e87d12ab978a60316f40532324d6bf15f7a64ba7eed7d86ad08d8"
DECODING_REPLAY_PURPOSE = "legacy Mac binary64 decoding compatibility; not canonical decimal rounding"
SOURCE_ANCHORS = {
    "timeeval/metrics/__init__.py": "3d79e78d897e4b027f5b6c070a36a77e148bc2e08c429f929d14859df2513ced",
    "timeeval/metrics/metric.py": "2333740807f8573784210b0796da16cae8d7b0aa81f391a0e43af0f3daf1f320",
    "timeeval/metrics/auc_metrics.py": "dcf1c0cfe11cfed7b7b6acb1fc32e5d1041145da0bfb361768fc1d3b291b0feb",
    "timeeval/metrics/range_metrics.py": "ba45a0cd3994c075de1026bbbe086ba7a03d0c7a86ca894d1d0cfe854521f5c4",
    "scripts/recalculate_metrics.py": "f374fed35411a0b54afef844b9ff60139e607e88034c7768c3396fbae35564e5",
    "timeeval/datasets/datasets.py": "a38965f2ca2d787bcc1db6d14b5a11ed5720d19132e8289337a5a9aa3328dd98",
    "timeeval/datasets/dataset.py": "64130d9eada0e2d07949e5635dde59b8464dcf83858bb900d355e1a2a708f380",
    "timeeval/datasets/dataset_manager.py": "c693279995e8aaba9544e1ec9ee3e31c23a61ff32c5a5c9f3e285d0a644a9d29",
    "timeeval/datasets/multi_dataset_manager.py": "a8bb571d99e658d4c00e007881ba5d422cd20161e81d9e96d34d5d67e25ff581",
    "timeeval/datasets/__init__.py": "692ce7ae441914f95952f7047ca1421821a03ce006eed06d63e86a6e60e52b1b",
    "timeeval/datasets/metadata.py": "515531dea3f1cc8fe743e4d0fa2fa0e7f5e4cbaac3aff8b61da09a9c921d5c4c",
    "timeeval/utils/datasets.py": "e47bb6acf4d6631d965957440c152a921a11cd41a5c6e0064915fef298ad09a1",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            result.update(block)
    return result.hexdigest()


def read_verified(path, expected):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, "file identity mismatch: " + str(path))
    return raw


def array_digest(array):
    array = np.ascontiguousarray(array)
    header = json.dumps({"dtype": array.dtype.str, "shape": list(array.shape)}, sort_keys=True).encode()
    return hashlib.sha256(header + b"\0" + array.tobytes()).hexdigest()


def recorded_path(value, root=ROOT):
    """Resolve a recorded path or its repository-relative portable equivalent."""
    path = Path(value)
    if not path.is_absolute():
        return Path(root) / path
    if path.exists():
        return path
    for anchor in (".cache", "cache", "artifacts", "scripts"):
        if anchor in path.parts:
            local = Path(root).joinpath(*path.parts[path.parts.index(anchor):])
            if local.exists():
                return local
    return path


def historical_path(value, expected, root):
    candidate = recorded_path(value, root)
    if candidate.exists():
        read_verified(candidate, expected)
        return candidate
    mapping = json.loads((Path(root) / PROVENANCE / "mapping.json").read_text())
    entries = [e for e in mapping["entries"]
               if e["historical_cache_path"] == value and e["sha256"] == expected]
    require(len(entries) == 1, "missing unique historical source identity: " + value)
    candidate = Path(root) / entries[0]["archive_path"]
    read_verified(candidate, expected)
    return candidate


def verify_frozen_sources(protocol, generation, root=ROOT):
    recovery = generation.get("post_generation_packaging_recovery")
    verified = []
    for entry in protocol["pinned_files"]:
        if entry["path"] == PRODUCER and recovery:
            require(recovery["fits_repeated"] == 0, "historical recovery repeated detector fits")
            require(recovery["frozen_producer_sha256"] == entry["sha256"], "historical producer identity mismatch")
            path = historical_path(recovery["frozen_producer_path"], entry["sha256"], root)
        else:
            path = recorded_path(entry["path"], root)
            read_verified(path, entry["sha256"])
        verified.append({"path": str(path), "sha256": entry["sha256"], "frozen_path": entry["path"]})
    if recovery:
        path = historical_path(recovery["recovery_script_path"], recovery["recovery_script_sha256"], root)
        verified.append({"path": str(path), "sha256": recovery["recovery_script_sha256"], "role": "historical packaging recovery"})
    return verified


def unique_index(rows, fields):
    indexed = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        require(key not in indexed, "duplicate identity: " + repr(key))
        indexed[key] = row
    return indexed


def load_decoding_replay(protocol, selected, root=ROOT):
    """Permit only the diagnosed, source-pinned original-input replay contract."""
    if "decoding_replay" not in protocol:
        return None, {}
    declaration = protocol["decoding_replay"]
    require(isinstance(declaration, dict), "decoding declaration is invalid")
    require(declaration.get("contract_path") == str(DECODING_CONTRACT)
            and declaration.get("contract_sha256") == DECODING_CONTRACT_SHA256
            and declaration.get("purpose") == DECODING_REPLAY_PURPOSE,
            "decoding contract identity or purpose differs")
    pinned = [entry for entry in protocol["pinned_files"]
              if entry["path"] == str(DECODING_CONTRACT)]
    require(len(pinned) == 1 and pinned[0]["sha256"] == DECODING_CONTRACT_SHA256,
            "decoding contract is not uniquely pinned before fitting")
    path = Path(root) / DECODING_CONTRACT
    contract = json.loads(read_verified(path, DECODING_CONTRACT_SHA256))
    require(contract["schema"] == "frozen-observation-binary64-replay-v1",
            "decoding contract schema differs")
    entries = {}
    for entry in contract["entries"]:
        identifier = entry["case_id"]
        require(identifier not in entries and (identifier,) in selected,
                "decoding entry is repeated or outside the frozen selection")
        case = selected[(identifier,)]
        require(entry["raw_member_sha256"] == case["raw_sha256"]
                and entry["original_frozen_observation_sha256"] == case["observation_hashes"][0],
                "decoding entry altered an original source identity")
        index = entry["row_index_zero_based"]
        require(type(index) is int and 0 <= index < case["n"], "decoding row index is invalid")
        entries[identifier] = entry
    require(len(entries) == 1, "decoding contract must contain exactly the one diagnosed observation")
    return {**declaration, "contract_resolved_path": str(path), "entries_verified": []}, entries


def replay_observation_decode(observations, raw_bytes, raw_case, entry):
    """Independently rehydrate one original binary64 value, with whole-vector guards."""
    require(entry["case_id"] == raw_case["id"]
            and hashlib.sha256(raw_bytes).hexdigest() == raw_case["raw_sha256"] == entry["raw_member_sha256"]
            and entry["original_frozen_observation_sha256"] == raw_case["observation_hashes"][0],
            "decoding source identity differs")
    index = entry["row_index_zero_based"]
    require(type(index) is int and 0 <= index < raw_case["n"], "decoding row index is invalid")
    reader = csv.DictReader(io.StringIO(raw_bytes.decode("utf-8"), newline=""))
    require(reader.fieldnames is not None and len(reader.fieldnames) == 2
            and reader.fieldnames.count("Label") == 1 and entry["column"] != "Label"
            and reader.fieldnames.count(entry["column"]) == 1, "decoding raw column differs")
    rows = list(reader)
    require(len(rows) == raw_case["n"] and rows[index][entry["column"]] == entry["literal"],
            "decoding raw literal or row differs")
    correct = float.fromhex(entry["correctly_rounded_binary64_hex"])
    original = float.fromhex(entry["original_frozen_binary64_hex"])
    require(math.isfinite(correct) and math.isfinite(original)
            and correct.hex() == entry["correctly_rounded_binary64_hex"]
            and original.hex() == entry["original_frozen_binary64_hex"]
            and float(entry["literal"]).hex() == correct.hex(),
            "decoding decimal-to-binary64 declaration differs")
    require(correct != original and math.nextafter(correct, original) == original,
            "decoding values are not one-ULP neighbors")
    require(observations.dtype == np.float64 and observations.shape == (raw_case["n"], 1)
            and np.isfinite(observations).all(), "decoding input shape or dtype differs")
    before = array_digest(observations[:, 0])
    require(before in (entry["correctly_rounded_observation_sha256"],
                       entry["original_frozen_observation_sha256"]),
            "decoding observed vector is neither diagnosed original nor correctly rounded input")
    needs_replay = before != entry["original_frozen_observation_sha256"]
    expected_value = correct if needs_replay else original
    require(float(observations[index, 0]).hex() == expected_value.hex(),
            "decoding observed value differs from its vector identity")
    reconstructed = observations.copy()
    reconstructed[index, 0] = original
    after = array_digest(reconstructed[:, 0])
    require(after == entry["original_frozen_observation_sha256"],
            "decoding replay failed the full original observation hash")
    return reconstructed, {
        "case_id": raw_case["id"], "raw_member_sha256": entry["raw_member_sha256"],
        "row_index_zero_based": index, "column": entry["column"], "literal": entry["literal"],
        "correctly_rounded_binary64_hex": correct.hex(), "original_frozen_binary64_hex": original.hex(),
        "one_ulp_adjacency_verified": True, "compatibility_value_applied": needs_replay,
        "observed_before_sha256": before, "verified_original_observation_sha256": after,
    }


def csv_rows(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def verify_native_score(path, expected):
    actual = np.genfromtxt(path, dtype=np.float64)
    expected = np.asarray(expected, dtype=np.float64)
    require(actual.shape == expected.shape and actual.tobytes() == expected.tobytes(),
            "native score bits differ: " + str(path))


def tree_hashes(root):
    excluded = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "build", "dist"}
    return {str(path.relative_to(root)): digest(path) for path in sorted(root.rglob("*"))
            if path.is_file() and not excluded.intersection(path.relative_to(root).parts)
            and not any(part.endswith(".egg-info") for part in path.relative_to(root).parts)
            and path.suffix not in (".pyc", ".pyo") and path.name != ".DS_Store"}


def native_readers(source):
    source = Path(source).resolve()
    for relative, expected in SOURCE_ANCHORS.items():
        read_verified(source / relative, expected)
    require((source / "timeeval/_version.py").is_file(), "complete pinned TimeEval source required")
    hashes = tree_hashes(source)
    sys.path.insert(0, str(source))
    timeeval = importlib.import_module("timeeval")
    utilities = importlib.import_module("timeeval.utils.datasets")
    manager = timeeval.MultiDatasetManager
    reader = utilities.load_labels_only
    for path in (timeeval.__file__, inspect.getsourcefile(manager), inspect.getsourcefile(reader)):
        require(Path(path).resolve().is_relative_to(source), "TimeEval import escaped supplied source tree")
    return manager, reader, {"revision": REVISION, "root": str(source),
                            "module_path": timeeval.__file__, "source_sha256": hashes,
                            "source_tree_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()}


def audit(generation_path, timeeval_source, root=ROOT):
    root = Path(root).resolve()
    generation_path = Path(generation_path).resolve()
    generation = json.loads(generation_path.read_text())
    require(generation["status"] == "ALL_SELECTED_PROFILES_GENERATED", "incomplete generation")
    require(generation["models"] == MODELS, "model order differs")
    require(generation["metric_evaluation_performed"] is False, "generation evaluated metrics")
    require((generation["selected_cases"], generation["selected_profiles"], generation["successful_profiles"]) == (26, 52, 52), "incomplete frozen cohort")
    protocol_path = recorded_path(generation["protocol_path"], root)
    protocol = json.loads(read_verified(protocol_path, generation["protocol_sha256"]))
    require(protocol["status"] == "FROZEN_BEFORE_FIRST_DETECTOR_FIT", "protocol was not prospectively frozen")
    require(protocol["models"] == MODELS and protocol["threads"] == 1, "changed generation contract")
    frozen_sources = verify_frozen_sources(protocol, generation, root)
    manifest_entry = next(p for p in protocol["pinned_files"] if p["path"].endswith("/source-manifest.json"))
    source_manifest = json.loads(read_verified(recorded_path(manifest_entry["path"], root), protocol["source_manifest_sha256"]))
    require(source_manifest["upstream_commit"] == protocol["source_commit"], "upstream source revision differs")
    for entry in source_manifest["files"]:
        read_verified(recorded_path(entry["path"], root), entry["sha256"])
    discovery_entry = next(p for p in protocol["pinned_files"] if p["path"].endswith("/source-discovery.json"))
    discovery = json.loads(read_verified(recorded_path(discovery_entry["path"], root), discovery_entry["sha256"]))
    selection_sha = hashlib.sha256(json.dumps(discovery["selection"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    require(selection_sha == protocol["selection_sha256"] == generation["selection_sha256"] == discovery["selection_sha256"], "selection identity differs")
    cases = unique_index(generation["cases"], ("id",))
    raw_cases = unique_index(protocol["cases"], ("id",))
    selected = unique_index(discovery["selection"]["cases"], ("id",))
    decoding_receipt, decoding_entries = load_decoding_replay(protocol, selected, root)
    profiles = unique_index(generation["profiles"], ("case_id", "model"))
    require(set(cases) == set(raw_cases) == set(selected) and len(cases) == 26, "case identity coverage differs")
    require(set(profiles) == {(c[0], model) for c in cases for model in MODELS}, "profile identity coverage differs")
    require({family: sum(c["family"] == family for c in cases.values()) for family in ("WSD", "Stock", "MSL")} == {"WSD": 12, "Stock": 12, "MSL": 2}, "family coverage differs")
    layout = generation["native_layout"]
    datasets_csv = recorded_path(layout["datasets_csv"], root)
    results_csv = recorded_path(layout["results_csv"], root)
    read_verified(datasets_csv, layout["datasets_sha256"])
    read_verified(results_csv, layout["results_sha256"])
    require(layout["datasets_sha256"] == protocol["native_datasets_sha256"], "dataset template changed after freeze")
    require(datasets_csv == recorded_path(protocol["native_datasets_csv"], root), "dataset template path differs")
    dataset_rows = unique_index(csv_rows(datasets_csv), ("collection_name", "dataset_name"))
    result_rows = unique_index(csv_rows(results_csv), ("dataset", "algorithm"))
    require(set(dataset_rows) == {(c["family"], c["id"]) for c in cases.values()}, "dataset template coverage differs")
    require(set(result_rows) == set(profiles), "native result coverage differs")
    manager_class, label_reader, timeeval_receipt = native_readers(timeeval_source)
    manager = manager_class([datasets_csv.parent])
    archive_path = recorded_path(protocol["raw_archive"]["path"], root)
    require(digest(archive_path) == protocol["raw_archive"]["sha256"], "raw archive identity mismatch")
    input_files = {str(datasets_csv): digest(datasets_csv), str(results_csv): digest(results_csv)}
    total_rows = 0
    with zipfile.ZipFile(archive_path) as archive:
        for key, case in cases.items():
            raw_case = raw_cases[key]
            selection = selected[key]
            require(all(raw_case[k] == selection[k] for k in selection), "protocol altered selected case")
            require((case["family"], case["n"], case["model_order"]) == (selection["family"], selection["n"], MODELS), "case metadata differs")
            require(case["model_status"] == {model: "Status.OK" for model in MODELS}, "retained model failure")
            raw_bytes = archive.read(raw_case["archive_member"])
            require(hashlib.sha256(raw_bytes).hexdigest() == raw_case["raw_sha256"], "raw member identity mismatch")
            frame = pd.read_csv(io.BytesIO(raw_bytes))
            require(frame.shape[1] == 2 and "Label" in frame, "raw CSV schema differs")
            observations = frame.drop(columns=["Label"]).to_numpy(dtype=np.float64)
            require(np.isin(frame["Label"].to_numpy(), [0, 1]).all(), "raw labels are not binary")
            labels = frame["Label"].to_numpy(dtype=np.int8)
            require(observations.shape == (case["n"], 1) and np.isfinite(observations).all(), "raw observations invalid")
            require(0 < int(labels.sum()) < case["n"], "raw label classes missing")
            require(array_digest(labels) == raw_case["label_hash"], "raw label array identity mismatch")
            if case["id"] in decoding_entries:
                observations, decoded = replay_observation_decode(
                    observations, raw_bytes, raw_case, decoding_entries[case["id"]])
                decoding_receipt["entries_verified"].append(decoded)
            vector = observations[:, 0]
            scale = float(np.std(vector))
            normalized = (vector - float(np.mean(vector))) / scale if scale else np.zeros_like(vector)
            normalized = np.round(normalized, 10)
            normalized[normalized == 0] = 0.0
            require([array_digest(vector), array_digest(normalized)] == raw_case["observation_hashes"], "raw observation array identity mismatch")
            raw_npz = recorded_path(raw_case["raw_npz_path"], root)
            read_verified(raw_npz, raw_case["raw_npz_sha256"])
            with np.load(raw_npz, allow_pickle=False) as data:
                require(data["labels"].dtype == labels.dtype and data["labels"].tobytes() == labels.tobytes(), "raw NPZ label bits differ")
                require(data["observations"].dtype == observations.dtype and data["observations"].shape == observations.shape and data["observations"].tobytes() == observations.tobytes(), "raw NPZ observation bits differ")
            npz_path = root / case["npz_relative_path"] if case.get("npz_relative_path") else recorded_path(case["npz_path"], root)
            read_verified(npz_path, case["npz_sha256"])
            with np.load(npz_path, allow_pickle=False) as data:
                combined_labels, scores = data["labels"], data["scores"]
            require(combined_labels.dtype == np.int8 and combined_labels.shape == (case["n"],) and combined_labels.tobytes() == labels.tobytes(), "combined label bits differ")
            require(scores.shape == (2, case["n"]) and scores.dtype == np.float64 and np.isfinite(scores).all(), "combined score contract differs")
            require(array_digest(combined_labels) == case["labels_sha256"] and array_digest(scores) == case["scores_sha256"], "combined array identity mismatch")
            native_test = manager.get_dataset_path((case["family"], case["id"]))
            require(native_test.resolve() == recorded_path(raw_case["native_test_path"], root).resolve(), "native dataset path differs")
            read_verified(native_test, raw_case["native_test_sha256"])
            native_labels = label_reader(native_test)
            require(native_labels.shape == labels.shape and np.array_equal(native_labels, labels), "TimeEval label reader differs")
            native_frame = pd.read_csv(native_test, float_precision="round_trip")
            require(native_frame["value"].to_numpy(np.float64).tobytes() == vector.tobytes(), "native observation bits differ")
            require(np.array_equal(native_frame["timestamp"].to_numpy(), np.arange(case["n"])), "native timestamp order differs")
            workload = results_csv.parent.parent
            for model_index, model in enumerate(MODELS):
                profile = profiles[(case["id"], model)]
                require(profile["status"] == "Status.OK" and profile["metric_evaluation_performed"] is False, "profile status differs")
                require(profile["protocol_sha256"] == generation["protocol_sha256"] and profile["started_utc"] >= protocol["frozen_utc"], "profile protocol/chronology differs")
                require(all(pool["num_threads"] == 1 for pool in profile["threadpools"]), "profile numerical threads differ")
                score_path = recorded_path(profile["score_path"], root)
                read_verified(score_path, profile["score_sha256"])
                score = np.load(score_path, allow_pickle=False)
                require(score.dtype == np.float64 and score.shape == (case["n"],) and score.tobytes() == scores[model_index].tobytes(), "per-model score bits differ")
                require(array_digest(score) == profile["score_array_sha256"], "score array identity mismatch")
                row = result_rows[(case["id"], model)]
                require((row["collection"], row["hyper_params_id"], row["repetition"], row["status"]) == (case["family"], "public-default", "1", "Status.OK"), "native results metadata differs")
                native_score = results_csv.parent / model / row["hyper_params_id"] / case["family"] / case["id"] / row["repetition"] / "anomaly_scores.ts"
                require(native_score.resolve() == recorded_path(profile["native_score_path"], root).resolve(), "native score path differs")
                read_verified(native_score, profile["native_score_sha256"])
                verify_native_score(native_score, score)
                worker_path = workload / "worker-receipts" / model / (case["id"] + ".json")
                worker = json.loads(worker_path.read_text())
                if "worker_receipt_sha256" in profile:
                    read_verified(worker_path, profile["worker_receipt_sha256"])
                require(all(profile.get(k) == value for k, value in worker.items()), "worker receipt differs from generation")
                for path in (score_path, native_score, worker_path):
                    input_files[str(path)] = digest(path)
            for path in (raw_npz, npz_path, native_test):
                input_files[str(path)] = digest(path)
            total_rows += case["n"]
    if decoding_receipt is not None:
        require(len(decoding_receipt["entries_verified"]) == len(decoding_entries),
                "decoding entry audit coverage differs")
    return {
        "status": "NATIVE_INPUTS_VERIFIED_WITHOUT_METRIC_EVALUATION",
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "generation_path": str(generation_path), "generation_sha256": digest(generation_path),
        "protocol_sha256": digest(protocol_path), "timeeval_module_path": timeeval_receipt["module_path"],
        "datasets_verified": len(cases), "profiles_verified": len(profiles), "total_rows": total_rows,
        "checks": ["all upstream and producer source identities, with explicit historical archive fallback",
                   "frozen selection and original raw archive/member/observation/label identities",
                   "all raw/combined NPZ identities and exact array bits",
                   "all native dataset/results templates and unique complete identifiers",
                   "actual pinned TimeEval MultiDatasetManager/load_labels_only for all26 labels",
                   "all52 per-model NPY/native text vectors bitwise equal to combined NPZ",
                   "worker receipts, frozen-before-fit chronology and one-thread records"],
        "metric_evaluation_performed": False, "candidate_code_imported": False,
        "auditor_path": str(Path(__file__).resolve()), "auditor_sha256": digest(__file__),
        "frozen_sources": frozen_sources, "input_sha256": input_files,
        "raw_archive": {"path": str(archive_path), "sha256": protocol["raw_archive"]["sha256"]},
        "timeeval_source": timeeval_receipt,
        "decoding_replay": decoding_receipt,
        "provenance_mode": "historical Mac packaging recovery" if generation.get("post_generation_packaging_recovery") else "clean current producer",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation", type=Path, required=True)
    parser.add_argument("--timeeval-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Refusing to replace an existing audit receipt: " + str(args.out))
    result = audit(args.generation, args.timeeval_source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "datasets_verified": result["datasets_verified"],
                      "profiles_verified": result["profiles_verified"], "generation_sha256": result["generation_sha256"],
                      "receipt": str(args.out), "receipt_sha256": digest(args.out)}))


if __name__ == "__main__":
    main()
