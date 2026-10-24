"""Exploratory post-hoc raster/incremental contrasts from saved control trials.

Reuses the byte-pinned independent auditor's paired-order bootstrap, without
importing metric implementations or evaluating scores. The six collection/query
contrasts per host receive Bonferroni adjustment together. No minimum-control
interval is computed, and no original protocol or report is modified.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import importlib.util
import itertools
import json
import math
from pathlib import Path

import numpy as np

import render_strengthening_evidence as presentation

FROZEN_AUDITOR_SHA256 = "2285fbb8b79aab3a9d365ac0cf7097b9b33098abc1fa78424a3ceaf138724923"
CORRECTION = 6


def load_bootstrap():
    path = Path(__file__).with_name("audit_weighted_range_study.py")
    presentation.require(presentation.digest(path) == FROZEN_AUDITOR_SHA256,
                         "independent bootstrap source changed")
    spec = importlib.util.spec_from_file_location("frozen_independent_weighted_auditor", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.paired_order_interval


def direct_summary(control, candidate, reference, paired_order_interval, seed, resamples):
    a, b = np.asarray(control, dtype=float), np.asarray(candidate, dtype=float)
    presentation.require(a.shape == b.shape and a.ndim == 3 and a.shape[1:] == (12, 6),
                         "expected cases x twelve semantics x six paired trials")
    presentation.require(np.isfinite(a).all() and np.isfinite(b).all() and (a > 0).all() and (b > 0).all(),
                         "timings must be finite and positive")
    logs = np.log(np.median(a, axis=2) / np.median(b, axis=2))
    center = float(np.exp(logs.mean()))
    presentation.check_close(center, reference, "direct center differs from presentation CSV")
    per_recording = np.exp(logs.mean(axis=1))
    per_semantic = np.exp(logs.mean(axis=0))
    return {
        "geometric_ratio": center,
        "paired_order95_interval": paired_order_interval(a, b, CORRECTION, seed, resamples),
        "correction_comparisons": CORRECTION,
        "recordings": len(a),
        "recording_wins": int(np.count_nonzero(per_recording > 1)),
        "recording_losses": int(np.count_nonzero(per_recording < 1)),
        "recording_ties": int(np.count_nonzero(per_recording == 1)),
        "min_recording_ratio": float(per_recording.min()),
        "max_recording_ratio": float(per_recording.max()),
        "semantic_ratio_range": [float(per_semantic.min()), float(per_semantic.max())],
        "center_matches_direct_saved_median_csv": True,
    }


def markdown(report):
    lines = [
        "# Exploratory post-hoc direct raster/incremental comparison",
        "",
        "These additional contrasts were specified after examining the supplemental interval-control results. They are exploratory post-hoc analyses, not prospectively frozen findings. Only saved durations are resampled; there are no new detector fits, metric evaluations or timing runs.",
        "",
        "Each ratio is raster time divided by incremental time, using the median of six balanced orders for each recording and semantic setting, then equal log weight over all twelve settings and all recordings in the collection. Incremental means bucket for grid100 and sweep for distinct. The original independent auditor's byte-pinned bootstrap resamples six paired trial indices separately within each recording and shares those indices across both methods and all twelve semantics. Recording membership is fixed.",
        "",
        "Intervals use 10,000 resamples, seed 20261024, and Bonferroni tails 0.025/6 and 1−0.025/6 over the three collections × two query contracts within each host. They are not jointly adjusted across hosts or the other reported contrasts. Six balanced orders support limited approximate timing uncertainty; these intervals do not give population coverage or correct post-hoc comparator selection. No interval is assigned to the minimum-control scatter.",
        "",
        "| Host | Collection | Query | Raster / incremental | Paired-order interval | Recording W/L/T | Semantic ratio range |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for row in report["estimates"]:
        lo, hi = row["paired_order95_interval"]
        slo, shi = row["semantic_ratio_range"]
        lines.append(f"| {row['host']} | {row['family']} | {row['query']} | {row['geometric_ratio']:.8g} | [{lo:.8g}, {hi:.8g}] | {row['recording_wins']}/{row['recording_losses']}/{row['recording_ties']} | [{slo:.8g}, {shi:.8g}] |")
    lines += [
        "",
        "All twelve point estimates were cross-checked against the independently exported direct-median CSVs. Raster is faster than interval for every Linux recording after semantic aggregation, but not every Mac recording; this report retains a fixed raster comparison and does not substitute an observed minimum comparator into the bootstrap. Both hosts retain the distinct-query MSL id7 raster/incremental loss. MSL contains only two selected recordings.",
        "",
        f"Frozen bootstrap auditor SHA256: `{FROZEN_AUDITOR_SHA256}`.",
        f"Report source SHA256: `{report['analysis_source_sha256']}`.",
        f"Presentation CSV SHA256: `{report['presentation_csv_sha256']}`.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mac", type=Path, required=True)
    parser.add_argument("--linux", type=Path, required=True)
    parser.add_argument("--presentation", type=Path, required=True, help="Audited presentation directory")
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    presentation.require(not args.out.exists(), "refusing to replace post-hoc outputs")
    csv_path = args.presentation / "weighted-aggregates.csv"
    receipt_path = args.presentation / "presentation-receipt.json"
    csv_sha = presentation.digest(csv_path)
    receipt_sha = presentation.digest(receipt_path)
    receipt = json.loads(receipt_path.read_text())
    presentation.require(receipt["status"] == "PASS_AUDITED_SAVED_DATA_PRESENTATION"
                         and receipt["outputs"][csv_path.name] == csv_sha,
                         "presentation receipt/CSV identity differs")
    with csv_path.open(newline="") as stream:
        csv_rows = presentation.index_unique(list(csv.DictReader(stream)),
                                             ("host", "family", "query", "control", "candidate"))
    sources = {row["host"]: row for row in receipt["sources"]}
    bootstrap = load_bootstrap()
    estimates, archive_receipts = [], []
    for host, path in (("Mac (arm64)", args.mac), ("Linux (x86_64)", args.linux)):
        _, _, _, _, source = presentation.load_host(host, path)
        presentation.require(source["sha256"] == sources[host]["sha256"],
                             "presentation and current archive identities differ")
        archive_receipts.append(source)
        protocol = json.loads((path / "protocol.json").read_text())
        presentation.require(protocol["bootstrap_seed"] == 20261024 and protocol["bootstrap_resamples"] == 10000,
                             "expected original bootstrap seed and resample count")
        records = [json.loads(line) for line in (path / "records.jsonl").read_text().splitlines()]
        indexed = presentation.index_unique(records, ("id", "query", "bias", "cardinality", "method", "trial"))
        settings = list(itertools.product(protocol["biases"], protocol["cardinalities"]))
        for family in ("WSD", "Stock", "MSL"):
            cases = [c for c in protocol["cases"] if c["family"] == family]
            for query in ("grid100", "distinct"):
                def timings(method):
                    return [[[indexed[c["id"], query, bias, card, method, trial]["seconds"] for trial in range(6)]
                             for bias, card in settings] for c in cases]
                reference = float(csv_rows[host, family, query, "raster", "incremental"]["geometric_ratio"])
                estimates.append({
                    "host": host, "family": family, "query": query, "control": "raster", "candidate": "incremental",
                    **direct_summary(timings("raster"), timings("incremental"), reference, bootstrap,
                                     protocol["bootstrap_seed"], protocol["bootstrap_resamples"]),
                })
        for name, expected in source["sha256"].items():
            presentation.require(presentation.digest(path / name) == expected, "archive changed during resampling")
    presentation.require(presentation.digest(csv_path) == csv_sha and presentation.digest(receipt_path) == receipt_sha,
                         "presentation inputs changed during resampling")
    report = {
        "status": "PASS_EXPLORATORY_POST_HOC_DIRECT_COMPARISON",
        "analysis_phase": "EXPLORATORY_POST_HOC_AFTER_SUPPLEMENTAL_RESULTS",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "metric_evaluation_performed": False, "new_timing_performed": False,
        "candidate_metric_code_imported": False,
        "bootstrap_source_sha256": FROZEN_AUDITOR_SHA256,
        "analysis_source_sha256": presentation.digest(__file__),
        "presentation_helper_sha256": presentation.digest(presentation.__file__),
        "presentation_csv_sha256": csv_sha, "presentation_receipt_sha256": receipt_sha,
        "bootstrap_seed": 20261024, "bootstrap_resamples": 10000, "numpy_version": np.__version__,
        "multiplicity": "Six collection/query estimates per host; not across hosts or other comparisons.",
        "uncertainty": "Fixed-panel paired-order bootstrap, shared indices across methods and semantic settings within each recording; no recording resampling.",
        "limits": "Exploratory post-hoc contrast; approximate timing interval from six balanced orders, not population coverage or selection-adjusted inference. No minimum-control interval.",
        "sources": archive_receipts, "estimates": estimates,
    }
    args.out.mkdir(parents=True, exist_ok=False)
    report_path = args.out / "posthoc-direct-raster-incremental.json"
    with report_path.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    (args.out / "posthoc-direct-raster-incremental.md").write_text(markdown(report))
    flattened = [{**{k: v for k, v in row.items() if not isinstance(v, list)},
                  "paired_order_lower": row["paired_order95_interval"][0],
                  "paired_order_upper": row["paired_order95_interval"][1],
                  "min_semantic_ratio": row["semantic_ratio_range"][0],
                  "max_semantic_ratio": row["semantic_ratio_range"][1]} for row in estimates]
    presentation.write_csv(args.out / "posthoc-direct-raster-incremental.csv", flattened)
    print(json.dumps({"status": report["status"], "report": str(report_path),
                      "report_sha256": presentation.digest(report_path), "estimates": len(estimates)}))


if __name__ == "__main__":
    main()
