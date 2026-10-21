"""Regenerate external inputs and run the frozen experiment on GitHub Actions.

No raw data or score arrays enter the upload directory. Mac receipts remain
available for identity checks, while Linux gets its own environment binding.
This wrapper deliberately refuses local execution before any mutation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "artifacts/saturation/external-inputs"
MAC_REFERENCE = ROOT / ".cache/saturation-mac-reference"
WORKFLOW = ROOT / ".github/workflows/saturation-external-benchmark.yml"
LICENSE_NOTE = ROOT / "docs/saturation_data_licenses_20261021.md"
MODELS = ["isolation_forest", "pca_reconstruction", "knn_distance", "robust_marginal_z"]
METHODS = ["saturation", "active_full", "last_positive", "radix", "dense_radix",
           "klein", "sparse_comparison", "dense_direct", "dense_direct_radix"]
VERSIONS = {"numpy": "1.26.4", "numba": "0.59.1", "pandas": "3.0.1",
            "scipy": "1.17.1", "scikit-learn": "1.8.0", "threadpoolctl": "3.6.0"}
SELECTION_FIELDS = (
    "source", "source_code_revision", "source_data_revision", "metadata_sha256",
    "file_tree_sha256", "previous_manifest_sha256", "previous_families",
    "previous_canonical_families", "family_aliases", "rule", "selected_count",
    "family_count", "models", "parameters", "source_sha256", "series",
)


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def copy_receipts(source, destination):
    """Only JSON metadata, never CSV observations, NPZ, NPY, or archives."""
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for path in sorted(source.glob("*.json")):
            require(not path.is_symlink(), f"Unexpected receipt symlink: {path}")
            shutil.copy2(path, destination / path.name)


def compare_selection(output):
    """Validate the new selection before downloading observations or fitting scores."""
    mac = read_json(MAC_REFERENCE / "selection.json")
    linux = read_json(INPUTS / "selection.json")
    fields = {key: mac[key] == linux[key] for key in SELECTION_FIELDS}
    write_json(output / "selection-identity-comparison.json", {
        "status": "MATCH" if all(fields.values()) else "FAILED",
        "stage": "before Linux raw-data download or score generation", "utc": utc(),
        "fields_equal": fields, "mac_selection_sha256": digest(MAC_REFERENCE / "selection.json"),
        "linux_selection_sha256": digest(INPUTS / "selection.json"),
        "scope": "Required selection content is compared; timestamps and platform-specific environment bindings may differ.",
    })
    require(all(fields.values()), f"Selection differs before acquisition: {[key for key, equal in fields.items() if not equal]}")


def compare_inputs(output):
    mac_selection = read_json(MAC_REFERENCE / "selection.json")
    linux_selection = read_json(INPUTS / "selection.json")
    mac = read_json(MAC_REFERENCE / "manifest.json")
    linux = read_json(INPUTS / "manifest.json")
    comparisons = []
    failures = []
    for key in SELECTION_FIELDS:
        if mac_selection[key] != linux_selection[key]:
            failures.append(f"Selection field differs: {key}")
    for manifest, label, directory in ((mac, "Mac", MAC_REFERENCE), (linux, "Linux", INPUTS)):
        if manifest["selection_sha256"] != digest(directory / "selection.json"):
            failures.append(f"{label} selection binding mismatch")
        for key, expected in (("series_count", 12), ("family_count", 9),
                              ("score_vectors", 48), ("models", MODELS),
                              ("metric_outcomes_computed", False),
                              ("status", "INPUTS_VERIFIED_NO_METRIC_OUTCOMES")):
            if manifest[key] != expected:
                failures.append(f"{label} manifest field {key} is not {expected!r}")
    old = {row["series"]: row for row in mac["series"]}
    new = {row["series"]: row for row in linux["series"]}
    if (len(mac["series"]) != 12 or len(linux["series"]) != 12
            or len(old) != 12 or len(new) != 12 or old.keys() != new.keys()):
        failures.append("Series identity or unique 12-series coverage differs")
    for name in sorted(old.keys() & new.keys()):
        before, after = old[name], new[name]
        fields = ("family", "canonical_family", "url", "raw_bytes", "raw_sha256", "n",
                  "preprocessing", "actual_parameters")
        changed = [key for key in fields if before[key] != after[key]]
        if before["array_sha256"]["labels"] != after["array_sha256"]["labels"]:
            changed.append("label_sha256")
        if set(before["array_sha256"]) != {"labels", *MODELS} or set(after["array_sha256"]) != {"labels", *MODELS}:
            changed.append("array_members")
        if changed:
            failures.append(f"{name}: required identity differs: {changed}")
        comparisons.append({
            "series": name, "family": after["family"], "n": after["n"],
            "required_identity_match": not changed, "different_required_fields": changed,
            "mac_raw_sha256": before["raw_sha256"], "linux_raw_sha256": after["raw_sha256"],
            "mac_label_sha256": before["array_sha256"]["labels"],
            "linux_label_sha256": after["array_sha256"]["labels"],
            "npz_sha256_match": before["npz_sha256"] == after["npz_sha256"],
            "score_hashes": {model: {
                "mac_sha256": before["array_sha256"][model],
                "linux_sha256": after["array_sha256"][model],
                "equal": before["array_sha256"][model] == after["array_sha256"][model],
            } for model in MODELS},
        })
    equal = sum(score["equal"] for row in comparisons for score in row["score_hashes"].values())
    result = {
        "status": "FAILED" if failures else "REQUIRED_IDENTITIES_MATCH",
        "failures": failures, "series": comparisons,
        "score_vectors_equal": equal, "score_vectors_compared": len(comparisons) * len(MODELS),
        "all_score_vectors_byte_identical": equal == 48,
        "scope": "Raw CSV and label hashes must match. Score hashes are compared explicitly; "
                 "platform-dependent floating-point score differences are allowed and retained. "
                 "This is regeneration, not an assumed byte-identical-input replay.",
        "mac_manifest_sha256": digest(MAC_REFERENCE / "manifest.json"),
        "linux_manifest_sha256": digest(INPUTS / "manifest.json"),
        "mac_environment": mac["environment"], "linux_environment": linux["environment"],
    }
    write_json(output / "input-identity-comparison.json", result)
    require(not failures, "External input identities differ; see input-identity-comparison.json")
    return result


def main():
    # This check precedes mkdir, receipt writes, downloads, or subprocesses.
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("CI-only reproduction: GITHUB_ACTIONS must be exactly true; no changes made")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    require(run_id.isdigit(), "GITHUB_RUN_ID must be a numeric Actions run ID")
    require(sys.platform == "linux", "This reproduction is restricted to Linux")
    output = ROOT / "artifacts/reproductions" / f"linux-saturation-{run_id}"
    require(not output.exists(), f"Refusing to replace a previous reproduction: {output}")
    output.mkdir(parents=True)
    terminal = {"status": "RUNNING", "started_utc": utc(), "run_id": run_id,
                "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "stage": "setup",
                "protocol_sha256": None, "arrays_uploaded": False}
    write_json(output / "terminal.json", terminal)
    commands = []
    moved_reference = False

    def execute(stage, arguments):
        terminal["stage"] = stage
        write_json(output / "terminal.json", terminal)
        record = {"stage": stage, "argv": [sys.executable, *arguments], "started_utc": utc()}
        commands.append(record)
        write_json(output / "commands.json", commands)
        start = time.perf_counter()
        try:
            completed = subprocess.run(record["argv"], cwd=ROOT, check=True)
            record["returncode"] = completed.returncode
        except subprocess.CalledProcessError as error:
            record["returncode"] = error.returncode
            raise
        finally:
            record.update(ended_utc=utc(), seconds=time.perf_counter() - start)
            write_json(output / "commands.json", commands)

    def interrupted(signum, _frame):
        raise InterruptedError(f"Received signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        require(sys.version_info[:2] == (3, 12), "Python 3.12 is required")
        actual_versions = {name: importlib.metadata.version(name) for name in VERSIONS}
        require(actual_versions == VERSIONS, f"Dependency version mismatch: {actual_versions}")
        require(INPUTS.is_dir(), "Tracked Mac reference receipts are missing")
        require(not MAC_REFERENCE.exists(), "Mac reference staging path already exists")
        require(not (ROOT / "cache/saturation-external").exists(), "Expected a fresh external input cache")
        mac_selection = read_json(INPUTS / "selection.json")
        for relative, expected in mac_selection["source_sha256"].items():
            require(digest(ROOT / relative) == expected, f"Frozen input source drift: {relative}")
        source_paths = [Path(__file__).resolve(), WORKFLOW, LICENSE_NOTE,
                        ROOT / "experiments/fetch_saturation_external.py",
                        ROOT / "experiments/benchmark_saturation.py"]
        source_hashes = {str(path.relative_to(ROOT)): digest(path) for path in source_paths}
        write_json(output / "reproduction-environment.json", {
            "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "machine": platform.machine(), "packages": actual_versions,
            "installed_packages": dict(sorted((package.metadata["Name"], package.version)
                                              for package in importlib.metadata.distributions())),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "actions": {key: os.environ.get(key) for key in (
                "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "GITHUB_REF",
                "GITHUB_REPOSITORY", "RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion")},
            "thread_environment": {key: os.environ.get(key) for key in (
                "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS")},
            "source_sha256": source_hashes,
        })
        scripts = output / "scripts"
        scripts.mkdir()
        for path in source_paths:
            shutil.copy2(path, scripts / path.name)
        shutil.copy2(LICENSE_NOTE, output / "ATTRIBUTION.md")
        MAC_REFERENCE.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(INPUTS), str(MAC_REFERENCE))
        moved_reference = True
        copy_receipts(MAC_REFERENCE, output / "mac-reference-input-receipts")
        execute("fetch-fast-vus", ["experiments/fast_vus_adapter.py", "--fetch"])
        shutil.copy2(ROOT / ".cache/fast_vus/source.json", output / "fast-vus-source.json")
        execute("freeze-linux-input-selection", ["experiments/fetch_saturation_external.py", "--freeze"])
        compare_selection(output)
        execute("generate-linux-inputs", ["experiments/fetch_saturation_external.py", "--generate"])
        copy_receipts(INPUTS, output / "linux-input-receipts")
        identity = compare_inputs(output)
        terminal["score_vectors_equal"] = identity["score_vectors_equal"]
        benchmark = output / "benchmark"
        execute("freeze-external-protocol", ["experiments/benchmark_saturation.py", "freeze",
                                            str(benchmark), "--phase", "external"])
        protocol = read_json(benchmark / "protocol.json")
        require(protocol["phase"] == "external" and protocol["cases"] == 144
                and protocol["series"] == 12 and len(protocol["families"]) == 9
                and protocol["models"] == MODELS and protocol["method_ids"] == METHODS
                and protocol["widths"] == [30, 100, 300] and protocol["repetitions"] == 3,
                "Frozen protocol does not cover the complete declared experiment")
        frozen_hash = digest(benchmark / "protocol.json")
        terminal["protocol_sha256"] = frozen_hash
        write_json(output / "frozen-protocol-receipt.json", {
            "protocol_sha256": frozen_hash, "frozen_utc": utc(), "cases": 144,
            "methods": 9, "repetitions": 3, "source_sha256": source_hashes,
            "timing_environment": "Dedicated GitHub Actions job; sequential steps and method calls; "
                                  "one compute thread. Hosted background load is not controlled.",
        })
        execute("run-external-protocol", ["experiments/benchmark_saturation.py", "run", str(benchmark),
                                         "--protocol-sha256", frozen_hash, "--phase", "external"])
        require(digest(benchmark / "protocol.json") == frozen_hash, "Frozen protocol changed")
        report = read_json(benchmark / "report.json")
        require(report["protocol_sha256"] == frozen_hash and report["cases"] == 144,
                "Final report does not match the frozen complete workload")
        for relative, expected in source_hashes.items():
            require(digest(ROOT / relative) == expected, f"Reproduction source changed: {relative}")
        terminal.update(status="COMPLETED", stage="completed", parity_pass=report["parity_pass"],
                        primary_decision=report["primary_decision"])
    except BaseException as error:
        terminal.update(status="FAILED", error_type=type(error).__name__, error=str(error))
        (output / "error.txt").write_text(traceback.format_exc())
        raise
    finally:
        # Keep partial JSON receipts and benchmark JSONL even if acquisition or timing failed.
        try:
            if moved_reference:
                copy_receipts(INPUTS, output / "linux-input-receipts")
            if LICENSE_NOTE.is_file():
                shutil.copy2(LICENSE_NOTE, output / "ATTRIBUTION.md")
            receipt_paths = sorted(path for path in output.rglob("*") if path.is_file()
                                   and path.name not in ("artifact-files.json", "terminal.json"))
            allowed = {".json", ".jsonl", ".md", ".txt", ".py", ".yml"}
            require(all(path.suffix in allowed and not path.is_symlink() for path in receipt_paths),
                    "Unexpected non-metadata file in upload directory")
            write_json(output / "artifact-files.json", {
                "raw_or_array_files_included": False,
                "files": {str(path.relative_to(output)): digest(path) for path in receipt_paths},
            })
        except BaseException as error:
            terminal.update(status="FAILED", finalization_error=f"{type(error).__name__}: {error}")
            raise
        finally:
            terminal["ended_utc"] = utc()
            write_json(output / "terminal.json", terminal)
            print(json.dumps(terminal, indent=2), flush=True)


if __name__ == "__main__":
    main()
