"""Independent tiny receipts reject materially false PR-engine success claims."""
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
sys.path.insert(0, str(EXPERIMENTS))
METHODS = ["sparse_pr", "dense_pr_direct", "sparse_both", "dense_nearest_both",
           "klein_pr", "benchopt_both", "radix_pr", "radix_both",
           "dense_pr_direct_radix", "dense_pr_nearest_radix", "v02_race", "fast_race",
           "fast_exact_completion", "fast_race_radix"]
EXACT = METHODS[:10]


def audit():
    assert importlib.util.find_spec("audit_pr_engine") is not None, "Independent PR-engine auditor missing"
    return importlib.import_module("audit_pr_engine")


def fixture():
    models = ["A", "B", "C"]
    inputs = [{"series": "tiny", "family": "synthetic", "n": 4, "max_buffer": 30,
               "label_sha256": "0" * 64, "score_sha256": {m: m.lower() * 64 for m in models}}]
    protocol = {"version": 3, "split": "development", "cases": 1,
                "models": models, "widths": [30, 100, 300], "primary_widths": [30, 100],
                "task_order": "width_then_series",
                "repetitions": 3, "seed": 2026102101, "method_ids": METHODS,
                "primary_width": 30, "secondary_width": 100, "stress_width": 300,
                "bootstrap": {"unit": "family", "repetitions": 2000, "seed": 2026102102,
                              "confidence": .95, "references": ["fast_race", "sparse_pr", "radix_pr", "fast_race_radix"]},
                "adaptive_fraction": .125, "memory_bytes_per_model": 8 * 1024 * 1024,
                "include_full_budget": False, "tie_atol": 1e-10,
                "order_margin": 3e-10, "containment_tolerance": 1e-10,
                "exact_parity_tolerance": 1e-11}
    values = {m: {"selected": ["A"], "pr": {"A": .9, "B": .5, "C": .1}}
              for m in EXACT}
    for method in METHODS[len(EXACT):]:
        bounds = {m: {"pr_lower": value, "pr_upper": value, "exact": True,
                      "evaluated_widths": list(range(31)), "curve_evaluations": 31}
                  for m, value in zip(models, (.9, .5, .1))}
        result = {"selected": ["A"], "candidates": ["A"], "bounds": bounds,
                  "total_unique_widths": 93, "total_curve_evaluations": 93,
                  "full_evaluation_count": 3,
                  "exact_pr": {"A": .9, "B": .5, "C": .1}}
        if method == "v02_race":
            result.update(early_winner=True, pruned=["B", "C"],
                          initial_unique_widths=93, initial_curve_evaluations=93, refinement_steps=0)
        else:
            result.update(early_winner=False, fallback_models=models,
                          retained_curve_bytes=0, adaptive_curve_evaluations=0,
                          completion_curve_evaluations=93)
        values[method] = result
    medians = {m: float(i + 1) for i, m in enumerate(METHODS)}
    rng = random.Random(protocol["seed"])
    order = []
    for _ in range(3):
        permutation = METHODS.copy()
        rng.shuffle(permutation)
        order.append(permutation)
    row = {**deepcopy(inputs[0]), "values": values,
           "seconds": {m: [t / 2, t, 2 * t] for m, t in medians.items()},
           "median_seconds": medians, "method_order": order}
    return [row], protocol, inputs


def test_valid_full_exact_receipt_and_separate_comparator_statistics():
    rows, protocol, inputs = fixture()
    result = audit().audit_records(rows, protocol, inputs)
    assert result["cases"] == 1
    stats = result["by_width"]["30"]["methods"]["fast_race"]["by_comparator"]
    assert stats["sparse_pr"]["median"] == 1 / 12
    assert stats["dense_pr_direct"]["aggregate_ratio"] == 2 / 12
    assert stats["sparse_pr"]["slower_cases"] == 1


