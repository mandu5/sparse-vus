"""Diagnose frozen raw-decoding identities without fitting or metric evaluation.

The output contains hashes, mismatch counts and aggregate floating-point metadata,
never observation/label vectors. Mismatches are diagnostic results, not waived
validation checks. The frozen producer and selection are not imported or changed.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "artifacts/pvldb-research-20261024/strengthening/source-discovery.json"
DISCOVERY_SHA = "3323712337117428e497655b7e0e3b1bafd2285938466de71e842c5375f76b26"
SELECTION_SHA = "ed9eb0e9d906c3bd321bf6446cb4bfbbabdeddef154e17fa8ef1fb2f9e5e196c"
ARCHIVE_SHA = "0c47020d3423723c70773736dbd800369f2b487328becbf339450d1ae5020961"
ARCHIVE_URL = "https://www.thedatum.org/datasets/TSB-AD-U.zip"
PARSERS = ("pandas_default", "pandas_round_trip", "python_float")


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def array_digest(array):
    array = np.ascontiguousarray(array)
    header = json.dumps({"dtype": array.dtype.str, "shape": list(array.shape)}, sort_keys=True).encode()
    return hashlib.sha256(header + b"\0" + array.tobytes()).hexdigest()


def acquire(path):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(path.name + ".download")
        if partial.exists():
            raise FileExistsError("Refusing to overwrite partial acquisition: " + str(partial))
        subprocess.run(["curl", "-fL", "--retry", "2", "--max-time", "300",
                        ARCHIVE_URL, "-o", str(partial)], check=True)
        if digest(partial) != ARCHIVE_SHA:
            raise ValueError("Canonical raw archive identity mismatch")
        partial.rename(path)
    if digest(path) != ARCHIVE_SHA:
        raise ValueError("Canonical raw archive identity mismatch")


def parse(raw, parser):
    if parser == "python_float":
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
        columns = reader.fieldnames
        if columns is None or len(columns) != 2 or "Label" not in columns:
            raise ValueError("Unexpected original CSV schema")
        column = next(c for c in columns if c != "Label")
        rows = list(reader)
        values = np.asarray([float(row[column]) for row in rows], dtype=np.float64)
        raw_labels = np.asarray([float(row["Label"]) for row in rows], dtype=np.float64)
    else:
        kwargs = {} if parser == "pandas_default" else {"float_precision": "round_trip"}
        frame = pd.read_csv(io.BytesIO(raw), **kwargs)
        if frame.shape[1] != 2 or "Label" not in frame:
            raise ValueError("Unexpected original CSV schema")
        values = frame.drop(columns=["Label"]).to_numpy(dtype=np.float64)[:, 0]
        raw_labels = frame["Label"].to_numpy()
    if not np.isfinite(values).all() or not np.isin(raw_labels, [0, 1]).all():
        raise ValueError("Nonfinite observations or nonbinary labels")
    return np.ascontiguousarray(values), np.ascontiguousarray(raw_labels.astype(np.int8))


def normalized(values):
    mean, scale = float(np.mean(values)), float(np.std(values))
    z = (values - mean) / scale if scale else np.zeros_like(values)
    rounded = np.round(z, 10)
    rounded[rounded == 0] = 0.0
    return np.ascontiguousarray(rounded), {"mean_hex": mean.hex(), "std_ddof0_hex": scale.hex()}


def diagnose(archive_path):
    if digest(DISCOVERY) != DISCOVERY_SHA:
        raise ValueError("Frozen discovery identity mismatch")
    discovery = json.loads(DISCOVERY.read_text())
    selection = discovery["selection"]
    actual_selection = hashlib.sha256(json.dumps(selection, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if actual_selection != SELECTION_SHA or discovery["selection_sha256"] != SELECTION_SHA:
        raise ValueError("Frozen selection identity mismatch")
    acquire(archive_path)
    reports = []
    with zipfile.ZipFile(archive_path) as archive:
        names = {Path(name).stem: name for name in archive.namelist() if name.endswith(".csv")}
        for case in selection["cases"]:
            raw = archive.read(names[case["id"]])
            raw_sha = hashlib.sha256(raw).hexdigest()
            parsed, entries = {}, {}
            for parser in PARSERS:
                try:
                    values, labels = parse(raw, parser)
                    rounded, moments = normalized(values)
                    exact_sha, z_sha, label_sha = array_digest(values), array_digest(rounded), array_digest(labels)
                    matches = {"raw_member": raw_sha == case["raw_sha256"],
                               "length": len(labels) == case["n"],
                               "labels": label_sha == case["label_hash"],
                               "exact_observations": exact_sha == case["observation_hashes"][0],
                               "rounded_z_observations": z_sha == case["observation_hashes"][1]}
                    entries[parser] = {"status": "PARSED", "n": len(labels), "positive": int(labels.sum()),
                                       "observation_dtype": values.dtype.str, "label_dtype": labels.dtype.str,
                                       "label_sha256": label_sha, "exact_observation_sha256": exact_sha,
                                       "rounded_z_observation_sha256": z_sha, "normalization": moments,
                                       "matches_frozen": matches, "all_components_match": all(matches.values())}
                    parsed[parser] = (values, labels, rounded)
                except Exception as error:
                    entries[parser] = {"status": "PARSE_ERROR", "error_type": type(error).__name__,
                                       "error": str(error), "all_components_match": False}
            comparisons = []
            for left, right in (("pandas_default", "pandas_round_trip"),
                                ("pandas_default", "python_float"),
                                ("pandas_round_trip", "python_float")):
                if left not in parsed or right not in parsed:
                    continue
                a, ya, za = parsed[left]
                b, yb, zb = parsed[right]
                same_shape = a.shape == b.shape and ya.shape == yb.shape
                entry = {"left": left, "right": right, "same_shape": same_shape}
                if same_shape:
                    entry.update({"observation_bit_mismatches": int(np.count_nonzero(a.view(np.uint64) != b.view(np.uint64))),
                                  "label_mismatches": int(np.count_nonzero(ya != yb)),
                                  "rounded_z_bit_mismatches": int(np.count_nonzero(za.view(np.uint64) != zb.view(np.uint64))),
                                  "max_absolute_observation_difference": float(np.max(np.abs(a - b))),
                                  "max_absolute_rounded_z_difference": float(np.max(np.abs(za - zb)))})
                comparisons.append(entry)
            reports.append({"id": case["id"], "family": case["family"], "archive_member": names[case["id"]],
                            "raw_sha256": raw_sha, "expected": {"n": case["n"], "raw_sha256": case["raw_sha256"],
                            "label_sha256": case["label_hash"], "exact_observation_sha256": case["observation_hashes"][0],
                            "rounded_z_observation_sha256": case["observation_hashes"][1]},
                            "parsers": entries, "parser_comparisons": comparisons})
    mismatches = {}
    for parser in PARSERS:
        mismatches[parser] = {component: [case["id"] for case in reports
            if not case["parsers"][parser].get("matches_frozen", {}).get(component, False)]
            for component in ("raw_member", "length", "labels", "exact_observations", "rounded_z_observations")}
    return {"status": "DIAGNOSTIC_COMPLETE_NOT_A_VALIDATION_WAIVER",
            "created_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
            "platform": platform.platform(), "machine": platform.machine(),
            "packages": {"numpy": np.__version__, "pandas": pd.__version__},
            "script_sha256": digest(__file__), "discovery_sha256": DISCOVERY_SHA,
            "selection_sha256": SELECTION_SHA, "archive_sha256": ARCHIVE_SHA,
            "archive_bytes": archive_path.stat().st_size, "cases": len(reports),
            "parsers": list(PARSERS), "mismatching_case_ids_by_component": mismatches,
            "case_reports": reports, "detector_fits_performed": 0,
            "metric_evaluation_performed": False, "raw_vectors_redistributed": False,
            "interpretation": "Compare each component separately. All mismatches are retained. No threshold, identity rule, source, selected recording or producer was changed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Refusing to replace diagnostic output: " + str(args.out))
    report = diagnose(args.archive.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "pandas": pd.__version__, "numpy": np.__version__,
                      "cases": report["cases"], "mismatch_counts": {
                          parser: {component: len(ids) for component, ids in by_component.items()}
                          for parser, by_component in report["mismatching_case_ids_by_component"].items()},
                      "out": str(args.out), "out_sha256": digest(args.out)}))


if __name__ == "__main__":
    main()
