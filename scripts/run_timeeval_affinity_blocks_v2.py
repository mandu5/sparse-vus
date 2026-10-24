"""Prospective v2: five sessions of one new fixed score realization.

Only orchestration/statistics are new. The pinned native workflow, adapters,
copy boundary, scalar checks, and numerical kernels are imported unchanged.
``freeze`` consumes source/input metadata only. ``run`` starts measurements
and must be invoked explicitly with the frozen protocol digest.
The failed v1 remains immutable. Prior score equality is diagnostic in v2;
same recordings/raw inputs remain mandatory. No timing outcome selected this revision.
"""
from __future__ import annotations

import argparse
import collections
from datetime import datetime, timezone
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
REL = Path('artifacts/pvldb-research-20261024/strengthening')
METHODS = ('raster', 'interval', 'bucket')
CONTRACTS = ('native_default50', 'all_observed')
THREADS = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
           'NUMBA_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')
NEW_SOURCES = ('scripts/run_timeeval_affinity_blocks_v2.py',
               'experiments/reproduce_affinity_blocks_v2.py',
               'experiments/reproduce_strengthening.py',
               'scripts/prepare_strengthening_workload.py',
               'experiments/audit_strengthening_inputs.py',
               'requirements-strengthening.txt',
               '.github/workflows/affinity-blocks-v2-reproduce.yml',
               'tests/test_timeeval_affinity_blocks_v2.py',
               'tests/test_timeeval_affinity_realization.py',
               'scripts/run_timeeval_affinity_blocks.py',
               'docs/superpowers/specs/2026-10-24-affinity-realization-v2.md')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def verify_files(bindings):
    for name, expected in bindings.items():
        if digest(name) != expected:
            raise ValueError('frozen file binding mismatch: ' + name)


def design():
    rng = random.Random(2026102405)
    blocks = []
    for block in range(5):
        permutations = {}
        for contract in CONTRACTS:
            permutations[contract] = list(itertools.permutations(METHODS))
            rng.shuffle(permutations[contract])
        trials = []
        for repeat in range(6):
            contracts = list(CONTRACTS)
            rng.shuffle(contracts)
            for contract in contracts:
                for position, method in enumerate(permutations[contract][repeat]):
                    trials.append({'trial': len(trials), 'contract': contract,
                                   'round': repeat, 'position': position,
                                   'method': method, 'batch': 'combined', 'row_count': 52})
        blocks.append({'block': block, 'trials': trials,
                       'warmup': [{'contract': c, 'method': m}
                                  for c in CONTRACTS for m in METHODS]})
    return {
        'schema': 'timeeval-affinity-five-blocks-v2-new-realization',
        'failed_predecessor': {'source_commit': 'ee3031aafb5cc30c7928d36e965d2156cf3ac2ca',
            'workflow_run': 40090142426, 'status': 'FAILED_PREPARATION', 'measured_blocks': 0},
        'score_realization': 'exactly one whole generation attempt for the fixed 52 profiles; any missing or failed fit aborts preparation, with no retry-until-complete, score/cardinality/outcome-based selection, exclusion or regeneration; prior score and query differences retained as diagnostics; fresh exact score bytes and realized query plans frozen before any metric and held fixed across all five blocks',
        'interpretation': 'same-recordings new-score-realization process variability, not a prior-profile replay or a causal explanation of prior Linux timing differences',
        'seed': 2026102405, 'blocks': blocks, 'planned_trials': 180,
        'primary_pairs': [['raster', 'bucket'], ['interval', 'bucket']],
        'affinity_policy': 'lowest logical CPU ID in the supervisor permitted affinity set; same single permitted logical CPU for every child, pinned before numerical imports; check every live thread before measurement and at block completion; shared-runner background load remains uncontrolled',
        'warmup': 'unchanged tiny native JIT warmup, then exactly one untimed full combined workflow per method/contract in the listed order, in every fresh child',
        'timing_boundary': 'unchanged execute(timed=True): native constructor, CSV reads, all three metrics and results CSV write/close; fixed 600s call deadline',
        'failure_policy': 'retain every trial and outlier; no repeats, replacements, trimming or censor-based skips; attempt all five blocks even after a block error or malformed child trace; complete child exit and hash-bound completion receipt required for block eligibility; any INVALID_OUTPUT invalidates its whole block for every comparison; TIMEOUT alone suppresses only intervals for incomplete comparison pairs',
        'output_parity': 'all pairs of completed 52-row, three-scalar results within each contract and block, including the six fixed full warmups, at absolute tolerance 1e-10; independently reread saved CSVs and check the same contract across all five blocks, including warmups; cross-block disagreement prevents five-block inference',
        'resource_limit': 'one explicitly authorized tagged workflow execution, fixed 90-minute overall job cap; an infrastructure interruption retains available partial evidence and is never a complete five-block result',
        'unit': 'five newly started Python processes on ONE Linux runner and ONE frozen 52-profile input; not five hosts or independent workload populations',
        'statistics': 'six matched log ratios averaged within each block; five block means equally averaged; enumerate all 5^5 empirical block-bootstrap sequences; descriptive 95% tails Bonferroni-adjusted over four contract/control contrasts; no finite-sample coverage or host-population claim',
        'public_reference_evaluated': False,
    }


