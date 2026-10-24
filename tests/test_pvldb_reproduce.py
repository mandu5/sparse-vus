import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "experiments/reproduce_pvldb20261024.py"
    spec = importlib.util.spec_from_file_location("reproduction", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_existing_destination_is_never_reused_or_deleted(tmp_path):
    path = tmp_path / "existing"; path.mkdir(); valuable = path / "keep"; valuable.write_text("unchanged")
    with pytest.raises(FileExistsError): module().prepare_workspace(path)
    assert valuable.read_text() == "unchanged"


def test_reproduction_rejects_changed_cohort_or_model_protocol():
    validate = module().same_design
    reference = {"cases": [{"series": "s1", "raw_sha256": "a"}], "models": ["m1"],
                 "methods": ["method"], "orders": [["method"]], "widths": [30, 100],
                 "primary_width": 30, "parity_atol": 1e-11, "winner_tie_atol": 1e-10,
                 "archive_sha256": "x", "source_sha256": {"kernel": "a"}}
    validate(reference, dict(reference))
    for key, value in [("cases", []), ("models", ["other"]), ("source_sha256", {"kernel": "b"})]:
        changed = {**reference, key: value}
        with pytest.raises(ValueError, match="design drift"): validate(reference, changed)


def test_supplement_design_preserves_every_contract_except_fresh_parent_ids():
    reference = {"created_utc": "old", "primary_protocol_sha256": "old-parent", "inputs_sha256": "old-inputs",
                 "source_sha256": {"supplement": "a"}, "methods": ["stream", "benchopt_pair"],
                 "orders": [["stream", "benchopt_pair"]], "width": 30, "repetitions": 1,
                 "cohort": "all fixed cases", "regret_threshold": .01, "timing": "complete calls",
                 "comparison": "matched output", "uncertainty": "paired", "failure_policy": "halt"}
    actual = {**reference, "created_utc": "new", "primary_protocol_sha256": "new-parent", "inputs_sha256": "new-inputs"}
    check = module().same_supplement_design
    check(reference, actual)
    for key, value in [("source_sha256", {"supplement": "b"}), ("methods", ["stream"]),
                       ("width", 100), ("regret_threshold", .1), ("cohort", "only favorable")]:
        with pytest.raises(ValueError, match="supplement design drift"): check(reference, {**actual, key: value})
