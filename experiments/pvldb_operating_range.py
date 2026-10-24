"""Frozen follow-up on long public recordings and controlled runtime regimes.

This follows the primary study and reviewer operating-range objection. It never
replaces the primary cohort or its result. Real recordings retain source/reuse
identities; controlled inputs are explicitly synthetic mechanism experiments.
"""
from __future__ import annotations
import os
for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","NUMBA_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[key]="1"
import argparse
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import time
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"artifacts/pvldb-research-20261024"
OUT=BASE/"operating-range"
CACHE=ROOT/".cache/pvldb-operating-range-20261024"
ARCHIVE=ROOT/"cache/TSB-AD-U.zip"
REAL_METHODS=["released","geometry","stream","dense","external","benchopt_pair","radix_pair"]
CONTROLLED_METHODS=["released","stream","dense","external"]


def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        while block:=f.read(1<<20):h.update(block)
    return h.hexdigest()


def write(p,value):
    with Path(p).open("x") as f:json.dump(value,f,indent=2,allow_nan=False);f.write("\n")


def controlled(n,models,fraction,components,levels):
    count=int(n*fraction)
    if not 0<count<n or not 1<=components<=count or components>n-count:
        raise ValueError("infeasible controlled label contract")
    y=np.zeros(n,np.int8)
    for j in range(components):
        size=count//components+(j<count%components)
        start=int((j+.5)*n/components)-size//2
        y[start:start+size]=1
    if y.sum()!=count or np.count_nonzero(np.diff(np.r_[0,y,0])==1)!=components:
        raise ValueError("controlled intervals overlap or escape boundary")
    scores=np.random.default_rng(20261024).random((models,n))
    if levels is not None:scores=np.floor(scores*levels)
    return y,scores


def controlled_cases():
    base={"n":100000,"models":8,"positive_fraction":.01,"components":1,"width":30,"levels":None}
    candidates=[]
    for key,values in [("n",[1000,10000,100000,1000000]),("positive_fraction",[.001,.01,.1,.5,.9]),
                       ("components",[1,10,100,1000]),("models",[1,8,32]),("width",[0,30,300]),("levels",[None,16])]:
        candidates.extend({**base,key:value} for value in values)
    unique=[]
    for c in candidates:
        if c not in unique:unique.append(c)
    return [{**c,"name":f"controlled_{i:02d}"} for i,c in enumerate(unique)]


def freeze():
    import pandas as pd
    p=json.loads((BASE/"full-precision/protocol.json").read_text())
    if sha(ARCHIVE)!=p["archive_sha256"]:raise ValueError("archive changed")
    old=set(json.loads((ROOT/"artifacts/selected_series.json").read_text())["ordered_series"])
    cases=[]
    with zipfile.ZipFile(ARCHIVE) as z:
        for member in sorted(z.namelist()):
            if not member.endswith(".csv") or not any("_"+f+"_" in member for f in ("MITDB","SWaT")):continue
            raw=z.read(member);frame=pd.read_csv(io.BytesIO(raw));x=frame["Data"].to_numpy(np.float64);y=frame["Label"].to_numpy(np.int8)
            name=Path(member).stem;family="MITDB" if "_MITDB_" in name else "SWaT"
            if not np.isfinite(x).all() or not np.isin(y,[0,1]).all() or not 0<y.sum()<len(y):raise ValueError("invalid raw input")
            cases.append({"name":name,"family":family,"member":member,"n":len(y),"models":8,"width":30,
                "positive_points":int(y.sum()),"components":int(np.count_nonzero(np.diff(np.r_[0,y,0])==1)),
                "raw_sha256":hashlib.sha256(raw).hexdigest(),"observation_label_identity":hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest(),
                "previously_measured_by_name":name in old})
    sources=dict(p["source_sha256"])
    for name in ["experiments/pvldb_operating_range.py","experiments/benchopt_vus_adapter.py",".cache/benchopt_vus/metrics.py"]:sources[name]=sha(ROOT/name)
    orders=lambda methods:[methods[i:]+methods[:i] for i in range(len(methods))]
    OUT.mkdir(exist_ok=False)
    write(OUT/"protocol.json",{"status":"FROZEN_BEFORE_FOLLOWUP_SCORES_AND_TIMINGS_AFTER_PRIMARY_AND_REVIEW",
        "created_utc":datetime.now(timezone.utc).isoformat(),"source_sha256":sources,"archive_sha256":p["archive_sha256"],
        "real_cases":cases,"controlled_cases":controlled_cases(),"real_methods":REAL_METHODS,"controlled_methods":CONTROLLED_METHODS,
        "real_orders":orders(REAL_METHODS),"controlled_orders":orders(CONTROLLED_METHODS),"workflow_orders":orders(REAL_METHODS)[:3],
        "selection_rule":"Every MITDB and SWaT series in the fixed public TSB-AD-U archive. No outcome-based exclusion. Controlled one-factor grids retain their common anchor once.",
        "detectors":p["models"],"model_protocol":p["model_protocol"],"seed":20261024,"parity_atol":1e-11,"winner_tie_atol":1e-10,
        "timing":"Serial single numerical thread; tiny warm-up equally; complete public calls including winner selection. Seven/ four cyclic orders balance positions in real/controlled cases. Three additional directly timed complete collection passes use the first three orders and are not fully position-balanced.",
        "inference":"Follow-up conditional evidence; per-case trial uncertainty, not nine new independent populations. MITDB has 8 series and SWaT one. Raw reuse and equal-label dependence disclosed. Controlled cases are not real data and do not imply detector accuracy.",
        "diagnostics":"After all clocks, profile actual visited and active positions across widths for every stored model. Check values against timed exact records.",
        "failure_policy":"Retain all runtime losses. Nonfinite data, missing/duplicate records or exact PR/ROC discrepancy above tolerance halt; no replacement."})
    print(json.dumps({"real_cases":len(cases),"controlled_cases":len(controlled_cases()),"protocol_sha256":sha(OUT/"protocol.json")}))


