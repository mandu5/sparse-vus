"""Small, independently constructed evidence for integrity regression tests."""
import hashlib
import json
import zipfile

import numpy as np


def write(path, value):
    path.write_text(json.dumps(value))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root):
    base = root / "artifacts/pvldb-research-20261024"
    folder = base / "full-precision"
    cache = root / ".cache/pvldb-full-precision-20261024"
    folder.mkdir(parents=True); cache.mkdir(parents=True)
    (base / "development").mkdir()
    write(base / "development/protocol.json", {"cases": []})
    (root / "cache").mkdir()
    raw = b"Data,Label\n10,0\n20,1\n30,0\n"
    with zipfile.ZipFile(root / "cache/TSB-AD-U.zip", "w") as z:
        z.writestr("one.csv", raw)
    x = np.array([10., 20., 30.]); y = np.array([0, 1, 0], np.int8)
    s = np.array([[.1, .9, .2], [.2, .8, .3]])
    case = {"series": "one", "family": "NAB", "n": 3, "member": "one.csv",
            "positive_points": 1, "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "observation_label_identity": hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest(),
            "raw_recording_previously_measured_by_name": False}
    p = {"cases": [case], "models": ["m0", "m1"], "collections": ["NAB"],
         "widths": [30], "primary_width": 30, "methods": ["released", "stream"],
         "repetitions": 2, "orders": [["released", "stream"], ["stream", "released"]],
         "source_sha256": {}, "archive_sha256": sha(root / "cache/TSB-AD-U.zip")}
    write(folder / "protocol.json", p)
    np.savez(cache / "one.npz", observations=x, labels=y, scores=s)
    c = {**case, "file": "one.npz", "bytes": (cache / "one.npz").stat().st_size,
         "npz_sha256": sha(cache / "one.npz"), "score_sha256": hashlib.sha256(s.tobytes()).hexdigest(),
         "models": {m: {"distinct": 3} for m in p["models"]}}
    write(folder / "inputs.json", {"status": "COMPLETE", "protocol_sha256": sha(folder / "protocol.json"), "series": [c]})
    rows, workflows = [], []
    for t in range(2):
        for m, sec in [("released", 2.), ("stream", 1.)]:
            rows.append({"series": "one", "family": "NAB", "width": 30, "method": m,
                         "trial": t, "seconds": sec*(t+1), "values": [.8, .5], "winners": [0], "max_error": 0.})
            workflows.append({"family": "NAB", "method": m, "trial": t, "seconds": 5*sec*(t+1),
                              "decisions": [{"series": "one", "values": [.8, .5], "winners": [0]}]})
    for name, data in [("records", rows), ("workflows", workflows)]:
        (folder / f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in data))
    summary = {"geometric_speedup": 2., "ci95": [2., 2.], "ci_familywise95_3collections": [2., 2.],
               "case_wins": 1, "cases": 1, "minimum_speedup": 2., "maximum_speedup": 2.}
    report = {name+"_sha256": sha(folder / (name+(".jsonl" if name in ["records", "workflows"] else ".json")))
              for name in ["protocol", "inputs", "records", "workflows"]}
    report.update({"status": "COMPLETE", "series": 1, "score_vectors": 2, "scalar_error_max": 0.,
                   "all_workflow_winner_sets_agree": True, "distinct_values": {"min": 3, "max": 3},
                   "case_paired_summaries": {"NAB_L30": {"released": summary}},
                   "workflows": {"NAB": {"median_seconds": {"released": 15., "stream": 7.5},
                        "all_seconds": {"released": [10., 20.], "stream": [5., 10.]},
                        "baseline_over_stream": {"released": 2., "stream": 1.},
                        "paired_trial_uncertainty": {"released": {**summary, "cases": 2, "case_wins": 2}}}}})
    write(folder / "report.json", report)
    write(folder / "run-start.json", {"protocol_sha256": report["protocol_sha256"], "inputs_sha256": report["inputs_sha256"]})
    write(folder / "run-complete.json", {"status": "COMPLETE", "records_sha256": report["records_sha256"], "workflows_sha256": report["workflows_sha256"]})
    return folder, cache


def rebind_inputs(folder):
    # Model an attacker or accidental rewrite which updates downstream hashes,
    # but must not be permitted to change the frozen cohort or its identity.
    for name in ["report.json", "run-start.json"]:
        d = json.loads((folder/name).read_text()); d["inputs_sha256"] = sha(folder/"inputs.json"); write(folder/name, d)
