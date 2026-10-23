"""Small behavior checks; never run the held-out collection or its timings."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def driver():
    path = Path(__file__).resolve().parents[1] / "experiments/benchmark_vus_collection.py"
    spec = importlib.util.spec_from_file_location("vus_collection_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_inputs(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    labels = np.array([0, 1, 1, 0], dtype=np.int64)
    np.savez(cache / "0000.npz", labels=labels,
             score_0=np.array([0., 1., 1., 0.]),
             score_1=np.array([0., 1., 1., 0.]),
             score_2=np.array([1., 0., 0., 1.]))
    return cache, [{"series": "tiny", "file": "0000.npz", "n": 4}]


def test_whole_workflow_reads_calls_selects_and_writes(tmp_path, driver):
    cache, inputs = fixture_inputs(tmp_path)
    calls = []

    def evaluator(y, s, width):
        calls.append((y.tolist(), s.tolist(), width))
        return float(s[y == 1].mean())

    output = tmp_path / "result.json"
    row = driver.run_workflow(cache, inputs, ["a", "b", "c"], evaluator,
                              output, method="fixture", trial=0, width=30,
                              tie_atol=1e-10)
    result = json.loads(output.read_text())
    assert result["rows"] == [{"series": "tiny", "pr": {"a": 1., "b": 1., "c": 0.},
                               "selected": ["a", "b"]}]
    assert len(calls) == 3 and all(c[2] == 30 for c in calls)
    assert row["counts"] == {"file_reads": 1, "arrays_read": 4, "metric_calls": 3,
                              "selections": 1, "serializations": 1, "file_writes": 1}
    assert row["whole_ns"] >= sum(row["phase_ns"].values()) > 0
    with pytest.raises(FileExistsError):
        driver.run_workflow(cache, inputs, ["a", "b", "c"], evaluator, output,
                            method="fixture", trial=0, width=30, tie_atol=1e-10)
    assert len(calls) == 3  # no repeated metric calls on a forbidden overwrite


def test_array_identity_includes_dtype_shape_and_raw_bits(driver):
    plus = np.array([0., 1.], dtype=np.float64)
    minus = np.array([-0., 1.], dtype=np.float64)
    assert driver.array_identity(plus) != driver.array_identity(minus)
    assert driver.array_identity(plus) != driver.array_identity(plus.astype(np.float32))
    assert driver.array_identity(plus) != driver.array_identity(plus.reshape(1, 2))


def test_source_or_input_drift_rejected(tmp_path, driver):
    source = tmp_path / "source.py"
    source.write_text("original\n")
    bindings = {"source.py": driver.digest(source)}
    driver.verify_files(tmp_path, bindings)
    source.write_text("changed\n")
    with pytest.raises(ValueError, match="SHA-256"):
        driver.verify_files(tmp_path, bindings)


def test_selection_tolerance_keeps_near_tie_and_rejects_nonfinite(driver):
    assert driver.select_best({"a": .5, "b": .5 - 5e-11, "c": .49}, 1e-10) == ["a", "b"]
    with pytest.raises(ValueError):
        driver.select_best({"a": float("nan")}, 1e-10)


def test_decision_requires_parity_sets_and_both_runtime_controls(driver):
    times = {"radix_pr": [1., 1.2, 1.1], "dense_pr_nearest_radix": [2., 2., 2.],
             "klein_pr": [3., 3., 3.]}
    assert driver.decision(times, 1e-13, True, 1e-11)["status"] == "PASS"
    assert driver.decision(times, 2e-11, True, 1e-11)["status"] == "FAIL"
    assert driver.decision(times, 0., False, 1e-11)["status"] == "FAIL"
    times["klein_pr"] = [.5, .5, .5]
    assert driver.decision(times, 0., True, 1e-11)["status"] == "FAIL"


def test_wrong_protocol_digest_rejected_before_inputs(tmp_path, driver):
    (tmp_path / "protocol.json").write_text('{}\n')
    with pytest.raises(ValueError, match="protocol SHA-256"):
        driver.validate_frozen(tmp_path, "0" * 64)


def test_ignored_cache_symlink_is_supported_without_allowing_escape(tmp_path, driver):
    root = tmp_path / "worktree"
    root.mkdir()
    shared = tmp_path / "shared-cache"
    shared.mkdir()
    (root / ".cache").symlink_to(shared, target_is_directory=True)
    resolved, relative = driver.cache_location(root, root / ".cache" / "collection")
    assert resolved == shared / "collection" and relative == ".cache/collection"
    with pytest.raises(ValueError, match="ignored .cache"):
        driver.cache_location(root, root / "public-arrays")


def test_real_method_adapters_agree_on_tiny_stored_collection(tmp_path, driver):
    cache = tmp_path / "cache"
    cache.mkdir()
    labels = np.zeros(32, dtype=np.int8)
    labels[[4, 5, 13, 25]] = 1
    scores = np.repeat(np.arange(8, dtype=float), 4)
    np.savez(cache / "0000.npz", labels=labels, score_0=scores,
             score_1=scores[::-1], score_2=scores.copy())
    entries = [{"series": "tiny-only", "file": "0000.npz", "n": 32}]
    outputs = []
    for method, evaluator in driver.make_methods().items():
        output = tmp_path / f"{method}.json"
        driver.run_workflow(cache, entries, ["a", "b", "c"], evaluator, output,
                            method=method, trial=0, width=30, tie_atol=1e-10)
        outputs.append(json.loads(output.read_text())["rows"][0])
    assert all(r["selected"] == outputs[0]["selected"] for r in outputs)
    assert all(abs(r["pr"][m] - outputs[0]["pr"][m]) <= 1e-11
               for r in outputs for m in ["a", "b", "c"])


def report_fixture(tmp_path, driver, monkeypatch):
    """Replace only the expensive immutable-corpus preflight; use real receipts."""
    cache, entries = fixture_inputs(tmp_path)
    study = tmp_path / "study"
    run = study / "run"
    run.mkdir(parents=True)
    p = {"models": ["a", "b", "c"], "orders": [list(driver.METHODS)] * 3,
         "inputs_sha256": "fixture-input", "source_sha256": {}, "tie_atol": 1e-10,
         "parity_atol": 1e-11, "families": ["fixture"], "scope": "unit-test fixture only"}
    monkeypatch.setattr(driver, "validate_frozen", lambda *a, **k: (p, entries, cache))
    protocol_sha = "fixture-protocol"
    env = {"protocol_sha256": protocol_sha, "inputs_sha256": p["inputs_sha256"],
           "source_sha256": {}, "threads": 1}
    driver.write_json(run / "environment.json", env)
    measurements = []
    for trial, order in enumerate(p["orders"]):
        for position, method in enumerate(order):
            row = driver.run_workflow(cache, entries, p["models"],
                                      lambda y, s, w: float(s[y == 1].mean()),
                                      run / f"trial-{trial}-{method}.json", method=method,
                                      trial=trial, width=30, tie_atol=1e-10)
            measurements.append({**row, "position": position, "protocol_sha256": protocol_sha})
    return study, run, p, protocol_sha, measurements


def finish_fixture(driver, run, p, protocol_sha, measurements):
    (run / "measurements.jsonl").write_text("".join(json.dumps(r) + "\n" for r in measurements))
    driver.write_json(run / "completion.json", {
        "status": "COMPLETE", "passes": 9, "protocol_sha256": protocol_sha,
        "inputs_sha256": p["inputs_sha256"],
        "measurements_sha256": driver.digest(run / "measurements.jsonl"),
        "environment_sha256": driver.digest(run / "environment.json"),
        "outputs_sha256": {r["output_file"]: r["output_sha256"] for r in measurements}})


def test_report_reconstructs_every_pass_and_numeric_difference(tmp_path, driver, monkeypatch):
    study, run, p, protocol_sha, measurements = report_fixture(tmp_path, driver, monkeypatch)
    finish_fixture(driver, run, p, protocol_sha, measurements)
    result = driver.report(study, protocol_sha)
    assert len(result["passes"]) == 9 and result["series"] == 1
    assert result["max_pairwise_pr_difference"] == 0.
    assert result["all_selected_sets_agree"]
    assert len(result["differences"][0]["passes"]) == 9
    assert all(v == 0. for row in result["differences"][0]["passes"]
               for v in row["pr_minus_reference"].values())


@pytest.mark.parametrize("defect,match", [
    ("duplicate_pass", "reordered collection passes"),
    ("wrong_clock", "inconsistent clocks"),
    ("wrong_winner", "selection disagrees"),
    ("wrong_output_method", "coverage/identity"),
])
def test_report_rejects_hash_consistent_malformed_receipts(tmp_path, driver, monkeypatch, defect, match):
    study, run, p, protocol_sha, measurements = report_fixture(tmp_path, driver, monkeypatch)
    if defect == "duplicate_pass":
        measurements[1] = measurements[0].copy()
    elif defect == "wrong_clock":
        measurements[0]["unattributed_ns"] += 1
    else:
        row = measurements[0]
        path = run / row["output_file"]
        value = json.loads(path.read_text())
        if defect == "wrong_winner":
            value["rows"][0]["selected"] = ["c"]
        else:
            value["method"] = "wrong-method"
        path.write_text(json.dumps(value))
        row["output_sha256"] = driver.digest(path)
        row["output_bytes"] = path.stat().st_size
    finish_fixture(driver, run, p, protocol_sha, measurements)
    with pytest.raises(ValueError, match=match):
        driver.report(study, protocol_sha)
