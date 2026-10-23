"""Independent stdlib-only audit of the completed three-way cost ledger.

This reuses no producer, metric, timing, or report functions. It checks ledger
coverage, immutable input chains, exact certificate outputs, and aggregates.
It does not rerun measurements or prove an absence of host interference.
"""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/msad-certificate-full-cost-20261023"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def records(path):
    with path.open() as stream:
        for line in stream:
            yield json.loads(line)


def main():
    expected_records_sha = "f837144c4d4d08fd1dc00b647f563145defc99e39d64b02a61636155542b1c31"
    expected_report_sha = "ec1baed881703f27427f6ef23762547de6cc66a81a853063eedf6ed5dfddd1ec"
    protocol = json.loads((OUT / "protocol.json").read_text())
    run = json.loads((OUT / "run-inputs.json").read_text())
    report_path = OUT / "report-f837144c4d4d08fd.json"
    report = json.loads(report_path.read_text())
    assert digest(OUT / "records.jsonl") == expected_records_sha
    assert digest(report_path) == expected_report_sha
    protocol_hash = digest(OUT / "protocol.json")
    assert protocol_hash == run["protocol_sha256"] == report["protocol_sha256"]
    assert report["records_sha256"] == expected_records_sha
    hashes = {"protocol.json": protocol_hash, "records.jsonl": expected_records_sha,
              report_path.name: expected_report_sha,
              "run-inputs.json": digest(OUT / "run-inputs.json")}
    for filename, expected in {**protocol["sources"], **run["reference_sha256"]}.items():
        actual = digest(ROOT / filename)
        assert actual == expected, (filename, actual, expected)
        hashes[filename] = actual
    assert run["reference_sha256"] == report["reference_sha256"]

    expected = set(itertools.product(
        [row["series"] for row in protocol["series"]], protocol["models"],
        range(protocol["repetitions"]), protocol["methods"]))
    assert len(expected) == 5400
    series_info = {row["series"]: row for row in protocol["series"]}
    references = {}
    for method, filename in protocol["reference_records"].items():
        chosen = {}
        for row in records(ROOT / filename):
            if method == "exact":
                keep = (row.get("phase") == "numerical" and
                        row.get("method") == "radix_exact" and row.get("width") == 30)
            else:
                keep = row.get("width") == 30 and (
                    row.get("budget") == 250 if method == "certificate"
                    else row.get("budget") == row.get("n"))
            if keep:
                key = row["series"], row["model"]
                assert key not in chosen
                chosen[key] = row
        references[method] = chosen

    found = set()
    times = defaultdict(list)
    ordered = defaultdict(list)
    output_counts = defaultdict(int)
    max_float_difference = 0.0
    for row in records(OUT / "records.jsonl"):
        case = row["series"], row["model"]
        key = (*case, row["repetition"], row["method"])
        assert key in expected and key not in found
        found.add(key)
        assert row["status"] == "ok"
        assert row["width"] == 30 and row["protocol_sha256"] == protocol_hash
        assert math.isfinite(row["seconds"]) and 0 < row["seconds"] <= 30
        assert row["family"] == series_info[row["series"]]["family"]
        assert row["npz_sha256"] == series_info[row["series"]]["npz_sha256"]
        ref_method = "exact" if row["method"] == "radix_exact" else row["method"]
        ref = references[ref_method][case]
        assert ref["status"] == "ok" and row["npz_sha256"] == ref["npz_sha256"]
        assert row["label_sha256"] == ref.get("labels_sha256", ref.get("label_sha256"))
        assert row["score_sha256"] == ref.get("scores_sha256", ref.get("score_sha256"))
        if ref_method == "exact":
            difference = abs(row["value"] - ref["value"])
            assert difference <= protocol["parity_tolerance"]
            max_float_difference = max(max_float_difference, difference)
        else:
            assert row["thresholds"] == ref["budget"]
            for field in ("lower_numerator", "upper_numerator", "scale"):
                assert int(row[field]) == int(ref[field])
            assert row["thresholds_retained"] == ref["thresholds_retained"]
        output_counts[row["method"]] += 1
        times[(*case, row["method"])].append(row["seconds"])
        ordered[(*case, row["repetition"])].append(row["order_index"])
    assert found == expected
    assert all(indices == [0, 1, 2] for indices in ordered.values())
    assert len(ordered) == 1800
    assert all(len(values) == 5 for values in times.values())
    medians = {key: statistics.median(values) for key, values in times.items()}
    cases = sorted({key[:2] for key in times})
    assert len(cases) == report["complete_three_way_cases"] == 360
    assert report["recorded_records"] == report["expected_records"] == 5400
    assert report["missing_records"] == 0 and report["comparative_claim_eligible"]
    assert report["status_counts"] == {"ok": 5400}
    reported_cases = {(row["series"], row["model"]): row for row in report["cases"]}
    assert len(reported_cases) == len(cases)
    for case in cases:
        assert reported_cases[case]["family"] == series_info[case[0]]["family"]
        for method in protocol["methods"]:
            assert medians[(*case, method)] == reported_cases[case]["median_seconds"][method]
    aggregates = {}
    for numerator, denominator in (("certificate", "full_certificate"),
                                   ("certificate", "radix_exact"),
                                   ("full_certificate", "radix_exact")):
        name = numerator + "_over_" + denominator
        ratios = [medians[(*case, numerator)] / medians[(*case, denominator)] for case in cases]
        by_family = defaultdict(list)
        for case, ratio in zip(cases, ratios):
            by_family[series_info[case[0]]["family"]].append(math.log(ratio))
        family = {key: math.exp(statistics.mean(values)) for key, values in by_family.items()}
        computed = {
            "median": statistics.median(ratios),
            "geometric_mean": math.exp(statistics.mean(map(math.log, ratios))),
            "equal_family_geometric_mean": math.exp(statistics.mean(
                statistics.mean(values) for values in by_family.values())),
            "per_family_geometric_mean": family,
        }
        reported = report["ratios"][name]
        for field in ("median", "geometric_mean", "equal_family_geometric_mean"):
            assert math.isclose(computed[field], reported[field], rel_tol=1e-14, abs_tol=1e-14)
        assert set(family) == set(reported["per_family_geometric_mean"])
        for key, value in family.items():
            assert math.isclose(value, reported["per_family_geometric_mean"][key], rel_tol=1e-14)
        aggregates[name] = computed
    sums = {method: math.fsum(medians[(*case, method)] for case in cases)
            for method in protocol["methods"]}
    for method, value in sums.items():
        assert math.isclose(value, report["sum_case_medians_seconds"][method], rel_tol=1e-14)
    result = {
        "status": "PASS_INDEPENDENT_STDLIB_COST_LEDGER_AUDIT",
        "utc": datetime.now(timezone.utc).isoformat(),
        "auditor_sha256": digest(Path(__file__)), "verified_sha256": hashes,
        "records": len(found), "complete_three_way_cases": len(cases),
        "series": len(series_info), "families": len({v["family"] for v in series_info.values()}),
        "repetitions_per_case_method": 5, "validated_outputs": dict(output_counts),
        "max_float_difference": max_float_difference,
        "ratios": aggregates, "sum_case_medians_seconds": sums,
        "scope": "Independent ledger/hash/coverage/output/aggregate audit. No producer functions imported; no timing reruns or host-interference proof.",
    }
    path = OUT / "independent-cost-ledger-audit.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "records": len(found), "path": str(path),
                      "sha256": digest(path), "ratios": {k: {x: v[x] for x in ("median", "geometric_mean")}
                                                            for k, v in aggregates.items()}}, indent=2))


if __name__ == "__main__":
    main()
