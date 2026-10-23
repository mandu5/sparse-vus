"""Post-acquisition overlap diagnostic; never changes frozen selection or scores."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "experiments"))
import fetch_msad_score_corpus as acquisition

manifest_path = ROOT / "artifacts/msad-corpus-20261023/manifest.json"
manifest = json.loads(manifest_path.read_text())
assert acquisition.file_sha(manifest_path) == "5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59"
prior = json.loads((ROOT / "artifacts/msad-corpus-20261023/prior-identity-index.json").read_text())["entries"]
prior_by_name = {(r["source"], r["series"]): r for r in prior}
lengths = {r["n"] for r in manifest["series"]}
labels, observations = defaultdict(set), defaultdict(set)
for r in manifest["series"]:
    labels[r["array_sha256"]["labels"]].add(r["series"])
    for h in r["observation_hashes"]:
        observations[h].add(r["series"])
matches = []
checked = 0

def check(name, source, y, values):
    global checked
    checked += 1
    if len(y)-1 not in lengths:
        return
    for direction, selector in [("drop_first", slice(1, None)), ("drop_last", slice(None, -1))]:
        label_matches = labels.get(acquisition.array_sha(y[selector].astype(np.int8)), set())
        exact, standardized = set(), set()
        for column in range(values.shape[1]):
            v = values[selector, column]
            if not np.isfinite(v).all():
                continue
            h1, h2 = acquisition.observation_hashes(v)
            exact.update(observations.get(h1, set()))
            standardized.update(observations.get(h2, set()))
        for target in sorted(label_matches | exact | standardized):
            matches.append({"prior_source": source, "prior_series": name, "transformation": direction,
                            "selected_series": target, "labels_match": target in label_matches,
                            "observations_exact_match": target in exact,
                            "observations_standardized_match": target in standardized})

selected = json.loads((ROOT / acquisition.PRIOR[0]).read_text())["ordered_series"]
with zipfile.ZipFile(ROOT / "cache/TSB-AD-U.zip") as archive:
    names = {Path(n).stem: n for n in archive.namelist() if n.endswith(".csv")}
    for name in selected:
        raw = archive.read(names[name])
        assert acquisition.sha(raw) == prior_by_name[("prior-tsb-ad", name)]["raw_sha256"]
        frame = pd.read_csv(io.BytesIO(raw))
        check(name, "prior-tsb-ad", frame["Label"].to_numpy(np.int8),
              frame.drop(columns=["Label"]).to_numpy(np.float64))
external = json.loads((ROOT / acquisition.PRIOR[1]).read_text())
for row in external["series"]:
    with np.load(ROOT / row["npz_path"], allow_pickle=False) as data:
        y = data["labels"].astype(np.int8)
    if len(y)-1 not in lengths:
        checked += 1
        continue
    raw = acquisition.external_raw_path(row).read_bytes()
    assert acquisition.sha(raw) == prior_by_name[("prior-mtsbench", row["series"])]["raw_sha256"]
    frame = pd.read_csv(io.BytesIO(raw))
    check(row["series"], "prior-mtsbench", y,
          frame[row["preprocessing"]["feature_columns"]].to_numpy(np.float64))
joint = {r["selected_series"] for r in matches if r["labels_match"] and
         (r["observations_exact_match"] or r["observations_standardized_match"])}
receipt = {"completed_utc": datetime.now(timezone.utc).isoformat(),
           "manifest_sha256": acquisition.file_sha(manifest_path),
           "source_sha256": acquisition.file_sha(Path(__file__)),
           "acquisition_source_sha256": acquisition.file_sha(ROOT / "experiments/fetch_msad_score_corpus.py"),
           "prior_inputs_checked": checked, "selected_series": 128,
           "selected_with_joint_one_point_matches": sorted(joint),
           "matches": matches,
           "scope": "Post-acquisition drop-first/drop-last diagnostic against prior350 TSB-AD and12 mTSBench; not a full cropped-recording or transformed-source overlap detector.",
           "selection_modified": False, "metric_outcomes_computed": False}
with (OUT / "one-point-overlap-audit.json").open("x") as stream:
    json.dump(receipt, stream, indent=2); stream.write("\n")
print(json.dumps({"prior_inputs_checked": checked, "joint_selected_count": len(joint),
                  "matches": len(matches), "joint_selected_series": sorted(joint)}, indent=2))
