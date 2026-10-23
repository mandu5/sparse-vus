"""Separate frozen paired-output supplement; never modifies the primary study.

Run only after other controlled timings have finished. External sources must
already be fetched by their existing adapters; this script never vendors them.
Every timed call runs in a persistent, warmed spawn worker. IPC, input loading,
imports and compilation are outside its internal full-public-call timer.
"""
from __future__ import annotations

import os
for _thread_name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                     "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_thread_name] = "1"

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import multiprocessing as mp
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))
SCRIPT = "experiments/benchmark_saturation_external_baselines.py"
DESIGN = "docs/saturation_external_baseline_protocol_20261021.md"
MAIN_METHODS = ("saturation_pair", "radix_pair", "benchopt_pair")
DTAI = "dtaianomaly_pair"
MODELS = ("isolation_forest", "pca_reconstruction", "knn_distance", "robust_marginal_z")
SEED = 2026102127
CONTRACT = {
    "version": 1, "width": 30, "cases": 48, "series": 12, "families": 9,
    "repetitions": 3, "seed": SEED, "parity_atol": 1e-11,
    "main_methods": list(MAIN_METHODS), "dtai_method": DTAI,
    "dtai_model": "isolation_forest", "dtai_cases": 12,
    "warmup_timeout_seconds": 120, "dtai_call_timeout_seconds": 30,
    "other_call_timeout_seconds": 300, "input_load_timeout_seconds": 120,
    "output": ["roc", "pr"], "compute_threads": 1,
}
EXTERNAL = {
    ".cache/benchopt_vus/metrics.py":
        "298c746c84a28f9296b015bd70eac984d27be5452e3ca42c853de05328c194a8",
    ".cache/dtaianomaly/_volume_under_surface_metrics.py":
        "728045cd8ddf0caa6aab10a9ab66f5f876ee77e5d0ae80dfbce5029eab9ed5b7",
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def append_json(stream, value):
    stream.write(json.dumps(value, allow_nan=False) + "\n")
    stream.flush()


def source_hashes():
    paths = sorted((ROOT / "src/sparse_vus").glob("*.py"))
    paths += [ROOT / name for name in (SCRIPT, DESIGN,
              "experiments/benchopt_vus_adapter.py", "experiments/dtaianomaly_adapter.py")]
    for relative, expected in EXTERNAL.items():
        require(digest(ROOT / relative) == expected, f"Pinned external source mismatch: {relative}")
        paths.append(ROOT / relative)
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def array_sha(array):
    import numpy as np
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def load_case(row):
    import numpy as np
    path = ROOT / row["npz_path"]
    require(digest(path) == row["npz_sha256"], "NPZ identity changed")
    with np.load(path, allow_pickle=False) as arrays:
        labels = np.ascontiguousarray(arrays["labels"])
        scores = np.ascontiguousarray(arrays[row["model"]])
    require(labels.ndim == scores.ndim == 1 and len(labels) == len(scores) == row["n"],
            "Input shape mismatch")
    require(array_sha(labels) == row["label_member_sha256"] and
            array_sha(scores) == row["score_member_sha256"], "Array identity mismatch")
    require(int(labels.sum()) == row["positive_points"], "Positive count mismatch")
    require(np.isin(labels, [0, 1]).all() and 0 < labels.sum() < len(labels)
            and np.isfinite(scores).all(), "Invalid metric input")
    if "label_dtype" in row:
        require(labels.dtype.str == row["label_dtype"] and scores.dtype.str == row["score_dtype"],
                "Input dtype changed")
    return labels, scores


def freeze(output, primary):
    """Freeze a new supplement only after the original external run is complete."""
    require(not output.exists(), "Refusing to replace an existing supplement")
    p = read_json(primary / "protocol.json")
    c = read_json(primary / "completion.json")
    r = read_json(primary / "report.json")
    ph = digest(primary / "protocol.json")
    require(p["phase"] == "external" and p["cases"] == 144 and p["series"] == 12,
            "Expected the complete frozen external primary study")
    require(c["status"] == "COMPLETED" and c["protocol_sha256"] == ph
            and r["protocol_sha256"] == ph and r["cases"] == 144,
            "Primary completion/report is not bound to its protocol")
    require(digest(primary / "inputs.json") == p["inputs_sha256"]
            and digest(primary / "measurements.jsonl") == c["measurements_sha256"]
            and r["measurements_sha256"] == c["measurements_sha256"],
            "Primary receipt binding mismatch")
    fields = ("series", "family", "model", "n", "positive_points", "max_buffer",
              "label_member_sha256", "score_member_sha256", "case_id", "npz_path", "npz_sha256")
    inputs = [{key: row[key] for key in fields} for row in read_json(primary / "inputs.json")
              if row["max_buffer"] == CONTRACT["width"]]
    inputs.sort(key=lambda row: (row["series"], row["model"]))
    require(len(inputs) == 48 and len({r["case_id"] for r in inputs}) == 48
            and len({r["series"] for r in inputs}) == 12
            and len({r["family"] for r in inputs}) == 9, "Supplement input coverage differs")
    for series in {r["series"] for r in inputs}:
        require({r["model"] for r in inputs if r["series"] == series} == set(MODELS),
                "Incomplete model coverage")
    for row in inputs:
        y, s = load_case(row)
        row.update(label_dtype=y.dtype.str, score_dtype=s.dtype.str)
    require(len({(r["label_dtype"], r["score_dtype"]) for r in inputs}) == 1,
            "This fixed warm-up protocol requires uniform generated input dtypes")
    bindings = source_hashes()
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "inputs.json", inputs)
    protocol = {
        **CONTRACT, "created_utc": utc(), "inputs_sha256": digest(output / "inputs.json"),
        "source_sha256": bindings,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "primary_receipts": {name: digest(primary / name) for name in
            ("protocol.json", "inputs.json", "completion.json", "report.json", "measurements.jsonl")},
        "primary_directory": str(primary.resolve()),
        "status": "FROZEN_SUPPLEMENT_NO_SUPPLEMENTAL_OUTCOMES",
        "scope": "Separate descriptive paired ROC/PR supplement, fixed after the primary study. "
                 "Does not replace its L=30 primary failure or change its decision rule.",
        "timing": "Three seeded randomized serial full public calls per case and method; "
                  "one persistent warmed spawn worker per method; input I/O, IPC, imports and "
                  "compilation excluded; validation and metric preparation included as implemented.",
        "dtai_censoring": "On the first timed timeout or error for a case, terminate that worker "
                          "and skip its remaining repeats for that case. Restart and warm for the "
                          "next prescribed case. Ratios require three completed parity-valid repeats. "
                          "Warm-up timeout is separate and supplies no runtime lower bound.",
        "comparison": "Benchopt thre=n and DTAI max_samples=n; unchanged pinned source AST adapters. "
                      "Both candidate and v0.3 radix return paired ROC/PR. Native DTAI parallel=True "
                      "and fastmath=True remain enabled with one Numba thread. Benchopt's native "
                      "kernel has less generic validation than the candidate public API.",
        "decision": "Descriptive only: parity, full timing distributions, losses and censor counts. "
                    "No new PASS criterion, no pooling of old timings, no censored speed ratios.",
    }
    write_json(output / "protocol.json", protocol)
    return {"protocol_sha256": digest(output / "protocol.json"), "cases": 48, "dtai_cases": 12}


