"""Independent standard-library audit of public stored-score workflow receipts.

No metric implementation, NumPy, NPZ, source ZIP, or external source cache is
loaded. Reconstructs decisions from public scalar outputs, with an explicit
boundary between checked repository sources and unavailable external bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("radix_pr", "dense_pr_nearest_radix", "klein_pr")
REPOSITORY_SOURCES = (
    "experiments/benchmark_vus_collection.py", "experiments/advancement_data_gate.py",
    "experiments/fast_vus_adapter.py", "src/sparse_vus/__init__.py",
    "src/sparse_vus/core.py", "src/sparse_vus/compiled.py", "src/sparse_vus/pr_compiled.py",
    "src/sparse_vus/radix.py", "src/sparse_vus/dense_radix.py",
    "docs/vus_collection_protocol_20261023.md",
)
EXTERNAL_SOURCES = (".cache/fast_vus/fast_vus.py", ".cache/fast_vus/LICENSE")
OLD_INPUTS = "artifacts/pr-engine/mac-holdout/inputs.json"
OLD_INPUTS_SHA = "783d6ec769682c8b0735fe4f4a17591ab4de042b2f2907e8ffbecbcc74690cd6"
OLD_PROTOCOL = "artifacts/pr-engine/mac-holdout/protocol.json"
OLD_PROTOCOL_SHA = "5417a38ec43cc4471e17a0ca7d6af0b11ef448689042a1c5dec4fa8ef2dffb07"
PHASES = {"read", "metric", "selection", "serialization_and_write"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1 << 20):
            value.update(chunk)
    return value.hexdigest()


def hash_string(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def checked_hash(path, expected):
    require(hash_string(expected) and digest(path) == expected, f"SHA-256 mismatch: {path}")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _bad_constant(value):
    raise ValueError(f"Nonfinite JSON constant: {value}")


def parse_json(text):
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_bad_constant)


def read_json(path):
    return parse_json(Path(path).read_text())


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def finite(value, minimum=0):
    return type(value) in (int, float) and math.isfinite(value) and value >= minimum


def load_release_population(root, protocol):
    """Immutable metadata only; the imported helper's top level uses stdlib."""
    checked_hash(root / OLD_INPUTS, OLD_INPUTS_SHA)
    checked_hash(root / OLD_PROTOCOL, OLD_PROTOCOL_SHA)
    old = read_json(root / OLD_PROTOCOL)
    gate = "experiments/advancement_data_gate.py"
    checked_hash(root / gate, old["source_sha256"][gate])
    spec = importlib.util.spec_from_file_location("collection_release_metadata_audit", root / gate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metadata, models, score_hashes, development, locks, original = module.released_metadata(root)
    selected = sorted(set(metadata) - set(development))
    expected = [{"series": series, "family": metadata[series]["family"],
                 "n": metadata[series]["n"], "max_buffer": 30,
                 "label_sha256": metadata[series]["label_sha256"],
                 "score_sha256": {m: score_hashes[series, m] for m in models}}
                for series in selected]
    require(expected == [r for r in read_json(root / OLD_INPUTS) if r["max_buffer"] == 30],
            "Prior holdout manifest differs from immutable released metadata")
    return expected, models, locks, original["records_sha256"], old["source_sha256"]


def validate_public_freeze(study, expected_hash, root):
    checked_hash(study / "protocol.json", expected_hash)
    p, freeze = read_json(study / "protocol.json"), read_json(study / "freeze_receipt.json")
    require(p["version"] == 1 and p["status"] == "FROZEN_BEFORE_COLLECTION_TIMING"
            and p["series"] == 308 and p["repetitions"] == 3 and p["max_buffer"] == 30
            and p["methods"] == list(METHODS), "Unsupported frozen collection contract")
    require(p["tie_atol"] == 1e-10 and p["parity_atol"] == 1e-11
            and integer(p["seed"]), "Frozen tolerance or seed differs")
    require(set(p["source_sha256"]) == set(REPOSITORY_SOURCES) | set(EXTERNAL_SOURCES)
            and all(hash_string(v) for v in p["source_sha256"].values()),
            "Incomplete or unexpected source-manifest membership")
    for name in REPOSITORY_SOURCES:
        checked_hash(root / name, p["source_sha256"][name])
    checked_hash(study / "inputs.json", p["inputs_sha256"])
    entries = read_json(study / "inputs.json")
    expected, models, locks, original_hash, old_sources = load_release_population(root, p)
    require(len(entries) == len(expected) == 308 and len(models) == 3 and p["models"] == models,
            "Original series/model coverage differs")
    require([{key: row[key] for key in expected[0]} for row in entries] == expected,
            "Input identities differ from original source manifest")
    require(p["families"] == sorted({r["family"] for r in entries}) and len(p["families"]) == 17,
            "Original family coverage differs")
    require(p["original_inputs_sha256"] == OLD_INPUTS_SHA
            and p["original_protocol_sha256"] == OLD_PROTOCOL_SHA
            and p["original_benchmark_sha256"] == original_hash
            and p["source_file_locks"] == locks["files"], "Immutable provenance chain differs")
    for name, sha in p["source_sha256"].items():
        if name in old_sources:
            require(sha == old_sources[name], f"Released implementation identity differs: {name}")
    require(set(p["source_archive_sha256"]) == {"TSB-AD-U.zip", *(f"{m}.score-range.zip" for m in models)}
            and all(hash_string(v) for v in p["source_archive_sha256"].values())
            and p["source_archive_sha256"]["TSB-AD-U.zip"] == locks["files"]["TSB-AD-U.zip"],
            "Source archive descriptors differ")
    signatures = set()
    for i, row in enumerate(entries):
        require(row["file"] == f"{i:04d}.npz" and integer(row["bytes"], 1)
                and hash_string(row["npz_sha256"]), "Invalid NPZ descriptor")
        require(set(row["arrays"]) == {"labels", "score_0", "score_1", "score_2"}, "Invalid NPZ array membership")
        for descriptor in [*row["arrays"].values(), row["decoded_label_array"]]:
            require(descriptor["shape"] == [row["n"]] and hash_string(descriptor["sha256"])
                    and isinstance(descriptor["dtype"], str)
                    and re.fullmatch(r"[<>=|][biuf][0-9]+", descriptor["dtype"]), "Invalid array descriptor")
        require(row["arrays"]["labels"]["dtype"] == "|i1", "Stored labels do not match Corpus int8 convention")
        for j in range(3):
            signatures.add((row["arrays"]["labels"]["dtype"], row["arrays"][f"score_{j}"]["dtype"]))
    require(integer(p["cache_bytes"], 1) and p["cache_bytes"] == sum(r["bytes"] for r in entries),
            "Frozen NPZ byte total differs")
    relative = Path(p["cache_relative"])
    require(not relative.is_absolute() and relative.parts[0] == ".cache" and ".." not in relative.parts,
            "Cache descriptor escapes ignored path")
    require(freeze == {"status": "FROZEN_NO_COLLECTION_TIMING", "protocol_sha256": expected_hash,
                       "inputs_sha256": p["inputs_sha256"],
                       "driver_sha256": p["source_sha256"]["experiments/benchmark_vus_collection.py"],
                       "verified_label_members": 308, "verified_score_members": 924,
                       "npz_files": 308, "npz_bytes": p["cache_bytes"]}, "Freeze receipt differs")
    rng, orders = random.Random(p["seed"]), []
    for _ in range(3):
        order = list(METHODS)
        rng.shuffle(order)
        orders.append(order)
    require(p["orders"] == orders, "Method order does not match frozen seed")
    return p, entries, signatures


def best_models(values, models, tolerance):
    require(set(values) == set(models)
            and all(finite(value) and value <= 1 + 1e-11 for value in values.values()),
            "Invalid PR output values")
    maximum = max(values.values())
    return sorted(model for model, value in values.items() if maximum - value <= tolerance)


def audit(output, expected_protocol_sha256, root=ROOT):
    root, study = Path(root), Path(output)
    expected_hash = expected_protocol_sha256
    p, entries, signatures = validate_public_freeze(study, expected_hash, root)
    run = study / "run"
    done = read_json(run / "completion.json")
    require(done["status"] == "COMPLETE" and done["passes"] == 9
            and done["protocol_sha256"] == expected_hash and done["inputs_sha256"] == p["inputs_sha256"],
            "Completion receipt differs")
    checked_hash(run / "measurements.jsonl", done["measurements_sha256"])
    checked_hash(run / "environment.json", done["environment_sha256"])
    env = read_json(run / "environment.json")
    require(env["protocol_sha256"] == expected_hash and env["inputs_sha256"] == p["inputs_sha256"]
            and env["source_sha256"] == p["source_sha256"] and type(env["threads"]) is int
            and env["threads"] == 1 and all(type(pool["num_threads"]) is int and pool["num_threads"] == 1
                                          for pool in env["threadpools"])
            and isinstance(env["cpu_clearance"], str) and env["cpu_clearance"].strip(),
            "Environment provenance or thread count differs")
    warmups = [(r["method"], r["label_dtype"], r["score_dtype"]) for r in env["warmup"]]
    require(len(warmups) == len(set(warmups)) and set(warmups) == {
        (method, label, score) for method in METHODS for label, score in signatures}
            and all(finite(r["seconds"]) for r in env["warmup"]), "Warmup signature coverage differs")
    rows = [parse_json(line) for line in (run / "measurements.jsonl").read_text().splitlines()]
    order = [(trial, position, method) for trial, methods in enumerate(p["orders"])
             for position, method in enumerate(methods)]
    require([(r["trial"], r["position"], r["method"]) for r in rows] == order
            and all(integer(r["trial"]) and integer(r["position"]) for r in rows),
            "Missing, duplicated or reordered pass")
    names = {f"trial-{trial}-{method}.json" for trial, _, method in order}
    require(set(done["outputs_sha256"]) == names, "Output manifest membership differs")
    counts = {"file_reads": 308, "arrays_read": 1232, "metric_calls": 924,
              "selections": 308, "serializations": 1, "file_writes": 1}
    outputs, seconds = {}, {m: [] for m in METHODS}
    for row in rows:
        require(row["protocol_sha256"] == expected_hash and row["counts"] == counts
                and all(integer(v) for v in row["counts"].values()), "Recorded operation counts differ")
        require(set(row["phase_ns"]) == PHASES and all(integer(v) for v in row["phase_ns"].values())
                and integer(row["whole_ns"], 1) and integer(row["unattributed_ns"])
                and row["whole_ns"] == sum(row["phase_ns"].values()) + row["unattributed_ns"],
                "Inconsistent stage or whole clock")
        name = f"trial-{row['trial']}-{row['method']}.json"
        require(row["output_file"] == name and row["output_sha256"] == done["outputs_sha256"][name]
                and integer(row["output_bytes"], 1) and row["output_bytes"] == (run / name).stat().st_size,
                "Output identity/size differs")
        checked_hash(run / name, row["output_sha256"])
        result = read_json(run / name)
        require(result["method"] == row["method"] and result["trial"] == row["trial"]
                and type(result["trial"]) is int and result["max_buffer"] == 30
                and [r["series"] for r in result["rows"]] == [r["series"] for r in entries],
                "Output series, method, trial or width differs")
        for result_row in result["rows"]:
            require(result_row["selected"] == best_models(result_row["pr"], p["models"], p["tie_atol"]),
                    "Recorded winner set disagrees with metric values")
        outputs[row["trial"], row["method"]] = result["rows"]
        seconds[row["method"]].append(row["whole_ns"] / 1e9)
    baseline = outputs[0, "radix_pr"]
    comparisons, largest, all_sets = [], 0.0, True
    for index, entry in enumerate(entries):
        results = [output[index] for output in outputs.values()]
        spans = {model: max(r["pr"][model] for r in results) - min(r["pr"][model] for r in results)
                 for model in p["models"]}
        largest = max(largest, *spans.values())
        agree = all(r["selected"] == baseline[index]["selected"] for r in results)
        all_sets = all_sets and agree
        comparisons.append({"series": entry["series"], "pairwise_max_minus_min": spans,
                            "all_selected_sets_agree": agree, "reference_selected": baseline[index]["selected"],
                            "passes": [{"trial": trial, "method": method,
                                        "pr_minus_reference": {m: output[index]["pr"][m] - baseline[index]["pr"][m]
                                                               for m in p["models"]},
                                        "selected_agrees": output[index]["selected"] == baseline[index]["selected"]}
                                       for (trial, method), output in outputs.items()]})
    medians = {method: statistics.median(values) for method, values in seconds.items()}
    faster = {method: medians["radix_pr"] < medians[method] for method in METHODS[1:]}
    passed = largest <= p["parity_atol"] and all_sets and all(faster.values())
    return {
        "status": "PASS" if passed else "FAIL", "receipt_validation": "PASS",
        "protocol_sha256": expected_hash, "inputs_sha256": p["inputs_sha256"],
        "freeze_receipt_sha256": digest(study / "freeze_receipt.json"),
        "completion_sha256": digest(run / "completion.json"), "auditor_sha256": digest(Path(__file__)),
        "series": 308, "families": 17, "whole_seconds": seconds, "median_seconds": medians,
        "radix_faster_than_control": faster,
        "median_speedup_over_radix": {m: medians[m] / medians["radix_pr"] for m in METHODS[1:]},
        "max_pairwise_pr_difference": largest, "all_selected_sets_agree": all_sets,
        "parity_atol": p["parity_atol"], "passes": rows, "differences": comparisons,
        "repository_sources_verified": {name: p["source_sha256"][name] for name in REPOSITORY_SOURCES},
        "external_sources_not_reopened": {name: p["source_sha256"][name] for name in EXTERNAL_SOURCES},
        "verification_scope": {
            "public_receipt_hashes_and_internal_consistency": True,
            "original_series_models_and_member_hashes": True,
            "repository_owned_source_bytes": True,
            "raw_npz_bytes_or_decoded_arrays": False,
            "raw_source_archives_or_zip_members": False,
            "external_klein_source_or_license_cache_bytes": False,
            "independent_metric_recomputation": False,
            "note": "Raw inputs and external source hashes are public frozen descriptors whose identity/provenance chain is checked. Their current bytes, numeric metric correctness, actual clock operation, and actual machine isolation are not established by this receipt-only audit. The cache-backed driver report is a separate verification step.",
        },
        "order_positions": {m: [order.index(m) for order in p["orders"]] for m in METHODS},
        "uncertainty": "Three observations per method; no CI or significance claim. Seeded order is randomized, not guaranteed position-balanced.",
        "scope": p["scope"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "Audit output already exists; overwrite forbidden")
    result = audit(args.study, args.protocol_sha256)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("passes", "differences")}, indent=2))


if __name__ == "__main__":
    main()
