"""Frozen, serial stored-score collection workflow; freeze never evaluates VUS.

The run command requires a reviewed protocol digest and explicit CPU clearance.
Raw arrays remain in ignored .cache; public receipts contain metrics and hashes.
"""
from __future__ import annotations

import os
for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_key] = "1"

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("radix_pr", "dense_pr_nearest_radix", "klein_pr")
OLD_INPUTS = "artifacts/pr-engine/mac-holdout/inputs.json"
OLD_INPUTS_SHA = "783d6ec769682c8b0735fe4f4a17591ab4de042b2f2907e8ffbecbcc74690cd6"
OLD_PROTOCOL = "artifacts/pr-engine/mac-holdout/protocol.json"
OLD_PROTOCOL_SHA = "5417a38ec43cc4471e17a0ca7d6af0b11ef448689042a1c5dec4fa8ef2dffb07"
SOURCES = (
    "experiments/benchmark_vus_collection.py",
    "experiments/advancement_data_gate.py", "experiments/fast_vus_adapter.py",
    "src/sparse_vus/__init__.py", "src/sparse_vus/core.py",
    "src/sparse_vus/compiled.py", "src/sparse_vus/pr_compiled.py",
    "src/sparse_vus/radix.py", "src/sparse_vus/dense_radix.py",
    ".cache/fast_vus/fast_vus.py", ".cache/fast_vus/LICENSE",
    "docs/vus_collection_protocol_20261023.md",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1 << 20):
            value.update(block)
    return value.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def verify_files(root, bindings):
    for name, expected in bindings.items():
        require(digest(Path(root) / name) == expected, f"SHA-256 mismatch: {name}")


def array_identity(array):
    """Bind shape/dtype and exact C-order bits, including signed zeros."""
    return {"dtype": array.dtype.str, "shape": list(array.shape),
            "sha256": hashlib.sha256(array.tobytes(order="C")).hexdigest()}


def cache_location(root, path):
    """Keep the ignored logical path while supporting the worktree cache symlink."""
    base, cache = (Path(root) / ".cache").resolve(), Path(path).resolve()
    require(cache.is_relative_to(base), "Raw inputs must remain under ignored .cache")
    return cache, str(Path(".cache") / cache.relative_to(base))


def released_inputs(root):
    sys.path.insert(0, str(root / "experiments"))
    from advancement_data_gate import released_metadata
    verify_files(root, {OLD_INPUTS: OLD_INPUTS_SHA, OLD_PROTOCOL: OLD_PROTOCOL_SHA})
    metadata, models, scores, development, locks, original = released_metadata(root)
    selected = sorted(set(metadata) - set(development))
    require(len(selected) == 308 and len(models) == 3, "Unexpected collection coverage")
    expected = [{"series": s, "family": metadata[s]["family"], "n": metadata[s]["n"],
                 "max_buffer": 30, "label_sha256": metadata[s]["label_sha256"],
                 "score_sha256": {m: scores[s, m] for m in models}} for s in selected]
    actual = [row for row in read_json(root / OLD_INPUTS) if row["max_buffer"] == 30]
    require(actual == expected, "Original held-out source identities differ")
    # The comparison is explicitly the released engines, not new October 23 code.
    old_sources = read_json(root / OLD_PROTOCOL)["source_sha256"]
    verify_files(root, {name: old_sources[name] for name in SOURCES if name in old_sources})
    return expected, models, metadata, locks, original


