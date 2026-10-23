"""Frozen, resumable MSAD sampling study; no acquisition or score repair.

Run with the research environment and PYTHONPATH=src. Commands are freeze,
numerical, validate, timing and report. Timing requires an explicit idle-host
acknowledgment. The worker is isolated so the fixed watchdog can stop a native
call. Every metric call includes its own public-API preparation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import platform
import sys
import time
import uuid

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/msad-sampling-20261023"
METHODS = ("radix_exact", "saturation_exact", "dense_exact", "klein250", "matched250")


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def array_hash(array):
    a = np.ascontiguousarray(array)
    header = json.dumps({"dtype": a.dtype.str, "shape": list(a.shape)}, sort_keys=True).encode()
    return hashlib.sha256(header + b"\0" + a.tobytes()).hexdigest()


def verify_hashes(hashes, root=ROOT):
    for relative, expected in hashes.items():
        if sha256_file(Path(root) / relative) != expected:
            raise ValueError(f"Source/data hash mismatch: {relative}")


def load_case(row, models, root=ROOT):
    path = Path(root) / row["npz_path"]
    if sha256_file(path) != row["npz_sha256"]:
        raise ValueError(f"NPZ hash mismatch: {path}")
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ["labels", "observations", *models]}
    for name, a in arrays.items():
        if array_hash(a) != row["array_sha256"][name]:
            raise ValueError(f"Input array hash mismatch: {name}")
        if a.ndim != 1 or len(a) != row["n"] or not np.isfinite(a).all():
            raise ValueError(f"Invalid input shape or finite values: {name}")
    labels = arrays["labels"]
    if (not np.isin(labels, [0, 1]).all() or not 0 < labels.sum() < len(labels)
            or int(labels.sum()) != row["positive_points"]):
        raise ValueError("Invalid original label classes/count")
    return arrays


def compare_vectors(exact, sampled, tol=1e-10, practical=.01):
    if not exact or set(exact) != set(sampled):
        raise ValueError("Nonempty identical model pools required")
    models = sorted(exact)
    if not all(math.isfinite(v) for values in [exact, sampled] for v in values.values()):
        raise ValueError("Metric values must be finite")
    best = max(exact.values())
    def winners(values):
        return [m for m in models if values[m] >= max(values.values()) - tol]
    def top3(values):
        cutoff = sorted(values.values(), reverse=True)[min(3, len(models)) - 1]
        return [m for m in models if values[m] >= cutoff - tol]
    ew, sw = winners(exact), winners(sampled)
    concordant = discordant = tx = ty = large = 0
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            de, ds = exact[a] - exact[b], sampled[a] - sampled[b]
            se = 0 if abs(de) <= tol else (1 if de > 0 else -1)
            ss = 0 if abs(ds) <= tol else (1 if ds > 0 else -1)
            if se and ss:
                concordant += se == ss
                discordant += se != ss
                large += se != ss and abs(de) >= practical and abs(ds) >= practical
            elif se == 0 and ss:
                tx += 1
            elif se and ss == 0:
                ty += 1
    den = math.sqrt((concordant + discordant + tx) * (concordant + discordant + ty))
    et, st = top3(exact), top3(sampled)
    errors = [sampled[m] - exact[m] for m in models]
    return {
        "exact_winners": ew, "sampled_winners": sw,
        "winner_set_changed": ew != sw,
        "unique_winner_changed": len(ew) == len(sw) == 1 and ew != sw,
        "best_regret": max(0., best - max(exact[m] for m in sw)),
        "worst_regret": max(0., best - min(exact[m] for m in sw)),
        "lexical_regret": max(0., best - exact[sw[0]]),
        "exact_top3": et, "sampled_top3": st, "top3_changed": et != st,
        "pair_reversals": int(discordant), "large_pair_reversals": int(large),
        "pair_count": len(models) * (len(models) - 1) // 2,
        "kendall_tau_b": (concordant - discordant) / den if den else None,
        "mean_absolute_error": float(np.mean(np.abs(errors))),
        "maximum_absolute_error": max(abs(x) for x in errors),
        "minimum_signed_error": min(errors), "maximum_signed_error": max(errors),
    }


def read_records(path):
    result = {}
    if not Path(path).exists():
        return result
    with Path(path).open() as f:
        for number, line in enumerate(f, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Incomplete/corrupt JSONL line {number}; preserve and repair explicitly") from exc
            key = row["key"]
            if key in result and result[key] != row:
                raise ValueError(f"Conflicting duplicate record: {key}")
            result[key] = row
    return result


def append_record(path, row, index=None):
    index = read_records(path) if index is None else index
    key = row["key"]
    if key in index:
        if index[key] != row:
            raise ValueError(f"Conflicting duplicate record: {key}")
        return
    with Path(path).open("a") as f:
        f.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    index[key] = row


def timing_subset(rows):
    families = defaultdict(list)
    for r in rows:
        families[r["family"]].append(r)
    def key(r):
        return hashlib.sha256(("msad-vus-20261023-v1\0" + r["series"]).encode()).hexdigest()
    return [r for family in sorted(families)
            for r in sorted(families[family], key=key)[:2]]


def _summary(cases, practical):
    if not cases:
        return {"series": 0}
    return {"series": len(cases),
            "practical_regret_fraction": float(np.mean([c["best_regret"] >= practical for c in cases])),
            "worst_case_practical_regret_fraction": float(np.mean([c["worst_regret"] >= practical for c in cases])),
            "winner_set_change_fraction": float(np.mean([c["winner_set_changed"] for c in cases])),
            "unique_winner_change_fraction": float(np.mean([c["unique_winner_changed"] for c in cases])),
            "top3_change_fraction": float(np.mean([c["top3_changed"] for c in cases])),
            "mean_best_regret": float(np.mean([c["best_regret"] for c in cases])),
            "maximum_best_regret": max(c["best_regret"] for c in cases),
            "mean_absolute_error": float(np.mean([c["mean_absolute_error"] for c in cases])),
            "maximum_absolute_error": max(c["maximum_absolute_error"] for c in cases),
            "pair_reversals": sum(c["pair_reversals"] for c in cases),
            "large_pair_reversals": sum(c["large_pair_reversals"] for c in cases)}


def _family_bootstrap(cases, practical, config):
    by = defaultdict(list)
    for c in cases:
        by[c["family"]].append(c["best_regret"] >= practical)
    if not by:
        return None
    fam = sorted(by)
    numerator = np.array([sum(by[f]) for f in fam], float)
    denominator = np.array([len(by[f]) for f in fam], float)
    rng = np.random.default_rng(config["seed"])
    sampled = rng.integers(0, len(fam), (config["replicates"], len(fam)))
    pooled = numerator[sampled].sum(axis=1) / denominator[sampled].sum(axis=1)
    equal = (numerator[sampled] / denominator[sampled]).mean(axis=1)
    return {"unit": "source_family", "families": len(fam),
            "replicates": config["replicates"],
            "pooled_95_percentile": np.quantile(pooled, [.025, .975]).tolist(),
            "equal_family_95_percentile": np.quantile(equal, [.025, .975]).tolist()}


def build_report(records, rows, protocol):
    records = list(records)
    lookup = {}
    for r in records:
        if r.get("phase") in ("numerical", "validation"):
            key = (r["phase"], r["series"], r["model"], r["width"], r["method"], r["thresholds"])
            if key in lookup and lookup[key] != r:
                raise ValueError("Conflicting duplicate numerical result")
            lookup[key] = r
    parity_errors = []
    for r in records:
        if r.get("phase") not in ("numerical", "validation", "timing") or r["status"] != "ok":
            continue
        if r.get("phase") == "timing" or r["method"] in ("klein250", "dense_exact", "klein_exact"):
            method, budget = (("matched_sampled", 250) if r["method"] in ("klein250", "matched250") else ("radix_exact", None))
            base = lookup.get(("numerical", r["series"], r["model"], r["width"], method, budget))
            if base and base["status"] == "ok":
                err = abs(r["value"] - base["value"])
                parity_errors.append(err)
                if err > protocol["parity_tolerance"]:
                    raise ValueError(f"Metric parity failure: {r['series']}/{r['model']}/{r['method']}: {err}")
    upstream_expected = len(rows) * len(protocol["models"]) * len(protocol["widths"])
    upstream_ok = sum(lookup.get(("numerical", row["series"], model, width, "klein250", 250), {}).get("status") == "ok"
                      for row in rows for model in protocol["models"] for width in protocol["widths"])
    validation_rows = timing_subset(rows)
    validation_expected = len(validation_rows) * len(protocol["models"]) * 2
    validation_ok = sum(
        any(r.get("phase") == "validation" and r["series"] == row["series"]
            and r["model"] == model and r["width"] == protocol["primary_width"]
            and r["method"] == method and r["status"] == "ok" for r in lookup.values())
        for row in validation_rows for model in protocol["models"] for method in ("dense_exact", "klein_exact"))
    coverage = {"upstream_250_expected": upstream_expected, "upstream_250_ok": upstream_ok,
                "upstream_250_complete": upstream_ok == upstream_expected,
                "exact_validation_expected": validation_expected, "exact_validation_ok": validation_ok,
                "exact_validation_complete": validation_ok == validation_expected}
    controls_complete = coverage["upstream_250_complete"] and coverage["exact_validation_complete"]
    panels = {}
    for width in protocol["widths"]:
        for budget in protocol["threshold_budgets"]:
            cases, missing = [], []
            for row in sorted(rows, key=lambda x: x["series"]):
                vectors = []
                for method, h in [("radix_exact", None), ("matched_sampled", budget)]:
                    values = {}
                    for model in protocol["models"]:
                        r = lookup.get(("numerical", row["series"], model, width, method, h))
                        if r and r["status"] == "ok":
                            values[model] = r["value"]
                    vectors.append(values)
                if any(set(v) != set(protocol["models"]) for v in vectors):
                    missing.append(row["series"])
                    continue
                c = compare_vectors(*vectors, protocol["tie_tolerance"], protocol["practical_regret_threshold"])
                c.update(series=row["series"], family=row["family"])
                cases.append(c)
            by_family = {f: _summary([c for c in cases if c["family"] == f], protocol["practical_regret_threshold"])
                         for f in sorted({r["family"] for r in rows})}
            valid = [v for v in by_family.values() if v["series"]]
            equal = {k: float(np.mean([v[k] for v in valid])) for k in (
                "practical_regret_fraction", "mean_best_regret", "mean_absolute_error",
                "winner_set_change_fraction", "unique_winner_change_fraction")} if valid else {}
            practical_families = len({c["family"] for c in cases if c["best_regret"] >= protocol["practical_regret_threshold"]})
            pooled = _summary(cases, protocol["practical_regret_threshold"])
            gate = (not missing and pooled.get("practical_regret_fraction", 0) >= protocol["promotion_gate"]["minimum_series_fraction"]
                    and practical_families >= protocol["promotion_gate"]["minimum_source_families"])
            panels[f"L{width}_H{budget}"] = {
                "complete_series": len(cases), "missing_series": missing,
                "pooled": pooled, "equal_family": equal, "per_family": by_family,
                "families_with_practical_regret": practical_families,
                "effect_threshold_passed": bool(gate),
                "promotion_gate_passed": bool(gate and controls_complete),
                "family_bootstrap": _family_bootstrap(cases, protocol["practical_regret_threshold"], protocol["bootstrap"]),
                "cases": cases}
    primary = panels[f"L{protocol['primary_width']}_H{protocol['primary_thresholds']}"]
    timing = timing_report(records, protocol)
    timing["expected_records"] = len(validation_rows) * len(protocol["models"]) * len(METHODS) * protocol.get("timing", {}).get("repetitions", 5)
    timing["recorded_records"] = sum(r.get("phase") == "timing" for r in records)
    timing["missing_records"] = timing["expected_records"] - timing["recorded_records"]
    return {"study_id": protocol.get("study_id", "fixture"), "series_expected": len(rows),
            "record_status_counts": dict(sorted(Counter(r.get("status", "metadata") for r in records).items())),
            "parity_comparisons": len(parity_errors), "maximum_parity_error": max(parity_errors, default=None),
            "primary": primary, "panels": panels, "control_coverage": coverage,
            "timing": timing}


def timing_report(records, protocol):
    groups = defaultdict(dict)
    failures = Counter()
    for r in records:
        if r.get("phase") != "timing":
            continue
        if r["status"] != "ok":
            failures[r["method"] + ":" + r["status"]] += 1
            continue
        if not math.isfinite(r["seconds"]) or r["seconds"] <= 0:
            raise ValueError("Invalid timing duration")
        key = (r["series"], r["family"], r["model"], r["method"])
        if r["repetition"] in groups[key]:
            raise ValueError("Duplicate timing repetition")
        groups[key][r["repetition"]] = r["seconds"]
    reps = protocol.get("timing", {}).get("repetitions", 5)
    medians = {k: float(np.median(list(v.values()))) for k, v in groups.items() if len(v) == reps}
    ratios = {}
    for method in METHODS[1:]:
        by = defaultdict(list)
        for (series, family, model, m), sec in medians.items():
            base = medians.get((series, family, model, "radix_exact"))
            if m == method and base:
                by[family].append(sec / base)
        all_ratios = [r for family in sorted(by) for r in by[family]]
        if not all_ratios:
            ratios[method] = {"complete_paired_cases": 0}
            continue
        logs = [np.log(by[f]) for f in sorted(by)]
        rng = np.random.default_rng(protocol["bootstrap"]["seed"])
        indices = rng.integers(0, len(logs), (protocol["bootstrap"]["replicates"], len(logs)))
        sums = np.array([x.sum() for x in logs]); counts = np.array([len(x) for x in logs])
        draws = np.exp(sums[indices].sum(axis=1) / counts[indices].sum(axis=1))
        ratios[method] = {"complete_paired_cases": len(all_ratios),
                          "ratio_definition": "comparator_seconds / radix_exact_seconds",
                          "median_ratio": float(np.median(all_ratios)),
                          "geometric_mean_ratio": float(np.exp(np.mean(np.log(all_ratios)))),
                          "equal_family_geometric_mean_ratio": float(np.exp(np.mean([x.mean() for x in logs]))),
                          "family_bootstrap_95_percentile": np.quantile(draws, [.025, .975]).tolist(),
                          "per_family_geometric_mean_ratio": {f: float(np.exp(np.mean(np.log(v)))) for f, v in sorted(by.items())}}
    return {"successful_records": sum(len(v) for v in groups.values()),
            "failed_or_censored_records": dict(sorted(failures.items())),
            "incomplete_method_cases": sum(len(v) != reps for v in groups.values()),
            "ratios": ratios}


def _worker_main(conn, root_string):
    root = Path(root_string)
    sys.path.insert(0, str(root / "src")); sys.path.insert(0, str(root / "experiments"))
    from threadpoolctl import threadpool_limits
    from sparse_vus.core import dense_vus
    from sparse_vus.radix import sparse_pr_radix_jit
    from sparse_vus.saturation import sparse_pr_saturation_jit
    from sparse_vus.sampling import sampled_pr_radix_jit
    from fast_vus_adapter import fast_vus_pr
    def evaluate(method, y, s, width, budget):
        if method == "radix_exact":
            return sparse_pr_radix_jit(y, s, width)
        if method == "saturation_exact":
            return sparse_pr_saturation_jit(y, s, width)
        if method == "dense_exact":
            return dense_vus(y, s, width)[1]
        if method in ("klein250", "klein_exact"):
            return fast_vus_pr(y, s, width, len(y) if method == "klein_exact" else 250)
        if method in ("matched250", "matched_sampled"):
            return sampled_pr_radix_jit(y, s, width, budget or 250)
        raise ValueError(f"Unknown method {method}")
    with threadpool_limits(limits=1):
        rng = np.random.default_rng(613)
        y = np.zeros(257, np.int8); y[31:41] = 1; y[180:187] = 1
        s = np.round(rng.normal(size=257), 1)
        for method in METHODS:
            evaluate(method, y, s, 30, 250)
        conn.send({"status": "ready"})
        arrays = None
        while True:
            request = conn.recv()
            if request["op"] == "stop":
                return
            try:
                if request["op"] == "load":
                    arrays = load_case(request["row"], request["models"], root)
                    conn.send({"status": "ok"})
                    continue
                start = time.perf_counter()
                value = float(evaluate(request["method"], arrays["labels"], arrays[request["model"]],
                                       request["width"], request.get("thresholds")))
                seconds = time.perf_counter() - start
                if not math.isfinite(value):
                    raise ValueError("Nonfinite metric output")
                conn.send({"status": "ok", "value": value, "seconds": seconds})
            except Exception as exc:
                conn.send({"status": "error", "error_type": type(exc).__name__, "error": str(exc)})


class Worker:
    def __init__(self, root=ROOT):
        self.root, self.process, self.conn, self.loaded = root, None, None, None

    def close(self):
        if self.process:
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill(); self.process.join()
            self.conn.close()
        self.process = self.conn = self.loaded = None

    def start(self):
        self.close()
        ctx = mp.get_context("spawn")
        self.conn, child = ctx.Pipe()
        self.process = ctx.Process(target=_worker_main, args=(child, str(self.root)))
        self.process.start(); child.close()
        if not self.conn.poll(180) or self.conn.recv().get("status") != "ready":
            self.close(); raise RuntimeError("Isolated synthetic warmup failed")

    def call(self, row, models, request, timeout):
        if self.process is None:
            self.start()
        if self.loaded != row["series"]:
            self.conn.send({"op": "load", "row": row, "models": models})
            if not self.conn.poll(60):
                self.close(); raise RuntimeError("Input loading exceeded 60 seconds")
            loaded = self.conn.recv()
            if loaded["status"] != "ok":
                raise ValueError(loaded)
            self.loaded = row["series"]
        self.conn.send(dict(request, op="evaluate"))
        if not self.conn.poll(timeout):
            self.close()
            return {"status": "timeout", "timeout_seconds": timeout}
        try:
            return self.conn.recv()
        except EOFError:
            self.close()
            return {"status": "error", "error_type": "WorkerExit", "error": "worker exited without result"}


def freeze(protocol, rows):
    relative = ["artifacts/msad-sampling-20261023/protocol.json", protocol["acquisition_manifest"],
                protocol["acquisition_protocol"], "experiments/msad_sampling_study.py",
                "experiments/fast_vus_adapter.py", ".cache/fast_vus/fast_vus.py",
                "tests/test_msad_sampling_study.py", "artifacts/msad-corpus-20261023/independent-input-audit.json",
                "src/sparse_vus/core.py", "src/sparse_vus/radix.py", "src/sparse_vus/pr_compiled.py",
                "src/sparse_vus/compiled.py", "src/sparse_vus/saturation.py", "src/sparse_vus/sampling.py"]
    path = OUT / "source_manifest.json"
    if path.exists():
        manifest = json.loads(path.read_text()); verify_hashes(manifest["sha256"])
        return manifest
    manifest = {"created_utc": utc(), "before_corpus_metrics": True,
                "sha256": {p: sha256_file(ROOT / p) for p in relative},
                "numerical_series": [r["series"] for r in rows],
                "validation_timing_series": [r["series"] for r in timing_subset(rows)],
                "hardware": dict(platform.uname()._asdict()), "python": sys.version,
                "numpy": np.__version__}
    with path.open("x") as f:
        json.dump(manifest, f, indent=2, allow_nan=False); f.write("\n")
    return manifest


def run_phase(phase, protocol, rows, sources, max_series=None):
    record_path = OUT / "records.jsonl"
    index = read_records(record_path)
    source_hash = sha256_file(OUT / "source_manifest.json")
    for old in index.values():
        if old.get("source_manifest_sha256") != source_hash:
            raise ValueError("Record source manifest mismatch")
    subset = rows if phase == "numerical" else timing_subset(rows)
    if max_series is not None:
        subset = subset[:max_series]
    worker = Worker()
    start = time.perf_counter(); started = utc(); calls = 0
    try:
        for ri, row in enumerate(subset):
            verify_hashes(sources["sha256"])
            arrays = load_case(row, protocol["models"])
            for model in protocol["models"]:
                if phase == "numerical":
                    statkey = f"input|{row['series']}|{model}"
                    if statkey not in index:
                        unique, counts = np.unique(arrays[model], return_counts=True)
                        append_record(record_path, {"key": statkey, "phase": "input", "series": row["series"],
                            "family": row["family"], "model": model, "n": row["n"], "distinct_scores": len(unique),
                            "distinct_fraction": len(unique) / row["n"], "largest_tie": int(counts.max()),
                            "score_minimum": float(unique[0]), "score_maximum": float(unique[-1]),
                            "npz_sha256": row["npz_sha256"], "source_manifest_sha256": source_hash}, index)
                requests = []
                if phase == "numerical":
                    for width in protocol["widths"]:
                        requests.append((width, "radix_exact", None, None))
                        requests.extend((width, "matched_sampled", h, None) for h in protocol["threshold_budgets"])
                        requests.append((width, "klein250", 250, None))
                elif phase == "validation":
                    requests = [(30, "dense_exact", None, None), (30, "klein_exact", row["n"], None)]
                else:
                    for repetition in range(protocol["timing"]["repetitions"]):
                        seed = int.from_bytes(hashlib.sha256(f"20261023|{row['series']}|{model}|{repetition}".encode()).digest()[:8], "big")
                        order = np.random.default_rng(seed).permutation(METHODS)
                        requests.extend((30, str(method), 250 if method in ("klein250", "matched250") else None, repetition)
                                        for method in order)
                for order_index, (width, method, budget, repetition) in enumerate(requests):
                    key = json.dumps([phase, row["series"], model, width, method, budget, repetition], separators=(",", ":"))
                    if key in index:
                        continue
                    request = {"model": model, "width": width, "method": method, "thresholds": budget}
                    result = worker.call(row, protocol["models"], request, protocol["numerical_timeout_seconds_per_call"])
                    record = dict(result, key=key, phase=phase, series=row["series"], family=row["family"],
                                  n=row["n"], model=model, width=width, method=method, thresholds=budget,
                                  repetition=repetition, order_index=order_index, utc=utc(),
                                  npz_sha256=row["npz_sha256"], label_sha256=row["array_sha256"]["labels"],
                                  score_sha256=row["array_sha256"][model], source_manifest_sha256=source_hash)
                    append_record(record_path, record, index); calls += 1
            print(json.dumps({"phase": phase, "series_done": ri + 1, "series_total": len(subset),
                              "new_calls": calls, "elapsed_seconds": time.perf_counter() - start}), flush=True)
    finally:
        worker.close()
        append_record(record_path, {"key": "collection|" + str(uuid.uuid4()), "phase": "collection",
                      "collection_phase": phase, "started_utc": started, "ended_utc": utc(),
                      "new_metric_calls": calls, "wall_seconds": time.perf_counter() - start,
                      "scope": "includes source hash checks, decode, warmup, evaluation, IPC and append/fsync",
                      "source_manifest_sha256": source_hash}, index)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["freeze", "numerical", "validate", "timing", "report"])
    parser.add_argument("--max-series", type=int)
    parser.add_argument("--idle-host-confirmed", action="store_true")
    args = parser.parse_args()
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    protocol = json.loads((OUT / "protocol.json").read_text())
    if sha256_file(ROOT / protocol["acquisition_protocol"]) != protocol["acquisition_protocol_sha256"]:
        raise ValueError("Acquisition protocol hash mismatch")
    manifest = json.loads((ROOT / protocol["acquisition_manifest"]).read_text())
    rows = manifest["series"]
    if len(rows) != protocol["expected_series"] or manifest["models"] != protocol["models"]:
        raise ValueError("Frozen series/model coverage mismatch")
    sources = freeze(protocol, rows)
    if args.command == "freeze":
        print(json.dumps({"source_manifest_sha256": sha256_file(OUT / "source_manifest.json"),
                          "series": len(rows), "validation_timing_series": len(timing_subset(rows))})); return
    if args.command in ("numerical", "validate", "timing"):
        if args.command == "timing" and not args.idle_host_confirmed:
            raise ValueError("Timing requires --idle-host-confirmed after coordination")
        run_phase("validation" if args.command == "validate" else args.command,
                  protocol, rows, sources, args.max_series)
    records = read_records(OUT / "records.jsonl")
    report = build_report(records.values(), rows, protocol)
    report.update(protocol_sha256=sha256_file(OUT / "protocol.json"),
                  source_manifest_sha256=sha256_file(OUT / "source_manifest.json"),
                  records_sha256=sha256_file(OUT / "records.jsonl"))
    # Reports are immutable snapshots named by the log they reconstruct.
    path = OUT / ("report-" + report["records_sha256"][:16] + ".json")
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if path.exists():
        if path.read_text() != payload:
            raise ValueError("Nondeterministic report reconstruction")
    else:
        with path.open("x") as f:
            f.write(payload)
    print(json.dumps({"report": str(path.relative_to(ROOT)), "primary": report["primary"]["pooled"],
                      "gate": report["primary"]["promotion_gate_passed"], "maximum_parity_error": report["maximum_parity_error"]}))


if __name__ == "__main__":
    main()
