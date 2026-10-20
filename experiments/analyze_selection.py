"""Generate the decision-latency report and paper table from audited runs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics

import numpy as np

from analyze_advancement import ratio_stats
from audit_selection import audit_selection_run
from audit_racing import audit_racing_run

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    return [json.loads(line) for line in
            (path / "measurements.jsonl").read_text().splitlines()]


def identities(rows):
    return [(r["series"], r["max_buffer"], r["label_sha256"],
             sorted(r["score_sha256"].items())) for r in rows]


def summarize(rows, method):
    result = {}
    for width in (30, 100, 300):
        group = [r for r in rows if r["max_buffer"] == width]
        names = ("sparse_exact", "dense_direct", "dense_nearest")
        entry = {
            "cases": len(group),
            "vs_sparse_exact": ratio_stats(group, lambda r:
                r["median_seconds"]["sparse_exact"] / r["median_seconds"][method]),
            "vs_fastest_tested_exact": ratio_stats(group, lambda r:
                min(r["median_seconds"][k] for k in names) / r["median_seconds"][method]),
            "by_exact_comparator": {
                name: ratio_stats(group, lambda r, name=name:
                    r["median_seconds"][name] / r["median_seconds"][method])
                for name in names},
            "median_milliseconds": {
                name: 1000 * statistics.median(r["median_seconds"][name] for r in group)
                for name in (*names, method)},
            "sum_case_median_seconds": {
                name: sum(r["median_seconds"][name] for r in group)
                for name in (*names, method)},
            "early_winners": sum(r["values"][method]["early_winner"] for r in group),
            "wrong_selections": sum(r["values"][method]["selected"] !=
                                    r["values"]["sparse_exact"]["selected"] for r in group),
        }
        if method.startswith("race"):
            entry.update(
                full_evaluations=sum(r["values"][method]["full_evaluation_count"] for r in group),
                median_unique_width_fraction=statistics.median(
                    r["values"][method]["total_unique_widths"] / (3 * (width + 1))
                    for r in group),
                median_curve_evaluation_fraction=statistics.median(
                    r["values"][method]["total_curve_evaluations"] / (3 * (width + 1))
                    for r in group),
            )
        else:
            entry["exact_fallback_evaluations"] = sum(
                r["values"][method]["exact_fallback_count"] for r in group)
        result[str(width)] = entry
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--mac-racing", type=Path, required=True)
    parser.add_argument("--linux-racing", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--paper-output", type=Path, default=ROOT / "paper/selection_results.tex")
    args = parser.parse_args()
    report = {"status": "PASS", "audits": {}, "fixed_tolerance": {}, "racing": {}}
    report["audits"]["fixed_tolerance"] = audit_selection_run(args.selection)
    fixed = read_rows(args.selection)
    for method in ("certificate_prune", "certificate_no_prune"):
        report["fixed_tolerance"][method] = summarize(fixed, method)
    report["fixed250_wrong_selections_by_width"] = {
        str(width): sum(r["fixed250_wrong_selection"] for r in fixed if r["max_buffer"] == width)
        for width in (30, 100, 300)}
    report["fixed250_unique_winner_disagreements_by_width"] = {
        str(width): sum(r["fixed250_wrong_selection"] and r["exact_unique_winner"]
                       for r in fixed if r["max_buffer"] == width)
        for width in (30, 100, 300)}
    races = {}
    for label, path, machine in (
        ("macOS-arm64", args.mac_racing, "arm64"),
        ("Linux-x86", args.linux_racing, "x86_64"),
    ):
        report["audits"][label] = audit_racing_run(path)
        rows = read_rows(path)
        if identities(rows) != identities(fixed):
            raise ValueError("Cross-run cases or source bytes differ")
        environment = json.loads((path / "environment.json").read_text())
        if environment["machine"] != machine:
            raise ValueError("Unexpected machine architecture")
        prefix = "macOS-" if label == "macOS-arm64" else "Linux-"
        if not environment["platform"].startswith(prefix):
            raise ValueError("Unexpected operating system")
        for reference, row in zip(fixed, rows):
            if reference["values"]["sparse_exact"]["selected"] != row["values"]["sparse_exact"]["selected"]:
                raise ValueError("Cross-platform exact selection differs")
        races[label] = rows
        report["racing"][label] = {
            method: summarize(rows, method) for method in ("race_prune", "race_no_prune")}
        report["racing"][label]["pruning_ablation"] = {
            str(width): ratio_stats(
                [r for r in rows if r["max_buffer"] == width],
                lambda r: r["median_seconds"]["race_no_prune"] / r["median_seconds"]["race_prune"])
            for width in (30, 100, 300)}
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output / "analysis.json"
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    sha = hashlib.sha256(output.read_bytes()).hexdigest()

    lines = [
        "% Generated by experiments/analyze_selection.py",
        f"% Analysis SHA-256: {sha}",
        r"\subsection{Complete model-selection workloads}",
        r"We select the maximum exact PR among all three released score vectors,",
        r"retaining every model within $10^{-10}$ of the maximum.",
        r"Both experiments use the same fixed 42-series metadata selection and",
        r"$L\in\{30,100,300\}$ (126 tasks), with no case exclusions.",
        r"Every timed call includes all model preparation and all subsequent",
        r"refinement or fallback; score loading and warmed JIT compilation are",
        r"excluded. Model training and inference are not measured.",
        r"Width 300 remains an explicit stress regime.",
        r"\paragraph{Fixed tolerance with exact fallback.}",
        r"At initial half-width $0.01$, the selector's median speed ratios",
        r"against sparse exact selection are",
    ]
    vals = [report["fixed_tolerance"]["certificate_prune"][str(w)]["vs_sparse_exact"]["median"]
            for w in (30, 100, 300)]
    fallback = lambda method: "/".join(str(
        report["fixed_tolerance"][method][str(w)]["exact_fallback_evaluations"]
    ) for w in (30, 100, 300))
    disagreements = "/".join(str(report["fixed250_wrong_selections_by_width"][str(w)])
                             for w in (30, 100, 300))
    unique_disagreements = "/".join(str(
        report["fixed250_unique_winner_disagreements_by_width"][str(w)])
        for w in (30, 100, 300))
    lines += [
        f"${vals[0]:.3f}\\times$, ${vals[1]:.3f}\\times$, and ${vals[2]:.3f}\\times$.",
        r"All 126 decisions agree, but the complete selector is slower at every",
        r"width in the median. Pruning reduces exact fallback model evaluations",
        f"from {fallback('certificate_no_prune')} to {fallback('certificate_prune')}, "
        "without recovering this overhead.",
        f"The fixed-250 comparator changes the selected set in {disagreements} tasks.",
        f"Of these, {unique_disagreements} have a unique exact winner; the remaining",
        r"case at each width breaks an exact three-way tie.",
        r"\paragraph{Incremental PR racing.}",
        r"The follow-up removes the fixed accuracy target and reuses each model's",
        r"prepared state (Section~\ref{sec:racing}). This design was chosen after",
        r"observing the fixed-tolerance overhead; it is not a preregistered",
        r"independent generalization study. Fresh timings on both architectures",
        r"retain the same inputs and separate each executable exact comparator.",
        r"Every racing decision agrees with exact selection on both platforms.",
        r"\begin{table}[t]\centering",
        r"\begin{tabular}{llrrrrrr}\toprule",
        r"Platform & $L$ & vs.\ sparse & vs.\ oracle & wins/42 & exact ms & race ms & widths \\\midrule",
    ]
    for label, short in (("macOS-arm64", "macOS"), ("Linux-x86", "Linux")):
        for width in (30, 100, 300):
            s = report["racing"][label]["race_prune"][str(width)]
            lines.append(
                f"{short} & {width} & {s['vs_sparse_exact']['median']:.3f}"
                f" & {s['vs_fastest_tested_exact']['median']:.3f}"
                f" & {s['vs_fastest_tested_exact']['faster_cases']}"
                f" & {s['median_milliseconds']['sparse_exact']:.2f}"
                f" & {s['median_milliseconds']['race_prune']:.2f}"
                f" & {100*s['median_unique_width_fraction']:.1f}\\% \\\\")
    lines += [
        r"\bottomrule\end{tabular}",
        r"\caption{Incremental PR selection, 42 tasks per row. Ratios above one",
        r"favor racing. The oracle chooses the fastest of three separately",
        r"measured compiled exact methods per task; it is not deployable.",
        r"Wins compare racing to that oracle; latency columns are medians in",
        r"milliseconds for sparse exact and racing. Widths is the median fraction",
        r"of the $3(L+1)$ distinct model-width queries evaluated. Recomputed",
        r"endpoint curves are separately counted in the released records.}",
        r"\label{tab:selection}\end{table}",
    ]
    lines.append(r"\paragraph{Median gain versus total cost.}")
    for label, short in (("macOS-arm64", "macOS"), ("Linux-x86", "Linux")):
        s = report["racing"][label]["race_prune"]["300"]["sum_case_median_seconds"]
        relation = "more" if s["race_prune"] > s["sparse_exact"] else "less"
        lines.append(
            f"At width 300 on {short}, summing the 42 case medians gives "
            f"{s['race_prune']:.3f}\\,s for racing versus "
            f"{s['sparse_exact']:.3f}\\,s for sparse exact evaluation "
            f"({relation} total time).")
    lines.append(
        r"Thus the distribution median and the total workload cost must be read "
        r"separately; a positive median speed ratio does not establish net time savings.")
    lines += [
        r"The no-pruning ablation retains the separated-winner rule and refines",
        r"all models when no winner separates. Its median time divided by the",
        r"pruning variant's time, at the three increasing widths, is",
    ]
    for label, short in (("macOS-arm64", "macOS"), ("Linux-x86", "Linux")):
        numbers = [report["racing"][label]["pruning_ablation"][str(w)]["median"] for w in (30,100,300)]
        lines.append(f"{short}: ${numbers[0]:.3f}$, ${numbers[1]:.3f}$, ${numbers[2]:.3f}$;")
    lines += [
        r"these values isolate the incremental effect of pruning in this workload.",
        r"All bound-separation decisions are numerical audits under the stated",
        r"$10^{-10}$ enclosure allowance, not formal Float64 certificates.",
        r"The artifact includes absolute totals, series-clustered intervals,",
        r"full-evaluation counts, and every slower task.",
    ]
    args.paper_output.write_text("\n".join(lines) + "\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.6), constrained_layout=True)
    for label, rows in races.items():
        ratios = np.sort([min(r["median_seconds"][m] for m in
                             ("sparse_exact", "dense_direct", "dense_nearest"))
                          / r["median_seconds"]["race_prune"] for r in rows])
        axes[0].plot(ratios, np.arange(1, len(rows)+1)/len(rows), label=label, lw=2)
        widths = (30, 100, 300)
        axes[1].plot(widths, [report["racing"][label]["race_prune"][str(w)]
                             ["vs_sparse_exact"]["median"] for w in widths],
                     marker="o", label=label, lw=2)
    axes[0].set(xscale="log", xlabel="Fastest tested exact time / racing time",
                ylabel="Fraction of tasks", title="126 complete three-model tasks")
    axes[0].axvline(1, color="0.5", ls="--", lw=1)
    axes[1].set(xscale="log", yscale="log", xlabel="Maximum buffer width",
                ylabel="Sparse exact time / racing time", title="Median decision speed ratio")
    axes[1].axhline(1, color="0.5", ls="--", lw=1)
    for ax in axes:
        ax.legend(frameon=False)
        ax.grid(alpha=0.15)
    fig.savefig(args.output / "selection.png", dpi=220)
    fig.savefig(args.output / "selection.pdf")
    plt.close(fig)
    print(json.dumps({"status": "PASS", "analysis_sha256": sha,
                      "output": str(output), "paper": str(args.paper_output)}, indent=2))


if __name__ == "__main__":
    main()
