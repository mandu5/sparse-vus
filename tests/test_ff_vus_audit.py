"""Tiny semantic witnesses; this file performs no timing comparisons."""
import importlib
import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))


@pytest.fixture
def audit():
    assert importlib.util.find_spec("ff_vus_audit") is not None, "FF-VUS audit is missing"
    module = importlib.import_module("ff_vus_audit")
    pytest.importorskip("torch")
    if not (module.CACHE / "vus_torch.py").exists():
        pytest.skip("Fetch optional FF-VUS audit sources first: python experiments/ff_vus_audit.py --fetch")
    return module


def test_ffvus_rounding_and_native_ramps_differ_from_original(audit):
    result = audit.run_audit()
    rows = {r["name"]: r for r in result["counterexamples"]}
    rounding = rows["wrapper_rounding_width_zero"]
    assert rounding["ffvus_pr"] == pytest.approx(.5)
    assert rounding["official_pr"] == pytest.approx(1.)
    assert rows["native_same_numeric_width"]["absolute_difference"] > .12
    assert result["matched_radius_geometry"]["absolute_difference"] > .009
    assert result["existence_memory_fallback"]["direct"] == [0., 0., 1.]
    assert result["existence_memory_fallback"]["fallback"] == [0., .5, 1.]


def test_ffvus_tampered_source_is_not_executed(audit, tmp_path, monkeypatch):
    (tmp_path / "vus_torch.py").write_text("raise RuntimeError('must not execute')\n")
    monkeypatch.setattr(audit, "CACHE", tmp_path)
    with pytest.raises(ValueError, match="hash mismatch"):
        audit.load_torch_module()
