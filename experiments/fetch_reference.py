"""Download the unmodified pinned numerical reference into ignored cache."""
from pathlib import Path
import hashlib
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "https://raw.githubusercontent.com/thedatumorg/VUS/467bace0c103f5c2bdb4900306d82939bcac8ff9/vus/utils/metrics.py"
SHA = "bd547c9746fc1b9bbce2895e20cb156f97d23365d5dce8c2a3fab90622ccdced"

if __name__ == "__main__":
    data = urllib.request.urlopen(URL, timeout=60).read()
    if hashlib.sha256(data).hexdigest() != SHA:
        raise RuntimeError("Pinned reference checksum mismatch")
    (ROOT / "cache").mkdir(exist_ok=True)
    (ROOT / "cache/official_metrics.py").write_bytes(data)
    print(SHA)
