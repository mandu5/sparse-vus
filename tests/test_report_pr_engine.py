"""Reports must preserve measured denominators, provenance, and failed decisions."""
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
from test_pr_engine_audit import fixture, audit


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False))


@pytest.fixture
def run(tmp_path):
    rows, protocol, inputs = fixture()
    root, output = tmp_path / "repo", tmp_path / "run"
    output.mkdir()
    protocol["source_sha256"] = {}
    for name in audit().REQUIRED_SOURCES:
        source = root / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("fixture source " + name)
        protocol["source_sha256"][name] = digest(source)
    auditor = root / "experiments/audit_pr_engine.py"
    auditor.write_text("fixture auditor")
    write(output / "inputs.json", inputs)
    protocol["inputs_sha256"] = digest(output / "inputs.json")
    write(output / "protocol.json", protocol)
    (output / "measurements.jsonl").write_text(json.dumps(rows[0]) + "\n")
    rebuilt = audit().audit_records(rows, protocol, inputs)
    report = {"status": "PASS", "protocol_sha256": digest(output / "protocol.json"),
              "inputs_sha256": digest(output / "inputs.json"),
              "measurements_sha256": digest(output / "measurements.jsonl"),
              "auditor_sha256": digest(auditor), "reconstructed": rebuilt,
              "data_provenance": {"status": "PASS", "source_members_checked": True},
              "limitations": ["Numerical audit, not formal rounding."]}
    write(output / "audit.json", report)
    write(output / "summary.json", {"status": "PASS", "violations": [],
          "protocol_sha256": report["protocol_sha256"],
          "measurements_sha256": report["measurements_sha256"], "reconstructed": rebuilt})
    write(output / "environment.json", {"protocol_sha256": report["protocol_sha256"],
          "source_sha256": protocol["source_sha256"], "platform": "fixture", "machine": "fixture",
          "threads": 1, "threadpool_info": [{"num_threads": 1}], "cpu_clearance": "No isolation claim"})
    return root, output


def module():
    return importlib.import_module("report_pr_engine")


def test_report_contains_every_method_and_retains_ratio_direction_failures_and_tails(run):
    root, output = run
    result = module().build_report(output, root=root)
    assert result["run_label"] == "v3 development"
    assert len(result["groups"]["30"]["methods"]) == 14
    ratio = result["groups"]["30"]["comparisons"]["radix_pr"]["sparse_pr"]
    assert ratio["median"] == pytest.approx(1 / 7)
    assert ratio["aggregate_ratio"] == pytest.approx(1 / 7)
    assert ratio["geomean_ci95"] == pytest.approx([1 / 7, 1 / 7])
    assert ratio["regressions"][0]["slowdown"] == pytest.approx(7.)
    assert result["decisions"]["radix_primary_decision"]["passes"] is False
    assert "dense_pr_nearest_radix" in result["decisions"]["radix_primary_decision"]["controls"]
    md = module().markdown(result)
    assert "v3 development" in md and "FAIL" in md and "dense_pr_nearest_radix" in md
    assert "radix_pr faster/slower" in md and "Worst radix_pr slowdown" in md
    visible_tex = "\n".join(line for line in module().latex(result).splitlines() if not line.startswith("%"))
    assert "dense\\_pr\\_nearest\\_radix" in visible_tex
    assert "$L=30$" in visible_tex and "comparator time / radix\\_pr time" in visible_tex


@pytest.mark.parametrize("change", ["raw", "protocol", "audit_failed", "input", "source", "false_summary", "auditor", "partial_provenance", "threads", "pool_threads"])
def test_report_rejects_false_or_unbound_receipts(run, change):
    root, output = run
    if change == "raw":
        with (output / "measurements.jsonl").open("a") as stream:
            stream.write("{}\n")
    elif change == "protocol":
        value = json.loads((output / "protocol.json").read_text())
        value["split"] = "holdout"
        write(output / "protocol.json", value)
    elif change == "input":
        write(output / "inputs.json", [])
    elif change == "source":
        (root / "src/sparse_vus/dense_radix.py").write_text("changed source")
    elif change == "auditor":
        (root / "experiments/audit_pr_engine.py").write_text("different auditor")
    elif change == "false_summary":
        value = json.loads((output / "summary.json").read_text())
        value["reconstructed"]["radix_primary_decision"]["passes"] = True
        write(output / "summary.json", value)
    elif change in ("threads", "pool_threads"):
        value = json.loads((output / "environment.json").read_text())
        if change == "threads":
            value["threads"] = 64
        else:
            value["threadpool_info"][0]["num_threads"] = 8
        write(output / "environment.json", value)
    else:
        value = json.loads((output / "audit.json").read_text())
        if change == "audit_failed":
            value["status"] = "FAIL"
        else:
            value["data_provenance"]["source_members_checked"] = False
        write(output / "audit.json", value)
    with pytest.raises(ValueError):
        module().build_report(output, root=root)


