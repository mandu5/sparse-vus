import importlib.util
import json
from pathlib import Path
import sys

import pytest

from pvldb_audit_fixture import fixture, sha, write


def module():
    directory = Path(__file__).resolve().parents[1]/"experiments"
    sys.path.insert(0, str(directory))
    spec = importlib.util.spec_from_file_location("supplement_audit", directory/"audit_pvldb_supplement.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def supplement_fixture(root):
    primary, _ = fixture(root)
    folder = primary.parent/"supplement"; folder.mkdir()
    methods = ["stream", "klein_exact", "benchopt_pair", "radix_pair", "klein250", "klein1000"]
    p = {"primary_protocol_sha256": sha(primary/"protocol.json"), "inputs_sha256": sha(primary/"inputs.json"),
         "source_sha256": {}, "methods": methods, "width": 30, "repetitions": 2, "regret_threshold": .01}
    write(folder/"protocol.json", p)
    rows, workflows = [], []
    for t in range(2):
        for i, method in enumerate(methods):
            approx = method == "klein250"
            values = [.4, .6] if approx else [.8, .5]
            selected = [1] if approx else [0]
            selection = {"selected": selected, "exact_winners": [0], "minimum_regret": .3 if approx else 0.,
                         "maximum_regret": .3 if approx else 0., "identical_winner_set": not approx}
            pair = method in ("benchopt_pair", "radix_pair")
            rows.append({"series": "one", "family": "NAB", "method": method, "trial": t, "seconds": (i+1)*(t+1),
                         "values": values, "winners": selected, "pr_error": .4 if approx else 0.,
                         "roc_error": 0. if pair else None, "selection": selection})
            workflows.append({"family": "NAB", "method": method, "trial": t, "seconds": (i+1)*(t+1),
                "decisions": [{"series": "one", "values": values, "winners": selected, "roc": [.9, .6] if pair else None}]})
    for name, data in [("records", rows), ("workflows", workflows)]:
        (folder/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in data))
    write(folder/"run-start.json", {"protocol_sha256": sha(folder/"protocol.json")})
    rebind(folder)
    return folder


def rebind(folder):
    write(folder/"complete.json", {"status": "COMPLETE", "protocol_sha256": sha(folder/"protocol.json"),
        "records_sha256": sha(folder/"records.jsonl"), "workflows_sha256": sha(folder/"workflows.jsonl")})


def test_supplement_reconstructs_sampling_loss_and_matched_outputs(tmp_path):
    supplement_fixture(tmp_path)
    module().audit(tmp_path, tmp_path/"supplement-audit.json")
    result = json.loads((tmp_path/"supplement-audit.json").read_text())
    assert result["status"] == "PASS"
    assert result["accuracy"]["NAB"]["klein250"]["minimum_regret_at_least_threshold"] == 1
    assert result["matched_pair"]["NAB"]["case_paired"]["geometric_speedup"] == pytest.approx(.75)


@pytest.mark.parametrize("kind", ["duplicate", "selection", "workflow_roc", "workflow_pr", "protocol_link"])
def test_supplement_rejects_corrupted_evidence(tmp_path, kind):
    folder = supplement_fixture(tmp_path)
    if kind == "protocol_link":
        p = json.loads((folder/"protocol.json").read_text()); p["inputs_sha256"] = "wrong"; write(folder/"protocol.json", p)
        write(folder/"run-start.json", {"protocol_sha256": sha(folder/"protocol.json")})
    else:
        file = folder/("workflows.jsonl" if kind.startswith("workflow") else "records.jsonl")
        rows = [json.loads(line) for line in file.read_text().splitlines()]
        if kind == "duplicate": rows[-1] = rows[0]
        if kind == "selection": rows[4]["selection"]["minimum_regret"] = 0.
        if kind == "workflow_roc": rows[2]["decisions"][0]["roc"][0] = .1
        if kind == "workflow_pr": rows[0]["decisions"][0]["values"][0] = .3
        file.write_text("".join(json.dumps(r)+"\n" for r in rows))
    rebind(folder)
    with pytest.raises(ValueError): module().audit(tmp_path, tmp_path/"supplement-audit.json")
