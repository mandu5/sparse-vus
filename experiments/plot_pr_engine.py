"""Plot complete, independently audited v3 holdout report JSONs.

This is a post-protocol descriptive figure, not a new experiment or decision.
No confidence intervals, case trimming, or synthetic outcomes are generated.
Matplotlib is imported only after both input reports pass validation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

ELIGIBLE = ["sparse_pr", "dense_pr_direct", "klein_pr",
            "dense_pr_direct_radix", "dense_pr_nearest_radix"]
WIDTHS = (30, 100, 300)
CAPTION = (
    "v3 policy holdout. Post-protocol descriptive oracle: fastest eligible PR-only exhaustive control per case.\n"
    "All 308 cases per width are included; no CIs or tail clipping. Ratios above 1 favor radix PR.\n"
    "Controls: comparison-sort sparse/direct dense, Klein, and radix direct/nearest dense; three-repeat whole-task medians."
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def close(actual, expected):
    return type(actual) in (int, float) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)


def validate_report(report, platform):
    require(report["schema_version"] == 1 and report["protocol_version"] == 3
            and report["split"] == "holdout" and report["audit_status"] == "PASS", "Requires independently audited v3 holdout PASS")
    require(report["cases"] == 924 and report["series"] == 308, "Holdout must contain all 924 cases / 308 series")
    description = report["environment"]["platform"]
    require(isinstance(description, str) and (
        description.startswith(("macOS", "Darwin")) if platform == "mac" else description.startswith("Linux")), "Platform label differs from report")
    for key in ("audit_sha256", "protocol_sha256", "inputs_sha256", "measurements_sha256", "reporter_sha256", "auditor_sha256"):
        value = report["bindings"][key]
        require(isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value), "Missing valid source binding")
    require(set(report["groups"]) == {"30", "100", "300", "combined_30_100"}, "Unexpected width groups")
    require(report["groups"]["combined_30_100"]["cases"] == 616, "Incomplete combined group")
    curves, identities, summaries = {}, None, {}
    for width in WIDTHS:
        group = report["groups"][str(width)]
        require(group["cases"] == group["series"] == 308, "Incomplete width coverage")
        oracle = group["descriptive_oracle"]
        require(oracle["status"] == "post_protocol_descriptive_oracle" and oracle["reference"] == "radix_pr"
                and oracle["eligible_comparators"] == ELIGIBLE, "Oracle scope or eligible comparator set differs")
        records = oracle["per_case_choices"]
        require(len(records) == 308 and len({r["series"] for r in records}) == 308, "Missing or duplicate case; no loss omission allowed")
        current = {r["series"]: r["family"] for r in records}
        require(len(set(current.values())) == group["families"] == report["families"], "Family coverage differs")
        require(identities is None or current == identities, "Series/families differ across widths")
        identities = current
        ratios, counts, losses = [], Counter(), {}
        for row in records:
            require(row["max_buffer"] == width and positive(row["oracle_seconds"])
                    and positive(row["reference_seconds"]), "Invalid case timing or width")
            tied = row["tied_fastest_controls"]
            require(isinstance(tied, list) and tied == sorted(set(tied)) and bool(tied)
                    and set(tied) <= set(ELIGIBLE) and row["selected_control"] == tied[0], "Invalid fastest-control attribution")
            counts[row["selected_control"]] += 1
            ratio = row["oracle_seconds"] / row["reference_seconds"]
            require(positive(ratio), "Invalid log-axis ratio")
            ratios.append(ratio)
            if ratio < 1:
                losses[row["series"]] = ratio
        require(oracle["winning_control_counts"] == {m: counts[m] for m in ELIGIBLE}, "Winning-control counts differ")
        require(oracle["tied_fastest_cases"] == sum(len(r["tied_fastest_controls"]) > 1 for r in records), "Timing-tie counts differ")
        stats = oracle["statistics"]
        require(not any(key.endswith("_ci95") for key in stats), "Oracle must not acquire unaudited confidence intervals")
        require(stats["faster_cases"] == sum(r > 1 for r in ratios)
                and stats["slower_cases"] == len(losses) and stats["tied_cases"] == sum(r == 1 for r in ratios), "Ratio counts differ")
        expected = {"min_ratio": min(ratios), "max_ratio": max(ratios),
                    "median": statistics.median(ratios),
                    "geomean": math.exp(math.fsum(math.log(r) for r in ratios) / 308),
                    "aggregate_ratio": math.fsum(r["oracle_seconds"] for r in records) / math.fsum(r["reference_seconds"] for r in records)}
        require(all(close(stats[key], value) for key, value in expected.items()), "Oracle point estimates differ from all case choices")
        regressions = stats["regressions"]
        require(len(regressions) == len(losses) and {r["series"] for r in regressions} == set(losses), "Negative cases were omitted or duplicated")
        require(all(r["max_buffer"] == width and close(r["ratio"], losses[r["series"]]) for r in regressions), "Negative-case ratios differ")
        curves[width] = sorted(ratios)
        summaries[str(width)] = {"included_cases": 308, "losses": len(losses), "timing_ties": stats["tied_cases"],
                                 "minimum_ratio": min(ratios), "maximum_ratio": max(ratios)}
    return curves, identities, summaries


def render(mac_path, linux_path, output_prefix):
    paths = {"mac": Path(mac_path), "linux": Path(linux_path)}
    reports = {platform: json.loads(path.read_text()) for platform, path in paths.items()}
    verified = {platform: validate_report(report, platform) for platform, report in reports.items()}
    require(verified["mac"][1] == verified["linux"][1], "Platforms contain different series/families")
    require(reports["mac"]["bindings"]["inputs_sha256"] == reports["linux"]["bindings"]["inputs_sha256"], "Platforms use different frozen inputs")
    # No imports, figure files, or directory creation occur before validation.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none"})
    all_values = [v for curves, _, _ in verified.values() for values in curves.values() for v in values]
    left, right = min(1., min(all_values)) / 1.15, max(1., max(all_values)) * 1.15
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.5), sharex=True, sharey=True)
    colors, styles = ("#0072B2", "#D55E00", "#009E73"), ("-", "--", ":")
    for axis, platform, title in zip(axes, ("mac", "linux"), ("Mac", "Linux")):
        for width, color, style in zip(WIDTHS, colors, styles):
            values = verified[platform][0][width]
            axis.step([left, *values, right], [0., *[(i + 1) / len(values) for i in range(len(values))], 1.],
                      where="post", label=f"L={width}", color=color, linestyle=style, linewidth=1.8)
        axis.axvline(1., color="#444444", linewidth=1., linestyle="--", zorder=0)
        axis.set(xscale="log", xlim=(left, right), ylim=(0., 1.015), title=f"{title}: 308 cases per width")
        axis.grid(axis="y", alpha=.25)
        axis.grid(axis="x", which="major", alpha=.12)
        axis.spines[["top", "right"]].set_visible(False)
        axis.legend(frameon=False, loc="lower right")
        axis.set_xlabel("Fastest eligible PR-only control time / radix PR time")
    axes[0].set_ylabel("Fraction of cases (ECDF)")
    fig.subplots_adjust(left=.075, right=.985, bottom=.29, top=.91, wspace=.12)
    fig.text(.5, .035, CAPTION, ha="center", va="bottom", fontsize=8.3, linespacing=1.45)
    prefix = Path(output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for extension in ("png", "pdf", "svg"):
        output = Path(str(prefix) + "." + extension)
        fig.savefig(output, dpi=300, facecolor="white")
        outputs[extension] = {"filename": output.name, "sha256": digest(output), "bytes": output.stat().st_size}
    plt.close(fig)
    receipt = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
               "analysis": "post_protocol_descriptive_oracle_ecdf", "caption": CAPTION,
               "eligible_comparators": ELIGIBLE, "confidence_intervals": "none", "excluded_cases": 0,
               "ratio": "minimum eligible complete-task case-median seconds / radix_pr case-median seconds",
               "axis": {"x_scale": "log", "x_limits": [left, right], "vertical_reference": 1.},
               "platforms": {p: {"report_filename": paths[p].name, "report_sha256": digest(paths[p]),
                                 "audit_sha256": reports[p]["bindings"]["audit_sha256"],
                                 "protocol_sha256": reports[p]["bindings"]["protocol_sha256"],
                                 "measurements_sha256": reports[p]["bindings"]["measurements_sha256"],
                                 "inputs_sha256": reports[p]["bindings"]["inputs_sha256"],
                                 "cases": 924, "by_width": verified[p][2]} for p in paths},
               "plotter_sha256": digest(Path(__file__)), "matplotlib": matplotlib.__version__, "outputs": outputs}
    Path(str(prefix) + ".json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mac", type=Path, required=True)
    parser.add_argument("--linux", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    result = render(args.mac, args.linux, args.output_prefix)
    print(json.dumps({"status": "PASS", "cases_per_platform": 924, "outputs": result["outputs"]}))


if __name__ == "__main__":
    main()
