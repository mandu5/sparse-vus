"""Download only score members of the public ZIPs, using HTTP byte ranges.

Model predictions are unused and can contain pickle files. This script never
downloads or deserializes them. Every selected NPY member passes ZIP CRC, and
its SHA-256 is recorded. Archive-level MD5 remains source metadata, not a
claimed verification of bytes that were not downloaded.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import zipfile
import time

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"
MANIFEST = ROOT / "experiments/data_manifest.json"


def get_range(url, start, end):
    request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}", "User-Agent": "Mozilla/5.0 (research reproduction)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                if response.status != 206 or response.headers.get("Content-Range", "").split("/")[0] != f"bytes {start}-{end}":
                    raise RuntimeError("Server did not honor the exact byte range")
                data = response.read()
                if len(data) != end - start + 1:
                    raise RuntimeError("Incomplete HTTP byte range")
                return data, response.url
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def fetch_model(model):
    CACHE.mkdir(parents=True, exist_ok=True)
    api = f"https://rdr.kuleuven.be/api/access/datafile/{model['id']}"
    total = model["bytes"]
    tail, direct_url = get_range(api, max(0, total - 262144), total - 1)
    target = CACHE / (model["name"] + ".score-range.zip")
    with target.open("wb") as stream:
        stream.seek(total - len(tail))
        stream.write(tail)
    with zipfile.ZipFile(target) as archive:
        members = [x for x in archive.infolist() if x.filename.startswith("scores/") and x.filename.endswith(".npy")]
    # Scores are one contiguous block in this archive. Fetch complete local
    # records plus central directory; all members remain CRC-checkable.
    start = min(x.header_offset for x in members)
    stop = total - len(tail)
    blocks = [(a, min(a + 4 * 1024 * 1024 - 1, stop - 1)) for a in range(start, stop, 4 * 1024 * 1024)]
    fd = os.open(target, os.O_WRONLY)
    def block(pair):
        a, b = pair
        data, _ = get_range(direct_url, a, b)
        written = os.pwrite(fd, data, a)
        if written != len(data):
            raise RuntimeError("Short local write")
        return {"start": a, "end": b, "sha256": hashlib.sha256(data).hexdigest()}
    try:
        with ThreadPoolExecutor(max_workers=12) as pool:
            chunks = list(pool.map(block, blocks))
    finally:
        os.close(fd)
    member_receipts = []
    with zipfile.ZipFile(target) as archive:
        for member in members:
            data = archive.read(member)  # zipfile verifies the CRC here.
            member_receipts.append({"path": member.filename, "bytes": len(data), "crc32": member.CRC,
                                    "sha256": hashlib.sha256(data).hexdigest()})
    locks = ROOT / "experiments/data_hashes.json"
    if locks.exists():
        expected = json.loads(locks.read_text())["score_member_manifests"][model["name"]]
        items = sorted((x["path"], x["sha256"]) for x in member_receipts)
        actual = hashlib.sha256(json.dumps(items, separators=(",", ":")).encode()).hexdigest()
        if actual != expected:
            raise RuntimeError("Released score bytes changed from the recorded experiment")
    receipt = {"model": model, "download_mode": "HTTP ranges, score members only",
               "source_url": api, "downloaded_bytes": total - start,
               "archive_md5_verified": False, "selected_members_crc_verified": True,
               "ranges": chunks, "members": member_receipts}
    (ROOT / "artifacts" / (model["name"] + "-download.json")).write_text(json.dumps(receipt, indent=2))
    print(json.dumps({"model": model["name"], "score_members": len(members), "downloaded_bytes": total - start}), flush=True)
    return receipt


if __name__ == "__main__":
    manifest = json.loads(MANIFEST.read_text())
    # Download one model at a time; 12 range workers keep individual transfers
    # bounded, while reducing wall time on this server's per-request throttle.
    results = [fetch_model(model) for model in manifest["models"]]
    from fetch_data import fetch
    labels = fetch(("TSB-AD-U.zip", manifest["labels"]["url"], None))
    evaluation_list = fetch(("TSB-AD-U-Eva.csv", manifest["labels"]["evaluation_list"], None))
    readme = fetch(("score-archive-README.txt", "https://rdr.kuleuven.be/api/access/datafile/337896", "a7cc285e002a8dccfde7b89cf45475ad"))
    report = {"completed_utc": datetime.now(timezone.utc).isoformat(),
              "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
              "score_download_receipts": [model["name"] + "-download.json" for model in manifest["models"]],
              "labels": labels, "evaluation_list": evaluation_list, "readme": readme}
    (ROOT / "artifacts/download_receipt.json").write_text(json.dumps(report, indent=2))