def validate_frozen(output, expected):
    require(digest(output / "protocol.json") == expected, "Protocol hash mismatch")
    p = read_json(output / "protocol.json")
    require(all(p.get(key) == value for key, value in CONTRACT.items()), "Frozen fixed contract differs")
    require(digest(output / "inputs.json") == p["inputs_sha256"], "Input manifest drift")
    require(source_hashes() == p["source_sha256"], "Measured source drift")
    return p, read_json(output / "inputs.json")


def environment():
    import importlib.metadata
    import numba
    from threadpoolctl import threadpool_info
    if sys.platform == "darwin":
        cpu = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    elif Path("/proc/cpuinfo").exists():
        cpu = next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                    if line.startswith("model name")), platform.processor())
    else:
        cpu = platform.processor()
    return {"utc": utc(), "pid": os.getpid(), "python": sys.version, "platform": platform.platform(),
            "cpu": cpu, "numba_threads": numba.get_num_threads(), "threadpools": threadpool_info(),
            "packages": {name: importlib.metadata.version(name) for name in
                         ("numpy", "numba", "threadpoolctl")},
            "thread_environment": {name: os.environ.get(name) for name in
                ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS")}}


def _worker(connection, method, first_row, expected_sources):
    """The child alone owns evaluator state; every call uses the same timer scope."""
    stage = "warmup"
    try:
        require(source_hashes() == expected_sources, "Worker source drift")
        import numpy as np
        import numba
        from threadpoolctl import threadpool_limits
        numba.set_num_threads(1)
        with threadpool_limits(limits=1):
            if method == "saturation_pair":
                from sparse_vus.saturation import sparse_vus_saturation_jit as evaluator
            elif method == "radix_pair":
                from sparse_vus.radix import sparse_vus_radix_jit as evaluator
            elif method == "benchopt_pair":
                from benchopt_vus_adapter import benchopt_vus
                evaluator = lambda y, s, w: benchopt_vus(y, s, w, max_samples=len(s))
            elif method == DTAI:
                from dtaianomaly_adapter import dtaianomaly_vus
                evaluator = lambda y, s, w: dtaianomaly_vus(y, s, w, max_samples=len(s))
            else:
                raise ValueError("Unknown method")
            warm_y = np.array([0, 1, 0, 0, 1, 0], dtype=np.dtype(first_row["label_dtype"]))
            warm_s = np.array([0., 4., 3., 2., 1., 0.], dtype=np.dtype(first_row["score_dtype"]))
            before = time.perf_counter()
            warm_result = [float(v) for v in evaluator(warm_y, warm_s, 6)]
            connection.send({"status": "READY", "method": method, "warm_seconds": time.perf_counter()-before,
                             "warm_result": warm_result, "environment": environment()})
            y = scores = None
            while True:
                command = connection.recv()
                if command["action"] == "stop":
                    return
                if command["action"] == "load":
                    stage = "load"
                    y, scores = load_case(command["row"])
                    connection.send({"status": "LOADED"})
                elif command["action"] == "measure":
                    stage = "measure"
                    require(y is not None, "No input loaded")
                    start = time.perf_counter_ns()
                    result = evaluator(y, scores, CONTRACT["width"])
                    seconds = (time.perf_counter_ns() - start) / 1e9
                    value = [float(v) for v in result]
                    require(len(value) == 2 and all(math.isfinite(v) for v in value)
                            and math.isfinite(seconds) and seconds > 0, "Invalid evaluator output")
                    connection.send({"status": "COMPLETE", "seconds": seconds, "value": value})
                else:
                    raise ValueError("Unknown worker command")
    except BaseException as error:
        try:
            connection.send({"status": "ERROR", "stage": stage, "error": repr(error),
                             "traceback": traceback.format_exc()})
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        connection.close()


class Worker:
    def __init__(self, method, row, sources):
        self.method = method
        context = mp.get_context("spawn")
        self.connection, child = context.Pipe()
        self.process = context.Process(target=_worker, args=(child, method, row, sources))
        self.process.start()
        child.close()

    def receive(self, seconds, timeout_status):
        try:
            if self.connection.poll(seconds):
                return self.connection.recv()
        except (EOFError, OSError) as error:
            return {"status": "ERROR", "error": repr(error), "exitcode": self.process.exitcode}
        return {"status": timeout_status, "watchdog_seconds": seconds,
                "censor_scope": "Parent wall-clock watchdog, not a measured evaluator duration"}

    def close(self):
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(timeout=2)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(timeout=2)
        self.connection.close()
        require(not self.process.is_alive(), "Could not stop timed-out worker")


def run(output, expected):
    p, inputs = validate_frozen(output, expected)
    require(not any((output / name).exists() for name in
                    ("terminal.json", "measurements.jsonl", "workers.jsonl", "report.json")),
            "Run already started; never replay into an existing receipt directory")
    terminal = {"status": "RUNNING", "started_utc": utc(), "protocol_sha256": expected,
                "source_sha256": p["source_sha256"], "completed_cases": 0}
    write_json(output / "terminal.json", terminal)
    write_json(output / "run-start.json", terminal)
    workers = {}
    rng = random.Random(SEED)
    try:
        with (output / "measurements.jsonl").open("x") as stream, (output / "workers.jsonl").open("x") as boots:
            for row in inputs:
                names = [*MAIN_METHODS, *([DTAI] if row["model"] == "isolation_forest" else [])]
                records = {name: {"repetitions": []} for name in names}
                disabled = {}
                for name in names:
                    if name not in workers:
                        worker = Worker(name, row, p["source_sha256"])
                        workers[name] = worker
                        ready = worker.receive(p["warmup_timeout_seconds"], "WARMUP_TIMEOUT")
                        append_json(boots, {"case_id": row["case_id"], "method": name, "utc": utc(), **ready})
                        if ready["status"] != "READY":
                            workers.pop(name).close()
                            disabled[name] = {**ready, "stage": "warmup"}
                    if name not in disabled:
                        workers[name].connection.send({"action": "load", "row": row})
                        loaded = workers[name].receive(p["input_load_timeout_seconds"], "LOAD_TIMEOUT")
                        if loaded["status"] != "LOADED":
                            workers.pop(name).close()
                            disabled[name] = {**loaded, "stage": "load"}
                    if name in disabled and name != DTAI:
                        raise RuntimeError(f"Required comparator startup failed: {name}: {disabled[name]}")
                orders = []
                for repeat in range(p["repetitions"]):
                    order = names.copy()
                    rng.shuffle(order)
                    orders.append(order)
                    for name in order:
                        if name in disabled:
                            result = {"status": "NOT_ATTEMPTED", "reason": disabled[name]}
                        else:
                            workers[name].connection.send({"action": "measure"})
                            timeout = p["dtai_call_timeout_seconds"] if name == DTAI else p["other_call_timeout_seconds"]
                            result = workers[name].receive(timeout, "TIMED_OUT")
                            if result["status"] != "COMPLETE":
                                workers.pop(name).close()
                                disabled[name] = {**result, "stage": "measure"}
                        records[name]["repetitions"].append({"repeat": repeat, **result})
                        if result["status"] not in ("COMPLETE", "NOT_ATTEMPTED") and name != DTAI:
                            append_json(stream, {**row, "methods": records, "orders": orders, "partial": True})
                            raise RuntimeError(f"Required comparator call failed: {name}: {result}")
                append_json(stream, {**row, "methods": records, "orders": orders, "partial": False})
                terminal["completed_cases"] += 1
                write_json(output / "terminal.json", terminal)
                print(json.dumps({"completed": terminal["completed_cases"], "total": len(inputs),
                                  "case_id": row["case_id"], "dtai_disabled": disabled.get(DTAI)}), flush=True)
        require(source_hashes() == p["source_sha256"], "Source drift during supplement")
        terminal.update(status="COMPLETED", ended_utc=utc(),
                        measurements_sha256=digest(output / "measurements.jsonl"),
                        workers_sha256=digest(output / "workers.jsonl"))
        write_json(output / "terminal.json", terminal)
        return report(output, expected)
    except BaseException as error:
        terminal.update(status="FAILED", ended_utc=utc(), error=repr(error), traceback=traceback.format_exc())
        for name in ("measurements.jsonl", "workers.jsonl"):
            if (output / name).exists():
                terminal[name + "_sha256"] = digest(output / name)
        write_json(output / "terminal.json", terminal)
        raise
    finally:
        for worker in workers.values():
            worker.close()


def report(output, expected):
    p, inputs = validate_frozen(output, expected)
    terminal = read_json(output / "terminal.json")
    start = read_json(output / "run-start.json")
    require(terminal["status"] == "COMPLETED" and terminal["completed_cases"] == len(inputs),
            "Full report requires a completed supplement; partial receipts remain unaggregated")
    for receipt in (start, terminal):
        require(receipt["protocol_sha256"] == expected and receipt["source_sha256"] == p["source_sha256"],
                "Execution receipt binding mismatch")
    require(digest(output / "measurements.jsonl") == terminal["measurements_sha256"]
            and digest(output / "workers.jsonl") == terminal["workers_sha256"], "Raw receipt digest mismatch")
    rows = [json.loads(line) for line in (output / "measurements.jsonl").read_text().splitlines()]
    require(len(rows) == len(inputs) == 48, "Incomplete measurement coverage")
    maximum_error = 0.0
    errors = []
    comparisons = {name: {"pairs": [], "incomplete": [], "three_repeat_completed_case_ids": [],
                          "parity_invalid_case_ids": []}
                   for name in (*MAIN_METHODS[1:], DTAI)}
    order_rng = random.Random(p["seed"])
    for expected_row, row in zip(inputs, rows):
        require(all(row.get(k) == v for k, v in expected_row.items()) and row.get("partial") is False,
                "Measurement input identity/order mismatch")
        names = [*MAIN_METHODS, *([DTAI] if row["model"] == "isolation_forest" else [])]
        require(set(row["methods"]) == set(names), "Method coverage mismatch")
        expected_orders = []
        for _ in range(p["repetitions"]):
            order = names.copy()
            order_rng.shuffle(order)
            expected_orders.append(order)
        require(row["orders"] == expected_orders, "Recorded method order differs from frozen randomization")
        medians = {}
        parity = {}
        reference = row["methods"]["saturation_pair"]["repetitions"]
        require(len(reference) == 3 and all(x["status"] == "COMPLETE" for x in reference),
                "Candidate requires three completed repeats")
        target = reference[0]["value"]
        for name in names:
            reps = row["methods"][name]["repetitions"]
            require(len(reps) == 3 and [r["repeat"] for r in reps] == [0, 1, 2], "Repeat coverage mismatch")
            require(all(r["status"] in {"COMPLETE", "TIMED_OUT", "NOT_ATTEMPTED", "ERROR"} for r in reps),
                    "Unknown measurement status")
            stopped_reason = None
            for rep in reps:
                if stopped_reason is not None:
                    require(rep["status"] == "NOT_ATTEMPTED" and rep.get("reason") == stopped_reason,
                            "A censored method resumed or changed its stopping reason")
                elif rep["status"] == "NOT_ATTEMPTED":
                    stopped_reason = rep.get("reason")
                    require(name == DTAI and rep["repeat"] == 0 and isinstance(stopped_reason, dict)
                            and stopped_reason.get("stage") in {"warmup", "load"}
                            and stopped_reason.get("status") in {"WARMUP_TIMEOUT", "LOAD_TIMEOUT", "ERROR"},
                            "Unexpected unattempted repetition")
                elif rep["status"] in {"TIMED_OUT", "ERROR"}:
                    require(name == DTAI, "A required method failed")
                    if rep["status"] == "TIMED_OUT":
                        require(rep.get("watchdog_seconds") == p["dtai_call_timeout_seconds"],
                                "Timed watchdog differs from the frozen deadline")
                    stopped_reason = {k: v for k, v in rep.items() if k != "repeat"}
                    stopped_reason["stage"] = "measure"
            completed = [r for r in reps if r["status"] == "COMPLETE"]
            parity[name] = True
            for rep in completed:
                require(math.isfinite(rep["seconds"]) and rep["seconds"] > 0
                        and len(rep["value"]) == 2 and all(math.isfinite(v) for v in rep["value"]),
                        "Invalid measured time/output")
                error = max(abs(a-b) for a, b in zip(rep["value"], target))
                maximum_error = max(maximum_error, error)
                if error > p["parity_atol"]:
                    parity[name] = False
                    errors.append({"case_id": row["case_id"], "method": name, "repeat": rep["repeat"],
                                   "absolute_error": error})
            if len(completed) == 3:
                medians[name] = statistics.median(r["seconds"] for r in completed)
                if name != "saturation_pair":
                    comparisons[name]["three_repeat_completed_case_ids"].append(row["case_id"])
            else:
                require(name == DTAI, "Required comparator is incomplete")
                comparisons[name]["incomplete"].append({"case_id": row["case_id"],
                    "completed_repeats": len(completed), "repetitions": reps,
                    "ratio": None, "reason": "No three-repeat paired timing; no ratio inferred"})
        for name in names[1:]:
            if not parity[name] or not parity["saturation_pair"]:
                comparisons[name]["parity_invalid_case_ids"].append(row["case_id"])
            if name in medians and parity[name] and parity["saturation_pair"]:
                comparisons[name]["pairs"].append({"case_id": row["case_id"], "family": row["family"],
                    "candidate_seconds": medians["saturation_pair"], "reference_seconds": medians[name],
                    "ratio_reference_over_candidate": medians[name] / medians["saturation_pair"]})
    for name, data in comparisons.items():
        pairs = data["pairs"]
        ratios = [r["ratio_reference_over_candidate"] for r in pairs]
        prescribed = p["dtai_cases"] if name == DTAI else p["cases"]
        completed_count = len(data["three_repeat_completed_case_ids"])
        require(completed_count + len(data["incomplete"]) == prescribed,
                "Completion and censoring counts do not cover the prescribed cases")
        data.update(completed_parity_valid_pairs=len(pairs), incomplete_cases=len(data["incomplete"]),
                    prescribed_cases=prescribed, three_repeat_completed_cases=completed_count,
                    three_repeat_completion_fraction=completed_count / prescribed,
                    parity_invalid_cases=len(data["parity_invalid_case_ids"]),
                    wins=sum(r > 1 for r in ratios), losses=sum(r < 1 for r in ratios),
                    ties=sum(r == 1 for r in ratios), median_ratio=statistics.median(ratios) if ratios else None,
                    geomean_ratio=math.exp(statistics.mean(math.log(r) for r in ratios)) if ratios else None,
                    aggregate_ratio=(sum(r["reference_seconds"] for r in pairs) /
                                     sum(r["candidate_seconds"] for r in pairs)) if pairs else None,
                    minimum_ratio=min(ratios) if ratios else None)
    result = {"status": "COMPLETE_DESCRIPTIVE_SUPPLEMENT", "cases": len(rows), "dtai_prescribed_cases": 12,
              "parity_pass_on_completed_results": not errors, "max_absolute_error": maximum_error,
              "parity_failures": errors, "comparisons": comparisons, "protocol_sha256": expected,
              "inputs_sha256": p["inputs_sha256"], "measurements_sha256": terminal["measurements_sha256"],
              "workers_sha256": terminal["workers_sha256"], "scope": p["scope"],
              "censoring": "Incomplete DTAI cases are enumerated separately. Timed watchdog expiry "
                           "and warm-up failure are not evaluator times or manufactured speed ratios.",
              "uncertainty": "Descriptive paired medians; no new hypothesis-test or PASS criterion. "
                             "Three repeats do not measure machine-population uncertainty."}
    write_json(output / "report.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run", "report"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--primary", type=Path, default=ROOT / "artifacts/saturation/mac-external")
    parser.add_argument("--protocol-sha256")
    args = parser.parse_args()
    if args.command == "freeze":
        result = freeze(args.output, args.primary)
    else:
        require(bool(args.protocol_sha256), "Run/report require the externally recorded protocol SHA256")
        result = (run if args.command == "run" else report)(args.output, args.protocol_sha256)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
