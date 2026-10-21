"""Append-only tests of the newly located baseline and certified width method.

The protocol is written before outcomes. The existing released measurements
are used only for fixed input selection and input hashes, never as new timings.
"""
from __future__ import annotations

import os
for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_key] = "1"

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import zipfile

import numpy as np
import pandas as pd
import numba
from threadpoolctl import threadpool_info, threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sparse_vus.compiled import sparse_vus_jit, dense_vus_jit, dense_vus_direct_jit
from sparse_vus.core import dense_vus


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def corpus_rows(mode):
    rows = [json.loads(line) for line in
            (ROOT / "artifacts/public_benchmark.jsonl").read_text().splitlines()]
    if mode == "baseline":
        return rows
    selected = {r["series"] for r in json.loads(
        (ROOT / "artifacts/external_supplement_selection.json").read_text())}
    output = []
    for row in rows:
        if row["series"] in selected and row["max_buffer"] == 30:
            for width in (30, 100, 300):
                output.append({**row, "max_buffer": width})
    return output


class Corpus:
    def __init__(self):
        manifest = json.loads((ROOT / "experiments/data_manifest.json").read_text())
        self.labels = zipfile.ZipFile(ROOT / "cache/TSB-AD-U.zip")
        self.names = {Path(n).stem: n for n in self.labels.namelist()
                      if n.endswith(".csv")}
        self.scores = {m["name"]: zipfile.ZipFile(
            ROOT / f"cache/{m['name']}.score-range.zip") for m in manifest["models"]}
        self.hashes = {}
        for name in self.scores:
            receipt = json.loads((ROOT / f"artifacts/{name}-download.json").read_text())
            self.hashes[name] = {Path(r["path"]).stem: r["sha256"]
                                 for r in receipt["members"]}
        self.cached_key = None

    def load(self, row):
        key = row["series"], row["model"]
        if key != self.cached_key:
            raw_y = self.labels.read(self.names[key[0]])
            raw_s = self.scores[key[1]].read(f"scores/{key[0]}.npy")
            if hashlib.sha256(raw_y).hexdigest() != row["label_member_sha256"]:
                raise ValueError("label hash mismatch")
            if hashlib.sha256(raw_s).hexdigest() != self.hashes[key[1]][key[0]]:
                raise ValueError("score hash mismatch")
            self.cached = (pd.read_csv(io.BytesIO(raw_y))["Label"].to_numpy(np.int8),
                           np.load(io.BytesIO(raw_s), allow_pickle=False))
            self.cached_key = key
        return self.cached


