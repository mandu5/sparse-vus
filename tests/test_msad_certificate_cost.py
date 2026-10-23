"""Cost-study coverage and output checks use synthetic receipts, never corpus outcomes."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "experiments/msad_certificate_cost.py"
spec = importlib.util.spec_from_file_location("certificate_cost_tests", PATH)
cost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cost)


def fixture_protocol():
    return {"series": [{"series": "F/one", "family": "F", "npz_sha256": "a"}],
            "models": ["A", "B"], "repetitions": 5, "width": 30,
            "thresholds": 250, "seed": 20261023, "parity_tolerance": 2e-10}


def fixture_records(protocol):
    records = []
    for task in cost.schedule(protocol):
        r = dict(task, status="ok", seconds=2. if task["method"] == "certificate" else 1.)
        if task["method"] == "certificate":
            r.update(lower_numerator="1", upper_numerator="3", scale="4", thresholds_retained=2)
        else:
            r["value"] = .5
        records.append(r)
    return records


def test_schedule_is_deterministic_paired_and_complete():
    p = fixture_protocol()
    tasks = cost.schedule(p)
    assert tasks == cost.schedule(p)
    assert len(tasks) == 20 and len({r["key"] for r in tasks}) == 20
    for offset in range(0, len(tasks), 2):
        pair = tasks[offset:offset+2]
        assert {r["method"] for r in pair} == {"certificate", "radix_exact"}
        assert len({(r["series"], r["model"], r["repetition"]) for r in pair}) == 1


def test_selected_ids_must_match_prior_fixed_subset():
    rows = [{"series": "F/one", "family": "F", "npz_sha256": "a"},
            {"series": "G/two", "family": "G", "npz_sha256": "b"}]
    proposal = {"cases": [dict(rows[1]), dict(rows[0])], "series_count": 2}
    assert cost.select_rows(rows, proposal) == [rows[1], rows[0]]
    proposal["cases"][0]["npz_sha256"] = "changed"
    with pytest.raises(ValueError, match="identity"):
        cost.select_rows(rows, proposal)


def test_complete_valid_outputs_allow_ratio_with_integer_endpoints_retained():
    p = fixture_protocol()
    report = cost.summarize(fixture_records(p), p)
    assert report["comparative_claim_eligible"]
    assert report["complete_paired_cases"] == 2
    assert report["ratio"]["median"] == 2
    assert report["exact_float_outside_certificate_informational"] == 0


def test_missing_failed_or_censored_calls_forbid_global_ratio():
    p = fixture_protocol()
    records = fixture_records(p)
    assert not cost.summarize(records[:-1], p)["comparative_claim_eligible"]
    records[0] = dict(records[0], status="timeout")
    report = cost.summarize(records, p)
    assert not report["comparative_claim_eligible"]
    assert report["ratio"] is None
    assert report["status_counts"]["timeout"] == 1


def test_foreign_or_duplicate_receipts_are_rejected():
    p = fixture_protocol()
    records = fixture_records(p)
    with pytest.raises(ValueError, match="duplicate"):
        cost.summarize(records + [records[0]], p)
    records[0] = dict(records[0], model="foreign")
    with pytest.raises(ValueError, match="task"):
        cost.summarize(records, p)


@pytest.mark.parametrize("field,value", [("seconds", float("nan")), ("seconds", 0),
                                         ("lower_numerator", "5"), ("scale", "0")])
def test_invalid_certificate_output_is_rejected(field, value):
    p = fixture_protocol()
    records = fixture_records(p)
    i = next(i for i, r in enumerate(records) if r["method"] == "certificate")
    records[i] = dict(records[i], **{field: value})
    with pytest.raises(ValueError):
        cost.summarize(records, p)


def test_certificate_repeated_endpoints_must_be_identical():
    p = fixture_protocol()
    records = fixture_records(p)
    i = next(i for i, r in enumerate(records) if r["method"] == "certificate")
    records[i] = dict(records[i], lower_numerator="2")
    with pytest.raises(ValueError, match="repeat"):
        cost.summarize(records, p)
