"""Report one independently audited PR-engine run; never pool different runs.

No metric execution, archive reads, or new bootstrap resampling occurs here.
Point estimates and all negative cases are reconstructed from the bound raw
records; confidence intervals come only from the completed independent audit.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
EXACT_V2 = ("sparse_pr", "dense_pr_direct", "sparse_both", "dense_nearest_both",
            "klein_pr", "benchopt_both", "radix_pr", "radix_both")
RACERS = ("v02_race", "fast_race", "fast_exact_completion", "fast_race_radix")
MATCHED = ("dense_pr_direct_radix", "dense_pr_nearest_radix")
SOURCES_V2 = {
    "experiments/benchmark_pr_engine.py", "experiments/benchmark_advancement.py",
    "experiments/advancement_data_gate.py", "experiments/fast_vus_adapter.py",
    "experiments/benchopt_vus_adapter.py", "src/sparse_vus/pr_compiled.py",
    "src/sparse_vus/fast_racing.py", "src/sparse_vus/racing.py",
    "src/sparse_vus/certified.py", "src/sparse_vus/selection.py",
    "src/sparse_vus/core.py", "src/sparse_vus/compiled.py", "src/sparse_vus/radix.py",
    ".cache/fast_vus/fast_vus.py", ".cache/benchopt_vus/metrics.py",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def same(actual, expected):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(), "Summary fields differ")
        for key in expected:
            same(actual[key], expected[key])
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), "Summary list differs")
        for a, b in zip(actual, expected):
            same(a, b)
    elif type(expected) is float:
        require(type(actual) in (int, float) and math.isfinite(actual)
                and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), "Summary numeric mismatch")
    else:
        require(type(actual) is type(expected) and actual == expected, "Summary value differs")


def quantile(values, q):
    values = sorted(values)
    index = (len(values) - 1) * q
    lo, hi = math.floor(index), math.ceil(index)
    return values[lo] + (values[hi] - values[lo]) * (index - lo)


def comparison(rows, reference, comparator):
    ratios = [r["median_seconds"][comparator] / r["median_seconds"][reference] for r in rows]
    families = defaultdict(list)
    regressions = []
    for row, ratio in zip(rows, ratios):
        families[row["family"]].append(math.log(ratio))
        if ratio < 1:
            regressions.append({"series": row["series"], "family": row["family"],
                                "max_buffer": row["max_buffer"], "ratio": ratio, "slowdown": 1 / ratio,
                                "reference_seconds": row["median_seconds"][reference],
                                "comparator_seconds": row["median_seconds"][comparator]})
    family_means = {f: math.exp(math.fsum(v) / len(v)) for f, v in sorted(families.items())}
    return {"median": statistics.median(ratios),
            "geomean": math.exp(math.fsum(math.log(v) for v in ratios) / len(ratios)),
            "aggregate_ratio": math.fsum(r["median_seconds"][comparator] for r in rows)
                               / math.fsum(r["median_seconds"][reference] for r in rows),
            "faster_cases": sum(v > 1 for v in ratios), "slower_cases": sum(v < 1 for v in ratios),
            "tied_cases": sum(v == 1 for v in ratios), "min_ratio": min(ratios), "max_ratio": max(ratios),
            "p05_ratio": quantile(ratios, .05), "max_slowdown": max(1 / v for v in ratios),
            "p95_slowdown": quantile([1 / v for v in ratios], .95),
            "slowdowns_over_2x": sum(1 / v > 2 for v in ratios),
            "macro_family_geomean": math.exp(math.fsum(math.log(v) for v in family_means.values()) / len(family_means)),
            "family_geomeans": family_means,
            "regressions": sorted(regressions, key=lambda r: (-r["slowdown"], r["series"], r["max_buffer"]))}


def build_report(run, *, audit_path=None, root=ROOT):
    root, run = Path(root), Path(run)
    paths = {name: run / f"{name}.json" for name in ("protocol", "inputs", "summary", "environment")}
    paths["audit"] = Path(audit_path) if audit_path else run / "audit.json"
    documents = {name: json.loads(path.read_text()) for name, path in paths.items()}
    p, audited, summary, env = (documents[k] for k in ("protocol", "audit", "summary", "environment"))
    require(p["version"] in (2, 3) and p["split"] in ("development", "holdout"), "Unsupported run identity")
    require(audited["status"] == summary["status"] == "PASS" and summary["violations"] == [], "Run did not independently pass")
    require(audited["data_provenance"]["status"] == "PASS"
            and audited["data_provenance"]["source_members_checked"] is True, "Source-member provenance is incomplete")
    require(sha(paths["protocol"]) == audited["protocol_sha256"] == summary["protocol_sha256"] == env["protocol_sha256"], "Protocol hash mismatch")
    require(type(env["threads"]) is int and env["threads"] == 1
            and isinstance(env["threadpool_info"], list)
            and all(type(pool["num_threads"]) is int and pool["num_threads"] == 1
                    for pool in env["threadpool_info"]), "Audited single-thread contract differs")
    require(sha(paths["inputs"]) == p["inputs_sha256"] == audited["inputs_sha256"], "Input hash mismatch")
    raw_path = run / "measurements.jsonl"
    require(sha(raw_path) == audited["measurements_sha256"] == summary["measurements_sha256"], "Raw-record hash mismatch")
    source_root = root / "artifacts/pr-engine/source-v2" if p["version"] == 2 else root
    expected_sources = SOURCES_V2 | ({"src/sparse_vus/dense_radix.py"} if p["version"] == 3 else set())
    require(set(p["source_sha256"]) == expected_sources and env["source_sha256"] == p["source_sha256"], "Measured source bindings differ")
    for relative, expected in p["source_sha256"].items():
        require(sha(source_root / relative) == expected, f"Measured source changed: {relative}")
    require(sha(source_root / "experiments/audit_pr_engine.py") == audited["auditor_sha256"], "Auditor identity differs")
    same(summary["reconstructed"], audited["reconstructed"])
    exact = [*EXACT_V2, *(MATCHED if p["version"] == 3 else ())]
    methods = [*exact, *RACERS, *(["fast_full_budget"] if p["include_full_budget"] else [])]
    require(p["method_ids"] == methods, "Missing comparator")
    rows = [json.loads(line) for line in raw_path.read_text().splitlines()]
    require(len(rows) == len(documents["inputs"]) == p["cases"] == audited["reconstructed"]["cases"] > 0, "Incomplete run")
    for row, identity in zip(rows, documents["inputs"]):
        require({k: row[k] for k in identity} == identity, "Input identity differs")
        for field in ("values", "seconds", "median_seconds"):
            require(set(row[field]) == set(methods), "Incomplete raw comparator coverage")
        for method in methods:
            times = row["seconds"][method]
            require(len(times) == 3 and all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in times), "Invalid raw timing")
            require(row["median_seconds"][method] == statistics.median(times), "Incorrect case median")
    groups = {str(w): [r for r in rows if r["max_buffer"] == w] for w in sorted({r["max_buffer"] for r in rows})}
    groups["combined_30_100"] = [r for r in rows if r["max_buffer"] in (30, 100)]
    output_groups = {}
    for name, cases in groups.items():
        require(bool(cases), "Missing primary/secondary cases")
        output = {"cases": len(cases), "series": len({r["series"] for r in cases}),
                  "families": len({r["family"] for r in cases}), "methods": {}, "comparisons": {}}
        for method in methods:
            values = [r["median_seconds"][method] for r in cases]
            record = {"sum_case_median_seconds": math.fsum(values), "median_case_seconds": statistics.median(values),
                      "geomean_case_seconds": math.exp(math.fsum(math.log(v) for v in values) / len(values)),
                      "work": "paired ROC+PR" if method in ("sparse_both", "dense_nearest_both", "benchopt_both", "radix_both")
                              else "PR selection" if method not in exact else "PR only"}
            if method not in exact:
                record["work_accounting"] = {key: sum(r["values"][method][key] for r in cases)
                    for key in ("total_unique_widths", "total_curve_evaluations", "full_evaluation_count")}
                if method != "v02_race":
                    record["work_accounting"].update({key: sum(r["values"][method][key] for r in cases)
                        for key in ("adaptive_curve_evaluations", "completion_curve_evaluations")})
                    record["work_accounting"]["fallback_models"] = sum(len(r["values"][method]["fallback_models"]) for r in cases)
                    record["work_accounting"]["max_retained_curve_bytes"] = max(r["values"][method]["retained_curve_bytes"] for r in cases)
            output["methods"][method] = record
        for reference in p["bootstrap"]["references"]:
            output["comparisons"][reference] = {}
            for comparator in methods:
                if comparator == reference:
                    continue
                stats = comparison(cases, reference, comparator)
                ci = audited["reconstructed"]["uncertainty"][name][reference][comparator]
                require(ci["cases"] == len(cases) and ci["families"] == output["families"], "CI population mismatch")
                for key in ("geomean_ci95", "aggregate_ratio_ci95"):
                    interval = ci[key]
                    require(len(interval) == 2 and all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in interval)
                            and interval[0] <= interval[1], "Invalid audited interval")
                    stats[key] = interval
                if name != "combined_30_100":
                    verified = audited["reconstructed"]["by_width"][name]["methods"][reference]["by_comparator"][comparator]
                    for key in verified:
                        same(stats[key], verified[key])
                output["comparisons"][reference][comparator] = stats
        output_groups[name] = output
    controls = {"primary_decision": ["sparse_pr", "dense_pr_direct", "radix_pr"],
                "radix_primary_decision": ["sparse_pr", "dense_pr_direct", "dense_nearest_both"],
                "radix_racing_decision": ["sparse_pr", "dense_pr_direct", "radix_pr"]}
    if p["version"] == 3:
        controls["radix_primary_decision"] += list(MATCHED)
        controls["radix_racing_decision"] += list(MATCHED)
    references = {"primary_decision": "fast_race", "radix_primary_decision": "radix_pr", "radix_racing_decision": "fast_race_radix"}
    decisions = {}
    for name, required in controls.items():
        value = audited["reconstructed"][name]
        passed = all(output_groups["30"]["comparisons"][references[name]][c][key][0] > 1
                     for c in required for key in ("geomean_ci95", "aggregate_ratio_ci95"))
        require(value["passes"] is passed, "Decision does not follow audited intervals")
        decisions[name] = {**value, "reference": references[name], "controls": required}
    return {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
            "run_label": f"v{p['version']} {p['split']}", "protocol_version": p["version"], "split": p["split"],
            "cases": len(rows), "series": len({r["series"] for r in rows}), "families": len({r["family"] for r in rows}),
            "models": p["models"], "method_order": methods, "audit_status": "PASS", "decisions": decisions,
            "environment": {k: env.get(k) for k in ("platform", "machine", "python", "numpy", "numba", "threads", "threadpool_info", "cpu_clearance")},
            "bindings": {**{f"{name}_sha256": sha(path) for name, path in paths.items()},
                         "measurements_sha256": sha(raw_path), "reporter_sha256": sha(Path(__file__)),
                         "auditor_sha256": audited["auditor_sha256"], "measured_source_sha256": p["source_sha256"]},
            "max_exact_pr_error": audited["reconstructed"]["max_exact_pr_error"],
            "max_enclosure_slack": audited["reconstructed"]["max_enclosure_slack"],
            "measurement_variation": audited["reconstructed"]["measurement_variation"],
            "bootstrap": p["bootstrap"], "groups": output_groups,
            "limitations": [*audited["limitations"],
                "Ratios use paired within-run case medians; values above one favor the named reference. No cross-run or cross-version times are pooled.",
                "Family-cluster CIs describe case variation, not uncertainty from only three timing repetitions; intervals are copied from the bound independent audit.",
                "Benchopt and paired controls compute ROC and PR; matched PR-only controls isolate the extra-work confound.",
                "The 308-series policy holdout belongs to the previously studied corpus and the same families; it is not a new external-domain dataset.",
                "DTAIAnomaly's bounded external appendix is separate. These results do not establish global SOTA.",
                "Retained curve bytes are not peak memory. CPU-clearance notes do not establish operating-system isolation."]}


def markdown(report):
    lines = [f"# PR-engine report: {report['run_label']}", "",
             f"Independent audit: **PASS**. {report['cases']} cases, {report['series']} series, {report['families']} families.", "",
             "Speed ratios are comparator time / radix_pr time; values above 1 favor radix_pr. All timing summaries use three-repetition case medians. Brackets contain audited 95% family-cluster intervals.", ""]
    for name, decision in report["decisions"].items():
        lines += [f"- **{name}: {'PASS' if decision['passes'] else 'FAIL'}** at L={decision['width']}; reference `{decision['reference']}`, controls: "
                  + ", ".join(f"`{c}`" for c in decision["controls"]) + "."]
    lines += ["", "Each decision requires both geomean and aggregate-ratio lower interval bounds above 1 against every listed control, plus correctness.", ""]
    for name, group in report["groups"].items():
        lines += [f"## {'Combined L=30/100 (descriptive)' if name == 'combined_30_100' else 'L=' + name}", "",
                  "| Method | Work | Total seconds | Median ratio | Geomean [95% CI] | Aggregate [95% CI] | radix_pr faster/slower | Worst radix_pr slowdown |",
                  "|---|---|---:|---:|---:|---:|---:|---:|"]
        for method in report["method_order"]:
            timing = group["methods"][method]
            if method == "radix_pr":
                cells = ["reference", "—", "—", "—", "—"]
            else:
                s = group["comparisons"]["radix_pr"][method]
                interval = lambda key: f"{s[key]:.3f} [{s[key + '_ci95'][0]:.3f}, {s[key + '_ci95'][1]:.3f}]"
                cells = [f"{s['median']:.3f}", interval("geomean"), interval("aggregate_ratio"),
                         f"{s['faster_cases']}/{s['slower_cases']}", f"{max(1., s['max_slowdown']):.3f}x"]
            lines.append(f"| {method} | {timing['work']} | {timing['sum_case_median_seconds']:.6f} | " + " | ".join(cells) + " |")
        lines += ["", "The JSON includes all four reference methods, every comparator, complete negative-case lists, family effects, and work accounting.", ""]
    lines += ["## Scope", "", *[f"- {v}" for v in report["limitations"]], "",
              f"Audit SHA-256: `{report['bindings']['audit_sha256']}`", "",
              f"Raw records SHA-256: `{report['bindings']['measurements_sha256']}`", ""]
    return "\n".join(lines)


def latex(report):
    escape = lambda s: "".join({"_": r"\_", "&": r"\&", "%": r"\%", "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}"}.get(c, c) for c in s)
    lines = [f"% {report['run_label']}; audit SHA256 {report['bindings']['audit_sha256']}",
             "% Comparator/radix PR ratios; >1 favors radix PR. Whole-call case medians; family-cluster intervals."]
    for name, group in report["groups"].items():
        if name == "combined_30_100":
            continue
        lines += [r"\par\noindent\textbf{" + escape(report["run_label"]) + f", $L={name}$" + "}",
                  r"Ratios are comparator time / radix\_pr time; values above 1 favor radix\_pr.",
                  r"Brackets show audited 95\% family-cluster intervals for three-repeat case medians.",
                  r"\par\smallskip", r"\begin{tabular}{lrrr}",
                  r"Comparator & Median & Geomean [95\% CI] & Aggregate [95\% CI] \\", r"\hline"]
        for method in report["method_order"]:
            if method == "radix_pr":
                continue
            s = group["comparisons"]["radix_pr"][method]
            g, a = s["geomean_ci95"], s["aggregate_ratio_ci95"]
            lines.append(f"{escape(method)} & {s['median']:.3f} & {s['geomean']:.3f} [{g[0]:.3f}, {g[1]:.3f}] & {s['aggregate_ratio']:.3f} [{a[0]:.3f}, {a[1]:.3f}] " + r"\\")
        lines += [r"\end{tabular}", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="Output filename prefix for .json/.md and optional .tex")
    parser.add_argument("--tex", action="store_true")
    args = parser.parse_args()
    report = build_report(args.run, audit_path=args.audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Path(str(args.output) + ".json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    Path(str(args.output) + ".md").write_text(markdown(report))
    if args.tex:
        Path(str(args.output) + ".tex").write_text(latex(report))
    print(json.dumps({"status": "PASS", "run": report["run_label"], "cases": report["cases"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
