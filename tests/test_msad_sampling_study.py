"""Study analysis and receipt guards, using hand-checked synthetic fixtures."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1] / "experiments/msad_sampling_study.py"
spec = importlib.util.spec_from_file_location("msad_study_tests", PATH)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_sampled_tie_reports_both_regrets_without_claiming_forced_mistake():
    r = study.compare_vectors({"A": .9, "B": .7, "C": .2},
                              {"A": .8, "B": .8, "C": .1})
    assert r["sampled_winners"] == ["A", "B"]
    assert r["best_regret"] == 0
    assert r["worst_regret"] == pytest.approx(.2)
    assert not r["unique_winner_changed"]


def test_opposite_pair_margins_count_reversal_but_tolerance_ties_do_not():
    r = study.compare_vectors({"A": .9, "B": .7, "C": .2},
                              {"A": .6, "B": .8, "C": .2})
    assert r["pair_reversals"] == 1
    assert r["large_pair_reversals"] == 1
    assert r["kendall_tau_b"] == pytest.approx(1 / 3)
    assert r["best_regret"] == pytest.approx(.2)
    tied = study.compare_vectors({"A": 1., "B": 1. - 5e-11},
                                 {"A": 0., "B": 1.})
    assert tied["pair_reversals"] == 0
    assert tied["exact_winners"] == ["A", "B"]
    assert tied["kendall_tau_b"] is None


def test_top_three_retains_all_ties_at_the_cutoff():
    r = study.compare_vectors({"A": .9, "B": .8, "C": .7, "D": .7},
                              {"A": .9, "B": .8, "C": .7, "D": .6})
    assert r["exact_top3"] == ["A", "B", "C", "D"]
    assert r["top3_changed"]


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_nonfinite_metric_cannot_enter_ranking(bad):
    with pytest.raises(ValueError, match="finite"):
        study.compare_vectors({"A": .5}, {"A": bad})


def test_changed_model_pool_is_rejected():
    with pytest.raises(ValueError, match="model"):
        study.compare_vectors({"A": .5}, {"B": .5})


def test_hash_guard_detects_mutated_source_before_resumption(tmp_path):
    source = tmp_path / "source.py"
    source.write_bytes(b"original")
    hashes = {"source.py": hashlib.sha256(b"original").hexdigest()}
    study.verify_hashes(hashes, tmp_path)
    source.write_bytes(b"mutated")
    with pytest.raises(ValueError, match="hash"):
        study.verify_hashes(hashes, tmp_path)


def test_append_log_does_not_overwrite_and_conflicting_duplicate_is_rejected(tmp_path):
    path = tmp_path / "results.jsonl"
    r = {"key": "one", "status": "ok", "value": .5}
    study.append_record(path, r)
    study.append_record(path, {"key": "two", "status": "timeout"})
    before = path.read_bytes()
    assert study.read_records(path)["one"] == r
    with pytest.raises(ValueError, match="duplicate"):
        study.append_record(path, dict(r, value=.8))
    assert path.read_bytes() == before


def test_npz_and_array_hash_guards_prevent_changed_inputs(tmp_path):
    labels = np.array([0, 1, 0], dtype=np.int8)
    score = np.array([.3, .9, .2])
    obs = np.array([1., 2., 3.])
    path = tmp_path / "case.npz"
    np.savez(path, labels=labels, observations=obs, A=score)
    row = {"npz_path": "case.npz", "npz_sha256": study.sha256_file(path),
           "array_sha256": {"labels": study.array_hash(labels),
                            "observations": study.array_hash(obs),
                            "A": study.array_hash(score)}, "n": 3,
           "positive_points": 1}
    got = study.load_case(row, ["A"], tmp_path)
    assert got["A"].tolist() == [.3, .9, .2]
    row["array_sha256"]["A"] = "0" * 64
    with pytest.raises(ValueError, match="array hash"):
        study.load_case(row, ["A"], tmp_path)


def fixture_protocol():
    return {"models": ["A", "B"], "widths": [30], "threshold_budgets": [250],
            "primary_width": 30, "primary_thresholds": 250,
            "tie_tolerance": 1e-10, "parity_tolerance": 2e-10,
            "practical_regret_threshold": .01,
            "promotion_gate": {"minimum_series_fraction": .05,
                               "minimum_source_families": 3},
            "bootstrap": {"replicates": 100, "seed": 23}}


def fixture_records():
    out = []
    for name, family, exact, sampled in [("a", "F1", [.9, .3], [.2, .4]),
                                        ("b", "F1", [.8, .2], [.8, .2]),
                                        ("c", "F2", [.7, .1], [.7, .1])]:
        for model, e, s in zip(["A", "B"], exact, sampled):
            for method, budget, value in [("radix_exact", None, e),
                                           ("matched_sampled", 250, s),
                                           ("klein250", 250, s)]:
                out.append({"key": f"{name}/{model}/{method}", "phase": "numerical",
                            "series": name, "family": family, "model": model,
                            "width": 30, "thresholds": budget, "method": method,
                            "status": "ok", "value": value})
    return out


def test_report_reconstruction_preserves_negative_gate_and_family_weights():
    rows = [{"series": "a", "family": "F1"}, {"series": "b", "family": "F1"},
            {"series": "c", "family": "F2"}]
    records = fixture_records()
    r = study.build_report(records, rows, fixture_protocol())
    assert r["primary"]["pooled"]["practical_regret_fraction"] == pytest.approx(1 / 3)
    assert r["primary"]["equal_family"]["practical_regret_fraction"] == .25
    assert r["primary"]["families_with_practical_regret"] == 1
    assert r["primary"]["promotion_gate_passed"] is False
    assert r == study.build_report(list(reversed(records)), rows, fixture_protocol())


def test_missing_model_is_visible_and_not_counted_as_valid_selection():
    records = fixture_records()
    records = [r for r in records if r["key"] != "a/A/matched_sampled"]
    rows = [{"series": "a", "family": "F1"}, {"series": "b", "family": "F1"},
            {"series": "c", "family": "F2"}]
    r = study.build_report(records, rows, fixture_protocol())
    assert r["primary"]["complete_series"] == 2
    assert r["primary"]["missing_series"] == ["a"]
    assert r["primary"]["promotion_gate_passed"] is False


def test_upstream_disagreement_blocks_scientific_gate():
    records = fixture_records()
    next(r for r in records if r["key"] == "a/A/klein250")["value"] = .7
    with pytest.raises(ValueError, match="parity"):
        study.build_report(records, [{"series": "a", "family": "F1"}], fixture_protocol())


def test_incomplete_control_coverage_cannot_promote_large_effect():
    records = []
    rows = []
    for name in ["a", "b", "c"]:
        rows.append({"series": name, "family": name})
        for model, exact, sampled in [("A", .9, .2), ("B", .2, .8)]:
            for method, h, value in [("radix_exact", None, exact),
                                      ("matched_sampled", 250, sampled)]:
                records.append({"key": f"{name}/{model}/{method}", "phase": "numerical",
                                "series": name, "family": name, "model": model,
                                "width": 30, "thresholds": h, "method": method,
                                "status": "ok", "value": value})
    r = study.build_report(records, rows, fixture_protocol())
    assert r["primary"]["effect_threshold_passed"] is True
    assert r["primary"]["promotion_gate_passed"] is False
    assert r["control_coverage"]["upstream_250_complete"] is False


def test_changed_value_in_timing_call_is_not_accepted_as_performance_evidence():
    records = fixture_records()
    records.append({"key": "timing", "phase": "timing", "series": "a", "family": "F1",
                    "model": "A", "width": 30, "method": "radix_exact", "thresholds": None,
                    "repetition": 0, "status": "ok", "value": .1, "seconds": .01})
    with pytest.raises(ValueError, match="parity"):
        study.build_report(records, [{"series": "a", "family": "F1"}], fixture_protocol())
