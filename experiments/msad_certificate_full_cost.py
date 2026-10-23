"""Separately frozen three-way cost execution plan, preserving the earlier protocol.

The original two-method study remains unexecuted. This addendum executes all
three methods once in randomized blocks and adds a same-guarantee full-grid
integer certificate comparison. No numerical production source is modified.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
import argparse
import hashlib
import json
import math
import multiprocessing as mp
from pathlib import Path
import platform
import statistics
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
import msad_certificate_cost as original
from msad_certificate_cost import common, read, write_new, utc, np

OUT = ROOT / "artifacts/msad-certificate-full-cost-20261023"
METHODS = ("certificate", "full_certificate", "radix_exact")
FULL_PROTOCOL = "artifacts/msad-full-certificate-20261023/protocol.json"
FULL_RECORDS = "artifacts/msad-full-certificate-20261023/records.jsonl"


def schedule(protocol):
    tasks = []
    for row in protocol["series"]:
        for model in protocol["models"]:
            for repetition in range(protocol["repetitions"]):
                seed = f"{protocol['seed']}|certificate-full-cost|{row['series']}|{model}|{repetition}|"
                order = sorted(METHODS, key=lambda method: hashlib.sha256((seed+method).encode()).digest())
                for order_index, method in enumerate(order):
                    key = json.dumps([row["series"], model, repetition, method], separators=(",", ":"))
                    budget = row["n"] if method == "full_certificate" else protocol["thresholds"] if method == "certificate" else None
                    tasks.append({"key": key, "series": row["series"], "family": row["family"],
                                  "model": model, "repetition": repetition, "method": method,
                                  "order_index": order_index, "width": protocol["width"], "thresholds": budget})
    return tasks


def validate_output(record):
    r = dict(record)
    if r["method"] == "full_certificate":
        r["method"] = "certificate"
    original.validate_output(r)


def summarize(records, protocol):
    expected = {r["key"]: r for r in schedule(protocol)}
    seen, statuses, groups = set(), Counter(), defaultdict(dict)
    for r in records:
        if r["key"] in seen:
            raise ValueError("duplicate three-way cost receipt")
        seen.add(r["key"])
        task = expected.get(r["key"])
        if task is None or any(r.get(k) != v for k,v in task.items()):
            raise ValueError("Unexpected or changed scheduled task")
        statuses[r["status"]] += 1
        validate_output(r)
        if r["status"] == "ok":
            groups[(r["series"], r["family"], r["model"], r["method"])][r["repetition"]] = r
    medians, outputs = {}, {}
    for key, rr in groups.items():
        records = list(rr.values())
        if key[3] != "radix_exact":
            signatures = {(r["lower_numerator"],r["upper_numerator"],r["scale"],r["thresholds_retained"]) for r in records}
            if len(signatures) != 1:
                raise ValueError("Integer certificate repeated outputs differ")
        elif max(r["value"] for r in records)-min(r["value"] for r in records) > protocol["parity_tolerance"]:
            raise ValueError("Exact repeated outputs differ")
        if set(rr) == set(range(protocol["repetitions"])):
            medians[key] = statistics.median(r["seconds"] for r in records)
            outputs[key] = records[0]
    complete = len(seen) == len(expected) and statuses.get("ok",0) == len(expected)
    cases, outside = [], Counter()
    for row in protocol["series"]:
        for model in protocol["models"]:
            keys = {m:(row["series"],row["family"],model,m) for m in METHODS}
            if not all(k in medians for k in keys.values()):
                continue
            item = {"series":row["series"],"family":row["family"],"model":model,
                    "median_seconds":{m:medians[k] for m,k in keys.items()}}
            e = Fraction.from_float(outputs[keys["radix_exact"]]["value"])
            for method in METHODS[:2]:
                c = outputs[keys[method]]
                lo,hi = (Fraction(int(c[k]),int(c["scale"])) for k in ("lower_numerator","upper_numerator"))
                outside[method] += not lo <= e <= hi
            cases.append(item)
    comparisons = [("certificate","full_certificate"),("certificate","radix_exact"),("full_certificate","radix_exact")]
    ratios = None
    if complete:
        ratios = {}
        for numerator, denominator in comparisons:
            values, by = [], defaultdict(list)
            for c in cases:
                ratio = c["median_seconds"][numerator]/c["median_seconds"][denominator]
                values.append(ratio);by[c["family"]].append(math.log(ratio))
            ratios[numerator+"_over_"+denominator] = {
                "definition":f"{numerator} complete-call seconds / {denominator} complete-call seconds",
                "median":statistics.median(values),"geometric_mean":math.exp(statistics.mean(map(math.log,values))),
                "equal_family_geometric_mean":math.exp(statistics.mean(statistics.mean(v) for v in by.values())),
                "per_family_geometric_mean":{f:math.exp(statistics.mean(v)) for f,v in sorted(by.items())}}
    return {"expected_records":len(expected),"recorded_records":len(seen),"missing_records":len(expected)-len(seen),
            "status_counts":dict(statuses),"complete_three_way_cases":len(cases),
            "comparative_claim_eligible":complete,"ratios":ratios,"cases":cases,
            "sum_case_medians_seconds":{m:sum(c["median_seconds"][m] for c in cases) for m in METHODS},
            "exact_float_outside_certificate_informational":dict(outside),
            "scope":"Fixed thirty-series published-score subset; real-arithmetic certification and floating evaluation are distinct guarantees."}


def freeze():
    p, prior_hash = original.verified_protocol("7a9962a21a2bc25292ef25c6c629fbe400cab7275de77547fc87d8210be2a267")
    if (original.OUT / "records.jsonl").exists():
        raise ValueError("Earlier two-way plan already executed; cannot supersede silently")
    p.update(study="msad-certificate-full-cost-20261023",frozen_utc=utc(),
             prior_unexecuted_protocol_sha256=prior_hash,
             prior_unexecuted_protocol=str((original.OUT/"protocol.json").relative_to(ROOT)),
             methods=list(METHODS),
             addendum_reason="Independent review requests a same-guarantee exhaustive integer certificate baseline; all source inputs and cost case IDs unchanged.",
             freeze_scope="Before any timed certificate cost call. The comparison/cases/repetitions were chosen on reviewer request before full-grid results; full-grid accuracy aggregates were disclosed while implementation finished, before this source/protocol freeze. Primary sampling outcomes were disclosed after the earlier cost protocol froze. No cost outcome has been observed.",
             execution_rule="This three-method plan supersedes execution of the preserved two-method cost plan; no timed results have been discarded.",
             ordering="For each case/model/repetition, sort the three method names by SHA256 of fixed seed plus case/model/repetition/method; execute serially.",
             full_grid_method="certified_sampled_pr(y,s,max_buffer=30,thresholds=len(y)); uses complete global ties and the same integer arithmetic guarantee.",
             full_grid_protocol=FULL_PROTOCOL,full_grid_protocol_sha256=common.sha256_file(ROOT/FULL_PROTOCOL))
    p["reference_records"]["full_certificate"] = FULL_RECORDS
    for path in ["experiments/msad_certificate_full_cost.py","tests/test_msad_certificate_full_cost.py",
                 str((original.OUT/"protocol.json").relative_to(ROOT)),FULL_PROTOCOL,
                 "experiments/msad_full_certificate_study.py"]:
        p["sources"][path] = common.sha256_file(ROOT/path)
    OUT.mkdir(exist_ok=False)
    write_new(OUT/"protocol.json",p)
    print(common.sha256_file(OUT/"protocol.json"))


def verified_protocol(expected=None):
    ph = common.sha256_file(OUT/"protocol.json")
    if expected is not None and ph != expected:
        raise ValueError("Three-way cost protocol hash mismatch")
    p = read(OUT/"protocol.json")
    common.verify_hashes(p["sources"])
    return p,ph


def references(p):
    reduced = dict(p,reference_records={k:v for k,v in p["reference_records"].items() if k != "full_certificate"})
    refs, hashes = original.references(reduced)
    targets = {(r["series"],m):r["n"] for r in p["series"] for m in p["models"]}
    path = ROOT/p["reference_records"]["full_certificate"]
    hashes[str(path.relative_to(ROOT))] = common.sha256_file(path)
    result = {}
    for line in path.read_text().splitlines():
        r = json.loads(line)
        if r["protocol_sha256"] != p["full_grid_protocol_sha256"]:
            raise ValueError("Full-grid reference provenance mismatch")
        key = (r["series"],r["model"])
        if key in targets:
            if key in result or r["status"] != "ok" or r["width"] != 30 or r["budget"] != targets[key]:
                raise ValueError("Full-grid reference invalid or duplicated")
            result[key] = r
    if set(result) != set(targets):
        raise ValueError("Full-grid references incomplete")
    refs["full_certificate"] = result
    return refs,hashes


def check_reference(r, refs, p):
    if r["status"] != "ok":
        return
    if r["method"] != "full_certificate":
        original.check_reference(r,refs,p)
    else:
        other = refs["full_certificate"][(r["series"],r["model"])]
        for field in ("lower_numerator","upper_numerator","scale","thresholds_retained"):
            if r[field] != other[field]:
                raise ValueError("Full-grid integer output mismatch: "+field)


def _worker_main(conn, root_string):
    root = Path(root_string)
    sys.path.insert(0,str(root/"src"))
    from threadpoolctl import threadpool_limits
    from sparse_vus.sampling_bounds import certified_sampled_pr
    from sparse_vus.radix import sparse_pr_radix_jit
    with threadpool_limits(limits=1):
        y = np.zeros(257,np.int8);y[31:41]=1;y[180:187]=1
        s = np.round(np.random.default_rng(613).normal(size=257),1)
        for h in (250,len(y)):certified_sampled_pr(y,s,30,h)
        sparse_pr_radix_jit(y,s,30)
        conn.send({"status":"ready"})
        arrays = None
        while True:
            request = conn.recv()
            if request["op"] == "stop":return
            try:
                if request["op"] == "load":
                    arrays = common.load_case(request["row"],request["models"],root)
                    conn.send({"status":"ok"});continue
                start = time.perf_counter()
                if request["method"] == "radix_exact":
                    value = sparse_pr_radix_jit(arrays["labels"],arrays[request["model"]],30)
                    seconds = time.perf_counter()-start
                    output = {"value":float(value)}
                else:
                    c = certified_sampled_pr(arrays["labels"],arrays[request["model"]],30,request["thresholds"])
                    seconds = time.perf_counter()-start
                    output = {"lower_numerator":str(c.lower_numerator),"upper_numerator":str(c.upper_numerator),
                              "scale":str(c.scale),"thresholds_retained":c.thresholds_retained}
                conn.send(dict(output,status="ok",seconds=seconds))
            except Exception as exc:
                conn.send({"status":"error","error_type":type(exc).__name__,"error":str(exc)})


class Worker(common.Worker):
    def start(self):
        self.close()
        ctx = mp.get_context("spawn")
        self.conn,child = ctx.Pipe()
        self.process = ctx.Process(target=_worker_main,args=(child,str(self.root)))
        self.process.start();child.close()
        if not self.conn.poll(180) or self.conn.recv().get("status") != "ready":
            self.close();raise RuntimeError("Three-way synthetic warmup failed")


def run(expected,idle):
    if not idle:raise ValueError("Coordinated --idle-host-confirmed required")
    p,ph = verified_protocol(expected)
    refs,hashes = references(p)
    receipt_path = OUT/"run-inputs.json"
    if receipt_path.exists():
        old = read(receipt_path)
        if old["reference_sha256"] != hashes or old["protocol_sha256"] != ph:
            raise ValueError("Reference logs changed")
    else:
        write_new(receipt_path,{"started_utc":utc(),"protocol_sha256":ph,"reference_sha256":hashes,
                                "idle_host_confirmed":True,"python":sys.version,"numpy":np.__version__,
                                "host":platform.uname()._asdict()})
    rows = {r["series"]:r for r in read(ROOT/original.MANIFEST)["series"]}
    record_path = OUT/"records.jsonl"
    index = common.read_records(record_path)
    for r in index.values():
        if r["protocol_sha256"] != ph:raise ValueError("Cost record protocol mismatch")
    summarize(index.values(),p)
    worker = Worker();started = time.perf_counter();previous = None;calls = 0
    try:
        for task in schedule(p):
            if task["key"] in index:continue
            if previous != task["series"]:
                verified_protocol(ph);previous = task["series"]
                print(json.dumps({"series":previous,"new_calls":calls}),flush=True)
            row = rows[task["series"]]
            result = worker.call(row,p["models"],task,p["timeout_seconds_per_call"])
            record = dict(task,**result,protocol_sha256=ph,utc=utc(),npz_sha256=row["npz_sha256"],
                          label_sha256=row["array_sha256"]["labels"],score_sha256=row["array_sha256"][task["model"]])
            try:
                validate_output(record);check_reference(record,refs,p)
            except ValueError as exc:
                record.update(status="output_mismatch",error=str(exc))
            common.append_record(record_path,record,index);calls += 1
    finally:
        worker.close()
        with (OUT/"collection.jsonl").open("a") as stream:
            stream.write(json.dumps({"id":str(uuid.uuid4()),"ended_utc":utc(),"protocol_sha256":ph,
                                     "new_calls":calls,"wall_seconds":time.perf_counter()-started,
                                     "scope":"Includes source/input verification, decode, synthetic warmup, IPC, metric calls and durable writes."})+"\n")
    report()


def report():
    p,ph = verified_protocol()
    refs,hashes = references(p)
    if read(OUT/"run-inputs.json")["reference_sha256"] != hashes:raise ValueError("Reference logs changed")
    records = list(common.read_records(OUT/"records.jsonl").values())
    for r in records:
        if r["protocol_sha256"] != ph:raise ValueError("Cost record protocol mismatch")
        check_reference(r,refs,p)
    result = summarize(records,p)
    result.update(protocol_sha256=ph,records_sha256=common.sha256_file(OUT/"records.jsonl"),reference_sha256=hashes)
    path = OUT/("report-"+result["records_sha256"][:16]+".json")
    if path.exists():
        if read(path) != result:raise ValueError("Nondeterministic cost report")
    else:write_new(path,result)
    print(json.dumps({"report":str(path.relative_to(ROOT)),"complete":result["comparative_claim_eligible"],
                      "recorded_records":result["recorded_records"],"ratios":result["ratios"]}),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["freeze","run","report"])
    parser.add_argument("--protocol-sha256")
    parser.add_argument("--idle-host-confirmed",action="store_true")
    args = parser.parse_args()
    if args.command == "freeze":freeze()
    elif args.command == "run":
        if not args.protocol_sha256:parser.error("--protocol-sha256 required")
        run(args.protocol_sha256,args.idle_host_confirmed)
    else:report()
