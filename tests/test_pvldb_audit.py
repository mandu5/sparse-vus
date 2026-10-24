import importlib.util
from pathlib import Path

import pytest
import hashlib
import json
import numpy as np
from pvldb_audit_fixture import fixture, write, sha, rebind_inputs


def audit():
    path = Path(__file__).resolve().parents[1] / "experiments/audit_pvldb20261024.py"
    spec = importlib.util.spec_from_file_location("independent_audit", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_coverage_rejects_duplicate_even_when_row_count_matches():
    validate = audit().coverage
    with pytest.raises(ValueError, match="coverage"):
        validate([("a", 1), ("a", 1)], {("a", 1), ("b", 1)})
    validate([("a", 1), ("b", 1)], {("a", 1), ("b", 1)})


def test_scalar_check_rejects_wrong_winners_or_nonfinite_values():
    check = audit().check_values
    assert check([.2, .8], [1], [.2, .8]) == 0
    with pytest.raises(ValueError): check([.2, .8], [0], [.2, .8])
    with pytest.raises(ValueError): check([.2, float("nan")], [1], [.2, .8])
    with pytest.raises(ValueError): check([.2, .8], [1], [.3, .8])


def test_equal_block_weighting_does_not_count_channels_as_independent():
    summarize = audit().block_summary
    # Ten copies of one physical/label group must have the same block estimate
    # as one copy when all their paired effects coincide.
    a = summarize([2., 4.], ["machine_a", "machine_b"])
    b = summarize([2.] * 10 + [4.], ["machine_a"] * 10 + ["machine_b"])
    assert a == b
    assert a["blocks"] == 2
    assert a["geometric_speedup"] == pytest.approx(8 ** .5)


def test_complete_independent_fixture_passes(tmp_path):
    fixture(tmp_path)
    audit().audit(tmp_path, tmp_path / "audit.json")
    assert json.loads((tmp_path/"audit.json").read_text())["status"] == "PASS"


@pytest.mark.parametrize("kind", ["ci", "wins", "tail", "workflow_ratio", "workflow_ci", "workflow_median", "distinct", "extra_method", "extra_collection"])
def test_corrupt_principal_table_is_rejected(tmp_path, kind):
    folder, _ = fixture(tmp_path)
    p = json.loads((folder/"report.json").read_text())
    s = p["case_paired_summaries"]["NAB_L30"]["released"]
    w = p["workflows"]["NAB"]
    if kind == "ci": s["ci95"] = [999., 1000.]
    if kind == "wins": s["case_wins"] = 0
    if kind == "tail": s["minimum_speedup"] = 0.1
    if kind == "workflow_ratio": w["baseline_over_stream"]["released"] = 999.
    if kind == "workflow_ci": w["paired_trial_uncertainty"]["released"]["ci95"] = [99., 100.]
    if kind == "workflow_median": w["median_seconds"]["stream"] = 123.
    if kind == "distinct": p["distinct_values"]["max"] = 999
    if kind == "extra_method": p["case_paired_summaries"]["NAB_L30"]["never_measured"] = {**s, "geometric_speedup": 999.}
    if kind == "extra_collection": p["case_paired_summaries"]["NEVER_MEASURED_L999"] = {"released": s}
    write(folder/"report.json", p)
    with pytest.raises(ValueError): audit().audit(tmp_path, tmp_path/"audit.json")


@pytest.mark.parametrize("kind", ["input_protocol", "start_protocol", "start_inputs", "raw_input", "case_family"])
def test_frozen_cohort_and_run_bindings_are_enforced(tmp_path, kind):
    folder, cache = fixture(tmp_path)
    ip = json.loads((folder/"inputs.json").read_text())
    start = json.loads((folder/"run-start.json").read_text())
    if kind == "input_protocol": ip["protocol_sha256"] = "wrong"
    if kind == "start_protocol": start["protocol_sha256"] = "wrong"
    if kind == "start_inputs": start["inputs_sha256"] = "wrong"
    if kind == "case_family": ip["series"][0]["family"] = "SMAP"
    if kind == "raw_input":
        with np.load(cache/"one.npz") as z: s = z["scores"]
        x = np.array([40., 50., 60.]); y = np.array([1, 0, 0], np.int8)
        np.savez(cache/"one.npz", observations=x, labels=y, scores=s)
        ip["series"][0].update({"npz_sha256": sha(cache/"one.npz"),
            "observation_label_identity": hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest()})
    write(folder/"inputs.json", ip)
    rebind_inputs(folder)
    if kind.startswith("start_"): write(folder/"run-start.json", start)
    with pytest.raises(ValueError): audit().audit(tmp_path, tmp_path/"audit.json")
