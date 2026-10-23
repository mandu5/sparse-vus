"""Frozen complete-call certificate cost supplement; no corpus selection by outcome.

Commands: freeze; run --protocol-sha256 HASH --idle-host-confirmed; report.
The fixed 30-series subset predates all corpus metric outcomes. This supplement
is frozen separately, before its author reads certificate results or times data.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import platform
import statistics
import sys
import time
import uuid

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
import msad_sampling_study as common

OUT = ROOT / "artifacts/msad-certificate-cost-20261023"
MANIFEST = "artifacts/msad-corpus-20261023/manifest.json"
MANIFEST_SHA = "5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59"
SUBSET = "artifacts/msad-corpus-20261023/timing-subset-proposal.json"
METHODS = ("certificate", "radix_exact")


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def select_rows(rows, proposal):
    lookup = {r["series"]: r for r in rows}
    selected = []
    for frozen in proposal["cases"]:
        row = lookup.get(frozen["series"])
        if row is None or any(row.get(k) != v for k, v in frozen.items()):
            raise ValueError("Fixed subset input identity mismatch")
        selected.append(row)
    if len(selected) != proposal["series_count"] or len({r["series"] for r in selected}) != len(selected):
        raise ValueError("Fixed subset duplicate/count mismatch")
    return selected


def schedule(protocol):
    tasks = []
    for row in protocol["series"]:
        for model in protocol["models"]:
            for repetition in range(protocol["repetitions"]):
                seed = f"{protocol['seed']}|certificate-cost|{row['series']}|{model}|{repetition}"
                flip = hashlib.sha256(seed.encode()).digest()[0] & 1
                order = METHODS if not flip else METHODS[::-1]
                for order_index, method in enumerate(order):
                    key = json.dumps([row["series"], model, repetition, method], separators=(",", ":"))
                    tasks.append({"key": key, "series": row["series"], "family": row["family"],
                                  "model": model, "repetition": repetition, "method": method,
                                  "order_index": order_index, "width": protocol["width"],
                                  "thresholds": protocol["thresholds"] if method == "certificate" else None})
    return tasks


def validate_output(record):
    if record["status"] != "ok":
        return
    if not math.isfinite(record["seconds"]) or record["seconds"] <= 0:
        raise ValueError("Invalid complete-call duration")
    if record["method"] == "certificate":
        lo, hi, scale = (int(record[k]) for k in ("lower_numerator", "upper_numerator", "scale"))
        if not (scale > 0 and 0 <= lo <= hi <= scale):
            raise ValueError("Invalid integer certificate output")
        if not isinstance(record["thresholds_retained"], int) or record["thresholds_retained"] <= 0:
            raise ValueError("Invalid retained threshold count")
    elif not math.isfinite(record["value"]):
        raise ValueError("Invalid exact floating-point output")


def summarize(records, protocol):
    expected = {r["key"]: r for r in schedule(protocol)}
    seen = set()
    groups = defaultdict(dict)
    statuses = Counter()
    for r in records:
        if r["key"] in seen:
            raise ValueError("duplicate cost receipt")
        seen.add(r["key"])
        task = expected.get(r["key"])
        if task is None or any(r.get(k) != v for k, v in task.items()):
            raise ValueError("Unexpected or mutated scheduled task")
        statuses[r["status"]] += 1
        validate_output(r)
        if r["status"] == "ok":
            groups[(r["series"], r["family"], r["model"], r["method"])][r["repetition"]] = r
    medians, outputs = {}, {}
    for key, reps in groups.items():
        rr = list(reps.values())
        if key[3] == "certificate":
            signatures = {(r["lower_numerator"], r["upper_numerator"], r["scale"],
                           r["thresholds_retained"]) for r in rr}
            if len(signatures) != 1:
                raise ValueError("Certificate repeated outputs differ")
        elif max(r["value"] for r in rr) - min(r["value"] for r in rr) > protocol["parity_tolerance"]:
            raise ValueError("Exact repeated outputs differ")
        if set(reps) == set(range(protocol["repetitions"])):
            medians[key] = statistics.median(r["seconds"] for r in rr)
            outputs[key] = rr[0]
    pairs, outside = [], 0
    for (series, family, model, method), seconds in medians.items():
        other = (series, family, model, "radix_exact")
        if method != "certificate" or other not in medians:
            continue
        c, e = outputs[(series, family, model, method)], outputs[other]
        lo, hi = (Fraction(int(c[k]), int(c["scale"])) for k in ("lower_numerator", "upper_numerator"))
        outside += not lo <= Fraction.from_float(e["value"]) <= hi
        pairs.append({"series": series, "family": family, "model": model,
                      "certificate_median_seconds": seconds,
                      "exact_median_seconds": medians[other], "ratio": seconds/medians[other]})
    complete = len(seen) == len(expected) and statuses.get("ok", 0) == len(expected)
    ratio = None
    if complete:
        ratios = [p["ratio"] for p in pairs]
        by_family = defaultdict(list)
        for p in pairs:
            by_family[p["family"]].append(math.log(p["ratio"]))
        ratio = {"definition": "certificate complete-call seconds / exact complete-call seconds",
                 "median": statistics.median(ratios),
                 "geometric_mean": math.exp(statistics.mean(map(math.log, ratios))),
                 "equal_family_geometric_mean": math.exp(statistics.mean(statistics.mean(v) for v in by_family.values())),
                 "per_family_geometric_mean": {f: math.exp(statistics.mean(v)) for f, v in sorted(by_family.items())},
                 "certificate_total_paired_medians_seconds": sum(p["certificate_median_seconds"] for p in pairs),
                 "exact_total_paired_medians_seconds": sum(p["exact_median_seconds"] for p in pairs)}
    return {"expected_records": len(expected), "recorded_records": len(seen),
            "missing_records": len(expected) - len(seen), "status_counts": dict(statuses),
            "complete_paired_cases": len(pairs), "comparative_claim_eligible": complete,
            "ratio": ratio, "pairs": pairs,
            "exact_float_outside_certificate_informational": int(outside),
            "scope": "Finite fixed 30-series subset. Certificate bounds target real arithmetic; floating containment is diagnostic only."}


def freeze():
    if common.sha256_file(ROOT / MANIFEST) != MANIFEST_SHA:
        raise ValueError("Acquisition manifest changed")
    manifest, proposal = read(ROOT / MANIFEST), read(ROOT / SUBSET)
    rows = select_rows(manifest["series"], proposal)
    if len(rows) != 30 or len(manifest["models"]) != 12:
        raise ValueError("Frozen 30 by 12 panel mismatch")
    if {r["series"] for r in rows} != {r["series"] for r in common.timing_subset(manifest["series"])}:
        raise ValueError("Main-study timing subset differs")
    sources = ["experiments/msad_certificate_cost.py", "tests/test_msad_certificate_cost.py",
               "experiments/msad_sampling_study.py", "src/sparse_vus/sampling.py",
               "src/sparse_vus/sampling_bounds.py", "src/sparse_vus/core.py",
               "src/sparse_vus/radix.py", "src/sparse_vus/pr_compiled.py",
               "src/sparse_vus/compiled.py", "src/sparse_vus/__init__.py", MANIFEST, SUBSET,
               "artifacts/msad-certificate-20261023/protocol.json",
               "artifacts/msad-sampling-20261023/source_manifest.json"]
    protocol = {"study": "msad-certificate-cost-20261023", "schema_version": 1,
                "frozen_utc": utc(),
                "freeze_scope": "Before this supplement author reads certificate corpus outcomes and before any timed supplement calls; main numerical/accuracy protocols already running.",
                "manifest": MANIFEST, "manifest_sha256": MANIFEST_SHA,
                "subset": SUBSET, "subset_rule": proposal["rule"],
                "series": [{k: r[k] for k in ("series", "family", "npz_sha256", "n")} for r in rows],
                "models": manifest["models"], "width": 30, "thresholds": 250,
                "methods": list(METHODS), "repetitions": 5, "seed": 20261023,
                "ordering": "For each series/model/repetition the two methods are ordered by one fixed SHA256 bit; serial execution.",
                "timer_scope": "Already loaded arrays; complete public function call including validation, preprocessing, integer square-root construction, and certificate assembly; excludes NPZ decode/hash, IPC, serialization, and synthetic warmup.",
                "resource_rule": "Run only after main numerical/validation/timing, certificate accuracy, and root full tests release CPU; explicit idle-host flag required.",
                "timeout_seconds_per_call": 30, "worker": "Reused spawn subprocess, terminated/restarted on timeout; both methods warmed on fixed synthetic data after each start.",
                "output_validation": "Integer endpoints identical to frozen accuracy study, exact values within 2e-10 of frozen main numerical study, and repeat consistency; complete coverage required for global ratio.",
                "parity_tolerance": 2e-10,
                "reference_records": {"exact": "artifacts/msad-sampling-20261023/records.jsonl",
                                      "certificate": "artifacts/msad-certificate-20261023/records.jsonl"},
                "failure_policy": "Keep each timeout/error/mismatch in denominator; resume only missing scheduled calls, never rerun an observed timed failure for this panel.",
                "cost_claim": "No claim that certification is faster; directly report certificate/exact ratios and total paired median cost.",
                "sources": {p: common.sha256_file(ROOT/p) for p in sources}}
    OUT.mkdir(exist_ok=False)
    write_new(OUT / "protocol.json", protocol)
    print(common.sha256_file(OUT / "protocol.json"))


def verified_protocol(expected=None):
    ph = common.sha256_file(OUT / "protocol.json")
    if expected is not None and ph != expected:
        raise ValueError("Cost protocol hash mismatch")
    p = read(OUT / "protocol.json")
    common.verify_hashes(p["sources"])
    return p, ph


def references(protocol):
    targets = {(r["series"], m) for r in protocol["series"] for m in protocol["models"]}
    result = {}
    hashes = {}
    main_source = common.sha256_file(ROOT / "artifacts/msad-sampling-20261023/source_manifest.json")
    cert_protocol = common.sha256_file(ROOT / "artifacts/msad-certificate-20261023/protocol.json")
    for kind, relative in protocol["reference_records"].items():
        path = ROOT / relative
        hashes[relative] = common.sha256_file(path)
        selected = {}
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if kind == "exact":
                if r.get("source_manifest_sha256") != main_source:
                    raise ValueError("Main reference provenance mismatch")
                keep = r.get("phase") == "numerical" and r.get("method") == "radix_exact" and r.get("width") == 30
            else:
                if r.get("protocol_sha256") != cert_protocol:
                    raise ValueError("Certificate reference provenance mismatch")
                keep = r.get("budget") == 250 and r.get("width") == 30
            key = (r.get("series"), r.get("model"))
            if keep and key in targets:
                if key in selected or r["status"] != "ok":
                    raise ValueError("Reference duplicate/failure: " + str(key))
                selected[key] = r
        if set(selected) != targets:
            raise ValueError("Required reference outcomes incomplete")
        result[kind] = selected
    return result, hashes


def check_reference(record, refs, protocol):
    if record["status"] != "ok":
        return
    key = (record["series"], record["model"])
    if record["method"] == "certificate":
        base = refs["certificate"][key]
        for field in ("lower_numerator", "upper_numerator", "scale", "thresholds_retained"):
            if record[field] != base[field]:
                raise ValueError("Certificate reference output mismatch: " + field)
    elif abs(record["value"] - refs["exact"][key]["value"]) > protocol["parity_tolerance"]:
        raise ValueError("Exact reference output mismatch")


def _worker_main(conn, root_string):
    root = Path(root_string)
    sys.path.insert(0, str(root / "src"))
    from threadpoolctl import threadpool_limits
    from sparse_vus.sampling_bounds import certified_sampled_pr
    from sparse_vus.radix import sparse_pr_radix_jit
    with threadpool_limits(limits=1):
        y = np.zeros(257, dtype=np.int8); y[31:41] = 1; y[180:187] = 1
        s = np.round(np.random.default_rng(613).normal(size=257), 1)
        certified_sampled_pr(y, s, 30, 250)
        sparse_pr_radix_jit(y, s, 30)
        conn.send({"status": "ready"})
        arrays = None
        while True:
            request = conn.recv()
            if request["op"] == "stop":
                return
            try:
                if request["op"] == "load":
                    arrays = common.load_case(request["row"], request["models"], root)
                    conn.send({"status": "ok"})
                    continue
                start = time.perf_counter()
                if request["method"] == "certificate":
                    c = certified_sampled_pr(arrays["labels"], arrays[request["model"]], 30, 250)
                    seconds = time.perf_counter() - start
                    result = {"lower_numerator": str(c.lower_numerator), "upper_numerator": str(c.upper_numerator),
                              "scale": str(c.scale), "thresholds_retained": c.thresholds_retained}
                else:
                    value = sparse_pr_radix_jit(arrays["labels"], arrays[request["model"]], 30)
                    seconds = time.perf_counter() - start
                    result = {"value": float(value)}
                conn.send(dict(result, status="ok", seconds=seconds))
            except Exception as exc:
                conn.send({"status": "error", "error_type": type(exc).__name__, "error": str(exc)})


class Worker(common.Worker):
    def start(self):
        self.close()
        ctx = mp.get_context("spawn")
        self.conn, child = ctx.Pipe()
        self.process = ctx.Process(target=_worker_main, args=(child, str(self.root)))
        self.process.start(); child.close()
        if not self.conn.poll(180) or self.conn.recv().get("status") != "ready":
            self.close()
            raise RuntimeError("Certificate cost synthetic warmup failed")


def run(expected, idle):
    if not idle:
        raise ValueError("Coordinated --idle-host-confirmed is required")
    p, ph = verified_protocol(expected)
    refs, hashes = references(p)
    receipt_path = OUT / "run-inputs.json"
    if receipt_path.exists():
        receipt = read(receipt_path)
        if receipt["reference_sha256"] != hashes or receipt["protocol_sha256"] != ph:
            raise ValueError("Reference logs changed since run start")
    else:
        write_new(receipt_path, {"started_utc": utc(), "protocol_sha256": ph,
                                "reference_sha256": hashes, "idle_host_confirmed": True,
                                "python": sys.version, "numpy": np.__version__,
                                "host": platform.uname()._asdict()})
    rows = {r["series"]: r for r in read(ROOT / MANIFEST)["series"]}
    record_path = OUT / "records.jsonl"
    index = common.read_records(record_path)
    for r in index.values():
        if r["protocol_sha256"] != ph:
            raise ValueError("Cost receipt protocol mismatch")
    summarize(index.values(), p)
    worker = Worker()
    started = time.perf_counter()
    previous, new_calls = None, 0
    try:
        for task in schedule(p):
            if task["key"] in index:
                continue
            if task["series"] != previous:
                verified_protocol(ph)
                previous = task["series"]
                print(json.dumps({"series": previous, "new_calls": new_calls}), flush=True)
            row = rows[task["series"]]
            result = worker.call(row, p["models"], task, p["timeout_seconds_per_call"])
            r = dict(task, **result, protocol_sha256=ph, utc=utc(),
                     npz_sha256=row["npz_sha256"], label_sha256=row["array_sha256"]["labels"],
                     score_sha256=row["array_sha256"][task["model"]])
            try:
                validate_output(r)
                check_reference(r, refs, p)
            except ValueError as exc:
                r.update(status="output_mismatch", error=str(exc))
            common.append_record(record_path, r, index)
            new_calls += 1
    finally:
        worker.close()
        with (OUT / "collection.jsonl").open("a") as stream:
            stream.write(json.dumps({"id": str(uuid.uuid4()), "ended_utc": utc(),
                                     "protocol_sha256": ph, "new_calls": new_calls,
                                     "wall_seconds": time.perf_counter() - started,
                                     "scope": "Includes load/hash/decode/warmup/IPC and append/fsync"}) + "\n")
    report()


def report():
    p, ph = verified_protocol()
    refs, hashes = references(p)
    if read(OUT / "run-inputs.json")["reference_sha256"] != hashes:
        raise ValueError("Reference logs changed")
    records = list(common.read_records(OUT / "records.jsonl").values())
    for r in records:
        if r["protocol_sha256"] != ph:
            raise ValueError("Cost receipt protocol mismatch")
        check_reference(r, refs, p)
    result = summarize(records, p)
    result.update(protocol_sha256=ph, records_sha256=common.sha256_file(OUT / "records.jsonl"),
                  reference_sha256=hashes)
    path = OUT / ("report-" + result["records_sha256"][:16] + ".json")
    if path.exists():
        if read(path) != result:
            raise ValueError("Nondeterministic cost report")
    else:
        write_new(path, result)
    print(json.dumps({"report": str(path.relative_to(ROOT)), "complete": result["comparative_claim_eligible"],
                      "recorded_records": result["recorded_records"], "ratio": result["ratio"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["freeze", "run", "report"])
    parser.add_argument("--protocol-sha256")
    parser.add_argument("--idle-host-confirmed", action="store_true")
    args = parser.parse_args()
    if args.command == "freeze":
        freeze()
    elif args.command == "run":
        if not args.protocol_sha256:
            parser.error("--protocol-sha256 is required")
        run(args.protocol_sha256, args.idle_host_confirmed)
    else:
        report()
