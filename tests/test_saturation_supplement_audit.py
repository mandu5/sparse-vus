"""Cache-free replay and deliberate integrity/censoring attacks."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "experiments/audit_saturation_supplement.py"
SPEC = importlib.util.spec_from_file_location("supplement_auditor_under_test", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def put(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(AUDIT, "ROOT", tmp_path)
    primary = tmp_path / "artifacts/saturation/mac-external"
    study = tmp_path / "artifacts/saturation/mac-external-baselines"
    primary.mkdir(parents=True)
    study.mkdir()
    sources = {"src/recorded_kernel.py": "a" * 64, ".cache/absent.py": "b" * 64}
    original = []
    for width in (30, 100, 300):
        for number in range(12):
            for model in sorted(AUDIT.MODELS):
                original.append({"series": f"s{number:02}", "family": f"f{number % 9}", "model": model,
                    "n": 10, "positive_points": 2, "max_buffer": width,
                    "label_member_sha256": "c" * 64, "score_member_sha256": "d" * 64,
                    "case_id": f"s{number:02}|{model}|{width}",
                    "npz_path": f"cache/absent/s{number:02}.npz", "npz_sha256": "e" * 64})
    put(primary / "inputs.json", original)
    put(primary / "protocol.json", {"phase": "external", "cases": 144, "series": 12,
                                     "source_sha256": sources})
    for name in ("completion.json", "report.json"):
        put(primary / name, {"fixture": "Bound primary receipt; no evaluator or data cache"})
    (primary / "measurements.jsonl").write_text('{"fixture": true}\n')
    inputs = [{**row, "label_dtype": "|u1", "score_dtype": "<f8"} for row in original if row["max_buffer"] == 30]
    put(study / "inputs.json", inputs)
    protocol = {**deepcopy(AUDIT.CONTRACT), "inputs_sha256": AUDIT.sha(study / "inputs.json"),
                "source_sha256": sources, "primary_directory": "/old/worktree/artifacts/saturation/mac-external",
                "primary_receipts": {name: AUDIT.sha(primary / name) for name in AUDIT.PRIMARY_RECEIPTS},
                "scope": "Synthetic fixture, no scientific performance claim"}
    put(study / "protocol.json", protocol)
    frozen = AUDIT.sha(study / "protocol.json")
    rng = random.Random(protocol["seed"])
    rows, workers, alive = [], [], set()
    comparisons = {name: {"pairs": [], "incomplete": [], "three_repeat_completed_case_ids": [],
                          "parity_invalid_case_ids": []} for name in (*AUDIT.MAIN[1:], AUDIT.DTAI)}
    for item in inputs:
        number = int(item["series"][1:])
        methods = [*AUDIT.MAIN, *([AUDIT.DTAI] if item["model"] == "isolation_forest" else [])]
        measured = {}
        for method in methods:
            if method not in alive:
                workers.append({"case_id": item["case_id"], "method": method, "status": "READY",
                    "warm_seconds": .01, "environment": {"numba_threads": 1, "threadpools": [{"num_threads": 1}]}})
                alive.add(method)
            duration = {"saturation_pair": 1., "radix_pair": .5 if number % 2 == 0 else 2.,
                        "benchopt_pair": 2., AUDIT.DTAI: 3.}[method]
            if method == AUDIT.DTAI and number in (4, 11):
                failure = {"status": "TIMED_OUT", "watchdog_seconds": 30,
                           "censor_scope": "Parent watchdog, not evaluator duration"}
                repetitions = [{"repeat": 0, **failure},
                    *[{"repeat": i, "status": "NOT_ATTEMPTED", "reason": {**failure, "stage": "measure"}}
                      for i in (1, 2)]]
                alive.remove(method)
                comparisons[method]["incomplete"].append({"case_id": item["case_id"], "completed_repeats": 0,
                    "repetitions": deepcopy(repetitions), "ratio": None,
                    "reason": "No three-repeat paired timing; no ratio inferred"})
            else:
                repetitions = [{"repeat": i, "status": "COMPLETE", "seconds": factor * duration,
                                "value": [.6, .5]} for i, factor in enumerate((.9, 1., 1.1))]
                if method != "saturation_pair":
                    comparisons[method]["three_repeat_completed_case_ids"].append(item["case_id"])
                    comparisons[method]["pairs"].append({"case_id": item["case_id"], "family": item["family"],
                        "candidate_seconds": 1., "reference_seconds": duration, "ratio_reference_over_candidate": duration})
            measured[method] = {"repetitions": repetitions}
        orders = []
        for _ in range(3):
            order = methods.copy()
            rng.shuffle(order)
            orders.append(order)
        rows.append({**item, "methods": measured, "orders": orders, "partial": False})
    for name, records in (("measurements.jsonl", rows), ("workers.jsonl", workers)):
        (study / name).write_text("".join(json.dumps(row) + "\n" for row in records))
    binding = {"protocol_sha256": frozen, "source_sha256": sources}
    put(study / "run-start.json", {**binding, "status": "RUNNING", "completed_cases": 0})
    raw_hashes = {"measurements_sha256": AUDIT.sha(study / "measurements.jsonl"),
                  "workers_sha256": AUDIT.sha(study / "workers.jsonl")}
    put(study / "terminal.json", {**binding, **raw_hashes, "status": "COMPLETED", "completed_cases": 48})
    # Independent hand-derived summaries, not the auditor's aggregation helper.
    for method, data in comparisons.items():
        count = 10 if method == AUDIT.DTAI else 48
        prescribed = 12 if method == AUDIT.DTAI else 48
        median, geometric, aggregate, minimum = ((1.25, 1., 1.25, .5) if method == "radix_pair"
            else (2., 2., 2., 2.) if method == "benchopt_pair" else (3., 3., 3., 3.))
        data.update(prescribed_cases=prescribed, three_repeat_completed_cases=count,
            three_repeat_completion_fraction=count / prescribed, completed_parity_valid_pairs=count,
            incomplete_cases=prescribed - count, parity_invalid_cases=0,
            wins=24 if method == "radix_pair" else count, losses=24 if method == "radix_pair" else 0,
            ties=0, median_ratio=median, geomean_ratio=geometric, aggregate_ratio=aggregate, minimum_ratio=minimum)
    report = {"status": "COMPLETE_DESCRIPTIVE_SUPPLEMENT", "cases": 48, "dtai_prescribed_cases": 12,
        "parity_pass_on_completed_results": True, "max_absolute_error": 0., "parity_failures": [],
        "comparisons": comparisons, **raw_hashes, "protocol_sha256": frozen,
        "inputs_sha256": protocol["inputs_sha256"], "scope": protocol["scope"]}
    put(study / "report.json", report)
    return study, protocol, inputs, rows, workers, frozen


def test_fresh_checkout_without_cache_reconstructs_losses_and_censoring(tmp_path, monkeypatch):
    study, _, _, _, _, frozen = fixture(tmp_path, monkeypatch)
    assert not (tmp_path / "cache").exists() and not (tmp_path / ".cache").exists()
    result = AUDIT.audit_study(study.relative_to(tmp_path), expected_protocol=frozen)
    assert result["scheduled_repetition_status_counts"] == {"COMPLETE": 462, "TIMED_OUT": 2, "NOT_ATTEMPTED": 4}
    assert result["worker_startups"] == 5
    assert result["comparisons"]["radix_pair"]["losses"] == 24
    assert result["comparisons"][AUDIT.DTAI]["three_repeat_completion_fraction"] == 10 / 12
    assert len(result["comparisons"][AUDIT.DTAI]["incomplete"]) == 2
    assert "not reverified" in result["scope"]


@pytest.mark.parametrize("attack", ["resume", "reason", "invented_time", "deadline", "first_failure", "parity", "order", "worker", "coverage"])
def test_reject_malformed_censoring_and_rehashed_record_attacks(tmp_path, monkeypatch, attack):
    _, protocol, inputs, rows, workers, _ = fixture(tmp_path, monkeypatch)
    censored = next(row for row in rows if row["series"] == "s04" and row["model"] == "isolation_forest")
    repetitions = censored["methods"][AUDIT.DTAI]["repetitions"]
    if attack == "resume":
        repetitions[1] = {"repeat": 1, "status": "COMPLETE", "seconds": 1., "value": [.6, .5]}
    elif attack == "reason":
        repetitions[1]["reason"]["watchdog_seconds"] = 99
    elif attack == "invented_time":
        repetitions[0]["seconds"] = 30.
    elif attack == "deadline":
        repetitions[0]["watchdog_seconds"] = 29
    elif attack == "first_failure":
        repetitions[0] = {"repeat": 0, "status": "COMPLETE", "seconds": 1., "value": [.6, .5]}
    elif attack == "parity":
        rows[0]["methods"]["benchopt_pair"]["repetitions"][2]["value"][1] += .001
    elif attack == "order":
        rows[0]["orders"][0].reverse()
    elif attack == "worker":
        workers.pop()
    else:
        rows.pop()
    with pytest.raises(ValueError):
        AUDIT.audit_records(rows, inputs, workers, protocol)


@pytest.mark.parametrize("attack", ["raw_hash", "input_hash", "source_chain", "false_ratio", "false_censor_ratio"])
def test_reject_receipt_and_report_tampering(tmp_path, monkeypatch, attack):
    study, _, _, _, _, frozen = fixture(tmp_path, monkeypatch)
    if attack == "raw_hash":
        with (study / "measurements.jsonl").open("a") as stream:
            stream.write("{}\n")
    elif attack == "input_hash":
        value = AUDIT.read_json(study / "inputs.json")
        value[0]["n"] += 1
        put(study / "inputs.json", value)
    elif attack == "source_chain":
        value = AUDIT.read_json(study / "terminal.json")
        value["source_sha256"] = {"changed.py": "f" * 64}
        put(study / "terminal.json", value)
    else:
        value = AUDIT.read_json(study / "report.json")
        if attack == "false_ratio":
            value["comparisons"]["radix_pair"]["aggregate_ratio"] = 100.
        else:
            value["comparisons"][AUDIT.DTAI]["incomplete"][0]["ratio"] = 30.
        put(study / "report.json", value)
    with pytest.raises(ValueError):
        AUDIT.audit_study(study, expected_protocol=frozen)


def test_json_duplicates_and_nonfinite_values_fail_closed():
    for value in ('{"status": 1, "status": 2}', '{"seconds": NaN}'):
        with pytest.raises(ValueError):
            AUDIT.parse_json(value)
