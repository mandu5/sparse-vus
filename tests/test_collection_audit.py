"""Public-receipt auditing with synthetic clocks; no metric or array execution."""
import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest


@pytest.fixture
def auditor():
    path = Path(__file__).resolve().parents[1] / "experiments/audit_vus_collection.py"
    spec = importlib.util.spec_from_file_location("collection_auditor_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dump(path, value):
    path.write_text(json.dumps(value) + "\n")


def refresh_run(auditor, study, rows, protocol_sha):
    """Rehash mutations so tests exercise semantics, not only stale digests."""
    run = study / "run"
    for row in rows:
        path = run / row["output_file"]
        row["output_sha256"] = auditor.digest(path)
        row["output_bytes"] = path.stat().st_size
    (run / "measurements.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    p = json.loads((study / "protocol.json").read_text())
    dump(run / "completion.json", {
        "status": "COMPLETE", "passes": 9, "protocol_sha256": protocol_sha,
        "inputs_sha256": p["inputs_sha256"],
        "measurements_sha256": auditor.digest(run / "measurements.jsonl"),
        "environment_sha256": auditor.digest(run / "environment.json"),
        "outputs_sha256": {f.name: auditor.digest(f) for f in run.glob("trial-*.json")}})


@pytest.fixture
def receipts(tmp_path, auditor, monkeypatch):
    root, study = tmp_path / "repository", tmp_path / "study"
    run = study / "run"
    root.mkdir()
    run.mkdir(parents=True)
    sources = {}
    for relative in auditor.REPOSITORY_SOURCES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# fixture source: {relative}\n")
        sources[relative] = auditor.digest(path)
    sources.update({path: "e" * 64 for path in auditor.EXTERNAL_SOURCES})
    models = ["a", "b", "c"]
    expected = [{"series": f"fixture-{i:03d}", "family": f"family-{i % 17:02d}",
                 "n": 4, "max_buffer": 30, "label_sha256": f"{i:064x}",
                 "score_sha256": {m: f"{3*i+j:064x}" for j, m in enumerate(models)}}
                for i in range(308)]
    entries = [{**copy.deepcopy(row), "file": f"{i:04d}.npz", "bytes": 1100,
                "npz_sha256": "d" * 64, "label_member": f"labels/{row['series']}.csv",
                "arrays": {name: {"dtype": "|i1" if name == "labels" else "<f8",
                                  "shape": [4], "sha256": "c" * 64}
                           for name in ["labels", "score_0", "score_1", "score_2"]},
                "decoded_label_array": {"dtype": "<i8", "shape": [4], "sha256": "b" * 64}}
               for i, row in enumerate(expected)]
    dump(study / "inputs.json", entries)
    rng, orders = random.Random(2026102307), []
    for _ in range(3):
        order = list(auditor.METHODS)
        rng.shuffle(order)
        orders.append(order)
    locks = {"files": {"TSB-AD-U.zip": "a" * 64}}
    original_sha = "9" * 64
    # Only replace the immutable original-corpus lookup. Public hashes, source
    # bytes, all 308 identities, nine passes and all decisions are real checks.
    monkeypatch.setattr(auditor, "load_release_population",
                        lambda root, p: (copy.deepcopy(expected), models, locks, original_sha, {}))
    p = {"version": 1, "status": "FROZEN_BEFORE_COLLECTION_TIMING", "series": 308,
         "repetitions": 3, "max_buffer": 30, "methods": list(auditor.METHODS), "models": models,
         "tie_atol": 1e-10, "parity_atol": 1e-11, "seed": 2026102307, "orders": orders,
         "source_sha256": sources, "inputs_sha256": auditor.digest(study / "inputs.json"),
         "families": [f"family-{i:02d}" for i in range(17)],
         "original_inputs_sha256": auditor.OLD_INPUTS_SHA,
         "original_protocol_sha256": auditor.OLD_PROTOCOL_SHA,
         "original_benchmark_sha256": original_sha, "source_file_locks": locks["files"],
         "source_archive_sha256": {name: "a" * 64 for name in
                                   ["TSB-AD-U.zip", *(f"{m}.score-range.zip" for m in models)]},
         "cache_bytes": 308 * 1100, "cache_relative": ".cache/absent-inputs",
         "scope": "Synthetic public receipts for unit tests; no benchmark results"}
    dump(study / "protocol.json", p)
    protocol_sha = auditor.digest(study / "protocol.json")
    dump(study / "freeze_receipt.json", {
        "status": "FROZEN_NO_COLLECTION_TIMING", "protocol_sha256": protocol_sha,
        "inputs_sha256": p["inputs_sha256"],
        "driver_sha256": sources["experiments/benchmark_vus_collection.py"],
        "verified_label_members": 308, "verified_score_members": 924, "npz_files": 308,
        "npz_bytes": p["cache_bytes"]})
    dump(run / "environment.json", {
        "protocol_sha256": protocol_sha, "inputs_sha256": p["inputs_sha256"],
        "source_sha256": sources, "threads": 1, "threadpools": [{"num_threads": 1}],
        "cpu_clearance": "Synthetic fixture, no computation measured",
        "warmup": [{"method": method, "label_dtype": "|i1", "score_dtype": "<f8", "seconds": .001}
                   for method in auditor.METHODS]})
    times = {"radix_pr": [1, 3, 2], "dense_pr_nearest_radix": [4, 6, 5], "klein_pr": [8, 10, 9]}
    rows = []
    for trial, order in enumerate(orders):
        for position, method in enumerate(order):
            filename = f"trial-{trial}-{method}.json"
            dump(run / filename, {"method": method, "trial": trial, "max_buffer": 30,
                                  "rows": [{"series": item["series"],
                                            "pr": {"a": .8, "b": .8 - 5e-11, "c": .6},
                                            "selected": ["a", "b"]} for item in entries]})
            whole = times[method][trial] * 1_000_000_000
            rows.append({"trial": trial, "position": position, "method": method,
                         "protocol_sha256": protocol_sha, "whole_ns": whole,
                         "phase_ns": {"read": 100, "metric": whole - 400, "selection": 100,
                                      "serialization_and_write": 100}, "unattributed_ns": 100,
                         "counts": {"file_reads": 308, "arrays_read": 1232, "metric_calls": 924,
                                    "selections": 308, "serializations": 1, "file_writes": 1},
                         "output_file": filename})
    refresh_run(auditor, study, rows, protocol_sha)
    return root, study, protocol_sha, rows


def test_public_audit_reconstructs_results_without_any_raw_cache(auditor, receipts):
    root, study, protocol_sha, _ = receipts
    assert not (root / ".cache").exists()
    result = auditor.audit(study, protocol_sha, root=root)
    assert result["status"] == "PASS"
    assert result["median_seconds"] == {"radix_pr": 2., "dense_pr_nearest_radix": 5., "klein_pr": 9.}
    assert result["whole_seconds"]["radix_pr"] == [1., 3., 2.]
    assert result["median_speedup_over_radix"] == {"dense_pr_nearest_radix": 2.5, "klein_pr": 4.5}
    assert result["max_pairwise_pr_difference"] == 0 and result["all_selected_sets_agree"]
    assert len(result["differences"]) == 308 and len(result["differences"][0]["passes"]) == 9
    assert result["differences"][0]["reference_selected"] == ["a", "b"]
    assert result["verification_scope"]["repository_owned_source_bytes"] is True
    assert result["verification_scope"]["raw_npz_bytes_or_decoded_arrays"] is False
    assert not (root / ".cache").exists()


@pytest.mark.parametrize("defect,match", [
    ("duplicate", "duplicated or reordered"), ("count", "operation counts"),
    ("clock", "stage or whole clock"), ("winner", "winner set"),
    ("method", "series, method, trial"), ("nonfinite", "Nonfinite JSON"),
])
def test_rehashed_malformed_receipts_rejected(auditor, receipts, defect, match):
    root, study, protocol_sha, rows = receipts
    if defect == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif defect == "count":
        rows[0]["counts"]["metric_calls"] = 923
    elif defect == "clock":
        rows[0]["unattributed_ns"] += 1
    else:
        path = study / "run" / rows[0]["output_file"]
        value = json.loads(path.read_text())
        if defect == "winner":
            value["rows"][0]["selected"] = ["c"]
        elif defect == "method":
            value["method"] = "klein_pr" if value["method"] != "klein_pr" else "radix_pr"
        else:
            value["rows"][0]["pr"]["a"] = float("nan")
        dump(path, value)
    refresh_run(auditor, study, rows, protocol_sha)
    with pytest.raises(ValueError, match=match):
        auditor.audit(study, protocol_sha, root=root)


def test_pairwise_span_fails_when_each_difference_from_reference_is_small(auditor, receipts):
    root, study, protocol_sha, rows = receipts
    for method, delta in [("dense_pr_nearest_radix", 8e-12), ("klein_pr", -8e-12)]:
        path = study / "run" / f"trial-0-{method}.json"
        value = json.loads(path.read_text())
        value["rows"][0]["pr"]["a"] += delta
        dump(path, value)
    refresh_run(auditor, study, rows, protocol_sha)
    result = auditor.audit(study, protocol_sha, root=root)
    assert result["status"] == "FAIL" and result["receipt_validation"] == "PASS"
    assert result["max_pairwise_pr_difference"] > 1e-11 and result["all_selected_sets_agree"]


def test_runtime_decision_requires_both_controls(auditor, receipts):
    root, study, protocol_sha, rows = receipts
    for row in rows:
        if row["method"] == "klein_pr":
            row["whole_ns"] = 500_000_000
            row["phase_ns"]["metric"] = 499_999_600
    refresh_run(auditor, study, rows, protocol_sha)
    result = auditor.audit(study, protocol_sha, root=root)
    assert result["status"] == "FAIL"
    assert result["radix_faster_than_control"] == {"dense_pr_nearest_radix": True, "klein_pr": False}


def test_repository_source_drift_rejected_without_external_cache(auditor, receipts):
    root, study, protocol_sha, _ = receipts
    (root / "src/sparse_vus/core.py").write_text("changed source\n")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        auditor.audit(study, protocol_sha, root=root)


def test_protocol_anchor_rejects_mutation(auditor, receipts):
    root, study, protocol_sha, _ = receipts
    path = study / "protocol.json"
    value = json.loads(path.read_text())
    value["parity_atol"] = .1
    dump(path, value)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        auditor.audit(study, protocol_sha, root=root)


def test_duplicate_json_fields_rejected(auditor):
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        auditor.parse_json('{"whole_ns":1,"whole_ns":2}')
