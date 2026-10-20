"""Stdlib-only reconstruction of sensitivity counts, independent of the driver."""
from collections import defaultdict
import csv
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOL = 1e-10


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows = [json.loads(line) for line in (HERE / "records.jsonl").read_text().splitlines()]
    summaries = json.loads((HERE / "summary.json").read_text())
    inventory = json.loads((HERE / "inventory.json").read_text())
    protocol = json.loads((HERE / "protocol.json").read_text())
    expected_keys = set(itertools.product(
        protocol["variants"], [r["series"] for r in inventory],
        protocol["models"], protocol["max_buffer"]))
    exclusions = json.loads((HERE / "exclusions.json").read_text())
    excluded = {(r["variant"], r["series"]) for r in exclusions}
    expected_keys = {key for key in expected_keys if key[:2] not in excluded}
    actual_keys = [(r["variant"], r["series"], r["model"], r["max_buffer"]) for r in rows]
    assert set(actual_keys) == expected_keys and len(actual_keys) == len(expected_keys)
    groups = defaultdict(list)
    for row in rows:
        groups[row["variant"], row["series"], row["max_buffer"]].append(row)
    metrics = defaultdict(lambda: {
        "pairs": 0, "strict_reversals": 0, "exact_ties": 0, "sampled_ties": 0,
        "unique_top_changes": 0, "top_cases": 0, "series": set(),
        "families": set(), "material_reversals": {"0.0001": 0, "0.001": 0, "0.01": 0}})
    family_counts = defaultdict(lambda: {"pairs": 0, "reversals": 0})
    reversal_sets = defaultdict(set)
    eligible_sets = defaultdict(set)
    for (variant, series, width), group in groups.items():
        assert len(group) == 3
        for metric_index, metric in enumerate(("ROC", "PR")):
            entry = metrics[variant, metric]
            entry["top_cases"] += 1
            ex = {r["model"]: r["exact"][metric_index] for r in group}
            ap = {r["model"]: r["sampled250"][metric_index] for r in group}
            ex_top = {m for m in ex if abs(ex[m] - max(ex.values())) <= TOL}
            ap_top = {m for m in ap if abs(ap[m] - max(ap.values())) <= TOL}
            entry["unique_top_changes"] += len(ex_top) == len(ap_top) == 1 and ex_top != ap_top
            for a, b in itertools.combinations(sorted(group, key=lambda r: r["model"]), 2):
                x = a["exact"][metric_index] - b["exact"][metric_index]
                z = a["sampled250"][metric_index] - b["sampled250"][metric_index]
                et, st = abs(x) <= TOL, abs(z) <= TOL
                reverse = not et and not st and ((x < 0 < z) or (z < 0 < x))
                entry["pairs"] += 1
                entry["exact_ties"] += et
                entry["sampled_ties"] += st
                family_counts[variant, metric, a["family"]]["pairs"] += 1
                key = series, width, a["model"], b["model"]
                eligible_sets[variant, metric].add(key)
                if reverse:
                    entry["strict_reversals"] += 1
                    entry["series"].add(series)
                    entry["families"].add(a["family"])
                    family_counts[variant, metric, a["family"]]["reversals"] += 1
                    reversal_sets[variant, metric].add(key)
                    for margin in entry["material_reversals"]:
                        entry["material_reversals"][margin] += min(abs(x), abs(z)) >= float(margin)
    confirmed = {}
    for (variant, metric), actual in metrics.items():
        actual["affected_series"] = len(actual.pop("series"))
        actual["affected_families"] = sorted(actual.pop("families"))
        expected = summaries["variants"][variant]["metrics"][metric]
        for key, value in actual.items():
            assert value == expected[key], (variant, metric, key, value, expected[key])
        confirmed[f"{variant}/{metric}"] = actual
    with (HERE / "family_effects.csv").open() as stream:
        for row in csv.DictReader(stream):
            actual = family_counts[row["variant"], row["metric"], row["family"]]
            assert actual["pairs"] == int(row["pairs"])
            assert actual["reversals"] == int(row["strict_reversals"])
    for variant in protocol["variants"]:
        if variant == "released":
            continue
        for metric in ("ROC", "PR"):
            before = reversal_sets["released", metric] & eligible_sets[variant, metric]
            after = reversal_sets[variant, metric]
            expected = summaries["reversal_overlap"][variant][metric]
            assert len(before & after) == expected.get("persistent", 0)
            assert len(before - after) == expected.get("lost", 0)
            assert len(after - before) == expected.get("new", 0)
    original = [json.loads(line) for line in (ROOT / "artifacts/public_benchmark.jsonl").read_text().splitlines()]
    old = {(r["series"], r["model"], r["max_buffer"]): r for r in original}
    reuse = 0
    for row in rows:
        if row["reused_original_result"]:
            source = old[row["series"], row["model"], row["max_buffer"]]
            assert row["exact"] == source["exact"] and row["sampled250"] == source["sampled250"]
            reuse += 1
    result = {"status": "PASS", "implementation": "Separate stdlib-only count reconstruction",
              "records": len(rows), "all_case_pairs": sum(r["pairs"] for r in metrics.values()),
              "reused_rows_equal_original": reuse, "confirmed": confirmed,
              "checked": ["coverage", "all strict/tie/material/top counts", "family counts",
                          "overlap counts", "reused values equal original"],
              "not_checked": ["new numerical kernels rerun", "bootstrap draws independently reproduced"],
              "input_sha256": {name: digest(HERE / name) for name in
                               ("records.jsonl", "summary.json", "family_effects.csv", "protocol.json")},
              "checker_sha256": digest(Path(__file__))}
    (HERE / "independent_check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("confirmed", "input_sha256")}, indent=2))


if __name__ == "__main__":
    main()
