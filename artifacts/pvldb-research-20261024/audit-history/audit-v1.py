"""Reconstruct frozen evidence without importing any producer or metric kernel.

This audits records, hashes, data identities and statistical summaries. It is
not a fresh timing run: use reproduce_pvldb20261024.py for that separate task.
"""
from __future__ import annotations
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import numpy as np


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while block := f.read(1 << 20): h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def coverage(actual, expected):
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("record coverage: duplicate, missing, or unexpected key")


def check_values(values, winners, reference):
    values, reference = np.asarray(values, float), np.asarray(reference, float)
    if values.ndim != 1 or not len(values) or values.shape != reference.shape or not np.isfinite(values).all():
        raise ValueError("invalid numerical values")
    selected = np.flatnonzero(values >= values.max() - 1e-10).tolist()
    if winners != selected: raise ValueError("winner list disagrees with values")
    error = float(np.max(np.abs(values - reference)))
    expected = np.flatnonzero(reference >= reference.max() - 1e-10).tolist()
    if error > 1e-11 or selected != expected: raise ValueError("scalar or winner parity failure")
    return error


def block_summary(ratios, labels):
    groups = defaultdict(list)
    if len(ratios) != len(labels) or not len(ratios): raise ValueError("nonempty paired inputs required")
    for ratio, label in zip(ratios, labels):
        if not np.isfinite(ratio) or ratio <= 0: raise ValueError("positive finite ratio required")
        groups[label].append(float(np.log(ratio)))
    means = np.array([np.mean(groups[k]) for k in sorted(groups)])
    rng = np.random.default_rng(20261024)
    samples = means[rng.integers(len(means), size=(10000, len(means)))].mean(axis=1)
    return {"geometric_speedup": float(np.exp(means.mean())), "blocks": len(means),
            "ci95": np.exp(np.quantile(samples, [.025, .975])).tolist(),
            "ci_familywise95_3collections": np.exp(np.quantile(samples, [.05/6, 1-.05/6])).tolist()}


