"""Execute unmodified external fast-VUS (PR only) from a verified cache.

The upstream default is the 250-threshold approximation. Set max_samples to
the input length for the full-threshold target. Timings must identify that
this baseline returns only PR while sparse_vus currently returns ROC and PR.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/fast_vus"
REVISION = "1bae859f8a4fa4467b215ba4e8e5efb1b16e6b00"
SOURCE_HASH = "15b7afb94da0e1f1b1c408fe44b937d910935c19f8eb76f42ae6719f9cfcb52b"
LICENSE_HASH = "3b19b00e8d74e9e8f3db69d8407da5b5dd2078f3bf9c57ff47ff0fb9551db282"
BASE_URL = f"https://raw.githubusercontent.com/tomlouisklein/fast-VUS/{REVISION}"
SOURCE_URL = f"{BASE_URL}/fast_vus.py"


def source_receipt():
    """Return provenance and comparison scope without writing artifacts."""
    return {
        "repository": "https://github.com/tomlouisklein/fast-VUS",
        "revision": REVISION,
        "upstream_commit_date": "2026-10-16T10:36:48Z",
        "upstream_first_commit": "189de211f8821c3027110af2d00593e603c11cfc",
        "upstream_first_commit_date": "2026-10-12T11:03:32Z",
        "source_url": SOURCE_URL,
        "source_sha256": SOURCE_HASH,
        "license": "Apache-2.0",
        "license_sha256": LICENSE_HASH,
        "adapter": "Full upstream module imported and vus_pr called unchanged.",
        "output": "PR scalar only; no ROC output.",
        "threshold_contract": "250 by default; max_samples=len(scores) includes all score thresholds.",
        "timing_contract": "Includes upstream validation, global and support sorting, ramp construction, and all width integrals; module import excluded after warm-up.",
    }


def fetch_reference():
    """Fetch source and license into ignored cache and verify exact bytes."""
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, expected in [("fast_vus.py", SOURCE_HASH), ("LICENSE", LICENSE_HASH)]:
        path = CACHE / name
        if not path.exists():
            temporary = path.with_suffix(path.suffix + ".download")
            try:
                subprocess.run(
                    ["curl", "-fsSL", "--retry", "2", "--max-time", "60",
                     f"{BASE_URL}/{name}", "-o", str(temporary)],
                    check=True,
                )
                if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
                    raise ValueError(f"fast-VUS {name} hash mismatch")
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"fast-VUS {name} hash mismatch")
    (CACHE / "source.json").write_text(json.dumps(source_receipt(), indent=2) + "\n")
    return CACHE / "fast_vus.py"


@lru_cache(maxsize=1)
def _load_module():
    path = CACHE / "fast_vus.py"
    if not path.exists():
        raise FileNotFoundError("Run python experiments/fast_vus_adapter.py --fetch first.")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError("fast-VUS metric source hash mismatch")
    spec = importlib.util.spec_from_file_location("pinned_external_fast_vus", path)
    module = importlib.util.module_from_spec(spec)
    # Compile the verified bytes, preventing a stale .pyc or reread from
    # silently executing bytes different from those just checked.
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def fast_vus_pr(labels, scores, max_buffer, max_samples=250):
    """Return upstream PR only, preserving its original threshold parameter."""
    return _load_module().vus_pr(labels, scores, max_buffer, thre=max_samples)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        print(fetch_reference())
