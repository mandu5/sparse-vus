"""Independently reconstruct supplementary exact/approximate comparisons.

No metric kernel or experiment producer is imported. ROC arrays are independently
compared in the complete workflow records; case records retain only ROC errors.
The latter are checked against the corresponding deterministic workflow values.
This is a record audit, distinct from a fresh execution by the reproduction CLI.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

from audit_pvldb20261024 import (digest, read, coverage, equivalent, ratio_summary,
                                block_summary, validate_inputs, workflow_summaries)
import numpy as np

SAMPLED = {"klein250", "klein1000"}
PAIRS = {"benchopt_pair", "radix_pair"}


def selection(reference, values):
    reference, values = np.asarray(reference, float), np.asarray(values, float)
    if reference.ndim != 1 or not len(reference) or values.shape != reference.shape or not np.isfinite(values).all():
        raise ValueError("invalid supplementary values")
    chosen = np.flatnonzero(values >= values.max()-1e-10).tolist()
    truth = np.flatnonzero(reference >= reference.max()-1e-10).tolist()
    loss = reference.max()-reference[chosen]
    return {"selected": chosen, "exact_winners": truth, "minimum_regret": float(loss.min()),
            "maximum_regret": float(loss.max()), "identical_winner_set": chosen == truth}


def audit(root, output):
    root = Path(root).resolve(); base = root/"artifacts/pvldb-research-20261024"
    folder = base/"supplement"; primary = base/"full-precision"
    p, start, complete = [read(folder/name) for name in ("protocol.json", "run-start.json", "complete.json")]
    parent, inputs = read(primary/"protocol.json"), read(primary/"inputs.json")
    if p["primary_protocol_sha256"] != digest(primary/"protocol.json") or p["inputs_sha256"] != digest(primary/"inputs.json"):
        raise ValueError("supplement parent binding mismatch")
    if inputs["protocol_sha256"] != p["primary_protocol_sha256"]: raise ValueError("input protocol mismatch")
    for receipt in (start, complete):
        if receipt["protocol_sha256"] != digest(folder/"protocol.json"): raise ValueError("supplement run binding")
    if complete["status"] != "COMPLETE": raise ValueError("incomplete supplement")
    for name in ("records", "workflows"):
        if complete[name+"_sha256"] != digest(folder/f"{name}.jsonl"): raise ValueError("supplement record binding")
    for path, expected in p["source_sha256"].items():
        if digest(root/path) != expected: raise ValueError(f"supplement source binding: {path}")
    labels, _, _ = validate_inputs(root, parent, inputs)
    rows = [json.loads(s) for s in (folder/"records.jsonl").read_text().splitlines()]
    workflows = [json.loads(s) for s in (folder/"workflows.jsonl").read_text().splitlines()]
    primary_rows = [json.loads(s) for s in (primary/"records.jsonl").read_text().splitlines()]
    primary_complete = read(primary/"run-complete.json")
    if digest(primary/"records.jsonl") != primary_complete["records_sha256"]: raise ValueError("primary record binding")
    cases = {c["series"]: c for c in parent["cases"]}; methods = p["methods"]; trials = range(p["repetitions"])
    references = {r["series"]: r["values"] for r in primary_rows
                  if r["method"] == "released" and r["trial"] == 0 and r["width"] == p["width"]}
    if references.keys() != cases.keys(): raise ValueError("missing primary numerical reference")
    coverage([(r["series"], r["method"], r["trial"]) for r in rows],
             {(n, m, t) for n in cases for m in methods for t in trials})
    coverage([(r["family"], r["method"], r["trial"]) for r in workflows],
             {(f, m, t) for f in parent["collections"] for m in methods for t in trials})
    row_map = {(r["series"], r["method"], r["trial"]): r for r in rows}
    roc_reference = {c["series"]: np.asarray(c["roc"], float) for r in workflows
                     if r["method"] == "radix_pair" and r["trial"] == 0 for c in r["decisions"]}
    if roc_reference.keys() != cases.keys(): raise ValueError("missing ROC reference")
    roc_errors = {}; max_workflow_error = 0.; max_roc_error = 0.
    for r in workflows:
        family, method, trial = r["family"], r["method"], r["trial"]
        coverage([c["series"] for c in r["decisions"]], {n for n, c in cases.items() if c["family"] == family})
        for c in r["decisions"]:
            name = c["series"]; values = np.asarray(c["values"], float)
            s = selection(references[name], values)
            if c["winners"] != s["selected"]: raise ValueError("workflow winner mismatch")
            equivalent(c["values"], row_map[name, method, trial]["values"], "workflow/case PR parity")
            error = float(np.max(np.abs(values-references[name])))
            if method not in SAMPLED:
                if error > 1e-11 or not s["identical_winner_set"]: raise ValueError("exact workflow PR failure")
                max_workflow_error = max(max_workflow_error, error)
            if method in PAIRS:
                roc = np.asarray(c["roc"], float)
                if roc.shape != (len(parent["models"]),) or not np.isfinite(roc).all(): raise ValueError("invalid ROC array")
                roc_error = float(np.max(np.abs(roc-roc_reference[name])))
                if roc_error > 1e-11: raise ValueError("workflow ROC parity failure")
                roc_errors[name, method, trial] = roc_error; max_roc_error = max(max_roc_error, roc_error)
            elif c["roc"] is not None: raise ValueError("unexpected ROC output")
    times = defaultdict(list); accuracy_cases = {}; max_exact_error = 0.
    for r in rows:
        name, method, trial = r["series"], r["method"], r["trial"]
        if r["family"] != cases[name]["family"]: raise ValueError("case collection mismatch")
        if not np.isfinite(r["seconds"]) or r["seconds"] <= 0: raise ValueError("invalid case time")
        values = np.asarray(r["values"], float); s = selection(references[name], values)
        if r["winners"] != s["selected"]: raise ValueError("case winners mismatch")
        equivalent(r["selection"], s, "selection regret")
        error = float(np.max(np.abs(values-references[name])))
        equivalent(r["pr_error"], error, "PR error")
        if method not in SAMPLED:
            if error > 1e-11 or not s["identical_winner_set"]: raise ValueError("exact case PR failure")
            max_exact_error = max(max_exact_error, error)
        if method in PAIRS: equivalent(r["roc_error"], roc_errors[name, method, trial], "record/workflow ROC error")
        elif r["roc_error"] is not None: raise ValueError("unexpected record ROC error")
        times[name, method].append(r["seconds"])
        entry = {**s, "scalar_error": error}
        if (name, method) in accuracy_cases: equivalent(entry, accuracy_cases[name, method], "deterministic trial values")
        else: accuracy_cases[name, method] = entry
    case_summaries = {}; blocks = {}; matched = {}; accuracy = {}
    workflow = workflow_summaries(workflows, parent["collections"], methods, p["repetitions"])
    for family in parent["collections"]:
        names = [n for n, c in cases.items() if c["family"] == family]
        med = {m: np.array([statistics.median(times[n, m]) for n in names]) for m in methods}
        case_summaries[family] = {m: ratio_summary(med[m]/med["stream"]) for m in methods if m != "stream"}
        blocks[family] = {m: block_summary(med[m]/med["stream"], [labels[n] for n in names]) for m in methods if m != "stream"}
        w = workflow[family]
        matched[family] = {"case_paired": ratio_summary(med["benchopt_pair"]/med["radix_pair"]),
            "identical_label_blocks": block_summary(med["benchopt_pair"]/med["radix_pair"], [labels[n] for n in names]),
            "workflow_median_ratio": w["median_seconds"]["benchopt_pair"]/w["median_seconds"]["radix_pair"],
            "workflow_paired": ratio_summary(np.array(w["all_seconds"]["benchopt_pair"])/w["all_seconds"]["radix_pair"])}
        accuracy[family] = {}
        for method in methods:
            items = [accuracy_cases[n, method] for n in names]
            accuracy[family][method] = {"series": len(names), "winner_set_changes": sum(not c["identical_winner_set"] for c in items),
                "minimum_regret_at_least_threshold": sum(c["minimum_regret"] >= p["regret_threshold"] for c in items),
                "maximum_regret_at_least_threshold": sum(c["maximum_regret"] >= p["regret_threshold"] for c in items),
                "maximum_regret": max(c["maximum_regret"] for c in items),
                "mean_minimum_regret": float(np.mean([c["minimum_regret"] for c in items])),
                "maximum_scalar_error": max(c["scalar_error"] for c in items)}
    result = {"status": "PASS", "audit_kind": "independent supplement record reconstruction, not a fresh run",
        "source_sha256": digest(__file__), "shared_auditor_sha256": digest(Path(__file__).with_name("audit_pvldb20261024.py")),
        "protocol_sha256": digest(folder/"protocol.json"), "inputs_sha256": digest(primary/"inputs.json"),
        "records_sha256": digest(folder/"records.jsonl"), "workflows_sha256": digest(folder/"workflows.jsonl"),
        "records": len(rows), "workflows": len(workflows), "max_exact_pr_error": max_exact_error,
        "max_exact_workflow_pr_error": max_workflow_error, "max_workflow_roc_error": max_roc_error,
        "case_paired": case_summaries, "identical_label_block_sensitivity": blocks,
        "workflow_summaries": workflow, "matched_pair": matched, "accuracy": accuracy,
        "case_accuracy": [{"series": n, "method": m, **c} for (n, m), c in accuracy_cases.items()],
        "qualifications": ["Benchopt's native API computes both ROC and PR; PR-consumer ratios differ in returned work.",
            "Matched pair ratios compare both outputs. Klein exact is the equal-output PR-only comparator.",
            "Case confidence intervals resample fixed-panel series; equal-label blocks are a sensitivity, not known physical identities.",
            "Trial intervals describe timing variation on a fixed collection, not new datasets.",
            "Supplement was frozen after primary results; numerical parity is not real-arithmetic certification."]}
    with Path(output).open("x") as f: json.dump(result, f, indent=2, allow_nan=False); f.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "records", "workflows", "max_exact_pr_error", "max_workflow_roc_error", "accuracy")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); audit(args.root, args.output)
