"""Tamper and historical-source boundaries; no detector or metric execution."""
import hashlib
import importlib.util
import json
import math
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


def decoding_fixture(module):
    literal = "2.9364790299813794"
    correct = float(literal)
    frozen = math.nextafter(correct, -math.inf)
    raw = ("Data,Label\n1,0\n" + literal + ",1\n4,0\n").encode()
    parsed = np.array([[1.0], [correct], [4.0]], dtype=np.float64)
    original = np.array([[1.0], [frozen], [4.0]], dtype=np.float64)
    entry = {
        "case_id": "fixture", "raw_member_sha256": digest(raw),
        "row_index_zero_based": 1, "column": "Data", "literal": literal,
        "correctly_rounded_binary64_hex": correct.hex(),
        "original_frozen_binary64_hex": frozen.hex(),
        "correctly_rounded_observation_sha256": module.array_digest(parsed[:, 0]),
        "original_frozen_observation_sha256": module.array_digest(original[:, 0]),
    }
    case = {"id": "fixture", "n": 3, "raw_sha256": digest(raw),
            "observation_hashes": [entry["original_frozen_observation_sha256"], "unused-z-hash"]}
    return raw, parsed, original, entry, case


def test_declared_decode_reconstructs_only_the_original_typed_input():
    module = auditor()
    raw, parsed, original, entry, case = decoding_fixture(module)
    actual, receipt = module.replay_observation_decode(parsed, raw, case, entry)
    assert actual.tobytes() == original.tobytes()
    assert parsed[1, 0].hex() == entry["correctly_rounded_binary64_hex"]
    assert receipt["compatibility_value_applied"] is True
    assert receipt["observed_before_sha256"] == entry["correctly_rounded_observation_sha256"]
    assert receipt["verified_original_observation_sha256"] == entry["original_frozen_observation_sha256"]


def test_declared_decode_accepts_an_already_original_vector_without_changing_it():
    module = auditor()
    raw, _, original, entry, case = decoding_fixture(module)
    actual, receipt = module.replay_observation_decode(original, raw, case, entry)
    assert actual.tobytes() == original.tobytes()
    assert receipt["compatibility_value_applied"] is False


@pytest.mark.parametrize("tamper", ["raw", "literal", "row", "column", "correct_hex",
                                     "nonadjacent", "source_hash", "other_point"])
def test_declared_decode_rejects_source_or_bit_changes(tamper):
    module = auditor()
    raw, parsed, _, entry, case = decoding_fixture(module)
    if tamper == "raw":
        raw += b"\n"
    elif tamper == "literal":
        entry["literal"] = "2.9364790299813795"
    elif tamper == "row":
        entry["row_index_zero_based"] = 0
    elif tamper == "column":
        entry["column"] = "Label"
    elif tamper == "correct_hex":
        entry["correctly_rounded_binary64_hex"] = entry["original_frozen_binary64_hex"]
    elif tamper == "nonadjacent":
        original = float.fromhex(entry["original_frozen_binary64_hex"])
        entry["original_frozen_binary64_hex"] = math.nextafter(original, -math.inf).hex()
    elif tamper == "source_hash":
        entry["original_frozen_observation_sha256"] = "0" * 64
    else:
        parsed[0, 0] = math.nextafter(parsed[0, 0], math.inf)
    with pytest.raises(ValueError, match="decoding"):
        module.replay_observation_decode(parsed, raw, case, entry)


def test_decoding_contract_is_optional_and_exactly_source_bound(tmp_path):
    module = auditor()
    assert module.load_decoding_replay({}, {}, tmp_path) == (None, {})
    source = Path(__file__).resolve().parents[1] / module.DECODING_CONTRACT
    target = tmp_path / module.DECODING_CONTRACT
    target.parent.mkdir(parents=True)
    target.write_bytes(source.read_bytes())
    contract = json.loads(source.read_text())
    entry = contract["entries"][0]
    selected = {(entry["case_id"],): {
        "id": entry["case_id"], "n": 18236,
        "raw_sha256": entry["raw_member_sha256"],
        "observation_hashes": [entry["original_frozen_observation_sha256"], "unused-z-hash"],
    }}
    declaration = {"contract_path": str(module.DECODING_CONTRACT),
                   "contract_sha256": module.DECODING_CONTRACT_SHA256,
                   "purpose": module.DECODING_REPLAY_PURPOSE}
    protocol = {"decoding_replay": declaration,
                "pinned_files": [{"path": declaration["contract_path"],
                                  "sha256": declaration["contract_sha256"]}]}
    receipt, entries = module.load_decoding_replay(protocol, selected, tmp_path)
    assert receipt["contract_sha256"] == digest(source.read_bytes())
    assert list(entries) == [entry["case_id"]]
    target.write_bytes(source.read_bytes() + b"\n")
    protocol["decoding_replay"]["contract_sha256"] = digest(target.read_bytes())
    protocol["pinned_files"][0]["sha256"] = digest(target.read_bytes())
    with pytest.raises(ValueError, match="decoding"):
        module.load_decoding_replay(protocol, selected, tmp_path)