def choose_core(allowed):
    if not allowed:
        raise ValueError('no permitted Linux logical CPU')
    return min(allowed)


def profile_identity(current, references):
    def index(value):
        if (value.get('status') != 'ALL_SELECTED_PROFILES_GENERATED'
                or value.get('metric_evaluation_performed') is not False
                or (value.get('selected_cases'), value.get('selected_profiles'),
                    value.get('successful_profiles')) != (26, 52, 52)):
            raise ValueError('complete 26-case / 52-profile generation required')
        indexed = {(p['case_id'], p['model']): p for p in value['profiles']}
        if len(indexed) != len(value['profiles']) or len(indexed) != 52:
            raise ValueError('52-profile identity coverage missing or duplicated')
        if any(p['status'] != 'Status.OK' for p in indexed.values()):
            raise ValueError('unsuccessful profile')
        return indexed
    actual = index(current)
    mismatches = []
    for number, reference in enumerate(references):
        expected = index(reference)
        if actual.keys() != expected.keys():
            raise ValueError('reference profile identity coverage differs')
        for identity, profile in actual.items():
            for field in ('score_array_sha256', 'native_score_sha256'):
                if profile[field] != expected[identity][field]:
                    mismatches.append({'reference': number, 'identity': list(identity),
                                       'field': field, 'actual': profile[field],
                                       'expected': expected[identity][field]})
    return {'matches': not mismatches, 'profiles': 52, 'references': len(references),
            'mismatches': mismatches, 'scope': 'array and native score CSV hashes; native input verifier is additionally mandatory'}


def cpu_receipt(chosen=None):
    if sys.platform != 'linux' or not hasattr(os, 'sched_getaffinity'):
        raise ValueError('this study requires Linux sched_getaffinity')
    allowed = sorted(os.sched_getaffinity(0))
    information = Path('/proc/cpuinfo').read_text()
    models = sorted({line.split(':', 1)[1].strip() for line in information.splitlines()
                     if line.startswith('model name')})
    return {'pid': os.getpid(), 'ppid': os.getppid(),
            'process_start_ticks': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
            'cpu_models': models, 'permitted_affinity': allowed, 'chosen_affinity': chosen,
            'hostname': platform.node(), 'platform': platform.platform(),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'cpuinfo_sha256': hashlib.sha256(information.encode()).hexdigest()}


