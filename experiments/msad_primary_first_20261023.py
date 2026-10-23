"""Order-only wrapper: unchanged frozen MSAD requests, primary widths first.

The separate scheduler receipt binds this file before it executes any corpus
metric. Existing durable keys are skipped by the unchanged study runner.
"""
import json
from pathlib import Path
import sys

import msad_sampling_study as study


def reconstruct():
    sys.argv = [str(Path(study.__file__)), "report"]
    study.main()


def main():
    receipt = json.loads((study.OUT / "primary-first-scheduler.json").read_text())
    if study.sha256_file(__file__) != receipt["wrapper_sha256"]:
        raise ValueError("Scheduler source hash mismatch")
    if study.sha256_file(study.OUT / "source_manifest.json") != receipt["source_manifest_sha256"]:
        raise ValueError("Frozen study source manifest changed")
    protocol = json.loads((study.OUT / "protocol.json").read_text())
    manifest = json.loads((study.ROOT / protocol["acquisition_manifest"]).read_text())
    sources = study.freeze(protocol, manifest["series"])
    primary_only = dict(protocol, widths=[protocol["primary_width"]])
    study.run_phase("numerical", primary_only, manifest["series"], sources)
    print("PRIMARY_NUMERICAL_COMPLETE", flush=True)
    reconstruct()
    study.run_phase("validation", protocol, manifest["series"], sources)
    print("PRIMARY_EXACT_VALIDATION_COMPLETE", flush=True)
    reconstruct()
    study.run_phase("numerical", protocol, manifest["series"], sources)
    print("ALL_NUMERICAL_COMPLETE", flush=True)
    reconstruct()


if __name__ == "__main__":
    # The numerical scheduler uses the same thread cap as the original CLI.
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        study.os.environ[name] = "1"
    main()
