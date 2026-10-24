"""Small archived-curve fixtures for the descriptive post-hoc tie auditor."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
import pytest


def auditor():
    path = Path(__file__).resolve().parents[1] / "experiments/audit_weighted_ties.py"
    spec = importlib.util.spec_from_file_location("weighted_tie_auditor", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, allow_nan=False) + "\n")


def fixture_archive(path):
    path.mkdir()
    (path / "curves").mkdir()
    protocol = {
        "status": "FROZEN_BEFORE_WEIGHTED_METRIC_TIMINGS", "utc": "2026-10-24T00:00:00+00:00",
        "model_order": ["FFT", "COPOD"], "cases": [{"id": "case", "family": "toy", "n": 4}],
        "biases": ["flat"], "cardinalities": ["one"],
        "queries": {"grid100": "strict > grid", "distinct": "strict > observed scores"},
        "orders": [list(order) for order in itertools.permutations(["raster", "interval", "incremental"])],
        "winner_atol": 1e-10, "parity_atol": 1e-10,
    }
    write_json(path / "protocol.json", protocol)
    records = []
    for query, values in (("grid100", [0.5, 0.5]), ("distinct", [0.9, 0.7])):
        count = 100 if query == "grid100" else 3
        arrays = [np.tile([0.5, 0.5, value], (count, 1)) for value in values]
        h = hashlib.sha256()
        for array in arrays:
            h.update(array.tobytes())
        for method in protocol["orders"][0]:
            relative = "curves/" + query + "-" + method + ".npz"
            np.savez_compressed(path / relative, **{f"flat_one_{i}": a for i, a in enumerate(arrays)})
            for trial in range(len(protocol["orders"])):
                records.append({
                    "id": "case", "family": "toy", "n": 4, "query": query,
                    "bias": "flat", "cardinality": "one", "trial": trial, "method": method,
                    "seconds": 0.001, "max_curve_error": 0.0, "query_counts": [count, count],
                    "values": values, "winners": [0, 1] if query == "grid100" else [0],
                    "output_sha256": h.hexdigest(), "curve_file": relative,
                    "curve_file_sha256": sha(path / relative),
                })
    bind_records(path, records)
    return records


def bind_records(path, records):
    (path / "records.jsonl").write_text("".join(json.dumps(r, allow_nan=False) + "\n" for r in records))
    write_json(path / "complete.json", {
        "status": "COMPLETE", "utc": "2026-10-24T00:01:00+00:00",
        "protocol_sha256": sha(path / "protocol.json"), "records_sha256": sha(path / "records.jsonl"),
    })


def test_best_and_worst_regret_differ_for_tolerance_based_grid_ties():
    module = auditor()
    detail = module.tie_detail([0.5, 0.5 - 5e-11], [0.9, 0.7], 1e-10)
    assert detail["grid_winners"] == [0, 1]
    assert detail["best_grid_winner_regret"] == 0.0
    assert detail["worst_grid_winner_regret"] == pytest.approx(0.2)
    assert detail["nonoverlap"] is False


def test_valid_archive_reconstructs_extrema_and_discloses_post_hoc_scope(tmp_path):
    path = tmp_path / "archive"
    fixture_archive(path)
    result = auditor().audit(path, sha(path / "complete.json"))
    assert result["analysis_phase"] == "DESCRIPTIVE_POST_HOC_TIE_SENSITIVITY"
    assert result["metric_evaluation_performed"] is False
    assert result["local_input_bytes_verified"] is False
    assert result["records_verified"] == 36
    row = result["grid_to_distinct_tie_sensitivity"][0]
    assert row["best_regret_ge_01"] == 0 and row["worst_regret_ge_01"] == 1
    assert row["max_best_regret"] == 0.0
    assert row["max_worst_regret"] == pytest.approx(0.2)
    text = auditor().render_markdown(result)
    assert "post-hoc" in text and "Worst" in text and "0.2" in text


def test_complete_file_requires_the_supplied_external_identity(tmp_path):
    path = tmp_path / "archive"
    fixture_archive(path)
    with pytest.raises(ValueError, match="complete.*identity"):
        auditor().audit(path, "0" * 64)


@pytest.mark.parametrize("tamper", ["missing", "duplicate", "repeat_value", "winner"])
def test_rebound_archive_still_rejects_incomplete_or_inconsistent_records(tmp_path, tamper):
    path = tmp_path / "archive"
    records = fixture_archive(path)
    if tamper == "missing":
        records.pop()
    elif tamper == "duplicate":
        records.append(dict(records[0]))
    elif tamper == "repeat_value":
        records[1] = {**records[1], "values": [0.51, 0.5]}
    else:
        records[0] = {**records[0], "winners": [0]}
    bind_records(path, records)
    with pytest.raises(ValueError):
        auditor().audit(path, sha(path / "complete.json"))


def test_changed_curve_cannot_hide_behind_rebound_file_hashes(tmp_path):
    path = tmp_path / "archive"
    records = fixture_archive(path)
    relative = records[0]["curve_file"]
    changed = np.tile([0.5, 0.5, 0.51], (100, 1))
    other = np.tile([0.5, 0.5, 0.5], (100, 1))
    np.savez_compressed(path / relative, flat_one_0=changed, flat_one_1=other)
    h = hashlib.sha256(changed.tobytes() + other.tobytes()).hexdigest()
    for record in records:
        if record["curve_file"] == relative:
            record["curve_file_sha256"] = sha(path / relative)
            record["output_sha256"] = h
    bind_records(path, records)
    with pytest.raises(ValueError, match="saved.*maximum|curve parity"):
        auditor().audit(path, sha(path / "complete.json"))
