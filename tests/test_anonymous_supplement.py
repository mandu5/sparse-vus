"""Archive-boundary checks using tiny repositories, with no network or timings."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))


def builder():
    assert importlib.util.find_spec("build_anonymous_supplement") is not None, "Supplement builder missing"
    return importlib.import_module("build_anonymous_supplement")


def put(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode())
    return path


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    put(root, "pyproject.toml", '[project]\nname="fixture"\nversion="0.1"\n')
    put(root, "LICENSE", "MIT License\nCopyright Scientific contributors\n")
    put(root, "THIRD_PARTY.md", "Credit Tom Louis Klein; https://github.com/tomlouisklein/fast-VUS\n")
    put(root, "src/sparse_vus/core.py", "def exact_value():\n    return 0.5\n")
    put(root, "tests/test_core.py", "from sparse_vus.core import exact_value\ndef test_value(): assert exact_value() == .5\n")
    put(root, "experiments/protocol.json", '{"seed": 7, "widths": [30, 100]}\n')
    put(root, "artifacts/run/measurements.jsonl", '{"seconds": [1.25, 2.5], "score": 1e-14}\n')
    put(root, "docs/theory.md", "An exact proof.\n")
    return root


def build(root, output, **kwargs):
    mod = builder()
    rules = mod.PrivacyRules(author_tokens=("review user", "reviewuser", "user@example.test"),
                             owner_accounts=("review-owner",))
    return mod.build_supplement(root, output, rules=rules, **kwargs)


def test_allowlist_keeps_science_and_excludes_private_cache_and_logs(repository, tmp_path):
    # A broad recursive copy would leak these files, including caches inside allowed roots.
    excluded = [".git/config", "cache/score.npy", ".cache/upstream.py", "private-context.md",
                "docs/submission_packet.md", "docs/tmlr_submission_audit_20261021.md",
                "experiments/vendor/upstream.py", "src/__pycache__/secret.py",
                "artifacts/run/run.log", "artifacts/full-tests.txt", "artifacts/public-progress.jsonl",
                "paper/main.tex", "CITATION.cff"]
    for name in excluded:
        put(repository, name, "user@example.test")
    output = tmp_path / "supplement.zip"
    build(repository, output)
    with zipfile.ZipFile(output) as archive:
        assert set(excluded).isdisjoint(archive.namelist())
        for name in ["src/sparse_vus/core.py", "tests/test_core.py", "experiments/protocol.json",
                     "artifacts/run/measurements.jsonl", "THIRD_PARTY.md", "LICENSE", "docs/theory.md"]:
            assert archive.read(name) == (repository / name).read_bytes()
        assert "README.md" in archive.namelist()


def test_followup_science_is_included_but_venue_and_author_context_are_excluded(repository, tmp_path):
    science = ["radix_prior_art_20261021.md", "pr_protocol_independent_review_20261021.md",
               "exact_vus_sota_search_20261021.md"]
    private = ["venue_route_20261021.md", "tmlr_submission_audit_20261021.md",
               "private-submission-context.md"]
    for name in science:
        put(repository, "docs/" + name, "Scientific evidence; third-party credit Tom Louis Klein.\n")
    for name in private:
        put(repository, "docs/" + name, "Unneeded author and submission context.\n")
    output = tmp_path / "followup.zip"
    build(repository, output)
    with zipfile.ZipFile(output) as archive:
        for name in science:
            assert archive.read("docs/" + name) == (repository / "docs" / name).read_bytes()
        assert all("docs/" + name not in archive.namelist() for name in private)


def test_historical_snapshot_keeps_code_license_and_inventory_but_not_cache_links(repository, tmp_path):
    snapshot = repository / "artifacts/pr-engine/source-v2"
    source = put(snapshot, "experiments/audit_pr_engine.py", "VERSION = 2\n")
    license_file = put(snapshot, "LICENSE", (repository / "LICENSE").read_bytes())
    inventory = put(snapshot, "source-manifest.json", json.dumps({"files": [
        {"path": "experiments/audit_pr_engine.py", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
        {"path": "LICENSE", "sha256": hashlib.sha256(license_file.read_bytes()).hexdigest()},
    ]}, indent=2))
    cached = tmp_path / "downloaded"
    put(cached, "upstream.py", "UPSTREAM_MUST_NOT_BE_DISTRIBUTED = True\n")
    (snapshot / "cache").symlink_to(cached, target_is_directory=True)
    (snapshot / ".cache").symlink_to(cached, target_is_directory=True)
    put(repository, "artifacts/unrelated/LICENSE", "Do not broaden the extensionless allowlist.\n")
    output = tmp_path / "historical.zip"
    build(repository, output)
    with zipfile.ZipFile(output) as archive:
        for path in (source, license_file, inventory):
            assert archive.read(path.relative_to(repository).as_posix()) == path.read_bytes()
        assert not any("/cache/" in name or "/.cache/" in name for name in archive.namelist())
        assert "artifacts/unrelated/LICENSE" not in archive.namelist()
        manifest = json.loads(archive.read("ANONYMIZATION_MANIFEST.json"))
        entry = next(x for x in manifest["files"] if x["path"].endswith("source-v2/LICENSE"))
        assert entry["byte_identical"] is True


def test_metadata_redaction_keeps_numeric_results_and_third_party_identity(repository, tmp_path):
    source = '{"cache":"/Users/reviewuser/private/cache","owner":"https://github.com/review-owner/project", "credit":"Tom Louis Klein", "url":"https://github.com/tomlouisklein/fast-VUS", "seconds":[1.25000,2.5e-03],"author":"review user"}\n'
    put(repository, "artifacts/run/environment.json", source)
    output = tmp_path / "supplement.zip"
    build(repository, output)
    with zipfile.ZipFile(output) as archive:
        raw = archive.read("artifacts/run/environment.json")
        value = json.loads(raw)
        assert value["seconds"] == [1.25, 0.0025]
        assert b'"seconds":[1.25000,2.5e-03]' in raw
        assert value["credit"] == "Tom Louis Klein"
        assert value["url"] == "https://github.com/tomlouisklein/fast-VUS"
        assert b"reviewuser" not in raw and b"review-owner" not in raw and b"review user" not in raw
        assert b"/Users/" not in raw
        assert (repository / "artifacts/run/environment.json").read_text() == source


def test_manifest_distinguishes_original_and_anonymous_bytes(repository, tmp_path):
    metadata = put(repository, "artifacts/run/environment.json", '{"cache":"/home/reviewuser/cache"}\n')
    output = tmp_path / "supplement.zip"
    build(repository, output)
    with zipfile.ZipFile(output) as archive:
        manifest = json.loads(archive.read("ANONYMIZATION_MANIFEST.json"))
        entries = {entry["path"]: entry for entry in manifest["files"]}
        code = entries["src/sparse_vus/core.py"]
        assert code["byte_identical"] is True and not code["transformations"]
        changed = entries["artifacts/run/environment.json"]
        assert changed["byte_identical"] is False and changed["transformations"]
        assert changed["source_sha256"] == hashlib.sha256(metadata.read_bytes()).hexdigest()
        assert changed["anonymous_sha256"] == hashlib.sha256(archive.read(changed["path"])).hexdigest()
        assert changed["source_sha256"] != changed["anonymous_sha256"]
        assert "reviewuser" not in json.dumps(manifest)


def test_measured_code_is_never_silently_redacted(repository, tmp_path):
    put(repository, "src/sparse_vus/core.py", 'OWNER="reviewuser"\n')
    with pytest.raises(ValueError, match="source|code"):
        build(repository, tmp_path / "supplement.zip")
    assert not (tmp_path / "supplement.zip").exists()


def test_symlink_cannot_export_a_file_outside_the_repository(repository, tmp_path):
    outside = put(tmp_path, "private.py", "SECRET=42\n")
    (repository / "src/sparse_vus/escape.py").symlink_to(outside)
    with pytest.raises(ValueError, match="[Ss]ymlink"):
        build(repository, tmp_path / "supplement.zip")


def test_output_is_deterministic_and_size_limit_fails_before_publication(repository, tmp_path):
    first, second = tmp_path / "a.zip", tmp_path / "b.zip"
    build(repository, first)
    build(repository, second)
    assert first.read_bytes() == second.read_bytes()
    with pytest.raises(ValueError, match="limit|size"):
        build(repository, tmp_path / "too-large.zip", max_bytes=100)
    assert not (tmp_path / "too-large.zip").exists()


def test_escaped_json_identifier_is_detected_without_rewriting_numbers(repository, tmp_path):
    put(repository, "artifacts/run/environment.json", r'{"cache":"/\u0055sers/reviewuser/a","n":1000,"error":1e-10}')
    output = tmp_path / "supplement.zip"
    build(repository, output)
    with zipfile.ZipFile(output) as archive:
        value = json.loads(archive.read("artifacts/run/environment.json"))
        assert "reviewuser" not in value["cache"] and "/Users/" not in value["cache"]
        assert value["n"] == 1000 and value["error"] == 1e-10


def test_unknown_binary_under_artifacts_is_not_silently_included(repository, tmp_path):
    put(repository, "artifacts/run/raw_scores.npy", b"opaque input data")
    output = tmp_path / "supplement.zip"
    build(repository, output)
    with zipfile.ZipFile(output) as archive:
        assert "artifacts/run/raw_scores.npy" not in archive.namelist()


def test_extracted_manifest_verifier_detects_tampering(repository, tmp_path):
    output = tmp_path / "supplement.zip"
    build(repository, output)
    extracted = tmp_path / "extracted"
    with zipfile.ZipFile(output) as archive:
        archive.extractall(extracted)
    command = [sys.executable, "experiments/verify_anonymous_manifest.py"]
    assert subprocess.run(command, cwd=extracted, capture_output=True).returncode == 0
    (extracted / "src/sparse_vus/core.py").write_text("changed\n")
    assert subprocess.run(command, cwd=extracted, capture_output=True).returncode != 0


def test_fresh_reproduction_workspace_preserves_published_results(repository, tmp_path):
    put(repository, "artifacts/mechanism_protocol.json", '{"seed":42}\n')
    put(repository, "artifacts/external_supplement_protocol.json", '{"limit":10}\n')
    output = tmp_path / "supplement.zip"
    build(repository, output)
    extracted = tmp_path / "extracted"
    with zipfile.ZipFile(output) as archive:
        archive.extractall(extracted)
    destination = tmp_path / "reproduction"
    command = [sys.executable, "experiments/create_anonymous_reproduction_workspace.py",
               "--output", str(destination)]
    result = subprocess.run(command, cwd=extracted, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (destination / "artifacts/mechanism_protocol.json").exists()
    assert not (destination / "artifacts/run/measurements.jsonl").exists()
    assert (extracted / "artifacts/run/measurements.jsonl").exists()
    assert subprocess.run(command, cwd=extracted, capture_output=True).returncode != 0


def test_anonymous_hash_bindings_follow_changed_metadata_and_preserve_original_provenance(repository, tmp_path):
    environment = put(repository, "artifacts/run/environment.json", '{"cpu_clearance":"Private agent coordination","seconds":1.25}\n')
    old_hash = hashlib.sha256(environment.read_bytes()).hexdigest()
    put(repository, "artifacts/run/audit.json", json.dumps({"environment_sha256": old_hash, "cases": 12}))
    output = tmp_path / "supplement.zip"
    build(repository, output)
    with zipfile.ZipFile(output) as archive:
        new_hash = hashlib.sha256(archive.read("artifacts/run/environment.json")).hexdigest()
        assert new_hash != old_hash
        assert json.loads(archive.read("artifacts/run/audit.json"))["environment_sha256"] == new_hash
        manifest = json.loads(archive.read("ANONYMIZATION_MANIFEST.json"))
        entry = next(x for x in manifest["files"] if x["path"] == "artifacts/run/environment.json")
        assert entry["source_sha256"] == old_hash
        assert json.loads(archive.read(entry["path"]))["seconds"] == 1.25


def test_owner_links_include_github_api_pages_and_raw_hosts(repository, tmp_path):
    urls = ["https://api.github.com/repos/review-owner/project/actions/runs/1",
            "https://review-owner.github.io/project/",
            "https://raw.githubusercontent.com/review%2downer/project/main/readme.md"]
    put(repository, "artifacts/links.json", json.dumps(urls))
    output = tmp_path / "supplement.zip"
    build(repository, output)
    with zipfile.ZipFile(output) as archive:
        text = archive.read("artifacts/links.json").decode()
        assert "review-owner" not in text and "review%2downer" not in text