def verify():
    p=json.loads((OUT/"protocol.json").read_text())
    for file,h in p["source_sha256"].items():
        if sha(ROOT/file)!=h:raise ValueError(f"source changed: {file}")
    if sha(ARCHIVE)!=p["archive_sha256"]:raise ValueError("archive changed")
    return p


def generate():
    import pandas as pd
    from pvldb_full_precision import generate_scores
    p=verify();CACHE.mkdir(exist_ok=False);records=[]
    with zipfile.ZipFile(ARCHIVE) as z,(OUT/"generation.jsonl").open("x") as log:
        for c in p["real_cases"]:
            raw=z.read(c["member"])
            if hashlib.sha256(raw).hexdigest()!=c["raw_sha256"]:raise ValueError("raw member changed")
            frame=pd.read_csv(io.BytesIO(raw));x=frame["Data"].to_numpy(np.float64);y=frame["Label"].to_numpy(np.int8)
            scores,details=generate_scores(x);file=CACHE/(c["name"]+".npz")
            with file.open("xb") as f:np.savez(f,observations=x,labels=y,scores=scores)
            r={**c,"kind":"real","file":file.name,"npz_sha256":sha(file),"score_sha256":hashlib.sha256(scores.tobytes()).hexdigest(),"model_details":details}
            records.append(r);log.write(json.dumps(r)+"\n");log.flush();print(c["name"],"generated",flush=True)
        for c in p["controlled_cases"]:
            y,s=controlled(c["n"],c["models"],c["positive_fraction"],c["components"],c["levels"]);file=CACHE/(c["name"]+".npz")
            with file.open("xb") as f:np.savez(f,labels=y,scores=s)
            r={**c,"kind":"controlled","family":"controlled","file":file.name,"npz_sha256":sha(file),"score_sha256":hashlib.sha256(s.tobytes()).hexdigest()}
            records.append(r);log.write(json.dumps(r)+"\n");log.flush()
    write(OUT/"inputs.json",{"status":"COMPLETE","protocol_sha256":sha(OUT/"protocol.json"),"cases":records})


def evaluate(method,y,scores,width):
    from pvldb_full_precision import evaluate as primary_evaluate
    if method in ("benchopt_pair","radix_pair"):
        from benchopt_vus_adapter import benchopt_vus
        from sparse_vus.radix import sparse_vus_radix_jit
        f=(lambda a,b:benchopt_vus(a,b,width,len(a))) if method=="benchopt_pair" else (lambda a,b:sparse_vus_radix_jit(a,b,width))
        values=np.asarray([f(y,s) for s in scores]);pr,roc=values[:,1],values[:,0]
    else:pr,_=primary_evaluate(method,y,scores,width);roc=None
    chosen=np.flatnonzero(pr>=pr.max()-1e-10).tolist()
    return pr,roc,chosen