def label_geometry(y, width):
    changes = np.diff(np.r_[0, y, 0]); starts = np.flatnonzero(changes == 1); ends = np.flatnonzero(changes == -1)-1
    intervals = []
    for start, end in zip(starts, ends):
        a, b = max(0, int(start)-width//2), min(len(y)-1, int(end)+width//2)
        if intervals and a <= intervals[-1][1]: intervals[-1][1] = max(b, intervals[-1][1])
        else: intervals.append([a, b])
    q = sum(b-a+1 for a, b in intervals)
    return {"original_components": len(starts), "expanded_components": len(intervals),
            "support": q, "support_fraction": q/len(y)}


def audit(root, output):
    root = Path(root).resolve(); base = root/"artifacts/pvldb-research-20261024"
    folder = base/"full-precision"; cache = root/".cache/pvldb-full-precision-20261024"
    p, inputs, report, complete = [read(folder/name) for name in ("protocol.json", "inputs.json", "report.json", "run-complete.json")]
    for file in ("protocol", "inputs", "records", "workflows"):
        extension = "jsonl" if file in ("records", "workflows") else "json"
        if digest(folder/f"{file}.{extension}") != report[f"{file}_sha256"]: raise ValueError(f"report binding: {file}")
    for file in ("records", "workflows"):
        if complete[f"{file}_sha256"] != report[f"{file}_sha256"]: raise ValueError("completion binding")
    for path, expected in p["source_sha256"].items():
        if digest(root/path) != expected: raise ValueError(f"source binding: {path}")
    rows = [json.loads(line) for line in (folder/"records.jsonl").read_text().splitlines()]
    workflow = [json.loads(line) for line in (folder/"workflows.jsonl").read_text().splitlines()]
    cases = {c["series"]: c for c in p["cases"]}; methods=p["methods"]; trials=range(p["repetitions"])
    coverage([(r["series"], r["width"], r["method"], r["trial"]) for r in rows],
             {(name, w, m, t) for name in cases for w in p["widths"] for m in methods for t in trials})
    coverage([(r["family"], r["method"], r["trial"]) for r in workflow],
             {(family, m, t) for family in p["collections"] for m in methods for t in trials})
    references = {(r["series"], r["width"]): r["values"] for r in rows if r["method"] == "released" and r["trial"] == 0}
    max_error = 0.; times = defaultdict(list)
    for row in rows:
        name, width, method = row["series"], row["width"], row["method"]
        if row["family"] != cases[name]["family"] or len(row["values"]) != len(p["models"]): raise ValueError("case metadata mismatch")
        if not np.isfinite(row["seconds"]) or row["seconds"] <= 0: raise ValueError("invalid timing")
        max_error = max(max_error, check_values(row["values"], row["winners"], references[name, width]))
        times[name, width, method].append(row["seconds"])
    for row in workflow:
        coverage([c["series"] for c in row["decisions"]], {n for n,c in cases.items() if c["family"] == row["family"]})
        for c in row["decisions"]: max_error=max(max_error, check_values(c["values"],c["winners"],references[c["series"],30]))
        if row["seconds"] <= 0 or not np.isfinite(row["seconds"]): raise ValueError("bad workflow time")
    dev = read(base/"development/protocol.json")["cases"]
    dev_labels = {r["arrays"]["labels"]["sha256"]:r["series"] for r in dev}
    identities = {}; geometry=[]; shared=[]
    coverage([r["series"] for r in inputs["series"]], set(cases))
    for case in inputs["series"]:
        file=cache/case["file"]
        if digest(file) != case["npz_sha256"]: raise ValueError("array file hash mismatch")
        with np.load(file,allow_pickle=False) as z:
            y,s,x=z["labels"],z["scores"],z["observations"]
        if hashlib.sha256(s.tobytes()).hexdigest()!=case["score_sha256"]: raise ValueError("score identity mismatch")
        if hashlib.sha256(x.astype(np.float64).tobytes()+y.astype(np.int8).tobytes()).hexdigest()!=case["observation_label_identity"]: raise ValueError("raw identity mismatch")
        if s.shape != (len(p["models"]),case["n"]) or not np.isfinite(s).all(): raise ValueError("score axes/value error")
        label_hash=hashlib.sha256(y.astype(np.int8).tobytes()).hexdigest(); identities[case["series"]]=label_hash
        if label_hash in dev_labels: shared.append({"series":case["series"],"development":dev_labels[label_hash]})
        geometry.append({"series":case["series"],"family":case["family"],"n":len(y),"label_sha256":label_hash,
                         "widths":{str(w):label_geometry(y,w) for w in p["widths"]}})
    stats={}; fresh_geometry_stats={}
    for width in p["widths"]:
        for family in p["collections"]:
            names=[n for n,c in cases.items() if c["family"]==family]
            result={}; disjoint={}
            for method in methods:
                if method=="stream":continue
                ratios=[statistics.median(times[n,width,method])/statistics.median(times[n,width,"stream"]) for n in names]
                expected=report["case_paired_summaries"][f"{family}_L{width}"][method]["geometric_speedup"]
                if not np.isclose(np.exp(np.mean(np.log(ratios))),expected,rtol=1e-12):raise ValueError("aggregate mismatch")
                result[method]=block_summary(ratios,[identities[n] for n in names])
                kept=[(n,r) for n,r in zip(names,ratios) if identities[n] not in dev_labels]
                if kept:disjoint[method]={**block_summary([r for n,r in kept],[identities[n] for n,r in kept]),"series":len(kept)}
            stats[f"{family}_L{width}"]=result;fresh_geometry_stats[f"{family}_L{width}"]=disjoint
    total_by_method={m:sum(statistics.median(r["seconds"] for r in workflow if r["method"]==m and r["family"]==f) for f in p["collections"]) for m in methods}
    result={"status":"PASS","audit_kind":"independent code/data/record and statistical reconstruction, not a fresh timing run",
            "source_sha256":digest(__file__),"records":len(rows),"workflows":len(workflow),"max_error":max_error,
            "identical_label_block_sensitivity":stats,"geometry_disjoint_from_development_sensitivity":fresh_geometry_stats,
            "shared_development_label_geometries":shared,"geometry":geometry,
            "sum_collection_median_seconds":total_by_method,
            "limits":"Equal-label grouping is conservative about repeated geometry but does not identify all physical-recording dependencies. CIs describe this collection/workload, not all future domains. LOF novelty mode scores include fitting windows; these are deterministic evaluator inputs, not a validated detection-accuracy protocol."}
    with Path(output).open("x") as f:json.dump(result,f,indent=2,allow_nan=False);f.write("\n")
    print(json.dumps({k:result[k] for k in ["status","records","workflows","max_error","sum_collection_median_seconds"]},indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();audit(args.root,args.output)