def reference_diagnostics(current, references, payload, consumer_references):
    """Separate mandatory raw/layout identity from fully retained score diagnostics."""
    identity = profile_identity(current, references)
    if len(references) != 2 or len(consumer_references) != 2:
        raise ValueError('both frozen prior Linux references required')
    hard, score_files, query_changes = [], [], []

    def difference(ref, field, actual, expected):
        if actual != expected:
            hard.append({'reference': ref, 'field': field, 'actual': actual, 'expected': expected})

    for number, (generation, previous) in enumerate(zip(references, consumer_references)):
        for key in ('selection_sha256', 'models'):
            difference(number, key, current[key], generation[key])
        case_fields = ('id', 'family', 'n', 'model_order', 'model_status', 'labels_sha256')
        difference(number, 'ordered_case_raw_label_identity',
                   [{k: p[k] for k in case_fields} for p in current['cases']],
                   [{k: p[k] for k in case_fields} for p in generation['cases']])
        profile_fields = ('case_id', 'model', 'dtype', 'shape', 'status')
        difference(number, 'ordered_profile_identity',
                   [{k: p[k] for k in profile_fields} for p in current['profiles']],
                   [{k: p[k] for k in profile_fields} for p in generation['profiles']])
        for key in ('datasets_sha256', 'results_sha256', 'immutable_template'):
            difference(number, 'native_layout.' + key,
                       current['native_layout'][key], generation['native_layout'][key])
        difference(number, 'row_ids', payload['row_ids'], previous['row_ids'])
        actual, expected = payload['input_sha256'], previous['input_sha256']
        difference(number, 'native_file_keys', sorted(actual), sorted(expected))
        for name in sorted(set(actual) | set(expected)):
            a, e = actual.get(name), expected.get(name)
            if a != e:
                if name in actual and name in expected and name.endswith('/anomaly_scores.ts'):
                    score_files.append({'reference': number, 'path': name, 'actual': a, 'expected': e})
                else:
                    difference(number, 'native_input.' + name, a, e)
        # Keep complete old/new plans, including exact threshold hashes and query counts.
        if payload['query_plan'] != previous['query_plan']:
            query_changes.append({'reference': number, 'actual': payload['query_plan'],
                                  'expected': previous['query_plan']})
    identity.update(prior_score_identity_required=False, hard_inputs_match=not hard,
                    hard_input_differences=hard, native_score_file_differences=score_files,
                    query_plan_differences=query_changes,
                    scope='Prior scores/queries are diagnostics; raw/native data, labels, selection, model and row layout must match. The new exact score/query realization is frozen before every metric block.')
    return identity