def test_ratio_of_total_costs_is_not_the_mean_of_case_ratios():
    rows = [{"series": "a", "family": "f", "max_buffer": 30,
             "median_seconds": {"ref": 1., "other": 10.}},
            {"series": "b", "family": "f", "max_buffer": 30,
             "median_seconds": {"ref": 100., "other": 50.}}]
    result = module().comparison(rows, "ref", "other")
    assert result["aggregate_ratio"] == pytest.approx(60 / 101)
    assert result["median"] == pytest.approx(5.25)
    assert len(result["regressions"]) == 1


@pytest.mark.parametrize("version", [2, 3])
def test_descriptive_oracle_selects_per_case_from_fixed_pr_only_controls(version):
    rows = [{"series": "a", "family": "f", "max_buffer": 30,
             "median_seconds": {"radix_pr": 1., "sparse_pr": .5, "dense_pr_direct": 2., "klein_pr": 10.,
                                "dense_pr_direct_radix": .1, "dense_pr_nearest_radix": 4.,
                                "benchopt_both": .001, "radix_both": .001, "fast_race": .001}},
            {"series": "b", "family": "f", "max_buffer": 30,
             "median_seconds": {"radix_pr": 1., "sparse_pr": 2., "dense_pr_direct": .5, "klein_pr": 10.,
                                "dense_pr_direct_radix": 4., "dense_pr_nearest_radix": .2,
                                "benchopt_both": .001, "radix_both": .001, "fast_race": .001}}]
    # Each old dense/sparse control has aggregate ratio 1.25, yet their
    # per-case fastest control has ratio .5 and defeats radix on both cases.
    assert module().comparison(rows, "radix_pr", "sparse_pr")["aggregate_ratio"] == 1.25
    assert module().comparison(rows, "radix_pr", "dense_pr_direct")["aggregate_ratio"] == 1.25
    result = module().descriptive_oracle(rows, version)
    expected = ["sparse_pr", "dense_pr_direct", "klein_pr"]
    if version == 3:
        expected += ["dense_pr_direct_radix", "dense_pr_nearest_radix"]
    assert result["eligible_comparators"] == expected
    assert result["statistics"]["aggregate_ratio"] == pytest.approx(.5 if version == 2 else .15)
    assert result["statistics"]["slower_cases"] == 2
    assert len(result["statistics"]["regressions"]) == 2
    assert "geomean_ci95" not in result["statistics"]
    assert "aggregate_ratio_ci95" not in result["statistics"]
    winners = ["sparse_pr", "dense_pr_direct"] if version == 2 else ["dense_pr_direct_radix", "dense_pr_nearest_radix"]
    assert [choice["selected_control"] for choice in result["per_case_choices"]] == winners
    assert sum(result["winning_control_counts"].values()) == 2
    assert all(result["winning_control_counts"][method] == 1 for method in winners)


def test_oracle_timing_ties_are_visible_and_counted_only_once():
    rows = [{"series": "tie", "family": "f", "max_buffer": 30,
             "median_seconds": {"radix_pr": 1., "sparse_pr": .5, "dense_pr_direct": .5, "klein_pr": 2.}}]
    result = module().descriptive_oracle(rows, 2)
    assert result["tied_fastest_cases"] == 1
    assert result["per_case_choices"][0]["tied_fastest_controls"] == ["dense_pr_direct", "sparse_pr"]
    assert result["winning_control_counts"] == {"sparse_pr": 0, "dense_pr_direct": 1, "klein_pr": 0}
