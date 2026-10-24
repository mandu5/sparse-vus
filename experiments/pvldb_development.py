"""Development-only comparison of three remedies; never held-out evidence."""
from __future__ import annotations
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[key] = "1"
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import time

import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "experiments")]
from sparse_vus.batch import batch_pr
from sparse_vus.radix import sparse_pr_radix_jit
from sparse_vus.dense_radix import dense_pr_nearest_radix_jit
from sparse_vus.sampling_bounds import certified_sampled_pr
from fast_vus_adapter import fast_vus_pr


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def evaluate(method, y, scores, width):
    if method in ("geometry", "stream"):
        values = batch_pr(y, scores, width, strategy=method)
    elif method == "certificate_fallback":
        certificates = [certified_sampled_pr(y, s, width, 250) for s in scores]
        winner = next((i for i, c in enumerate(certificates)
                       if all(i == j or c.certifies_greater_than(o)
                              for j, o in enumerate(certificates))), None)
        if winner is not None:
            return {"winner": winner, "certified": True, "values": None}
        values = np.asarray([sparse_pr_radix_jit(y, s, width) for s in scores])
    elif method == "released":
        values = np.asarray([sparse_pr_radix_jit(y, s, width) for s in scores])
    elif method == "dense":
        values = np.asarray([dense_pr_nearest_radix_jit(y, s, width) for s in scores])
    elif method == "external":
        values = np.asarray([fast_vus_pr(y, s, width, len(y)) for s in scores])
    else:
        raise ValueError(method)
    return {"winner": int(np.argmax(values)), "certified": False, "values": values.tolist()}


def main():
    out = ROOT / "artifacts/pvldb-research-20261024/development"
    out.mkdir(parents=True, exist_ok=False)
    source = json.loads((ROOT / "artifacts/collection-workflow/mac-20261023/inputs.json").read_text())
    cases = [r for f in ("NAB", "SMAP", "SMD") for r in sorted(
        (r for r in source if r["family"] == f), key=lambda r:r["series"])[:2]]
    methods = ["released", "geometry", "stream", "dense", "external", "certificate_fallback"]
    dependencies = ["src/sparse_vus/batch.py", "src/sparse_vus/radix.py",
                    "src/sparse_vus/sampling_bounds.py", "src/sparse_vus/pr_compiled.py",
                    "src/sparse_vus/dense_radix.py", "experiments/pvldb_development.py",
                    "experiments/fast_vus_adapter.py", ".cache/fast_vus/fast_vus.py"]
    protocol = {"kind":"development_on_previously_measured_raw_recordings_and_scores",
                "primary_width":30, "repetitions":6, "methods":methods, "cases":cases,
                "source_sha256":{p:digest(ROOT/p) for p in dependencies},
                "orders":[methods[i:]+methods[:i] for i in range(len(methods))],
                "timing":"all preparation and exact fallback; imports/JIT excluded; one CPU thread",
                "platform":platform.platform(), "python":sys.version,
                "numpy":np.__version__}
    (out/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    y = np.array([0,1,0,0,1,0], dtype=np.int8)
    s = np.array([[1,2,3,4,5,6], [6,5,4,3,2,1], [1,1,0,0,1,1]],float)
    for method in methods:
        evaluate(method,y,s,30)
    records=[]
    with (out/"records.jsonl").open("x") as file:
        for case in cases:
            path=ROOT/".cache/vus-collection/mac-20261023"/case["file"]
            if digest(path)!=case["npz_sha256"]:
                raise ValueError("changed cached input")
            with np.load(path,allow_pickle=False) as z:
                y=z["labels"]; scores=np.stack([z[f"score_{i}"] for i in range(3)])
            expected=np.asarray(evaluate("released",y,scores,30)["values"])
            for trial,order in enumerate(protocol["orders"]):
                for method in order:
                    started=time.perf_counter_ns(); result=evaluate(method,y,scores,30)
                    seconds=(time.perf_counter_ns()-started)*1e-9
                    if result["winner"] != int(np.argmax(expected)):
                        raise ValueError("winner mismatch")
                    error=None if result["values"] is None else float(np.max(np.abs(expected-result["values"])))
                    if error is not None and error>1e-11:
                        raise ValueError("scalar mismatch")
                    row={"series":case["series"],"family":case["family"],"method":method,
                         "trial":trial,"seconds":seconds,"n":len(y),
                         "distinct_scores":[len(np.unique(s)) for s in scores],
                         "max_error":error,**result}
                    records.append(row); file.write(json.dumps(row)+"\n"); file.flush()
            print(case["series"],"complete",flush=True)
    medians={}
    for case in cases:
        medians[case["series"]]={m:statistics.median(r["seconds"] for r in records
                if r["series"]==case["series"] and r["method"]==m) for m in methods}
    report={"status":"COMPLETE_DEVELOPMENT", "cases":len(cases),"calls":len(records),
            "protocol_sha256":digest(out/"protocol.json"),"records_sha256":digest(out/"records.jsonl"),
            "case_medians":medians,"released_over_method_geomean":{
                m:float(np.exp(np.mean([np.log(v["released"]/v[m]) for v in medians.values()])))
                for m in methods},
            "certificate_early_returns":sum(r["certified"] for r in records),
            "max_scalar_difference":max(r["max_error"] or 0 for r in records)}
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report["released_over_method_geomean"],indent=2),flush=True)


if __name__=="__main__":
    main()
