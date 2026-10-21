"""Validation-only fixtures: no figures or benchmark outcomes are generated."""
from copy import deepcopy
import importlib
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))


def fixture():
    eligible = ["sparse_pr", "dense_pr_direct", "klein_pr", "dense_pr_direct_radix", "dense_pr_nearest_radix"]
    groups = {"combined_30_100": {"cases": 616}}
    for width in (30, 100, 300):
        records = [{"series": f"s{i:03}", "family": f"f{i % 23}", "max_buffer": width,
                    "oracle_seconds": .25 if i == 0 else 2., "reference_seconds": 1.,
                    "selected_control": "sparse_pr", "tied_fastest_controls": ["sparse_pr"]}
                   for i in range(308)]
        stats = {"faster_cases": 307, "slower_cases": 1, "tied_cases": 0,
                 "min_ratio": .25, "max_ratio": 2., "median": 2.,
                 "geomean": math.exp((math.log(.25) + 307 * math.log(2.)) / 308),
                 "aggregate_ratio": (.25 + 307 * 2.) / 308,
                 "regressions": [{"series": "s000", "max_buffer": width, "ratio": .25}]}
        groups[str(width)] = {"cases": 308, "series": 308, "families": 23,
            "descriptive_oracle": {"status": "post_protocol_descriptive_oracle", "reference": "radix_pr",
                "eligible_comparators": eligible.copy(), "per_case_choices": records,
                "winning_control_counts": {m: 308 if m == "sparse_pr" else 0 for m in eligible},
                "tied_fastest_cases": 0, "statistics": stats}}
    return {"schema_version": 1, "protocol_version": 3, "split": "holdout", "audit_status": "PASS",
            "cases": 924, "series": 308, "families": 23, "environment": {"platform": "macOS-fixture"},
            "bindings": {key: "a" * 64 for key in ("audit_sha256", "protocol_sha256", "inputs_sha256",
                         "measurements_sha256", "reporter_sha256", "auditor_sha256")}, "groups": groups}


def test_complete_validation_keeps_every_case_and_the_loss_tail():
    module = importlib.import_module("plot_pr_engine")
    curves, identities, counts = module.validate_report(fixture(), "mac")
    assert len(identities) == 308
    for width in (30, 100, 300):
        assert len(curves[width]) == 308
        assert curves[width][0] == .25 and curves[width][-1] == 2.
        assert counts[str(width)]["losses"] == 1


@pytest.mark.parametrize("change", ["old_version", "development", "incomplete", "omit_loss", "duplicate",
                                  "different_control", "false_loss_list", "ci", "platform", "false_aggregate"])
def test_plot_rejects_partial_mislabeled_or_selected_outcomes(change):
    module = importlib.import_module("plot_pr_engine")
    report = fixture()
    oracle = report["groups"]["30"]["descriptive_oracle"]
    if change == "old_version":
        report["protocol_version"] = 2
    elif change == "development":
        report["split"] = "development"
    elif change == "incomplete":
        report["cases"] = 923
    elif change == "omit_loss":
        oracle["per_case_choices"].pop(0)
    elif change == "duplicate":
        oracle["per_case_choices"][0] = deepcopy(oracle["per_case_choices"][1])
    elif change == "different_control":
        oracle["eligible_comparators"].append("benchopt_both")
    elif change == "false_loss_list":
        oracle["statistics"]["regressions"] = []
    elif change == "ci":
        oracle["statistics"]["geomean_ci95"] = [.1, 10.]
    elif change == "platform":
        report["environment"]["platform"] = "Linux-fixture"
    else:
        oracle["statistics"]["aggregate_ratio"] = 20.
    with pytest.raises(ValueError):
        module.validate_report(report, "mac")
