"""Recompute descriptive statistics, paired ranking changes, and paper figures."""
from __future__ import annotations
from collections import defaultdict
import csv
import hashlib
import itertools
import json
from pathlib import Path
import platform
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
ART, PAPER = ROOT / "artifacts", ROOT / "paper"
TIE_TOL = 1e-10


def write_csv(path, rows):
    if not rows:
        path.write_text(""); return
    with path.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def tex_number(value):
    if abs(value) >= 0.01:
        return f"{value:.3f}"
    mantissa, exponent = f"{value:.2e}".split("e")
    return f"{mantissa}\\times10^{{{int(exponent)}}}"


def main():
    gate = json.loads((ART / "final_artifact_gate.json").read_text())
    if gate["status"] != "PASS":
        raise RuntimeError("The independent artifact gate must pass before analysis")
    for relative, expected in gate["input_sha256"].items():
        actual = hashlib.sha256((ART / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Artifact changed after verification: {relative}")
    gate_source = ROOT / "experiments/verify_artifact.py"
    if hashlib.sha256(gate_source.read_bytes()).hexdigest() != gate["gate_source_sha256"]:
        raise RuntimeError("Verification code changed; rerun the artifact gate")
    rows = [json.loads(line) for line in (ART / "public_benchmark.jsonl").read_text().splitlines()]
    external = json.loads((ART / "public_external_baselines.json").read_text())
    environment = json.loads((ART / "benchmark_environment.json").read_text())
    receipt = json.loads((ART / "public_benchmark_receipt.json").read_text())
    ratios = np.array([r["speedup_vs_fastest_dense"] for r in rows])
    by_series, by_family, by_case = defaultdict(list), defaultdict(list), defaultdict(dict)
    for row in rows:
        by_series[row["series"]].append(row)
        by_family[row["family"]].append(row)
        by_case[(row["series"], row["max_buffer"])][row["model"]] = row
    series_log_ratios = np.array([np.mean(np.log([r["speedup_vs_fastest_dense"] for r in group])) for group in by_series.values()])
    rng = np.random.default_rng(2026101901)
    bootstrap = np.exp(np.mean(rng.choice(series_log_ratios, (5000, len(series_log_ratios)), replace=True), axis=1))
    family_log_sum = np.array([sum(np.log(r["speedup_vs_fastest_dense"]) for r in group) for group in by_family.values()])
    family_sizes = np.array([len(group) for group in by_family.values()])
    family_choice = rng.integers(0, len(by_family), size=(5000, len(by_family)))
    family_bootstrap = np.exp(family_log_sum[family_choice].sum(axis=1) / family_sizes[family_choice].sum(axis=1))
    pair_rows, reversal_rows, metric_summary = [], [], {}
    for metric_index, metric_name in enumerate(["ROC", "PR"]):
        pairs, exact_ties, sampled_ties, reversals, top_changes = 0, 0, 0, 0, 0
        affected_series, affected_families = set(), set()
        for (series, width), models in sorted(by_case.items()):
            for a, b in itertools.combinations(sorted(models), 2):
                first, second = models[a], models[b]
                exact_delta = first["exact"][metric_index] - second["exact"][metric_index]
                sampled_delta = first["sampled250"][metric_index] - second["sampled250"][metric_index]
                tie_exact, tie_sample = abs(exact_delta) <= TIE_TOL, abs(sampled_delta) <= TIE_TOL
                reverse = (not tie_exact and not tie_sample and exact_delta * sampled_delta < 0)
                pairs += 1; exact_ties += int(tie_exact); sampled_ties += int(tie_sample); reversals += int(reverse)
                pair = {"series": series, "family": first["family"], "max_buffer": width, "metric": metric_name,
                        "model_a": a, "model_b": b, "exact_delta": exact_delta, "sampled_delta": sampled_delta,
                        "exact_tie": tie_exact, "sampled_tie": tie_sample, "strict_reversal": reverse}
                pair_rows.append(pair)
                if reverse:
                    reversal_rows.append(pair); affected_series.add(series); affected_families.add(first["family"])
            exact = {m: r["exact"][metric_index] for m, r in models.items()}
            approximate = {m: r["sampled250"][metric_index] for m, r in models.items()}
            top_exact = {m for m, v in exact.items() if max(exact.values()) - v <= TIE_TOL}
            top_sample = {m for m, v in approximate.items() if max(approximate.values()) - v <= TIE_TOL}
            if len(top_exact) == len(top_sample) == 1 and top_exact != top_sample:
                top_changes += 1
        errors = np.abs(np.array([r["sampled250_delta"][metric_index] for r in rows]))
        metric_summary[metric_name] = {"paired_comparisons": pairs, "strict_reversals": reversals,
            "exact_ties": exact_ties, "sampled_ties": sampled_ties, "affected_unique_series": len(affected_series),
            "affected_families": sorted(affected_families), "unique_top_model_changes": top_changes,
            "absolute_error_median": float(np.median(errors)), "absolute_error_p95": float(np.quantile(errors, .95)),
            "absolute_error_max": float(errors.max()), "mean_signed_error": float(np.mean([r["sampled250_delta"][metric_index] for r in rows]))}
    write_csv(ART / "ranking_pairs.csv", pair_rows)
    write_csv(ART / "ranking_reversals.csv", reversal_rows)
    family_rows = []
    for family, group in sorted(by_family.items()):
        speed = np.array([r["speedup_vs_fastest_dense"] for r in group])
        family_rows.append({"family": family, "series": len(set(r["series"] for r in group)), "metric_evaluations": len(group),
                           "median_speedup": float(np.median(speed)), "geometric_mean_speedup": float(np.exp(np.mean(np.log(speed)))),
                           "fraction_faster": float(np.mean(speed > 1)), "median_support_fraction": float(np.median([r["support_points"] / r["n"] for r in group]))})
    write_csv(ART / "family_summary.csv", family_rows)
    indexed = {(r["series"], r["model"], r["max_buffer"]): r for r in rows}
    external_summary = {}
    for key in ["official250", "dtaianomaly250", "dtaianomaly_exact"]:
        speed = []
        errors = []
        for row in external:
            base = row[key]
            speed.append(float(np.median(base["seconds"])) / indexed[(row["series"], row["model"], row["width"])]["median_seconds"]["sparse_numba"])
            errors.append(base.get("target_error", base.get("sampled_error")))
        external_summary[key] = {"comparisons": len(speed), "series": len(set(r["series"] for r in external)),
                                 "family": "NAB", "median_speedup": float(np.median(speed)),
                                 "min_speedup": min(speed), "max_speedup": max(speed), "max_target_error": max(errors)}
    max_error_row = max(rows, key=lambda r: abs(r["sampled250_delta"][1]))
    summary = {"series": len(by_series), "families": len(by_family), "score_vectors": receipt["score_vectors"],
        "metric_evaluations": len(rows), "sequence_length_min": min(r["n"] for r in rows), "sequence_length_max": max(r["n"] for r in rows),
        "median_speedup_vs_fastest_dense": float(np.median(ratios)),
        "geometric_mean_speedup_vs_fastest_dense": float(np.exp(np.mean(series_log_ratios))),
        "series_cluster_bootstrap95": np.quantile(bootstrap, [.025, .975]).tolist(),
        "family_cluster_bootstrap95": np.quantile(family_bootstrap, [.025, .975]).tolist(),
        "faster_count": int(np.sum(ratios > 1)), "slower_or_equal_count": int(np.sum(ratios <= 1)),
        "minimum_speedup": float(ratios.min()), "maximum_speedup": float(ratios.max()),
        "max_numerical_error": max(gate["maximum_main_error"], gate["maximum_crop_error"], gate["maximum_external_error"]),
        "metrics": metric_summary, "external": external_summary,
        "largest_pr_error_example": {k: max_error_row[k] for k in ["series", "model", "max_buffer", "n", "exact", "sampled250", "sampled250_delta"]},
        "ci_scope": "Descriptive bootstrap over this fixed benchmark; series clusters retain all models and widths. Family-cluster interval additionally resamples whole source-family groups. Neither is a population-generalization guarantee."}
    (ART / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
    # Standard publication-oriented plots. Vector SVG and high-resolution PNG.
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6), constrained_layout=True)
    for width, color in [(10, "#2563a6"), (30, "#d37725")]:
        subset = [r for r in rows if r["max_buffer"] == width]
        axes[0].scatter([r["support_points"] / r["n"] for r in subset], [r["speedup_vs_fastest_dense"] for r in subset], s=10, alpha=.35, color=color, label=f"L = {width}", rasterized=True)
    axes[0].axhline(1, color="black", ls="--", lw=1)
    axes[0].set(xscale="log", yscale="log", xlabel="Maximum support fraction Q / n", ylabel="Speedup over fastest dense baseline")
    axes[0].set_ylim(.23, 8.5)
    axes[0].yaxis.set_major_locator(FixedLocator([.25, .5, 1, 2, 4, 8]))
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}×"))
    axes[0].legend(frameon=False)
    for index, label, color in [(0, "VUS-ROC", "#2563a6"), (1, "VUS-PR", "#b33d4d")]:
        values = np.sort(np.abs([r["sampled250_delta"][index] for r in rows]))
        axes[1].plot(np.maximum(values, 1e-16), np.arange(1, len(values) + 1) / len(values), label=label, color=color)
    axes[1].set(xscale="log", xlabel="Absolute error of 250-threshold approximation", ylabel="Fraction of evaluated score/width cases", ylim=(0, 1.02))
    axes[1].legend(frameon=False)
    fig.savefig(PAPER / "public-results.png", dpi=300)
    fig.savefig(PAPER / "public-results.svg")
    plt.close(fig)
    macros = {"NumSeries": str(summary["series"]), "NumScores": str(summary["score_vectors"]),
              "MedianSpeedup": f"{summary['median_speedup_vs_fastest_dense']:.2f}$\\times$",
              "MachineCPU": environment["cpu"], "PythonVersion": environment["python"].split()[0]}
    (PAPER / "results.tex").write_text("\n".join("\\newcommand{\\" + name + "}{" + value + "}" for name, value in macros.items()) + "\n")
    geom = summary["geometric_mean_speedup_vs_fastest_dense"]
    ci, family_ci = summary["series_cluster_bootstrap95"], summary["family_cluster_bootstrap95"]
    body = f"""The completed experiment contains {summary['series']} series from {summary['families']} source
families, {summary['score_vectors']} released score vectors, and {len(rows)} score/width
evaluations. Sequence lengths range from {summary['sequence_length_min']:,} to
{summary['sequence_length_max']:,}. The independent final artifact gate passes all
coverage, finite-value, source-hash, internal, crop, and external-comparator checks.
The maximum absolute numerical discrepancy is ${tex_number(summary['max_numerical_error'])}$.

The median compiled-sparse speedup over the fastest dense baseline is
{summary['median_speedup_vs_fastest_dense']:.2f}$\\times$, with geometric mean {geom:.2f}$\\times$.
The 95\\% series-cluster bootstrap interval for the geometric mean is
[{ci[0]:.2f}, {ci[1]:.2f}]; resampling whole source families gives
[{family_ci[0]:.2f}, {family_ci[1]:.2f}]. These are descriptive uncertainty summaries
for the fixed corpus. Sparse evaluation is faster in {summary['faster_count']} of
{len(rows)} cases, while {summary['slower_or_equal_count']} cases are slower or equal.
The full speedup range is {summary['minimum_speedup']:.2f}--{summary['maximum_speedup']:.2f}$\\times$.
Figure~\\ref{{fig:results}} retains these slowdowns rather than filtering dense support.

\\begin{{figure}}[t]
\\centering
\\includegraphics[width=\\linewidth]{{public-results.png}}
\\caption{{Left: all {len(rows)} paired runtime comparisons, using the fastest of three dense
implementations per input. Right: threshold-sampling error on the same fixed score vectors.
Zero errors are displayed at $10^{{-16}}$ for the logarithmic axis.}}
\\label{{fig:results}}
\\end{{figure}}

\\begin{{table}}[htbp]
\\centering
\\begin{{tabular}}{{lrrrr}}
\\toprule
Metric & Median error & 95th percentile & Maximum error & Reversals / pairs \\\\
\\midrule
"""
    for metric in ["ROC", "PR"]:
        m = metric_summary[metric]
        body += f"VUS-{metric} & ${tex_number(m['absolute_error_median'])}$ & ${tex_number(m['absolute_error_p95'])}$ & ${tex_number(m['absolute_error_max'])}$ & {m['strict_reversals']} / {m['paired_comparisons']} \\\\\n"
    body += "\\bottomrule\n\\end{tabular}\n\\caption{Errors are absolute differences between the same metric at 250 sampled thresholds and all thresholds. Reversals require strict opposite order in both calculations.}\n\\label{tab:sampling}\n\\end{table}\n\n"
    for metric in ["ROC", "PR"]:
        m = metric_summary[metric]
        body += f"For VUS-{metric}, strict reversals occur on {m['affected_unique_series']} unique series across {len(m['affected_families'])} families, and the unique top model changes in {m['unique_top_model_changes']} of {len(by_case)} series/width cases. Exact and sampled comparisons contain {m['exact_ties']} and {m['sampled_ties']} ties, respectively.\n\n"
    example = summary["largest_pr_error_example"]
    body += f"The largest observed PR discrepancy occurs on the {example['n']:,}-point UCR HumanActivity series with Time-MoE scores and $L={example['max_buffer']}$: exact VUS-PR is {example['exact'][1]:.6f}, versus {example['sampled250'][1]:.6f} at 250 thresholds. The scores are unchanged between calculations.\n\n"
    body += "On the bounded 12-series NAB external comparison, the median speed ratios relative to compiled sparse evaluation are "
    body += f"{external_summary['dtaianomaly_exact']['median_speedup']:.2f}$\\times$ for full-threshold dtaianomaly, {external_summary['dtaianomaly250']['median_speedup']:.2f}$\\times$ for 250-threshold dtaianomaly, and {external_summary['official250']['median_speedup']:.2f}$\\times$ for official 250-threshold evaluation. The latter two compare exact computation with a coarser approximation. These results do not establish the same advantage on other families or against the unavailable accelerated VUS implementation.\n"
    if (ART / "scaling_final.json").exists():
        scaling = json.loads((ART / "scaling_final.json").read_text())["rows"]
        largest = scaling[-1]
        body += f"\nIn the frozen fixed-support scaling experiment ($Q=102$, $L=30$), the one-million-point case takes {largest['median_seconds']['sparse_numba']:.4f} seconds for compiled sparse evaluation, an {largest['speedup_vs_fastest_dense']:.2f}$\\times$ speedup over the fastest dense implementation, with five randomized-order repetitions.\n"
    if (ART / "mechanism_results.json").exists():
        mechanism = json.loads((ART / "mechanism_results.json").read_text())
        mechanism_receipt = json.loads((ART / "mechanism_results/run_receipt.json").read_text())
        if hashlib.sha256((ART / "mechanism_results.json").read_bytes()).hexdigest() != mechanism_receipt["results_sha256"]:
            raise RuntimeError("Mechanism result changed after verification")
        if hashlib.sha256((ART / "mechanism_results/raw_cases.jsonl").read_bytes()).hexdigest() != mechanism_receipt["raw_cases_sha256"]:
            raise RuntimeError("Mechanism raw records changed after verification")
        for relative, expected in mechanism["source_sha256"].items():
            if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
                raise RuntimeError(f"Mechanism dependency changed: {relative}")
        if mechanism["status"] != "complete" or mechanism["summary"]["max_parity_error"] > 1e-11:
            raise RuntimeError("Mechanism ablation did not pass")
        m = mechanism["summary"]
        count_ratio = m["ratios"]["speedup_current_vs_fullsort"]
        dense_ratio = m["ratios"]["speedup_current_vs_fastest_dense"]
        mechanism_figure = "figures/mechanism.readable.png" if (PAPER / "figures/mechanism.readable.png").exists() else "figures/mechanism.png"
        summary["mechanism_ablation"] = m
        body += f"""
\\subsection{{Mechanism and the density/width tradeoff}}
On the {m['cases']}-case synthetic grid, replacing full-score sorting with
support-score counting gives a geometric-mean end-to-end speedup of
{count_ratio['geometric_mean']:.2f}$\\times$ with the same integration kernel,
range {count_ratio['minimum']:.2f}--{count_ratio['maximum']:.2f}$\\times$.
The adapter deliberately holds support grouping and all other preparation
fixed, isolating the score-counting choice. Relative to the fastest dense
implementation, the complete sparse method has geometric-mean speedup
{dense_ratio['geometric_mean']:.2f}$\\times$, range
{dense_ratio['minimum']:.2f}--{dense_ratio['maximum']:.2f}$\\times$.
There are {dense_ratio['material_wins']} cases with at least a 1.1$\\times$
speed ratio and {dense_ratio['material_losses']} with ratio at most $1/1.1$.
The remaining cases lie between those thresholds. Thus the count-preprocessing
improvement is modest on this grid; sparse event integration supplies the
larger opportunity as support shrinks and the width range grows.

\\begin{{figure}}[t]
\\centering
\\includegraphics[width=\\linewidth]{{{mechanism_figure}}}
\\caption{{Mechanism ablation: each point is one predeclared synthetic cell,
using medians of three randomized repetitions. Support fraction $Q/n$ is
measured after expansion. The dense comparator is the fastest of three dense
implementations. The full-sort variant keeps support grouping and the compiled
sparse integration kernel fixed.}}
\\label{{fig:mechanism}}
\\end{{figure}}
"""
    if (ART / "external_supplement_summary.json").exists():
        supplement = json.loads((ART / "external_supplement_summary.json").read_text())
        if supplement["status"] != "PASS":
            raise RuntimeError("External cross-family supplement did not pass")
        record_path = ART / "external_supplement.jsonl"
        if hashlib.sha256(record_path.read_bytes()).hexdigest() != supplement["records_sha256"]:
            raise RuntimeError("Supplementary records changed after verification")
        for relative, expected in {**supplement["source_sha256"], **supplement["input_sha256"]}.items():
            if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
                raise RuntimeError(f"Supplementary dependency changed: {relative}")
        supplement_rows = [json.loads(line) for line in record_path.read_text().splitlines()]
        summary["external_crossfamily"] = supplement
        body += f"""
\\subsection{{Published implementation across source families}}
The post-review supplement selects the shortest and median-length series
within each family, deduplicating coincident choices. It contains
{supplement['series']} full-length series from all {supplement['families']}
families, uses Chronos-Bolt base scores and $L=30$, and preserves all vectors.
Methods run in a seeded random order, with three repetitions per method.
Each call has a ten-second post-warmup time limit; late or unfinished calls
are recorded as right-censored. Compilation and subprocess startup are
excluded. Table~\\ref{{tab:external}} reports speed ratios only for completed
pairs, whose subset differs across threshold modes. No numerical speed ratio
is imputed for a censored result.

\\begin{{table}}[htbp]
\\centering
\\begin{{tabular}}{{lrrrr}}
\\toprule
dtaianomaly mode & Completed & Censored & Families represented & Median ratio \\\\
\\midrule
"""
        for key, label in [("dtaianomaly250", "250 thresholds"), ("dtaianomaly_exact", "All thresholds")]:
            stats = supplement["comparisons"][key]
            complete_families = {r["family"] for r in supplement_rows if r["methods"][key]["status"] == "COMPLETE" and r["methods"]["sparse_numba"]["status"] == "COMPLETE"}
            ratio = stats["median_ratio_on_complete_pairs"]
            ratio_tex = "--" if ratio is None else f"{ratio:.2f}$\\times$"
            body += f"{label} & {stats['paired_complete']} & {stats['timeout']} & {len(complete_families)} & {ratio_tex} \\\\\n"
        body += f"""\\bottomrule
\\end{{tabular}}
\\caption{{Actual pinned dtaianomaly code on {supplement['series']} source-stratified
full-length inputs. Ratios divide the published baseline's median time by
compiled sparse exact evaluation. The 250-threshold row compares an
approximation with exact computation. Completion-conditioned medians are
not full-corpus runtime estimates. Family counts require at least one completed
pair within the family.}}
\\label{{tab:external}}
\\end{{table}}

The maximum absolute discrepancy for returned outputs, compared with the
corresponding exact or 250-threshold main result, is
${tex_number(supplement['max_error'])}$. All selection, timeout, environment,
and per-call receipts are retained.
"""
    (ART / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
    (PAPER / "result_body.tex").write_text(body)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
