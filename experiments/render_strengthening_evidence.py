"""Present audited interval-control archives without new metric evaluation.

Ratios come directly from per-method median saved durations. Audited contrasts
retain their original intervals; derived contrasts and the post-hoc faster-
control scatter receive no new or borrowed interval. Hosts are never pooled.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
import statistics

METHODS = ("raster", "interval", "incremental")
PAIRS = (("raster", "incremental"), ("interval", "incremental"), ("raster", "interval"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometric_mean(values):
    require(bool(values) and all(math.isfinite(v) and v > 0 for v in values), "invalid positive timings/ratios")
    return math.exp(math.fsum(math.log(v) for v in values) / len(values))


def check_close(actual, expected, message):
    require(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), message)


def index_unique(rows, fields):
    result = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        require(key not in result, "duplicate identity: " + repr(key))
        result[key] = row
    return result


def comparison_summary(values, reference):
    ratio = geometric_mean(values)
    wins, losses = sum(v > 1 for v in values), sum(v < 1 for v in values)
    if reference is not None:
        check_close(ratio, reference["geometric_ratio"], "ratio differs from independent audit")
        check_close(min(values), reference["min_ratio"], "minimum recording ratio differs")
        check_close(max(values), reference["max_ratio"], "maximum recording ratio differs")
        require((len(values), wins) == (reference["units"], reference["wins"]), "audited coverage/wins differ")
    return {"geometric_ratio": ratio, "recordings": len(values), "wins": wins, "losses": losses,
            "ties": len(values) - wins - losses, "min_recording_ratio": min(values), "max_recording_ratio": max(values),
            "contrast_kind": "audited_prespecified_contrast" if reference else "derived_fixed_contrast_no_new_interval",
            "paired_order_lower": reference["paired_order95_interval"][0] if reference else "",
            "paired_order_upper": reference["paired_order95_interval"][1] if reference else "",
            "recording_sensitivity_lower": reference["recording_reweighting95_interval"][0] if reference else "",
            "recording_sensitivity_upper": reference["recording_reweighting95_interval"][1] if reference else ""}


def load_host(host, path):
    path = Path(path).resolve()
    protocol = json.loads((path / "protocol.json").read_text())
    report = json.loads((path / "independent-report.json").read_text())
    complete = json.loads((path / "complete.json").read_text())
    hashes = {name: digest(path / name) for name in ("protocol.json", "records.jsonl", "complete.json", "independent-report.json")}
    require(report["status"] == "PASS" and complete["status"] == "COMPLETE", "completed independent audit required")
    for receipt in (complete, report):
        require(receipt["protocol_sha256"] == hashes["protocol.json"] and receipt["records_sha256"] == hashes["records.jsonl"],
                "archive/report hash binding differs")
    require(report["winner_disagreements"] == 0 and report["max_curve_error"] <= protocol["parity_atol"], "output parity missing")
    require(protocol["model_order"] == ["FFT", "COPOD"], "expected frozen FFT/COPOD panel")
    require(protocol.get("incremental_mapping") == {"grid100": "bucket", "distinct": "sweep"}, "expected interval-control study")
    require(set(protocol["queries"]) == {"grid100", "distinct"}, "query coverage differs")
    require(len(protocol["orders"]) == 6 and all(len(order) == 3 and set(order) == set(METHODS) for order in protocol["orders"])
            and len({tuple(order) for order in protocol["orders"]}) == 6, "expected six balanced method orders")
    cases = index_unique(protocol["cases"], ("id",))
    require(len(cases) == report["cases"] == 26, "incomplete panel")
    require({f: sum(c["family"] == f for c in cases.values()) for f in ("WSD", "Stock", "MSL")}
            == {"WSD": 12, "Stock": 12, "MSL": 2}, "family coverage differs")
    settings = list(itertools.product(protocol["biases"], protocol["cardinalities"]))
    require(len(set(settings)) == len(settings) == 12, "semantic coverage differs")
    records = [json.loads(line) for line in (path / "records.jsonl").read_text().splitlines()]
    keyed = index_unique(records, ("id", "query", "bias", "cardinality", "method", "trial"))
    expected = {(c[0], q, b, g, m, t) for c in cases for q in protocol["queries"]
                for b, g in settings for m in METHODS for t in range(6)}
    require(set(keyed) == expected and len(records) == report["records"], "record coverage differs")
    original_semantics = index_unique(report["semantic_timing"], ("family", "query", "bias", "cardinality", "control", "candidate"))
    original_aggregates = index_unique(report["aggregate_timing"], ("family", "query", "control", "candidate"))
    declared = {(f, q, c, d) for f in ("WSD", "Stock", "MSL") for q, c, d in protocol["comparisons"]}
    require(set(original_aggregates) == declared and set(original_semantics)
            == {(f, q, b, g, c, d) for f, q, c, d in declared for b, g in settings}, "audited comparison coverage differs")
    medians, counts, detailed, recordings = {}, {}, [], []
    for (identifier,), case in cases.items():
        for query in protocol["queries"]:
            for bias, card in settings:
                times = {}
                for method in METHODS:
                    group = [keyed[identifier, query, bias, card, method, t] for t in range(6)]
                    for row in group:
                        require((row["family"], row["n"]) == (case["family"], case["n"]), "record metadata differs")
                        require(math.isfinite(row["seconds"]) and row["seconds"] > 0, "invalid saved duration")
                        require(len(row["query_counts"]) == 2 and all(type(v) is int and v > 0 for v in row["query_counts"]),
                                "invalid detector query counts")
                        counts.setdefault((identifier, query), row["query_counts"])
                        require(row["query_counts"] == counts[identifier, query], "query counts vary by method/setting/trial")
                    times[method] = statistics.median(row["seconds"] for row in group)
                    medians[identifier, query, bias, card, method] = times[method]
                check_close(times["raster"] / times["incremental"],
                            (times["raster"] / times["interval"]) * (times["interval"] / times["incremental"]),
                            "per-setting direct/indirect contrast differs")
                detailed.append({"host": host, "id": identifier, "family": case["family"], "n": case["n"],
                                 "query": query, "bias": bias, "cardinality": card,
                                 **{m + "_median_seconds": times[m] for m in METHODS},
                                 **{c + "_over_" + d: times[c] / times[d] for c, d in PAIRS}})
            times = {m: geometric_mean([medians[identifier, query, b, g, m] for b, g in settings]) for m in METHODS}
            ratios = {(c, d): geometric_mean([medians[identifier, query, b, g, c] / medians[identifier, query, b, g, d]
                                             for b, g in settings]) for c, d in PAIRS}
            for (control, candidate), value in ratios.items():
                check_close(value, times[control] / times[candidate], "per-recording ratio aggregation differs")
            faster = min(("raster", "interval"), key=lambda m: (times[m], m))
            faster_ratio = min(ratios["raster", "incremental"], ratios["interval", "incremental"])
            check_close(faster_ratio, times[faster] / times["incremental"], "post-hoc control choice differs")
            qcounts = counts[identifier, query]
            recordings.append({"host": host, "id": identifier, "family": case["family"], "n": case["n"], "query": query,
                               "fft_queries": qcounts[0], "copod_queries": qcounts[1], "total_queries": sum(qcounts),
                               "mean_queries_per_detector": statistics.mean(qcounts), "semantic_settings": len(settings),
                               **{m + "_geomean_median_seconds": times[m] for m in METHODS},
                               **{c + "_over_" + d: ratios[c, d] for c, d in PAIRS},
                               "posthoc_faster_control": faster, "posthoc_faster_control_over_incremental": faster_ratio})
    semantics, aggregates = [], []
    for family in ("WSD", "Stock", "MSL"):
        group = [case for case in cases.values() if case["family"] == family]
        for query in protocol["queries"]:
            for control, candidate in PAIRS:
                for bias, card in settings:
                    values = [medians[c["id"], query, bias, card, control] / medians[c["id"], query, bias, card, candidate] for c in group]
                    reference = original_semantics.get((family, query, bias, card, control, candidate))
                    semantics.append({"host": host, "family": family, "query": query, "bias": bias, "cardinality": card,
                                      "control": control, "candidate": candidate, **comparison_summary(values, reference)})
                values = [next(r[control + "_over_" + candidate] for r in recordings if r["id"] == c["id"] and r["query"] == query) for c in group]
                reference = original_aggregates.get((family, query, control, candidate))
                aggregates.append({"host": host, "family": family, "query": query, "control": control,
                                   "candidate": candidate, **comparison_summary(values, reference)})
    sem_index = index_unique(semantics, ("family", "query", "bias", "cardinality", "control", "candidate"))
    agg_index = index_unique(aggregates, ("family", "query", "control", "candidate"))
    for family in ("WSD", "Stock", "MSL"):
        for query in protocol["queries"]:
            for bias, card in settings:
                prefix = (family, query, bias, card)
                check_close(sem_index[prefix + ("raster", "incremental")]["geometric_ratio"],
                            sem_index[prefix + ("raster", "interval")]["geometric_ratio"] * sem_index[prefix + ("interval", "incremental")]["geometric_ratio"],
                            "collection semantic direct/indirect contrast differs")
            prefix = (family, query)
            check_close(agg_index[prefix + ("raster", "incremental")]["geometric_ratio"],
                        agg_index[prefix + ("raster", "interval")]["geometric_ratio"] * agg_index[prefix + ("interval", "incremental")]["geometric_ratio"],
                        "aggregate direct/indirect contrast differs")
    for name, expected_sha in hashes.items():
        require(digest(path / name) == expected_sha, "archive changed during rendering preparation")
    return recordings, detailed, semantics, aggregates, {
        "host": host, "archive": str(path), "sha256": hashes,
        "case_order": [{"id": c["id"], "family": c["family"], "n": c["n"]} for c in cases.values()],
        "independent_audit_local_input_bytes_verified": report["local_input_bytes_verified"],
        "audited_semantic_rows_reconstructed": len(original_semantics), "audited_aggregate_rows_reconstructed": len(original_aggregates),
        "direct_indirect_ratio_checks": "all recording/settings and collection/settings/aggregates agree within 1e-12"}


def write_csv(path, rows):
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def render_scatter(output, points, sources):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, FixedLocator
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9,
                         "axes.labelsize": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
    count = len(sources)
    figure, axes = plt.subplots(1, count, figsize=(3.45 * count, 3.0), sharex=True, sharey=True,
                                squeeze=False, layout="constrained")
    styles = (("WSD", "#0072B2", "o"), ("Stock", "#D55E00", "^"), ("MSL", "#009E73", "s"))
    distinct = [p for p in points if p["query"] == "distinct"]
    xs = [p["total_queries"] for p in distinct]
    ys = [p["posthoc_faster_control_over_incremental"] for p in distinct]
    ymin, ymax = min(min(ys) / 1.5, 0.7), max(max(ys) * 1.5, 1.5)
    ticks = [v for v in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500) if ymin <= v <= ymax]
    for index, source in enumerate(sources):
        ax = axes[0, index]
        group = [p for p in distinct if p["host"] == source["host"]]
        for family, color, marker in styles:
            rows = [p for p in group if p["family"] == family]
            ax.scatter([p["total_queries"] for p in rows], [p["posthoc_faster_control_over_incremental"] for p in rows],
                       label=f"{family} (n={len(rows)})", color=color, marker=marker,
                       s=25, alpha=0.85, edgecolors="white", linewidths=0.35, zorder=3)
        ax.axhline(1, color="#555555", linestyle="--", linewidth=0.8, zorder=2)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlim(min(xs) / 1.5, max(xs) * 1.35); ax.set_ylim(ymin, ymax)
        ax.yaxis.set_major_locator(FixedLocator(ticks))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:g}"))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:,.0f}"))
        ax.set_xlabel("Distinct queries (FFT + COPOD)"); ax.set_title(source["host"])
        ax.grid(which="major", alpha=0.18, linewidth=0.5, zorder=0)
        ax.spines[["top", "right"]].set_visible(False); ax.tick_params(which="minor", length=2)
        for point in group:
            if point["family"] == "MSL" and point["posthoc_faster_control_over_incremental"] < 1:
                label = "MSL id" + point["id"].split("_id_")[1].split("_")[0]
                ax.annotate(label, (point["total_queries"], point["posthoc_faster_control_over_incremental"]),
                            xytext=(7, -10), textcoords="offset points", fontsize=6.5, color="#006B52")
        if index == count - 1:
            ax.legend(frameon=False, fontsize=6.7, loc="upper left", handletextpad=0.4, borderaxespad=0.3, labelspacing=0.35)
    axes[0, 0].set_ylabel("Incremental speedup\nvs. faster compiled control")
    figure.supxlabel("Post-hoc control choice per recording; descriptive, no CI", fontsize=7)
    figure.savefig(output / "interval-control-query-regime.pdf", metadata={
        "Title": "Post-hoc incremental speedup against the faster compiled control",
        "Subject": "Fixed-panel descriptive saved-data analysis; no confidence interval", "CreationDate": None, "ModDate": None})
    figure.savefig(output / "interval-control-query-regime.png", dpi=300)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mac", type=Path, required=True)
    parser.add_argument("--linux", type=Path, help="Optional completed audited Linux interval-control archive")
    parser.add_argument("--mac-label", default="Mac (arm64)")
    parser.add_argument("--linux-label", default="Linux (x86_64)")
    parser.add_argument("--output", type=Path, required=True, help="New directory; refuses replacement")
    args = parser.parse_args()
    require(not args.output.exists(), "refusing to replace a presentation directory")
    hosts = [(args.mac_label, args.mac)] + ([(args.linux_label, args.linux)] if args.linux is not None else [])
    require(len({h for h, _ in hosts}) == len(hosts), "host labels must differ")
    recordings, detailed, semantics, aggregates, sources = [], [], [], [], []
    for host, path in hosts:
        a, b, c, d, source = load_host(host, path)
        recordings.extend(a); detailed.extend(b); semantics.extend(c); aggregates.extend(d); sources.append(source)
    require(all(s["case_order"] == sources[0]["case_order"] for s in sources), "host cohorts differ")
    args.output.mkdir(parents=True, exist_ok=False)
    for name, rows in (("weighted-recordings.csv", recordings), ("weighted-recording-semantics.csv", detailed),
                       ("weighted-semantics.csv", semantics), ("weighted-aggregates.csv", aggregates)):
        write_csv(args.output / name, rows)
    render_scatter(args.output, recordings, sources)
    receipt = {
        "status": "PASS_AUDITED_SAVED_DATA_PRESENTATION", "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Saved-data presentation and cross-checking; no new fits, metrics, timings or intervals.",
        "sources": sources, "recording_query_rows": len(recordings), "plotted_recordings": len(recordings) // 2,
        "recording_semantic_rows": len(detailed), "collection_semantic_rows": len(semantics), "aggregate_rows": len(aggregates),
        "x_definition": "Sum of distinct query counts across FFT and COPOD, matching the two-profile timed workflow; CSV also contains their mean and individual counts.",
        "y_definition": "min(GM_semantics median_trials raster/incremental time, GM_semantics median_trials interval/incremental time), selecting one control per recording after equal-log aggregation across all 12 settings.",
        "scatter_inference": "Post-hoc descriptive control choice; no CI, preregistration or population inference.",
        "csv_intervals": "Existing intervals only for audited prespecified contrasts. Direct raster/incremental contrasts use raw medians and agree with products of original contrasts; their interval fields are blank.",
        "host_policy": "Separate host panels and source-specific generated score/query identities; timings never pooled.",
        "renderer_sha256": digest(__file__), "render_packages": {n: importlib.metadata.version(n) for n in ("matplotlib", "numpy")},
        "outputs": {p.name: digest(p) for p in sorted(args.output.iterdir()) if p.is_file()},
    }
    with (args.output / "presentation-receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps({"status": receipt["status"], "output": str(args.output),
                      "plotted_recordings": receipt["plotted_recordings"], "aggregate_rows": len(aggregates)}))


if __name__ == "__main__":
    main()
