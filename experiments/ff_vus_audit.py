"""Reproduce small FF-VUS semantic mismatches; never a timing benchmark.

Unmodified upstream Torch source is loaded from a hash-verified ignored cache.
The rounded-input witness reproduces the public wrapper's two-decimal input
transformation; the wrapper itself is preserved in cache but not executed.
PyTorch is an optional dependency used only when running this audit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/ff_vus"
REVISION = "facf4362092525671215031048a75842b9d6d632"
BASE_URL = f"https://raw.githubusercontent.com/doanthihoaithu/aVUSi/{REVISION}"
FF_DIRECTORY = "3_metric_calculator/metrics/ffvus"
SOURCES = {
    "vus_torch.py": (f"{BASE_URL}/{FF_DIRECTORY}/vus_torch.py", "bed53590c5981fbb06eb858007869a90617730f9c5a2738595352323b93e0224"),
    "vus_numpy.py": (f"{BASE_URL}/{FF_DIRECTORY}/vus_numpy.py", "5140c7e1e0ad4d83f3a256cce3a7bafeff4fe4df0e360cb98c24153958fcf973"),
    "ffvus_metrics.py": (f"{BASE_URL}/{FF_DIRECTORY}/ffvus_metrics.py", "49cd9c46b2af1dea338f39c36dd4c91e88fe728eed1421aeba0951db9a2dd446"),
    "LICENSE": (f"{BASE_URL}/LICENSE", "034cb0ba268aa950853dace0de40ac90173dff46fae558e49ae3f6f1f6b80815"),
    "official_metrics.py": ("https://raw.githubusercontent.com/thedatumorg/VUS/467bace0c103f5c2bdb4900306d82939bcac8ff9/vus/utils/metrics.py", "bd547c9746fc1b9bbce2895e20cb156f97d23365d5dce8c2a3fab90622ccdced"),
}


def source_receipt():
    return {
        "repository": "https://github.com/doanthihoaithu/aVUSi",
        "revision": REVISION,
        "revision_date": "2026-06-23T21:55:37Z",
        "ffvus_first_file_commit": "921e3bc2ec7b9484733a976434b9390fdacaa56d",
        "ffvus_first_file_date": "2026-06-13T20:49:03Z",
        "code_attribution": "File headers name Emmanouil Sylligardos and FF-VUS.",
        "license": "Repository MIT, copyright 2026 Thu T. H. Doan; no upstream source vendored here.",
        "sources": {name: {"url": url, "sha256": digest} for name, (url, digest) in SOURCES.items()},
        "paper_linkage": "Connection to the 2025 PhD workshop timing version is not independently established.",
    }


def fetch_reference():
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in SOURCES.items():
        path = CACHE / name
        if not path.exists():
            temporary = path.with_suffix(path.suffix + ".download")
            try:
                subprocess.run(["curl", "-fsSL", "--retry", "2", "--max-time", "60", url, "-o", str(temporary)], check=True)
                if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
                    raise ValueError(f"FF-VUS audit {name} hash mismatch")
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"FF-VUS audit {name} hash mismatch")
    (CACHE / "source.json").write_text(json.dumps(source_receipt(), indent=2) + "\n")
    return CACHE


def _load(name, module_name):
    path = CACHE / name
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCES[name][1]:
        raise ValueError(f"FF-VUS audit {name} hash mismatch")
    module = types.ModuleType(module_name)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def load_torch_module():
    return _load("vus_torch.py", "pinned_ffvus_torch")


def run_audit():
    import torch
    sys.path.insert(0, str(ROOT / "src"))
    from sparse_vus.core import sparse_vus
    ff = load_torch_module()
    official = _load("official_metrics.py", "pinned_official_vus")
    rows = []
    for name, y, scores, width, rounded in [
        ("wrapper_rounding_width_zero", [0, 1, 0], [.101, .102, .001], 0, True),
        ("native_same_numeric_width", [0, 0, 0, 1, 0, 0, 0], [0, 1, 5, 4, 3, 2, -1], 2, False),
        ("native_overlap", [0, 1, 0, 1, 0], [5, 4, 3, 2, 1], 2, False),
    ]:
        y, scores = np.asarray(y, dtype=float), np.asarray(scores, dtype=float)
        ff_scores = np.round(scores, 2) if rounded else scores
        values, _ = ff.VUSTorch(slope_size=width, device="cpu").compute(torch.from_numpy(y), torch.from_numpy(ff_scores))
        reference = official.metricor().RangeAUC_volume_opt(y, scores, width, thre=len(y))[-1]
        sparse = sparse_vus(y, scores, width)[1]
        if abs(sparse - reference) > 1e-12:
            raise AssertionError("Sparse and official witness values disagree")
        rows.append({"name": name, "labels": y.tolist(), "scores": scores.tolist(), "max_buffer": width,
                     "ffvus_score_input": ff_scores.tolist(), "ffvus_pr": float(values[0]),
                     "official_pr": float(reference), "sparse_pr": float(sparse),
                     "absolute_difference": abs(float(values[0]) - float(reference))})

    # Matching physical radius still leaves different ramp values at distance 1.
    y = torch.tensor([0., 0., 0., 1., 0., 0., 0.])
    scores = torch.tensor([0., 1., 5., 4., 3., 2., -1.])
    metric = ff.VUSTorch(slope_size=2, device="cpu")
    metric.update_max_memory_tokens()
    (_, (starts, ends)), _ = metric.get_anomalies_coordinates(y)
    positions, _ = metric.distance_from_anomaly(y, starts, ends)
    labels, _ = metric.add_slopes(y, positions)
    thresholds, _ = metric.get_unique_thresholds(scores)
    score_mask, _ = metric.get_score_mask(scores, thresholds)
    existence, _ = metric.compute_existence(labels, score_mask)
    (fp, _, tp, positives, _, _), _ = metric.compute_confusion_matrix(labels, score_mask)
    (precision, recall), _ = metric.precision_recall_curve(tp, fp, positives, existence)
    ff_width2 = float(torch.sum((recall[:, 1:] - recall[:, :-1]) * precision[:, 1:], axis=1)[-1])
    reference = official.metricor().RangeAUC_volume_opt(y.numpy(), scores.numpy(), 4, thre=len(y))
    official_width4 = float(np.dot(np.diff(np.asarray(reference[0])[-1, :-1]), np.asarray(reference[2])[-1, 1:]))
    geometry = {"ff_slope": 2, "official_width": 4, "labels": y.tolist(), "scores": scores.tolist(),
                "ff_width2_weights": labels[-1].tolist(),
                "official_width4_weights": [0, float(np.sqrt(.5)), float(np.sqrt(.75)), 1, float(np.sqrt(.75)), float(np.sqrt(.5)), 0],
                "ff_width2_pr": ff_width2, "official_width4_pr": official_width4,
                "absolute_difference": abs(ff_width2 - official_width4)}

    # Isolate the documented memory-triggered existence interpolation.
    # Single anomaly; a prediction at distance two is found only at slope two.
    y = torch.tensor([0., 0., 1., 0., 0., 0., 0., 0., 0.])
    (_, (starts, ends)), _ = metric.get_anomalies_coordinates(y)
    positions, _ = metric.distance_from_anomaly(y, starts, ends)
    labels, _ = metric.add_slopes(y, positions)
    mask = torch.tensor([[False, False, False, False, True, False, False, False, False]])
    metric.max_memory_tokens = 10**9
    direct, _ = metric.compute_existence(labels, mask)
    metric.max_memory_tokens = 1
    fallback, _ = metric.compute_existence(labels, mask)
    memory = {"direct": direct[:, 0].tolist(), "fallback": fallback[:, 0].tolist(),
              "note": "Internal existence function; explicit memory budgets exercise both unmodified branches. No speed measurement."}
    return {"status": "COUNTEREXAMPLES_REPRODUCED", "source": source_receipt(),
            "numpy": np.__version__, "torch": torch.__version__, "device": "cpu",
            "counterexamples": rows, "matched_radius_geometry": geometry,
            "existence_memory_fallback": memory, "no_performance_claim": True}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.fetch:
        fetch_reference()
    if args.output:
        result = run_audit()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(args.output)
