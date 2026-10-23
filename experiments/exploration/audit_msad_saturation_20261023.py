"""Read-only standard-library audit of the exploratory saturation ledger."""
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'artifacts/msad-saturation-diagnostic-20261023'


def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rational(value): return Fraction.from_float(value)


def main():
    protocol, report = read(OUT/'protocol.json'), read(OUT/'report.json')
    assert digest(OUT/'protocol.json') == report['protocol_sha256']
    assert digest(OUT/'records.jsonl') == report['records_sha256']
    for path, expected in protocol['sources'].items(): assert digest(ROOT/path) == expected
    manifest_path = ROOT/'artifacts/msad-corpus-20261023/manifest.json'
    extraction_path = ROOT/'artifacts/msad-sampling-20261023/primary-signed-error-extraction.json'
    assert digest(manifest_path) == protocol['manifest_sha256']
    assert digest(extraction_path) == protocol['extraction_sha256']
    extraction, manifest = read(extraction_path), read(manifest_path)
    assert set(protocol['series']) == {r['series'] for r in extraction['harmful_cases']}
    assert len(protocol['series']) == len(set(protocol['series'])) == 8
    records = [json.loads(s) for s in (OUT/'records.jsonl').read_text().splitlines()]
    expected = {(s, m) for s in protocol['series'] for m in protocol['models']}
    assert len(records) == 96
    assert {(r['series'], r['model']) for r in records} == expected
    inputs = {r['series']: r for r in manifest['series']}
    group = defaultdict(list)
    largest_residual = Fraction(0)
    largest_mean_residual = 0.
    float_identities = [
        ('total_error', ['sampled', 'exact'], [1, -1]),
        ('remaining_pre_saturation_error', ['saturation_inserted', 'exact'], [1, -1]),
        ('post_saturation_change', ['sampled', 'saturation_inserted'], [1, -1]),
        ('post_saturation_change', ['post_saturation_buffer_mass_term',
             'post_saturation_original_mass_term', 'post_saturation_count_dilution_term'], [1, 1, 1]),
        ('total_error', ['post_saturation_change', 'remaining_pre_saturation_error'], [1, 1])]
    for r in records:
        assert r['npz_sha256'] == inputs[r['series']]['npz_sha256']
        assert r['family'] == inputs[r['series']]['family']
        assert r['all_saturation_indices_integer_verified'] is True
        assert [v['width'] for v in r['per_width']] == list(range(31))
        for v in r['per_width']:
            assert v['first_saturation_index_integer_verified'] is True
            assert 0 < v['saturation_global_count'] <= v['next_sampled_global_count'] <= inputs[r['series']]['n']
            for key, terms, signs in float_identities:
                residual = abs(rational(v[key])-sum((sign*rational(v[term]) for term, sign in zip(terms, signs)), Fraction(0)))
                largest_residual = max(largest_residual, residual)
                assert residual < Fraction(3, 10**13)
        for key, value in r['means'].items():
            mean = math.fsum(v[key] for v in r['per_width'])/31
            largest_mean_residual = max(largest_mean_residual, abs(value-mean))
            assert abs(value-mean) < 3e-13
        group[r['series']].append(r)
    restored, decisions = [], []
    claimed = {r['series']: r['winner_sets'] for r in report['decisions']}
    for series, rr in group.items():
        sets = {}
        for key in ['exact', 'sampled', 'saturation_inserted']:
            best = max(r['means'][key] for r in rr)
            sets[key] = sorted(r['model'] for r in rr if best-r['means'][key] <= 1e-10)
        assert sets == claimed[series]
        if sets['exact'] == sets['saturation_inserted'] and sets['exact'] != sets['sampled']:
            restored.append(series)
        decisions.append({'series': series, 'winner_sets': sets})
    assert len(restored) == 3
    pair = [dict(series=r['series'], model=r['model'], means=r['means']) for r in records
            if 'DISTORTEDCIMIS44AirTemperature1' in r['series'] and r['model'] in ['CNN', 'LOF']]
    result = {'status': 'PASS_SOURCE_ALGEBRA_AND_LEDGER_REPLAY',
        'audit_source_sha256': digest(Path(__file__)), 'protocol_sha256': digest(OUT/'protocol.json'),
        'records_sha256': digest(OUT/'records.jsonl'), 'report_sha256': digest(OUT/'report.json'),
        'model_records_checked': 96, 'width_records_checked': 2976,
        'all_eight_cases_all_twelve_models': True,
        'all_logged_integer_stopping_checks_true': True,
        'integer_stop_test_algebra_reviewed': 'Full coverage and B>=2(P0-A); use current lower and prior upper weight brackets',
        'integer_states_independently_recomputed': False,
        'integer_evidence_scope': 'Frozen producer source algebra and all logged booleans verified; ledger omits raw integer witnesses, no kernel/input replay performed during timings',
        'largest_binary64_identity_residual': float(largest_residual),
        'largest_mean_residual': largest_mean_residual,
        'restored_winner_count': len(restored), 'restored_series': sorted(restored),
        'cnn_lof_decomposition': pair,
        'interpretation': 'Exploratory insertion intervention includes buffer mass, original mass, and count dilution; restoring 3/8 does not attribute all three reversals solely to buffer inflation'}
    with (OUT/'independent-ledger-review.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
