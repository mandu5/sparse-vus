"""Portable structural/external tie replication, separate from frozen studies.

Preparation downloads fixed sources and regenerates scores; it does not compute
metrics. Run timing only after preparation, in an otherwise idle environment.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "experiments/reproduce_tie_runs.py"
DESIGN = "docs/tie_run_replication_protocol_20261023.md"
REFERENCE = "artifacts/tie-runs/mac-20261023"
EXTERNAL = "artifacts/saturation/external-inputs"
MODELS = ("isolation_forest", "pca_reconstruction", "knn_distance", "robust_marginal_z")
METHODS = ("tie_runs", "saturation", "radix", "klein")
WIDTHS = (30, 100, 300)
IGNORED_SELECTION_FIELDS = frozenset({"environment", "frozen_utc"})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_new_json(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def bound_path(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    require(not relative.is_absolute(), "A bound path must be repository-relative")
    require(relative.parts and ".." not in relative.parts,
            "Bound path escapes repository through parent traversal")
    target = root / relative
    resolved = target.resolve()
    if relative.parts[0] == ".cache":
        cache_root = (root / ".cache").resolve()
        require(resolved == cache_root or cache_root in resolved.parents,
                "Bound path escapes the shared cache root")
    else:
        require(resolved != root and root in resolved.parents, "Bound path escapes repository")
    # The generator records target.relative_to(ROOT); retain its logical path
    # even when the worktree's ignored .cache points to a shared external cache.
    return target


def check_hashes(root, bindings):
    for relative, expected in bindings.items():
        require(digest(bound_path(root, relative)) == expected,
                f"Bound source/input changed: {relative}")


def output_path(root, value):
    root = Path(root).resolve()
    output = Path(value)
    output = output.resolve() if output.is_absolute() else (root / output).resolve()
    base = root / "artifacts/tie-runs"
    require(base in output.parents and root in output.parents,
            "Output must be inside repository artifacts/tie-runs")
    require(output.name not in {".", "..", ""}, "Invalid output name")
    return output


def reserve_paths(root, value):
    root = Path(root).resolve()
    output = output_path(root, value)
    cache = bound_path(root, f".cache/tie-replication/{output.name}")
    require(not output.exists() and not cache.exists(),
            "Output and replication cache must both be new")
    output.mkdir(parents=True, exist_ok=False)
    cache.mkdir(parents=True, exist_ok=False)
    return output, cache


def compare_selection(reference, regenerated):
    """Ignore only time/environment; all selection and generator facts must match."""
    require(reference.keys() == regenerated.keys(), "Selection field set differs")
    changed = [key for key in reference
               if key not in IGNORED_SELECTION_FIELDS and reference[key] != regenerated[key]]
    require(not changed, f"Selection differs before generation: {changed}")
    return {"status": "SELECTION_IDENTICAL", "ignored_fields": sorted(IGNORED_SELECTION_FIELDS),
            "compared_fields": sorted(reference.keys() - IGNORED_SELECTION_FIELDS),
            "scope": "Same fixed source selection and generation procedure; environment/time may differ."}


def compare_manifests(reference, regenerated):
    """Require observations/labels, retain score comparisons without requiring equality."""
    for label, manifest in (("reference", reference), ("regenerated", regenerated)):
        expected = {"status": "INPUTS_VERIFIED_NO_METRIC_OUTCOMES", "series_count": 12,
                    "family_count": 9, "score_vectors": 48, "models": list(MODELS),
                    "metric_outcomes_computed": False}
        require(all(manifest.get(k) == v for k, v in expected.items()),
                f"Invalid {label} manifest coverage/status")
    require(reference["parameters"] == regenerated["parameters"], "Generator parameters differ")
    before = {row["series"]: row for row in reference["series"]}
    after = {row["series"]: row for row in regenerated["series"]}
    require(len(reference["series"]) == len(regenerated["series"]) == len(before) == len(after) == 12
            and before.keys() == after.keys(), "Series identities/unique coverage differ")
    comparisons = []
    for name in sorted(before):
        old, new = before[name], after[name]
        for key in ("family", "canonical_family", "url", "raw_bytes", "raw_sha256", "n",
                    "preprocessing", "actual_parameters"):
            require(old[key] == new[key], f"Required input identity differs: {name}/{key}")
        require(set(old["array_sha256"]) == set(new["array_sha256"]) == {"labels", *MODELS},
                f"Array member set differs: {name}")
        require(old["array_sha256"]["labels"] == new["array_sha256"]["labels"],
                f"Label identity differs: {name}")
        comparisons.append({"series": name, "raw_sha256": new["raw_sha256"],
            "labels_sha256": new["array_sha256"]["labels"],
            "npz_bytes_equal": old["npz_sha256"] == new["npz_sha256"],
            "scores": {model: {"reference_sha256": old["array_sha256"][model],
                "regenerated_sha256": new["array_sha256"][model],
                "equal": old["array_sha256"][model] == new["array_sha256"][model]}
                for model in MODELS}})
    equal = sum(score["equal"] for row in comparisons for score in row["scores"].values())
    return {"status": "RAW_AND_LABEL_IDENTITIES_MATCH", "series": comparisons,
            "score_vectors_compared": 48, "score_vectors_equal": equal,
            "all_score_vectors_byte_identical": equal == 48,
            "scope": "Regenerated previously studied data, not an unseen population or assumed identical-score replay."}


def raw_array_digest(array):
    """External generation receipts hash only contiguous numerical bytes."""
    import numpy as np
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def array_digest(array):
    """Match the frozen timing runner's dtype/shape-prefixed array identity."""
    import numpy as np
    array = np.ascontiguousarray(array)
    header = json.dumps({"dtype": array.dtype.str, "shape": list(array.shape)},
                        sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(header + b"\n" + array.tobytes()).hexdigest()


def validate_labels(labels, n):
    import numpy as np
    require(labels.shape == (n,) and labels.dtype == np.uint8
            and np.isin(labels, [0, 1]).all() and 0 < labels.sum() < n, "Invalid labels")
    return int(np.count_nonzero((labels == 1) & np.r_[True, labels[:-1] != 1]))


def make_inputs(root, output, cache, manifest, structural_rows, expected_external):
    """Build scalar fixtures; observational arrays stay only in ignored cache."""
    import numpy as np
    root, output, cache = Path(root), Path(output), Path(cache)
    public = output / "inputs"
    private = cache / "scalar-inputs"
    public.mkdir(exist_ok=False)
    private.mkdir(exist_ok=False)
    rows = []
    for index, item in enumerate(structural_rows):
        require(item["phase"] == "structural", "Only structural fixtures may be published")
        source = bound_path(root, item["input_path"])
        require(digest(source) == item["npz_sha256"], "Structural fixture identity changed")
        with np.load(source, allow_pickle=False) as arrays:
            require(set(arrays.files) == {"labels", "scores"}, "Unexpected structural NPZ members")
            y, scores = arrays["labels"], arrays["scores"]
            require(validate_labels(y, item["n"]) == 1, "Structural fixture is not one interval")
            require(array_digest(y) == item["labels_sha256"]
                    and array_digest(scores) == item["scores_sha256"], "Structural arrays changed")
        target = public / f"{index:03}.npz"
        shutil.copyfile(source, target)
        rows.append({**item, "input_path": str(target.relative_to(root))})

    actual_external = set()
    for receipt in manifest["series"]:
        path = bound_path(root, receipt["npz_path"])
        require(digest(path) == receipt["npz_sha256"], "Generated NPZ identity changed")
        with np.load(path, allow_pickle=False) as arrays:
            require(set(arrays.files) == {"labels", *MODELS}, "Unexpected generated NPZ members")
            y = arrays["labels"]
            intervals = validate_labels(y, receipt["n"])
            for name in arrays.files:
                a = arrays[name]
                require(a.shape == y.shape and np.isfinite(a).all()
                        and raw_array_digest(a) == receipt["array_sha256"][name],
                        f"Generated array identity changed: {receipt['series']}/{name}")
                if name != "labels":
                    require(a.dtype == np.float64, "Generated scores must be binary64")
            if intervals != 1:
                continue
            for model in MODELS:
                scores = arrays[model]
                target = private / f"{len(rows):03}.npz"
                with target.open("xb") as stream:
                    np.savez(stream, labels=y, scores=scores)
                common = {"phase": "external_regenerated", "family": receipt["family"],
                    "series": receipt["series"], "model": model, "n": len(y),
                    "positive_points": int(y.sum()), "input_path": str(target.relative_to(root)),
                    "npz_sha256": digest(target), "labels_sha256": array_digest(y),
                    "scores_sha256": array_digest(scores)}
                for width in WIDTHS:
                    key = (receipt["series"], model, width)
                    require(key not in actual_external, "Duplicate regenerated case")
                    actual_external.add(key)
                    rows.append({**common, "max_buffer": width,
                        "case_id": f"regenerated|{receipt['series']}|{model}|{width}"})
    require(actual_external == set(expected_external),
            "One-interval case coverage differs from the fixed historical label selection")
    return rows


def prepare(value, root=ROOT):
    root = Path(root).resolve()
    output, cache = reserve_paths(root, value)
    sys.path.insert(0, str(root / "experiments"))
    generator = importlib.import_module("fetch_saturation_external")
    adapter = importlib.import_module("fast_vus_adapter")
    baseline = importlib.import_module("benchmark_tie_runs")
    require(generator.ROOT.resolve() == baseline.ROOT.resolve() == root, "Imported module root differs")
    adapter.fetch_reference()
    old_selection_path = root / EXTERNAL / "selection.json"
    old_manifest_path = root / EXTERNAL / "manifest.json"
    old_selection, old_manifest = read_json(old_selection_path), read_json(old_manifest_path)
    require(old_manifest["selection_sha256"] == digest(old_selection_path), "Historical selection binding differs")
    check_hashes(root, old_selection["source_sha256"])
    old_protocol_path, old_inputs_path = root / REFERENCE / "protocol.json", root / REFERENCE / "inputs.json"
    old_protocol = read_json(old_protocol_path)
    check_hashes(root, old_protocol["source_sha256"])
    require(digest(old_inputs_path) == old_protocol["inputs_sha256"], "Historical tie inputs changed")
    old_inputs = read_json(old_inputs_path)
    structural = [row for row in old_inputs if row["phase"] == "structural"]
    expected_external = {(row["series"], row["model"], row["max_buffer"])
                         for row in old_inputs if row["phase"] == "external"}
    require(len(structural) == 20 and len(expected_external) == 48, "Historical subset coverage differs")
    require(tuple(baseline.METHODS) == METHODS and baseline.REPS == 5, "Measured method configuration changed")
    source_bindings = baseline.sources()
    for name in (SCRIPT, DESIGN, generator.SCRIPT, generator.DESIGN):
        source_bindings[name] = digest(root / name)

    previous_cache, previous_out = generator.CACHE, generator.OUT
    generation = output / "generation"
    try:
        generator.CACHE, generator.OUT = cache / "generation", generation
        generator.freeze()
        selection_path = generation / "selection.json"
        selection_check = compare_selection(old_selection, read_json(selection_path))
        selection_check.update(reference_sha256=digest(old_selection_path),
                               regenerated_sha256=digest(selection_path))
        write_new_json(output / "selection-comparison.json", selection_check)
        generator.generate()
        manifest_path = generation / "manifest.json"
        manifest = read_json(manifest_path)
        require(manifest["selection_sha256"] == digest(selection_path), "Generated selection binding differs")
        comparison = compare_manifests(old_manifest, manifest)
        comparison.update(reference_manifest_sha256=digest(old_manifest_path),
                          regenerated_manifest_sha256=digest(manifest_path))
        write_new_json(output / "input-comparison.json", comparison)
        rows = make_inputs(root, output, cache, manifest, structural, expected_external)
    finally:
        generator.CACHE, generator.OUT = previous_cache, previous_out
    require(len(rows) == 68, "Expected 20 structural plus 48 regenerated external cases")
    check_hashes(root, source_bindings)
    write_new_json(output / "inputs.json", rows)
    bound = (old_protocol_path, old_inputs_path, old_selection_path, old_manifest_path,
             generation / "selection.json", generation / "manifest.json",
             output / "selection-comparison.json", output / "input-comparison.json")
    protocol = {"version": 1, "methods": list(METHODS), "repetitions": baseline.REPS,
        "seed": baseline.SEED, "parity_atol": baseline.ATOL, "cases": len(rows),
        "source_sha256": source_bindings,
        "manifest_sha256": {str(path.relative_to(root)): digest(path) for path in bound},
        "inputs_sha256": digest(output / "inputs.json"),
        "replication": {"orchestrator": SCRIPT, "structural_cases": 20,
            "regenerated_external_cases": 48, "excluded_historical_development_cases": 63},
        "history": "Same 12 fixed external series, regenerated scores; previously studied data. "
                   "Only one-interval vectors enter timing. Historical development archives are excluded.",
        "decision": "Numerical/work checks only; all timing ratios and losses descriptive. "
                    "Not the original 131-case study or a new primary runtime criterion."}
    write_new_json(output / "protocol.json", protocol)
    result = {"status": "PREPARED_NO_METRIC_OUTCOMES", "cases": len(rows),
              "protocol_sha256": digest(output / "protocol.json"),
              "score_vectors_equal_to_mac": comparison["score_vectors_equal"],
              "score_vectors_compared": comparison["score_vectors_compared"]}
    write_new_json(output / "preparation.json", result)
    return result


def run(value, expected_hash, root=ROOT):
    root = Path(root).resolve()
    output = output_path(root, value)
    require(digest(output / "protocol.json") == expected_hash, "Protocol hash differs")
    protocol = read_json(output / "protocol.json")
    require(protocol.get("replication", {}).get("orchestrator") == SCRIPT,
            "Not a portable tie-replication protocol")
    check_hashes(root, protocol["source_sha256"])
    check_hashes(root, protocol["manifest_sha256"])
    sys.path.insert(0, str(root / "experiments"))
    baseline = importlib.import_module("benchmark_tie_runs")
    require(baseline.ROOT.resolve() == root, "Imported benchmark root differs")
    return baseline.run(output, expected_hash)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--protocol-sha256")
    args = parser.parse_args()
    if args.command == "run" and not args.protocol_sha256:
        parser.error("run requires --protocol-sha256 from preparation")
    if args.command == "prepare" and args.protocol_sha256:
        parser.error("prepare does not accept --protocol-sha256")
    result = prepare(args.output) if args.command == "prepare" else run(args.output, args.protocol_sha256)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