def load_control():
    # This import sets the same numerical thread variables as the frozen study.
    spec = importlib.util.spec_from_file_location(
        '_affinity_unchanged_interval_control', ROOT / 'scripts/run_timeeval_interval_control.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def freeze(args):
    host = cpu_receipt()
    core = choose_core(host['permitted_affinity'])
    control = load_control(); base = control.BASE
    payload = base.manifest(args.workload, args.source, args.generation, args.input_audit)
    reference_files = [ROOT / REL / 'linux-original-replay/workload-generation.json',
                       ROOT / REL / 'linux-interval-replay/workload-generation.json']
    original_path = ROOT / REL / 'linux-original-replay/timeeval-global.json'
    control_path = ROOT / REL / 'linux-interval-replay/timeeval-control-global.json'
    original = read_json(original_path)['timeeval_consumer']
    previous = read_json(control_path)['timeeval_consumer']
    identity = reference_diagnostics(read_json(args.generation),
        [read_json(p) for p in reference_files], payload, [original, previous])
    write_new(args.protocol.with_suffix('.input-identity.json'), identity)
    if not identity['hard_inputs_match']:
        raise ValueError('same-recording/raw/label/layout check failed; no measured block may start')
    for key in ('source_revision', 'source_sha256', 'project_sha256', 'prts_sha256', 'dependencies',
                'python_version', 'row_ids', 'records', 'design'):
        if payload[key] != previous[key]:
            raise ValueError('pinned native/compiler contract differs: ' + key)
    if payload['records'] != 52:
        raise ValueError('combined primary requires exactly 52 profiles')
    bindings = {str((ROOT / name).resolve()): digest(ROOT / name) for name in NEW_SOURCES}
    bindings.update({str(p.resolve()): digest(p) for p in reference_files + [original_path, control_path]})
    from threadpoolctl import threadpool_info
    write_new(args.protocol, {'status': 'FROZEN_BEFORE_ANY_AFFINITY_BLOCK_MEASUREMENT',
              'utc': datetime.now(timezone.utc).isoformat(), 'study': design(),
              'timeeval_consumer': payload, 'supervisor_preflight': host,
              'chosen_core': core, 'file_bindings': bindings,
              'identity_receipt': {'path': str(args.protocol.with_suffix('.input-identity.json').resolve()),
                                   'sha256': digest(args.protocol.with_suffix('.input-identity.json'))},
              'preflight_threadpools': threadpool_info(),
              'thread_environment': {k: os.environ.get(k) for k in THREADS}})


def check_protocol(path, expected):
    if digest(path) != expected:
        raise ValueError('frozen protocol digest mismatch')
    protocol = read_json(path)
    if protocol['status'] != 'FROZEN_BEFORE_ANY_AFFINITY_BLOCK_MEASUREMENT' or protocol['study'] != design():
        raise ValueError('frozen study design differs')
    verify_files(protocol['file_bindings'])
    verify_files({protocol['identity_receipt']['path']: protocol['identity_receipt']['sha256']})
    return protocol


def summarize(records, plan, eligibility=None):
    expected = {(b['block'], t['trial']): t for b in plan['blocks'] for t in b['trials']}
    keyed = {}
    for row in records:
        if not isinstance(row, dict) or any(type(row.get(k)) is not int for k in ('block', 'trial')):
            raise ValueError('planned trial identity is malformed')
        if row.get('status') not in ('COMPLETE', 'TIMEOUT', 'ERROR', 'INVALID_OUTPUT'):
            raise ValueError('planned trial status is malformed')
        key = row['block'], row['trial']
        if key in keyed:
            raise ValueError('duplicate planned trial identity')
        if key not in expected or any(row.get(k) != v for k, v in expected[key].items()):
            raise ValueError('planned trial identity differs')
        keyed[key] = row
    if keyed.keys() != expected.keys():
        raise ValueError('planned trial coverage incomplete')
    if eligibility is not None and set(eligibility) != set(range(5)):
        raise ValueError('five block eligibility receipts required')
    output = {'status_counts': dict(collections.Counter(r['status'] for r in records)),
              'resampling_unit': plan['unit'], 'uncertainty_scope': plan['statistics'],
              'block_eligibility': eligibility,
              'block_receipts_validated': eligibility is not None,
              'comparisons': {}}
    for contract in CONTRACTS:
        for a, b in plan['primary_pairs']:
            means, counts, block_pairs = [], [], []
            for block in range(5):
                selected = {(r['round'], r['method']): r for r in records
                            if r['block'] == block and r['contract'] == contract}
                ratios = []
                for repeat in range(6):
                    x, y = selected[(repeat, a)], selected[(repeat, b)]
                    if x['status'] == y['status'] == 'COMPLETE':
                        if not all(type(r.get('seconds')) in (int, float)
                                   and math.isfinite(r['seconds']) and r['seconds'] > 0 for r in (x, y)):
                            raise ValueError('invalid positive workflow duration')
                        ratios.append(x['seconds'] / y['seconds'])
                counts.append(len(ratios)); block_pairs.append(ratios)
                valid = eligibility is None or eligibility[block]['eligible']
                means.append(statistics.mean(map(math.log, ratios)) if len(ratios) == 6 and valid else None)
            value = {'block_ratios': [math.exp(x) if x is not None else None for x in means],
                     'paired_order_ratios_by_block': block_pairs,
                     'within_block_pairs': counts, 'complete_blocks': sum(x is not None for x in means),
                     'descriptive_block_bootstrap95_bonferroni4': None,
                     'resampling_units': 5, 'exact_bootstrap_sequences': 3125}
            if all(x is not None for x in means):
                samples = sorted(statistics.mean(means[i] for i in indices)
                                 for indices in itertools.product(range(5), repeat=5))
                def quantile(p):
                    index = (len(samples) - 1) * p
                    lo = int(index); hi = min(lo + 1, len(samples) - 1)
                    return math.exp(samples[lo] + (index - lo) * (samples[hi] - samples[lo]))
                value.update(geometric_ratio=math.exp(statistics.mean(means)),
                             block_range=[math.exp(min(means)), math.exp(max(means))],
                             descriptive_block_bootstrap95_bonferroni4=[quantile(.025 / 4), quantile(1 - .025 / 4)])
            else:
                value['interval_unavailable_reason'] = 'all five complete blocks required; no omission or imputation'
            output['comparisons'][contract + '/' + a + '_over_' + b] = value
    return output


def pairwise_error(actual, earlier, compare):
    """Use the frozen scalar checker for every earlier result, not one anchor."""
    return max((compare(actual, values) for values in earlier), default=0.0)


def validate_threads(affinities, core, pools):
    if not affinities or any(cpus != [core] for cpus in affinities.values()):
        raise ValueError('a live thread escaped the frozen singleton CPU affinity')
    if any(pool.get('num_threads') != 1 for pool in pools):
        raise ValueError('a reported numerical pool exceeds the one-thread contract')


def thread_contract(core, pools):
    affinities, vanished = {}, []
    for path in sorted(Path('/proc/self/task').iterdir()):
        tid = int(path.name)
        try:
            affinities[tid] = sorted(os.sched_getaffinity(tid))
        except ProcessLookupError:
            vanished.append(tid)
    validate_threads(affinities, core, pools)
    return {'affinities_by_tid': affinities, 'vanished_during_inspection': vanished,
            'numerical_pools': pools, 'utc': datetime.now(timezone.utc).isoformat()}


def read_trial_trace(path):
    """A crash may leave a partial final line; retain its bytes and keep going."""
    rows, issues = [], []
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        return rows, [{'line': None, 'error': str(exc)}]
    for number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError('trace row is not an object')
            rows.append(row)
        except (ValueError, UnicodeDecodeError) as exc:
            issues.append({'line': number, 'error': str(exc)})
    return rows, issues


def block_eligibility(directory, process, protocol_sha, core):
    reasons = []
    if process['returncode'] != 0:
        reasons.append('child did not exit successfully')
    if process.get('trace_parse_issues'):
        reasons.append('child trace is malformed or missing; raw bytes retained')
    try:
        path = directory / 'block-complete.json'
        if digest(path) != process['block_complete_sha256']:
            raise ValueError('completion receipt hash differs')
        completion = read_json(path)
        if (completion['block'] != process['block']
                or completion['protocol_sha256'] != protocol_sha
                or completion['recorded_trials'] != 36
                or completion['status'] not in ('COMPLETE', 'COMPLETE_WITH_FAILED_TRIALS')
                or completion.get('input_bindings_verified_after_block') is not True):
            raise ValueError('completion identity or final verification differs')
        for name in ('child-initial.json', 'block-start.json', 'trials.jsonl', 'metrics.jsonl'):
            if digest(directory / name) != completion['evidence_sha256'][name]:
                raise ValueError('completed block evidence hash differs: ' + name)
        trials, parse_issues = read_trial_trace(directory / 'trials.jsonl')
        if parse_issues:
            raise ValueError('hash-bound child trace is malformed')
        # Invalid scalars compromise the session, including its other methods
        # and contract. A timeout alone remains local to an incomplete pair.
        if any(trial.get('status') == 'INVALID_OUTPUT' for trial in trials):
            reasons.append('INVALID_OUTPUT invalidates the whole session block')
        threads = completion['thread_contract']
        validate_threads(threads['affinities_by_tid'], core, threads['numerical_pools'])
        if completion['native_cpu']['permitted_affinity'] != [core]:
            raise ValueError('final CPU affinity differs')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        reasons.append(str(exc))
    return {'eligible': not reasons, 'reasons': reasons,
            'block_complete_sha256': process.get('block_complete_sha256')}


def compare_block_outputs(outputs, compare):
    previous = collections.defaultdict(list)
    failures, pairs, maximum = [], 0, 0.0
    for current in outputs:
        for earlier in previous[current['contract']]:
            if earlier['block'] == current['block']:
                continue
            pairs += 1
            try:
                maximum = max(maximum, compare(current['values'], earlier['values']))
            except ValueError as exc:
                failures.append({'contract': current['contract'],
                                 'left_block': earlier['block'], 'right_block': current['block'],
                                 'left_path': earlier['path'], 'right_path': current['path'],
                                 'error': str(exc)})
        previous[current['contract']].append(current)
    return {'status': 'FAILED' if failures else 'PASS', 'failures': failures,
            'compared_cross_block_pairs': pairs, 'maximum_passing_absolute_error': maximum,
            'tolerance': 1e-10, 'scalar_columns': ['ROC_AUC', 'PR_AUC', 'RANGE_PR_AUC']}


def audit_saved_outputs(out, protocol):
    """Reread hash-bound CSVs after all sessions; no metric execution here."""
    base = load_control().BASE
    import pandas as pd
    rows = pd.DataFrame(protocol['timeeval_consumer']['row_ids'], columns=base.IDS)
    outputs, issues, files = [], [], []
    for block in protocol['study']['blocks']:
        directory = out / 'blocks' / f'{block["block"]:02d}'
        try:
            warmups = read_json(directory / 'block-start.json')['warmup_results']
            metrics, parse_issues = read_trial_trace(directory / 'metrics.jsonl')
            if parse_issues:
                raise ValueError('malformed saved metrics trace: ' + str(parse_issues))
            for item in warmups + metrics:
                path = directory / item['directory'] / 'results/results.csv'
                actual = digest(path)
                if actual != item['results_sha256']:
                    raise ValueError('saved results CSV binding differs: ' + str(path))
                _, values = base.audit_output(path, rows)
                identity = {'block': block['block'], 'contract': item['contract'],
                            'path': str(path.relative_to(out)), 'sha256': actual}
                files.append(identity)
                outputs.append({**identity, 'values': values})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            issues.append({'block': block['block'], 'error': str(exc)})
    result = compare_block_outputs(outputs, base.compare_values)
    result.update(saved_csvs=files, saved_csv_errors=issues,
                  saved_completed_outputs=len(files), full_planned_outputs_including_warmups=210,
                  complete_output_coverage=len(files) == 210,
                  metric_execution_performed=False)
    if issues:
        result['status'] = 'FAILED'
    return result


def run_block(args):
    protocol = check_protocol(args.protocol, args.protocol_sha256)
    before = cpu_receipt(protocol['chosen_core'])
    write_new(args.out / 'child-initial.json', {
        'block': args.block, 'utc': datetime.now(timezone.utc).isoformat(),
        'protocol_sha256': args.protocol_sha256, 'native_cpu_before_affinity': before,
        'thread_environment_before_import': {k: os.environ.get(k) for k in THREADS}})
    frozen = protocol['supervisor_preflight']
    for key in ('permitted_affinity', 'cpu_models', 'hostname', 'boot_id'):
        if before[key] != frozen[key]:
            raise ValueError('child does not match frozen runner: ' + key)
    core = protocol['chosen_core']
    os.sched_setaffinity(0, {core})  # before importing numpy/Numba/native TimeEval
    for name in THREADS:
        os.environ[name] = '1'
    control = load_control(); base = control.BASE
    workload, source = base.verify_bindings(protocol['timeeval_consumer'])
    native = base.load_native(source)
    rows = base.workload_rows(workload)
    base.configure_logging(args.out)
    from threadpoolctl import threadpool_limits, threadpool_info
    import numba
    block = protocol['study']['blocks'][args.block]
    outputs, records, warmup_receipts = {c: [] for c in CONTRACTS}, [], []
    errors = {c: [] for c in CONTRACTS}
    with threadpool_limits(limits=1):
        if numba.get_num_threads() != 1:
            raise ValueError('numerical thread contract differs')
        base.warmup(native)
        for i, item in enumerate(block['warmup']):
            directory = args.out / 'warmup' / f'{i:02d}-{item["contract"]}-{item["method"]}'
            target = base.copy_trial(workload, directory, rows, combined=True)
            base.execute(native, workload, target, directory,
                         control.metric_suite(native, item['method'], item['contract']), timed=False)
            _, values = base.audit_output(target / 'results.csv', rows)
            error = pairwise_error(values, outputs[item['contract']], base.compare_values)
            outputs[item['contract']].append(values)
            errors[item['contract']].append(error)
            warmup_receipts.append({**item, 'directory': str(directory.relative_to(args.out)),
                                    'results_sha256': digest(target / 'results.csv'),
                                    'max_pairwise_scalar_error': error})
        base.verify_bindings(protocol['timeeval_consumer'])
        start_threads = thread_contract(core, threadpool_info())
        write_new(args.out / 'block-start.json', {
            'block': args.block, 'utc': datetime.now(timezone.utc).isoformat(),
            'protocol_sha256': args.protocol_sha256, 'before_affinity': before,
            'native_cpu': cpu_receipt(core), 'dependencies': base.versions(),
            'threadpools': threadpool_info(), 'thread_environment': {k: os.environ.get(k) for k in THREADS},
            'thread_contract': start_threads,
            'fixed_warmup_completed': True, 'warmup_workflows': 6,
            'warmup_results': warmup_receipts,
            'input_bindings_verified_before_timing': True})
        with (args.out / 'trials.jsonl').open('x') as trace, (args.out / 'metrics.jsonl').open('x') as metric_trace:
            for item in block['trials']:
                trial_threads = thread_contract(core, threadpool_info())
                directory = args.out / 'trials' / f'{item["trial"]:03d}-{item["contract"]}-{item["method"]}'
                identity = {**item, 'block': args.block, 'directory': str(directory.relative_to(args.out))}
                try:
                    target = base.copy_trial(workload, directory, rows, combined=True)
                    outcome = base.execute(native, workload, target, directory,
                                           control.metric_suite(native, item['method'], item['contract']), timed=True)
                    record = {**identity, **outcome, 'thread_contract_before_timing': trial_threads}
                    if outcome['status'] == 'COMPLETE':
                        try:
                            frame, values = base.audit_output(target / 'results.csv', rows)
                            error = pairwise_error(values, outputs[item['contract']], base.compare_values)
                            outputs[item['contract']].append(values)
                            errors[item['contract']].append(error)
                            record['max_pairwise_scalar_error'] = error
                            base.append(metric_trace, {**identity, 'max_pairwise_scalar_error': error,
                                        'public_reference_available': False,
                                        'results_sha256': digest(target / 'results.csv'),
                                        'rows': frame[list(base.IDS) + list(base.METRICS)].to_dict(orient='records')})
                        except Exception as exc:
                            record.update(status='INVALID_OUTPUT', error=str(exc),
                                          traceback=traceback.format_exc())
                except Exception as exc:
                    record = {**identity, 'status': 'ERROR', 'error': str(exc),
                              'traceback': traceback.format_exc()}
                records.append(record); base.append(trace, record)
        base.verify_bindings(protocol['timeeval_consumer'])
        final_threads = thread_contract(core, threadpool_info())
        write_new(args.out / 'block-complete.json', {
            'block': args.block, 'status': 'COMPLETE' if all(r['status'] == 'COMPLETE' for r in records) else 'COMPLETE_WITH_FAILED_TRIALS',
            'recorded_trials': len(records), 'protocol_sha256': args.protocol_sha256,
            'native_cpu': cpu_receipt(core), 'threadpools': threadpool_info(),
            'thread_contract': final_threads, 'input_bindings_verified_after_block': True,
            'pairwise_output_parity': {
                c: {'completed_outputs_including_warmup': len(outputs[c]),
                    'maximum_absolute_error': max(errors[c]), 'tolerance': 1e-10}
                for c in CONTRACTS},
            'trials_sha256': digest(args.out / 'trials.jsonl'),
            'metrics_sha256': digest(args.out / 'metrics.jsonl'),
            'evidence_sha256': {name: digest(args.out / name) for name in
                               ('child-initial.json', 'block-start.json', 'trials.jsonl', 'metrics.jsonl')}})


def run_sessions(args):
    protocol = check_protocol(args.protocol, args.protocol_sha256)
    host = cpu_receipt(protocol['chosen_core'])
    for key in ('permitted_affinity', 'cpu_models', 'hostname', 'boot_id'):
        if host[key] != protocol['supervisor_preflight'][key]:
            raise ValueError('supervisor runner changed after freeze: ' + key)
    args.out.mkdir(parents=True, exist_ok=False)
    write_new(args.out / 'bound-protocol.json', protocol)
    write_new(args.out / 'supervisor-start.json', {'utc': datetime.now(timezone.utc).isoformat(),
              'protocol_sha256': args.protocol_sha256, 'native_cpu': host,
              'scope': protocol['study']['unit']})
    receipts, records, eligibility = [], [], {}
    for block in protocol['study']['blocks']:
        target = args.out / 'blocks' / f'{block["block"]:02d}'
        target.mkdir(parents=True, exist_ok=False)
        command = [sys.executable, str(Path(__file__).resolve()), 'block',
                   '--protocol', str(args.protocol), '--protocol-sha256', args.protocol_sha256,
                   '--block', str(block['block']), '--out', str(target)]
        env = dict(os.environ); env.update({k: '1' for k in THREADS})
        env['PYTHONOPTIMIZE'] = '0'
        started = datetime.now(timezone.utc).isoformat()
        pid, code, launch_error = None, None, None
        try:
            with (target / 'process.stdout.log').open('x') as stdout, (target / 'process.stderr.log').open('x') as stderr:
                process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env)
                pid = process.pid
                code = process.wait()
        except OSError as exc:
            launch_error = str(exc)
        rows, parse_issues = read_trial_trace(target / 'trials.jsonl')
        completion = target / 'block-complete.json'
        receipt = {'block': block['block'], 'pid': pid, 'returncode': code,
                   'command': command, 'started_utc': started,
                   'launch_error': launch_error, 'trace_parse_issues': parse_issues,
                   'raw_trials_sha256': digest(target / 'trials.jsonl') if (target / 'trials.jsonl').exists() else None,
                   'block_complete_sha256': digest(completion) if completion.exists() else None,
                   'completed_utc': datetime.now(timezone.utc).isoformat()}
        receipts.append(receipt); write_new(target / 'process-receipt.json', receipt)
        eligibility[block['block']] = block_eligibility(
            target, receipt, args.protocol_sha256, protocol['chosen_core'])
        records.extend(rows)
    write_new(args.out / 'session-processes.json', receipts)
    try:
        parity = audit_saved_outputs(args.out, protocol)
    except Exception as exc:
        parity = {'status': 'FAILED', 'error': str(exc), 'traceback': traceback.format_exc(),
                  'metric_execution_performed': False}
    write_new(args.out / 'cross-block-output-parity.json', parity)
    if parity['status'] != 'PASS':
        for result in eligibility.values():
            result['eligible'] = False
            result['reasons'].append('cross-block saved-CSV parity verification failed')
    write_new(args.out / 'block-eligibility.json', eligibility)
    try:
        summary = summarize(records, protocol['study'], eligibility)
        write_new(args.out / 'summary.json', summary)
        complete = (all(r['eligible'] for r in eligibility.values())
                    and set(summary['status_counts']) == {'COMPLETE'}
                    and parity.get('complete_output_coverage') is True)
    except ValueError as exc:
        complete = False
        write_new(args.out / 'summary-unavailable.json', {'error': str(exc), 'observed_records': len(records),
                  'no_partial_block_interval': True})
    write_new(args.out / 'complete.json', {'status': 'COMPLETE' if complete else 'INCOMPLETE_OR_FAILED_TRIALS',
              'planned_blocks': 5, 'attempted_blocks': len(receipts), 'planned_trials': 180,
              'observed_trials': len(records), 'protocol_sha256': args.protocol_sha256,
              'native_cpu': cpu_receipt(protocol['chosen_core']),
              'process_receipts_sha256': digest(args.out / 'session-processes.json'),
              'block_eligibility_sha256': digest(args.out / 'block-eligibility.json'),
              'cross_block_output_parity_sha256': digest(args.out / 'cross-block-output-parity.json'),
              'summary_receipts_sha256': {p.name: digest(p) for p in args.out.glob('summary*.json')},
              'blocks': {str(b['block']): {p.name: digest(p) for p in
                         (args.out / 'blocks' / f'{b["block"]:02d}').glob('*.json*')}
                         for b in protocol['study']['blocks']}})
    if not complete:
        raise ValueError('five complete valid blocks not obtained; all attempts retained')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('freeze')
    for name in ('workload', 'source', 'generation', 'input-audit', 'protocol'):
        p.add_argument('--' + name, type=Path, required=True)
    for command in ('run', 'block'):
        p = sub.add_parser(command)
        p.add_argument('--protocol', type=Path, required=True)
        p.add_argument('--protocol-sha256', required=True)
        p.add_argument('--out', type=Path, required=True)
        if command == 'block':
            p.add_argument('--block', type=int, choices=range(5), required=True)
    args = parser.parse_args()
    for key, value in vars(args).items():
        if isinstance(value, Path):
            setattr(args, key, value.resolve())
    try:
        if args.command == 'freeze':
            freeze(args)
        elif args.command == 'block':
            run_block(args)
        else:
            run_sessions(args)
    except BaseException as exc:
        if getattr(args, 'out', None) and args.out.exists():
            write_new(args.out / 'failure.json', {'error': str(exc), 'traceback': traceback.format_exc(),
                      'utc': datetime.now(timezone.utc).isoformat()})
        raise


if __name__ == '__main__':
    main()
