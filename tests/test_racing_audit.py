"""Adversarial tiny racing receipts; no kernel runs or real archive access."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
sys.path.insert(0, str(EXPERIMENTS))
spec = importlib.util.spec_from_file_location("racing_audit_tests", EXPERIMENTS / "audit_racing.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def record(*, early=False, early_but_full=False):
    pr = {"A": .9 if early else .5, "B": .5, "C": .1}
    winners = ["A"] if early else ["A", "B"]
    values = {name: {"selected": winners.copy(), "pr": pr.copy()}
              for name in ("sparse_exact", "dense_direct", "dense_nearest")}
    for method in audit.RACING:
        candidates = ["A"] if early else (["A", "B", "C"] if method == "race_no_prune" else ["A", "B"])
        bounds = {}
        for model, value in pr.items():
            full = early_but_full or (not early and model in candidates)
            widths = list(range(31)) if full else [0, 30]
            bounds[model] = {
                "pr_lower": value if full else value - .005,
                "pr_upper": value if full else value + .005,
                "exact": full, "evaluated_widths": widths, "curve_evaluations": len(widths),
            }
        exact = {m: pr[m] for m, bound in bounds.items() if bound["exact"]}
        total = sum(len(bound["evaluated_widths"]) for bound in bounds.values())
        initial = 93 if early_but_full else 6
        values[method] = {
            "selected": winners.copy(), "early_winner": early,
            "candidates": candidates, "pruned": [m for m in pr if m not in candidates],
            "bounds": bounds, "exact_pr": exact, "full_evaluation_count": len(exact),
            "initial_unique_widths": initial, "initial_curve_evaluations": initial,
            "refinement_steps": total - initial,
            "total_unique_widths": total, "total_curve_evaluations": total,
        }
    medians = {"sparse_exact": 2., "dense_direct": 1.5, "dense_nearest": 1.7,
               "race_prune": 1., "race_no_prune": 1.2}
    return {
        "series": "tiny", "family": "synthetic", "n": 4, "max_buffer": 30,
        "label_sha256": "0" * 64, "score_sha256": {m: m.lower() * 64 for m in pr},
        "values": values, "exact_unique_winner": early,
        "seconds": {m: [v / 2, v, v * 1.5] for m, v in medians.items()},
        "median_seconds": medians,
    }


def protocol(rows):
    keys = [(row["series"], row["max_buffer"]) for row in rows]
    return {
        "cases": len(rows), "models_per_case": 3, "repetitions": 3,
        "selection_sha256": sha(json.dumps(keys, separators=(",", ":")).encode()),
        "exact_parity_tolerance": 1e-11, "float64_containment_tolerance": 1e-10,
    }


@pytest.mark.parametrize("early", [True, False])
def test_valid_racing_stopping_paths_and_comparator_ratios(early):
    rows = [record(early=early)]
    result, expanded = audit.audit_racing_records(rows, protocol(rows))
    assert len(expanded) == 3
    output = result["by_width"]["30"]
    assert output["race_prune"]["ratios_by_comparator"]["sparse_exact"]["median"] == 2.
    assert output["race_prune"]["ratios_by_comparator"]["dense_direct"]["median"] == 1.5
    assert output["race_prune"]["full_evaluations"] == (0 if early else 2)
    assert output["race_no_prune"]["full_evaluations"] == (0 if early else 3)


def test_early_flag_does_not_falsely_imply_skipped_widths():
    rows = [record(early=True, early_but_full=True)]
    result, _ = audit.audit_racing_records(rows, protocol(rows))
    work = result["work"]["30"]["race_prune"]
    assert work["median_unique_width_fraction"] == 1.
    assert work["early_winners_with_all_models_fully_evaluated"] == 1
    # Exact values for the excluded B/C remain visible and counted.
    assert result["by_width"]["30"]["race_prune"]["full_evaluations"] == 3


def test_unresolved_no_prune_ablation_must_fully_evaluate_every_model():
    rows = [record()]
    value = rows[0]["values"]["race_no_prune"]
    # Preserve a correct final tie selection but hide the exact evaluation of C.
    value["bounds"]["C"] = {
        "pr_lower": .095, "pr_upper": .105, "exact": False,
        "evaluated_widths": [0, 30], "curve_evaluations": 2,
    }
    del value["exact_pr"]["C"]
    value.update(full_evaluation_count=2, total_unique_widths=64, total_curve_evaluations=64,
                 refinement_steps=58)
    with pytest.raises(ValueError, match="stopped before"):
        audit.audit_racing_records(rows, protocol(rows))


def test_pruned_tie_cannot_be_omitted_from_result():
    rows = [record()]
    value = rows[0]["values"]["race_prune"]
    value.update(selected=["A"], candidates=["A"], pruned=["B", "C"])
    with pytest.raises(ValueError, match="lost exact tie"):
        audit.audit_racing_records(rows, protocol(rows))


@pytest.mark.parametrize("change", ["duplicate_width", "false_exact", "missing_exact_pr",
                                  "wrong_exact_pr", "hidden_refinement", "false_initial", "false_curve_total"])
def test_work_and_full_evaluation_claims_need_per_model_evidence(change):
    rows = [record()]
    value = rows[0]["values"]["race_prune"]
    if change == "duplicate_width":
        value["bounds"]["A"]["evaluated_widths"].append(30)
    elif change == "false_exact":
        value["bounds"]["C"]["exact"] = True
    elif change == "missing_exact_pr":
        del value["exact_pr"]["A"]
    elif change == "wrong_exact_pr":
        value["exact_pr"]["A"] = .6
    elif change == "hidden_refinement":
        value["refinement_steps"] -= 1
    elif change == "false_initial":
        value["initial_curve_evaluations"] = 1
    else:
        value["total_curve_evaluations"] -= 1
    with pytest.raises(ValueError):
        audit.audit_racing_records(rows, protocol(rows))


def test_noncontaining_interval_is_not_rescued_by_correct_selected_model():
    rows = [record(early=True)]
    rows[0]["values"]["race_prune"]["bounds"]["A"].update(pr_lower=.95, pr_upper=.96)
    with pytest.raises(ValueError, match="excludes exact"):
        audit.audit_racing_records(rows, protocol(rows))


def test_recomputed_endpoint_counts_cannot_exceed_three_curves_per_split():
    rows = [record()]
    value = rows[0]["values"]["race_prune"]
    excess_total = value["initial_curve_evaluations"] + 3 * value["refinement_steps"] + 1
    value["bounds"]["A"]["curve_evaluations"] += excess_total - value["total_curve_evaluations"]
    value["total_curve_evaluations"] = excess_total
    with pytest.raises(ValueError, match="accounting is impossible"):
        audit.audit_racing_records(rows, protocol(rows))


def test_false_early_winner_flag_on_exact_tie_is_rejected():
    rows = [record()]
    rows[0]["values"]["race_prune"]["early_winner"] = True
    with pytest.raises(ValueError, match="separation mismatch"):
        audit.audit_racing_records(rows, protocol(rows))


def test_compiled_baseline_requires_all_three_model_scores():
    rows = [record()]
    del rows[0]["values"]["dense_nearest"]["pr"]["C"]
    with pytest.raises(ValueError, match="Model-value coverage"):
        audit.audit_racing_records(rows, protocol(rows))


def test_same_winner_is_not_sufficient_for_exact_baseline_parity():
    rows = [record(early=True)]
    rows[0]["values"]["dense_direct"]["pr"]["A"] = .8
    with pytest.raises(ValueError, match="parity failure"):
        audit.audit_racing_records(rows, protocol(rows))


@pytest.mark.parametrize("duration", [0, -1, float("nan"), float("inf"), True])
def test_invalid_timing_is_rejected(duration):
    rows = [record()]
    rows[0]["seconds"]["race_prune"][0] = duration
    with pytest.raises(ValueError, match="Invalid racing timing"):
        audit.audit_racing_records(rows, protocol(rows))


def test_duplicate_case_cannot_receive_a_new_valid_coverage_hash():
    rows = [record(), record()]
    with pytest.raises(ValueError, match="Duplicate"):
        audit.audit_racing_records(rows, protocol(rows))


@pytest.fixture
def tiny_run(tmp_path, monkeypatch):
    root, run = tmp_path / "repo", tmp_path / "run"
    root.mkdir()
    run.mkdir()
    rows = [record()]
    frozen = protocol(rows)
    write_json(run / "protocol.json", frozen)
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    (run / "measurements.jsonl").write_bytes(raw)
    bindings = {}
    for relative in audit.REQUIRED_SOURCES:
        source = root / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"# Test source for {relative}\n")
        bindings[relative] = sha(source.read_bytes())
    write_json(run / "environment.json", {
        "source_sha256": bindings, "protocol_sha256": sha((run / "protocol.json").read_bytes()),
        "threads": 1, "threadpool_info": [],
        "warmup_seconds": {method: .01 for method in audit.METHODS},
    })
    rebuilt, _ = audit.audit_racing_records(rows, frozen)
    write_json(run / "summary.json", {
        "status": "PASS", "violations": [], "cases": 1,
        "measurements_sha256": sha(raw), "by_width": rebuilt["by_width"],
    })
    calls = []

    def fixture_data(expanded, *, mode, root):
        calls.append((deepcopy(expanded), mode, root))
        return {"status": "PASS", "fixture_only": True}
    monkeypatch.setattr(audit, "validate_advancement_data", fixture_data)
    return root, run, rows, calls


def test_completed_run_binds_selection_dependency_and_expands_models(tiny_run):
    root, run, _, calls = tiny_run
    result = audit.audit_racing_run(run, root=root)
    assert result["status"] == "PASS"
    assert "src/sparse_vus/selection.py" in result["source_sha256"]
    assert len(calls[0][0]) == 3 and calls[0][1] == "certified"


def test_rehashed_wrong_selection_does_not_inherit_pass(tiny_run):
    root, run, rows, _ = tiny_run
    rows[0]["values"]["race_prune"]["selected"] = ["A"]
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    (run / "measurements.jsonl").write_bytes(raw)
    summary = json.loads((run / "summary.json").read_text())
    summary["measurements_sha256"] = sha(raw)
    write_json(run / "summary.json", summary)
    with pytest.raises(ValueError, match="lost exact tie"):
        audit.audit_racing_run(run, root=root)


def test_forged_aggregate_speed_is_recomputed_from_raw_calls(tiny_run):
    root, run, _, _ = tiny_run
    summary = json.loads((run / "summary.json").read_text())
    summary["by_width"]["30"]["race_prune"]["ratios_by_comparator"]["dense_direct"]["median"] = 100.
    write_json(run / "summary.json", summary)
    with pytest.raises(ValueError, match="Summary numeric mismatch"):
        audit.audit_racing_run(run, root=root)


def test_changed_shared_policy_source_breaks_timing_binding(tiny_run):
    root, run, _, _ = tiny_run
    (root / "src/sparse_vus/selection.py").write_text("# Policy changed after timing\n")
    with pytest.raises(ValueError, match="Racing source changed"):
        audit.audit_racing_run(run, root=root)


def test_omitted_shared_policy_source_is_not_a_complete_receipt(tiny_run):
    root, run, _, _ = tiny_run
    environment = json.loads((run / "environment.json").read_text())
    del environment["source_sha256"]["src/sparse_vus/selection.py"]
    write_json(run / "environment.json", environment)
    with pytest.raises(ValueError, match="source coverage"):
        audit.audit_racing_run(run, root=root)
