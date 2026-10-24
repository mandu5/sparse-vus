"""Separate source-bound process-memory study, not a timing benchmark.

OS peak RSS includes the interpreter, imported libraries, input generation/load,
warm-up and the complete call. A difference of high-water marks is not an exact
workspace measurement. Synthetic cases test resource scaling only.
"""
from __future__ import annotations
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[key] = "1"
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/"artifacts/pvldb-research-20261024"
OUT = BASE/"resources"
METHODS = ["released", "geometry", "stream", "dense"]


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, value):
    with Path(p).open("x") as f: json.dump(value, f, indent=2, allow_nan=False); f.write("\n")


def stress(n, models, fraction):
    y = np.zeros(n, np.int8); count = max(1, int(n*fraction)); start = (n-count)//2
    y[start:start+count] = 1
    return y, np.random.default_rng(20261024).random((models, n))


def rss_bytes(value, system):
    if system == "Darwin": return int(value)
    if system == "Linux": return int(value)*1024
    raise ValueError("OS peak-RSS units not specified for this platform")


def freeze():
    primary = json.loads((BASE/"full-precision/protocol.json").read_text())
    inputs = json.loads((BASE/"full-precision/inputs.json").read_text())["series"]
    audit = json.loads((BASE/"full-precision/independent-audit-v3.json").read_text())
    g = audit["geometry"]
    names = list(dict.fromkeys([max(g, key=lambda c:c["n"])["series"],
        max(g, key=lambda c:c["widths"]["30"]["support_fraction"])["series"],
        max(g, key=lambda c:c["widths"]["30"]["original_components"])["series"]]))
    by_name = {c["series"]:c for c in inputs}
    cases = [{"name":n+"_M8", "kind":"real", "input":by_name[n], "models":8} for n in names]
    largest=max(g,key=lambda c:c["n"])["series"]
    cases.append({"name":largest+"_M32_repeated", "kind":"real_repeated_models", "input":by_name[largest], "models":32})
    for f in (.01,.5):cases.append({"name":f"synthetic_n500000_M8_p{f}", "kind":"synthetic_resource_only", "n":500000,"models":8,"positive_fraction":f})
    sources=dict(primary["source_sha256"]);sources["experiments/pvldb_resources.py"]=digest(__file__)
    OUT.mkdir(exist_ok=False)
    write(OUT/"protocol.json",{"created_utc":datetime.now(timezone.utc).isoformat(),
        "status":"FROZEN_BEFORE_RESOURCE_OUTCOMES_AFTER_TIMING_RESULTS", "source_sha256":sources,
        "primary_inputs_sha256":digest(BASE/"full-precision/inputs.json"), "cases":cases,
        "methods":METHODS,"repetitions":3,"width":30,
        "selection_rule":"Real maxima of n, support fraction and original component count, ties in frozen order; largest real case repeats eight scores four times for M32. Two declared synthetic density/resource stress cases.",
        "measurement":"Fresh interpreter process per case/method/repetition; warm tiny JIT call, load/generate inputs, OS lifetime peak RSS before/after complete call. Includes interpreter/libraries/inputs. No auxiliary-memory inference from high-water delta; no timing comparison.",
        "hardware":platform.platform(), "synthetic_scope":"Uniform fixed-seed scores and one centered anomaly interval test memory scaling, not real-data generalization."})


def child(case, method, width):
    sys.path.insert(0,str(ROOT/"src"))
    from sparse_vus.batch import batch_pr
    from sparse_vus.radix import sparse_pr_radix_jit
    from sparse_vus.dense_radix import dense_pr_nearest_radix_jit
    def evaluate(y,s):
        if method in ("geometry","stream"):return batch_pr(y,s,width,strategy=method)
        f=sparse_pr_radix_jit if method=="released" else dense_pr_nearest_radix_jit
        return np.asarray([f(y,v,width) for v in s])
    evaluate(np.array([0,1,0,0,1,0],np.int8),np.tile(np.arange(6.),(8,1)))
    if case["kind"].startswith("real"):
        p=ROOT/".cache/pvldb-full-precision-20261024"/case["input"]["file"]
        if digest(p)!=case["input"]["npz_sha256"]:raise ValueError("resource input changed")
        with np.load(p,allow_pickle=False) as z:y=z["labels"];s=z["scores"]
        if case["models"]!=len(s):s=np.tile(s,(case["models"]//len(s),1))
    else:y,s=stress(case["n"],case["models"],case["positive_fraction"])
    before=rss_bytes(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,platform.system())
    result=evaluate(y,s)
    after=rss_bytes(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,platform.system())
    if not np.isfinite(result).all():raise ValueError("nonfinite resource result")
    print(json.dumps({"name":case["name"],"method":method,"n":len(y),"models":len(s),
        "input_array_bytes":y.nbytes+s.nbytes,"peak_before_call_bytes":before,"peak_after_call_bytes":after,
        "additional_lifetime_highwater_bytes":after-before,"values":result.tolist()},allow_nan=False))


def run():
    p=json.loads((OUT/"protocol.json").read_text())
    for path,h in p["source_sha256"].items():
        if digest(ROOT/path)!=h:raise ValueError(f"source changed: {path}")
    if digest(BASE/"full-precision/inputs.json")!=p["primary_inputs_sha256"]:raise ValueError("input receipt changed")
    rows=[]
    with (OUT/"records.jsonl").open("x") as f:
        for case in p["cases"]:
            for trial in range(p["repetitions"]):
                for method in p["methods"]:
                    text=subprocess.check_output([sys.executable,__file__,"child","--case",json.dumps(case),"--method",method],text=True,cwd=ROOT)
                    row=json.loads(text);row["trial"]=trial;rows.append(row)
                    f.write(json.dumps(row)+"\n");f.flush()
            print(case["name"],"complete",flush=True)
    report={};max_error=0.
    for case in p["cases"]:
        selected=[r for r in rows if r["name"]==case["name"]]
        reference=next(r["values"] for r in selected if r["method"]=="released")
        for r in selected:
            error=float(np.max(np.abs(np.asarray(r["values"])-reference)));max_error=max(max_error,error)
            if error>1e-11:raise ValueError("resource scalar parity failure")
        report[case["name"]]={m:{"peak_process_mib_median":statistics.median(r["peak_after_call_bytes"] for r in selected if r["method"]==m)/(1<<20),
            "input_mib":selected[0]["input_array_bytes"]/(1<<20),
            "additional_lifetime_highwater_mib_median":statistics.median(r["additional_lifetime_highwater_bytes"] for r in selected if r["method"]==m)/(1<<20)} for m in p["methods"]}
    write(OUT/"report.json",{"status":"COMPLETE","protocol_sha256":digest(OUT/"protocol.json"),
        "records_sha256":digest(OUT/"records.jsonl"),"max_scalar_error":max_error,"cases":report,
        "qualification":p["measurement"],"completed_utc":datetime.now(timezone.utc).isoformat()})


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=["freeze","run","child"])
    parser.add_argument("--case");parser.add_argument("--method",choices=METHODS);a=parser.parse_args()
    if a.command=="child":child(json.loads(a.case),a.method,30)
    else:globals()[a.command]()