def freeze(output, cache, *, root=ROOT):
    """Verify source archive/member identity and materialize NPZ; no metric calls."""
    import numpy as np
    import pandas as pd
    root, output = Path(root).resolve(), Path(output).resolve()
    cache, cache_relative = cache_location(root, cache)
    require(not output.exists() and not cache.exists(), "Freeze destinations already exist")
    inputs, models, metadata, locks, original = released_inputs(root)
    sources = {name: digest(root / name) for name in SOURCES}
    verify_files(root / "cache", locks["files"])
    archives = ["TSB-AD-U.zip", *(f"{m}.score-range.zip" for m in models)]
    archive_hashes = {name: digest(root / "cache" / name) for name in archives}
    output.mkdir(parents=True, exist_ok=False)
    cache.mkdir(parents=True, exist_ok=False)
    entries, total_bytes = [], 0
    with ExitStack() as stack:
        labels_zip = stack.enter_context(zipfile.ZipFile(root / "cache/TSB-AD-U.zip"))
        label_members = [p for p in labels_zip.namelist() if p.endswith(".csv")]
        names = {Path(p).stem: p for p in label_members}
        require(len(names) == len(label_members), "Ambiguous label archive members")
        score_zips = {m: stack.enter_context(zipfile.ZipFile(root / "cache" / f"{m}.score-range.zip"))
                      for m in models}
        for m, archive in score_zips.items():
            require(len(archive.namelist()) == len(set(archive.namelist())),
                    f"Duplicate score archive member: {m}")
        for index, row in enumerate(inputs):
            raw = labels_zip.read(names[row["series"]])
            require(hashlib.sha256(raw).hexdigest() == row["label_sha256"], "Label member changed")
            decoded = pd.read_csv(io.BytesIO(raw), usecols=["Label"])["Label"].to_numpy()
            require(decoded.ndim == 1 and len(decoded) == row["n"]
                    and np.isin(decoded, [0, 1]).all()
                    and int(decoded.sum()) == metadata[row["series"]]["positive_points"]
                    and 0 < decoded.sum() < len(decoded), "Label metadata mismatch")
            # Match Corpus.load's pre-existing binary label representation exactly.
            labels = decoded.astype(np.int8)
            require(np.array_equal(labels, decoded), "Label conversion changed values")
            arrays = {"labels": labels}
            for i, model in enumerate(models):
                raw_score = score_zips[model].read(f"scores/{row['series']}.npy")
                require(hashlib.sha256(raw_score).hexdigest() == row["score_sha256"][model],
                        f"Score member changed: {row['series']}, {model}")
                score = np.load(io.BytesIO(raw_score), allow_pickle=False)
                require(score.ndim == 1 and len(score) == row["n"]
                        and score.dtype.kind in "fiu" and np.isfinite(score).all(), "Invalid score vector")
                arrays[f"score_{i}"] = score
            name = f"{index:04d}.npz"
            with (cache / name).open("xb") as stream:
                np.savez(stream, **arrays)  # stored ZIP entries, no compression
            identities = {key: array_identity(a) for key, a in arrays.items()}
            with np.load(cache / name, allow_pickle=False) as stored:
                require(set(stored.files) == set(arrays), "NPZ keys differ")
                require({key: array_identity(stored[key]) for key in stored.files} == identities,
                        "NPZ round-trip changed array bits")
            size = (cache / name).stat().st_size
            total_bytes += size
            entries.append({**row, "file": name, "bytes": size, "npz_sha256": digest(cache / name),
                            "arrays": identities, "decoded_label_array": array_identity(decoded),
                            "label_member": names[row["series"]]})
    verify_files(root, sources)
    write_json(output / "inputs.json", entries)
    rng = random.Random(2026102307)
    orders = []
    for _ in range(3):
        order = list(METHODS)
        rng.shuffle(order)
        orders.append(order)
    protocol = {
        "version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FROZEN_BEFORE_COLLECTION_TIMING", "series": 308, "models": models,
        "families": sorted({row["family"] for row in entries}), "max_buffer": 30,
        "methods": list(METHODS), "repetitions": 3, "seed": 2026102307, "orders": orders,
        "tie_atol": 1e-10, "parity_atol": 1e-11, "cache_relative": cache_relative,
        "cache_bytes": total_bytes, "inputs_sha256": digest(output / "inputs.json"),
        "source_sha256": sources, "original_inputs_sha256": OLD_INPUTS_SHA,
        "original_protocol_sha256": OLD_PROTOCOL_SHA,
        "original_benchmark_sha256": original["records_sha256"],
        "source_archive_sha256": archive_hashes, "source_file_locks": locks["files"],
        "array_preparation": "Original score NPY arrays preserved bit-for-bit without scaling, reordering, or new padding; binary CSV labels cast to int8 exactly as existing Corpus.load. Decoded and stored label identities are both recorded.",
        "selection": "All 308 previously studied holdout series and all 3 original released score vectors; sorted series and model order; no duplication, sampling, or extrapolated collection size.",
        "metric": "Full public PR-only calls including validation and preparation, exhaustive widths 0..30; Klein max_samples=n. No tie-run aggregation or active-prefix candidate.",
        "timing": "One serial process, one numerical thread. Each whole pass starts before its first NPZ open and ends after the result JSON has been serialized, written and closed. 308 file loads, 924 full metric calls, 308 selections, one JSON write. Stage clocks are diagnostic; the decision uses the measured whole clock, never their sum or old case medians.",
        "startup": "Imports, tiny synthetic dtype-matched JIT warmups, provenance checks and explicit filesystem warming are outside timing. Before each pass read and SHA-256-check all NPZ bytes, then reopen and materialize every array inside the timed workflow. Warm OS filesystem/page cache, no cache eviction or cold-disk claim; JSON close without fsync.",
        "decision": "All 9 passes select identical best-model sets per series and maximum pairwise PR difference across methods/repetitions is <=1e-11; median whole-collection radix runtime is strictly smaller than both control medians. Report all 3 times per method; no CI or significance claim.",
        "scope": "Local stored-score model selection, from disk input to JSON decisions. Excludes detector training/inference, source download, network, first-use compilation and cold-cache storage. Same previously studied 17-family corpus; not new-domain confirmation or an operational adoption study.",
    }
    write_json(output / "protocol.json", protocol)
    write_json(output / "freeze_receipt.json", {
        "status": "FROZEN_NO_COLLECTION_TIMING", "protocol_sha256": digest(output / "protocol.json"),
        "inputs_sha256": protocol["inputs_sha256"], "driver_sha256": sources[SOURCES[0]],
        "verified_label_members": 308, "verified_score_members": 924,
        "npz_files": 308, "npz_bytes": total_bytes,
    })
    return read_json(output / "freeze_receipt.json")