def load(c):
    with np.load(CACHE/c["file"],allow_pickle=False) as z:return z["labels"],z["scores"]


def run():
    sys.path[:0]=[str(ROOT/"src"),str(ROOT/"experiments")]
    p=verify();ip=json.loads((OUT/"inputs.json").read_text());cases=ip["cases"]
    if ip["protocol_sha256"]!=sha(OUT/"protocol.json"):raise ValueError("input binding")
    for c in cases:
        if sha(CACHE/c["file"])!=c["npz_sha256"]:raise ValueError("score file changed")
    write(OUT/"run-start.json",{"protocol_sha256":sha(OUT/"protocol.json"),"inputs_sha256":sha(OUT/"inputs.json"),"platform":platform.platform(),"python":sys.version,"utc":datetime.now(timezone.utc).isoformat()})
    for method in REAL_METHODS:evaluate(method,np.array([0,1,0,0,1,0],np.int8),np.tile(np.arange(6.),(8,1)),30)
    references={}
    with (OUT/"records.jsonl").open("x") as log:
        for c in cases:
            y,s=load(c);pr0,roc0,win0=evaluate("radix_pair",y,s,c["width"]);references[c["name"]]=pr0
            orders=p["real_orders"] if c["kind"]=="real" else p["controlled_orders"]
            for trial,order in enumerate(orders):
                for method in order:
                    start=time.perf_counter_ns();pr,roc,winners=evaluate(method,y,s,c["width"]);elapsed=(time.perf_counter_ns()-start)*1e-9
                    pe=float(np.max(np.abs(pr-pr0)));re=None if roc is None else float(np.max(np.abs(roc-roc0)))
                    if pe>p["parity_atol"] or (re or 0)>p["parity_atol"] or winners!=win0:raise ValueError(f"parity failure {c['name']} {method} {pe} {re}")
                    row={"name":c["name"],"family":c["family"],"kind":c["kind"],"method":method,"trial":trial,"seconds":elapsed,
                        "values":pr.tolist(),"roc":None if roc is None else roc.tolist(),"winners":winners,"pr_error":pe,"roc_error":re}
                    log.write(json.dumps(row,allow_nan=False)+"\n");log.flush()
            print(c["name"],"timed",flush=True)
    with (OUT/"workflows.jsonl").open("x") as log:
        for family in ("MITDB","SWaT"):
            group=[c for c in cases if c["kind"]=="real" and c["family"]==family]
            for trial,order in enumerate(p["workflow_orders"]):
                for method in order:
                    start=time.perf_counter_ns();decisions=[]
                    for c in group:
                        y,s=load(c);pr,roc,winners=evaluate(method,y,s,c["width"])
                        decisions.append({"name":c["name"],"values":pr.tolist(),"roc":None if roc is None else roc.tolist(),"winners":winners})
                    with (CACHE/"last-output.json").open("w") as f:json.dump(decisions,f,allow_nan=False)
                    elapsed=(time.perf_counter_ns()-start)*1e-9
                    log.write(json.dumps({"family":family,"method":method,"trial":trial,"seconds":elapsed,"decisions":decisions})+"\n");log.flush()
            print(family,"workflow complete",flush=True)
    from sparse_vus.saturation import profile_saturation
    with (OUT/"diagnostics.jsonl").open("x") as log:
        for c in cases:
            y,s=load(c)
            for model,score in enumerate(s):
                d=profile_saturation(y,score,c["width"])
                if abs(d["values"]["pr"]-references[c["name"]][model])>1e-11:raise ValueError("diagnostic parity")
                log.write(json.dumps({"name":c["name"],"model":model,**d})+"\n")
    write(OUT/"complete.json",{"status":"COMPLETE","protocol_sha256":sha(OUT/"protocol.json"),"inputs_sha256":sha(OUT/"inputs.json"),
        **{name+"_sha256":sha(OUT/(name+".jsonl")) for name in ("records","workflows","diagnostics")},"utc":datetime.now(timezone.utc).isoformat()})


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=["freeze","generate","run"])
    globals()[parser.parse_args().command]()
