"""Synthetic receipt attacks against the independent evidence auditor."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "experiments/summarize_saturation_evidence.py"
SPEC = importlib.util.spec_from_file_location("independent_saturation_evidence", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def records():
    models = ["control_score"]
    protocol = {"version": 1, "phase": "external", "cases": 6, "series": 2,
                "families": ["f1", "f2"], "models": models, "widths": [30, 100, 300],
                "primary_width": 30, "repetitions": 3, "seed": 2026102113,
                "method_ids": list(AUDIT.METHODS), "parity_atol": 1e-11,
                "bootstrap": {"unit": "family", "repetitions": 2000, "seed": 2026102114, "confidence": .95},
                "source_sha256": {"test-source.py": "a" * 64}, "source_commit": "synthetic",
                "history": "Synthetic audit fixture; not a measured research outcome.",
                "decision": "All lower family-bootstrap bounds above one at L=30."}
    inputs, rows = [], []
    rng = random.Random(protocol["seed"])
    for width in (30, 100, 300):
        for series, family, control_time, k in (("s1", "f1", 2., 1), ("s2", "f2", .5, 2)):
            identity = {"series": series, "family": family, "model": models[0], "n": 10,
                        "positive_points": 2, "max_buffer": width, "label_member_sha256": "b" * 64,
                        "score_member_sha256": "c" * 64, "case_id": f"{series}|{models[0]}|{width}"}
            methods = {}
            for name in AUDIT.METHODS:
                median = 1. if name == "saturation" else control_time
                methods[name] = {"seconds": [.9 * median, median, 1.1 * median], "values": [.5, .5, .5]}
            orders = []
            for _ in range(3):
                order = list(AUDIT.METHODS)
                rng.shuffle(order)
                orders.append(order)
            active = [2] + [4] * width
            profiles = {name: {"Q": 4, "K": k, "active": active.copy(),
                              "visited": [2] * (width + 1) if name == "saturation" else active.copy(),
                              "values": {"roc": .6, "pr": .5}} for name in AUDIT.PROFILE_MODES}
            inputs.append(identity)
            rows.append({**deepcopy(identity), "methods": methods, "orders": orders, "profiles": profiles})
    return rows, protocol, inputs


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def fixture_folder(path):
    rows, protocol, inputs = records()
    path.mkdir()
    write_json(path / "inputs.json", inputs)
    protocol["inputs_sha256"] = AUDIT.sha(path / "inputs.json")
    write_json(path / "protocol.json", protocol)
    (path / "measurements.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    binding = {"protocol_sha256": AUDIT.sha(path / "protocol.json"), "source_sha256": protocol["source_sha256"]}
    write_json(path / "run-start.json", binding)
    write_json(path / "completion.json", {**binding, "status": "COMPLETED", "cases": 6,
               "measurements_sha256": AUDIT.sha(path / "measurements.jsonl")})
    # Hand-specified statistics: half of cases have ratio 2, half ratio 1/2.
    comparison = {"median_ratio": 1.25, "geomean_ratio": 1., "aggregate_ratio": 1.25,
                  "wins": 1, "losses": 1, "ties": 0, "minimum_ratio": .5,
                  "candidate_seconds_sum": 2., "reference_seconds_sum": 2.5,
                  "geomean_ci95": [.5, 2.], "aggregate_ci95": [.5, 2.]}
    report = {"cases": 6, "parity_pass": True, "max_absolute_error": 0., "primary_decision": False,
              "phase": "external", "scope": protocol["history"],
              "protocol_sha256": binding["protocol_sha256"], "inputs_sha256": protocol["inputs_sha256"],
              "measurements_sha256": AUDIT.sha(path / "measurements.jsonl"),
              "widths": {str(width): {"cases": 2, "families": ["f1", "f2"],
                          "comparisons": {name: deepcopy(comparison) for name in AUDIT.CONTROLS}}
                         for width in (30, 100, 300)}}
    write_json(path / "report.json", report)
    return path


def test_independent_valid_receipts_keep_losses_and_failed_primary(tmp_path):
    study = AUDIT.audit_study("tiny", fixture_folder(tmp_path / "study"))
    assert study["audit_status"] == "PASS_RECORDED_EVIDENCE"
    assert study["primary_decision"] is False
    for width in (30, 100, 300):
        part = study["widths"][str(width)]
        oracle = part["fastest_eight_control_oracle"]
        assert oracle["loss_case_ids"] == [f"s2|control_score|{width}"]
        assert oracle["wins"] == oracle["losses"] == 1
        assert oracle["minimum_ratio"] == .5
        assert part["K1_cases"] == part["K1_unique_series"] == 1
        assert part["work"]["maximum_over_saturation"]["median_ratio"] == 2.
        assert part["work"]["active_full_over_saturation"]["median_ratio"] == pytest.approx((2 + 4 * width) / (2 * (width + 1)))
    rendered = AUDIT.markdown([study])
    assert "criterion: **FAIL**" in rendered
    assert "s2|control_score|300" in rendered


def test_raw_tampering_rejected_before_statistics(tmp_path):
    path = fixture_folder(tmp_path / "study")
    with (path / "measurements.jsonl").open("a") as stream:
        stream.write("{}\n")
    with pytest.raises(ValueError, match="Raw measurement hash mismatch"):
        AUDIT.audit_study("tampered", path)


@pytest.mark.parametrize("field", ["protocol", "inputs", "completion", "start", "report"])
def test_receipt_chain_attacks(tmp_path, field):
    path = fixture_folder(tmp_path / "study")
    filename = {"start": "run-start.json"}.get(field, field + ".json")
    value = AUDIT.load_json(path / filename)
    if field == "protocol":
        value["seed"] += 1
    elif field == "inputs":
        value[0]["positive_points"] += 1
    elif field == "completion":
        value["status"] = "RUNNING"
    elif field == "start":
        value["source_sha256"] = {"different.py": "d" * 64}
    else:
        value["widths"]["30"]["comparisons"]["radix"]["aggregate_ratio"] = 100.
    write_json(path / filename, value)
    with pytest.raises(ValueError):
        AUDIT.audit_study("false", path)


@pytest.mark.parametrize("attack", ["coverage", "duplicate", "method", "repetition", "duration", "parity", "order", "work", "identity"])
def test_reject_plausibly_rehashed_but_invalid_measurements(attack):
    rows, protocol, inputs = records()
    if attack == "coverage":
        rows.pop()
        inputs.pop()
        protocol["cases"] -= 1  # Matching headline counts cannot conceal one omitted case.
    elif attack == "duplicate":
        rows[-1], inputs[-1] = deepcopy(rows[-2]), deepcopy(inputs[-2])
    elif attack == "method":
        del rows[0]["methods"]["klein"]
    elif attack == "repetition":
        rows[0]["methods"]["saturation"]["seconds"].pop()
    elif attack == "duration":
        rows[0]["methods"]["radix"]["seconds"][0] = 0.
    elif attack == "parity":
        rows[0]["methods"]["radix"]["values"][1] += 1e-4
    elif attack == "order":
        rows[0]["orders"][0] = list(AUDIT.METHODS)
    elif attack == "work":
        rows[0]["profiles"]["saturation"]["visited"][1] = 5
    else:
        rows[0]["score_member_sha256"] = "f" * 64
    with pytest.raises(ValueError):
        AUDIT.audit_records(rows, protocol, inputs)


def test_false_primary_pass_rejected(tmp_path):
    path = fixture_folder(tmp_path / "study")
    report = AUDIT.load_json(path / "report.json")
    report["primary_decision"] = True
    write_json(path / "report.json", report)
    with pytest.raises(ValueError, match="primary decision"):
        AUDIT.audit_study("false-pass", path)


@pytest.mark.parametrize("text", ['{"x": 1, "x": 2}', '{"x": NaN}', '{"x": Infinity}'])
def test_ambiguous_or_nonfinite_json_rejected(text):
    with pytest.raises(ValueError):
        AUDIT.parse_json(text)


def test_no_benchmark_or_kernel_dependency():
    # The auditor must stay usable without compiling/loading the measured implementation.
    import ast
    tree = ast.parse(SCRIPT.read_text())
    imported = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imported += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    assert not any(name.startswith(("benchmark_saturation", "sparse_vus", "numba")) for name in imported)
