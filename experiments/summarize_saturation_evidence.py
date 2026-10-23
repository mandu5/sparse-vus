"""Independently audit frozen saturation receipts and summarize all outcomes.

No benchmark driver or metric implementation is imported. This checks recorded
identities, timing coverage, parity, work counters and statistics; it does not
recompute metric values from the original observations or authenticate the host.
Use --plot for publication figures after controlled timing has finished.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import statistics

METHODS = ("saturation", "active_full", "last_positive", "radix", "dense_radix",
           "klein", "sparse_comparison", "dense_direct", "dense_direct_radix")
CONTROLS = METHODS[1:]
WIDTHS = (30, 100, 300)
PROFILE_MODES = ("saturation", "active_full", "last_positive")
ATOL = 1e-11
SEED = 2026102113
SCALARS = ("median_ratio", "geomean_ratio", "aggregate_ratio", "wins", "losses", "ties",
           "minimum_ratio", "candidate_seconds_sum", "reference_seconds_sum")
RECEIPTS = ("protocol.json", "inputs.json", "run-start.json", "completion.json",
            "measurements.jsonl", "report.json")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hash_string(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Nonfinite JSON constant: {value}")


def parse_json(text):
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)


def load_json(path):
    return parse_json(Path(path).read_text())


def close(actual, expected, context):
    require(finite(actual) and finite(expected)
            and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-14),
            f"Stored report differs: {context}: {actual!r} vs {expected!r}")


def ratio_summary(numerators, denominators, case_ids):
    require(len(numerators) == len(denominators) == len(case_ids) > 0, "Empty ratio population")
    require(all(finite(v) and v > 0 for v in [*numerators, *denominators]), "Invalid ratio inputs")
    ratios = [a / b for a, b in zip(numerators, denominators)]
    require(all(finite(r) and r > 0 for r in ratios), "Nonfinite ratio")
    return {
        "median_ratio": statistics.median(ratios),
        "geomean_ratio": math.exp(math.fsum(map(math.log, ratios)) / len(ratios)),
        "aggregate_ratio": math.fsum(numerators) / math.fsum(denominators),
        "wins": sum(r > 1 for r in ratios), "losses": sum(r < 1 for r in ratios),
        "ties": sum(r == 1 for r in ratios), "minimum_ratio": min(ratios),
        "maximum_ratio": max(ratios), "maximum_slowdown": 1 / min(ratios),
        "reference_seconds_sum": math.fsum(numerators),
        "candidate_seconds_sum": math.fsum(denominators),
        "loss_case_ids": [case for case, ratio in zip(case_ids, ratios) if ratio < 1],
    }


def work_summary(numerators, denominators, case_ids):
    result = ratio_summary(numerators, denominators, case_ids)
    result["reference_visits_sum"] = result.pop("reference_seconds_sum")
    result["candidate_visits_sum"] = result.pop("candidate_seconds_sum")
    result.pop("maximum_slowdown")
    return result


def audit_records(rows, protocol, inputs):
    """Validate the declared Cartesian workload and each unaggregated record."""
    require(protocol["version"] == 1 and protocol["phase"] in ("development", "external"),
            "Unsupported protocol")
    require(protocol["method_ids"] == list(METHODS) and protocol["repetitions"] == 3
            and protocol["widths"] == list(WIDTHS) and protocol["primary_width"] == 30
            and protocol["parity_atol"] == ATOL and protocol["seed"] == SEED,
            "Changed method, width, repetition, parity or randomization contract")
    require(protocol["bootstrap"] == {"unit": "family", "repetitions": 2000,
                                      "seed": SEED + 1, "confidence": .95},
            "Changed family-bootstrap contract")
    models = protocol["models"]
    require(isinstance(models, list) and models and len(models) == len(set(models))
            and all(isinstance(m, str) and m for m in models), "Invalid models")
    require(len(rows) == len(inputs) == protocol["cases"] and bool(inputs), "Incomplete case coverage")
    series = sorted({item["series"] for item in inputs})
    require(len(series) == protocol["series"], "Series coverage differs")
    require(sorted({item["family"] for item in inputs}) == protocol["families"], "Family coverage differs")
    expected = sorted(itertools.product(WIDTHS, series, models))
    actual = [(item["max_buffer"], item["series"], item["model"]) for item in inputs]
    require(actual == expected, "Incomplete, duplicate or reordered Cartesian case coverage")
    require(len({item["case_id"] for item in inputs}) == len(inputs), "Duplicate case IDs")
    rng = random.Random(SEED)
    maximum_error = 0.0
    cases = []
    series_identity, score_identity, interval_counts = {}, {}, {}
    required_identity = {"series", "family", "model", "n", "positive_points", "max_buffer",
                         "label_member_sha256", "score_member_sha256", "case_id"}
    for row, identity in zip(rows, inputs):
        case = identity["case_id"]
        require(required_identity <= set(identity), f"Missing input identity: {case}")
        require(case == f"{identity['series']}|{identity['model']}|{identity['max_buffer']}", "False case ID")
        require(set(row) == set(identity) | {"methods", "orders", "profiles"}
                and all(row[key] == value for key, value in identity.items()), f"Input identity differs: {case}")
        n, positives, width = row["n"], row["positive_points"], row["max_buffer"]
        require(type(n) is int and type(positives) is int and 0 < positives < n, f"Invalid labels metadata: {case}")
        require(hash_string(row["label_member_sha256"]) and hash_string(row["score_member_sha256"]), "Invalid array hash")
        if "npz_sha256" in identity:
            require(hash_string(identity["npz_sha256"]), "Invalid NPZ hash")
        key = row["series"]
        label_identity = (row["family"], n, positives, row["label_member_sha256"])
        require(series_identity.setdefault(key, label_identity) == label_identity, "Series metadata changes across cases")
        score_key = (key, row["model"])
        require(score_identity.setdefault(score_key, row["score_member_sha256"]) == row["score_member_sha256"],
                "Scores change across widths")
        require(list(row["methods"]) == list(METHODS), f"Incomplete or reordered methods: {case}")
        orders = []
        for _ in range(3):
            order = list(METHODS)
            rng.shuffle(order)
            orders.append(order)
        require(row["orders"] == orders, f"Method randomization differs: {case}")
        medians = {}
        reference = row["methods"]["saturation"]["values"][0]
        for method in METHODS:
            measured = row["methods"][method]
            times, values = measured["seconds"], measured["values"]
            require(len(times) == len(values) == 3, f"Invalid repetition count: {case}/{method}")
            require(all(finite(v) and v > 0 for v in times), f"Invalid timing: {case}/{method}")
            require(all(finite(v) and -ATOL <= v <= 1 + ATOL for v in values), f"Invalid PR: {case}/{method}")
            maximum_error = max(maximum_error, *(abs(v - reference) for v in values))
            medians[method] = statistics.median(times)
        require(maximum_error <= ATOL, f"Metric parity exceeds {ATOL}: {case}")
        profiles = row["profiles"]
        require(set(profiles) == set(PROFILE_MODES), "Incomplete work profiles")
        q, k = profiles["saturation"]["Q"], profiles["saturation"]["K"]
        require(type(q) is int and type(k) is int and 1 <= k <= positives <= q <= n, "Invalid Q/K")
        require(interval_counts.setdefault(key, k) == k, "Original interval count changes across cases")
        for name in PROFILE_MODES:
            profile = profiles[name]
            require(profile["Q"] == q and profile["K"] == k, "Inconsistent profile Q/K")
            visited, active = profile["visited"], profile["active"]
            require(len(visited) == len(active) == width + 1, "Invalid work-vector coverage")
            require(all(type(v) is int and type(a) is int and 0 < v <= a <= q for v, a in zip(visited, active)),
                    "Invalid visited/active counters")
            require(active == sorted(active) and active[0] == positives and active[-1] == q,
                    "Invalid support activation counts")
            require(active == profiles["saturation"]["active"], "Activation differs between stop controls")
            require(set(profile["values"]) == {"roc", "pr"}
                    and all(finite(v) and -ATOL <= v <= 1 + ATOL for v in profile["values"].values()),
                    "Invalid profile metric values")
            require(abs(profile["values"]["pr"] - reference) <= ATOL, "Profile PR differs from timed value")
        require(profiles["active_full"]["visited"] == profiles["active_full"]["active"], "Full scan omits work")
        require(all(a <= b <= c for a, b, c in zip(profiles["saturation"]["visited"],
                    profiles["last_positive"]["visited"], profiles["active_full"]["visited"])),
                "Saturation work exceeds stop controls")
        work = {name: sum(profiles[name]["visited"]) for name in PROFILE_MODES}
        work["maximum"] = (width + 1) * q
        fastest = min(medians[name] for name in CONTROLS)
        cases.append({**identity, "median_seconds": medians, "Q": q, "K": k,
                      "work_visits": work,
                      "fastest_control_seconds": fastest,
                      "fastest_controls": [name for name in CONTROLS if medians[name] == fastest],
                      "fastest_control_ratio": fastest / medians["saturation"],
                      "control_ratios": {name: medians[name] / medians["saturation"] for name in CONTROLS},
                      "work_ratios": {name: work[name] / work["saturation"]
                                      for name in ("active_full", "last_positive", "maximum")}})
    return cases, maximum_error


def summarize_cases(cases):
    """Reconstruct paired summaries and bootstrap from family-level sufficient sums."""
    import numpy as np

    rng = np.random.default_rng(SEED + 1)
    widths = {}
    for width in WIDTHS:
        rows = [row for row in cases if row["max_buffer"] == width]
        ids = [row["case_id"] for row in rows]
        candidate = [row["median_seconds"]["saturation"] for row in rows]
        families = sorted({row["family"] for row in rows})
        groups = [[i for i, row in enumerate(rows) if row["family"] == family] for family in families]
        draws = rng.integers(0, len(groups), size=(2000, len(groups)))
        comparisons = {}
        for control in CONTROLS:
            reference = [row["median_seconds"][control] for row in rows]
            result = ratio_summary(reference, candidate, ids)
            counts = np.array([len(group) for group in groups])
            logs = np.array([math.fsum(math.log(reference[i] / candidate[i]) for i in group) for group in groups])
            numerators = np.array([math.fsum(reference[i] for i in group) for group in groups])
            denominators = np.array([math.fsum(candidate[i] for i in group) for group in groups])
            geometric = np.exp(logs[draws].sum(axis=1) / counts[draws].sum(axis=1))
            aggregate = numerators[draws].sum(axis=1) / denominators[draws].sum(axis=1)
            result["geomean_ci95"] = np.quantile(geometric, [.025, .975]).tolist()
            result["aggregate_ci95"] = np.quantile(aggregate, [.025, .975]).tolist()
            comparisons[control] = result
        visits = [row["work_visits"]["saturation"] for row in rows]
        work = {f"{mode}_over_saturation": work_summary(
                    [row["work_visits"][mode] for row in rows], visits, ids)
                for mode in ("active_full", "last_positive", "maximum")}
        work["maximum_over_active_full"] = work_summary(
            [row["work_visits"]["maximum"] for row in rows],
            [row["work_visits"]["active_full"] for row in rows], ids)
        work["saturation_fraction_of_maximum"] = {
            "median": statistics.median(row["work_visits"]["saturation"] / row["work_visits"]["maximum"] for row in rows),
            "aggregate": sum(visits) / sum(row["work_visits"]["maximum"] for row in rows)}
        widths[str(width)] = {
            "cases": len(rows), "families": families, "comparisons": comparisons, "work": work,
            "K1_cases": sum(row["K"] == 1 for row in rows),
            "K1_unique_series": len({row["series"] for row in rows if row["K"] == 1}),
            "K1_case_ids": [row["case_id"] for row in rows if row["K"] == 1],
            "fastest_eight_control_oracle": ratio_summary(
                [row["fastest_control_seconds"] for row in rows], candidate, ids),
        }
    return widths


def compare_report(report, widths, maximum_error, cases):
    require(report["cases"] == cases and report["parity_pass"] is True, "Stored parity/coverage differs")
    close(report["max_absolute_error"], maximum_error, "max_absolute_error")
    require(set(report["widths"]) == set(widths), "Stored width coverage differs")
    for width, actual in widths.items():
        stored = report["widths"][width]
        require(stored["cases"] == actual["cases"] and stored["families"] == actual["families"],
                "Stored width/family coverage differs")
        require(set(stored["comparisons"]) == set(CONTROLS), "Stored control coverage differs")
        for control, calculated in actual["comparisons"].items():
            previous = stored["comparisons"][control]
            for key in SCALARS:
                if key in ("wins", "losses", "ties"):
                    require(type(previous[key]) is int and previous[key] == calculated[key],
                            f"Stored report differs: {width}/{control}/{key}")
                else:
                    close(previous[key], calculated[key], f"{width}/{control}/{key}")
            for key in ("geomean_ci95", "aggregate_ci95"):
                require(len(previous[key]) == 2, "Invalid stored interval")
                for before, after in zip(previous[key], calculated[key]):
                    close(before, after, f"{width}/{control}/{key}")
    decision = all(value["geomean_ci95"][0] > 1 and value["aggregate_ci95"][0] > 1
                   for value in widths["30"]["comparisons"].values())
    require(type(report["primary_decision"]) is bool and report["primary_decision"] == decision,
            "Stored primary decision differs from reconstructed criterion")
    return decision


def audit_study(label, path):
    path = Path(path).resolve()
    hashes = {name: sha(path / name) for name in RECEIPTS}
    protocol, inputs = load_json(path / "protocol.json"), load_json(path / "inputs.json")
    start, completion = load_json(path / "run-start.json"), load_json(path / "completion.json")
    report = load_json(path / "report.json")
    require(protocol["inputs_sha256"] == hashes["inputs.json"], "Frozen input hash mismatch")
    require(start["protocol_sha256"] == completion["protocol_sha256"] == hashes["protocol.json"],
            "Protocol hash chain mismatch")
    require(completion["status"] == "COMPLETED" and completion["cases"] == protocol["cases"],
            "Missing complete terminal receipt")
    require(completion["measurements_sha256"] == hashes["measurements.jsonl"], "Raw measurement hash mismatch")
    require(protocol["source_sha256"] and all(hash_string(value) for value in protocol["source_sha256"].values()),
            "Invalid source hash inventory")
    require(start["source_sha256"] == completion["source_sha256"] == protocol["source_sha256"],
            "Source binding chain mismatch")
    for field, filename in (("protocol_sha256", "protocol.json"), ("inputs_sha256", "inputs.json"),
                            ("measurements_sha256", "measurements.jsonl")):
        require(report[field] == hashes[filename], f"Report binding mismatch: {field}")
    require(report["phase"] == protocol["phase"] and report["scope"] == protocol["history"],
            "Stored study scope differs")
    rows = [parse_json(line) for line in (path / "measurements.jsonl").read_text().splitlines()]
    cases, maximum_error = audit_records(rows, protocol, inputs)
    widths = summarize_cases(cases)
    decision = compare_report(report, widths, maximum_error, len(cases))
    # The evidence folder must remain unchanged throughout this read-only audit.
    require(hashes == {name: sha(path / name) for name in RECEIPTS}, "Evidence changed during audit")
    return {
        "label": label, "path": str(path), "audit_status": "PASS_RECORDED_EVIDENCE",
        "phase": protocol["phase"], "history": protocol["history"],
        "cases": len(cases), "series": protocol["series"], "families": protocol["families"],
        "models": protocol["models"], "receipt_sha256": hashes,
        "source_sha256": protocol["source_sha256"], "source_commit": protocol["source_commit"],
        "parity_pass": True, "max_absolute_error": maximum_error,
        "primary_decision": decision, "primary_criterion": protocol["decision"],
        "widths": widths, "case_results": cases,
        "scope": "Independent receipt/statistical reconstruction, not independent metric recomputation or hardware attestation. "
                 "Fastest-control oracle selects the fastest of all eight controls separately for each case after measurement. "
                 "Work reductions count support visits and do not imply equal wall-time reductions. "
                 "Family-bootstrap intervals do not quantify machine-population or timing-repeat uncertainty.",
    }


def markdown(studies):
    lines = ["# Saturation evidence audit", "", "Ratios are control time / saturation time: below 1 means saturation is slower. "
             "All cases and widths are retained. Audit PASS is separate from the frozen primary empirical criterion.", ""]
    for study in studies:
        lines += [f"## {study['label']}", "", study["history"], "",
                  f"Receipt audit: **{study['audit_status']}**. Cases: {study['cases']}; "
                  f"series: {study['series']}; families: {len(study['families'])}. "
                  f"Maximum recorded PR discrepancy: {study['max_absolute_error']:.3g}. "
                  f"Frozen primary L=30 criterion: **{'PASS' if study['primary_decision'] else 'FAIL'}**.", "",
                  "| L | Control | Median | Geomean [95% CI] | Aggregate | Wins / losses / ties | Minimum |",
                  "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
        for width, values in study["widths"].items():
            for control, stats in values["comparisons"].items():
                lower, upper = stats["geomean_ci95"]
                lines.append(f"| {width} | {control} | {stats['median_ratio']:.3f} | "
                             f"{stats['geomean_ratio']:.3f} [{lower:.3f}, {upper:.3f}] | "
                             f"{stats['aggregate_ratio']:.3f} | {stats['wins']} / {stats['losses']} / {stats['ties']} | "
                             f"{stats['minimum_ratio']:.3f} |")
            oracle = values["fastest_eight_control_oracle"]
            lines.append(f"| {width} | Per-case fastest eight-control oracle | {oracle['median_ratio']:.3f} | "
                         f"{oracle['geomean_ratio']:.3f} | {oracle['aggregate_ratio']:.3f} | "
                         f"{oracle['wins']} / {oracle['losses']} / {oracle['ties']} | {oracle['minimum_ratio']:.3f} |")
        lines += ["", "| L | K=1 cases | Median visits: active full / saturation | "
                  "Last positive / saturation | Maximum (L+1)Q / saturation | Aggregate fraction of maximum visited |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for width, values in study["widths"].items():
            work = values["work"]
            lines.append(f"| {width} | {values['K1_cases']} | {work['active_full_over_saturation']['median_ratio']:.3f} | "
                         f"{work['last_positive_over_saturation']['median_ratio']:.3f} | "
                         f"{work['maximum_over_saturation']['median_ratio']:.3f} | "
                         f"{work['saturation_fraction_of_maximum']['aggregate']:.4f} |")
        lines += ["", "### Every recorded loss case", ""]
        for width, values in study["widths"].items():
            for control, stats in {**values["comparisons"], "fastest_eight_control_oracle": values["fastest_eight_control_oracle"]}.items():
                losses = ", ".join(f"`{case}`" for case in stats["loss_case_ids"]) or "None"
                lines += [f"L={width}, {control} ({stats['losses']} losses): {losses}", ""]
        lines += [study["scope"], "", f"Protocol SHA-256: `{study['receipt_sha256']['protocol.json']}`", ""]
    return "\n".join(lines)


def plot_studies(studies, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {30: "#0072B2", 100: "#D55E00", 300: "#009E73"}
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 9,
                         "pdf.fonttype": 42, "svg.fonttype": "none"}):
        figure, axes = plt.subplots(len(studies), 3, figsize=(15, 4.1 * len(studies)), squeeze=False)
        for row_axes, study in zip(axes, studies):
            ecdf, controls, mechanism = row_axes
            for width in WIDTHS:
                rows = [case for case in study["case_results"] if case["max_buffer"] == width]
                ratios = sorted(case["fastest_control_ratio"] for case in rows)
                losses = sum(ratio < 1 for ratio in ratios)
                ecdf.step(ratios, [(i + 1) / len(ratios) for i in range(len(ratios))], where="post",
                          color=colors[width], label=f"L={width}: {losses}/{len(rows)} slower")
                mechanism.scatter([case["work_ratios"]["active_full"] for case in rows],
                                  [case["fastest_control_ratio"] for case in rows],
                                  s=13, alpha=.55, color=colors[width], label=f"L={width}", linewidths=0)
            ecdf.set_xscale("log")
            ecdf.axvline(1, color="black", linestyle="--", linewidth=.8)
            ecdf.set_ylim(0, 1.02)
            ecdf.set_xlabel("Fastest control / saturation time")
            ecdf.set_ylabel("Cumulative fraction of cases")
            ecdf.set_title(f"{study['label']}: every case, all widths")
            ecdf.legend(fontsize=7, loc="best")
            primary = study["widths"]["30"]["comparisons"]
            for i, control in enumerate(CONTROLS):
                item = primary[control]
                lower, upper = item["geomean_ci95"]
                controls.plot([lower, upper], [i, i], color="#333333", linewidth=1.5)
                controls.plot(item["geomean_ratio"], i, "o", color="#0072B2", markersize=4)
            controls.set_yticks(range(len(CONTROLS)), labels=CONTROLS)
            controls.invert_yaxis()
            controls.set_xscale("log")
            controls.axvline(1, color="black", linestyle="--", linewidth=.8)
            controls.set_xlabel("Geomean time ratio; family-bootstrap 95% CI")
            controls.set_title(f"L=30: frozen primary criterion {'PASS' if study['primary_decision'] else 'FAIL'}")
            mechanism.set_xscale("log")
            mechanism.set_yscale("log")
            mechanism.axhline(1, color="black", linestyle="--", linewidth=.8)
            mechanism.set_xlabel("Active-full visits / saturation visits")
            mechanism.set_ylabel("Fastest control / saturation time")
            mechanism.set_title("Recorded work and measured time")
            mechanism.legend(fontsize=7, loc="best")
            for axis in row_axes:
                axis.grid(True, alpha=.18)
        figure.tight_layout()
        files = []
        for suffix in ("pdf", "svg", "png"):
            path = output / f"saturation-evidence.{suffix}"
            figure.savefig(path, dpi=220, bbox_inches="tight")
            files.append(path.name)
        plt.close(figure)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", action="append", required=True, metavar="LABEL=PATH")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plot", action="store_true", help="Create PDF, SVG and PNG figures after timing is complete")
    args = parser.parse_args()
    specifications = []
    for value in args.study:
        label, separator, path = value.partition("=")
        require(separator and label and path, "Study must be LABEL=PATH")
        require(label not in {name for name, _ in specifications}, "Study labels must be unique")
        specifications.append((label, Path(path).resolve()))
    output = args.output.resolve()
    require(not output.exists(), "Use a new output directory; previous summaries are not overwritten")
    require(all(not output.is_relative_to(path) for _, path in specifications), "Do not write inside frozen study folders")
    studies = [audit_study(label, path) for label, path in specifications]
    output.mkdir(parents=True)
    result = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "auditor_sha256": sha(__file__), "studies": studies,
              "pooling": "Studies are reported separately; no cross-platform byte-identity or pooled-speed claim."}
    (output / "evidence.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    (output / "evidence.md").write_text(markdown(studies))
    figures = plot_studies(studies, output) if args.plot else []
    print(json.dumps({"output": str(output), "studies": len(studies), "figures": figures,
                      "primary_decisions": {study["label"]: study["primary_decision"] for study in studies}}, indent=2))


if __name__ == "__main__":
    main()
