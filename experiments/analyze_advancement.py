"""Reconstruct advancement findings only from completed, hash-bound runs."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def read_run(path):
    summary = json.loads((path / "summary.json").read_text())
    raw = (path / "measurements.jsonl").read_bytes()
    if summary["status"] != "PASS":
        raise ValueError(f"non-PASS run: {path}")
    if hashlib.sha256(raw).hexdigest() != summary["measurements_sha256"]:
        raise ValueError(f"changed run: {path}")
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    if len(rows) != summary["cases"]:
        raise ValueError("incomplete case coverage")
    keys = [(r["series"], r["model"], r["max_buffer"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate case")
    protocol = json.loads((path / "protocol.json").read_text())
    environment = json.loads((path / "environment.json").read_text())
    if environment["protocol_sha256"] != hashlib.sha256(
        (path / "protocol.json").read_bytes()
    ).hexdigest():
        raise ValueError("protocol/environment binding mismatch")
    for name, expected in environment["source_sha256"].items():
        source = (ROOT / name).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise ValueError(f"missing or invalid bound source: {name}")
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError(f"source differs from measured source: {name}")
    expected_methods = (
        {"sparse_exact", "fast_vus_exact_pr", "dense_direct", "dense_nearest", "dense_numpy"}
        if protocol["mode"] == "baseline" else
        {"sparse_exact", "certified_0.01", "certified_0.001"}
    )
    selected_hash = hashlib.sha256(
        json.dumps(keys, separators=(",", ":")).encode()).hexdigest()
    if selected_hash != protocol["selection_sha256"]:
        raise ValueError("selection mismatch")
    for r in rows:
        if any(set(r[key]) != expected_methods
               for key in ("seconds", "median_seconds", "values")):
            raise ValueError("method coverage mismatch")
        for name, calls in r["seconds"].items():
            if len(calls) != protocol["repetitions"] or not all(
                np.isfinite(v) and v > 0 for v in calls
            ):
                raise ValueError("invalid timing")
            if float(np.median(calls)) != r["median_seconds"][name]:
                raise ValueError("median mismatch")
        exact = r["values"]["sparse_exact"]
        if len(exact) != 2 or not all(np.isfinite(v) and -1e-10 <= v <= 1 + 1e-10
                                     for v in exact):
            raise ValueError("invalid exact result")
        for name, value in r["values"].items():
            if name.startswith("certified"):
                bounds = [value[k] for k in ("roc_lower", "roc_upper", "pr_lower", "pr_upper")]
                if not all(np.isfinite(v) for v in bounds):
                    raise ValueError("nonfinite interval")
                if not (bounds[0] <= bounds[1] and bounds[2] <= bounds[3]):
                    raise ValueError("reversed interval")
                tol = protocol["float64_containment_tolerance"]
                if not (bounds[0] - tol <= exact[0] <= bounds[1] + tol and
                        bounds[2] - tol <= exact[1] <= bounds[3] + tol):
                    raise ValueError("interval excludes exact value")
                half_width = max(bounds[1] - bounds[0], bounds[3] - bounds[2]) / 2
                if half_width > float(name.split("_")[1]) + 1e-12:
                    raise ValueError("requested interval tolerance not reached")
                if value["estimate"] != [(bounds[0] + bounds[1]) / 2,
                                          (bounds[2] + bounds[3]) / 2]:
                    raise ValueError("midpoint mismatch")
                widths = value["evaluated_widths"]
                if (widths != sorted(set(widths)) or
                    not all(isinstance(w, int) and 0 <= w <= r["max_buffer"] for w in widths) or
                    value["total_widths"] != r["max_buffer"] + 1 or
                    value["exact"] != (len(widths) == value["total_widths"]) or
                    value["curve_evaluations"] < len(widths)):
                    raise ValueError("invalid width accounting")
                expected_error = float(np.max(np.abs(np.asarray(value["estimate"]) - exact)))
                if r["checks"][name]["max_midpoint_error"] != expected_error:
                    raise ValueError("recorded midpoint error mismatch")
            else:
                if len(value) != 2 or (
                    name == "fast_vus_exact_pr" and value[0] is not None
                ):
                    raise ValueError("unexpected output contract")
                for index, (a, b) in enumerate(zip(value, exact)):
                    if a is None and name == "fast_vus_exact_pr" and index == 0:
                        continue
                    if a is None or not np.isfinite(a) or abs(a - b) > protocol["exact_parity_tolerance"]:
                        raise ValueError("exact comparison parity failure")
    return rows, summary


def ratio_stats(rows, ratio):
    values = np.asarray([ratio(r) for r in rows])
    by_series = defaultdict(list)
    by_family = defaultdict(list)
    for row, value in zip(rows, values):
        by_series[row["series"]].append(float(np.log(value)))
        by_family[row["family"]].append(float(np.log(value)))
    def clustered_ci(groups):
        # Resample clusters, preserving all observations within each draw.
        sums = np.array([sum(v) for _, v in sorted(groups.items())])
        counts = np.array([len(v) for _, v in sorted(groups.items())])
        rng = np.random.default_rng(202610202)
        draws = rng.integers(0, len(sums), size=(2000, len(sums)))
        means = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
        return np.exp(np.quantile(means, [0.025, 0.975])).tolist()
    return {
        "cases": len(rows),
        "median": float(np.median(values)),
        "geomean": float(np.exp(np.mean(np.log(values)))),
        "min": float(values.min()), "max": float(values.max()),
        "faster_cases": int(np.sum(values > 1)),
        "series_clustered_geomean_ci95": clustered_ci(by_series),
        "family_clustered_geomean_ci95": clustered_ci(by_family),
        "families": {k: {"cases": len(v), "geomean": float(np.exp(np.mean(v)))}
                     for k, v in sorted(by_family.items())},
    }


def certify_rankings(rows, method):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["series"], row["max_buffer"])].append(row)
    pairs = certified_pairs = wrong_pairs = certified_winners = wrong_winners = 0
    decision_margin = 2e-10  # Sum of the two independent containment allowances.
    for group in groups.values():
        if len(group) != 3:
            raise ValueError("model coverage mismatch")
        for i in range(3):
            a = group[i]
            ba = a["values"][method]
            competitors = [group[j]["values"][method]["pr_upper"]
                           for j in range(3) if j != i]
            if ba["pr_lower"] > max(competitors) + decision_margin:
                certified_winners += 1
                if not all(a["values"]["sparse_exact"][1] >
                           group[j]["values"]["sparse_exact"][1] for j in range(3) if j != i):
                    wrong_winners += 1
            for j in range(i + 1, 3):
                b = group[j]
                bb = b["values"][method]
                pairs += 1
                direction = (1 if ba["pr_lower"] > bb["pr_upper"] + decision_margin else
                             -1 if bb["pr_lower"] > ba["pr_upper"] + decision_margin else 0)
                if direction:
                    certified_pairs += 1
                    actual = a["values"]["sparse_exact"][1] - b["values"]["sparse_exact"][1]
                    if direction * actual <= 0:
                        wrong_pairs += 1
    return {"model_pairs": pairs, "certified_pairs": certified_pairs,
            "incorrect_certified_pairs": wrong_pairs, "selection_cases": len(groups),
            "certified_unique_winners": certified_winners,
            "incorrect_certified_winners": wrong_winners,
            "decision_margin": decision_margin,
            "scope": "Numerical replay of real-arithmetic interval rule, not statistical "
                     "generalization or a formally outward-rounded floating-point proof."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mac-baseline", type=Path, required=True)
    parser.add_argument("--linux-baseline", type=Path, required=True)
    parser.add_argument("--certified", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"status": "PASS", "baseline": {}, "certified": {}, "data_provenance": {},
              "input_measurement_sha256": {}}
    from advancement_data_gate import validate_advancement_data
    baseline_rows = {}
    for name, path in [("macOS-arm64", args.mac_baseline), ("Linux-x86", args.linux_baseline)]:
        rows, summary = read_run(path)
        report["data_provenance"][name] = validate_advancement_data(rows, mode="baseline")
        environment = json.loads((path / "environment.json").read_text())
        if name == "macOS-arm64":
            if not (environment["platform"].startswith("macOS-") and environment["machine"] == "arm64"):
                raise ValueError("expected macOS arm64 environment")
        elif not (environment["platform"].startswith("Linux-") and
                  environment["machine"] in ("x86_64", "AMD64")):
            raise ValueError("expected Linux x86 environment")
        baseline_rows[name] = rows
        report["input_measurement_sha256"][name] = summary["measurements_sha256"]
        methods = ("fast_vus_exact_pr", "dense_direct", "dense_nearest", "dense_numpy")
        report["baseline"][name] = {
            "fast_vus": ratio_stats(rows, lambda r:
                r["median_seconds"]["fast_vus_exact_pr"] / r["median_seconds"]["sparse_exact"]),
            "fastest_tested": ratio_stats(rows, lambda r:
                min(r["median_seconds"][k] for k in methods) / r["median_seconds"]["sparse_exact"]),
            "max_pr_error_vs_fast_vus": max(
                abs(r["values"]["fast_vus_exact_pr"][1] - r["values"]["sparse_exact"][1]) for r in rows),
            "same_machine_isolated_evaluator_seconds": {
                "sparse_sum_of_case_medians": sum(r["median_seconds"]["sparse_exact"] for r in rows),
                "fast_vus_sum_of_case_medians": sum(r["median_seconds"]["fast_vus_exact_pr"] for r in rows),
            },
        }
    keys = lambda rows: [(r["series"], r["model"], r["max_buffer"],
                          r["label_sha256"], r["score_sha256"]) for r in rows]
    if keys(baseline_rows["macOS-arm64"]) != keys(baseline_rows["Linux-x86"]):
        raise ValueError("cross-platform inputs differ")
    rows, summary = read_run(args.certified)
    report["data_provenance"]["certified"] = validate_advancement_data(rows, mode="certified")
    report["input_measurement_sha256"]["certified"] = summary["measurements_sha256"]
    for method in ("certified_0.01", "certified_0.001"):
        by_width = {}
        for width in sorted({r["max_buffer"] for r in rows}):
            subset = [r for r in rows if r["max_buffer"] == width]
            stats = ratio_stats(subset, lambda r:
                r["median_seconds"]["sparse_exact"] / r["median_seconds"][method])
            stats["median_unique_width_fraction"] = float(np.median([
                len(r["values"][method]["evaluated_widths"]) / (width + 1) for r in subset]))
            stats["median_curve_evaluation_fraction"] = float(np.median([
                r["values"][method]["curve_evaluations"] / (width + 1) for r in subset]))
            stats["max_midpoint_error"] = max(
                r["checks"][method]["max_midpoint_error"] for r in subset)
            stats["rank_decisions"] = certify_rankings(subset, method)
            if (stats["rank_decisions"]["incorrect_certified_pairs"] or
                    stats["rank_decisions"]["incorrect_certified_winners"]):
                raise ValueError("false certified decision")
            by_width[str(width)] = stats
        report["certified"][method] = by_width
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "analysis.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.6), constrained_layout=True)
    for idx, (name, rr) in enumerate(baseline_rows.items()):
        ratios = np.sort([r["median_seconds"]["fast_vus_exact_pr"] /
                          r["median_seconds"]["sparse_exact"] for r in rr])
        axes[0].plot(ratios, np.arange(1, len(rr) + 1) / len(rr), label=name, lw=2)
    axes[0].set(xscale="log", xlabel="fast-VUS PR time / Sparse VUS ROC+PR time",
                ylabel="Fraction of cases", title="Exact evaluation, 2,100 paired cases")
    axes[0].axvline(1, color="0.5", ls="--", lw=1)
    axes[0].legend(frameon=False)
    for method, marker in [("certified_0.01", "o"), ("certified_0.001", "s")]:
        widths = sorted(int(w) for w in report["certified"][method])
        values = [report["certified"][method][str(w)]["median"] for w in widths]
        axes[1].plot(widths, values, marker=marker, lw=2,
                     label=f"half-width tolerance {method.split('_')[1]}")
    axes[1].set(xscale="log", yscale="log", xlabel="Maximum buffer width",
                ylabel="Exact time / bounded-evaluation time",
                title="Certified-width evaluation, 126 cases per width")
    axes[1].axhline(1, color="0.5", ls="--", lw=1)
    axes[1].legend(frameon=False, fontsize=8)
    for ax in axes:
        ax.grid(alpha=0.15)
    fig.savefig(args.output / "advancement.png", dpi=220)
    fig.savefig(args.output / "advancement.pdf")
    plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
