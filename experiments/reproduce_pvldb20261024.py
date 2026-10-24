"""Fresh one-command reproduction in a new directory; no frozen outputs replaced.

Run with the project's accelerated/research dependencies installed. By default
the primary study, supplementary comparison and independent audit all execute.
The public raw archive is downloaded if an existing copy is not provided.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path("artifacts/pvldb-research-20261024")
ARCHIVE_SHA = "0c47020d3423723c70773736dbd800369f2b487328becbf339450d1ae5020961"
SCRIPTS = ["pvldb_full_precision.py", "pvldb_supplement.py", "audit_pvldb20261024.py",
           "audit_pvldb_supplement.py", "fast_vus_adapter.py", "benchopt_vus_adapter.py"]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while block := f.read(1 << 20): h.update(block)
    return h.hexdigest()


def same_design(reference, actual):
    for key in ("cases", "models", "methods", "orders", "widths", "primary_width",
                "parity_atol", "winner_tie_atol", "archive_sha256", "source_sha256"):
        if reference[key] != actual[key]: raise ValueError(f"design drift: {key}")


def same_supplement_design(reference, actual):
    # Only fresh creation/parent identities may differ. All scientific contracts
    # and supplement-specific source hashes must remain identical.
    fresh = {"created_utc", "primary_protocol_sha256", "inputs_sha256"}
    if {k: v for k, v in reference.items() if k not in fresh} != {k: v for k, v in actual.items() if k not in fresh}:
        raise ValueError("supplement design drift")


def prepare_workspace(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copytree(ROOT/"src", destination/"src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.nbc", "*.nbi"))
    (destination/"experiments").mkdir()
    for name in SCRIPTS: shutil.copy2(ROOT/"experiments"/name, destination/"experiments"/name)
    for relative in (Path("artifacts/selected_series.json"), EVIDENCE/"development/protocol.json"):
        target=destination/relative; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT/relative,target)
    return destination


def run(args):
    dest = prepare_workspace(args.output)
    archive = args.archive
    if archive is None and (ROOT/"cache/TSB-AD-U.zip").exists(): archive=ROOT/"cache/TSB-AD-U.zip"
    (dest/"cache").mkdir()
    target=dest/"cache/TSB-AD-U.zip"
    if archive is None:
        subprocess.run(["curl", "-fL", "--retry", "2", "--max-time", "900",
                        "https://www.thedatum.org/datasets/TSB-AD-U.zip", "-o", str(target)], check=True)
    else: target.symlink_to(Path(archive).resolve())
    if sha(target) != ARCHIVE_SHA: raise ValueError("raw archive identity mismatch")
    env=dict(os.environ)
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"): env[key]="1"
    env["PYTHONPATH"]=str(dest/"src")
    def call(name, *arguments):
        subprocess.run([sys.executable,str(dest/"experiments"/name),*map(str,arguments)],cwd=dest,env=env,check=True)
    for adapter in ("fast_vus_adapter.py", "benchopt_vus_adapter.py"): call(adapter,"--fetch")
    call("pvldb_full_precision.py","freeze")
    original=json.loads((ROOT/EVIDENCE/"full-precision/protocol.json").read_text())
    replica=json.loads((dest/EVIDENCE/"full-precision/protocol.json").read_text())
    same_design(original,replica)
    hardware = platform.processor()
    if platform.system()=="Darwin":
        hardware=subprocess.check_output(["sysctl","-n","machdep.cpu.brand_string"],text=True).strip()
    elif Path("/proc/cpuinfo").exists():
        hardware=next((line.split(":",1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")),hardware)
    receipt={"status":"RUNNING","started_utc":datetime.now(timezone.utc).isoformat(),
             "platform":platform.platform(),"machine":platform.machine(),"processor":hardware,
             "logical_cpus":os.cpu_count(),"python":sys.version,
             "packages":{p:importlib.metadata.version(p) for p in ("numpy","numba","pandas","scikit-learn","scipy")},
             "original_protocol_sha256":sha(ROOT/EVIDENCE/"full-precision/protocol.json"),
             "replica_protocol_sha256":sha(dest/EVIDENCE/"full-precision/protocol.json"),
             "host_scope":args.host_note,"fresh_scores":True,
             "claim":"Same frozen data/model/method design executed afresh; generated scores can have platform-dependent floating-point differences."}
    receipt_file=dest/EVIDENCE/"reproduction-start.json";receipt_file.write_text(json.dumps(receipt,indent=2)+"\n")
    call("pvldb_full_precision.py","generate")
    call("pvldb_full_precision.py","run")
    call("audit_pvldb20261024.py","--root",dest,"--output",dest/EVIDENCE/"full-precision/independent-audit.json")
    if not args.primary_only:
        call("pvldb_supplement.py","freeze")
        original_supplement=json.loads((ROOT/EVIDENCE/"supplement/protocol.json").read_text())
        new_supplement=json.loads((dest/EVIDENCE/"supplement/protocol.json").read_text())
        same_supplement_design(original_supplement,new_supplement)
        if new_supplement["primary_protocol_sha256"] != sha(dest/EVIDENCE/"full-precision/protocol.json") or new_supplement["inputs_sha256"] != sha(dest/EVIDENCE/"full-precision/inputs.json"):
            raise ValueError("replica supplement parent binding")
        call("pvldb_supplement.py","run")
        call("audit_pvldb_supplement.py","--root",dest,"--output",dest/EVIDENCE/"supplement/independent-report.json")
        receipt["supplement_protocol_sha256"]=sha(dest/EVIDENCE/"supplement/protocol.json")
        receipt["supplement_report_sha256"]=sha(dest/EVIDENCE/"supplement/independent-report.json")
    receipt["status"]="COMPLETE";receipt["completed_utc"]=datetime.now(timezone.utc).isoformat()
    receipt["primary_report_sha256"]=sha(dest/EVIDENCE/"full-precision/report.json")
    receipt["primary_audit_sha256"]=sha(dest/EVIDENCE/"full-precision/independent-audit.json")
    (dest/EVIDENCE/"reproduction-complete.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"status":"COMPLETE","evidence":str(dest/EVIDENCE)},indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--archive",type=Path);parser.add_argument("--primary-only",action="store_true")
    parser.add_argument("--host-note",default="Serial local reproduction; other host workloads are not automatically controlled.")
    run(parser.parse_args())
