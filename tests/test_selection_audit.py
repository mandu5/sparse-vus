"""Tiny receipt attacks against the independent whole-selection audit.

No metric kernels, real released archives, or network access are involved.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
sys.path.insert(0, str(EXPERIMENTS))
spec = importlib.util.spec_from_file_location("selection_audit_tests", EXPERIMENTS / "audit_selection.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def fixture_record(*, early=False):
    pr = {"A": .9 if early else .5, "B": .5, "C": .1}
    selected = ["A"] if early else ["A", "B"]
    bounds = {m: [v - .005, v + .005] for m, v in pr.items()}
    sampled = pr.copy() if early else {"A": .2, "B": .5, "C": .1}
    values = {
        method: {"selected": selected.copy(), "pr": pr.copy()}
        for method in ("sparse_exact", "dense_direct", "dense_nearest", "fast_vus_exact_pr")
    }
    values["fixed250_pr"] = {"selected": ["A"] if early else ["B"], "pr": sampled}
    for method in audit.CERTIFIED:
        candidates = ["A"] if early else (["A", "B", "C"] if method.endswith("no_prune") else ["A", "B"])
        exact = {} if early else {m: pr[m] for m in candidates}
        values[method] = {
            "selected": selected.copy(), "early_winner": early,
            "candidates": candidates, "pruned": [m for m in pr if m not in candidates],
            "exact_fallback_count": len(exact), "exact_pr": exact,
            "certified_evaluations": 3, "certified_curve_evaluations": 6,
            "certified_unique_widths": 6, "bounds": deepcopy(bounds),
        }
    medians = {method: 2.0 for method in audit.METHODS}
    medians.update(certificate_prune=1.0, certificate_no_prune=1.2, fixed250_pr=.25)
    return {
        "series": "synthetic_case", "family": "synthetic", "n": 4, "max_buffer": 30,
        "label_sha256": "0" * 64, "score_sha256": {m: m.lower() * 64 for m in pr},
        "values": values,
        "seconds": {method: [median / 2, median, median * 1.5] for method, median in medians.items()},
        "median_seconds": medians, "fixed250_wrong_selection": not early,
        "exact_unique_winner": early,
    }


def fixture_protocol(rows):
    keys = [(row["series"], row["max_buffer"]) for row in rows]
    return {
        "cases": len(rows), "models_per_case": 3, "repetitions": 3, "atol": .01,
        "exact_parity_tolerance": 1e-11, "float64_containment_tolerance": 1e-10,
        "selection_sha256": digest_bytes(json.dumps(keys, separators=(",", ":")).encode()),
    }


@pytest.mark.parametrize("early", [False, True])
def test_valid_ties_fallback_and_early_winner_records(early):
    rows = [fixture_record(early=early)]
    result, expanded = audit.audit_records(rows, fixture_protocol(rows))
    assert len(expanded) == 3
    assert {row["model"] for row in expanded} == {"A", "B", "C"}
    summary = result["by_width"]["30"]
    assert summary["certificate_prune"]["ratios_by_comparator"]["sparse_exact"]["median"] == 2.0
    assert summary["certificate_prune"]["exact_fallback_evaluations"] == (0 if early else 2)
    assert summary["certificate_no_prune"]["exact_fallback_evaluations"] == (0 if early else 3)
    assert summary["fixed250_wrong_selections"] == (0 if early else 1)


def test_ablation_cannot_hide_pruning_even_when_final_selection_is_correct():
    rows = [fixture_record()]
    value = rows[0]["values"]["certificate_no_prune"]
    value.update(candidates=["A", "B"], pruned=["C"],
                 exact_pr={"A": .5, "B": .5}, exact_fallback_count=2)
    with pytest.raises(ValueError, match="Pruning/candidate policy"):
        audit.audit_records(rows, fixture_protocol(rows))


def test_missing_exact_tie_is_rejected():
    rows = [fixture_record()]
    rows[0]["values"]["certificate_prune"]["selected"] = ["A"]
    with pytest.raises(ValueError, match="Wrong certificate selection"):
        audit.audit_records(rows, fixture_protocol(rows))


@pytest.mark.parametrize("kind", ["false_early", "fallback_count", "missing_value", "wrong_pr", "curve_count"])
def test_false_work_or_semantics_claims_are_rejected(kind):
    rows = [fixture_record()]
    value = rows[0]["values"]["certificate_prune"]
    if kind == "false_early":
        value["early_winner"] = True
    elif kind == "fallback_count":
        value["exact_fallback_count"] = 0
    elif kind == "missing_value":
        del value["exact_pr"]["B"]
    elif kind == "wrong_pr":
        value["exact_pr"]["A"] = .7
    else:
        value["certified_curve_evaluations"] = 1
    with pytest.raises(ValueError):
        audit.audit_records(rows, fixture_protocol(rows))


def test_changed_bound_work_invalidates_no_pruning_ablation():
    rows = [fixture_record()]
    rows[0]["values"]["certificate_no_prune"]["bounds"]["A"][0] += .001
    with pytest.raises(ValueError, match="ablation changed"):
        audit.audit_records(rows, fixture_protocol(rows))


@pytest.mark.parametrize("pair", [[.7, .71], [.51, .49], [.4, .6], [float("nan"), .51]])
def test_false_interval_is_rejected_even_if_selected_models_are_right(pair):
    rows = [fixture_record()]
    rows[0]["values"]["certificate_prune"]["bounds"]["A"] = pair
    with pytest.raises(ValueError):
        audit.audit_records(rows, fixture_protocol(rows))


def test_external_exact_value_requires_parity_not_just_same_winner():
    rows = [fixture_record(early=True)]
    rows[0]["values"]["fast_vus_exact_pr"]["pr"]["A"] = .8
    with pytest.raises(ValueError, match="Exact PR mismatch"):
        audit.audit_records(rows, fixture_protocol(rows))


def test_omitted_model_score_cannot_pass_on_winner_alone():
    rows = [fixture_record(early=True)]
    del rows[0]["values"]["fast_vus_exact_pr"]["pr"]["C"]
    with pytest.raises(ValueError, match="Model-value coverage"):
        audit.audit_records(rows, fixture_protocol(rows))


def test_approximate_decision_error_cannot_be_erased_by_a_flag():
    rows = [fixture_record()]
    rows[0]["fixed250_wrong_selection"] = False
    with pytest.raises(ValueError, match="fixed250 disagreement"):
        audit.audit_records(rows, fixture_protocol(rows))


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf"), True])
def test_invalid_duration_is_not_a_speed_measurement(bad):
    rows = [fixture_record()]
    rows[0]["seconds"]["certificate_prune"][0] = bad
    with pytest.raises(ValueError, match="Invalid selection timing"):
        audit.audit_records(rows, fixture_protocol(rows))


def test_faster_forged_median_is_rejected():
    rows = [fixture_record()]
    rows[0]["median_seconds"]["certificate_prune"] = .01
    with pytest.raises(ValueError, match="Forged selection median"):
        audit.audit_records(rows, fixture_protocol(rows))


def test_duplicate_coverage_rejected_with_matching_new_selection_hash():
    row = fixture_record()
    rows = [row, deepcopy(row)]
    with pytest.raises(ValueError, match="Duplicate selection"):
        audit.audit_records(rows, fixture_protocol(rows))


@pytest.fixture
def tiny_run(tmp_path, monkeypatch):
    root, run = tmp_path / "repository", tmp_path / "run"
    root.mkdir()
    run.mkdir()
    rows = [fixture_record()]
    protocol = fixture_protocol(rows)
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    (run / "measurements.jsonl").write_bytes(raw)
    write_json(run / "protocol.json", protocol)
    source_hashes = {}
    for relative in audit.REQUIRED_SOURCES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Independent fixture for {relative}\n")
        source_hashes[relative] = digest_bytes(path.read_bytes())
    write_json(run / "environment.json", {
        "protocol_sha256": digest_bytes((run / "protocol.json").read_bytes()),
        "source_sha256": source_hashes, "threads": 1, "threadpool_info": [],
        "warmup_seconds": {method: .01 for method in audit.METHODS},
    })
    reconstructed, _ = audit.audit_records(rows, protocol)
    write_json(run / "summary.json", {
        "status": "PASS", "cases": 1, "violations": [],
        "measurements_sha256": digest_bytes(raw), "by_width": reconstructed["by_width"],
    })
    calls = []

    def fixture_provenance(expanded, *, mode, root):
        calls.append((deepcopy(expanded), mode, root))
        return {"status": "PASS", "fixture_only": True}
    monkeypatch.setattr(audit, "validate_advancement_data", fixture_provenance)
    return root, run, rows, calls


def test_complete_run_binds_sources_and_expands_every_model(tiny_run):
    root, path, _, calls = tiny_run
    result = audit.audit_selection_run(path, root=root)
    assert result["status"] == "PASS"
    expanded, mode, given_root = calls[0]
    assert mode == "certified" and given_root == root
    assert len(expanded) == 3 and {row["model"] for row in expanded} == {"A", "B", "C"}


def test_rehashed_false_raw_success_is_rejected(tiny_run):
    root, path, rows, _ = tiny_run
    rows[0]["values"]["dense_direct"]["pr"]["A"] = .9
    rows[0]["values"]["dense_direct"]["selected"] = ["A"]
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    (path / "measurements.jsonl").write_bytes(raw)
    summary = json.loads((path / "summary.json").read_text())
    summary["measurements_sha256"] = digest_bytes(raw)
    write_json(path / "summary.json", summary)
    with pytest.raises(ValueError, match="Wrong exact selection"):
        audit.audit_selection_run(path, root=root)


def test_correct_raw_records_do_not_justify_fabricated_aggregate_speed(tiny_run):
    root, path, _, _ = tiny_run
    summary = json.loads((path / "summary.json").read_text())
    summary["by_width"]["30"]["certificate_prune"]["ratios_by_comparator"]["sparse_exact"]["median"] = 100.
    write_json(path / "summary.json", summary)
    with pytest.raises(ValueError, match="Summary numeric mismatch"):
        audit.audit_selection_run(path, root=root)


def test_protocol_mutation_does_not_inherit_old_environment_receipt(tiny_run):
    root, path, _, _ = tiny_run
    protocol = json.loads((path / "protocol.json").read_text())
    protocol["atol"] = 1
    write_json(path / "protocol.json", protocol)
    with pytest.raises(ValueError, match="protocol binding"):
        audit.audit_selection_run(path, root=root)


def test_code_change_does_not_inherit_old_timing_receipt(tiny_run):
    root, path, _, _ = tiny_run
    (root / "src/sparse_vus/selection.py").write_text("# Different algorithm\n")
    with pytest.raises(ValueError, match="measured source changed"):
        audit.audit_selection_run(path, root=root)
