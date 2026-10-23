"""Three-way cost supplement reporting must retain same-guarantee comparisons."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "experiments/msad_certificate_full_cost.py"
spec = importlib.util.spec_from_file_location("full_certificate_cost_tests", PATH)
cost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cost)


def fixture():
    p = {"series": [{"series": "F/s", "family": "F", "n": 600}],
         "models": ["A"], "repetitions": 5, "seed": 20261023, "width": 30,
         "thresholds": 250, "parity_tolerance": 2e-10}
    records = []
    for task in cost.schedule(p):
        r = dict(task, status="ok", seconds={"certificate": 2., "full_certificate": 3., "radix_exact": 1.}[task["method"]])
        if task["method"] == "radix_exact":
            r["value"] = .5
        else:
            r.update(lower_numerator="1", upper_numerator="3", scale="4", thresholds_retained=2)
        records.append(r)
    return p, records


def test_three_methods_form_complete_deterministic_blocks():
    p, records = fixture()
    assert cost.schedule(p) == cost.schedule(p)
    assert len(records) == len({r["key"] for r in records}) == 15
    for i in range(0, 15, 3):
        assert {r["method"] for r in records[i:i+3]} == set(cost.METHODS)
    assert all(r["thresholds"] == 600 for r in records if r["method"] == "full_certificate")


def test_same_guarantee_ratio_and_both_exact_overheads_are_reported():
    p, records = fixture()
    r = cost.summarize(records, p)
    assert r["comparative_claim_eligible"]
    assert r["ratios"]["certificate_over_full_certificate"]["median"] == pytest.approx(2/3)
    assert r["ratios"]["certificate_over_radix_exact"]["median"] == 2
    assert r["ratios"]["full_certificate_over_radix_exact"]["median"] == 3


def test_missing_or_failed_full_certificate_blocks_global_comparison():
    p, records = fixture()
    r = cost.summarize(records[:-1], p)
    assert not r["comparative_claim_eligible"] and r["ratios"] is None
    records[0] = dict(records[0], status="timeout")
    assert not cost.summarize(records, p)["comparative_claim_eligible"]


def test_full_certificate_repeat_change_or_duplicate_is_detected():
    p, records = fixture()
    i = next(i for i,r in enumerate(records) if r["method"] == "full_certificate")
    records[i] = dict(records[i], upper_numerator="2")
    with pytest.raises(ValueError, match="repeat"):
        cost.summarize(records, p)
    p, records = fixture()
    with pytest.raises(ValueError, match="duplicate"):
        cost.summarize(records+[records[0]], p)
