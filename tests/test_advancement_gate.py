"""Reject materially false PASS artifacts, including self-consistent rehashes.

All inputs are tiny synthetic fixtures. No released ZIP, model inference,
benchmark kernel, network request, or real corpus scan is used.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
sys.path.insert(0, str(EXPERIMENTS))


def load_script(name):
    spec = importlib.util.spec_from_file_location(f"audit_test_{name}", EXPERIMENTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyzer = load_script("analyze_advancement")
data_gate = load_script("advancement_data_gate")


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def make_row(model, pr, mode="baseline", width=30):
    exact = [0.8, pr]
    if mode == "baseline":
        values = {
            "sparse_exact": exact,
            "fast_vus_exact_pr": [None, pr],
            "dense_direct": exact.copy(),
            "dense_nearest": exact.copy(),
            "dense_numpy": exact.copy(),
        }
        checks = {name: {"max_error": 0.0} for name in values if name != "sparse_exact"}
    else:
        values = {"sparse_exact": exact}
        checks = {}
        for tolerance in ("0.01", "0.001"):
            # Exactly represented singleton intervals make valid fixture
            # midpoint/error values independent of the integration algorithm.
            name = f"certified_{tolerance}"
            values[name] = {
                "roc_lower": 0.8, "roc_upper": 0.8,
                "pr_lower": pr, "pr_upper": pr,
                "estimate": exact.copy(), "exact": False,
                "evaluated_widths": [0, width], "total_widths": width + 1,
                "curve_evaluations": 2,
            }
            checks[name] = {"contains_exact": True, "half_width": 0.0, "max_midpoint_error": 0.0}
    return {
        "series": "independent_fixture", "family": "fixture", "model": model,
        "n": 4, "max_buffer": width, "values": values, "checks": checks,
        "seconds": {name: [0.01, 0.02, 0.03] for name in values},
        "median_seconds": {name: 0.02 for name in values},
        "label_sha256": "a" * 64, "score_sha256": model.lower() * 64,
    }


def write_run(path, rows, *, mode="baseline", platform="macOS-test", machine="arm64"):
    path.mkdir(parents=True)
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    (path / "measurements.jsonl").write_bytes(raw)
    keys = [(r["series"], r["model"], r["max_buffer"]) for r in rows]
    protocol = {
        "mode": mode, "repetitions": 3, "cases": len(rows),
        "selection_sha256": sha_bytes(json.dumps(keys, separators=(",", ":")).encode()),
        "exact_parity_tolerance": 1e-11,
        "float64_containment_tolerance": 1e-10,
    }
    write_json(path / "protocol.json", protocol)
    # ROOT is replaced by the fixture, so these are the only source bytes read.
    source = path.parent / "fixture_source.py"
    source.write_text("FIXTURE = 'bound source, not a metric implementation'\n")
    hashes = {"fixture_source.py": sha_bytes(source.read_bytes())}
    required = ["experiments/benchmark_advancement.py",
                "src/sparse_vus/core.py", "src/sparse_vus/compiled.py"]
    required += (["experiments/fast_vus_adapter.py", ".cache/fast_vus/fast_vus.py"]
                 if mode == "baseline" else ["src/sparse_vus/certified.py"])
    for name in required:
        target = path.parent / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        hashes[name] = sha_bytes(target.read_bytes())
    write_json(path / "environment.json", {
        "platform": platform, "machine": machine,
        "protocol_sha256": sha_bytes((path / "protocol.json").read_bytes()),
        "source_sha256": hashes,
    })
    write_json(path / "summary.json", {
        "status": "PASS", "cases": len(rows), "measurements_sha256": sha_bytes(raw),
    })
    return path


def rehash_results(path, rows, *, update_count=True):
    """Simulate a false record whose transport/receipt hash is fully valid."""
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    (path / "measurements.jsonl").write_bytes(raw)
    summary = json.loads((path / "summary.json").read_text())
    summary["measurements_sha256"] = sha_bytes(raw)
    if update_count:
        summary["cases"] = len(rows)
    write_json(path / "summary.json", summary)


@pytest.fixture
def run_factory(tmp_path, monkeypatch):
    monkeypatch.setattr(analyzer, "ROOT", tmp_path)
    # Corpus membership is exercised separately below with synthetic archives.
    # Keep numerical artifact tests independent of the real release corpus.
    monkeypatch.setattr(analyzer, "validate_advancement_data",
                        lambda *args, **kwargs: {"status": "PASS"}, raising=False)

    def create(mode="baseline"):
        rows = [make_row(model, pr, mode) for model, pr in (("A", .5), ("B", .4), ("C", .1))]
        return write_run(tmp_path / mode, rows, mode=mode), rows
    return create


@pytest.mark.parametrize("mode", ["baseline", "certified"])
def test_valid_independently_constructed_run_is_accepted(run_factory, mode):
    path, rows = run_factory(mode)
    accepted, summary = analyzer.read_run(path)
    assert accepted == rows
    assert summary["status"] == "PASS"


def test_rehashed_pass_cannot_hide_external_exact_parity_failure(run_factory):
    path, rows = run_factory()
    rows[0]["values"]["fast_vus_exact_pr"][1] = .9
    rows[0]["checks"]["fast_vus_exact_pr"]["max_error"] = 0.0
    rehash_results(path, rows)
    with pytest.raises(ValueError, match="parity"):
        analyzer.read_run(path)


def test_rehashed_pass_cannot_hide_noncontaining_interval(run_factory):
    path, rows = run_factory("certified")
    value = rows[0]["values"]["certified_0.001"]
    value.update(pr_lower=.7, pr_upper=.7, estimate=[.8, .7])
    # Leave the producer's false success/check fields untouched.
    rehash_results(path, rows)
    with pytest.raises(ValueError, match="excludes exact"):
        analyzer.read_run(path)


@pytest.mark.parametrize("kind", ["reversed", "nonfinite", "too_wide", "false_midpoint", "false_width_count"])
def test_rehashed_certification_contract_failures_are_rejected(run_factory, kind):
    path, rows = run_factory("certified")
    value = rows[0]["values"]["certified_0.001"]
    if kind == "reversed":
        value.update(pr_lower=.50000000001, pr_upper=.49999999999)
    elif kind == "nonfinite":
        value["roc_upper"] = float("inf")
    elif kind == "too_wide":
        value.update(pr_lower=.4, pr_upper=.6)
    elif kind == "false_midpoint":
        value["estimate"] = [.8, .9]
    else:
        value["total_widths"] = 999
    rehash_results(path, rows)
    with pytest.raises(ValueError):
        analyzer.read_run(path)


def test_protocol_edit_without_environment_rebinding_is_rejected(run_factory):
    path, _ = run_factory()
    protocol = json.loads((path / "protocol.json").read_text())
    protocol["exact_parity_tolerance"] = 1.0
    write_json(path / "protocol.json", protocol)
    with pytest.raises(ValueError, match="protocol/environment"):
        analyzer.read_run(path)


def test_changed_measured_source_is_rejected(run_factory):
    path, _ = run_factory()
    (path.parent / "fixture_source.py").write_text("FIXTURE = 'different code'\n")
    with pytest.raises(ValueError, match="source differs"):
        analyzer.read_run(path)


@pytest.mark.parametrize("mode", ["baseline", "certified"])
def test_omitting_required_source_binding_is_rejected(run_factory, mode):
    path, _ = run_factory(mode)
    environment = json.loads((path / "environment.json").read_text())
    environment["source_sha256"].pop("src/sparse_vus/compiled.py")
    write_json(path / "environment.json", environment)
    with pytest.raises(ValueError, match="missing required measured source"):
        analyzer.read_run(path)


@pytest.mark.parametrize("kind", ["missing", "duplicate"])
def test_rehashing_does_not_legalize_changed_case_coverage(run_factory, kind):
    path, rows = run_factory()
    changed = rows[:-1] if kind == "missing" else rows + [deepcopy(rows[0])]
    rehash_results(path, changed)
    with pytest.raises(ValueError, match="selection mismatch|duplicate case"):
        analyzer.read_run(path)


def test_rehashing_does_not_legalize_omitted_competitor(run_factory):
    path, rows = run_factory()
    for key in ("seconds", "median_seconds", "values"):
        del rows[0][key]["fast_vus_exact_pr"]
    rehash_results(path, rows)
    with pytest.raises(ValueError, match="method coverage"):
        analyzer.read_run(path)


@pytest.mark.parametrize("bad_calls", [
    [0.0, .02, .03], [-1.0, .02, .03],
    [float("nan"), .02, .03], [float("inf"), .02, .03], [.01, .02],
])
def test_invalid_durations_cannot_enter_speed_ratios(run_factory, bad_calls):
    path, rows = run_factory()
    rows[0]["seconds"]["sparse_exact"] = bad_calls
    rehash_results(path, rows)
    with pytest.raises(ValueError, match="invalid timing"):
        analyzer.read_run(path)


def test_forged_fast_median_is_rejected_even_when_durations_are_valid(run_factory):
    path, rows = run_factory()
    rows[0]["median_seconds"]["sparse_exact"] = .000001
    rehash_results(path, rows)
    with pytest.raises(ValueError, match="median mismatch"):
        analyzer.read_run(path)


def test_numeric_margin_abstains_on_two_containment_allowances():
    rows = [
        make_row("A", .50000000001, "certified"),
        make_row("B", .5, "certified"),
        make_row("C", .1, "certified"),
    ]
    method = "certified_0.001"
    for row, bound in zip(rows, [.49999999992, .50000000008, .1]):
        row["values"][method].update(pr_lower=bound, pr_upper=bound)
    result = analyzer.certify_rankings(rows, method)
    # A/B have reversed rounded intervals within two allowed numerical errors.
    # Both are clearly above C, so abstaining on every pair is also incorrect.
    assert result["model_pairs"] == 3
    assert result["certified_pairs"] == 2
    assert result["certified_unique_winners"] == 0
    assert result["incorrect_certified_pairs"] == result["incorrect_certified_winners"] == 0


def test_disjoint_intervals_produce_three_pairs_and_one_winner():
    rows = [make_row(m, p, "certified") for m, p in (("A", .9), ("B", .6), ("C", .1))]
    result = analyzer.certify_rankings(rows, "certified_0.001")
    assert result["certified_pairs"] == 3
    assert result["certified_unique_winners"] == 1
    assert result["incorrect_certified_pairs"] == result["incorrect_certified_winners"] == 0


def test_aggregate_report_rejects_its_own_wrong_decision_count(tmp_path, monkeypatch):
    import advancement_data_gate as runtime_data_gate

    baseline = [make_row(m, p) for m, p in (("A", .9), ("B", .6), ("C", .1))]
    certified = [make_row(m, p, "certified") for m, p in (("A", .9), ("B", .6), ("C", .1))]
    mac = write_run(tmp_path / "mac", baseline)
    linux = write_run(tmp_path / "linux", baseline, platform="Linux-test", machine="x86_64")
    cert = write_run(tmp_path / "cert", certified, mode="certified")
    output = tmp_path / "report"
    monkeypatch.setattr(analyzer, "ROOT", tmp_path)
    # Isolate the final status gate: upstream artifact checks have separate tests.
    monkeypatch.setattr(analyzer, "read_run", lambda path: (
        certified if path == cert else baseline, {"measurements_sha256": "fixture"}))
    monkeypatch.setattr(analyzer, "ratio_stats", lambda *args: {})
    monkeypatch.setattr(analyzer, "certify_rankings", lambda *args: {
        "incorrect_certified_pairs": 1, "incorrect_certified_winners": 0})
    monkeypatch.setattr(analyzer, "validate_advancement_data", lambda *args, **kwargs: {"status": "PASS"},
                        raising=False)
    # main imports this function locally; patch its actual import source too.
    monkeypatch.setattr(runtime_data_gate, "validate_advancement_data",
                        lambda *args, **kwargs: {"status": "PASS"})
    monkeypatch.setattr(sys, "argv", [
        "analyze_advancement.py", "--mac-baseline", str(mac), "--linux-baseline", str(linux),
        "--certified", str(cert), "--output", str(output),
    ])
    with pytest.raises(ValueError, match="false certified decision"):
        analyzer.main()
    assert not (output / "analysis.json").exists()


def npy_bytes(values):
    buffer = io.BytesIO()
    np.save(buffer, np.asarray(values, dtype=float), allow_pickle=False)
    return buffer.getvalue()


@pytest.fixture
def tiny_archive_corpus(tmp_path, monkeypatch):
    """An independent four-point dataset; never opens a real benchmark ZIP."""
    cache = tmp_path / "cache"
    cache.mkdir()
    label_bytes = b"signal,Label\n1,0\n3,1\n2,0\n4,0\n"
    with zipfile.ZipFile(cache / "TSB-AD-U.zip", "w") as archive:
        archive.writestr("data/tiny.csv", label_bytes)
    metadata = {"tiny": {"n": 4, "family": "synthetic", "positive_points": 1,
                          "label_sha256": sha_bytes(label_bytes)}}
    models = ["A", "B", "C"]
    scores, score_hashes = {}, {}
    for index, model in enumerate(models):
        scores[model] = npy_bytes([index, index + 1, index + 3, index + 2])
        with zipfile.ZipFile(cache / f"{model}.score-range.zip", "w") as archive:
            archive.writestr("scores/tiny.npy", scores[model])
        score_hashes["tiny", model] = sha_bytes(scores[model])
    locks = {"files": {"TSB-AD-U.zip": sha_bytes((cache / "TSB-AD-U.zip").read_bytes())}}
    receipt = {"records_sha256": "a" * 64}
    # Isolate actual-member checks from the separately tested immutable anchor.
    monkeypatch.setattr(data_gate, "released_metadata",
                        lambda root: (metadata, models, score_hashes, ["tiny"], locks, receipt))
    rows = [{"series": "tiny", "model": model, "max_buffer": width, "n": 4,
             "family": "synthetic", "label_sha256": metadata["tiny"]["label_sha256"],
             "score_sha256": score_hashes["tiny", model]}
            for model, width in itertools.product(models, (10, 30))]
    return tmp_path, rows, metadata, score_hashes, locks


def test_data_gate_accepts_tiny_actual_archive_members(tiny_archive_corpus):
    root, rows, *_ = tiny_archive_corpus
    result = data_gate.validate_advancement_data(rows, mode="baseline", root=root)
    assert result["status"] == "PASS"
    assert result["actual_label_members_verified"] == 1
    assert result["actual_score_members_verified"] == 3
    assert result["measurement_rows"] == 6
    assert result["whole_score_archive_md5_verified"] is False


@pytest.mark.parametrize("kind", ["missing", "duplicate", "wrong_mode"])
def test_data_gate_rejects_selective_measurement_coverage(tiny_archive_corpus, kind):
    root, rows, *_ = tiny_archive_corpus
    mode = "baseline"
    if kind == "missing":
        rows = rows[:-1]
    elif kind == "duplicate":
        rows.append(deepcopy(rows[0]))
    else:
        mode = "certified"
    with pytest.raises(ValueError, match="case set"):
        data_gate.validate_advancement_data(rows, mode=mode, root=root)


@pytest.mark.parametrize("field,value", [
    ("n", 500), ("family", "misattributed"), ("label_sha256", "0" * 64),
    ("score_sha256", "0" * 64),
])
def test_data_gate_rejects_wrong_per_row_provenance(tiny_archive_corpus, field, value):
    root, rows, *_ = tiny_archive_corpus
    rows[0][field] = value
    with pytest.raises(ValueError, match="Recorded"):
        data_gate.validate_advancement_data(rows, mode="baseline", root=root)


def test_changed_score_with_valid_new_zip_crc_is_rejected(tiny_archive_corpus):
    root, rows, *_ = tiny_archive_corpus
    # Rewriting the ZIP recomputes a valid CRC; only the original SHA lock
    # distinguishes it from the claimed score input.
    with zipfile.ZipFile(root / "cache/A.score-range.zip", "w") as archive:
        archive.writestr("scores/tiny.npy", npy_bytes([99, 1, 3, 2]))
    with pytest.raises(ValueError, match="Actual score member changed"):
        data_gate.validate_advancement_data(rows, mode="baseline", root=root)


def test_rehashed_label_archive_cannot_hide_changed_label_member(tiny_archive_corpus):
    root, rows, _, _, locks = tiny_archive_corpus
    path = root / "cache/TSB-AD-U.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("data/tiny.csv", b"signal,Label\n1,1\n3,0\n2,0\n4,0\n")
    locks["files"]["TSB-AD-U.zip"] = sha_bytes(path.read_bytes())
    with pytest.raises(ValueError, match="Actual label member changed"):
        data_gate.validate_advancement_data(rows, mode="baseline", root=root)


def test_hash_consistent_nonfinite_score_is_still_invalid(tiny_archive_corpus):
    root, rows, _, hashes, _ = tiny_archive_corpus
    raw = npy_bytes([0, float("nan"), 3, 2])
    with zipfile.ZipFile(root / "cache/A.score-range.zip", "w") as archive:
        archive.writestr("scores/tiny.npy", raw)
    hashes["tiny", "A"] = sha_bytes(raw)
    for row in rows:
        if row["model"] == "A":
            row["score_sha256"] = hashes["tiny", "A"]
    with pytest.raises(ValueError, match="shape/finite"):
        data_gate.validate_advancement_data(rows, mode="baseline", root=root)


def test_changed_release_anchor_is_rejected_before_reading_any_archive(tmp_path, monkeypatch):
    path = tmp_path / "experiments/data_hashes.json"
    path.parent.mkdir()
    original = b'{"fixture": "immutable anchor"}\n'
    path.write_bytes(original)
    monkeypatch.setattr(data_gate, "RELEASE_BINDINGS", {
        "experiments/data_hashes.json": sha_bytes(original),
    })
    path.write_bytes(b'{"fixture": "replacement anchor"}\n')
    with pytest.raises(ValueError, match="Release binding mismatch"):
        data_gate.released_metadata(tmp_path)


def test_rehashed_original_records_still_require_pinned_receipt(tmp_path, monkeypatch):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    original = b'{"series": "original"}\n'
    receipt = artifacts / "public_benchmark_receipt.json"
    write_json(receipt, {"records_sha256": sha_bytes(original)})
    monkeypatch.setattr(data_gate, "RELEASE_BINDINGS", {
        "artifacts/public_benchmark_receipt.json": sha_bytes(receipt.read_bytes()),
    })
    (artifacts / "public_benchmark.jsonl").write_bytes(b'{"series": "selected replacement"}\n')
    with pytest.raises(ValueError, match="Original benchmark differs"):
        data_gate.released_metadata(tmp_path)