def validate_frozen(output, expected_hash, *, root=ROOT, verify_cache=True):
    root, output = Path(root).resolve(), Path(output)
    require(digest(output / "protocol.json") == expected_hash, "Frozen protocol SHA-256 differs")
    p = read_json(output / "protocol.json")
    require(p["version"] == 1 and p["methods"] == list(METHODS) and p["series"] == 308
            and p["repetitions"] == 3 and p["max_buffer"] == 30, "Unexpected protocol contract")
    require(set(p["source_sha256"]) == set(SOURCES), "Incomplete source bindings")
    verify_files(root, p["source_sha256"])
    require(digest(output / "inputs.json") == p["inputs_sha256"], "Input manifest SHA-256 differs")
    entries = read_json(output / "inputs.json")
    expected, models, _, _, _ = released_inputs(root)
    require([{k: row[k] for k in expected[0]} for row in entries] == expected
            and p["models"] == models, "Collection differs from original held-out identities")
    require(p["families"] == sorted({r["family"] for r in entries}), "Family coverage differs")
    require([r["file"] for r in entries] == [f"{i:04d}.npz" for i in range(308)], "NPZ file coverage differs")
    require(p["tie_atol"] == 1e-10 and p["parity_atol"] == 1e-11, "Tolerance contract differs")
    rng, orders = random.Random(p["seed"]), []
    for _ in range(p["repetitions"]):
        order = list(METHODS)
        rng.shuffle(order)
        orders.append(order)
    require(orders == p["orders"], "Frozen method order differs from seed")
    cache, relative = cache_location(root, root / p["cache_relative"])
    require(relative == p["cache_relative"], "Noncanonical raw cache path")
    if verify_cache:
        verify_files(cache, {r["file"]: r["npz_sha256"] for r in entries})
    return p, entries, cache


def select_best(values, tolerance):
    require(values and all(math.isfinite(v) and 0 <= v <= 1 + 1e-11 for v in values.values()),
            "Invalid PR metric value")
    best = max(values.values())
    return sorted(model for model, value in values.items() if best - value <= tolerance)


