"""Derive a compact manuscript fragment from two complete v3 holdout reports.

This publication step never runs metrics, resamples intervals, or pools runs.
Use report_pr_engine.py to produce each report from its independent audit first.
The report schema, complete oracle population, tabulated statistics, decisions,
and cross-platform input/source bindings are checked before any output is written.
These checks do not replace the source-member and raw-record audit.

The figure is produced separately by plot_pr_engine.py from the same reports;
this builder references it but does not render or validate figure bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import plot_pr_engine
from plot_pr_engine import close, positive, require, validate_report

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("mac", "linux")
TITLES = {"mac": "Mac", "linux": "Linux"}
MATCHED = ("dense_pr_direct_radix", "dense_pr_nearest_radix")
EXACT = ("sparse_pr", "dense_pr_direct", "sparse_both", "dense_nearest_both",
         "klein_pr", "benchopt_both", "radix_pr", "radix_both", *MATCHED)
RACERS = ("v02_race", "fast_race", "fast_exact_completion", "fast_race_radix")
METHODS = (*EXACT, *RACERS)
PAIRED = {"sparse_both", "dense_nearest_both", "benchopt_both", "radix_both"}
CONTROLS = ("sparse_pr", "dense_pr_direct", "dense_nearest_both", *MATCHED)
LABELS = {"sparse_pr": "Sparse comparison", "dense_pr_direct": "Dense direct",
          "dense_nearest_both": "Dense nearest (R+P)",
          "dense_pr_direct_radix": "Dense direct radix",
          "dense_pr_nearest_radix": "Dense nearest radix",
          "klein_pr": "Klein fast-VUS", "benchopt_both": "Benchopt (R+P)"}
DECISIONS = {
    "radix_primary_decision": ("radix_pr", CONTROLS),
    "primary_decision": ("fast_race", ("sparse_pr", "dense_pr_direct", "radix_pr")),
    "radix_racing_decision": ("fast_race_radix", ("sparse_pr", "dense_pr_direct", "radix_pr", *MATCHED)),
}
BOOTSTRAP = {"unit": "family", "repetitions": 2000, "seed": 2026102102,
             "confidence": .95, "references": ["fast_race", "sparse_pr", "radix_pr", "fast_race_radix"]}
MEASURED_SOURCES = {
    "experiments/benchmark_pr_engine.py", "experiments/benchmark_advancement.py",
    "experiments/advancement_data_gate.py", "experiments/fast_vus_adapter.py",
    "experiments/benchopt_vus_adapter.py", "src/sparse_vus/pr_compiled.py",
    "src/sparse_vus/fast_racing.py", "src/sparse_vus/racing.py",
    "src/sparse_vus/certified.py", "src/sparse_vus/selection.py",
    "src/sparse_vus/core.py", "src/sparse_vus/compiled.py", "src/sparse_vus/radix.py",
    "src/sparse_vus/dense_radix.py", ".cache/fast_vus/fast_vus.py",
    ".cache/benchopt_vus/metrics.py",
}
FIGURE = "figures/pr-only-oracle-ecdf.pdf"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def hash_value(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def validate_statistics(stats, group, reference, comparator):
    for key in ("median", "geomean", "aggregate_ratio", "min_ratio", "max_ratio"):
        require(positive(stats[key]), f"Invalid {key} for {reference}/{comparator}")
    for key in ("geomean_ci95", "aggregate_ratio_ci95"):
        interval = stats[key]
        require(isinstance(interval, list) and len(interval) == 2
                and all(positive(value) for value in interval) and interval[0] <= interval[1], "Invalid audited interval")
    counts = [stats[key] for key in ("faster_cases", "slower_cases", "tied_cases")]
    require(all(type(value) is int and value >= 0 for value in counts)
            and sum(counts) == group["cases"], "Incomplete comparison counts")
    require(stats["min_ratio"] <= stats["median"] <= stats["max_ratio"], "Invalid median range")
    total = lambda method: group["methods"][method]["sum_case_median_seconds"]
    require(close(stats["aggregate_ratio"], total(comparator) / total(reference)), "Aggregate is not the ratio of sums of case medians")
    losses = stats["regressions"]
    require(isinstance(losses, list) and len(losses) == stats["slower_cases"], "Missing negative cases")
    require(len({(row["series"], row["max_buffer"]) for row in losses}) == len(losses), "Duplicate negative cases")
    require(all(positive(row["ratio"]) and row["ratio"] < 1 for row in losses), "Invalid negative-case ratio")


def validate(reports):
    require(set(reports) == set(PLATFORMS), "Exactly one Mac and one Linux report are required")
    identities = {}
    for platform, report in reports.items():
        _, identities[platform], _ = validate_report(report, platform)
        require(report["method_order"] == list(METHODS), "Holdout method coverage differs")
        require(report["bootstrap"] == BOOTSTRAP, "Frozen uncertainty specification differs")
        require(isinstance(report["models"], list) and len(report["models"]) == 3
                and all(isinstance(model, str) for model in report["models"])
                and len(set(report["models"])) == 3, "Expected three distinct models")
        error = report["max_exact_pr_error"]
        require(type(error) in (int, float) and math.isfinite(error) and 0 <= error <= 1e-11,
                "Exact PR discrepancy exceeds the audited numerical contract")
        slack = report["max_enclosure_slack"]
        require(type(slack) in (int, float) and math.isfinite(slack) and 0 <= slack <= 1e-10,
                "Racing enclosure error exceeds the audited numerical contract")
        sources = report["bindings"]["measured_source_sha256"]
        require(isinstance(sources, dict) and set(sources) == MEASURED_SOURCES
                and all(isinstance(name, str) and not Path(name).is_absolute()
                        and ".." not in Path(name).parts and hash_value(value)
                        for name, value in sources.items()), "Missing measured source bindings")
        for name, group in report["groups"].items():
            require(group["series"] == report["series"] and group["families"] == report["families"], "Comparison population differs")
            require(set(group["methods"]) == set(METHODS), "Missing method timings")
            for method, timing in group["methods"].items():
                require(positive(timing["sum_case_median_seconds"]), "Invalid summed case medians")
                work = "paired ROC+PR" if method in PAIRED else "PR only" if method in EXACT else "PR selection"
                require(timing["work"] == work, "PR-only and paired work labels differ")
            require(set(group["comparisons"]) == set(BOOTSTRAP["references"]), "Missing comparison reference")
            for reference, comparisons in group["comparisons"].items():
                require(set(comparisons) == set(METHODS) - {reference}, "Missing comparator")
                for comparator, stats in comparisons.items():
                    validate_statistics(stats, group, reference, comparator)
            if name != "combined_30_100":
                oracle_rows = group["descriptive_oracle"]["per_case_choices"]
                require(close(group["methods"]["radix_pr"]["sum_case_median_seconds"],
                              math.fsum(row["reference_seconds"] for row in oracle_rows)), "Oracle reference denominator differs")
        combined = report["groups"]["combined_30_100"]
        components = [report["groups"][str(width)] for width in (30, 100)]
        for method in METHODS:
            require(close(combined["methods"][method]["sum_case_median_seconds"],
                          math.fsum(group["methods"][method]["sum_case_median_seconds"] for group in components)),
                    "Combined timing total differs from L=30 and L=100")
        for reference, comparisons in combined["comparisons"].items():
            for comparator, stats in comparisons.items():
                parts = [group["comparisons"][reference][comparator] for group in components]
                require(all(stats[key] == sum(part[key] for part in parts)
                            for key in ("faster_cases", "slower_cases", "tied_cases")),
                        "Combined comparison counts differ from L=30 and L=100")
                losses = lambda items: {(row["series"], row["max_buffer"]): row for row in items}
                require(losses(stats["regressions"]) == losses([row for part in parts for row in part["regressions"]]),
                        "Combined negative cases differ from L=30 and L=100")
        require(set(report["decisions"]) == set(DECISIONS), "Decision coverage differs")
        for name, (reference, controls) in DECISIONS.items():
            decision = report["decisions"][name]
            require(decision["width"] == 30 and decision["reference"] == reference
                    and decision["controls"] == list(controls), "Frozen decision specification differs")
            expected = all(report["groups"]["30"]["comparisons"][reference][method][key][0] > 1
                           for method in controls for key in ("geomean_ci95", "aggregate_ratio_ci95"))
            require(decision["passes"] is expected, "Reported decision contradicts its audited intervals")
    mac, linux = (reports[platform] for platform in PLATFORMS)
    require(identities["mac"] == identities["linux"], "Platforms contain different series/families")
    require(mac["models"] == linux["models"], "Platforms contain different model sets")
    for key in ("inputs_sha256", "measured_source_sha256"):
        require(mac["bindings"][key] == linux["bindings"][key], f"Platforms have different frozen {key}")


def number(value):
    return f"{value:.3f}" if .001 <= value < 1000 else f"{value:.3g}"


def interval(stats, key):
    low, high = stats[key + "_ci95"]
    return f"{number(stats[key])} [{number(low)}, {number(high)}]"


def counts(stats):
    return "/".join(str(stats[key]) for key in ("faster_cases", "slower_cases", "tied_cases"))


def scientific(value):
    mantissa, exponent = f"{value:.3e}".split("e")
    return mantissa + r"\times 10^{" + str(int(exponent)) + "}"


def outcome(report, name):
    return r"\textbf{" + ("PASS" if report["decisions"][name]["passes"] else "FAIL") + "}"


def table(caption, label, columns, heading, rows):
    return [r"\begin{table}[tbp]", r"\centering\small", r"\setlength{\tabcolsep}{3pt}",
            r"\caption{" + caption + "}", r"\label{" + label + "}",
            r"\resizebox{\linewidth}{!}{%", r"\begin{tabular}{" + columns + "}",
            r"\toprule", heading + r" \\", r"\midrule", *rows,
            r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""]


def comparison_row(report, width, method, prefix):
    stats = report["groups"][str(width)]["comparisons"]["radix_pr"][method]
    cells = [*prefix, LABELS[method], number(stats["median"]), interval(stats, "geomean"),
             interval(stats, "aggregate_ratio"), counts(stats)]
    return " & ".join(cells) + r" \\"


def render(reports, report_hashes=None):
    validate(reports)
    mac, linux = (reports[platform] for platform in PLATFORMS)
    cases, series, families = mac["cases"], mac["series"], mac["families"]
    lines = [r"\subsection{Frozen v3 policy holdout: exact radix evaluation}",
             r"\label{sec:pr-engine-results}",
             f"Each platform completed all {cases} tasks on the same {series} series in {families} families,",
             r"with $L=30$ primary, $L=100$ secondary, and $L=300$ a stress regime.",
             "Each task evaluates the three frozen model score vectors and returns the best-PR model set, retaining numerical ties.",
             "Times include whole-task preparation and use the median of three repetitions.",
             "The maximum absolute PR discrepancy from the comparison-sort sparse PR reference was",
             "$" + scientific(mac["max_exact_pr_error"]) + "$ on Mac and $"
             + scientific(linux["max_exact_pr_error"]) + "$ on Linux.",
             "These are numerical agreement checks for the pinned target.", "",
             r"The frozen exact-radix decision at $L=30$ is Mac: " + outcome(mac, "radix_primary_decision")
             + "; Linux: " + outcome(linux, "radix_primary_decision") + ".",
             "It requires both the geometric-mean and aggregate-ratio lower confidence bounds",
             "to exceed one against every one of the five frozen controls, together with correctness.",
             "Klein and Benchopt comparisons are descriptive and are outside this decision.",
             "Table~\\ref{tab:radix-primary} retains every primary control and both external implementations.", "",
             r"All ratios are comparator time divided by exact sparse-radix PR time; values above one favor radix PR.",
             r"Brackets contain audited 95\% family-cluster bootstrap intervals ("
             + str(mac["bootstrap"]["repetitions"]) + " resamples).",
             "The aggregate ratio divides sums of per-case median times; it is not an observed batch wall time.",
             "Intervals describe variation across families, not uncertainty in three timing repetitions.",
             "F/S/T counts cases where radix PR is faster/slower/tied. Decisions use unrounded bounds.", ""]
    rows = []
    for index, platform in enumerate(PLATFORMS):
        if index:
            rows.append(r"\midrule")
        for method in (*CONTROLS, "klein_pr", "benchopt_both"):
            row = comparison_row(reports[platform], 30, method, [TITLES[platform]])
            if method in CONTROLS:
                row = row.replace(LABELS[method], LABELS[method] + r"$^{\dagger}$", 1)
            rows.append(row)
    lines += table(
        r"Primary $L=30$: all " + str(series) + r" cases per platform. $\dagger$ marks the five frozen decision controls. "
        r"R+P methods compute both ROC and PR; the others compute PR only. Dense direct and dense nearest use comparison sorting unless labelled radix.",
        "tab:radix-primary", "llrrrr", r"Platform & Comparator & Median & Geomean [CI] & Aggregate [CI] & F/S/T", rows)
    lines += [r"\paragraph{Secondary and stress regimes.}",
              r"Table~\ref{tab:radix-secondary} gives both matched PR-only radix dense controls at $L=100$ and $L=300$.",
              "These controls share fixed-width score ordering with sparse radix and retain full dense width sweeps.",
              "Their ratios assess the support-event reduction after matching the ranking implementation.",
              "The full bound reports retain every other comparator, family effect, and slower case at each width.", ""]
    rows = [comparison_row(reports[platform], width, method, [TITLES[platform], str(width)])
            for platform in PLATFORMS for width in (100, 300) for method in MATCHED]
    lines += table(r"Secondary and stress widths: all " + str(series)
                   + r" cases per row, matched PR-only controls. Ratio direction and intervals follow Table~\ref{tab:radix-primary}.",
                   "tab:radix-secondary", "lllrrrr",
                   r"Platform & $L$ & Comparator & Median & Geomean [CI] & Aggregate [CI] & F/S/T", rows)
    lines += [r"\paragraph{Post-protocol descriptive PR-only oracle.}",
              "For each case, the oracle selects the fastest of comparison-based sparse PR, direct dense PR,",
              "Klein PR, direct dense radix PR, and nearest-interval dense radix PR.",
              "Paired ROC+PR methods and adaptive racers are excluded from this PR-only exhaustive set.",
              r"Table~\ref{tab:radix-oracle} and Figure~\ref{fig:radix-oracle} retain every case and loss.",
              "No confidence interval is assigned to this retrospective minimum, and it changes no frozen decision.", ""]
    rows = []
    for platform in PLATFORMS:
        for width in (30, 100, 300):
            stats = reports[platform]["groups"][str(width)]["descriptive_oracle"]["statistics"]
            rows.append(" & ".join([TITLES[platform], str(width), number(stats["median"]),
                                    number(stats["geomean"]), number(stats["aggregate_ratio"]),
                                    counts(stats), number(stats["min_ratio"])]) + r" \\")
    lines += table("Descriptive PR-only oracle / exact sparse-radix ratios; no confidence intervals. Minimum retains the slowest relative radix case.",
                   "tab:radix-oracle", "llrrrrr", r"Platform & $L$ & Median & Geomean & Aggregate & F/S/T & Minimum", rows)
    lines += [r"\begin{figure}[tbp]", r"\centering",
              r"\includegraphics[width=\linewidth]{" + FIGURE + "}",
              r"\caption{Post-protocol oracle ECDFs for the v3 policy holdout: all " + str(series)
              + r" cases at each width on each platform, without tail clipping. The horizontal coordinate is the fastest eligible exhaustive PR-only control's whole-task case median divided by exact sparse-radix PR time. Values above one favor radix PR. The five eligible controls are specified in the text; no oracle confidence intervals are computed.}",
              r"\label{fig:radix-oracle}", r"\end{figure}", "",
              r"\paragraph{Separate racing decisions and scope.}",
              r"The frozen comparison-order racing decision at $L=30$ is Mac " + outcome(mac, "primary_decision")
              + ", Linux " + outcome(linux, "primary_decision") + "; the separate radix-order racing decision is Mac "
              + outcome(mac, "radix_racing_decision") + ", Linux " + outcome(linux, "radix_racing_decision") + ".",
              "The first requires both interval lower bounds above one against comparison-based sparse PR, direct dense PR, and exact radix PR;",
              "the second additionally requires this against both matched dense radix PR controls.",
              "These decisions include preparation, adaptive queries, and exact completion in each measured task.",
              "Racing outcomes are separate from the exact-radix decision, and failed criteria remain reported.",
              "The v2 development runs remain historical development evidence and are not pooled with this holdout.",
              "Platforms are summarized separately: no cross-run timing pooling is performed.",
              "The Mac was not isolated: its starting snapshot shows an unrelated Python worker near 100 percent CPU, alongside normal desktop activity. Snapshots are not a continuous load trace. Agent test, build, and report execution stopped during timing; lightweight status reads, completed remote-artifact transfers, and document edits continued. No unrelated process was stopped by the experiment.",
              "The Linux confirmation used a separate serial GitHub Actions job; hosted hardware and host background load were outside our control.",
              "This policy holdout uses previously studied corpus families; it is not an external-domain dataset.",
              "The results address the stated workload and tested implementations, without establishing universal superiority.", ""]
    if report_hashes is not None:
        require(set(report_hashes) == set(PLATFORMS) and all(hash_value(value) for value in report_hashes.values()), "Invalid report receipt")
        lines += [r"\par\noindent{\footnotesize Reproducibility receipt (SHA-256 prefixes): "
                  + "; ".join(TITLES[p] + r" report \texttt{" + report_hashes[p][:12]
                               + r"}, audit \texttt{" + reports[p]["bindings"]["audit_sha256"][:12] + "}"
                               for p in PLATFORMS)
                  + ". The accompanying JSON receipt records full report, measured-source, and generator hashes.}", ""]
    return "\n".join(lines)


def build(mac_path, linux_path, output, receipt_path=None):
    paths = {"mac": Path(mac_path), "linux": Path(linux_path)}
    raw = {platform: path.read_bytes() for platform, path in paths.items()}
    reports = {platform: json.loads(data) for platform, data in raw.items()}
    hashes = {platform: sha(data) for platform, data in raw.items()}
    text = render(reports, hashes)
    output = Path(output)
    receipt_path = Path(receipt_path) if receipt_path else output.with_suffix(".receipt.json")
    targets = {output.resolve(), receipt_path.resolve()}
    require(len(targets) == 2 and not targets.intersection(path.resolve() for path in paths.values()), "Output paths overlap input reports or each other")
    receipt = {"schema_version": 1, "status": "PASS", "scope": "validated report-to-manuscript derivation; no metric execution or raw-data reaudit",
               "platforms": {platform: {"report_filename": paths[platform].name, "report_sha256": hashes[platform],
                                         "cases": reports[platform]["cases"], "series": reports[platform]["series"],
                                         "bindings": reports[platform]["bindings"],
                                         "decisions": {name: decision["passes"] for name, decision in reports[platform]["decisions"].items()}}
                             for platform in PLATFORMS},
               "builder_sha256": sha(Path(__file__).read_bytes()),
               "validator_sha256": sha(Path(plot_pr_engine.__file__).read_bytes()),
               "output_filename": output.name, "output_sha256": sha(text.encode("utf-8")),
               "figure": {"path": FIGURE, "validation": "not performed by this builder; generate from the same two reports with plot_pr_engine.py"},
               "timing_pooling": "none", "oracle_confidence_intervals": "none"}
    serialized = json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
    # All validation and serialization complete before output directory creation.
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    receipt_path.write_text(serialized, encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mac", type=Path, required=True)
    parser.add_argument("--linux", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "paper/pr_engine_results.tex")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = build(args.mac, args.linux, args.output, args.receipt)
    print(json.dumps({"status": receipt["status"], "output": receipt["output_filename"],
                      "sha256": receipt["output_sha256"], "cases_per_platform": 924}))


if __name__ == "__main__":
    main()