def freeze(output, mode):
    rows = corpus_rows(mode)
    protocol = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "Before this experiment's outcomes; after inspecting v0.1.0 outcomes.",
        "mode": mode,
        "selection": ("All 350 original common series, 3 models, widths 10 and 30."
                      if mode == "baseline" else
                      "Original metadata-only 42-series cross-family selection; "
                      "all 3 models, widths 30, 100, 300."),
        "cases": len(rows), "repetitions": 3, "seed": 202610201,
        "source_scores": "Unchanged released vectors, including documented zero padding.",
        "timing": "Whole-call validation and preprocessing included; JIT warmup excluded. "
                  "One thread; random method order in each repetition; serial timings.",
        "baseline_comparison": "Actual fast-VUS returns PR only; Sparse VUS computes "
                               "both ROC and PR, so this comparison favors fast-VUS.",
        "certified_atol": [0.01, 0.001],
        "atol_definition": "Both returned interval half-widths <= atol.",
        "float64_containment_tolerance": 1e-10,
        "exact_parity_tolerance": 1e-11,
        "reporting": "All cases and regressions; no timing substitution from old runs; "
                     "float64 numerical audit is not directed-rounding certification.",
        "selection_sha256": hashlib.sha256(json.dumps(
            [(r["series"], r["model"], r["max_buffer"]) for r in rows],
            separators=(",", ":")).encode()).hexdigest(),
    }
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "protocol.json", protocol)
    return rows, protocol


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("baseline", "certified"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cpu-clearance", required=True)
    args = parser.parse_args()
    rows, protocol = freeze(args.output, args.mode)
    numba.set_num_threads(1)
    threadpool_limits(1)
    if args.mode == "baseline":
        from fast_vus_adapter import fast_vus_pr, source_receipt
        methods = {
            "sparse_exact": sparse_vus_jit,
            "fast_vus_exact_pr": lambda y, s, w: (None, float(fast_vus_pr(y, s, w, len(y)))),
            "dense_direct": dense_vus_direct_jit,
            "dense_nearest": dense_vus_jit,
            "dense_numpy": dense_vus,
        }
    else:
        from sparse_vus.certified import certified_vus
        methods = {
            "sparse_exact": sparse_vus_jit,
            "certified_0.01": lambda y, s, w: certified_vus(y, s, w, atol=0.01),
            "certified_0.001": lambda y, s, w: certified_vus(y, s, w, atol=0.001),
        }
    warm = {}
    yy, ss = np.array([0, 1, 0, 0, 1, 0], np.int8), np.arange(6, dtype=float)
    for name, method in methods.items():
        t = time.perf_counter()
        method(yy, ss, 4)
        warm[name] = time.perf_counter() - t
    sources = [Path(__file__), ROOT / "src/sparse_vus/core.py",
               ROOT / "src/sparse_vus/compiled.py"]
    sources += ([ROOT / "experiments/fast_vus_adapter.py"] if args.mode == "baseline"
                else [ROOT / "src/sparse_vus/certified.py"])
    if args.mode == "baseline":
        sources.append(ROOT / ".cache/fast_vus/fast_vus.py")
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    env = {"started_utc": datetime.now(timezone.utc).isoformat(),
           "platform": platform.platform(), "machine": platform.machine(),
           "python": sys.version, "numpy": np.__version__, "numba": numba.__version__,
           "cpu_clearance": args.cpu_clearance, "warmup_seconds": warm,
           "threads": numba.get_num_threads(), "threadpool_info": threadpool_info(),
           "source_sha256": source_hashes,
           "protocol_sha256": digest(args.output / "protocol.json")}
    if args.mode == "baseline":
        env["external_baseline"] = source_receipt()
    if sys.platform == "darwin":
        env["cpu"] = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    else:
        env["cpu"] = platform.processor()
        if Path("/proc/cpuinfo").exists():
            env["cpuinfo"] = Path("/proc/cpuinfo").read_text()
    write_json(args.output / "environment.json", env)
    rng = np.random.default_rng(protocol["seed"])
    corpus = Corpus()
    ratios, fractions = defaultdict(list), defaultdict(list)
    errors, violations = [], []
    with (args.output / "measurements.jsonl").open("x") as stream:
        for index, row in enumerate(rows):
            y, scores = corpus.load(row)
            timings, values = defaultdict(list), {}
            for repeat in range(protocol["repetitions"]):
                order = list(methods)
                rng.shuffle(order)
                for name in order:
                    started = time.perf_counter()
                    value = methods[name](y, scores, row["max_buffer"])
                    timings[name].append(time.perf_counter() - started)
                    if name.startswith("certified"):
                        value = {"roc_lower": value.roc_lower, "roc_upper": value.roc_upper,
                                 "pr_lower": value.pr_lower, "pr_upper": value.pr_upper,
                                 "estimate": list(value.estimate), "exact": value.exact,
                                 "evaluated_widths": list(value.evaluated_widths),
                                 "total_widths": value.total_widths,
                                 "curve_evaluations": value.curve_evaluations}
                    else:
                        value = [None if v is None else float(v) for v in value]
                    if name in values and value != values[name]:
                        raise AssertionError(f"nondeterministic result: {name}")
                    values[name] = value
            exact = values["sparse_exact"]
            medians = {name: statistics.median(ts) for name, ts in timings.items()}
            record = {k: row[k] for k in ("series", "family", "model", "n", "max_buffer")}
            record.update(values=values, seconds=dict(timings), median_seconds=medians,
                          label_sha256=row["label_member_sha256"],
                          score_sha256=corpus.hashes[row["model"]][row["series"]])
            checks = {}
            for name, value in values.items():
                if name.startswith("certified"):
                    tol = float(name.split("_")[1])
                    containment = (value["roc_lower"] - 1e-10 <= exact[0] <= value["roc_upper"] + 1e-10
                                   and value["pr_lower"] - 1e-10 <= exact[1] <= value["pr_upper"] + 1e-10)
                    half_width = max(value["roc_upper"] - value["roc_lower"],
                                     value["pr_upper"] - value["pr_lower"]) / 2
                    checks[name] = {"contains_exact": containment, "half_width": half_width,
                                    "max_midpoint_error": float(np.max(
                                        np.abs(np.asarray(value["estimate"]) - exact)))}
                    if not containment or half_width > tol + 1e-12:
                        violations.append({**record, "failure": name})
                    fractions[name].append(len(value["evaluated_widths"]) / value["total_widths"])
                    ratios[name].append(medians["sparse_exact"] / medians[name])
                elif name != "sparse_exact":
                    error = max(abs(a-b) for a, b in zip(value, exact) if a is not None)
                    checks[name] = {"max_error": error}
                    errors.append(error)
                    if error > protocol["exact_parity_tolerance"]:
                        violations.append({**record, "failure": name})
                    ratios[name].append(medians[name] / medians["sparse_exact"])
            record["checks"] = checks
            if args.mode == "baseline":
                for name, competitors in {
                    "fastest_dense": ["dense_direct", "dense_nearest", "dense_numpy"],
                    "fastest_tested": ["dense_direct", "dense_nearest", "dense_numpy",
                                       "fast_vus_exact_pr"],
                }.items():
                    ratios[name].append(min(medians[k] for k in competitors)
                                        / medians["sparse_exact"])
            stream.write(json.dumps(record, allow_nan=False) + "\n")
            stream.flush()
            if (index + 1) % 30 == 0 or index + 1 == len(rows):
                print(json.dumps({"done": index + 1, "total": len(rows),
                                  "violations": len(violations)}), flush=True)
    if source_hashes != {str(p.relative_to(ROOT)): digest(p) for p in sources}:
        raise RuntimeError("source changed during experiment")
    def stats(xs):
        return {"median": float(np.median(xs)), "geomean": float(np.exp(np.mean(np.log(xs)))),
                "min": float(min(xs)), "max": float(max(xs)),
                "above_one": int(np.sum(np.asarray(xs) > 1)), "count": len(xs)}
    summary = {"status": "PASS" if not violations else "FAIL",
               "cases": len(rows), "series": len({r["series"] for r in rows}),
               "families": len({r["family"] for r in rows}),
               "ratio_definition": ("comparator_seconds / sparse_exact_seconds"
                                    if args.mode == "baseline" else
                                    "sparse_exact_seconds / certified_seconds"),
               "speed_ratios": {k: stats(v) for k, v in ratios.items()},
               "evaluated_width_fractions": {k: stats(v) for k, v in fractions.items()},
               "max_exact_parity_error": max(errors, default=0.0),
               "violations": len(violations), "violation_records": violations,
               "measurements_sha256": digest(args.output / "measurements.jsonl"),
               "completed_utc": datetime.now(timezone.utc).isoformat()}
    write_json(args.output / "summary.json", summary)
    print(json.dumps(summary, indent=2, allow_nan=False))
    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
