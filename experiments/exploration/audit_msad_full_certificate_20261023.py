"""Standard-library ledger replay; imports no metric or study implementation."""
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import statistics

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'artifacts/msad-full-certificate-20261023'
PRIOR = ROOT/'artifacts/msad-certificate-20261023'


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path): return [json.loads(s) for s in path.read_text().splitlines()]
def bounds(row):
    low, high, scale = (int(row[k]) for k in ['lower_numerator', 'upper_numerator', 'scale'])
    assert 0 <= low <= high <= scale and scale > 0
    return Fraction(low, scale), Fraction(high, scale)


def main():
    protocol, report = read(OUT/'protocol.json'), read(OUT/'report.json')
    manifest = read(ROOT/protocol['manifest'])
    assert sha(ROOT/protocol['manifest']) == protocol['manifest_sha256']
    assert sha(PRIOR/'records.jsonl') == protocol['prior_records_sha256']
    assert sha(PRIOR/'protocol.json') == protocol['prior_protocol_sha256']
    assert sha(OUT/'protocol.json') == report['protocol_sha256']
    assert sha(OUT/'records.jsonl') == report['records_sha256']
    for path, digest in protocol['sources'].items(): assert sha(ROOT/path) == digest
    full = rows(OUT/'records.jsonl')
    previous = {(r['series_index'], r['model'], r['budget']): r for r in rows(PRIOR/'records.jsonl')}
    assert len(previous) == 3072
    lookup = {(r['series_index'], r['model']): r for r in full}
    assert len(full) == len(lookup) == 1536
    assert set(lookup) == {(i, m) for i in range(128) for m in protocol['models']}
    group = defaultdict(dict)
    for r in full:
        source = manifest['series'][r['series_index']]
        assert r['status'] == 'ok' and r['width'] == 30 and r['budget'] == source['n']
        assert r['series'] == source['series'] and r['family'] == source['family']
        assert r['npz_sha256'] == source['npz_sha256']
        assert r['labels_sha256'] == source['array_sha256']['labels']
        assert r['scores_sha256'] == source['array_sha256'][r['model']]
        assert r['thresholds_retained'] == r['distinct_scores']
        group[r['series_index']][r['model']] = bounds(r)
    decisions = {(d['series_index'], d['budget']): d for d in report['decisions']}
    assert len(decisions) == 256
    comparison = {(d['series_index'], d['model'], d['budget']): d for d in report['interval_comparisons']}
    assert len(comparison) == 3072
    outputs = {}
    for budget in [250, 1000]:
        harmful, wrong, winners = [], [], []
        nesting_escape = Fraction(0)
        for index, interval in group.items():
            selected = [previous[index, m, budget] for m in protocol['models']]
            maximum = max(r['sampled_float'] for r in selected)
            sampled = sorted(r['model'] for r in selected if maximum-r['sampled_float'] <= 1e-10)
            certified = sorted(m for m, (a, b) in interval.items()
                               if all(a > d for other, (c, d) in interval.items() if other != m))
            regret = max(Fraction(0), max(a for a, b in interval.values())
                         - max(interval[m][1] for m in sampled))
            d = decisions[index, budget]
            assert d['status'] == 'complete' and d['sampled_winner_set'] == sampled
            assert d['certified_unique_winner'] == certified
            assert regret == Fraction(int(d['regret_lower_numerator']), int(d['regret_lower_denominator']))
            assert d['sampled_set_certifiably_suboptimal'] == (regret > 0)
            assert d['sampled_set_certified_regret_at_least_0_01'] == (regret >= Fraction(1, 100))
            if certified: winners.append(index)
            if regret > 0: wrong.append(index)
            if regret >= Fraction(1, 100): harmful.append(index)
            for m, (a, b) in interval.items():
                c, e = bounds(previous[index, m, budget])
                cmp = comparison[index, m, budget]
                assert cmp['overlap'] == (max(a, c) <= min(b, e))
                assert cmp['full_contained_in_sampled'] == (c <= a <= b <= e)
                assert cmp['identical'] == (a == c and b == e)
                nesting_escape = max(nesting_escape, c-a, b-e)
        family_harmful = defaultdict(int)
        for index in harmful: family_harmful[manifest['series'][index]['family']] += 1
        outputs[str(budget)] = {'certified_unique_winners': len(winners),
            'certified_suboptimal_sampled_sets': len(wrong), 'certified_regret_at_least_0_01': len(harmful),
            'harmful_series_indices': harmful, 'harmful_families': dict(family_harmful),
            'maximum_full_interval_escape_beyond_prior_informational': float(nesting_escape),
            'retained_thresholds_median': statistics.median(r['thresholds_retained'] for r in previous.values() if r['budget'] == budget)}
        assert len(winners) == report['comparison_budgets'][str(budget)]['full_certified_unique_winners']
        assert len(wrong) == report['comparison_budgets'][str(budget)]['certified_suboptimal_sampled_sets']
        assert len(harmful) == report['comparison_budgets'][str(budget)]['certified_regret_at_least_0_01']
        for fam, data in report['comparison_budgets'][str(budget)]['per_family'].items():
            assert data['certified_regret_at_least_0_01'] == family_harmful[fam]
    result = {'status': 'PASS', 'audit_source_sha256': sha(Path(__file__)),
        'imports': 'Python standard library only; no study/metric implementation',
        'protocol_sha256': sha(OUT/'protocol.json'), 'records_sha256': sha(OUT/'records.jsonl'),
        'report_sha256': sha(OUT/'report.json'), 'endpoint_records_checked': 1536,
        'comparison_pairs_checked': 3072, 'decisions_checked': 256,
        'full_retained_thresholds_median': statistics.median(r['thresholds_retained'] for r in full),
        'comparison_budgets': outputs}
    with (OUT/'independent-ledger-audit.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