@pytest.mark.parametrize("change", ["selection", "exact_value", "bounds", "score_hash",
                                  "duplicate", "missing_method", "order", "recomputed",
                                  "false_exact", "fallback_count", "hidden_phase_work", "hidden_fallback"])
def test_reject_false_claims_even_when_basic_coverage_is_plausible(change):
    rows, protocol, inputs = fixture()
    row = rows[0]
    if change == "selection":
        row["values"]["fast_race"]["selected"] = ["B"]
    elif change == "exact_value":
        row["values"]["dense_pr_direct"]["pr"]["A"] = .8
    elif change == "bounds":
        row["values"]["fast_race"]["bounds"]["B"].update(pr_lower=.6, pr_upper=.6)
    elif change == "score_hash":
        row["score_sha256"]["A"] = "9" * 64
    elif change == "duplicate":
        rows.append(deepcopy(row))
    elif change == "missing_method":
        del row["values"]["benchopt_both"]
    elif change == "order":
        row["method_order"][0] = list(reversed(row["method_order"][0]))
    elif change == "recomputed":
        row["values"]["fast_race"]["bounds"]["A"]["curve_evaluations"] += 1
        row["values"]["fast_race"]["total_curve_evaluations"] += 1
        row["values"]["fast_race"]["completion_curve_evaluations"] += 1
    elif change == "false_exact":
        row["values"]["fast_race"]["bounds"]["A"]["evaluated_widths"].pop()
    elif change == "fallback_count":
        row["values"]["fast_exact_completion"]["fallback_models"] = ["A"]
    elif change == "hidden_fallback":
        row["values"]["fast_race"]["fallback_models"] = []
    else:
        row["values"]["fast_race"]["completion_curve_evaluations"] -= 1
    with pytest.raises(ValueError):
        audit().audit_records(rows, protocol, inputs)


@pytest.mark.parametrize("duration", [0, -1, float("nan"), float("inf"), True])
def test_nonpositive_nonfinite_or_boolean_duration_is_not_a_speed_measurement(duration):
    rows, protocol, inputs = fixture()
    rows[0]["seconds"]["fast_race"][0] = duration
    with pytest.raises(ValueError):
        audit().audit_records(rows, protocol, inputs)


def test_numeric_margin_does_not_allow_dropping_a_true_tolerance_tie():
    rows, protocol, inputs = fixture()
    for result in rows[0]["values"].values():
        if "pr" in result:
            result["pr"]["B"] = .9 - 5e-11
            result["selected"] = ["A", "B"]
    # A false success receipt preserves the previous unique winner and exclusion.
    with pytest.raises(ValueError):
        audit().audit_records(rows, protocol, inputs)


def test_full_budget_variant_cannot_enter_holdout_by_relabeling_protocol():
    rows, protocol, inputs = fixture()
    protocol.update(split="holdout", include_full_budget=True)
    with pytest.raises(ValueError):
        audit().audit_records(rows, protocol, inputs)


def test_cluster_bootstrap_keeps_whole_families_and_reports_constant_ratio_exactly():
    rows, protocol, inputs = fixture()
    result = audit().audit_records(rows, protocol, inputs)
    ci = result["uncertainty"]["30"]["fast_race"]["sparse_pr"]
    assert ci["geomean_ci95"] == pytest.approx([1 / 12, 1 / 12])
    assert ci["aggregate_ratio_ci95"] == pytest.approx([1 / 12, 1 / 12])
    assert ci["families"] == 1
    assert result["primary_decision"]["passes"] is False


