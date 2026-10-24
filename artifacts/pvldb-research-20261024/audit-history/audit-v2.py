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
import zipfile
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


def equivalent(actual, expected, path="summary"):
    """Compare complete reported structures, rejecting absent and extra fields."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or actual.keys() != expected.keys():
            raise ValueError(f"{path}: field mismatch")
        for key in expected: equivalent(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
            raise ValueError(f"{path}: length mismatch")
        for i, (a, b) in enumerate(zip(actual, expected)): equivalent(a, b, f"{path}[{i}]")
    elif isinstance(expected, (float, np.floating)):
        if not isinstance(actual, (int, float)) or not np.isfinite(actual) or not np.isclose(actual, expected, rtol=1e-12, atol=1e-13):
            raise ValueError(f"{path}: numerical mismatch")
    elif actual != expected:
        raise ValueError(f"{path}: mismatch")


def ratio_summary(ratios):
    """Independent reconstruction of the declared paired log bootstrap."""
    r = np.asarray(ratios, dtype=float)
    if r.ndim != 1 or not len(r) or not np.isfinite(r).all() or np.any(r <= 0):
        raise ValueError("positive finite ratios required")
    z = np.log(r)
    indices = np.random.default_rng(20261024).integers(len(r), size=(10000, len(r)))
    simulated = z[indices].mean(axis=1)
    return {"geometric_speedup": float(np.exp(z.mean())),
            "ci95": np.exp(np.quantile(simulated, [.025, .975])).tolist(),
            "ci_familywise95_3collections": np.exp(np.quantile(simulated, [.05/6, 1-.05/6])).tolist(),
            "case_wins": int(np.count_nonzero(r > 1)), "cases": len(r),
            "minimum_speedup": float(r.min()), "maximum_speedup": float(r.max())}


def workflow_summaries(rows, families, methods, repetitions, candidate="stream"):
    keyed = {(r["family"], r["method"], r["trial"]): r["seconds"] for r in rows}
    result = {}
    for family in families:
        # Explicit trial keys are the pairing unit, independent of file order.
        times = {m: [keyed[family, m, t] for t in range(repetitions)] for m in methods}
        med = {m: statistics.median(t) for m, t in times.items()}
        if any(not np.isfinite(x) or x <= 0 for t in times.values() for x in t):
            raise ValueError("invalid workflow duration")
        result[family] = {"median_seconds": med, "all_seconds": times,
            "baseline_over_stream": {m: med[m]/med[candidate] for m in methods},
            "paired_trial_uncertainty": {m: ratio_summary(np.array(times[m])/times[candidate])
                                         for m in methods if m != candidate}}
    return result


def validate_inputs(root, p, inputs):
    """Bind actual arrays and raw member bytes directly to the frozen cases."""
    root = Path(root); cases = {c["series"]: c for c in p["cases"]}
    coverage([c["series"] for c in p["cases"]], set(cases))
    coverage([c["series"] for c in inputs["series"]], set(cases))
    archive = root/"cache/TSB-AD-U.zip"
    if digest(archive) != p["archive_sha256"]: raise ValueError("archive binding mismatch")
    identities = {}; geometry = []; distinct = []
    with zipfile.ZipFile(archive) as z:
        for c in inputs["series"]:
            frozen = cases[c["series"]]
            for key, expected in frozen.items():
                if c.get(key) != expected: raise ValueError(f"frozen case metadata mismatch: {key}")
            if hashlib.sha256(z.read(frozen["member"])).hexdigest() != frozen["raw_sha256"]:
                raise ValueError("raw archive member mismatch")
            file = root/".cache/pvldb-full-precision-20261024"/c["file"]
            if digest(file) != c["npz_sha256"] or file.stat().st_size != c["bytes"]:
                raise ValueError("array file identity mismatch")
            with np.load(file, allow_pickle=False) as arrays:
                y, s, x = arrays["labels"], arrays["scores"], arrays["observations"]
            n = frozen["n"]
            if (x.shape != (n,) or y.shape != (n,) or s.shape != (len(p["models"]), n)
                    or s.dtype != np.float64 or not np.isfinite(s).all() or not np.isfinite(x).all()
                    or not np.isin(y, [0, 1]).all() or int(y.sum()) != frozen["positive_points"]):
                raise ValueError("array axes/value mismatch")
            identity = hashlib.sha256(x.astype(np.float64).tobytes()+y.astype(np.int8).tobytes()).hexdigest()
            if identity != frozen["observation_label_identity"]: raise ValueError("frozen raw identity mismatch")
            if hashlib.sha256(s.tobytes()).hexdigest() != c["score_sha256"]: raise ValueError("score identity mismatch")
            if set(c["models"]) != set(p["models"]): raise ValueError("model metadata mismatch")
            for model, score in zip(p["models"], s):
                d = len(np.unique(score)); distinct.append(d)
                if c["models"][model]["distinct"] != d: raise ValueError("distinct-score metadata mismatch")
            label_hash = hashlib.sha256(y.astype(np.int8).tobytes()).hexdigest()
            identities[c["series"]] = label_hash
            geometry.append({"series": c["series"], "family": c["family"], "n": n, "label_sha256": label_hash,
                             "widths": {str(w): label_geometry(y, w) for w in p["widths"]}})
    return identities, geometry, {"min": min(distinct), "max": max(distinct)}


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
    p, inputs, report, complete, start = [read(folder/name) for name in ("protocol.json", "inputs.json", "report.json", "run-complete.json", "run-start.json")]
    if inputs["protocol_sha256"] != digest(folder/"protocol.json"): raise ValueError("input protocol binding")
    for name in ("protocol", "inputs"):
        if start[name+"_sha256"] != digest(folder/f"{name}.json"): raise ValueError("run-start binding")
    if any(d["status"] != "COMPLETE" for d in (inputs, report, complete)): raise ValueError("incomplete receipt")
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
    max_error = 0.; max_record_error = 0.; times = defaultdict(list)
    for row in rows:
        name, width, method = row["series"], row["width"], row["method"]
        if row["family"] != cases[name]["family"] or len(row["values"]) != len(p["models"]): raise ValueError("case metadata mismatch")
        if not np.isfinite(row["seconds"]) or row["seconds"] <= 0: raise ValueError("invalid timing")
        error = check_values(row["values"], row["winners"], references[name, width])
        if not np.isclose(row["max_error"], error, rtol=1e-12, atol=1e-18): raise ValueError("record error metadata")
        max_error = max(max_error, error); max_record_error = max(max_record_error, error)
        times[name, width, method].append(row["seconds"])
    for row in workflow:
        coverage([c["series"] for c in row["decisions"]], {n for n,c in cases.items() if c["family"] == row["family"]})
        for c in row["decisions"]: max_error=max(max_error, check_values(c["values"],c["winners"],references[c["series"],p["primary_width"]]))
        if row["seconds"] <= 0 or not np.isfinite(row["seconds"]): raise ValueError("bad workflow time")
    dev = read(base/"development/protocol.json")["cases"]
    dev_labels = {r["arrays"]["labels"]["sha256"]:r["series"] for r in dev}
    identities, geometry, distinct = validate_inputs(root, p, inputs)
    shared = [{"series": n, "development": dev_labels[h]} for n, h in identities.items() if h in dev_labels]
    equivalent(report["distinct_values"], distinct, "distinct_values")
    for key, expected in [("series", len(cases)), ("score_vectors", len(cases)*len(p["models"])),
                           ("all_workflow_winner_sets_agree", True)]:
        equivalent(report[key], expected, key)
    if not np.isclose(report["scalar_error_max"], max_record_error, rtol=1e-12, atol=1e-18):
        raise ValueError("reported maximum scalar error mismatch")
    stats={}; fresh_geometry_stats={}
    for width in p["widths"]:
        for family in p["collections"]:
            names=[n for n,c in cases.items() if c["family"]==family]
            result={}; disjoint={}
            for method in methods:
                if method=="stream":continue
                ratios=[statistics.median(times[n,width,method])/statistics.median(times[n,width,"stream"]) for n in names]
                expected=report["case_paired_summaries"][f"{family}_L{width}"][method]
                equivalent(expected, ratio_summary(ratios), f"case_summary.{family}.L{width}.{method}")
                result[method]=block_summary(ratios,[identities[n] for n in names])
                kept=[(n,r) for n,r in zip(names,ratios) if identities[n] not in dev_labels]
                if kept:disjoint[method]={**block_summary([r for n,r in kept],[identities[n] for n,r in kept]),"series":len(kept)}
            stats[f"{family}_L{width}"]=result;fresh_geometry_stats[f"{family}_L{width}"]=disjoint
    workflows = workflow_summaries(workflow, p["collections"], methods, p["repetitions"])
    equivalent(report["workflows"], workflows, "workflow_summary")
    total_by_method={m:sum(workflows[f]["median_seconds"][m] for f in p["collections"]) for m in methods}
    result={"status":"PASS","audit_version":2,"audit_kind":"independent code/data/record and complete statistical reconstruction, not a fresh timing run",
            "source_sha256":digest(__file__),"records":len(rows),"workflows":len(workflow),"max_error":max_error,
            "report_sha256":digest(folder/"report.json"), "protocol_sha256":digest(folder/"protocol.json"),
            "run_start_sha256":digest(folder/"run-start.json"), "inputs_sha256":digest(folder/"inputs.json"),
            "verified_principal_summaries":report["case_paired_summaries"], "verified_workflows":workflows,
            "identical_label_block_sensitivity":stats,"geometry_disjoint_from_development_sensitivity":fresh_geometry_stats,
            "shared_development_label_geometries":shared,"geometry":geometry,
            "sum_collection_median_seconds":total_by_method,
            "limits":"Equal-label grouping is conservative about repeated geometry but does not identify all physical-recording dependencies. CIs describe this collection/workload, not all future domains. LOF novelty mode scores include fitting windows; these are deterministic evaluator inputs, not a validated detection-accuracy protocol."}
    with Path(output).open("x") as f:json.dump(result,f,indent=2,allow_nan=False);f.write("\n")
    print(json.dumps({k:result[k] for k in ["status","records","workflows","max_error","sum_collection_median_seconds"]},indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();audit(args.root,args.output)
