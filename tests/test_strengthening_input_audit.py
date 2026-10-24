"""Tamper and historical-source boundaries; no detector or metric execution."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


def auditor():
    path = Path(__file__).resolve().parents[1] / "experiments/audit_strengthening_inputs.py"
    spec = importlib.util.spec_from_file_location("input_auditor", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def test_changed_bytes_are_rejected(tmp_path):
    target = tmp_path / "source.py"
    target.write_bytes(b"changed")
    with pytest.raises(ValueError, match="identity"):
        auditor().read_verified(target, digest(b"original"))


def test_native_score_comparison_preserves_signed_zero(tmp_path):
    target = tmp_path / "anomaly_scores.ts"
    target.write_text("-0\n1.0000000000000002\n")
    expected = np.array([-0.0, np.nextafter(1.0, 2.0)])
    auditor().verify_native_score(target, expected)
    target.write_text("0\n1.0000000000000002\n")
    with pytest.raises(ValueError, match="bits"):
        auditor().verify_native_score(target, expected)


def test_historical_producer_uses_hash_bound_archive_fallback(tmp_path):
    module = auditor()
    current = tmp_path / "scripts/prepare_strengthening_workload.py"
    current.parent.mkdir()
    current.write_bytes(b"current fixed producer")
    archive = tmp_path / "artifacts/pvldb-research-20261024/strengthening/provenance"
    archive.mkdir(parents=True)
    original = archive / "prepare_strengthening_workload.frozen.py"
    original.write_bytes(b"historical producer")
    recovery = archive / "assemble_existing_scores.py"
    recovery.write_bytes(b"historical recovery")
    old_producer = "/unavailable/mac-cache/prepare_strengthening_workload.frozen.py"
    old_recovery = "/unavailable/mac-cache/assemble_existing_scores.py"
    entries = [{"historical_cache_path": old_producer,
                "archive_path": str(original.relative_to(tmp_path)),
                "sha256": digest(original.read_bytes())},
               {"historical_cache_path": old_recovery,
                "archive_path": str(recovery.relative_to(tmp_path)),
                "sha256": digest(recovery.read_bytes())}]
    (archive / "mapping.json").write_text(json.dumps({"entries": entries}))
    protocol = {"pinned_files": [{"path": str(current.relative_to(tmp_path)),
                                  "sha256": digest(original.read_bytes())}]}
    generation = {"post_generation_packaging_recovery": {
        "frozen_producer_path": old_producer,
        "frozen_producer_sha256": digest(original.read_bytes()),
        "recovery_script_path": old_recovery,
        "recovery_script_sha256": digest(recovery.read_bytes()),
        "fits_repeated": 0}}
    checked = module.verify_frozen_sources(protocol, generation, tmp_path)
    assert any(x["path"] == str(original) for x in checked)
    original.write_bytes(b"tampered historical producer")
    with pytest.raises(ValueError, match="identity"):
        module.verify_frozen_sources(protocol, generation, tmp_path)


def test_clean_run_cannot_substitute_a_different_current_producer(tmp_path):
    current = tmp_path / "scripts/prepare_strengthening_workload.py"
    current.parent.mkdir()
    current.write_bytes(b"different producer")
    protocol = {"pinned_files": [{"path": str(current.relative_to(tmp_path)),
                                  "sha256": digest(b"frozen producer")}]}
    with pytest.raises(ValueError, match="identity"):
        auditor().verify_frozen_sources(protocol, {}, tmp_path)


def test_duplicate_identity_rows_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        auditor().unique_index([{"id": "same"}, {"id": "same"}], ("id",))