def test_freeze_needs_no_kernel_import_or_corpus_load(tmp_path, monkeypatch):
    assert importlib.util.find_spec("benchmark_pr_engine") is not None, "PR-engine driver missing"
    driver = importlib.import_module("benchmark_pr_engine")
    models = ["A", "B", "C"]
    metadata = {f"s{i:03}": {"n": 4, "family": f"f{i % 23}", "label_sha256": "0" * 64}
                for i in range(350)}
    score_hashes = {(s, m): "1" * 64 for s in metadata for m in models}
    monkeypatch.setattr(driver, "released_metadata", lambda root: (
        metadata, models, score_hashes, list(metadata)[:42], {}, {}))
    monkeypatch.setattr(driver, "source_hashes", lambda root: {"fixture": "2" * 64})
    monkeypatch.setattr(driver, "make_methods", lambda *a, **k: pytest.fail("Freeze executed a kernel adapter"))
    development = driver.freeze(tmp_path / "dev", "development")
    holdout = driver.freeze(tmp_path / "held", "holdout")
    assert development["cases"] == 126
    assert holdout["cases"] == 924
    dev_ids = {r["series"] for r in json.loads((tmp_path / "dev/inputs.json").read_text())}
    held_ids = {r["series"] for r in json.loads((tmp_path / "held/inputs.json").read_text())}
    assert dev_ids.isdisjoint(held_ids) and len(dev_ids | held_ids) == 350
    held_inputs = json.loads((tmp_path / "held/inputs.json").read_text())
    assert [r["max_buffer"] for r in held_inputs] == [30] * 308 + [100] * 308 + [300] * 308
    assert [(r["max_buffer"], r["series"]) for r in held_inputs] == sorted(
        (r["max_buffer"], r["series"]) for r in held_inputs)
    # Neither a matching new file digest nor a current source mutation may
    # silently turn the existing freeze into a different measured experiment.
    protocol_hash = driver.digest(tmp_path / "held/protocol.json")
    driver.validate_frozen(tmp_path / "held", protocol_hash, "holdout")
    monkeypatch.setattr(driver, "source_hashes", lambda root: {"fixture": "3" * 64})
    with pytest.raises(ValueError, match="Source changed"):
        driver.validate_frozen(tmp_path / "held", protocol_hash, "holdout")
    with pytest.raises(ValueError, match="development"):
        driver.freeze(tmp_path / "bad", "holdout", include_full_budget=True)
    assert not (tmp_path / "bad").exists()


def test_unequal_family_sizes_are_resampled_as_clusters_not_individual_cases():
    _, protocol, _ = fixture()
    cases = [{"family": "large", "max_buffer": 30, "median_seconds": {"fast_race": 1., "sparse_pr": 2.}}
             for _ in range(3)]
    cases.append({"family": "small", "max_buffer": 30, "median_seconds": {"fast_race": 100., "sparse_pr": 50.}})
    specification = {**protocol["bootstrap"], "references": ["fast_race", "sparse_pr"]}
    result = audit().uncertainty(cases, ["fast_race", "sparse_pr"], specification)
    # Two sampled clusters give AA, AB, or BB. BB has 25% probability; a case
    # bootstrap's four B observations would instead have only 1/256 probability.
    assert result["30"]["fast_race"]["sparse_pr"]["geomean_ci95"] == pytest.approx([.5, 2.])
    assert result["30"]["fast_race"]["sparse_pr"]["aggregate_ratio_ci95"] == pytest.approx([.5, 2.])


def run_files(tmp_path, monkeypatch):
    module = audit()
    rows, protocol, inputs = fixture()
    root, output = tmp_path / "source", tmp_path / "run"
    output.mkdir()
    protocol["source_sha256"] = {}
    for name in module.REQUIRED_SOURCES:
        path = root / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text("independent tiny fixture: " + name)
        protocol["source_sha256"][name] = module.sha(path)
    (output / "inputs.json").write_text(json.dumps(inputs))
    protocol["inputs_sha256"] = module.sha(output / "inputs.json")
    (output / "protocol.json").write_text(json.dumps(protocol))
    (output / "measurements.jsonl").write_text(json.dumps(rows[0]) + "\n")
    environment = {"protocol_sha256": module.sha(output / "protocol.json"),
                   "source_sha256": protocol["source_sha256"], "threads": 1,
                   "threadpool_info": [{"num_threads": 1}],
                   "warmup_seconds": {m: .001 for m in METHODS}}
    summary = {"status": "PASS", "violations": [],
               "protocol_sha256": module.sha(output / "protocol.json"),
               "measurements_sha256": module.sha(output / "measurements.jsonl"),
               "reconstructed": module.audit_records(rows, protocol, inputs)}
    (output / "environment.json").write_text(json.dumps(environment))
    (output / "summary.json").write_text(json.dumps(summary))
    monkeypatch.setattr(module, "validate_inputs_manifest", lambda *a, **kw: {"status": "PASS", "fixture": True})
    return module, root, output, rows, protocol, environment, summary


