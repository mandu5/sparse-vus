"""Recover only packaging after the cache-symlink path error; never fit models."""
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path.cwd().resolve()
SCRIPT = ROOT / "scripts/prepare_strengthening_workload.py"
spec = importlib.util.spec_from_file_location("packager", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ARTIFACT = ROOT / "artifacts/pvldb-research-20261024/strengthening"
PROTOCOL = ARTIFACT / "workload-protocol.json"
OUTPUT = (ROOT / ".cache/strengthening-workload").resolve()
FROZEN_PRODUCER = OUTPUT / "provenance/prepare_strengthening_workload.frozen.py"
GENERATION = ARTIFACT / "workload-generation.json"
protocol = json.loads(PROTOCOL.read_text())
protocol_sha = module.file_sha(PROTOCOL)
frozen_entry = next(p for p in protocol["pinned_files"]
                    if p["path"] == "scripts/prepare_strengthening_workload.py")
assert module.file_sha(FROZEN_PRODUCER) == frozen_entry["sha256"]
module.verify_files(ROOT, [p for p in protocol["pinned_files"] if p is not frozen_entry])
assert module.file_sha(protocol["raw_archive"]["path"]) == protocol["raw_archive"]["sha256"]
assert module.file_sha(protocol["native_datasets_csv"]) == protocol["native_datasets_sha256"]
assert not GENERATION.exists()
assert len(list((OUTPUT / "worker-receipts").glob("*/*.json"))) == 52
assert len(list((OUTPUT / "scores").glob("*/*.npy"))) == 52

profiles, combined, expected_rows = [], [], []
for case in protocol["cases"]:
    assert module.file_sha(case["raw_npz_path"]) == case["raw_npz_sha256"]
    assert module.file_sha(case["native_test_path"]) == case["native_test_sha256"]
    with np.load(case["raw_npz_path"], allow_pickle=False) as raw:
        labels = raw["labels"]
    assert module.array_sha(labels) == case["label_hash"]
    scores = []
    for model in module.MODELS:
        worker_path = OUTPUT / "worker-receipts" / model / (case["id"] + ".json")
        profile = json.loads(worker_path.read_text())
        assert (profile["case_id"], profile["model"], profile["status"]) == (case["id"], model, "Status.OK")
        assert profile["protocol_sha256"] == protocol_sha
        assert profile["started_utc"] > protocol["frozen_utc"]
        assert not profile["metric_evaluation_performed"]
        assert all(pool["num_threads"] == 1 for pool in profile["threadpools"])
        assert module.file_sha(profile["score_path"]) == profile["score_sha256"]
        score = module.validate_score(np.load(profile["score_path"], allow_pickle=False), case["n"])
        assert module.array_sha(score) == profile["score_array_sha256"]
        native = OUTPUT / "results" / model / "public-default" / case["family"] / case["id"] / "1/anomaly_scores.ts"
        native_score = np.genfromtxt(native, dtype=np.float64)
        assert native_score.shape == score.shape
        assert native_score.tobytes() == score.astype(np.float64).tobytes()
        profile.update({"native_score_path": str(native), "native_score_sha256": module.file_sha(native),
                        "native_float64_bit_roundtrip": True,
                        "worker_receipt_path": str(worker_path),
                        "worker_receipt_sha256": module.file_sha(worker_path),
                        "subprocess_wall_seconds_not_metric_time": None,
                        "subprocess_capture_availability": "Parent stdout/stderr and subprocess wall duration were held in memory and lost on final packaging error; worker fit duration and complete score receipt remain."})
        profiles.append(profile)
        scores.append(score)
        expected_rows.append({"algorithm": model, "hyper_params_id": "public-default",
                              "collection": case["family"], "dataset": case["id"],
                              "repetition": "1", "status": "Status.OK"})
    stacked = np.stack(scores)
    target = OUTPUT / "arrays" / (case["id"] + ".npz")
    if target.exists():
        with np.load(target, allow_pickle=False) as existing:
            assert existing["labels"].dtype == labels.dtype
            assert existing["labels"].tobytes() == labels.tobytes()
            assert existing["scores"].shape == stacked.shape
            assert existing["scores"].dtype == stacked.dtype
            assert existing["scores"].tobytes() == stacked.tobytes()
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            np.savez_compressed(stream, labels=labels, scores=stacked)
    combined.append({"id": case["id"], "family": case["family"], "n": case["n"],
                     "model_order": list(module.MODELS),
                     "model_status": {model: "Status.OK" for model in module.MODELS},
                     "npz_path": str(target), "npz_relative_path": module.relative_cache_path(target),
                     "npz_sha256": module.file_sha(target), "labels_sha256": module.array_sha(labels),
                     "scores_sha256": module.array_sha(stacked)})

datasets_csv = OUTPUT / "datasets/datasets.csv"
results_csv = OUTPUT / "results/results.csv"
with results_csv.open(newline="") as stream:
    assert list(csv.DictReader(stream)) == expected_rows
receipt = {
    "status": "ALL_SELECTED_PROFILES_GENERATED",
    "started_utc": min(p["started_utc"] for p in profiles),
    "completed_utc": module.now(), "protocol_path": str(PROTOCOL),
    "protocol_sha256": protocol_sha, "selection_sha256": protocol["selection_sha256"],
    "models": list(module.MODELS), "selected_cases": len(combined),
    "selected_profiles": len(profiles), "successful_profiles": len(profiles),
    "metric_evaluation_performed": False, "profiles": profiles, "cases": combined,
    "native_layout": {"datasets_directory": str(OUTPUT / "datasets"),
                      "datasets_csv": str(datasets_csv), "datasets_sha256": module.file_sha(datasets_csv),
                      "results_directory": str(OUTPUT / "results"),
                      "results_csv": str(results_csv), "results_sha256": module.file_sha(results_csv),
                      "immutable_template": True},
    "environment": protocol["environment"],
    "post_generation_packaging_recovery": {
        "cause": "All 52 original fits and native score round-trips completed. Final combined-NPZ metadata construction failed because .cache resolves outside the worktree and Path.relative_to(ROOT) rejected that physical path.",
        "scope": "Relative-path serialization fix and receipt assembly from existing verified worker outputs only; no detector fits repeated; frozen protocol unchanged.",
        "historical_pinned_script_path": frozen_entry["path"],
        "frozen_producer_path": str(FROZEN_PRODUCER),
        "frozen_producer_sha256": module.file_sha(FROZEN_PRODUCER),
        "fixed_reproduction_script_path": str(SCRIPT),
        "fixed_reproduction_script_sha256": module.file_sha(SCRIPT),
        "recovery_script_path": str(Path(__file__).resolve()),
        "recovery_script_sha256": module.file_sha(Path(__file__).resolve()),
        "fits_repeated": 0,
        "unavailable_parent_fields": ["subprocess_wall_seconds_not_metric_time", "stdout", "stderr"],
        "historical_source_verification": "All frozen upstream/source/discovery hashes still match. Historical producer hash matches preserved frozen copy; current reproduction script contains only the cache-relative-path fix."},
}
module.write_new_json(GENERATION, receipt)
print(json.dumps({"status": receipt["status"], "cases": len(combined), "profiles": len(profiles),
                  "generation_sha256": module.file_sha(GENERATION),
                  "protocol_sha256": protocol_sha, "native_layout": receipt["native_layout"]}, indent=2))
