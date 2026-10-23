"""Portable replication must preserve selection, provenance, and output isolation."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def replication():
    path = Path(__file__).resolve().parents[1] / "experiments/reproduce_tie_runs.py"
    spec = importlib.util.spec_from_file_location("portable_tie_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selection_allows_only_time_and_environment(replication):
    original = {"environment": {"python": "host-a"}, "frozen_utc": "before",
                "parameters": {"seed": 1}, "series": ["fixed"], "source_sha256": {"x": "abc"}}
    regenerated = copy.deepcopy(original)
    regenerated.update(environment={"python": "host-b"}, frozen_utc="after")
    assert replication.compare_selection(original, regenerated)["status"] == "SELECTION_IDENTICAL"
    regenerated["parameters"]["seed"] = 2
    with pytest.raises(ValueError, match="Selection differs"):
        replication.compare_selection(original, regenerated)
    with pytest.raises(ValueError, match="field set"):
        replication.compare_selection(original, {**original, "unbound_extra": True})


def manifests(replication):
    rows = []
    for i in range(12):
        rows.append({"series": f"series{i}", "family": f"family{i % 9}",
            "canonical_family": f"family{i % 9}", "url": f"pinned/{i}", "raw_bytes": 10,
            "raw_sha256": f"raw{i}", "n": 3, "preprocessing": {"order": "unchanged"},
            "actual_parameters": {"rank": 1}, "npz_sha256": f"npz{i}",
            "array_sha256": {name: f"{name}-{i}" for name in ("labels", *replication.MODELS)}})
    original = {"status": "INPUTS_VERIFIED_NO_METRIC_OUTCOMES", "series_count": 12,
        "family_count": 9, "score_vectors": 48, "models": list(replication.MODELS),
        "metric_outcomes_computed": False, "parameters": {"seed": 1}, "series": rows}
    return original, copy.deepcopy(original)


def test_scores_may_change_but_are_counted(replication):
    old, new = manifests(replication)
    new["series"][0]["array_sha256"][replication.MODELS[0]] = "different-score"
    new["series"][0]["npz_sha256"] = "different-container"
    result = replication.compare_manifests(old, new)
    assert result["score_vectors_compared"] == 48
    assert result["score_vectors_equal"] == 47
    assert not result["all_score_vectors_byte_identical"]


@pytest.mark.parametrize("field", ["raw_sha256", "labels", "duplicate"])
def test_required_input_identity_cannot_drift(replication, field):
    old, new = manifests(replication)
    if field == "labels":
        new["series"][0]["array_sha256"]["labels"] = "changed"
    elif field == "duplicate":
        new["series"][1] = copy.deepcopy(new["series"][0])
    else:
        new["series"][0][field] = "changed"
    with pytest.raises(ValueError):
        replication.compare_manifests(old, new)


def test_reservation_rejects_existing_outputs_and_escape(replication, tmp_path):
    target = "artifacts/tie-runs/fresh"
    output, cache = replication.reserve_paths(tmp_path, target)
    marker = output / "retained.txt"
    marker.write_text("do not replace")
    with pytest.raises(ValueError, match="both be new"):
        replication.reserve_paths(tmp_path, target)
    assert marker.read_text() == "do not replace" and cache.is_dir()
    with pytest.raises(ValueError, match="inside repository"):
        replication.reserve_paths(tmp_path, tmp_path.parent / "outside")
    with pytest.raises(ValueError, match="escapes"):
        replication.bound_path(tmp_path, "../outside")


def test_source_hash_guard_rejects_modified_bytes(replication, tmp_path):
    path = tmp_path / "generator.py"
    path.write_text("original")
    bindings = {"generator.py": replication.digest(path)}
    replication.check_hashes(tmp_path, bindings)
    path.write_text("changed")
    with pytest.raises(ValueError, match="Bound source/input changed"):
        replication.check_hashes(tmp_path, bindings)


def test_shared_cache_symlink_preserves_logical_paths(replication, tmp_path):
    root, shared = tmp_path / "repo", tmp_path / "shared-cache"
    root.mkdir()
    shared.mkdir()
    (root / ".cache").symlink_to(shared, target_is_directory=True)
    source = shared / "reference.py"
    source.write_text("pinned reference")
    logical = replication.bound_path(root, ".cache/reference.py")
    assert logical == root / ".cache/reference.py"
    assert logical.relative_to(root).as_posix() == ".cache/reference.py"
    replication.check_hashes(root, {".cache/reference.py": replication.digest(source)})
    output, cache = replication.reserve_paths(root, "artifacts/tie-runs/shared")
    assert output.is_dir() and cache.is_dir()
    assert cache == root / ".cache/tie-replication/shared"
    assert cache.relative_to(root).as_posix() == ".cache/tie-replication/shared"
    assert cache.resolve() == shared / "tie-replication/shared"
    array_path = cache / "arrays/example.npz"
    array_path.parent.mkdir()
    np.savez(array_path, labels=np.array([0, 1, 0], dtype=np.uint8))
    assert array_path.relative_to(root).as_posix().startswith(".cache/")
    assert replication.bound_path(root, array_path.relative_to(root)) == array_path


def test_shared_cache_does_not_authorize_other_symlink_escapes(replication, tmp_path):
    root, shared, outside = (tmp_path / name for name in ("repo", "cache", "outside"))
    for directory in (root, shared, outside):
        directory.mkdir()
    (root / ".cache").symlink_to(shared, target_is_directory=True)
    (shared / "escape").symlink_to(outside, target_is_directory=True)
    (root / "other").symlink_to(shared, target_is_directory=True)
    for relative in (".cache/escape/file.npz", "other/file.npz", "../outside/file.npz",
                     ".cache/../file.npz", outside / "file.npz"):
        with pytest.raises(ValueError):
            replication.bound_path(root, relative)


def test_array_digest_matches_real_frozen_fixture(replication):
    root = Path(__file__).resolve().parents[1]
    rows = json.loads((root / "artifacts/tie-runs/mac-20261023/inputs.json").read_text())
    item = next(row for row in rows if row["phase"] == "structural")
    with np.load(root / item["input_path"], allow_pickle=False) as arrays:
        for name, key in (("labels", "labels_sha256"), ("scores", "scores_sha256")):
            assert replication.array_digest(arrays[name]) == item[key]
            assert hashlib.sha256(arrays[name].tobytes()).hexdigest() != item[key]


def input_fixture(replication, tmp_path):
    output, cache = replication.reserve_paths(tmp_path, "artifacts/tie-runs/fixtures")
    source = tmp_path / "source"
    source.mkdir()
    labels = np.array([0, 1, 0], dtype=np.uint8)
    scores = np.array([2., 1., 0.])
    structural_path = source / "structural.npz"
    np.savez(structural_path, labels=labels, scores=scores)
    structural = {"case_id": "fixture|32", "phase": "structural", "family": "fixture",
        "series": "fixture", "model": "fixture", "max_buffer": 32, "n": 3,
        "positive_points": 1, "input_path": str(structural_path.relative_to(tmp_path)),
        "npz_sha256": replication.digest(structural_path),
        "labels_sha256": replication.array_digest(labels), "scores_sha256": replication.array_digest(scores)}
    raw_path = source / "external.npz"
    arrays = {"labels": labels, **{model: scores.copy() for model in replication.MODELS}}
    np.savez(raw_path, **arrays)
    manifest = {"series": [{"series": "example", "family": "fixed", "n": 3,
        "npz_path": str(raw_path.relative_to(tmp_path)), "npz_sha256": replication.digest(raw_path),
        "array_sha256": {name: hashlib.sha256(a.tobytes()).hexdigest() for name, a in arrays.items()}}]}
    expected = {("example", model, width) for model in replication.MODELS for width in replication.WIDTHS}
    return output, cache, structural, manifest, expected, raw_path


def test_input_freeze_keeps_observations_ignored_and_all_widths(replication, tmp_path):
    output, cache, structural, manifest, expected, _ = input_fixture(replication, tmp_path)
    rows = replication.make_inputs(tmp_path, output, cache, manifest, [structural], expected)
    assert len(rows) == 13
    assert len(list((output / "inputs").glob("*.npz"))) == 1
    external = [row for row in rows if row["phase"] == "external_regenerated"]
    assert len(external) == 12
    assert {row["max_buffer"] for row in external} == {30, 100, 300}
    assert all(row["input_path"].startswith(".cache/tie-replication/") for row in external)
    assert len({row["input_path"] for row in external}) == 4
    for row in rows:
        assert replication.digest(tmp_path / row["input_path"]) == row["npz_sha256"]


def test_generated_npz_tampering_is_rejected(replication, tmp_path):
    output, cache, structural, manifest, expected, path = input_fixture(replication, tmp_path)
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Generated NPZ identity"):
        replication.make_inputs(tmp_path, output, cache, manifest, [structural], expected)


def test_missing_prescribed_external_case_is_rejected(replication, tmp_path):
    output, cache, structural, manifest, expected, _ = input_fixture(replication, tmp_path)
    expected.add(("missing", replication.MODELS[0], 30))
    with pytest.raises(ValueError, match="case coverage differs"):
        replication.make_inputs(tmp_path, output, cache, manifest, [structural], expected)


@pytest.mark.parametrize("kind", ["nonfinite_score", "invalid_label", "score_dtype", "score_shape"])
def test_consistently_rehashed_invalid_arrays_are_rejected(replication, tmp_path, kind):
    output, cache, structural, manifest, expected, path = input_fixture(replication, tmp_path)
    with np.load(path, allow_pickle=False) as stored:
        arrays = {name: stored[name].copy() for name in stored.files}
    model = replication.MODELS[0]
    if kind == "nonfinite_score":
        arrays[model][0] = np.nan
    elif kind == "invalid_label":
        arrays["labels"][0] = 2
    elif kind == "score_dtype":
        arrays[model] = arrays[model].astype(np.float32)
    else:
        arrays[model] = arrays[model][:-1]
    np.savez(path, **arrays)
    receipt = manifest["series"][0]
    receipt["npz_sha256"] = replication.digest(path)
    receipt["array_sha256"] = {name: hashlib.sha256(a.tobytes()).hexdigest()
                               for name, a in arrays.items()}
    with pytest.raises(ValueError):
        replication.make_inputs(tmp_path, output, cache, manifest, [structural], expected)


def test_generated_scalar_passes_actual_frozen_runner_identity_checks(replication, tmp_path, monkeypatch):
    output, cache, structural, manifest, expected, _ = input_fixture(replication, tmp_path)
    rows = replication.make_inputs(tmp_path, output, cache, manifest, [structural], expected)
    external = next(row for row in rows if row["phase"] == "external_regenerated")
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/benchmark_tie_runs.py"
    spec = importlib.util.spec_from_file_location("frozen_tie_identity_test", path)
    benchmark = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(benchmark)
    monkeypatch.setattr(benchmark, "ROOT", tmp_path)
    monkeypatch.setattr(benchmark, "environment", lambda: {})
    monkeypatch.setattr(benchmark, "contract", lambda output, expected: (
        {"methods": list(benchmark.METHODS), "seed": benchmark.SEED, "repetitions": 5}, [external]))
    import sparse_vus.tie_runs as candidate

    class ReachedWarmup(Exception):
        pass

    def stop_before_any_metric_or_timing(labels, scores, width):
        assert labels.dtype == np.uint8 and scores.dtype == np.float64
        assert np.isfinite(scores).all() and width == 30
        raise ReachedWarmup

    monkeypatch.setattr(candidate, "interval_pr_tie_runs_jit", stop_before_any_metric_or_timing)
    # The unmodified run() must accept the NPZ and both array hashes before
    # reaching the first warm call. No metric or timing loop executes.
    with pytest.raises(ReachedWarmup):
        benchmark.run(output, "fixture-contract")


def test_run_rejects_wrong_hash_before_loading_benchmark(replication, tmp_path, monkeypatch):
    output, _ = replication.reserve_paths(tmp_path, "artifacts/tie-runs/hash-guard")
    (output / "protocol.json").write_text("{}")
    monkeypatch.setattr(replication.importlib, "import_module",
                        lambda name: pytest.fail("Benchmark imported before protocol check"))
    with pytest.raises(ValueError, match="Protocol hash differs"):
        replication.run(output, "incorrect", tmp_path)
