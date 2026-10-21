"""Post-run provenance gate for advancement measurements.

The recorded benchmark input hashes are reconciled against the immutable
v0.1.0 release manifests and the locally cached source-member bytes. This gate
was added after benchmark execution began; it is not preregistration.

API:
    validate_advancement_data(rows, mode="baseline")
    validate_advancement_data(rows, mode="certified")

CLI (run only after controlled timing has finished):
    python experiments/advancement_data_gate.py --mode baseline \
        artifacts/advancement/mac_baseline/measurements.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE_COMMIT = "7565b6657ba510e79db13e79b809b58e77feacc0"
# Hashes obtained directly from git show <RELEASE_COMMIT>:<path>, not from
# today's mutable files. They bind the original input/selection chain.
RELEASE_BINDINGS = {
    "experiments/data_hashes.json": "d53de71d4fedad5824bb2793a5997f7e416fb3f18246c4a7675a1fefd071857b",
    "experiments/data_manifest.json": "1bec6e203f49125de455bc8f8518795135f1382596aeee69419dbec82d13006e",
    "artifacts/public_benchmark_receipt.json": "06415e81b835bdc649ca75bea0672d1e4ddc8ded0d04f5a2972cb6adf638e02d",
    "artifacts/selected_series.json": "c8a48fcffe7b06d62067ad573bc4144d354619022972277c760070b18a65ef40",
    "artifacts/external_supplement_selection.json": "dadd9dda028cd261b7715121f2526cb596e356188d5be7d57b29da21599eeaee",
    "artifacts/bolt_base_64-download.json": "b4b01871da70d7c778ede06274c077696f8af42d50e2787d4bfcb683d0eb9cc9",
    "artifacts/TimeMoE-200M_64-download.json": "36bf99d0219b882257fa93d1252647999d40c9a6f01dbcb5f68ae10727514fad",
    "artifacts/timesfm-1.0-200m_64-download.json": "91da5b782937e3b7538118241f9585e4f408571a0fc47feeda6126debe16d24c",
}


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def released_metadata(root):
    """Verify small manifests and original JSONL without opening source ZIPs."""
    root = Path(root)
    for relative, expected in RELEASE_BINDINGS.items():
        require(digest(root / relative) == expected, f"Release binding mismatch: {relative}")
    receipt = load_json(root / "artifacts/public_benchmark_receipt.json")
    original_path = root / "artifacts/public_benchmark.jsonl"
    require(digest(original_path) == receipt["records_sha256"],
            "Original benchmark differs from release receipt")
    original = [json.loads(line) for line in original_path.read_text().splitlines()]
    selection = load_json(root / "artifacts/selected_series.json")
    models = sorted(m["name"] for m in load_json(root / "experiments/data_manifest.json")["models"])
    series = selection["ordered_series"]
    require(len(series) == 350 and len(set(series)) == 350, "Original series coverage mismatch")
    require(set(selection["models"]) == set(models) and len(models) == 3,
            "Original model coverage mismatch")
    original_keys = [(r["series"], r["model"], r["max_buffer"]) for r in original]
    expected = set(itertools.product(series, models, (10, 30)))
    require(len(original_keys) == len(set(original_keys)) and set(original_keys) == expected,
            "Original case coverage mismatch")
    require(receipt["metric_evaluations"] == len(original) == 2100,
            "Original receipt case count mismatch")
    series_metadata = {}
    for row in original:
        metadata = {"n": row["n"], "family": row["family"],
                    "positive_points": row["positive_points"],
                    "label_sha256": row["label_member_sha256"]}
        if row["series"] in series_metadata:
            require(series_metadata[row["series"]] == metadata,
                    f"Inconsistent original series metadata: {row['series']}")
        series_metadata[row["series"]] = metadata
    score_hashes = {}
    locks = load_json(root / "experiments/data_hashes.json")
    for model in models:
        download = load_json(root / f"artifacts/{model}-download.json")
        members = download["members"]
        member_paths = [r["path"] for r in members]
        require(len(set(member_paths)) == len(member_paths), f"Duplicate score receipt: {model}")
        locked_items = sorted((r["path"], r["sha256"]) for r in members)
        computed = hashlib.sha256(json.dumps(locked_items, separators=(",", ":")).encode()).hexdigest()
        require(computed == locks["score_member_manifests"][model],
                f"Score member lock differs from released manifest: {model}")
        for item in members:
            stem = Path(item["path"]).stem
            if stem in series_metadata:
                require(item["path"] == f"scores/{stem}.npy", "Unexpected score member path")
                score_hashes[stem, model] = item["sha256"]
    require(set(score_hashes) == set(itertools.product(series, models)),
            "Missing selected score-member hash")
    supplement = load_json(root / "artifacts/external_supplement_selection.json")
    selected = [r["series"] for r in supplement]
    require(len(selected) == len(set(selected)) == 42, "Certified selection coverage mismatch")
    for row in supplement:
        meta = series_metadata[row["series"]]
        require(all(row[key] == meta[key] for key in ("n", "family", "label_sha256")),
                f"Supplement metadata mismatch: {row['series']}")
        require(row["score_sha256"] == score_hashes[row["series"], "bolt_base_64"],
                f"Supplement source score mismatch: {row['series']}")
    return series_metadata, models, score_hashes, selected, locks, receipt


def validate_advancement_data(rows, *, mode, root=None):
    """Fail closed on changed source bytes, selection, hashes or row metadata.

    Opens every selected source score member and each selected label member.
    This performs no metric evaluation or timing experiment. Its returned audit
    is evidence about recorded input identity, not a retrospective claim that
    these stronger checks ran before measurement.
    """
    if mode not in ("baseline", "certified"):
        raise ValueError("mode must be baseline or certified")
    root = Path(root or ROOT).resolve()
    metadata, models, score_hashes, selected, locks, original_receipt = released_metadata(root)
    wanted_series = sorted(metadata) if mode == "baseline" else sorted(selected)
    widths = (10, 30) if mode == "baseline" else (30, 100, 300)
    expected = set(itertools.product(wanted_series, models, widths))
    keys = [(r["series"], r["model"], r["max_buffer"]) for r in rows]
    require(len(keys) == len(set(keys)) and set(keys) == expected,
            "Advancement case set differs from fixed release selection")
    for row in rows:
        meta = metadata[row["series"]]
        for name in ("n", "family", "label_sha256"):
            require(row[name] == meta[name], f"Recorded {name} mismatch: {row['series']}")
        require(row["score_sha256"] == score_hashes[row["series"], row["model"]],
                f"Recorded score identity mismatch: {row['series']}, {row['model']}")

    # Import numerical/CSV readers only after the cheap provenance checks.
    import numpy as np
    import pandas as pd
    source_files = {}
    for filename, expected_sha in locks["files"].items():
        observed = digest(root / "cache" / filename)
        require(observed == expected_sha, f"Cached release file changed: {filename}")
        source_files[filename] = observed
    label_count = 0
    with zipfile.ZipFile(root / "cache/TSB-AD-U.zip") as archive:
        paths = [name for name in archive.namelist() if name.endswith(".csv")]
        names = {Path(name).stem: name for name in paths}
        require(len(names) == len(paths), "Ambiguous label member stem")
        for series in wanted_series:
            raw = archive.read(names[series])  # zipfile checks this member's CRC
            require(hashlib.sha256(raw).hexdigest() == metadata[series]["label_sha256"],
                    f"Actual label member changed: {series}")
            y = pd.read_csv(io.BytesIO(raw), usecols=["Label"])["Label"].to_numpy()
            require(len(y) == metadata[series]["n"] and np.isin(y, [0, 1]).all()
                    and int(y.sum()) == metadata[series]["positive_points"]
                    and 0 < y.sum() < len(y), f"Actual label metadata mismatch: {series}")
            label_count += 1
    score_count = 0
    observed_members = []
    for model in models:
        with zipfile.ZipFile(root / f"cache/{model}.score-range.zip") as archive:
            members = archive.namelist()
            require(len(members) == len(set(members)), f"Ambiguous ZIP members: {model}")
            for series in wanted_series:
                member = f"scores/{series}.npy"
                raw = archive.read(member)
                actual = hashlib.sha256(raw).hexdigest()
                require(actual == score_hashes[series, model],
                        f"Actual score member changed: {series}, {model}")
                score = np.load(io.BytesIO(raw), allow_pickle=False)
                require(score.ndim == 1 and len(score) == metadata[series]["n"]
                        and np.isfinite(score).all(),
                        f"Actual score shape/finite check failed: {series}, {model}")
                observed_members.append((series, model, actual))
                score_count += 1
    return {
        "status": "PASS", "mode": mode,
        "scope": "Post-run provenance reconciliation added after benchmark start; not preregistration.",
        "release_commit": RELEASE_COMMIT, "release_bindings": RELEASE_BINDINGS,
        "original_benchmark_sha256": original_receipt["records_sha256"],
        "measurement_rows": len(rows), "series": len(wanted_series),
        "families": len({metadata[s]["family"] for s in wanted_series}),
        "actual_label_members_verified": label_count,
        "actual_score_members_verified": score_count,
        "source_files_sha256": source_files,
        "verified_score_manifest_sha256": hashlib.sha256(
            json.dumps(sorted(observed_members), separators=(",", ":")).encode()).hexdigest(),
        "checks": ["release manifest and receipt identity", "original case coverage",
                   "score-member manifest locks", "actual ZIP member CRC and SHA-256",
                   "actual label shape/classes/count", "actual score shape/finite values",
                   "measurement per-row label/score identity", "exact mode-specific case set"],
        "whole_score_archive_md5_verified": False,
        "gate_sha256": digest(Path(__file__))
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("baseline", "certified"), required=True)
    parser.add_argument("measurements", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = {}
    for path in args.measurements:
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        results[str(path)] = validate_advancement_data(rows, mode=args.mode)
    text = json.dumps(results, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
