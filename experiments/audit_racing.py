"""Post-run independent audit of incremental PR model-racing measurements."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics

from advancement_data_gate import validate_advancement_data
from audit_selection import compare_tree, digest, exact_winners, finite_number, names, require, value_map

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("sparse_exact", "dense_direct", "dense_nearest", "race_prune", "race_no_prune")
RACING = ("race_prune", "race_no_prune")
TIE = 1e-10
MARGIN = 3e-10
REQUIRED_SOURCES = {
    "experiments/benchmark_racing.py", "experiments/benchmark_advancement.py",
    "src/sparse_vus/racing.py", "src/sparse_vus/selection.py", "src/sparse_vus/certified.py",
    "src/sparse_vus/core.py", "src/sparse_vus/compiled.py",
}


def audit_racing_records(rows, protocol):
    require(protocol["models_per_case"] == 3 and protocol["repetitions"] == 3,
            "Unexpected racing coverage/repetition contract")
    require(protocol["exact_parity_tolerance"] == 1e-11
            and protocol["float64_containment_tolerance"] == TIE, "Unexpected racing numeric contract")
    require(len(rows) == protocol["cases"] and bool(rows), "Incomplete racing coverage")
    keys = [(row["series"], row["max_buffer"]) for row in rows]
    require(keys == sorted(keys) and len(set(keys)) == len(keys), "Duplicate or unordered racing cases")
    key_hash = hashlib.sha256(json.dumps(keys, separators=(",", ":")).encode()).hexdigest()
    require(key_hash == protocol["selection_sha256"], "Racing selection hash mismatch")
    expanded, max_error, max_slack = [], 0., 0.
    for row in rows:
        models = sorted(row["score_sha256"])
        width = row["max_buffer"]
        require(len(models) == 3 and all(isinstance(m, str) for m in models), "Racing model coverage mismatch")
        require(type(width) is int and width in (30, 100, 300), "Unexpected racing width")
        for key in ("values", "seconds", "median_seconds"):
            require(set(row[key]) == set(METHODS), f"Racing method coverage mismatch: {key}")
        for method in METHODS:
            calls = row["seconds"][method]
            require(len(calls) == 3 and all(finite_number(v) and v > 0 for v in calls),
                    "Invalid racing timing")
            require(row["median_seconds"][method] == statistics.median(calls), "Forged racing median")
        reference = row["values"]["sparse_exact"]
        value_map(reference["pr"], models)
        winners = exact_winners(reference["pr"])
        require(reference["selected"] == winners, "Reference racing ties are inconsistent")
        for method in ("sparse_exact", "dense_direct", "dense_nearest"):
            result = row["values"][method]
            value_map(result["pr"], models)
            require(result["selected"] == exact_winners(result["pr"]) == winners,
                    "Compiled exact selection mismatch")
            error = max(abs(result["pr"][m] - reference["pr"][m]) for m in models)
            max_error = max(max_error, error)
            require(error <= protocol["exact_parity_tolerance"], "Compiled exact PR parity failure")
        require(type(row["exact_unique_winner"]) is bool
                and row["exact_unique_winner"] == (len(winners) == 1), "Incorrect racing winner flag")
        for method in RACING:
            result = row["values"][method]
            for key in ("selected", "candidates", "pruned"):
                names(result[key], models, nonempty=key != "pruned")
            require(result["selected"] == winners, "Wrong racing selection or lost exact tie")
            require(set(result["bounds"]) == set(models), "Missing racing model bound")
            bounds = result["bounds"]
            unique_total, curves_total, full_models = 0, 0, []
            for model, bound in bounds.items():
                lower, upper = bound["pr_lower"], bound["pr_upper"]
                require(finite_number(lower) and finite_number(upper)
                        and -TIE <= lower <= upper <= 1 + TIE, "Invalid racing interval")
                truth = reference["pr"][model]
                require(lower - TIE <= truth <= upper + TIE, "Racing interval excludes exact PR")
                max_slack = max(max_slack, lower - truth, truth - upper)
                widths = bound["evaluated_widths"]
                require(isinstance(widths, list) and widths == sorted(set(widths)) and bool(widths)
                        and all(type(w) is int and 0 <= w <= width for w in widths),
                        "Invalid per-model racing widths")
                require(type(bound["curve_evaluations"]) is int and bound["curve_evaluations"] >= len(widths),
                        "Invalid per-model curve accounting")
                is_full = len(widths) == width + 1
                require(type(bound["exact"]) is bool and bound["exact"] == is_full,
                        "False fully evaluated model claim")
                if is_full:
                    require(lower == upper, "Fully evaluated PR interval is not a singleton")
                    full_models.append(model)
                unique_total += len(widths)
                curves_total += bound["curve_evaluations"]
            value_map(result["exact_pr"], full_models)
            for model, value in result["exact_pr"].items():
                require(abs(value - reference["pr"][model]) <= protocol["exact_parity_tolerance"]
                        and abs(value - bounds[model]["pr_lower"]) <= protocol["exact_parity_tolerance"],
                        "Fully evaluated PR value mismatch")
            for key in ("full_evaluation_count", "initial_unique_widths", "initial_curve_evaluations",
                        "refinement_steps", "total_unique_widths", "total_curve_evaluations"):
                require(type(result[key]) is int and result[key] >= 0, f"Invalid racing count: {key}")
            require(result["full_evaluation_count"] == len(full_models), "Miscounted fully evaluated models")
            require(result["total_unique_widths"] == unique_total
                    and result["total_curve_evaluations"] == curves_total,
                    "Aggregate racing work differs from per-model work")
            require(unique_total == result["initial_unique_widths"] + result["refinement_steps"],
                    "One-new-width-per-refinement invariant failed")
            require(len(models) <= result["initial_unique_widths"] <= unique_total
                    and result["initial_curve_evaluations"] >= result["initial_unique_widths"]
                    and curves_total >= result["initial_curve_evaluations"] + result["refinement_steps"],
                    "Initial/refined racing work accounting is impossible")
            early = [m for m in models if all(
                bounds[m]["pr_lower"] > bounds[other]["pr_upper"] + MARGIN
                for other in models if other != m)]
            require(len(early) <= 1 and type(result["early_winner"]) is bool
                    and result["early_winner"] == bool(early), "Racing early-winner separation mismatch")
            if early:
                candidates = early
                require(result["selected"] == early, "Wrong separated racing winner")
            else:
                highest_lower = max(bound["pr_lower"] for bound in bounds.values())
                candidates = (models if method == "race_no_prune" else
                              [m for m in models if bounds[m]["pr_upper"] >= highest_lower - MARGIN])
                require(all(bounds[m]["exact"] for m in candidates),
                        "Unresolved race stopped before all surviving models were exact")
                require(result["selected"] == exact_winners({m: result["exact_pr"][m] for m in candidates}),
                        "Survivor exact values disagree with selected models")
            require(result["candidates"] == candidates
                    and result["pruned"] == [m for m in models if m not in candidates],
                    "Racing candidate/pruning policy mismatch")
            exact_best = max(reference["pr"].values())
            require(all(exact_best - reference["pr"][m] > TIE for m in result["pruned"]),
                    "A pruned model is an exact winner or tolerance tie")
        # The two policies must start with the same endpoint work. Their final
        # bounds and refinements may differ, which is the intended ablation.
        for key in ("initial_unique_widths", "initial_curve_evaluations"):
            require(row["values"][RACING[0]][key] == row["values"][RACING[1]][key],
                    "Racing ablation changed initial preparation work")
        expanded.extend({
            "series": row["series"], "family": row["family"], "n": row["n"], "max_buffer": width,
            "model": model, "label_sha256": row["label_sha256"],
            "score_sha256": row["score_sha256"][model],
        } for model in models)
    by_width, work = {}, {}
    for width in sorted({row["max_buffer"] for row in rows}):
        group = [row for row in rows if row["max_buffer"] == width]
        output = {
            "cases": len(group),
            "exact_unique_winner_cases": sum(row["exact_unique_winner"] for row in group),
            "sum_case_median_seconds": {
                method: sum(row["median_seconds"][method] for row in group) for method in METHODS},
        }
        work[str(width)] = {}
        for method in RACING:
            output[method] = {
                "early_winners": sum(row["values"][method]["early_winner"] for row in group),
                "full_evaluations": sum(row["values"][method]["full_evaluation_count"] for row in group),
                "ratios_by_comparator": {
                    comparator: {
                        "median": float(statistics.median(
                            row["median_seconds"][comparator] / row["median_seconds"][method] for row in group)),
                        "faster_cases": sum(row["median_seconds"][comparator] > row["median_seconds"][method]
                                            for row in group),
                    } for comparator in METHODS if comparator != method},
            }
            work[str(width)][method] = {
                "initial_unique_widths": sum(row["values"][method]["initial_unique_widths"] for row in group),
                "total_unique_widths": sum(row["values"][method]["total_unique_widths"] for row in group),
                "total_curve_evaluations": sum(row["values"][method]["total_curve_evaluations"] for row in group),
                "refinement_steps": sum(row["values"][method]["refinement_steps"] for row in group),
                "median_unique_width_fraction": statistics.median(
                    row["values"][method]["total_unique_widths"] / (3 * (width + 1)) for row in group),
                "median_actual_curve_fraction": statistics.median(
                    row["values"][method]["total_curve_evaluations"] / (3 * (width + 1)) for row in group),
                "early_winners_with_all_models_fully_evaluated": sum(
                    row["values"][method]["early_winner"] and row["values"][method]["full_evaluation_count"] == 3
                    for row in group),
            }
        by_width[str(width)] = output
    return {"cases": len(rows), "max_exact_pr_error": max_error, "max_enclosure_slack": max_slack,
            "by_width": by_width, "work": work}, expanded


def audit_racing_run(path, *, root=None):
    path, root = Path(path), Path(root or ROOT).resolve()
    protocol = json.loads((path / "protocol.json").read_text())
    environment = json.loads((path / "environment.json").read_text())
    summary = json.loads((path / "summary.json").read_text())
    raw = (path / "measurements.jsonl").read_bytes()
    raw_hash = hashlib.sha256(raw).hexdigest()
    require(summary["status"] == "PASS" and summary["violations"] == [], "Racing run did not pass")
    require(summary["measurements_sha256"] == raw_hash, "Racing raw-result hash mismatch")
    require(environment["protocol_sha256"] == digest(path / "protocol.json"), "Racing protocol binding mismatch")
    require(set(environment["source_sha256"]) == REQUIRED_SOURCES, "Racing source coverage mismatch")
    for relative, expected in environment["source_sha256"].items():
        source = (root / relative).resolve()
        require(source.is_relative_to(root) and source.is_file(), "Invalid racing source path")
        require(digest(source) == expected, f"Racing source changed: {relative}")
    require(environment["threads"] == 1 and all(
        pool["num_threads"] == 1 for pool in environment["threadpool_info"]), "Invalid racing thread configuration")
    require(set(environment["warmup_seconds"]) == set(METHODS) and all(
        finite_number(value) and value >= 0 for value in environment["warmup_seconds"].values()),
        "Missing racing warmup")
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    result, expanded = audit_racing_records(rows, protocol)
    require(summary["cases"] == result["cases"], "Racing summary count differs")
    compare_tree(summary["by_width"], result["by_width"], "racing_by_width")
    provenance = validate_advancement_data(expanded, mode="certified", root=root)
    require(provenance["status"] == "PASS", "Racing data provenance did not pass")
    return {
        "status": "PASS", "completed_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Post-run independent receipt reconstruction; no metric or racing kernels rerun.",
        "measurements_sha256": raw_hash, "protocol_sha256": digest(path / "protocol.json"),
        "environment_sha256": digest(path / "environment.json"),
        "producer_summary_sha256": digest(path / "summary.json"),
        "auditor_sha256": digest(Path(__file__)),
        "helper_sha256": digest(Path(__file__).with_name("audit_selection.py")),
        "source_sha256": environment["source_sha256"], "reconstructed": result, "data_provenance": provenance,
        "checks": ["frozen hashes and complete source set", "complete model/case input identity",
                   "all exact PR/tie choices", "all interval containments",
                   "every pruned model below the exact best beyond tie tolerance",
                   "full-evaluation flags and exact-PR maps", "per-model and aggregate width/curve counts",
                   "one unseen width per refinement", "3e-10 early/pruning semantics",
                   "finite whole-call timings and exact medians", "all producer summary aggregates"],
        "limitations": ["Floating-point checks are numerical, not directed-rounding proofs.",
                        "Initial per-model width IDs and timing-order trace are not recorded.",
                        "An early_winner flag need not imply fewer evaluated widths."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_racing_run(args.run)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
