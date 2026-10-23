"""Audit the public evidence bundle using only the Python standard library.

This checks frozen ledgers, hash chains, decisions and integer witnesses. It
does not access raw-input caches, import a metric implementation, or freshly
execute a metric. Write the receipt outside artifacts with --output PATH.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
MAIN = 'artifacts/msad-sampling-20261023'
PARTIAL = 'artifacts/msad-certificate-20261023'
FULL = 'artifacts/msad-full-certificate-20261023'
SAT = 'artifacts/msad-saturation-diagnostic-20261023'
COST = 'artifacts/msad-certificate-full-cost-20261023'
CORPUS = 'artifacts/msad-corpus-20261023'
OVERLAP = 'artifacts/msad-score-provenance-20261023/one-point-overlap-audit.json'
ANCHORS = {
    f'{MAIN}/protocol.json': 'c778699fe9393ba4f5a6bb9e54362bb9327bcdc1efb3aca4b2cad6deb3cdc2cb',
    f'{MAIN}/source_manifest.json': 'dae17c7e3e370c5d4d1206762ab201435f1c693d1ececf80f506972b72b0e96d',
    f'{MAIN}/records.jsonl': '283ccfafa5b712e2a7316b344b4c75ae8f528359bbb42725fd48fc3963224023',
    f'{CORPUS}/manifest.json': '5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59',
    f'{PARTIAL}/protocol.json': '4b73c88d7f129f5d5fdfeb7b36e1efb71d753bc8351c55ea5815c3bb84897e04',
    f'{PARTIAL}/records.jsonl': '4e557a2696ab92d35b2c433bdf98918de41afeb7e1a92172da62adfa52e185ab',
    f'{FULL}/protocol.json': 'fb1e1ba34bdcf6b4c21c098386fbd8e0efa46fe457c20a41d9c6905877d2ee66',
    f'{FULL}/records.jsonl': '604a96f3f5ef1c42326a8786ae349381d49f715fac347196cafc5dc307eb4a46',
    f'{SAT}/protocol.json': '5603f8b261af280dcb77acf39155a8329f8cd3262e1a81adae4a0372c860935b',
    f'{SAT}/records.jsonl': '98709c790ff7c767dc816d35fa47921ca577a102fc552b3ece68d27190b1e039',
    f'{SAT}/integer-replay-witnesses.jsonl': 'cdd636a7ed855dee9effbdd2d0739baae344893e70be272c8afdf7a989db21ca',
    OVERLAP: '281c9af140cc9378ad993d35c637359ccc54eed637c190a36767be878c02b900',
    f'{COST}/protocol.json': '651cb0cc4d5bde61195f8ef0da64a76694886dc06412b6314e3be22c27467c7a',
    f'{COST}/records.jsonl': 'f837144c4d4d08fd1dc00b647f563145defc99e39d64b02a61636155542b1c31',
}
EXTERNAL_SOURCE = '.cache/fast_vus/fast_vus.py'
EXTERNAL_DIGEST = '15b7afb94da0e1f1b1c408fe44b937d910935c19f8eb76f42ae6719f9cfcb52b'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            result.update(block)
    return result.hexdigest()


def unique_index(rows, key, expected=None, name='records'):
    index = {}
    for row in rows:
        item = key(row)
        require(item not in index, f'{name}: duplicate key {item}')
        index[item] = row
    if expected is not None:
        require(set(index) == set(expected),
                f'{name}: missing or unexpected keys ({len(set(expected)-set(index))} missing, '
                f'{len(set(index)-set(expected))} unexpected)')
    return index


def same(actual, expected, name):
    if isinstance(expected, dict):
        require(set(actual) == set(expected), f'{name}: dictionary fields differ')
        for key in expected:
            same(actual[key], expected[key], f'{name}.{key}')
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), f'{name}: list differs')
        for i, (a, b) in enumerate(zip(actual, expected)):
            same(a, b, f'{name}[{i}]')
    elif isinstance(expected, float):
        require(isinstance(actual, (int, float)) and math.isfinite(actual)
                and math.isclose(actual, expected, rel_tol=5e-13, abs_tol=5e-14), f'{name}: numerical replay differs')
    else:
        require(actual == expected, f'{name}: value differs ({actual!r} != {expected!r})')


class Bundle:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.hashes = {}
        self.external = {}

    def path(self, relative):
        path = (self.root/relative).resolve()
        require(path.is_relative_to(self.root), f'Path escapes bundle: {relative}')
        require('.cache' not in Path(relative).parts, f'Raw cache access prohibited: {relative}')
        return path

    def hash(self, relative, expected=None):
        actual = sha256(self.path(relative))
        if expected is not None:
            require(actual == expected, f'Hash mismatch: {relative}')
        self.hashes[relative] = actual
        return actual

    def sources(self, mapping):
        for relative, expected in mapping.items():
            if relative == EXTERNAL_SOURCE:
                require(expected == EXTERNAL_DIGEST, 'External upstream source commitment changed')
                self.external[relative] = expected
            else:
                self.hash(relative, expected)

    def json(self, relative):
        self.hash(relative)
        return json.loads(self.path(relative).read_text())

    def jsonl(self, relative):
        self.hash(relative)
        with self.path(relative).open() as stream:
            return [json.loads(line) for line in stream]


def numerical_decision(exact, sampled, tolerance=1e-10):
    require(set(exact) == set(sampled) and bool(exact), 'Different model pools')
    require(all(math.isfinite(v) for v in list(exact.values())+list(sampled.values())), 'Nonfinite metric')
    models = sorted(exact)
    def winners(values): return [m for m in models if values[m] >= max(values.values())-tolerance]
    def top(values):
        cutoff = sorted(values.values(), reverse=True)[min(3, len(models))-1]
        return [m for m in models if values[m] >= cutoff-tolerance]
    ew, sw = winners(exact), winners(sampled)
    concordant = discordant = tx = ty = large = 0
    for i, a in enumerate(models):
        for b in models[i+1:]:
            de, ds = exact[a]-exact[b], sampled[a]-sampled[b]
            se = 0 if abs(de) <= tolerance else (1 if de > 0 else -1)
            ss = 0 if abs(ds) <= tolerance else (1 if ds > 0 else -1)
            if se and ss:
                concordant += se == ss
                discordant += se != ss
                large += se != ss and abs(de) >= .01 and abs(ds) >= .01
            elif not se and ss: tx += 1
            elif se and not ss: ty += 1
    denominator = math.sqrt((concordant+discordant+tx)*(concordant+discordant+ty))
    errors = [sampled[m]-exact[m] for m in models]
    et, st = top(exact), top(sampled)
    return dict(exact_winners=ew, sampled_winners=sw, winner_set_changed=ew != sw,
        unique_winner_changed=len(ew) == len(sw) == 1 and ew != sw,
        best_regret=max(0., max(exact.values())-max(exact[m] for m in sw)),
        worst_regret=max(0., max(exact.values())-min(exact[m] for m in sw)),
        lexical_regret=max(0., max(exact.values())-exact[sw[0]]), exact_top3=et,
        sampled_top3=st, top3_changed=et != st, pair_reversals=discordant,
        large_pair_reversals=large, pair_count=len(models)*(len(models)-1)//2,
        kendall_tau_b=(concordant-discordant)/denominator if denominator else None,
        mean_absolute_error=statistics.mean(abs(x) for x in errors),
        maximum_absolute_error=max(abs(x) for x in errors),
        minimum_signed_error=min(errors), maximum_signed_error=max(errors))


def numerical_summary(cases):
    return {'series': len(cases),
        'practical_regret_fraction': statistics.mean(c['best_regret'] >= .01 for c in cases),
        'worst_case_practical_regret_fraction': statistics.mean(c['worst_regret'] >= .01 for c in cases),
        'winner_set_change_fraction': statistics.mean(c['winner_set_changed'] for c in cases),
        'unique_winner_change_fraction': statistics.mean(c['unique_winner_changed'] for c in cases),
        'top3_change_fraction': statistics.mean(c['top3_changed'] for c in cases),
        'mean_best_regret': statistics.mean(c['best_regret'] for c in cases),
        'maximum_best_regret': max(c['best_regret'] for c in cases),
        'mean_absolute_error': statistics.mean(c['mean_absolute_error'] for c in cases),
        'maximum_absolute_error': max(c['maximum_absolute_error'] for c in cases),
        'pair_reversals': sum(c['pair_reversals'] for c in cases),
        'large_pair_reversals': sum(c['large_pair_reversals'] for c in cases)}


def input_identity(record, row, label_key='label_sha256', score_key='score_sha256'):
    require(record['series'] == row['series'] and record['family'] == row['family'], 'Input identity differs')
    require(record['npz_sha256'] == row['npz_sha256'], 'NPZ commitment differs')
    if label_key in record:
        require(record[label_key] == row['array_sha256']['labels'], 'Label commitment differs')
        require(record[score_key] == row['array_sha256'][record['model']], 'Score commitment differs')


def audit_main(bundle, manifest):
    protocol = bundle.json(f'{MAIN}/protocol.json')
    sources = bundle.json(f'{MAIN}/source_manifest.json')
    bundle.sources(sources['sha256'])
    bundle.hash(protocol['acquisition_protocol'], protocol['acquisition_protocol_sha256'])
    report = bundle.json(f'{MAIN}/report-{ANCHORS[f"{MAIN}/records.jsonl"][:16]}.json')
    for field, path in [('protocol_sha256', f'{MAIN}/protocol.json'),
                        ('source_manifest_sha256', f'{MAIN}/source_manifest.json'),
                        ('records_sha256', f'{MAIN}/records.jsonl')]:
        bundle.hash(path, report[field])
    rows, models = manifest['series'], protocol['models']
    require(len(rows) == 128 and len(models) == 12 and models == manifest['models'], 'Panel coverage differs')
    byseries = {r['series']: r for r in rows}
    require(len(byseries) == 128 and len({r['family'] for r in rows}) == 16, 'Series identities differ')
    require(sources['numerical_series'] == [r['series'] for r in rows], 'Frozen series order differs')
    subset = []
    for family in sorted({r['family'] for r in rows}):
        fr = [r for r in rows if r['family'] == family]
        fr.sort(key=lambda r: hashlib.sha256(('msad-vus-20261023-v1\0'+r['series']).encode()).hexdigest())
        subset.extend(r['series'] for r in fr[:2])
    require(subset == sources['validation_timing_series'] and len(subset) == 30, 'Fixed subset differs')
    records = bundle.jsonl(f'{MAIN}/records.jsonl')
    unique_index(records, lambda r: r['key'], name='main ledger')
    expected = set()
    for row in rows:
        sid = row['series']
        for model in models:
            for width in protocol['widths']:
                expected.add(('numerical', sid, model, width, 'radix_exact', None, None))
                expected.add(('numerical', sid, model, width, 'klein250', 250, None))
                for budget in protocol['threshold_budgets']:
                    expected.add(('numerical', sid, model, width, 'matched_sampled', budget, None))
            if sid in subset:
                expected.add(('validation', sid, model, 30, 'dense_exact', None, None))
                expected.add(('validation', sid, model, 30, 'klein_exact', row['n'], None))
                for rep in range(5):
                    for method in protocol['timing']['methods']:
                        budget = 250 if method in ('klein250', 'matched250') else None
                        expected.add(('timing', sid, model, 30, method, budget, rep))
    fields = ('phase', 'series', 'model', 'width', 'method', 'thresholds', 'repetition')
    calls = [r for r in records if r['phase'] in ('numerical', 'validation', 'timing')]
    lookup = unique_index(calls, lambda r: tuple(r[k] for k in fields), expected, 'main metric calls')
    input_rows = [r for r in records if r['phase'] == 'input']
    unique_index(input_rows, lambda r: (r['series'], r['model']),
                 {(r['series'], m) for r in rows for m in models}, 'input statistics')
    require(len(calls) == 46584, 'Main call count differs')
    require(all(r['phase'] in ('input', 'collection', 'numerical', 'validation', 'timing') for r in records), 'Unknown phase')
    parity = []
    for r in records:
        require(r['source_manifest_sha256'] == bundle.hashes[f'{MAIN}/source_manifest.json'], 'Record source chain differs')
        if r['phase'] == 'collection': continue
        input_identity(r, byseries[r['series']])
        if r['phase'] == 'input':
            require(1 <= r['distinct_scores'] <= 101 and r['n'] == byseries[r['series']]['n'], 'Score precision metadata differs')
            continue
        require(r['status'] == 'ok' and math.isfinite(r['value']), 'Failed or nonfinite main call')
        require(r['key'] == json.dumps([r[k] for k in fields], separators=(',', ':')), 'Canonical metric key differs')
        if r['phase'] == 'timing': require(math.isfinite(r['seconds']) and r['seconds'] > 0, 'Invalid timing duration')
        if r['phase'] in ('validation', 'timing') or r['method'] == 'klein250':
            method, budget = ('matched_sampled', 250) if r['method'] in ('klein250', 'matched250') else ('radix_exact', None)
            base = lookup['numerical', r['series'], r['model'], r['width'], method, budget, None]
            error = abs(base['value']-r['value']); parity.append(error)
            require(error <= protocol['parity_tolerance'], 'Control parity differs')
    panels, primary_cases = {}, None
    expected_panels = {f'L{w}_H{h}' for w in protocol['widths'] for h in protocol['threshold_budgets']}
    require(set(report['panels']) == expected_panels and len(expected_panels) == 18, 'Sensitivity coverage differs')
    for width in protocol['widths']:
        for budget in protocol['threshold_budgets']:
            key = f'L{width}_H{budget}'
            cases = []
            for row in sorted(rows, key=lambda r: r['series']):
                exact = {m: lookup['numerical', row['series'], m, width, 'radix_exact', None, None]['value'] for m in models}
                sampled = {m: lookup['numerical', row['series'], m, width, 'matched_sampled', budget, None]['value'] for m in models}
                cases.append(dict(numerical_decision(exact, sampled), series=row['series'], family=row['family']))
            frozen = report['panels'][key]
            same(cases, frozen['cases'], key+'.cases')
            summary = numerical_summary(cases)
            same(summary, frozen['pooled'], key+'.pooled')
            family = {f: numerical_summary([c for c in cases if c['family'] == f]) for f in sorted({r['family'] for r in rows})}
            same(family, frozen['per_family'], key+'.families')
            equal = {k: statistics.mean(f[k] for f in family.values()) for k in frozen['equal_family']}
            same(equal, frozen['equal_family'], key+'.equal_family')
            harmful = [c for c in cases if c['best_regret'] >= .01]
            nf = len({c['family'] for c in harmful})
            gate = len(harmful)/128 >= .05 and nf >= 3
            require(frozen['complete_series'] == 128 and frozen['missing_series'] == []
                    and frozen['families_with_practical_regret'] == nf
                    and frozen['effect_threshold_passed'] == gate
                    and frozen['promotion_gate_passed'] == gate, key+': coverage or gate differs')
            panels[key] = dict(series=128, harmful=len(harmful), harmful_families=nf,
                               maximum_regret=summary['maximum_best_regret'])
            if key == 'L30_H250': primary_cases = cases
    require(panels['L30_H250']['harmful'] == 8 and panels['L30_H250']['harmful_families'] == 4, 'Primary finding differs')
    same(report['primary'], report['panels']['L30_H250'], 'primary report alias')
    claim = bundle.json(f'{MAIN}/primary-validated-claim-table.json')
    same(claim['metrics'], report['primary']['pooled'], 'primary claim table')
    same(claim['per_family'], report['primary']['per_family'], 'primary family table')
    return dict(calls=len(calls), input_statistics=len(input_rows), sensitivity_cells=panels,
                control_comparisons=len(parity), maximum_control_difference=max(parity)), lookup, primary_cases


def interval(row):
    low, high, scale = (int(row[k]) for k in ('lower_numerator', 'upper_numerator', 'scale'))
    require(scale > 0 and 0 <= low <= high <= scale, 'Invalid certificate interval')
    return Fraction(low, scale), Fraction(high, scale)


def integer_decision(rows, sampled):
    model = unique_index(rows, lambda r: r['model'], name='certificate models')
    require(len(model) >= 2 and sampled and set(sampled) <= model.keys(), 'Invalid sampled winner set')
    bounds = {m: interval(r) for m, r in model.items()}
    winners = sorted(m for m, (a, b) in bounds.items() if all(a > d for o, (c, d) in bounds.items() if o != m))
    lower = max(Fraction(0), max(a for a, b in bounds.values())-max(bounds[m][1] for m in sampled))
    upper = max(b for a, b in bounds.values())-max(bounds[m][0] for m in sampled)
    return winners, lower, upper


def audit_certificates(bundle, manifest, numerical):
    datasets = {}
    reports = {}
    for directory, budgets in ((PARTIAL, [250, 1000]), (FULL, [None])):
        protocol = bundle.json(f'{directory}/protocol.json'); bundle.sources(protocol['sources'])
        bundle.hash(f'{CORPUS}/manifest.json', protocol['manifest_sha256'])
        completion, report = bundle.json(f'{directory}/completion.json'), bundle.json(f'{directory}/report.json')
        for receipt in (completion, report):
            bundle.hash(f'{directory}/records.jsonl', receipt['records_sha256'])
            bundle.hash(f'{directory}/protocol.json', receipt['protocol_sha256'])
        records = bundle.jsonl(f'{directory}/records.jsonl')
        expected = {(i, m, b) for i in range(128) for m in manifest['models'] for b in budgets}
        data = unique_index(records, lambda r: (r['series_index'], r['model'], r['budget'] if directory == PARTIAL else None), expected, directory)
        require(completion['record_count'] == report['record_count'] == len(expected), 'Certificate receipt count differs')
        unique_index(report['decisions'], lambda d: (d['series_index'], d['budget']),
                     {(i, h) for i in range(128) for h in (250, 1000)}, 'certificate report decisions')
        for (i, model, budget), r in data.items():
            require(r['status'] == 'ok' and r['width'] == 30, 'Failed certificate call')
            require(r['protocol_sha256'] == bundle.hashes[f'{directory}/protocol.json'], 'Certificate source chain differs')
            input_identity(r, manifest['series'][i], 'labels_sha256', 'scores_sha256')
            interval(r)
            if directory == FULL:
                require(r['budget'] == r['n'] == manifest['series'][i]['n']
                        and r['thresholds_retained'] == r['distinct_scores'], 'Full distinct grid differs')
            else:
                for field, method, h in [('sampled_float', 'matched_sampled', budget), ('exhaustive_float', 'radix_exact', None)]:
                    base = numerical['numerical', r['series'], model, 30, method, h, None]['value']
                    require(abs(r[field]-base) <= 2e-10, 'Certificate numerical selector/reference differs')
        datasets[directory], reports[directory] = data, report
    bundle.hash(f'{PARTIAL}/records.jsonl', bundle.json(f'{FULL}/protocol.json')['prior_records_sha256'])
    comparisons = unique_index(reports[FULL]['interval_comparisons'],
        lambda d: (d['series_index'], d['model'], d['budget']),
        {(i, m, h) for i in range(128) for m in manifest['models'] for h in (250, 1000)},
        'full/partial interval comparisons')
    summary = {}
    for budget in [250, 1000]:
        partial_decisions = unique_index([d for d in reports[PARTIAL]['decisions'] if d['budget'] == budget], lambda d: d['series_index'], range(128), 'partial decisions')
        full_decisions = unique_index([d for d in reports[FULL]['decisions'] if d['budget'] == budget], lambda d: d['series_index'], range(128), 'full decisions')
        pc = fc = wrong = harmful = below = 0
        maximum_upper = Fraction(0)
        for i in range(128):
            pr = [datasets[PARTIAL][i, m, budget] for m in manifest['models']]
            fr = [datasets[FULL][i, m, None] for m in manifest['models']]
            best = max(r['sampled_float'] for r in pr)
            sampled = sorted(r['model'] for r in pr if best-r['sampled_float'] <= 1e-10)
            for rr, d in [(pr, partial_decisions[i]), (fr, full_decisions[i])]:
                win, lower, upper = integer_decision(rr, sampled)
                require(d['status'] == 'complete' and d['sampled_winner_set'] == sampled
                        and d['certified_unique_winner'] == win, 'Integer winner differs')
                require(Fraction(int(d['regret_lower_numerator']), int(d['regret_lower_denominator'])) == lower
                        and d['sampled_set_certifiably_suboptimal'] == (lower > 0), 'Exact regret differs')
            pw, _, _ = integer_decision(pr, sampled)
            fw, lower, upper = integer_decision(fr, sampled)
            pc += bool(pw); fc += bool(fw); wrong += lower > 0
            harmful += lower >= Fraction(1, 100); below += upper < Fraction(1, 100)
            maximum_upper = max(maximum_upper, upper)
            require(full_decisions[i]['sampled_set_certified_regret_at_least_0_01'] == (lower >= Fraction(1, 100)), 'Cutoff claim differs')
            for a, b in zip(pr, fr):
                al, au = interval(a); bl, bu = interval(b)
                require(max(al, bl) <= min(au, bu), 'Disjoint same-target certificates')
                relation = comparisons[i, a['model'], budget]
                require(relation['overlap'] and relation['identical'] == (al == bl and au == bu)
                        and relation['full_contained_in_sampled'] == (al <= bl <= bu <= au),
                        'Recorded interval relation differs')
        require(pc == {250: 63, 1000: 94}[budget] and fc == 128, 'Certified winner counts differ')
        require(wrong == {250: 10, 1000: 1}[budget] and harmful == {250: 8, 1000: 0}[budget]
                and harmful+below == 128, 'Guaranteed regret counts differ')
        psummary = reports[PARTIAL]['budgets'][str(budget)]
        fsummary = reports[FULL]['comparison_budgets'][str(budget)]
        require(psummary['certified_unique_winners'] == pc and psummary['successful_scalar_calls'] == 1536
                and psummary['failed_scalar_calls'] == 0 and psummary['complete_series'] == 128,
                'Partial report summary differs')
        require(fsummary['full_certified_unique_winners'] == fc
                and fsummary['prior_certified_unique_winners'] == pc
                and fsummary['certified_suboptimal_sampled_sets'] == wrong
                and fsummary['certified_regret_at_least_0_01'] == harmful,
                'Full report summary differs')
        summary[str(budget)] = dict(partial_certified_winners=pc, full_certified_winners=fc,
            provably_suboptimal_sampled_sets=wrong, regret_at_least_0_01=harmful,
            regret_below_0_01=below, maximum_regret_upper_fraction=[str(maximum_upper.numerator), str(maximum_upper.denominator)])
    return summary, datasets


def stopping_state(state, p0):
    a, count = state['original_positive_count'], state['predicted_count']
    low, high, D = (int(state[k]) for k in ('buffer_lower_numerator', 'buffer_upper_numerator', 'weight_scale'))
    h, K = state['hit_count'], state['components']
    require(D == 1 << 32 and 0 <= a <= p0 and a <= count and 0 <= low <= high <= (count-a)*D
            and K > 0 and 0 <= h <= K, 'Invalid stopping witness bounds')
    rhs = 2*(p0-a)*D
    require(int(state['saturation_buffer_threshold_numerator']) == rhs
            and int(state['lower_mass_minus_threshold_numerator']) == low-rhs
            and int(state['upper_mass_minus_threshold_numerator']) == high-rhs, 'Forged stopping margins')
    def recall(b): return Fraction(h*min(2*(a*D+b), 2*p0*D+b), K*(2*p0*D+b))
    rl, ru = recall(low), recall(high)
    for key, value in [('recall_lower_fraction', rl), ('recall_upper_fraction', ru)]:
        require(Fraction(*(int(x) for x in state[key])) == value, 'Forged recall fraction')
    return rl, ru


def audit_saturation(bundle, manifest, primary):
    protocol, report = bundle.json(f'{SAT}/protocol.json'), bundle.json(f'{SAT}/report.json')
    bundle.sources(protocol['sources'])
    bundle.hash(f'{CORPUS}/manifest.json', protocol['manifest_sha256'])
    bundle.hash(f'{MAIN}/primary-signed-error-extraction.json', protocol['extraction_sha256'])
    bundle.hash(f'{SAT}/protocol.json', report['protocol_sha256'])
    bundle.hash(f'{SAT}/records.jsonl', report['records_sha256'])
    harmful = {r['series'] for r in primary if r['best_regret'] >= .01}
    require(set(protocol['series']) == harmful and len(harmful) == 8, 'Diagnostic selection differs')
    records = bundle.jsonl(f'{SAT}/records.jsonl')
    keyed = unique_index(records, lambda r: (r['series'], r['model']),
        {(s, m) for s in harmful for m in manifest['models']}, 'diagnostic model records')
    for r in records:
        unique_index(r['per_width'], lambda w: w['width'], range(31), 'diagnostic widths')
        for w in r['per_width']:
            require(w['first_saturation_index_integer_verified'] is True, 'Producer stopping test failed')
            require(abs(w['total_error']-(w['sampled']-w['exact'])) < 3e-13, 'Diagnostic error identity differs')
            require(abs(w['post_saturation_change']-(w['sampled']-w['saturation_inserted'])) < 3e-13, 'Insertion identity differs')
            total = sum(w[k] for k in ('post_saturation_buffer_mass_term', 'post_saturation_original_mass_term', 'post_saturation_count_dilution_term'))
            require(abs(total-w['post_saturation_change']) < 3e-13, 'Decomposition identity differs')
        for key, value in r['means'].items():
            require(abs(value-statistics.mean(w[key] for w in r['per_width'])) < 3e-13, 'Diagnostic mean differs')
    replay = bundle.json(f'{SAT}/integer-replay-protocol.json')
    receipt = bundle.json(f'{SAT}/integer-replay-receipt.json')
    require(receipt['status'] == 'PASS' and receipt['model_records'] == 96
            and receipt['width_records'] == receipt['first_saturation_proofs'] == 2976,
            'Integer replay receipt counts differ')
    bundle.hash(f'{SAT}/integer-replay-protocol.json', receipt['protocol_sha256'])
    bundle.hash('experiments/exploration/replay_msad_saturation_integers_20261023.py', receipt['source_sha256'])
    require(receipt['source_sha256'] == replay['source_sha256'], 'Replay source chain differs')
    bundle.hash(f'{SAT}/protocol.json', replay['producer_protocol_sha256'])
    bundle.hash(f'{SAT}/records.jsonl', replay['producer_records_sha256'])
    bundle.hash(f'{CORPUS}/manifest.json', replay['manifest_sha256'])
    bundle.hash(f'{SAT}/integer-replay-witnesses.jsonl', receipt['witnesses_sha256'])
    witnesses = bundle.jsonl(f'{SAT}/integer-replay-witnesses.jsonl')
    unique_index(witnesses, lambda w: (w['series'], w['model'], w['width']),
                 {(s, m, w) for s in harmful for m in manifest['models'] for w in range(31)}, 'integer stopping witnesses')
    source_rows = {r['series']: r for r in manifest['series']}
    for w in witnesses:
        current, previous = w['current'], w['previous']
        require(w['first_saturation_proved'] is True
                and w['npz_sha256'] == source_rows[w['series']]['npz_sha256']
                and w['total_original_positives'] == source_rows[w['series']]['positive_points']
                and current['components'] == previous['components'], 'Stopping witness input differs')
        require(stopping_state(current, w['total_original_positives'])[0] == 1
                and stopping_state(previous, w['total_original_positives'])[1] < 1,
                'First saturation not proved')
        require(previous['predicted_count'] < current['predicted_count'], 'Nonincreasing threshold count')
        producer = keyed[w['series'], w['model']]['per_width'][w['width']]
        require(current['predicted_count'] == producer['saturation_global_count'], 'Saturation boundary differs')
    restored = 0
    unique_index(report['decisions'], lambda d: d['series'], harmful, 'saturation winner decisions')
    for d in report['decisions']:
        rr = [keyed[d['series'], m] for m in manifest['models']]
        sets = {}
        for key in ('exact', 'sampled', 'saturation_inserted'):
            best = max(r['means'][key] for r in rr)
            sets[key] = sorted(r['model'] for r in rr if best-r['means'][key] <= 1e-10)
        require(sets == d['winner_sets'], 'Saturation intervention winner differs')
        restored += sets['exact'] == sets['saturation_inserted'] and sets['exact'] != sets['sampled']
    require(restored == 3, 'Restoration count differs')
    return dict(model_records=96, integer_stopping_proofs=len(witnesses), restored_winners=restored)


def audit_overlap(bundle, primary):
    overlap = bundle.json(OVERLAP)
    bundle.hash(f'{CORPUS}/manifest.json', overlap['manifest_sha256'])
    bundle.hash('artifacts/msad-score-provenance-20261023/audit_one_point_overlap.py', overlap['source_sha256'])
    matched = set(overlap['selected_with_joint_one_point_matches'])
    derived = {m['selected_series'] for m in overlap['matches'] if m['labels_match']
               and (m['observations_exact_match'] or m['observations_standardized_match'])}
    require(matched == derived and len(matched) == 20, 'Overlap classification differs')
    remaining = [c for c in primary if c['series'] not in matched]
    harmful = [c for c in remaining if c['best_regret'] >= .01]
    require(len(remaining) == 108 and len(harmful) == 4 and len({c['family'] for c in harmful}) == 2, 'Overlap subgroup differs')
    return dict(matched=20, nonmatching=108, nonmatching_harmful=4,
                nonmatching_harmful_families=2, maximum_nonmatching_regret=max(c['best_regret'] for c in remaining))


def audit_cost(bundle, manifest, numerical, certificates):
    protocol = bundle.json(f'{COST}/protocol.json'); bundle.sources(protocol['sources'])
    run = bundle.json(f'{COST}/run-inputs.json')
    bundle.hash(f'{COST}/protocol.json', run['protocol_sha256']); bundle.sources(run['reference_sha256'])
    report = bundle.json(f'{COST}/report-{ANCHORS[f"{COST}/records.jsonl"][:16]}.json')
    bundle.hash(f'{COST}/records.jsonl', report['records_sha256'])
    bundle.hash(f'{COST}/protocol.json', report['protocol_sha256'])
    rows = bundle.jsonl(f'{COST}/records.jsonl')
    expected = {(r['series'], m, rep, method) for r in protocol['series'] for m in protocol['models']
                for rep in range(5) for method in ('certificate', 'full_certificate', 'radix_exact')}
    keyed = unique_index(rows, lambda r: (r['series'], r['model'], r['repetition'], r['method']), expected, 'cost calls')
    require(len(keyed) == 5400, 'Cost count differs')
    series = {r['series']: (i, r) for i, r in enumerate(manifest['series'])}
    groups = defaultdict(list)
    for r in rows:
        i, row = series[r['series']]
        input_identity(r, row)
        require(r['status'] == 'ok' and math.isfinite(r['seconds']) and r['seconds'] > 0, 'Failed/invalid cost call')
        require(r['protocol_sha256'] == bundle.hashes[f'{COST}/protocol.json'] and r['width'] == 30, 'Cost provenance differs')
        require(r['key'] == json.dumps([r['series'], r['model'], r['repetition'], r['method']], separators=(',', ':')), 'Cost key differs')
        prefix = f"{protocol['seed']}|certificate-full-cost|{r['series']}|{r['model']}|{r['repetition']}|"
        order = sorted(protocol['methods'], key=lambda m: hashlib.sha256((prefix+m).encode()).digest())
        require(order[r['order_index']] == r['method'], 'Frozen cost order differs')
        if r['method'] == 'radix_exact':
            require(r['thresholds'] is None and abs(r['value']-numerical['numerical', r['series'], r['model'], 30, 'radix_exact', None, None]['value']) <= 2e-10, 'Cost exact output differs')
        else:
            directory, budget = (PARTIAL, 250) if r['method'] == 'certificate' else (FULL, None)
            reference = certificates[directory][i, r['model'], budget]
            require(r['thresholds'] == (250 if directory == PARTIAL else row['n']), 'Cost threshold budget differs')
            for key in ('lower_numerator', 'upper_numerator', 'scale', 'thresholds_retained'):
                require(r[key] == reference[key], 'Cost integer output differs')
        groups[r['series'], r['model'], r['method']].append(r['seconds'])
    cases = unique_index(report['cases'], lambda c: (c['series'], c['model']),
                         {(r['series'], m) for r in protocol['series'] for m in protocol['models']}, 'cost case medians')
    for (sid, model), c in cases.items():
        for method in protocol['methods']:
            same(statistics.median(groups[sid, model, method]), c['median_seconds'][method], 'cost median')
    require(report['expected_records'] == report['recorded_records'] == 5400
            and report['missing_records'] == 0 and report['comparative_claim_eligible'], 'Cost report coverage differs')
    return dict(calls=5400, complete_cases=len(cases), integer_outputs_identical_to_accuracy=True)


def audit(root=ROOT):
    bundle = Bundle(root)
    for path, expected in ANCHORS.items(): bundle.hash(path, expected)
    manifest = bundle.json(f'{CORPUS}/manifest.json')
    main, numerical, primary = audit_main(bundle, manifest)
    certificates, datasets = audit_certificates(bundle, manifest, numerical)
    saturation = audit_saturation(bundle, manifest, primary)
    overlap = audit_overlap(bundle, primary)
    cost = audit_cost(bundle, manifest, numerical, datasets)
    return {'status': 'PASS', 'audit_source_sha256': sha256(Path(__file__)),
        'scope': 'Cache-independent public ledger, source-chain and integer-witness audit; no raw input loaded and no fresh metric execution',
        'main_study': main, 'integer_certificates': certificates,
        'saturation': saturation, 'overlap_subgroup': overlap, 'certificate_cost': cost,
        'verified_repository_sha256': dict(sorted(bundle.hashes.items())),
        'external_source_commitments_not_rehashed': bundle.external,
        'not_recomputed': ['raw source parsing or input-array hashes', 'metric values from original score arrays',
                           'square-root mass brackets from raw labels', 'bootstrap RNG draws', 'cost ratio aggregation beyond per-case medians']}


def output_path(path, root=ROOT):
    target = Path(path).expanduser().resolve()
    require(not target.is_relative_to((Path(root)/'artifacts').resolve()), 'Output must be outside artifacts')
    require(not target.exists(), 'Output already exists; refusing to overwrite')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New JSON receipt outside artifacts')
    args = parser.parse_args()
    try:
        target = output_path(args.output)
        result = audit()
        with target.open('x') as stream:
            json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
        print(json.dumps({'status': result['status'], 'receipt': str(target),
                          'primary': result['main_study']['sensitivity_cells']['L30_H250'],
                          'integer_stopping_proofs': result['saturation']['integer_stopping_proofs']}))
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        print(f'Audit failed: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == '__main__': main()