def test_complete_tiny_run_passes_independent_reconstruction(tmp_path, monkeypatch):
    module, root, output, *_ = run_files(tmp_path, monkeypatch)
    assert module.audit_run(output, root=root)["status"] == "PASS"


@pytest.mark.parametrize("tamper", ["bound", "exact", "summary", "source", "protocol", "missing_source", "input"])
def test_rehashed_false_success_is_rejected(tmp_path, monkeypatch, tamper):
    module, root, output, rows, protocol, environment, summary = run_files(tmp_path, monkeypatch)
    if tamper == "bound":
        rows[0]["values"]["fast_race"]["bounds"]["B"].update(pr_lower=.8, pr_upper=.8)
    elif tamper == "exact":
        rows[0]["values"]["klein_pr"]["pr"]["C"] = .2
    elif tamper == "summary":
        summary["reconstructed"]["by_width"]["30"]["methods"]["fast_race"]["by_comparator"]["sparse_pr"]["aggregate_ratio"] = 8.
    elif tamper == "source":
        (root / "src/sparse_vus/pr_compiled.py").write_text("new metric implementation")
    elif tamper == "protocol":
        protocol["containment_tolerance"] = .5
    elif tamper == "missing_source":
        del protocol["source_sha256"]["src/sparse_vus/pr_compiled.py"]
        environment["source_sha256"] = protocol["source_sha256"]
    else:
        inputs = json.loads((output / "inputs.json").read_text())
        inputs[0]["score_sha256"]["A"] = "9" * 64
        (output / "inputs.json").write_text(json.dumps(inputs))
        protocol["inputs_sha256"] = module.sha(output / "inputs.json")
    # Recompute all hashes after tampering, leaving a claimed PASS summary.
    (output / "measurements.jsonl").write_text(json.dumps(rows[0]) + "\n")
    summary["measurements_sha256"] = module.sha(output / "measurements.jsonl")
    (output / "protocol.json").write_text(json.dumps(protocol))
    summary["protocol_sha256"] = environment["protocol_sha256"] = module.sha(output / "protocol.json")
    (output / "environment.json").write_text(json.dumps(environment))
    (output / "summary.json").write_text(json.dumps(summary))
    with pytest.raises(ValueError):
        module.audit_run(output, root=root)


def test_numpy_producer_and_stdlib_auditor_agree_on_whole_case_statistics():
    driver = importlib.import_module("benchmark_pr_engine")
    rows, protocol, inputs = fixture()
    # A second, differently sized cost cluster exercises geomean, ratio-of-sums,
    # percentiles, macro-family weights, and clustered uncertainty together.
    second = deepcopy(rows[0])
    second.update(series="tiny2", family="other")
    for name in METHODS:
        second["seconds"][name] = [v * (2 if name == "sparse_pr" else 7) for v in second["seconds"][name]]
        second["median_seconds"][name] *= 2 if name == "sparse_pr" else 7
    rows.append(second)
    inputs.append({key: deepcopy(second[key]) for key in audit().IDENTITY})
    protocol["cases"] = 2
    rng = random.Random(protocol["seed"])
    for row in rows:
        row["method_order"] = []
        for _ in range(3):
            order = METHODS.copy()
            rng.shuffle(order)
            row["method_order"].append(order)
    audit().compare(driver.summarize(rows, protocol), audit().audit_records(rows, protocol, inputs))


