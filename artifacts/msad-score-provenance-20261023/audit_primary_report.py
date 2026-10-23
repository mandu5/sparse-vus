"""Independent primary effect/parity recomputation, without study analysis imports."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
def sha(data): return hashlib.sha256(data).hexdigest()
manifest_path = ROOT / "artifacts/msad-corpus-20261023/manifest.json"
manifest_bytes = manifest_path.read_bytes()
assert sha(manifest_bytes) == "5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59"
manifest = json.loads(manifest_bytes)
overlap_path = OUT / "one-point-overlap-audit.json"
overlap = set(json.loads(overlap_path.read_text())["selected_with_joint_one_point_matches"])
log = ROOT / "artifacts/msad-sampling-20261023/records.jsonl"
data = log.read_bytes()
# The sensitivity pass may append concurrently. Audit an exact complete-line
# prefix and retain byte count/hash so it can be recovered from the final log.
data = data[:data.rfind(b"\n")+1]
index = {}
for line in data.splitlines():
    r = json.loads(line)
    if r.get("width") != 30:
        continue
    phase, method = r.get("phase"), r.get("method")
    keep = phase == "numerical" and (method in ("radix_exact", "klein250") or
                                    method == "matched_sampled" and r.get("thresholds") == 250)
    keep |= phase == "validation" and method in ("dense_exact", "klein_exact")
    if keep:
        key = (r["series"], r["model"], method)
        assert key not in index and r["status"] == "ok"
        index[key] = r
rows, parity = [], {m: [] for m in ("klein250", "dense_exact", "klein_exact")}
for row in manifest["series"]:
    name = row["series"]
    exact = {m: index[(name, m, "radix_exact")]["value"] for m in manifest["models"]}
    sampled = {m: index[(name, m, "matched_sampled")]["value"] for m in manifest["models"]}
    best_sampled = max(sampled.values())
    winners = [m for m in manifest["models"] if best_sampled-sampled[m] <= 1e-10]
    regret = max(exact.values()) - max(exact[m] for m in winners)
    errors = [sampled[m]-exact[m] for m in manifest["models"]]
    rows.append({"series": name, "family": row["family"], "best_case_regret": regret,
                 "sampled_winner_set": winners, "minimum_signed_error": min(errors),
                 "maximum_signed_error": max(errors), "joint_one_point_prior_overlap": name in overlap})
    for model in manifest["models"]:
        for method in parity:
            r = index.get((name, model, method))
            if r is not None:
                reference = sampled[model] if method == "klein250" else exact[model]
                parity[method].append(abs(r["value"]-reference))
assert len(parity["klein250"]) == 1536
assert len(parity["dense_exact"]) == len(parity["klein_exact"]) == 360
assert all(max(v) <= 2e-10 for v in parity.values())
def summary(group):
    affected = [r for r in group if r["best_case_regret"] >= .01]
    return {"series": len(group), "practical_best_case_regret_cases": len(affected),
            "practical_fraction": len(affected)/len(group),
            "affected_families": dict(Counter(r["family"] for r in affected)),
            "maximum_best_case_regret": max(r["best_case_regret"] for r in group),
            "minimum_signed_error": min(r["minimum_signed_error"] for r in group),
            "maximum_signed_error": max(r["maximum_signed_error"] for r in group)}
receipt = {"completed_utc": datetime.now(timezone.utc).isoformat(),
           "manifest_sha256": sha(manifest_bytes), "source_sha256": sha(Path(__file__).read_bytes()),
           "source_log": str(log.relative_to(ROOT)), "source_log_prefix_bytes": len(data),
           "source_log_prefix_sha256": sha(data), "overlap_audit_sha256": sha(overlap_path.read_bytes()),
           "scope": "Independent L30/H250 primary table; post-acquisition overlap subgroup is descriptive, not a replacement primary panel.",
           "primary_fixed_128": summary(rows),
           "bounded_nonmatch_108": summary([r for r in rows if not r["joint_one_point_prior_overlap"]]),
           "joint_overlap_20": summary([r for r in rows if r["joint_one_point_prior_overlap"]]),
           "parity": {m: {"comparisons": len(v), "maximum_error": max(v)} for m,v in parity.items()},
           "rows": rows}
with (OUT / "independent-primary-audit.json").open("x") as stream:
    json.dump(receipt, stream, indent=2); stream.write("\n")
print(json.dumps({k:v for k,v in receipt.items() if k != "rows"}, indent=2))
