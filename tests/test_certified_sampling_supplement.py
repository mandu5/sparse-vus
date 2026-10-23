"""Transport-only anonymization must preserve scientific evidence and source."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

import pytest

PATH = Path(__file__).resolve().parents[1]/"experiments/build_certified_sampling_supplement.py"
SPEC = importlib.util.spec_from_file_location("certified_supplement_tests", PATH)
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fixture_files():
    source = b'"""Frozen scientific source."""\nvalue = 0.125\n'
    metadata = b'{"hardware":{"node":"private-machine.local","machine":"arm64"},"value":0.125000,"count":3}\n'
    records = (json.dumps({"source_manifest_sha256": digest(metadata),
                           "value": .125, "lower_numerator": "12345678901234567890"})+'\n').encode()
    report = (json.dumps({"records_sha256": digest(records), "value": .125})+'\n').encode()
    return {"src/science.py": source, "artifacts/main/source_manifest.json": metadata,
            "artifacts/main/records.jsonl": records,
            "artifacts/main/report-"+digest(records)[:16]+".json": report,
            "experiments/audit_certified_sampling_bundle.py":
                ("ANCHORS = {'records': '"+digest(records)+"'}\nvalue = 0.125\n").encode()}


def test_hostname_scrub_preserves_numbers_and_integer_strings():
    original = fixture_files()["artifacts/main/source_manifest.json"]
    clean, changes = builder.anonymize_metadata("artifacts/main/source_manifest.json", original)
    assert b"private-machine" not in clean
    assert b'"value":0.125000' in clean
    assert json.loads(clean)["hardware"]["machine"] == "arm64"
    assert changes["machine_hostname"] == 1


def test_identifying_scientific_code_is_rejected_instead_of_rewritten():
    with pytest.raises(ValueError, match="Scientific source"):
        builder.anonymize_metadata("src/science.py", b'PATH = "/Users/gosmain/private"\n')


def test_hash_rebinding_preserves_sources_and_integer_endpoints():
    original = fixture_files()
    payload, entries = builder.make_payload(original)
    metadata = payload["artifacts/main/source_manifest.json"]
    records = payload["artifacts/main/records.jsonl"]
    report_path = "artifacts/main/report-"+digest(records)[:16]+".json"
    assert digest(metadata) == json.loads(records)["source_manifest_sha256"]
    assert digest(records) == json.loads(payload[report_path])["records_sha256"]
    assert json.loads(records)["lower_numerator"] == "12345678901234567890"
    assert payload["src/science.py"] == original["src/science.py"]
    name = "experiments/audit_certified_sampling_bundle.py"
    assert payload[name] == original[name]
    derived = payload[builder.DERIVED_AUDITOR]
    assert digest(records).encode() in derived
    assert entries[builder.DERIVED_AUDITOR]["transformation"] == "sha256_string_literals_only"
    assert all(v["nontext_json_equal"] is True for k,v in entries.items() if k.endswith((".json", ".jsonl")))


def test_auditor_derivation_changes_only_whole_string_hash_literals():
    old, new = "a"*64, "b"*64
    source = (f"# {old}\nHASH = '{old}'\nPATH = 'prefix/{old}'\nvalue = 1\n").encode()
    derived = builder.derive_auditor(source, {old:new})
    assert derived == source.replace(f"HASH = '{old}'".encode(), f"HASH = '{new}'".encode())
    assert ast.parse(derived).body[-1].value.value == 1


def test_numeric_and_structural_mutation_is_rejected():
    with pytest.raises(ValueError, match="numeric|structural"):
        builder.assert_nontext_equal("x.json", b'{"count":1}', b'{"count":2}')
    with pytest.raises(ValueError, match="numeric|structural"):
        builder.assert_nontext_equal("x.jsonl", b'{"count":1}\n', b'{"other":1}\n')
    with pytest.raises(ValueError, match="numeric"):
        builder.assert_nontext_equal("x.json", b'{"endpoint":"12345"}', b'{"endpoint":"12346"}')
    with pytest.raises(ValueError, match="lexical"):
        builder.assert_nontext_equal("x.json", b'{"count":0.125000}', b'{"count":0.125}')


def test_zip_roundtrip_has_manifest_and_leaves_originals_unchanged(tmp_path):
    files = fixture_files()
    for name,data in files.items():
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    target = tmp_path/"paper/supplement.zip"
    result = builder.build_supplement(tmp_path, target, inputs=files)
    assert result["sha256"] == digest(target.read_bytes())
    with zipfile.ZipFile(target) as archive:
        manifest = json.loads(archive.read("ANONYMIZATION_MANIFEST.json"))
        for entry in manifest["files"]:
            assert digest(archive.read(entry["path"])) == entry["anonymous_sha256"]
        assert b"private-machine" not in b"".join(archive.read(n) for n in archive.namelist())
    assert all((tmp_path/name).read_bytes() == data for name,data in files.items())
    with pytest.raises(FileExistsError):
        builder.build_supplement(tmp_path, target, inputs=files)


def test_file_selection_is_explicit_and_checks_bound_dependency_hash(tmp_path):
    source = tmp_path/"src/science.py"
    source.parent.mkdir(); source.write_bytes(b"value = 1\n")
    audit = tmp_path/builder.AUDIT_RECEIPT
    audit.parent.mkdir(parents=True)
    audit.write_text(json.dumps({"verified_repository_sha256":{"src/science.py":digest(source.read_bytes())}}))
    (tmp_path/"private.txt").write_text("must not be selected")
    assert builder.select_inputs(tmp_path, extra=(), include_corpus_closure=False) == {"src/science.py":source.read_bytes()}
    source.write_bytes(b"value = 2\n")
    with pytest.raises(ValueError, match="Frozen dependency"):
        builder.select_inputs(tmp_path, extra=(), include_corpus_closure=False)


def test_unsafe_archive_paths_and_symlinks_fail(tmp_path):
    with pytest.raises(ValueError, match="Unsafe"):
        builder.make_payload({"../outside.json":b"{}"})
    outside = tmp_path/"outside.py"; outside.write_text("value=1\n")
    link = tmp_path/"link.py"; link.symlink_to(outside)
    audit = tmp_path/builder.AUDIT_RECEIPT
    audit.parent.mkdir(parents=True)
    audit.write_text(json.dumps({"verified_repository_sha256":{"link.py":digest(link.read_bytes())}}))
    with pytest.raises(ValueError, match="Symlink"):
        builder.select_inputs(tmp_path, extra=(), include_corpus_closure=False)