def test_actual_tiny_adapters_preserve_full_metric_and_racer_result_contracts():
    np = pytest.importorskip("numpy")
    pytest.importorskip("numba")
    from benchmark_pr_engine import make_methods, serialize_result
    rows, protocol, inputs = fixture()
    protocol = deepcopy(protocol)
    protocol["include_full_budget"] = True
    protocol["method_ids"] = [*METHODS, "fast_full_budget"]
    methods = make_methods(protocol)
    labels = np.array([0, 1, 1, 0, 0, 0, 1, 0], dtype=np.int8)
    scores = {"A": np.array([0., 1., 1., 0., 0., .5, 1., 0.]),
              "B": np.arange(8, dtype=float), "C": np.ones(8)}
    # Cached upstream source is required; never download in a test.
    for relative in (".cache/fast_vus/fast_vus.py", ".cache/benchopt_vus/metrics.py"):
        if not (EXPERIMENTS.parent / relative).exists():
            pytest.skip("External reference source not cached")
    values = {name: serialize_result(name, fn(labels, scores, 30)) for name, fn in methods.items()}
    reference = values["sparse_pr"]
    for name, value in values.items():
        assert value["selected"] == reference["selected"], name
        if name in EXACT:
            assert value["pr"] == pytest.approx(reference["pr"], abs=1e-11), name
        else:
            assert value["total_unique_widths"] <= 93
            assert set(value["bounds"]) == set(scores)
            if name != "v02_race":
                assert value["adaptive_curve_evaluations"] + value["completion_curve_evaluations"] == value["total_curve_evaluations"]
    inputs[0]["n"] = len(labels)
    rows[0].update(inputs[0], values=values,
                   seconds={m: [1., 2., 3.] for m in methods},
                   median_seconds={m: 2. for m in methods})
    rng = random.Random(protocol["seed"])
    rows[0]["method_order"] = []
    for _ in range(3):
        order = list(methods)
        rng.shuffle(order)
        rows[0]["method_order"].append(order)
    assert audit().audit_records(rows, protocol, inputs)["cases"] == 1


def test_manifest_gate_rejects_matching_rehashed_rows_for_wrong_source_members(monkeypatch):
    module = audit()
    _, protocol, _ = fixture()
    models = protocol["models"]
    metadata = {f"s{i:03}": {"n": 4, "family": "synthetic", "label_sha256": "0" * 64}
                for i in range(350)}
    score_hashes = {(s, m): "1" * 64 for s in metadata for m in models}
    development = list(metadata)[:42]
    monkeypatch.setattr(module, "released_metadata", lambda root: (
        metadata, models, score_hashes, development, {}, {"records_sha256": "2" * 64}))
    protocol["split"] = "holdout"
    inputs = [{"series": s, "family": "synthetic", "n": 4, "max_buffer": w,
               "label_sha256": "0" * 64, "score_sha256": {m: "1" * 64 for m in models}}
              for w in (30, 100, 300) for s in list(metadata)[42:]]
    assert module.validate_inputs_manifest(inputs, protocol, Path("/fixture"), verify_members=False)["series"] == 308
    # Record and input-file hashes could agree with this false identity; the
    # immutable released source hash must still independently reject it.
    inputs[0]["score_sha256"]["A"] = "9" * 64
    with pytest.raises(ValueError, match="immutable split"):
        module.validate_inputs_manifest(inputs, protocol, Path("/fixture"), verify_members=False)


