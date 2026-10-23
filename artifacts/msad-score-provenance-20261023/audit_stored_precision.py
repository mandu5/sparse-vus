"""Audit source text precision only; no metric computation or score alteration."""
import hashlib
import json
from pathlib import Path
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MANIFEST_SHA = "5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59"
AUDIT_SHA = "cf9219a90121e188108bcfe6b6ca970d5b5de89c5680401fe8baff0badd0ef06"
def sha(data): return hashlib.sha256(data).hexdigest()

manifest_bytes = (ROOT / "artifacts/msad-corpus-20261023/manifest.json").read_bytes()
audit_bytes = (ROOT / "artifacts/msad-corpus-20261023/independent-input-audit.json").read_bytes()
assert sha(manifest_bytes) == MANIFEST_SHA and sha(audit_bytes) == AUDIT_SHA
assert json.loads(audit_bytes)["status"] == "PASS_INDEPENDENT_STORED_TEXT_TO_ARRAY_IDENTITIES"
manifest = json.loads(manifest_bytes)
results = {m: {"files": 0, "values": 0, "at_most_two_decimal_files": 0,
               "outside_two_decimal_examples": []} for m in manifest["models"]}
outside_alphabet = re.compile(rb"[^0-9.\-+\r\n \t]")
more_decimals = re.compile(rb"\.[0-9]{3}")
for row in manifest["series"]:
    for model in manifest["models"]:
        member = row["scores"][model]
        path = ROOT / ".cache/msad-corpus-20261023/members" / (sha(member["path"].encode()) + ".data")
        data = path.read_bytes()
        assert len(data) == member["bytes"] and sha(data) == member["sha256"]
        # The hash-bound prior audit independently parsed every complete line
        # as a finite float. These two lexical checks therefore suffice to
        # distinguish integer/one-/two-decimal tokens from finer/scientific text.
        fits = outside_alphabet.search(data) is None and more_decimals.search(data) is None
        result = results[model]
        result["files"] += 1
        result["values"] += row["n"]
        result["at_most_two_decimal_files"] += int(fits)
        if not fits:
            result["outside_two_decimal_examples"].append(row["series"])
receipt = {"completed_utc": datetime.now(timezone.utc).isoformat(),
           "manifest_sha256": MANIFEST_SHA, "input_audit_sha256": AUDIT_SHA,
           "source_sha256": sha(Path(__file__).read_bytes()),
           "models": results, "score_files": sum(v["files"] for v in results.values()),
           "score_values": sum(v["values"] for v in results.values()),
           "scope": "Actual stored decimal text; does not infer the original generating script or unavailable full precision.",
           "metric_outcomes_computed": False}
with (OUT / "stored-precision-audit.json").open("x") as stream:
    json.dump(receipt, stream, indent=2); stream.write("\n")
print(json.dumps(receipt, indent=2))
