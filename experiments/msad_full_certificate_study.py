"""Separately frozen full-grid, same-guarantee certificate baseline."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import statistics
import sys

os.environ.setdefault('NUMBA_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
MANIFEST = ROOT/'artifacts/msad-corpus-20261023/manifest.json'
MANIFEST_SHA = '5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59'
PRIOR = ROOT/'artifacts/msad-certificate-20261023'
PRIOR_RECORDS_SHA = '4e557a2696ab92d35b2c433bdf98918de41afeb7e1a92172da62adfa52e185ab'
OUT = ROOT/'artifacts/msad-full-certificate-20261023'
SOURCES = ['experiments/msad_full_certificate_study.py',
           'tests/test_msad_full_certificate.py', 'src/sparse_vus/sampling.py',
           'src/sparse_vus/sampling_bounds.py', 'src/sparse_vus/core.py',
           'src/sparse_vus/radix.py', 'src/sparse_vus/pr_compiled.py',
           'src/sparse_vus/compiled.py', 'src/sparse_vus/__init__.py']


def now(): return datetime.now(timezone.utc).isoformat()
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def array_digest(a):
    a = np.ascontiguousarray(a)
    header = json.dumps({'dtype': a.dtype.str, 'shape': list(a.shape)}, sort_keys=True).encode()
    return hashlib.sha256(header+b'\0'+a.tobytes()).hexdigest()


def endpoints(row):
    lo, hi, scale = (int(row[k]) for k in ['lower_numerator', 'upper_numerator', 'scale'])
    if not 0 <= lo <= hi <= scale or scale <= 0:
        raise ValueError('Invalid integer interval')
    return Fraction(lo, scale), Fraction(hi, scale)


def decide(rows, sampled_winners):
    if len({r['model'] for r in rows}) != len(rows):
        raise ValueError('duplicate model')
    intervals = {r['model']: endpoints(r) for r in rows}
    if len(intervals) < 2 or not sampled_winners or not set(sampled_winners) <= intervals.keys():
        raise ValueError('Invalid model set')
    winners = sorted(m for m, (lo, _) in intervals.items()
                     if all(lo > hi for other, (_, hi) in intervals.items() if other != m))
    regret = max(Fraction(0), max(lo for lo, _ in intervals.values())
                 - max(intervals[m][1] for m in sampled_winners))
    return {'certified_unique_winner': winners,
            'sampled_set_certifiably_suboptimal': regret > 0,
            'sampled_set_certified_regret_at_least_0_01': regret >= Fraction(1, 100),
            'regret_lower_numerator': str(regret.numerator),
            'regret_lower_denominator': str(regret.denominator),
            'regret_lower_display': float(regret)}


def compare_intervals(full, sampled):
    fl, fu = endpoints(full)
    sl, su = endpoints(sampled)
    return {'overlap': max(fl, sl) <= min(fu, su),
            'full_contained_in_sampled': sl <= fl <= fu <= su,
            'identical': fl == sl and fu == su}


def freeze():
    if digest(MANIFEST) != MANIFEST_SHA or digest(PRIOR/'records.jsonl') != PRIOR_RECORDS_SHA:
        raise ValueError('Frozen input changed')
    manifest = read(MANIFEST)
    assert manifest['series_count'] == 128 and len(manifest['models']) == 12
    OUT.mkdir(exist_ok=False)
    protocol = {'study': 'msad-full-certificate-20261023', 'schema_version': 1,
        'frozen_utc': now(),
        'freeze_scope': 'Before observing any full-grid certificate outcomes; follows the original sampled-certificate and primary numerical outcomes, not an independent prospective replication.',
        'trigger_known_before_freeze': 'All 1536 published score vectors have at most 101 distinct values; primary sampled numerical regret gate has 8/128 cases across 4 families; H250/H1000 certificates confirm 63/94 unique winners.',
        'manifest': str(MANIFEST.relative_to(ROOT)), 'manifest_sha256': MANIFEST_SHA,
        'prior_records': str((PRIOR/'records.jsonl').relative_to(ROOT)),
        'prior_records_sha256': PRIOR_RECORDS_SHA,
        'prior_protocol_sha256': digest(PRIOR/'protocol.json'),
        'series_count': 128, 'models': manifest['models'], 'width': 30,
        'method': 'certified_sampled_pr(y, scores, max_buffer=30, thresholds=len(y))',
        'retained_grid': 'Every global distinct numerical score tie, deduplicated by the unchanged implementation',
        'target': 'Ideal real-arithmetic original dynamic VUS-PR; same directed integer guarantee as sampled certificates',
        'weight_bits': 32, 'output_bits': 56,
        'comparison_budgets': [250, 1000], 'sampled_winner_tolerance': 1e-10,
        'numerical_ground_truth': 'None: use exact integer/Fraction comparisons of intervals; floats are displays or previously declared sampled selectors only',
        'coverage': 'All 128 retained series by all 12 detector configurations; no outcome filtering',
        'winner_rule': 'Unique model whose integer lower bound strictly exceeds every other integer upper bound',
        'regret_rule': 'max full lower - max full upper over the entire sampled winner set, clipped at zero; compare exactly to 1/100',
        'interval_comparison': 'Check overlap, containment, and equality with both prior grids using exact fractions. Containment is descriptive because independent outward rounding need not preserve nesting.',
        'failure_policy': 'Retain each failed call in the 1536-call denominator; no reruns of observed failures',
        'timeout_seconds': 120,
        'timing': 'No timing claims; cost comparator is a separate addendum frozen before timings',
        'sources': {path: digest(ROOT/path) for path in SOURCES}}
    write_new(OUT/'protocol.json', protocol)
    (OUT/'ATTRIBUTION.md').write_text((ROOT/'artifacts/msad-corpus-20261023/ATTRIBUTION.md').read_text())
    print(digest(OUT/'protocol.json'))


def verify(expected=None):
    p = read(OUT/'protocol.json')
    ph = digest(OUT/'protocol.json')
    if expected and expected != ph: raise ValueError('Protocol changed')
    if digest(MANIFEST) != p['manifest_sha256']: raise ValueError('Manifest changed')
    if digest(PRIOR/'records.jsonl') != p['prior_records_sha256']: raise ValueError('Prior ledger changed')
    if digest(PRIOR/'protocol.json') != p['prior_protocol_sha256']: raise ValueError('Prior protocol changed')
    for path, value in p['sources'].items():
        if digest(ROOT/path) != value: raise ValueError('Source changed: '+path)
    return p, ph


def alarm(*_): raise TimeoutError('Frozen 120 second limit exceeded')


def run(expected):
    from sparse_vus.sampling_bounds import certified_sampled_pr
    p, ph = verify(expected)
    records = OUT/'records.jsonl'
    done = set()
    if records.exists():
        for line in records.read_text().splitlines():
            r = json.loads(line)
            key = (r['series_index'], r['model'])
            if key in done or r['protocol_sha256'] != ph: raise ValueError('Conflicting prior record')
            done.add(key)
    if not (OUT/'run.json').exists():
        write_new(OUT/'run.json', {'started_utc': now(), 'protocol_sha256': ph,
            'python': sys.version, 'numpy': np.__version__, 'platform': platform.platform()})
    signal.signal(signal.SIGALRM, alarm)
    with records.open('a') as stream:
        for index, row in enumerate(read(MANIFEST)['series']):
            verify(ph)
            source = ROOT/row['npz_path']
            if digest(source) != row['npz_sha256']: raise ValueError('NPZ changed')
            with np.load(source, allow_pickle=False) as package:
                arrays = {name: package[name] for name in ['labels']+p['models']}
            for name, value in arrays.items():
                if array_digest(value) != row['array_sha256'][name]: raise ValueError('Array changed')
            for model in p['models']:
                if (index, model) in done: continue
                r = {'series_index': index, 'series': row['series'], 'family': row['family'],
                    'model': model, 'n': row['n'], 'width': 30, 'budget': row['n'],
                    'protocol_sha256': ph, 'npz_sha256': row['npz_sha256'],
                    'labels_sha256': row['array_sha256']['labels'],
                    'scores_sha256': row['array_sha256'][model]}
                try:
                    signal.alarm(p['timeout_seconds'])
                    unique = int(np.unique(arrays[model]).size)
                    cert = certified_sampled_pr(arrays['labels'], arrays[model], 30, int(row['n']))
                    if cert.thresholds_retained != unique:
                        raise ValueError('Full grid did not retain every global distinct score tie')
                    r.update(status='ok', distinct_scores=unique, thresholds_retained=cert.thresholds_retained,
                        lower_numerator=str(cert.lower_numerator), upper_numerator=str(cert.upper_numerator),
                        scale=str(cert.scale), lower_display=cert.lower, upper_display=cert.upper)
                    endpoints(r)
                except Exception as exc:
                    r.update(status='failed', exception_type=type(exc).__name__, error=str(exc))
                finally:
                    signal.alarm(0)
                stream.write(json.dumps(r, allow_nan=False)+'\n')
                stream.flush()
                done.add((index, model))
            if (index+1) % 8 == 0: print(f'Completed {index+1}/128 series', flush=True)
    verify(ph)
    write_new(OUT/'completion.json', {'completed_utc': now(), 'protocol_sha256': ph,
        'record_count': len(done), 'records_sha256': digest(records)})
    report()


def report():
    p, ph = verify()
    completion = read(OUT/'completion.json')
    if digest(OUT/'records.jsonl') != completion['records_sha256']: raise ValueError('Ledger changed')
    rows = [json.loads(s) for s in (OUT/'records.jsonl').read_text().splitlines()]
    keys = [(r['series_index'], r['model']) for r in rows]
    expected = {(i, m) for i in range(128) for m in p['models']}
    if len(set(keys)) != len(keys) or set(keys) != expected: raise ValueError('Incomplete or duplicate coverage')
    prior = {(r['series_index'], r['model'], r['budget']): r for r in
             (json.loads(s) for s in (PRIOR/'records.jsonl').read_text().splitlines())}
    decisions, comparisons = [], []
    byseries = defaultdict(list)
    for r in rows:
        byseries[r['series_index']].append(r)
        if r['status'] != 'ok': continue
        for budget in p['comparison_budgets']:
            old = prior[(r['series_index'], r['model'], budget)]
            comparisons.append(dict(series_index=r['series_index'], model=r['model'], budget=budget,
                                    **compare_intervals(r, old)))
    for index, rr in sorted(byseries.items()):
        for budget in p['comparison_budgets']:
            d = {'series_index': index, 'series': rr[0]['series'], 'family': rr[0]['family'], 'budget': budget}
            if any(r['status'] != 'ok' for r in rr):
                d.update(status='incomplete'); decisions.append(d); continue
            old = [prior[(index, m, budget)] for m in p['models']]
            best = max(r['sampled_float'] for r in old)
            winners = sorted(r['model'] for r in old if best-r['sampled_float'] <= p['sampled_winner_tolerance'])
            d.update(status='complete', sampled_winner_set=winners, **decide(rr, winners))
            d['prior_certified_unique_winner'] = decide(old, winners)['certified_unique_winner']
            d['previous_certificate_preserved'] = (not d['prior_certified_unique_winner']
                                                  or d['prior_certified_unique_winner'] == d['certified_unique_winner'])
            decisions.append(d)
    good = [r for r in rows if r['status'] == 'ok']
    widths = [endpoints(r)[1]-endpoints(r)[0] for r in good]
    summaries = {}
    for budget in p['comparison_budgets']:
        ds = [d for d in decisions if d['budget'] == budget]
        complete = [d for d in ds if d['status'] == 'complete']
        family = {}
        for name in sorted({d['family'] for d in ds}):
            attempted = [d for d in ds if d['family'] == name]
            subset = [d for d in attempted if d['status'] == 'complete']
            family[name] = {'attempted': len(attempted), 'complete': len(subset),
                'certified_unique_winners': sum(bool(d['certified_unique_winner']) for d in subset),
                'certified_suboptimal_sampled_sets': sum(d['sampled_set_certifiably_suboptimal'] for d in subset),
                'certified_regret_at_least_0_01': sum(d['sampled_set_certified_regret_at_least_0_01'] for d in subset)}
        cmp = [r for r in comparisons if r['budget'] == budget]
        summaries[str(budget)] = {'complete_series': len(complete),
            'full_certified_unique_winners': sum(bool(d['certified_unique_winner']) for d in complete),
            'prior_certified_unique_winners': sum(bool(d['prior_certified_unique_winner']) for d in complete),
            'previous_certificate_preserved': all(d['previous_certificate_preserved'] for d in complete),
            'certified_suboptimal_sampled_sets': sum(d['sampled_set_certifiably_suboptimal'] for d in complete),
            'certified_regret_at_least_0_01': sum(d['sampled_set_certified_regret_at_least_0_01'] for d in complete),
            'max_certified_regret_lower': max((d['regret_lower_display'] for d in complete), default=None),
            'equal_family_certified_winner_fraction': statistics.mean(v['certified_unique_winners']/v['attempted'] for v in family.values()),
            'disjoint_interval_pairs': sum(not r['overlap'] for r in cmp),
            'full_contained_in_sampled_pairs': sum(r['full_contained_in_sampled'] for r in cmp),
            'identical_interval_pairs': sum(r['identical'] for r in cmp), 'per_family': family}
    result = {'status': 'COMPLETE_ALL_DECLARED_CASES_RETAINED', 'protocol_sha256': ph,
        'records_sha256': digest(OUT/'records.jsonl'), 'record_count': len(rows),
        'status_counts': dict(Counter(r['status'] for r in rows)),
        'distinct_scores_min': min((r['distinct_scores'] for r in good), default=None),
        'distinct_scores_max': max((r['distinct_scores'] for r in good), default=None),
        'interval_width_median': float(statistics.median(widths)) if widths else None,
        'interval_width_max': float(max(widths)) if widths else None,
        'comparison_budgets': summaries, 'decisions': decisions, 'interval_comparisons': comparisons,
        'scope': 'Same-guarantee full-grid baseline on the existing selected corpus; no float oracle or new algorithm claim'}
    write_new(OUT/'report.json', result)
    compact = {k: v for k, v in result.items() if k not in ['decisions', 'interval_comparisons', 'comparison_budgets']}
    compact['comparison_budgets'] = {k: {a: b for a, b in v.items() if a != 'per_family'} for k, v in summaries.items()}
    print(json.dumps(compact, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['freeze', 'run', 'report'])
    parser.add_argument('--protocol-sha256')
    args = parser.parse_args()
    if args.command == 'freeze': freeze()
    elif args.command == 'run':
        if not args.protocol_sha256: parser.error('--protocol-sha256 required')
        run(args.protocol_sha256)
    else: report()