def test_primary_decisions_include_new_stronger_radix_control_and_nearest_dense():
    rows, protocol, inputs = fixture()
    row = rows[0]
    for method, duration in {"fast_race": .3, "radix_pr": .2,
                             "fast_race_radix": .1, "dense_nearest_both": .15}.items():
        row["seconds"][method] = [duration, duration, duration]
        row["median_seconds"][method] = duration
    result = audit().audit_records(rows, protocol, inputs)
    # Old racing clears both original PR controls, but loses to radix exact.
    assert result["primary_decision"]["passes"] is False
    # Radix exact clears sparse/direct, but loses to the nearest dense control.
    assert result["radix_primary_decision"]["passes"] is False
    assert result["radix_racing_decision"]["passes"] is True
    driver = importlib.import_module("benchmark_pr_engine")
    audit().compare(driver.summarize(rows, protocol), result)


def test_previous_result_cleanup_cannot_be_charged_to_next_method(monkeypatch):
    driver = importlib.import_module("benchmark_pr_engine")
    events, ticks = [], iter([0., 1., 2., 3.])

    class Result:
        def __del__(self):
            events.append("cleanup")

    def metric(*args):
        events.append("metric")
        return Result()

    def clock():
        events.append("clock")
        return next(ticks)

    def serialize(*args):
        events.append("serialize")
        return {"selected": ["A"]}

    monkeypatch.setattr(driver.time, "perf_counter", clock)
    monkeypatch.setattr(driver, "serialize_result", serialize)
    first, first_duration = driver.timed_call("fake", metric, None, None, 30)
    second, second_duration = driver.timed_call("fake", metric, None, None, 30)
    assert first == second == {"selected": ["A"]}
    assert first_duration == second_duration == 1.
    assert events == ["clock", "metric", "clock", "serialize", "cleanup"] * 2


@pytest.mark.parametrize("matched_control", ["dense_pr_direct_radix", "dense_pr_nearest_radix"])
def test_radix_success_requires_beating_each_matched_radix_pr_dense_control(matched_control):
    rows, protocol, inputs = fixture()
    for method, duration in {"radix_pr": .2, "fast_race_radix": .1, matched_control: .05}.items():
        rows[0]["seconds"][method] = [duration] * 3
        rows[0]["median_seconds"][method] = duration
    result = audit().audit_records(rows, protocol, inputs)
    assert result["radix_primary_decision"]["passes"] is False
    assert result["radix_racing_decision"]["passes"] is False
    driver = importlib.import_module("benchmark_pr_engine")
    audit().compare(driver.summarize(rows, protocol), result)


def test_v3_rejects_old_series_first_schedule_even_with_unchanged_case_set():
    _, protocol, inputs = fixture()
    inputs = [{**inputs[0], "series": series, "max_buffer": width}
              for series in ("a", "b") for width in (30, 100)]
    protocol["cases"] = len(inputs)
    with pytest.raises(ValueError, match="input task manifest"):
        audit().audit_records([], protocol, inputs)


def test_historical_v2_receipt_uses_preserved_auditor_not_current_v3_contract():
    rows, protocol, inputs = fixture()
    historical_path = EXPERIMENTS.parent / "artifacts/pr-engine/source-v2/experiments/audit_pr_engine.py"
    assert historical_path.exists(), "The exact v2 historical auditor must remain available"
    spec = importlib.util.spec_from_file_location("historical_pr_engine_v2_audit", historical_path)
    historical = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(historical)
    old_methods = [m for m in METHODS if m not in ("dense_pr_direct_radix", "dense_pr_nearest_radix")]
    protocol.update(version=2, method_ids=old_methods)
    del protocol["task_order"]
    for field in ("values", "seconds", "median_seconds"):
        rows[0][field] = {m: value for m, value in rows[0][field].items() if m in old_methods}
    rng = random.Random(protocol["seed"])
    rows[0]["method_order"] = []
    for _ in range(3):
        order = old_methods.copy()
        rng.shuffle(order)
        rows[0]["method_order"].append(order)
    assert historical.audit_records(rows, protocol, inputs)["cases"] == 1
    with pytest.raises(ValueError, match="source-v2 auditor"):
        audit().audit_records(rows, protocol, inputs)
