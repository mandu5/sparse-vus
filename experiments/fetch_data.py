"""Fetch public pinned score archives; no model inference or paid service."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"
MANIFEST = ROOT / "experiments/data_manifest.json"


def fetch(item):
    name, url, md5 = item
    target = CACHE / name
    if not target.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research reproduction)"})
        with urllib.request.urlopen(req, timeout=120) as response, target.with_suffix(target.suffix + ".part").open("wb") as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        target.with_suffix(target.suffix + ".part").replace(target)
    digest_md5 = hashlib.md5()
    digest_sha = hashlib.sha256()
    with target.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest_md5.update(chunk)
            digest_sha.update(chunk)
    if md5 and digest_md5.hexdigest() != md5:
        raise RuntimeError(f"Checksum mismatch: {name}")
    locks = ROOT / "experiments/data_hashes.json"
    if locks.exists():
        expected = json.loads(locks.read_text())["files"].get(name)
        if expected and digest_sha.hexdigest() != expected:
            raise RuntimeError(f"Source content changed from the recorded experiment: {name}")
    if name.endswith(".zip"):
        with zipfile.ZipFile(target) as archive:
            bad = archive.testzip()
            if bad:
                raise RuntimeError(f"ZIP CRC mismatch: {name}/{bad}")
    result = {"file": name, "url": url, "bytes": target.stat().st_size,
              "md5": digest_md5.hexdigest(), "sha256": digest_sha.hexdigest()}
    print(json.dumps(result), flush=True)
    return result


if __name__ == "__main__":
    manifest = json.loads(MANIFEST.read_text())
    CACHE.mkdir(exist_ok=True)
    items = [(x["file"], f"https://rdr.kuleuven.be/api/access/datafile/{x['id']}", x["md5"]) for x in manifest["models"]]
    items += [("TSB-AD-U.zip", manifest["labels"]["url"], None),
              ("TSB-AD-U-Eva.csv", manifest["labels"]["evaluation_list"], None),
              ("score-archive-README.txt", "https://rdr.kuleuven.be/api/access/datafile/337896", "a7cc285e002a8dccfde7b89cf45475ad")]
    with ThreadPoolExecutor(max_workers=3) as pool:
        receipts = list(pool.map(fetch, items))
    report = {"completed_utc": datetime.now(timezone.utc).isoformat(),
              "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(), "files": receipts}
    (ROOT / "artifacts/download_receipt.json").write_text(json.dumps(report, indent=2))