def run_workflow(cache, entries, models, evaluator, output, *, method, trial, width, tie_atol):
    """The operator workflow. No model values or inputs survive into another pass."""
    import numpy as np
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    phase = {"read": 0, "metric": 0, "selection": 0, "serialization_and_write": 0}
    counts = {"file_reads": 0, "arrays_read": 0, "metric_calls": 0,
              "selections": 0, "serializations": 0, "file_writes": 0}
    start = time.perf_counter_ns()
    rows = []
    for entry in entries:
        begin = time.perf_counter_ns()
        with np.load(Path(cache) / entry["file"], allow_pickle=False) as stored:
            labels = stored["labels"]
            scores = [stored[f"score_{i}"] for i in range(len(models))]
        phase["read"] += time.perf_counter_ns() - begin
        counts["file_reads"] += 1
        counts["arrays_read"] += 1 + len(models)
        begin = time.perf_counter_ns()
        values = {m: float(evaluator(labels, score, width)) for m, score in zip(models, scores)}
        phase["metric"] += time.perf_counter_ns() - begin
        counts["metric_calls"] += len(models)
        begin = time.perf_counter_ns()
        selected = select_best(values, tie_atol)
        rows.append({"series": entry["series"], "pr": values, "selected": selected})
        phase["selection"] += time.perf_counter_ns() - begin
        counts["selections"] += 1
        del labels, scores
    begin = time.perf_counter_ns()
    with output.open("x") as stream:
        json.dump({"method": method, "trial": trial, "max_buffer": width, "rows": rows},
                  stream, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
    phase["serialization_and_write"] += time.perf_counter_ns() - begin
    whole = time.perf_counter_ns() - start
    counts["serializations"] = counts["file_writes"] = 1
    return {"method": method, "trial": trial, "whole_ns": whole, "phase_ns": phase,
            "unattributed_ns": whole - sum(phase.values()), "counts": counts,
            "output_file": output.name, "output_sha256": digest(output),
            "output_bytes": output.stat().st_size}


def make_methods(root=ROOT):
    sys.path.insert(0, str(Path(root) / "src"))
    sys.path.insert(0, str(Path(root) / "experiments"))
    from sparse_vus.radix import sparse_pr_radix_jit
    from sparse_vus.dense_radix import dense_pr_nearest_radix_jit
    from fast_vus_adapter import fast_vus_pr
    return {"radix_pr": sparse_pr_radix_jit, "dense_pr_nearest_radix": dense_pr_nearest_radix_jit,
            "klein_pr": lambda y, s, w: fast_vus_pr(y, s, w, max_samples=len(s))}


def execute(output, expected_hash, cpu_clearance, *, root=ROOT):
    require(cpu_clearance.strip(), "Explicit CPU-clearance statement required")
    output = Path(output)
    p, entries, cache = validate_frozen(output, expected_hash, root=root)
    require(not (output / "run").exists(), "Run already exists; no overwrite or resume")
    run = output / "run"
    run.mkdir(exist_ok=False)
    import numpy as np
    import numba
    from threadpoolctl import threadpool_limits, threadpool_info
    numba.set_num_threads(1)
    methods = make_methods(root)
    warmups = []
    with threadpool_limits(limits=1):
        # Cover every stored signature without evaluating any collection input.
        signatures = sorted({(r["arrays"]["labels"]["dtype"], r["arrays"][f"score_{i}"]["dtype"])
                             for r in entries for i in range(3)})
        for label_dtype, score_dtype in signatures:
            labels = np.zeros(32, dtype=label_dtype)
            labels[[4, 5, 13, 25]] = 1
            scores = np.repeat(np.arange(8, dtype=score_dtype), 4)
            for name, fn in methods.items():
                begin = time.perf_counter_ns()
                value = float(fn(labels, scores, 30))
                require(math.isfinite(value), "Nonfinite synthetic warmup")
                warmups.append({"method": name, "label_dtype": label_dtype, "score_dtype": score_dtype,
                                "seconds": (time.perf_counter_ns() - begin) / 1e9})
        pools = threadpool_info()
        require(numba.get_num_threads() == 1 and all(pool["num_threads"] == 1 for pool in pools),
                "Numerical worker count is not one")
        verify_files(root, p["source_sha256"])
        cpu = platform.processor()
        if sys.platform == "darwin":
            cpu = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
        write_json(run / "environment.json", {
            "started_utc": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
            "machine": platform.machine(), "cpu": cpu, "python": sys.version,
            "numpy": np.__version__, "numba": numba.__version__, "threads": numba.get_num_threads(),
            "threadpools": pools, "warmup": warmups, "cpu_clearance": cpu_clearance,
            "protocol_sha256": expected_hash, "inputs_sha256": p["inputs_sha256"],
            "source_sha256": p["source_sha256"], "filesystem": "Explicitly warmed before every measured pass",
        })
        outputs = {}
        with (run / "measurements.jsonl").open("x") as stream:
            for trial, order in enumerate(p["orders"]):
                for position, name in enumerate(order):
                    # Integrity verification also establishes the stated warm-cache condition.
                    verify_files(cache, {r["file"]: r["npz_sha256"] for r in entries})
                    result = run_workflow(cache, entries, p["models"], methods[name],
                                          run / f"trial-{trial}-{name}.json", method=name,
                                          trial=trial, width=p["max_buffer"], tie_atol=p["tie_atol"])
                    result["position"] = position
                    result["protocol_sha256"] = expected_hash
                    stream.write(json.dumps(result, allow_nan=False) + "\n")
                    stream.flush()
                    outputs[result["output_file"]] = result["output_sha256"]
                    print(json.dumps({"trial": trial, "method": name,
                                      "whole_seconds": result["whole_ns"] / 1e9}), flush=True)
        verify_files(root, p["source_sha256"])
        verify_files(cache, {r["file"]: r["npz_sha256"] for r in entries})
        write_json(run / "completion.json", {
            "status": "COMPLETE", "passes": 9, "protocol_sha256": expected_hash,
            "inputs_sha256": p["inputs_sha256"],
            "measurements_sha256": digest(run / "measurements.jsonl"),
            "environment_sha256": digest(run / "environment.json"), "outputs_sha256": outputs,
        })


def decision(times, max_difference, sets_agree, parity_atol):
    medians = {method: statistics.median(values) for method, values in times.items()}
    wins = {control: medians["radix_pr"] < medians[control] for control in METHODS[1:]}
    passed = sets_agree and max_difference <= parity_atol and all(wins.values())
    return {"status": "PASS" if passed else "FAIL", "median_seconds": medians,
            "whole_seconds": times, "radix_faster_than_control": wins,
            "median_speedup_over_radix": {m: medians[m] / medians["radix_pr"] for m in METHODS[1:]},
            "max_pairwise_pr_difference": max_difference, "all_selected_sets_agree": sets_agree,
            "parity_atol": parity_atol, "uncertainty": "Three observations per method; no CI or significance claim"}


def report(output, expected_hash, *, root=ROOT):
    """Reconstruct every numeric difference and decision from hash-bound outputs."""
    output = Path(output)
    p, entries, _ = validate_frozen(output, expected_hash, root=root)
    run = output / "run"
    done, env = read_json(run / "completion.json"), read_json(run / "environment.json")
    require(done["status"] == "COMPLETE" and done["passes"] == 9
            and done["protocol_sha256"] == env["protocol_sha256"] == expected_hash
            and done["inputs_sha256"] == env["inputs_sha256"] == p["inputs_sha256"]
            and env["source_sha256"] == p["source_sha256"] and env["threads"] == 1,
            "Completion/environment bindings differ")
    verify_files(run, {"measurements.jsonl": done["measurements_sha256"],
                       "environment.json": done["environment_sha256"], **done["outputs_sha256"]})
    rows = [json.loads(line) for line in (run / "measurements.jsonl").read_text().splitlines()]
    expected_order = [(trial, pos, method) for trial, order in enumerate(p["orders"])
                      for pos, method in enumerate(order)]
    require([(r["trial"], r["position"], r["method"]) for r in rows] == expected_order,
            "Incomplete, duplicated or reordered collection passes")
    series_count, model_count = len(entries), len(p["models"])
    wanted_counts = {"file_reads": series_count, "arrays_read": series_count * (model_count + 1),
                     "metric_calls": series_count * model_count,
                     "selections": series_count, "serializations": 1, "file_writes": 1}
    outputs, times = {}, {m: [] for m in METHODS}
    for row in rows:
        require(row["protocol_sha256"] == expected_hash and row["counts"] == wanted_counts,
                "Pass protocol/count differs")
        require(set(row["phase_ns"]) == {"read", "metric", "selection", "serialization_and_write"}
                and all(type(v) is int and v >= 0 for v in row["phase_ns"].values())
                and type(row["whole_ns"]) is int and row["whole_ns"] > 0
                and row["unattributed_ns"] == row["whole_ns"] - sum(row["phase_ns"].values()) >= 0,
                "Invalid or inconsistent clocks")
        filename = f"trial-{row['trial']}-{row['method']}.json"
        require(row["output_file"] == filename and row["output_sha256"] == done["outputs_sha256"][filename]
                and row["output_bytes"] == (run / filename).stat().st_size, "Output binding differs")
        result = read_json(run / filename)
        require(result["method"] == row["method"] and result["trial"] == row["trial"]
                and result["max_buffer"] == 30
                and [r["series"] for r in result["rows"]] == [r["series"] for r in entries],
                "Output coverage/identity differs")
        for item in result["rows"]:
            require(set(item["pr"]) == set(p["models"])
                    and item["selected"] == select_best(item["pr"], p["tie_atol"]),
                    "Stored selection disagrees with stored PR values")
        outputs[row["trial"], row["method"]] = result["rows"]
        times[row["method"]].append(row["whole_ns"] / 1e9)
    require(set(done["outputs_sha256"]) == {r["output_file"] for r in rows}, "Extra/missing output receipt")
    reference = outputs[0, "radix_pr"]
    differences, maximum, agree = [], 0.0, True
    for index, entry in enumerate(entries):
        values = [result[index] for result in outputs.values()]
        spans = {m: max(v["pr"][m] for v in values) - min(v["pr"][m] for v in values)
                 for m in p["models"]}
        maximum = max(maximum, *spans.values())
        selected_agree = all(v["selected"] == reference[index]["selected"] for v in values)
        agree = agree and selected_agree
        differences.append({"series": entry["series"], "pairwise_max_minus_min": spans,
                            "all_selected_sets_agree": selected_agree,
                            "reference_selected": reference[index]["selected"],
                            "passes": [{"trial": trial, "method": method,
                                        "pr_minus_reference": {m: result[index]["pr"][m] - reference[index]["pr"][m]
                                                               for m in p["models"]},
                                        "selected_agrees": result[index]["selected"] == reference[index]["selected"]}
                                       for (trial, method), result in outputs.items()]})
    return {**decision(times, maximum, agree, p["parity_atol"]),
            "protocol_sha256": expected_hash, "inputs_sha256": p["inputs_sha256"],
            "completion_sha256": digest(run / "completion.json"), "series": series_count,
            "families": len(p["families"]), "passes": rows, "differences": differences,
            "scope": p["scope"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    frozen = sub.add_parser("freeze")
    frozen.add_argument("output", type=Path)
    frozen.add_argument("--cache", required=True, type=Path)
    run = sub.add_parser("run")
    run.add_argument("output", type=Path)
    run.add_argument("--protocol-sha256", required=True)
    run.add_argument("--cpu-clearance", required=True)
    audit = sub.add_parser("report")
    audit.add_argument("output", type=Path)
    audit.add_argument("--protocol-sha256", required=True)
    audit.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "freeze":
        print(json.dumps(freeze(args.output, args.cache), indent=2))
    elif args.command == "run":
        execute(args.output, args.protocol_sha256, args.cpu_clearance)
    else:
        require(not args.report.exists(), "Report output already exists")
        result = report(args.output, args.protocol_sha256)
        write_json(args.report, result)
        print(json.dumps({k: v for k, v in result.items() if k not in ("passes", "differences")}, indent=2))


if __name__ == "__main__":
    main()
