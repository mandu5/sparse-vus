"""Descriptive post-hoc tied-winner sensitivity from completed saved archives.

No detector, metric, study producer or original auditor is imported. NumPy only
reads saved curve arrays and checks their maxima/parity. No timings are measured.
The caller supplies the independently obtained SHA256 of complete.json, which
binds protocol.json and records.jsonl; records bind every saved curve file.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np


PHASE = "DESCRIPTIVE_POST_HOC_TIE_SENSITIVITY"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def decode(raw):
    def reject_constant(value):
        raise ValueError("nonfinite JSON constant: " + value)
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def winners(values, tolerance):
    require(bool(values) and all(finite_number(value) for value in values), "invalid saved maximum values")
    require(finite_number(tolerance) and tolerance >= 0, "invalid winner tolerance")
    maximum = max(values)
    return [i for i, value in enumerate(values) if value >= maximum - tolerance]


def tie_detail(grid_values, distinct_values, tolerance):
    require(len(grid_values) == len(distinct_values), "model coverage differs between queries")
    grid_winners = winners(grid_values, tolerance)
    distinct_winners = winners(distinct_values, tolerance)
    optimum = max(distinct_values)
    selected = [distinct_values[i] for i in grid_winners]
    best = optimum - max(selected)
    worst = optimum - min(selected)
    require(0 <= best <= worst, "invalid tied-winner regret ordering")
    return {
        "grid_values": list(grid_values), "distinct_values": list(distinct_values),
        "grid_winners": grid_winners, "distinct_winners": distinct_winners,
        "grid_tied": len(grid_winners) > 1, "distinct_tied": len(distinct_winners) > 1,
        "nonoverlap": not bool(set(grid_winners).intersection(distinct_winners)),
        "best_grid_winner_regret": best, "worst_grid_winner_regret": worst,
        "tie_regret_width": worst - best,
    }


def summarize(details):
    return {
        "cases": len(details), "grid_ties": sum(d["grid_tied"] for d in details),
        "distinct_ties": sum(d["distinct_tied"] for d in details),
        "nonoverlap": sum(d["nonoverlap"] for d in details),
        "best_regret_ge_01": sum(d["best_grid_winner_regret"] >= 0.01 for d in details),
        "worst_regret_ge_01": sum(d["worst_grid_winner_regret"] >= 0.01 for d in details),
        "max_best_regret": max(d["best_grid_winner_regret"] for d in details),
        "max_worst_regret": max(d["worst_grid_winner_regret"] for d in details),
        "max_tie_regret_width": max(d["tie_regret_width"] for d in details),
    }


def record_key(record):
    return tuple(record[k] for k in ("id", "query", "bias", "cardinality", "trial", "method"))


def same_values(left, right):
    return len(left) == len(right) and all(float(a).hex() == float(b).hex() for a, b in zip(left, right))


def archive_path(root, relative):
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "curve path escapes archive")
    path = (root / path).resolve()
    require(path.is_relative_to(root) and path.is_file(), "curve path is missing or escapes archive")
    return path


def audit(output, expected_complete_sha256):
    output = Path(output).resolve()
    complete_path, protocol_path, records_path = (output / name for name in ("complete.json", "protocol.json", "records.jsonl"))
    require(digest(complete_path) == expected_complete_sha256, "complete file identity differs from supplied SHA256")
    complete = decode(complete_path.read_bytes())
    require(complete["status"] == "COMPLETE", "archive is not complete")
    protocol_sha, records_sha = digest(protocol_path), digest(records_path)
    require(complete["protocol_sha256"] == protocol_sha, "protocol hash differs from completion receipt")
    require(complete["records_sha256"] == records_sha, "records hash differs from completion receipt")
    protocol = decode(protocol_path.read_bytes())
    require(str(protocol["status"]).startswith("FROZEN_BEFORE_"), "unrecognized frozen study status")
    require(datetime.fromisoformat(complete["utc"]) >= datetime.fromisoformat(protocol["utc"]),
            "completion predates protocol freeze")
    anchors = {"complete.json": expected_complete_sha256, "protocol.json": protocol_sha, "records.jsonl": records_sha}
    if (output / "run-start.json").exists():
        started = decode((output / "run-start.json").read_bytes())
        require(started["protocol_sha256"] == protocol_sha, "run-start protocol identity differs")
        require(datetime.fromisoformat(protocol["utc"]) <= datetime.fromisoformat(started["utc"])
                <= datetime.fromisoformat(complete["utc"]), "run chronology differs")
        anchors["run-start.json"] = digest(output / "run-start.json")
    models = protocol["model_order"]
    require(len(models) > 0 and len(set(models)) == len(models), "duplicate or missing model identifiers")
    case_rows = protocol["cases"]
    cases = {case["id"]: case for case in case_rows}
    require(len(cases) == len(case_rows) > 0, "duplicate or missing recording identifiers")
    require(all(type(c["n"]) is int and c["n"] > 0 for c in case_rows), "invalid recording lengths")
    biases, cardinalities = protocol["biases"], protocol["cardinalities"]
    require(len(set(biases)) == len(biases) > 0 and len(set(cardinalities)) == len(cardinalities) > 0,
            "duplicate or missing semantic settings")
    require(set(protocol["queries"]) == {"grid100", "distinct"}, "unsupported query contract")
    orders = protocol["orders"]
    require(len(orders) > 0, "missing recorded trial orders")
    methods = orders[0]
    require("raster" in methods and len(set(methods)) == len(methods), "missing raster reference or duplicate method")
    require(all(len(order) == len(methods) and set(order) == set(methods) for order in orders),
            "method coverage differs between trials")
    require(len({tuple(order) for order in orders}) == len(orders), "duplicate trial order")
    tolerance, parity = protocol["winner_atol"], protocol["parity_atol"]
    require(finite_number(tolerance) and tolerance >= 0 and finite_number(parity) and parity >= 0,
            "invalid frozen tolerances")
    records = [decode(line) for line in records_path.read_text().splitlines()]
    indexed = {}
    for record in records:
        require(type(record["trial"]) is int, "invalid trial index")
        key = record_key(record)
        require(key not in indexed, "duplicate study record: " + repr(key))
        indexed[key] = record
    expected = {(case, query, bias, card, trial, method)
                for case in cases for query in protocol["queries"]
                for bias, card in itertools.product(biases, cardinalities)
                for trial, order in enumerate(orders) for method in order}
    require(set(indexed) == expected, "record coverage differs from frozen protocol")
    semantics = list(itertools.product(biases, cardinalities))
    curve_hashes, curve_owners = {}, {}
    maximum_error = 0.0
    repeat_checks = 0
    for identifier, case in cases.items():
        for query in protocol["queries"]:
            bundles = {}
            for method in methods:
                canonical = indexed[(identifier, query, biases[0], cardinalities[0], 0, method)]
                relative = canonical["curve_file"]
                require(relative not in curve_owners, "curve file reused across case/query/method bundles")
                curve_owners[relative] = (identifier, query, method)
                path = archive_path(output, relative)
                require(digest(path) == canonical["curve_file_sha256"], "saved curve file hash differs")
                curve_hashes[relative] = canonical["curve_file_sha256"]
                with np.load(path, allow_pickle=False) as arrays:
                    required_keys = {f"{bias}_{card}_{i}" for bias, card in semantics for i in range(len(models))}
                    require(set(arrays.files) == required_keys, "saved curve key coverage differs")
                    bundles[method] = {key: arrays[key] for key in arrays.files}
            for bias, card in semantics:
                reference = [bundles["raster"][f"{bias}_{card}_{i}"] for i in range(len(models))]
                reference_winners = None
                for method in ["raster"] + [name for name in methods if name != "raster"]:
                    arrays = [bundles[method][f"{bias}_{card}_{i}"] for i in range(len(models))]
                    h = hashlib.sha256()
                    for array, ref in zip(arrays, reference):
                        require(array.dtype == np.float64 and array.ndim == 2 and array.shape[1] == 3
                                and len(array) > 0 and np.isfinite(array).all(), "saved curve shape/dtype/finiteness differs")
                        require(array.shape == ref.shape, "method curve shapes differ")
                        require(float(array.min()) >= -parity and float(array.max()) <= 1 + parity,
                                "saved curve values fall outside metric range")
                        require(len(array) == 100 if query == "grid100" else len(array) <= case["n"],
                                "query count differs from recorded contract")
                        error = float(np.max(np.abs(array - ref)))
                        require(error <= parity, "saved curve parity exceeds frozen tolerance")
                        maximum_error = max(maximum_error, error)
                        h.update(np.ascontiguousarray(array, dtype=np.float64).tobytes())
                    maxima = [float(np.max(array[:, 2])) for array in arrays]
                    winner_indices = winners(maxima, tolerance)
                    if reference_winners is None:
                        reference_winners = winner_indices
                    require(winner_indices == reference_winners, "method winner sets differ at the frozen tolerance")
                    canonical = indexed[(identifier, query, bias, card, 0, method)]
                    bundle = indexed[(identifier, query, biases[0], cardinalities[0], 0, method)]
                    for trial in range(len(orders)):
                        record = indexed[(identifier, query, bias, card, trial, method)]
                        require((record["family"], record["n"]) == (case["family"], case["n"]), "recording metadata differs")
                        require(finite_number(record["seconds"]) and record["seconds"] > 0, "invalid recorded duration")
                        require(finite_number(record["max_curve_error"]) and 0 <= record["max_curve_error"] <= parity,
                                "invalid recorded parity error")
                        require(len(record["values"]) == len(models) and all(finite_number(v) for v in record["values"])
                                and same_values(record["values"], maxima), "saved record maximum differs from full curve")
                        require(record["winners"] == winner_indices
                                and all(type(i) is int for i in record["winners"]), "saved winners violate frozen tolerance")
                        require(record["output_sha256"] == h.hexdigest(), "saved output byte hash differs")
                        require(record["query_counts"] == [len(array) for array in arrays], "saved query count differs")
                        require((record["curve_file"], record["curve_file_sha256"])
                                == (bundle["curve_file"], bundle["curve_file_sha256"]), "repeated curve identity differs")
                        require(same_values(record["values"], canonical["values"])
                                and record["winners"] == canonical["winners"]
                                and record["output_sha256"] == canonical["output_sha256"], "repeated result differs")
                        repeat_checks += 1
    sensitivity = []
    for bias, card in semantics:
        details = []
        for identifier, case in cases.items():
            grid = indexed[(identifier, "grid100", bias, card, 0, "raster")]
            distinct = indexed[(identifier, "distinct", bias, card, 0, "raster")]
            require(all(d + parity >= g for g, d in zip(grid["values"], distinct["values"])),
                    "observed-distinct maximum is below grid maximum beyond tolerance")
            detail = tie_detail(grid["values"], distinct["values"], tolerance)
            details.append({"id": identifier, "family": case["family"], **detail,
                            "grid_winner_models": [models[i] for i in detail["grid_winners"]],
                            "distinct_winner_models": [models[i] for i in detail["distinct_winners"]]})
        by_family = [{"family": family, **summarize([d for d in details if d["family"] == family])}
                     for family in sorted({case["family"] for case in cases.values()})]
        sensitivity.append({"bias": bias, "cardinality": card, **summarize(details),
                            "by_family": by_family, "details": details})
    primary_path = output / "independent-report.json"
    primary_verified = None
    if primary_path.exists():
        primary = decode(primary_path.read_bytes())
        require(primary["status"] == "PASS" and primary["protocol_sha256"] == protocol_sha
                and primary["records_sha256"] == records_sha, "primary audit identity differs")
        original = {(row["bias"], row["cardinality"]): row for row in primary["grid_to_distinct_selection"]}
        require(len(original) == len(primary["grid_to_distinct_selection"]) == len(sensitivity)
                and set(original) == set(semantics), "primary selection coverage differs")
        for row in sensitivity:
            earlier = original[(row["bias"], row["cardinality"])]
            require((earlier["nonoverlap"], earlier["regret_ge_01"], earlier["max_regret"])
                    == (row["nonoverlap"], row["best_regret_ge_01"], row["max_best_regret"]),
                    "primary summary does not match reconstructed best-winner regret")
            by_case = {d["id"]: d for d in earlier["details"]}
            require(len(by_case) == len(earlier["details"]) == len(cases) and set(by_case) == set(cases),
                    "primary per-case coverage differs")
            for detail in row["details"]:
                old = by_case[detail["id"]]
                require((old["family"], old["nonoverlap"], old["best_grid_winner_regret"])
                        == (detail["family"], detail["nonoverlap"], detail["best_grid_winner_regret"]),
                        "primary per-case best-winner regret differs")
        anchors["independent-report.json"] = digest(primary_path)
        primary_verified = {"path": "independent-report.json", "sha256": anchors["independent-report.json"],
                            "quantity_checked": "best_grid_winner_regret and its original counts/maxima only"}
    for relative, expected_sha in {**anchors, **curve_hashes}.items():
        require(digest(output / relative) == expected_sha, "archive changed during read-only audit: " + relative)
    all_details = [detail for row in sensitivity for detail in row["details"]]
    return {
        "status": "PASS_POST_HOC_ARCHIVE_TIE_SENSITIVITY", "analysis_phase": PHASE,
        "created_utc": datetime.now(timezone.utc).isoformat(), "archive": str(output),
        "scope": "Descriptive reconstruction from trial0 saved curve maxima, with all recorded trials and methods checked. Added after review; not a newly preregistered result or a new measurement.",
        "metric_evaluation_performed": False, "metric_or_candidate_code_imported": False,
        "detector_fits_performed": 0, "local_input_bytes_verified": False,
        "timing_statistics_recomputed": False, "source_bytes_verified": False,
        "protocol_sha256": protocol_sha, "records_sha256": records_sha,
        "complete_sha256": expected_complete_sha256, "archive_sha256": anchors,
        "curve_file_sha256": curve_hashes, "records_verified": len(records),
        "repeated_record_checks": repeat_checks, "curve_files_verified": len(curve_hashes),
        "cases": len(cases), "semantic_contracts": len(semantics), "methods": methods,
        "trials_per_method": len(orders), "model_order": models, "reference_method": "raster",
        "winner_atol": tolerance, "parity_atol": parity, "max_curve_error": maximum_error,
        "cross_method_winner_disagreements": 0, "primary_best_regret_reconstructed": primary_verified,
        "definitions": {
            "grid_winners": "i with grid maximum[i] >= max(grid maximum) - frozen winner_atol; includes tolerance-based near ties",
            "distinct_winners": "i with observed-distinct maximum[i] >= max(observed-distinct maximum) - frozen winner_atol",
            "best_grid_winner_regret": "max_i distinct[i] - max_{i in grid winners} distinct[i]",
            "worst_grid_winner_regret": "max_i distinct[i] - min_{i in grid winners} distinct[i]",
            "threshold_scope": "Strict score > threshold over observed score thresholds; excludes the below-minimum/all-positive state.",
        },
        "grid_to_distinct_tie_sensitivity": sensitivity,
        "across_semantics_descriptive": {
            "cases_with_any_grid_tie": len({d["id"] for d in all_details if d["grid_tied"]}),
            "cases_with_any_best_regret_ge_01": len({d["id"] for d in all_details if d["best_grid_winner_regret"] >= .01}),
            "cases_with_any_worst_regret_ge_01": len({d["id"] for d in all_details if d["worst_grid_winner_regret"] >= .01}),
            "max_best_regret": max(d["best_grid_winner_regret"] for d in all_details),
            "max_worst_regret": max(d["worst_grid_winner_regret"] for d in all_details),
        },
        "limits": "Archive-only consistency, not an independent raw-data metric recomputation. No confidence interval, population interpretation or practical-benefit hypothesis is added. Semantic settings and recordings are dependent; no post-hoc case selection or replacement is performed.",
        "auditor_path": str(Path(__file__).resolve()), "auditor_sha256": digest(__file__),
    }


def render_markdown(result):
    rows = ["# Descriptive post-hoc tied-winner sensitivity", "",
            "This analysis was added after review. It reconstructs saved trial-0 maxima and checks all repeated records and complete curves; it adds no detector fits, metric evaluations, timings or preregistered finding.", "",
            f"Verified {result['cases']} recordings, {result['semantic_contracts']} semantic contracts, {result['records_verified']} records and {result['curve_files_verified']} curve files. Winner tolerance: `{result['winner_atol']}`. Reference: `{result['reference_method']}`; model order: `{result['model_order']}`.", "",
            "Best regret chooses the best observed-distinct performer among all grid winners. Worst regret chooses the worst among that same tolerance-based winner set. Both compare with the maximum over observed score thresholds; the below-minimum state is excluded.", "",
            "| Bias | Cardinality | Grid ties | Nonoverlap | Best ≥ .01 | Worst ≥ .01 | Max best | Max worst |",
            "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in result["grid_to_distinct_tie_sensitivity"]:
        rows.append(f"| {row['bias']} | {row['cardinality']} | {row['grid_ties']} | {row['nonoverlap']} | {row['best_regret_ge_01']} | {row['worst_regret_ge_01']} | {row['max_best_regret']:.12g} | {row['max_worst_regret']:.12g} |")
    total = result["across_semantics_descriptive"]
    rows.extend(["", f"Across settings, {total['cases_with_any_best_regret_ge_01']} distinct recordings have best regret ≥ .01 and {total['cases_with_any_worst_regret_ge_01']} have worst regret ≥ .01. These are descriptive counts with no independence or population claim.", "",
                 f"Completion SHA256: `{result['complete_sha256']}`. Protocol SHA256: `{result['protocol_sha256']}`. Records SHA256: `{result['records_sha256']}`.", "",
                 result["limits"], ""])
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Completed study archive; only read")
    parser.add_argument("--complete-sha256", required=True, help="Independently obtained completion receipt SHA256")
    parser.add_argument("--report", type=Path, required=True, help="New JSON report; refuses replacement")
    parser.add_argument("--markdown", type=Path, help="Optional new descriptive Markdown report")
    args = parser.parse_args()
    targets = [path for path in (args.report, args.markdown) if path is not None]
    require(len({path.resolve() for path in targets}) == len(targets), "report paths must differ")
    for path in targets:
        require(not path.exists(), "refusing to replace existing report: " + str(path))
    result = audit(args.output, args.complete_sha256)
    for path in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    if args.markdown:
        with args.markdown.open("x") as stream:
            stream.write(render_markdown(result))
    print(json.dumps({"status": result["status"], "analysis_phase": PHASE,
                      "report": str(args.report), "report_sha256": digest(args.report),
                      "cases": result["cases"], **result["across_semantics_descriptive"]}))


if __name__ == "__main__":
    main()
