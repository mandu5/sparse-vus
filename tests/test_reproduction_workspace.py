"""Fresh workspaces retain historical audit inputs without copying caches."""
import hashlib
import importlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))


def helper():
    return importlib.import_module("create_reproduction_workspace")


def put(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def snapshot(root):
    directory = root / "artifacts/pr-engine/source-v2"
    inventory = []
    for name in sorted(helper().SNAPSHOT_REQUIRED | {"src/sparse_vus/radix.py"}):
        content = ("historical bytes: " + name + "\n").encode()
        put(directory, name, content)
        inventory.append({"path": name, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
    put(directory, "source-manifest.json", json.dumps({"files": inventory}).encode())
    return directory


def test_new_workspace_copies_complete_historical_inventory_and_anchors(tmp_path, monkeypatch):
    root, destination = tmp_path / "source", tmp_path / "rerun"
    for name in ("src", "tests", "experiments", "docs", ".github"):
        (root / name).mkdir(parents=True)
    for name in ("pyproject.toml", "README.md", "LICENSE", "THIRD_PARTY.md", "CITATION.cff", ".gitignore",
                 "paper/main.tex", "artifacts/mechanism_protocol.json", "artifacts/external_supplement_protocol.json"):
        put(root, name, b"fixture\n")
    historical = snapshot(root)
    outside = tmp_path / "cached-inputs"
    outside.mkdir()
    put(outside, "private.npy", b"not redistributable")
    (historical / "cache").symlink_to(outside, target_is_directory=True)
    (historical / ".cache").symlink_to(outside, target_is_directory=True)
    put(historical, "unlisted.log", b"must not copy")
    put(root, "artifacts/public_benchmark.jsonl", b"published root evidence\n")
    monkeypatch.setattr(helper(), "ROOT", root)
    helper().create_workspace(destination)
    copied = destination / "artifacts/pr-engine/source-v2"
    inventory = json.loads((historical / "source-manifest.json").read_text())
    assert (copied / "source-manifest.json").read_bytes() == (historical / "source-manifest.json").read_bytes()
    for entry in inventory["files"]:
        assert (copied / entry["path"]).read_bytes() == (historical / entry["path"]).read_bytes()
    for name in ("experiments/audit_pr_engine.py", "artifacts/public_benchmark.jsonl",
                 "artifacts/public_benchmark_receipt.json", "experiments/data_hashes.json", "LICENSE"):
        assert (copied / name).is_file()
    assert not (copied / "cache").exists() and not (copied / ".cache").exists()
    assert not (copied / "unlisted.log").exists()
    # The legacy rerun still needs an empty root result location.
    assert not (destination / "artifacts/public_benchmark.jsonl").exists()
    assert (root / "artifacts/public_benchmark.jsonl").read_bytes() == b"published root evidence\n"


@pytest.mark.parametrize("change", ["changed_bytes", "omitted_anchor", "omitted_source", "external_symlink", "parent_path"])
def test_historical_copy_rejects_invalid_inventory_before_creating_snapshot(tmp_path, change):
    root, destination = tmp_path / "source", tmp_path / "rerun"
    historical = snapshot(root)
    manifest_path = historical / "source-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entry = next(row for row in manifest["files"] if row["path"] == "LICENSE")
    if change == "changed_bytes":
        (historical / "LICENSE").write_bytes(b"changed")
    elif change == "omitted_anchor":
        manifest["files"] = [row for row in manifest["files"] if row["path"] != "artifacts/selected_series.json"]
    elif change == "omitted_source":
        manifest["files"] = [row for row in manifest["files"] if row["path"] != "src/sparse_vus/compiled.py"]
    elif change == "external_symlink":
        outside = put(tmp_path, "external-license", (historical / "LICENSE").read_bytes())
        (historical / "LICENSE").unlink()
        (historical / "LICENSE").symlink_to(outside)
    else:
        manifest["files"].append({**entry, "path": "../escape"})
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        helper().copy_historical_snapshot(root, destination)
    assert not (destination / "artifacts/pr-engine/source-v2").exists()


def test_staged_downloader_creates_cache_and_preserves_release_receipts(tmp_path):
    root, output = tmp_path / "source", tmp_path / "rerun"
    names = ("fetch_score_ranges.py", "fetch_data.py", "data_manifest.json", "data_hashes.json")
    for name in names:
        put(root, "experiments/" + name, ("pinned input: " + name).encode())
    original = put(root, "artifacts/bolt_base_64-download.json", b"original release receipt\n")
    assert not (root / "cache").exists()
    staging = helper().prepare_data_fetch(root, output)
    assert (root / "cache").is_dir()
    assert (staging / "cache").is_symlink()
    assert (staging / "cache").resolve() == (root / "cache").resolve()
    for name in names:
        assert (staging / "experiments" / name).read_bytes() == (root / "experiments" / name).read_bytes()
    (staging / "artifacts/bolt_base_64-download.json").write_bytes(b"fresh download receipt\n")
    assert original.read_bytes() == b"original release receipt\n"
    with pytest.raises(FileExistsError):
        helper().prepare_data_fetch(root, output)
