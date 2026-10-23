"""Frozen synthetic structural witnesses; full-call timings are descriptive.

Freeze constructs and hashes inputs without evaluating any metric. Run is serial,
single-threaded, and refuses replay or source/input drift. Report verifies the
complete receipts before recomputing assertions and paired timing ratios.
"""
from __future__ import annotations

import os

THREAD_VARS = (
    "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS",
)
for _name in THREAD_VARS:
    os.environ[_name] = "1"

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
FAMILIES = (
    "singleton_original_last", "two_positive_separation",
    "interval8_original_last", "tied_singleton",
)
WIDTHS = (32, 128, 512, 2048)
METHOD_IDS = ("saturation", "last_positive", "active_full", "radix")
PROFILE_MODES = (("saturation", True), ("last_positive", "last_positive"),
                 ("active_full", False))
SEED = 2026102127
REPETITIONS = 3
ATOL = 1e-11


def require(condition, message):
    """Assertions remain enabled even if Python is invoked with -O."""
    if not condition:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_digest(array):
    array = np.ascontiguousarray(array)
    header = json.dumps({"dtype": array.dtype.str, "shape": list(array.shape)},
                        sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(header + b"\n" + array.tobytes()).hexdigest()


def write_json(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sources():
    names = ["src/sparse_vus/" + name for name in (
        "__init__.py", "core.py", "compiled.py", "pr_compiled.py",
        "radix.py", "saturation.py",
    )]
    names += ["experiments/benchmark_saturation_structural.py",
              "docs/saturation_structural_protocol_20261021.md"]
    return {name: digest(ROOT / name) for name in names}


def make_case(family, width):
    require(family in FAMILIES and width in WIDTHS, "Unsupported structural case")
    n = 4 * width + 3
    y = np.zeros(n, dtype=np.uint8)
    scores = np.arange(1, n + 1, dtype=np.float64)
    center = 2 * width + 1
    if family == "singleton_original_last":
        y[center] = 1
        scores[center] = -1.0
    elif family == "interval8_original_last":
        y[center:center + 8] = 1
        scores[center:center + 8] = -np.arange(1, 9, dtype=np.float64)
    elif family == "two_positive_separation":
        a, b = width + 1, 3 * width + 1
        y[[a, b]] = 1
        scores.fill(0.0)
        scores[a], scores[a - 1], scores[a + 1] = 10.0, 9.0, 8.0
        scores[b - 1], scores[b] = 7.0, -10.0
    else:
        y[center] = 1
        scores.fill(0.0)
    return y, scores


def freeze(output):
    output.mkdir(parents=True, exist_ok=False)
    (output / "inputs").mkdir()
    rows = []
    for width in WIDTHS:
        for family in FAMILIES:
            y, scores = make_case(family, width)
            case_id = f"{family}__L{width}"
            relative = f"inputs/{case_id}.npz"
            path = output / relative
            np.savez(path, labels=y, scores=scores)
            rows.append({
                "case_id": case_id, "family": family, "max_buffer": width,
                "n": len(y), "positive_points": int(y.sum()),
                "input_path": relative, "npz_sha256": digest(path),
                "label_sha256": array_digest(y), "score_sha256": array_digest(scores),
            })
    write_json(output / "inputs.json", rows)
    protocol = {
        "version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "cases": 16, "families": list(FAMILIES), "widths": list(WIDTHS),
        "repetitions": REPETITIONS, "seed": SEED, "parity_atol": ATOL,
        "method_ids": list(METHOD_IDS), "inputs_sha256": digest(output / "inputs.json"),
        "source_sha256": sources(),
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "hypotheses": {
            "singleton_original_last": "Every J_w<=min(Q_w,3); sum J<=3(L+1).",
            "two_positive_separation": "J_0=J_1=2, J_w=4 for w>=2; sum J=4L. Last-positive visits Q_w=2+4 floor(w/2), whose sum is quadratic in L.",
            "interval8_original_last": "Every J_w<=min(Q_w,ceil(16 sqrt(2)))=min(Q_w,23).",
            "tied_singleton": "All three active-list modes visit Q_w=1+2 floor(w/2); no early-stop work reduction.",
        },
        "timing": "Complete public scalar PR calls including validation and preparation; one untimed per-case call per method, then three seeded randomized serial repetitions. Profile and I/O work excluded. One compute thread.",
        "decision": "Require complete coverage, structural assertions, and parity <=1e-11. No runtime success threshold; preserve all wins and losses.",
        "scope": "Constructed theorem witnesses and a negative control, not unseen-domain confirmation, an empirical population sample, or a firstness/SOTA claim.",
    }
    write_json(output / "protocol.json", protocol)
    return {"cases": len(rows), "protocol_sha256": digest(output / "protocol.json")}


def load_contract(output):
    protocol = json.loads((output / "protocol.json").read_text())
    require(protocol["version"] == 1 and protocol["cases"] == 16
            and protocol["families"] == list(FAMILIES)
            and protocol["widths"] == list(WIDTHS)
            and protocol["method_ids"] == list(METHOD_IDS)
            and protocol["repetitions"] == REPETITIONS
            and protocol["seed"] == SEED and protocol["parity_atol"] == ATOL,
            "Unsupported frozen protocol")
    require(digest(output / "inputs.json") == protocol["inputs_sha256"], "Input manifest drift")
    rows = json.loads((output / "inputs.json").read_text())
    expected = [f"{family}__L{width}" for width in WIDTHS for family in FAMILIES]
    require([row["case_id"] for row in rows] == expected, "Missing/reordered input coverage")
    return protocol, rows


def load_case(output, row):
    path = output / row["input_path"]
    require(digest(path) == row["npz_sha256"], "NPZ input drift")
    with np.load(path, allow_pickle=False) as arrays:
        require(set(arrays.files) == {"labels", "scores"}, "Unexpected NPZ members")
        y, scores = arrays["labels"], arrays["scores"]
    expected_y, expected_scores = make_case(row["family"], row["max_buffer"])
    require(y.dtype == np.uint8 and scores.dtype == np.float64
            and np.array_equal(y, expected_y) and np.array_equal(scores, expected_scores)
            and len(y) == row["n"] and int(y.sum()) == row["positive_points"]
            and array_digest(y) == row["label_sha256"]
            and array_digest(scores) == row["score_sha256"], "Input identity/recipe mismatch")
    return y, scores


def evaluators():
    from sparse_vus.radix import sparse_pr_radix_jit
    from sparse_vus.saturation import sparse_pr_saturation_jit
    return {
        "saturation": sparse_pr_saturation_jit,
        "last_positive": lambda y, s, w: sparse_pr_saturation_jit(y, s, w, stop="last_positive"),
        "active_full": lambda y, s, w: sparse_pr_saturation_jit(y, s, w, stop=False),
        "radix": sparse_pr_radix_jit,
    }


def environment():
    import numba
    from threadpoolctl import threadpool_info
    if sys.platform == "darwin":
        cpu = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    elif Path("/proc/cpuinfo").exists():
        cpu = next((line.split(":", 1)[1].strip()
                    for line in Path("/proc/cpuinfo").read_text().splitlines()
                    if line.startswith("model name")), "not captured")
    else:
        cpu = platform.processor()
    pools = threadpool_info()
    require(numba.get_num_threads() == 1 and all(p["num_threads"] == 1 for p in pools),
            "Single-thread contract violated")
    return {
        "utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "platform": platform.platform(), "cpu_model": cpu, "cpu_count": os.cpu_count(),
        "numpy": np.__version__, "numba": numba.__version__,
        "numba_threads": numba.get_num_threads(), "threadpools": pools,
        "thread_environment": {name: os.environ[name] for name in THREAD_VARS},
        "process_snapshot": subprocess.check_output(["ps", "-axo", "pid,pcpu,comm"], text=True).splitlines(),
        "scope": "Local host; start/end snapshots do not certify continuous isolation.",
    }


def validate_record(row):
    width, family = row["max_buffer"], row["family"]
    require(list(row["methods"]) == list(METHOD_IDS), "Incomplete method coverage")
    require(len(row["orders"]) == REPETITIONS
            and all(sorted(order) == sorted(METHOD_IDS) for order in row["orders"]),
            "Invalid repetition orders")
    reference = row["methods"]["radix"]["values"][0]
    maximum_error = 0.0
    for data in row["methods"].values():
        require(len(data["seconds"]) == REPETITIONS and len(data["values"]) == REPETITIONS
                and all(math.isfinite(t) and t > 0 for t in data["seconds"])
                and all(math.isfinite(v) and -ATOL <= v <= 1 + ATOL for v in data["values"]),
                "Invalid timing or PR values")
        maximum_error = max(maximum_error, *(abs(v - reference) for v in data["values"]))
    profiles = row["profiles"]
    require(set(profiles) == {name for name, _ in PROFILE_MODES}, "Missing profiles")
    positives = 8 if family == "interval8_original_last" else (2 if family == "two_positive_separation" else 1)
    intervals = 2 if family == "two_positive_separation" else 1
    expected_active = [positives + 2 * intervals * (w // 2) for w in range(width + 1)]
    for profile in profiles.values():
        require(profile["K"] == intervals and profile["Q"] == expected_active[-1]
                and profile["active"] == expected_active
                and len(profile["visited"]) == width + 1
                and all(type(j) is int and 0 < j <= q
                        for j, q in zip(profile["visited"], expected_active)),
                "Incorrect active geometry or visit profile")
        require(all(math.isfinite(profile["values"][metric]) for metric in ("roc", "pr")),
                "Nonfinite profile values")
        maximum_error = max(maximum_error, abs(profile["values"]["pr"] - reference))
        require(abs(profile["values"]["roc"] - profiles["saturation"]["values"]["roc"]) <= ATOL,
                "ROC profile ablation mismatch")
    candidate = profiles["saturation"]["visited"]
    require(profiles["active_full"]["visited"] == expected_active
            and profiles["last_positive"]["visited"] == expected_active
            and all(j <= q for j, q in zip(candidate, expected_active)),
            "Expected complete active scans for the controls")
    if family == "singleton_original_last":
        require(all(j <= min(q, 3) for j, q in zip(candidate, expected_active))
                and sum(candidate) <= 3 * (width + 1), "Singleton mass bound failed")
    elif family == "interval8_original_last":
        require(all(j <= min(q, 23) for j, q in zip(candidate, expected_active)),
                "Eight-positive interval mass bound failed")
    elif family == "two_positive_separation":
        require(candidate == [2, 2] + [4] * (width - 1)
                and sum(candidate) == 4 * width, "Two-positive separation count failed")
    else:
        require(candidate == expected_active and max(candidate) > 3,
                "All-tied negative control failed")
    require(maximum_error <= ATOL, "PR parity failed")
    return maximum_error


def run(output, expected_hash):
    from sparse_vus.saturation import profile_saturation
    from threadpoolctl import threadpool_limits
    require(expected_hash and digest(output / "protocol.json") == expected_hash,
            "Supply the exact frozen --protocol-sha256")
    protocol, inputs = load_contract(output)
    require(sources() == protocol["source_sha256"], "Source/protocol document drift")
    for name in ("run-start.json", "environment.json", "environment-end.json",
                 "measurements.jsonl", "completion.json", "report.json"):
        require(not (output / name).exists(), "Run already started; freeze a new output to replay")
    calls = evaluators()
    rng = random.Random(SEED)
    write_json(output / "run-start.json", {
        "protocol_sha256": expected_hash, "source_sha256": sources(),
        "utc": datetime.now(timezone.utc).isoformat(),
    })
    with threadpool_limits(limits=1):
        warm_y, warm_scores = make_case(FAMILIES[0], WIDTHS[0])
        for function in calls.values():
            function(warm_y, warm_scores, WIDTHS[0])
        for _, stop in PROFILE_MODES:
            profile_saturation(warm_y, warm_scores, WIDTHS[0], stop=stop)
        write_json(output / "environment.json", environment())
        with (output / "measurements.jsonl").open("x") as stream:
            for index, item in enumerate(inputs):
                y, scores = load_case(output, item)
                warm_order = list(calls)
                rng.shuffle(warm_order)
                for name in warm_order:
                    calls[name](y, scores, item["max_buffer"])
                measured = {name: {"seconds": [], "values": []} for name in calls}
                orders = []
                for _ in range(REPETITIONS):
                    order = list(calls)
                    rng.shuffle(order)
                    orders.append(order)
                    for name in order:
                        start = time.perf_counter_ns()
                        value = calls[name](y, scores, item["max_buffer"])
                        elapsed = (time.perf_counter_ns() - start) / 1e9
                        measured[name]["seconds"].append(elapsed)
                        measured[name]["values"].append(float(value))
                profiles = {name: profile_saturation(y, scores, item["max_buffer"], stop=stop)
                            for name, stop in PROFILE_MODES}
                record = {**item, "warm_order": warm_order, "orders": orders,
                          "methods": measured, "profiles": profiles}
                stream.write(json.dumps(record, allow_nan=False) + "\n")
                stream.flush()
                validate_record(record)
                require(array_digest(y) == item["label_sha256"]
                        and array_digest(scores) == item["score_sha256"], "Evaluator mutated input")
                print(json.dumps({"completed": index + 1, "total": len(inputs),
                                  "case_id": item["case_id"]}), flush=True)
        write_json(output / "environment-end.json", environment())
    require(sources() == protocol["source_sha256"], "Source drift during measurement")
    write_json(output / "completion.json", {
        "status": "COMPLETED", "cases": len(inputs), "protocol_sha256": expected_hash,
        "source_sha256": sources(), "utc": datetime.now(timezone.utc).isoformat(),
        "measurements_sha256": digest(output / "measurements.jsonl"),
        "environment_sha256": digest(output / "environment.json"),
        "environment_end_sha256": digest(output / "environment-end.json"),
    })
    return report(output)


def report(output):
    protocol, inputs = load_contract(output)
    start = json.loads((output / "run-start.json").read_text())
    completed = json.loads((output / "completion.json").read_text())
    protocol_hash = digest(output / "protocol.json")
    require(sources() == protocol["source_sha256"], "Source drift before report")
    require(completed["status"] == "COMPLETED" and completed["cases"] == len(inputs)
            and start["protocol_sha256"] == completed["protocol_sha256"] == protocol_hash
            and start["source_sha256"] == completed["source_sha256"] == protocol["source_sha256"]
            and digest(output / "measurements.jsonl") == completed["measurements_sha256"]
            and digest(output / "environment.json") == completed["environment_sha256"]
            and digest(output / "environment-end.json") == completed["environment_end_sha256"],
            "Completion/protocol/measurement receipt mismatch")
    rows = [json.loads(line) for line in (output / "measurements.jsonl").read_text().splitlines()]
    require(len(rows) == len(inputs), "Incomplete measured cases")
    maximum_error, summaries = 0.0, []
    rng = random.Random(SEED)
    for row, item in zip(rows, inputs):
        require(all(row.get(key) == value for key, value in item.items()), "Measured input identity drift")
        warm_order = list(METHOD_IDS)
        rng.shuffle(warm_order)
        orders = []
        for _ in range(REPETITIONS):
            order = list(METHOD_IDS)
            rng.shuffle(order)
            orders.append(order)
        require(row["warm_order"] == warm_order and row["orders"] == orders,
                "Execution orders differ from the frozen randomization")
        load_case(output, item)
        maximum_error = max(maximum_error, validate_record(row))
        medians = {name: statistics.median(data["seconds"]) for name, data in row["methods"].items()}
        summaries.append({
            "case_id": row["case_id"], "family": row["family"],
            "n": row["n"], "max_buffer": row["max_buffer"],
            "median_seconds": medians,
            "baseline_over_saturation": {name: medians[name] / medians["saturation"]
                                         for name in METHOD_IDS if name != "saturation"},
            "visited_sums": {name: sum(profile["visited"]) for name, profile in row["profiles"].items()},
            "maximum_support_size": row["profiles"]["saturation"]["Q"],
            "radix_full_support_position_budget": (row["max_buffer"] + 1) * row["profiles"]["saturation"]["Q"],
        })
    result = {
        "cases": len(rows), "structural_assertions_pass": True,
        "parity_pass": True, "max_absolute_pr_error": maximum_error,
        "protocol_sha256": protocol_hash, "inputs_sha256": protocol["inputs_sha256"],
        "measurements_sha256": completed["measurements_sha256"], "results": summaries,
        "scope": protocol["scope"],
        "runtime_decision": "Descriptive only; no runtime pass/fail threshold or population confidence interval.",
        "radix_budget_scope": "Analytic maximum-support positions per width, not an instrumented radix profile.",
    }
    path = output / "report.json"
    if path.exists():
        require(json.loads(path.read_text()) == result, "Existing report differs; refusing overwrite")
    else:
        write_json(path, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run", "report"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--protocol-sha256")
    args = parser.parse_args()
    if args.action == "freeze":
        result = freeze(args.output)
    elif args.action == "run":
        result = run(args.output, args.protocol_sha256)
    else:
        result = report(args.output)
    print(json.dumps(result, indent=2, allow_nan=False))
