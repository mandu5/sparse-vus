"""Synthetic report tests only; these fixtures are not benchmark outcomes."""
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))


def fixture(platform):
    reporter = importlib.import_module("report_pr_engine")
    exact = [*reporter.EXACT_V2, *reporter.MATCHED]
    methods = [*exact, *reporter.RACERS]
    references = ["fast_race", "sparse_pr", "radix_pr", "fast_race_radix"]
    rows = []
    for width in (30, 100, 300):
        for index in range(308):
            times = {method: 2. for method in methods}
            times.update(radix_pr=1., fast_race=3., fast_race_radix=4.)
            if index == 0:
                times["sparse_pr"] = .25
            if platform == "linux":
                times["dense_pr_nearest_radix"] = .5
            rows.append({"series": f"s{index:03}", "family": f"f{index % 23}",
                         "max_buffer": width, "median_seconds": times})
    groups = {}
    for name in ("30", "100", "300", "combined_30_100"):
        selected = [r for r in rows if r["max_buffer"] in
                    ((30, 100) if name == "combined_30_100" else (int(name),))]
        group = {"cases": len(selected), "series": 308, "families": 23,
                 "methods": {}, "comparisons": {},
                 "descriptive_oracle": reporter.descriptive_oracle(selected, 3)}
        for method in methods:
            group["methods"][method] = {
                "sum_case_median_seconds": math.fsum(r["median_seconds"][method] for r in selected),
                "work": "paired ROC+PR" if method in ("sparse_both", "dense_nearest_both", "benchopt_both", "radix_both")
                        else "PR only" if method in exact else "PR selection"}
        for reference in references:
            group["comparisons"][reference] = {}
            for method in methods:
                if method == reference:
                    continue
                stats = reporter.comparison(selected, reference, method)
                # Deliberately synthetic intervals, not a resampling procedure.
                for key in ("geomean", "aggregate_ratio"):
                    stats[key + "_ci95"] = [stats[key] * .9, stats[key] * 1.1]
                group["comparisons"][reference][method] = stats
        groups[name] = group
    specifications = {
        "primary_decision": ("fast_race", ["sparse_pr", "dense_pr_direct", "radix_pr"]),
        "radix_primary_decision": ("radix_pr", ["sparse_pr", "dense_pr_direct", "dense_nearest_both", *reporter.MATCHED]),
        "radix_racing_decision": ("fast_race_radix", ["sparse_pr", "dense_pr_direct", "radix_pr", *reporter.MATCHED]),
    }
    decisions = {}
    for name, (reference, controls) in specifications.items():
        passes = all(groups["30"]["comparisons"][reference][method][key][0] > 1
                     for method in controls for key in ("geomean_ci95", "aggregate_ratio_ci95"))
        decisions[name] = {"width": 30, "passes": passes, "reference": reference, "controls": controls}
    return {"schema_version": 1, "protocol_version": 3, "split": "holdout", "audit_status": "PASS",
            "cases": 924, "series": 308, "families": 23, "models": ["a", "b", "c"],
            "method_order": methods, "max_exact_pr_error": 3.25e-13, "max_enclosure_slack": 0.,
            "environment": {"platform": "macOS-fixture" if platform == "mac" else "Linux-fixture"},
            "bootstrap": {"unit": "family", "repetitions": 2000, "seed": 2026102102,
                          "confidence": .95, "references": references},
            "bindings": {**{key: "a" * 64 for key in ("audit_sha256", "protocol_sha256", "inputs_sha256",
                         "measurements_sha256", "reporter_sha256", "auditor_sha256")},
                         "measured_source_sha256": {name: "b" * 64 for name in
                             reporter.SOURCES_V2 | {"src/sparse_vus/dense_radix.py"}}},
            "groups": groups, "decisions": decisions}


def module():
    return importlib.import_module("build_pr_engine_paper")


def test_full_reports_keep_platform_decisions_losses_and_paired_work_visible():
    reports = {platform: fixture(platform) for platform in ("mac", "linux")}
    text = module().render(reports)
    assert r"Mac: \textbf{PASS}; Linux: \textbf{FAIL}" in text
    assert "Dense nearest (R+P)" in text and "Benchopt (R+P)" in text
    assert "307/1/0" in text and "0/308/0" in text
    assert r"3.250\times 10^{-13}" in text
    assert "discrepancy from the comparison-sort sparse PR reference" in text
    assert "not an observed batch wall time" in text
    assert "v2 development" in text and "No confidence interval" in text
    assert "figures/pr-only-oracle-ecdf.pdf" in text
    assert text.count(r"\begin{table}") == 3
    assert "AMD" not in text and "M1" not in text
    assert r"Mac \textbf{FAIL}, Linux \textbf{FAIL}" in text


