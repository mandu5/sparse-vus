"""Independently reconstruct the recorded paired-output saturation supplement.

Standard library only: no data cache, evaluator, benchmark driver, NumPy, or
Numba is loaded. Paths supplied on the command line are repository-relative
unless absolute. Defaults select the historical Mac supplement. Source hashes
are checked as recorded identities across receipts, not against cached kernels.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STUDY = Path("artifacts/saturation/mac-external-baselines")
DEFAULT_OUTPUT = Path("artifacts/saturation/evidence-review/supplement-independent-audit-reproducible.json")
FROZEN_PROTOCOL = "8e9bf4a9e1d938f9b4467e46050ff5820ab04083d5cc8011cf770eb5083ae5ad"
MAIN = ("saturation_pair", "radix_pair", "benchopt_pair")
DTAI = "dtaianomaly_pair"
MODELS = {"isolation_forest", "pca_reconstruction", "knn_distance", "robust_marginal_z"}
RECEIPTS = ("protocol.json", "inputs.json", "run-start.json", "terminal.json",
            "measurements.jsonl", "workers.jsonl", "report.json")
PRIMARY_RECEIPTS = ("protocol.json", "inputs.json", "completion.json", "report.json", "measurements.jsonl")
CONTRACT = {
    "version": 1, "width": 30, "cases": 48, "series": 12, "families": 9,
    "repetitions": 3, "seed": 2026102127, "parity_atol": 1e-11,
    "main_methods": list(MAIN), "dtai_method": DTAI, "dtai_model": "isolation_forest",
    "dtai_cases": 12, "warmup_timeout_seconds": 120, "dtai_call_timeout_seconds": 30,
    "other_call_timeout_seconds": 300, "input_load_timeout_seconds": 120,
    "output": ["roc", "pr"], "compute_threads": 1,
}


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


def read_json(path):
    return parse_json(Path(path).read_text())


def repository_path(path):
    path = Path(path)
    return (path if path.is_absolute() else ROOT / path).resolve()


def resolve_primary(protocol, override=None):
    if override is not None:
        result = repository_path(override)
    else:
        recorded = Path(protocol["primary_directory"])
        parts = recorded.parts
        # Prefer this checkout, so a fresh clone never silently consults an older workspace.
        relative = Path(*parts[parts.index("artifacts"):]) if "artifacts" in parts else recorded
        result = repository_path(relative)
    require(result.is_dir(), f"Missing primary receipts: {result}; use --primary to locate them")
    return result


def check_close(actual, expected, context):
    require(finite(actual) and finite(expected)
            and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-15),
            f"Stored statistic differs: {context}")


def validate_inputs(inputs, primary_inputs):
    primary = {row["case_id"]: row for row in primary_inputs if row["max_buffer"] == 30}
    require(len(primary) == len(inputs) == 48 and len({r["case_id"] for r in inputs}) == 48,
            "Input case coverage differs")
    require(len({r["series"] for r in inputs}) == 12 and len({r["family"] for r in inputs}) == 9,
            "Input series/family coverage differs")
    keys = [(row["series"], row["model"]) for row in inputs]
    require(keys == sorted(keys) and len(set(keys)) == 48, "Input order or uniqueness differs")
    for row in inputs:
        require(row["case_id"] in primary, "Supplement case missing from primary")
        original = primary[row["case_id"]]
        require(set(row) == set(original) | {"label_dtype", "score_dtype"}
                and all(row[key] == value for key, value in original.items()), "Input identity differs from primary")
        require(row["case_id"] == f"{row['series']}|{row['model']}|30", "Malformed case ID")
        require(type(row["n"]) is int and type(row["positive_points"]) is int
                and 0 < row["positive_points"] < row["n"], "Invalid binary-label metadata")
        require(all(hash_string(row[key]) for key in ("label_member_sha256", "score_member_sha256", "npz_sha256")),
                "Invalid recorded input hash")
        require(row["label_dtype"] == "|u1" and row["score_dtype"] == "<f8", "Unexpected generated dtypes")
    for series in {row["series"] for row in inputs}:
        require({row["model"] for row in inputs if row["series"] == series} == MODELS,
                "Incomplete four-model coverage")


def check_initial_censor(reason, protocol):
    require(isinstance(reason, dict), "Missing initial censor reason")
    stage, status = reason.get("stage"), reason.get("status")
    require(stage in {"warmup", "load"}, "Initial censor stage must precede measurement")
    permitted = {"warmup": {"WARMUP_TIMEOUT", "ERROR"}, "load": {"LOAD_TIMEOUT", "ERROR"}}
    require(status in permitted[stage], "Initial censor status/stage disagree")
    if status != "ERROR":
        key = "warmup_timeout_seconds" if stage == "warmup" else "input_load_timeout_seconds"
        require(reason.get("watchdog_seconds") == protocol[key], "Initial watchdog deadline differs")


def audit_records(rows, inputs, workers, protocol):
    require(len(rows) == len(inputs) == 48, "Incomplete measurement coverage")
    rng = random.Random(protocol["seed"])
    statuses = Counter()
    maximum_error = 0.0
    per_method_error = {name: 0.0 for name in (*MAIN, DTAI)}
    comparisons = {name: {"pairs": [], "incomplete": [], "three_repeat_completed_case_ids": [],
                          "parity_invalid_case_ids": []} for name in (*MAIN[1:], DTAI)}
    active_workers = set()
    expected_startups = []
    startup_requirements = {}
    for identity, row in zip(inputs, rows):
        case = identity["case_id"]
        require(row.get("partial") is False and set(row) == set(identity) | {"methods", "orders", "partial"}
                and all(row[key] == value for key, value in identity.items()), "Raw case identity/order differs")
        methods = [*MAIN, *([DTAI] if row["model"] == "isolation_forest" else [])]
        require(set(row["methods"]) == set(methods), "Method coverage differs")
        new_workers = set(methods) - active_workers
        for method in methods:
            if method in new_workers:
                expected_startups.append((case, method))
                startup_requirements[case, method] = "READY"
                active_workers.add(method)
        expected_orders = []
        for _ in range(3):
            order = methods.copy()
            rng.shuffle(order)
            expected_orders.append(order)
        require(row["orders"] == expected_orders, "Seeded method order differs")
        reference = row["methods"]["saturation_pair"]["repetitions"]
        require(len(reference) == 3 and reference[0]["status"] == "COMPLETE", "Candidate reference missing")
        target = reference[0]["value"]
        require(len(target) == 2 and all(finite(value) for value in target), "Invalid candidate target")
        medians = {}
        for method in methods:
            repeats = row["methods"][method]["repetitions"]
            require(len(repeats) == 3 and [r["repeat"] for r in repeats] == [0, 1, 2], "Repetition coverage differs")
            durations = []
            stopped = None
            for repeat in repeats:
                status = repeat["status"]
                statuses[status] += 1
                require(status in {"COMPLETE", "TIMED_OUT", "ERROR", "NOT_ATTEMPTED"}, "Unknown repeat status")
                if status != "COMPLETE":
                    require("seconds" not in repeat and "value" not in repeat, "Censored repeat contains invented timing/output")
                if stopped is not None:
                    require(status == "NOT_ATTEMPTED" and repeat.get("reason") == stopped,
                            "Censored method resumed or changed its stopping reason")
                elif status == "COMPLETE":
                    require(finite(repeat["seconds"]) and repeat["seconds"] > 0, "Invalid completed duration")
                    values = repeat["value"]
                    require(len(values) == 2 and all(finite(value) and -1e-11 <= value <= 1 + 1e-11 for value in values),
                            "Invalid paired metric output")
                    error = max(abs(value - expected) for value, expected in zip(values, target))
                    maximum_error = max(maximum_error, error)
                    per_method_error[method] = max(per_method_error[method], error)
                    require(error <= protocol["parity_atol"], "Completed metric parity violation")
                    durations.append(repeat["seconds"])
                elif status == "NOT_ATTEMPTED":
                    require(method == DTAI and repeat["repeat"] == 0, "Unexpected initial unattempted repeat")
                    stopped = repeat.get("reason")
                    check_initial_censor(stopped, protocol)
                    if stopped["stage"] == "warmup":
                        require(method in new_workers, "Warmup failed without a recorded worker startup")
                        startup_requirements[case, method] = stopped["status"]
                else:
                    require(method == DTAI, "Required comparator failed")
                    if status == "TIMED_OUT":
                        require(repeat.get("watchdog_seconds") == protocol["dtai_call_timeout_seconds"],
                                "Timed watchdog deadline differs")
                    stopped = {key: value for key, value in repeat.items() if key != "repeat"}
                    stopped["stage"] = "measure"
            if stopped is not None:
                active_workers.discard(method)
            if len(durations) == 3:
                medians[method] = statistics.median(durations)
                if method != "saturation_pair":
                    comparisons[method]["three_repeat_completed_case_ids"].append(case)
            else:
                require(method == DTAI, "Required comparator incomplete")
                comparisons[method]["incomplete"].append({"case_id": case, "completed_repeats": len(durations),
                    "repetitions": repeats, "ratio": None,
                    "reason": "No three-repeat paired timing; no ratio inferred"})
        for method in methods[1:]:
            if method in medians:
                comparisons[method]["pairs"].append({"case_id": case, "family": row["family"],
                    "candidate_seconds": medians["saturation_pair"], "reference_seconds": medians[method],
                    "ratio_reference_over_candidate": medians[method] / medians["saturation_pair"]})
    require([(row["case_id"], row["method"]) for row in workers] == expected_startups,
            "Persistent worker startup/restart history differs")
    for worker in workers:
        key = worker["case_id"], worker["method"]
        require(worker["status"] == startup_requirements[key], "Worker startup status disagrees with censoring")
        if worker["status"] == "READY":
            require(finite(worker["warm_seconds"]) and worker["warm_seconds"] > 0, "Invalid warmup duration")
            require(worker["environment"]["numba_threads"] == 1 and all(
                    pool["num_threads"] == 1 for pool in worker["environment"]["threadpools"]),
                    "Worker compute-thread contract differs")
        elif worker["status"] == "WARMUP_TIMEOUT":
            require(worker.get("watchdog_seconds") == protocol["warmup_timeout_seconds"], "Worker warmup watchdog differs")
    for method, comparison in comparisons.items():
        pairs = comparison["pairs"]
        ratios = [pair["ratio_reference_over_candidate"] for pair in pairs]
        prescribed = 12 if method == DTAI else 48
        completed = len(comparison["three_repeat_completed_case_ids"])
        require(completed + len(comparison["incomplete"]) == prescribed, "Completion/censor coverage differs")
        comparison.update(
            prescribed_cases=prescribed, three_repeat_completed_cases=completed,
            three_repeat_completion_fraction=completed / prescribed,
            completed_parity_valid_pairs=len(pairs), incomplete_cases=len(comparison["incomplete"]),
            parity_invalid_cases=0, wins=sum(value > 1 for value in ratios),
            losses=sum(value < 1 for value in ratios), ties=sum(value == 1 for value in ratios),
            median_ratio=statistics.median(ratios) if ratios else None,
            geomean_ratio=math.exp(math.fsum(map(math.log, ratios)) / len(ratios)) if ratios else None,
            aggregate_ratio=(math.fsum(pair["reference_seconds"] for pair in pairs)
                             / math.fsum(pair["candidate_seconds"] for pair in pairs)) if pairs else None,
            minimum_ratio=min(ratios) if ratios else None,
            loss_case_ids=[pair["case_id"] for pair in pairs if pair["ratio_reference_over_candidate"] < 1],
        )
    return {"comparisons": comparisons, "max_absolute_error": maximum_error,
            "per_method_max_absolute_error": per_method_error,
            "scheduled_repetition_status_counts": dict(statuses), "worker_startups": len(workers)}


def compare_report(report, rebuilt):
    require(report["status"] == "COMPLETE_DESCRIPTIVE_SUPPLEMENT" and report["cases"] == 48
            and report["dtai_prescribed_cases"] == 12, "Stored completion coverage differs")
    require(report["parity_pass_on_completed_results"] is True and report["parity_failures"] == []
            and report["max_absolute_error"] == rebuilt["max_absolute_error"], "Stored parity claim differs")
    require(set(report["comparisons"]) == set(rebuilt["comparisons"]), "Stored comparator coverage differs")
    for method, actual in rebuilt["comparisons"].items():
        stored = report["comparisons"][method]
        require(set(stored) == set(actual) - {"loss_case_ids"}, "Stored comparator schema differs")
        for key, expected in actual.items():
            if key == "loss_case_ids":
                continue
            if type(expected) is float:
                check_close(stored[key], expected, f"{method}/{key}")
            else:
                require(type(stored[key]) is type(expected) and stored[key] == expected,
                        f"Stored comparison differs: {method}/{key}")


def audit_study(study, primary=None, expected_protocol=FROZEN_PROTOCOL):
    study = repository_path(study)
    hashes = {name: sha(study / name) for name in RECEIPTS}
    require(hashes["protocol.json"] == expected_protocol, "Protocol differs from the externally recorded frozen hash")
    protocol = read_json(study / "protocol.json")
    require(all(protocol[key] == value for key, value in CONTRACT.items()), "Frozen protocol contract differs")
    inputs, start, terminal, report = [read_json(study / name) for name in
                                     ("inputs.json", "run-start.json", "terminal.json", "report.json")]
    require(protocol["inputs_sha256"] == hashes["inputs.json"], "Input hash mismatch")
    require(start["status"] == "RUNNING" and start["completed_cases"] == 0, "Invalid start receipt")
    require(terminal["status"] == "COMPLETED" and terminal["completed_cases"] == 48, "Incomplete terminal receipt")
    inventory = protocol["source_sha256"]
    require(inventory and all(hash_string(value) for value in inventory.values()), "Malformed recorded source inventory")
    for receipt in (start, terminal):
        require(receipt["protocol_sha256"] == expected_protocol and receipt["source_sha256"] == inventory,
                "Execution source/protocol binding mismatch")
    for field, filename in (("measurements_sha256", "measurements.jsonl"), ("workers_sha256", "workers.jsonl")):
        require(terminal[field] == report[field] == hashes[filename], f"Raw log hash mismatch: {filename}")
    require(report["protocol_sha256"] == expected_protocol and report["inputs_sha256"] == hashes["inputs.json"]
            and report["scope"] == protocol["scope"], "Report binding or scope differs")
    primary = resolve_primary(protocol, primary)
    require(set(protocol["primary_receipts"]) == set(PRIMARY_RECEIPTS), "Primary receipt coverage differs")
    primary_hashes = {name: sha(primary / name) for name in PRIMARY_RECEIPTS}
    require(primary_hashes == protocol["primary_receipts"], "Bound primary receipt hash mismatch")
    primary_protocol = read_json(primary / "protocol.json")
    require(primary_protocol["phase"] == "external" and primary_protocol["cases"] == 144
            and primary_protocol["series"] == 12, "Bound primary study differs")
    shared_sources = set(inventory) & set(primary_protocol["source_sha256"])
    require(shared_sources and all(inventory[name] == primary_protocol["source_sha256"][name] for name in shared_sources),
            "Shared source identities differ from the primary study")
    validate_inputs(inputs, read_json(primary / "inputs.json"))
    rows = [parse_json(line) for line in (study / "measurements.jsonl").read_text().splitlines()]
    workers = [parse_json(line) for line in (study / "workers.jsonl").read_text().splitlines()]
    rebuilt = audit_records(rows, inputs, workers, protocol)
    compare_report(report, rebuilt)
    require(hashes == {name: sha(study / name) for name in RECEIPTS}
            and primary_hashes == {name: sha(primary / name) for name in PRIMARY_RECEIPTS},
            "Recorded evidence changed during audit")
    return {
        "schema_version": 1, "status": "PASS_RECORDED_SUPPLEMENT",
        "checked_utc": datetime.now(timezone.utc).isoformat(), "auditor_sha256": sha(__file__),
        "study_directory": str(study), "primary_directory": str(primary),
        "protocol_sha256": expected_protocol, "receipt_sha256": hashes,
        "primary_receipt_sha256": primary_hashes, "recorded_source_sha256": inventory,
        "shared_primary_source_names": sorted(shared_sources),
        "cases": 48, "series": 12, "families": 9, **rebuilt,
        "scope": "Cache-free independent reconstruction of recorded receipt identities, seeded order, worker lifecycle, "
                 "completed-output parity, censoring and paired timing statistics. No metric kernel or data array is loaded. "
                 "Source hashes are recorded identities; cached source bytes and NPZ contents are not reverified. "
                 "DTAI ratios describe only completed parity-valid pairs; no timeout is treated as an evaluator time or speed ratio. "
                 "This descriptive supplement does not change the earlier primary criterion or its outcome.",
    }


def markdown(result):
    lines = ["# Reproducible independent supplement audit", "", f"**{result['status']}**", "",
             f"Cases: {result['cases']}; series: {result['series']}; families: {result['families']}. "
             f"Maximum completed paired-output discrepancy: {result['max_absolute_error']:.16g}.", "",
             "| Comparator | Completed / prescribed | Median | Geomean | Aggregate | Wins / losses / ties | Minimum |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, value in result["comparisons"].items():
        number = lambda key: "NA" if value[key] is None else f"{value[key]:.6f}"
        lines.append(f"| {name} | {value['three_repeat_completed_cases']}/{value['prescribed_cases']} | "
                     f"{number('median_ratio')} | {number('geomean_ratio')} | {number('aggregate_ratio')} | "
                     f"{value['wins']}/{value['losses']}/{value['ties']} | {number('minimum_ratio')} |")
    lines += ["", "Ratios are comparator median time / saturation median time.", ""]
    for name, value in result["comparisons"].items():
        if value["incomplete"]:
            lines += [f"{name} incomplete cases (no inferred ratio): "
                      + ", ".join(f"`{row['case_id']}` ({row['completed_repeats']} completed repeats)" for row in value["incomplete"]), ""]
    lines += [result["scope"], "", f"Frozen protocol SHA-256: `{result['protocol_sha256']}`", "",
              f"Auditor SHA-256: `{result['auditor_sha256']}`", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=DEFAULT_STUDY)
    parser.add_argument("--primary", type=Path, help="Override the location of the bound primary receipts")
    parser.add_argument("--protocol-sha256", default=FROZEN_PROTOCOL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = repository_path(args.output)
    require(output.suffix == ".json", "--output must name a JSON file")
    study = repository_path(args.study)
    require(not output.is_relative_to(study), "Write the audit outside the immutable study directory")
    result = audit_study(study, args.primary, args.protocol_sha256)
    require(not output.is_relative_to(Path(result["primary_directory"])), "Write the audit outside the primary study directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    output.with_suffix(".md").write_text(markdown(result))
    print(json.dumps({"status": result["status"], "output": str(output), "cases": result["cases"],
                      "maximum_error": result["max_absolute_error"],
                      "repetition_statuses": result["scheduled_repetition_status_counts"]}, indent=2))


if __name__ == "__main__":
    main()