@pytest.mark.parametrize("change", ["incomplete", "different_inputs", "different_sources", "different_models",
                                    "missing_control", "false_decision", "invalid_ci", "false_sum",
                                    "false_counts", "paired_work", "invalid_error", "different_population",
                                    "missing_sources_both", "invalid_enclosure", "false_combined_sum",
                                    "false_combined_counts", "false_combined_loss"])
def test_report_rejection_precedes_any_output_write(tmp_path, change):
    reports = {platform: fixture(platform) for platform in ("mac", "linux")}
    report = reports["linux"]
    stats = report["groups"]["30"]["comparisons"]["radix_pr"]["sparse_pr"]
    if change == "incomplete":
        report["cases"] = 923
    elif change == "different_inputs":
        report["bindings"]["inputs_sha256"] = "c" * 64
    elif change == "different_sources":
        report["bindings"]["measured_source_sha256"]["src/sparse_vus/radix.py"] = "c" * 64
    elif change == "different_models":
        report["models"][0] = "changed"
    elif change == "missing_control":
        del report["groups"]["30"]["comparisons"]["radix_pr"]["dense_pr_nearest_radix"]
    elif change == "false_decision":
        report["decisions"]["radix_primary_decision"]["passes"] = True
    elif change == "invalid_ci":
        stats["geomean_ci95"] = [2., 1.]
    elif change == "false_sum":
        stats["aggregate_ratio"] *= 2
    elif change == "false_counts":
        stats["slower_cases"] = 0
    elif change == "paired_work":
        report["groups"]["30"]["methods"]["benchopt_both"]["work"] = "PR only"
    elif change == "invalid_error":
        report["max_exact_pr_error"] = float("nan")
    elif change == "missing_sources_both":
        # Matching maps do not establish full provenance if both omit the driver.
        for value in reports.values():
            del value["bindings"]["measured_source_sha256"]["experiments/benchmark_pr_engine.py"]
    elif change == "invalid_enclosure":
        report["max_enclosure_slack"] = 2e-10
    elif change == "false_combined_sum":
        # Every ratio still agrees with these totals, but the totals are invented.
        for timing in report["groups"]["combined_30_100"]["methods"].values():
            timing["sum_case_median_seconds"] *= 2
    elif change == "false_combined_counts":
        # Preserve the total count and loss list while claiming a false timing tie.
        combined = report["groups"]["combined_30_100"]["comparisons"]["radix_pr"]["dense_pr_direct"]
        combined["faster_cases"] -= 1
        combined["tied_cases"] += 1
    elif change == "false_combined_loss":
        combined = report["groups"]["combined_30_100"]["comparisons"]["radix_pr"]["sparse_pr"]
        combined["regressions"][0]["series"] = "invented-loss"
    elif change == "different_population":
        for group in report["groups"].values():
            for row in group["descriptive_oracle"]["per_case_choices"]:
                if row["series"] == "s001":
                    row["family"] = "f2"
    paths = {}
    for platform, value in reports.items():
        paths[platform] = tmp_path / f"{platform}.json"
        paths[platform].write_text(json.dumps(value))
    output = tmp_path / "paper" / "results.tex"
    with pytest.raises(ValueError):
        module().build(paths["mac"], paths["linux"], output)
    assert not output.parent.exists()


def test_receipt_binds_exact_input_and_generated_bytes_without_absolute_paths(tmp_path):
    paths = {}
    for platform in ("mac", "linux"):
        paths[platform] = tmp_path / f"{platform}.json"
        paths[platform].write_text(json.dumps(fixture(platform)))
    output = tmp_path / "paper" / "results.tex"
    receipt = module().build(paths["mac"], paths["linux"], output)
    assert receipt["output_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert receipt["platforms"]["linux"]["report_sha256"] == hashlib.sha256(paths["linux"].read_bytes()).hexdigest()
    assert receipt["platforms"]["mac"]["decisions"]["radix_primary_decision"] is True
    assert receipt["platforms"]["linux"]["decisions"]["radix_primary_decision"] is False
    assert receipt["platforms"]["mac"]["cases"] == 924
    assert str(tmp_path) not in json.dumps(receipt)
    assert json.loads(output.with_suffix(".receipt.json").read_text()) == receipt


def test_pass_is_decided_before_display_rounding():
    reports = {platform: fixture(platform) for platform in ("mac", "linux")}
    report = reports["mac"]
    stats = report["groups"]["30"]["comparisons"]["radix_pr"]["sparse_pr"]
    stats["geomean_ci95"][0] = 1.00001
    assert r"Mac: \textbf{PASS}" in module().render(reports)
    stats["geomean_ci95"][0] = 1.
    report["decisions"]["radix_primary_decision"]["passes"] = False
    assert r"Mac: \textbf{FAIL}" in module().render(reports)
