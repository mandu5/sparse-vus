"""Reconstruct the public consumer's complete trace without evaluator imports."""
import argparse
import json
from pathlib import Path
import statistics
import numpy as np
from audit_pvldb20261024 import digest, read, coverage, equivalent

KEYS = {'AUC-PR', 'AUC-ROC', 'VUS-PR', 'VUS-ROC', 'Standard-F1', 'PA-F1',
        'Event-based-F1', 'R-based-F1', 'Affiliation-F'}


def reconstruct(p, rows, workflows, expected_width):
    coverage([(r['trial'], r['model']) for r in rows],
             {(t, m) for t in range(len(p['order'])) for m in range(p['model_count'])})
    coverage([r['trial'] for r in workflows], set(range(len(p['order']))))
    index = {(r['trial'], r['model']): r for r in rows}
    maximum = 0.
    width = rows[0]['width']
    if not isinstance(width, int) or width < 0 or width != expected_width:
        raise ValueError('width')
    for r in rows:
        if r['method'] != p['order'][r['trial']] or r['width'] != width:
            raise ValueError('trace axes')
        if not np.isfinite([r['seconds'], r['vus_seconds']]).all() or not 0 < r['vus_seconds'] <= r['seconds']:
            raise ValueError('nested timings')
        if set(r['metrics']) != KEYS or not np.isfinite(list(r['metrics'].values())).all():
            raise ValueError('nine metric contract')
        ref = index[0, r['model']]['metrics']
        error = max(abs(r['metrics'][k] - ref[k]) for k in KEYS)
        maximum = max(maximum, error)
        if error > p['parity_atol']:
            raise ValueError('output parity')
    for w in workflows:
        t = w['trial']
        if w['method'] != p['order'][t] or w['width'] != width or w['series'] != p['case']['series']:
            raise ValueError('workflow axes')
        equivalent(w['outputs'], [index[t, m]['metrics'] for m in range(p['model_count'])], 'workflow outputs')
        equivalent(w['vus_seconds'], sum(index[t, m]['vus_seconds'] for m in range(p['model_count'])), 'VUS sum')
        if not np.isfinite(w['seconds']) or w['seconds'] < sum(index[t, m]['seconds'] for m in range(p['model_count'])):
            raise ValueError('workflow nesting')
    methods = {}
    for method in sorted(set(p['order'])):
        records = [w for w in workflows if w['method'] == method]
        methods[method] = {'total_seconds': [w['seconds'] for w in records],
            'vus_seconds': [w['vus_seconds'] for w in records],
            'median_total_seconds': statistics.median(w['seconds'] for w in records),
            'median_vus_seconds': statistics.median(w['vus_seconds'] for w in records),
            'vus_fraction_each_trial': [w['vus_seconds']/w['seconds'] for w in records]}
    return {'profiles_per_pass': p['model_count'], 'passes': len(workflows), 'metric_calls': len(rows),
        'width': width, 'series': p['case']['series'], 'n': p['case']['n'],
        'max_nine_metric_discrepancy': maximum, 'methods': methods,
        'total_median_ratio': methods['benchopt_pair']['median_total_seconds']/methods['radix_pair']['median_total_seconds'],
        'vus_median_ratio': methods['benchopt_pair']['median_vus_seconds']/methods['radix_pair']['median_vus_seconds'],
        'scope': 'One repeated public multi-metric consumer on fixed stored profiles; two trials per backend, no population CI, fitting excluded.'}


def audit(root, output):
    root = Path(root).resolve()
    base = root / 'artifacts/pvldb-research-20261024'
    folder = base / 'public-consumer'
    p, start, done = [read(folder / name) for name in ('protocol.json', 'run-start.json', 'complete.json')]
    if done['status'] != 'COMPLETE':
        raise ValueError('incomplete')
    for r in (start, done):
        if r['protocol_sha256'] != digest(folder / 'protocol.json'):
            raise ValueError('protocol binding')
    for name in ('profiles', 'workflows'):
        if digest(folder / (name + '.jsonl')) != done[name + '_sha256']:
            raise ValueError('trace binding')
    for path, h in p['source_sha256'].items():
        if digest(root / path) != h:
            raise ValueError('source binding: ' + path)
    for key, file in [('primary_protocol_sha256', 'protocol.json'), ('inputs_sha256', 'inputs.json')]:
        if digest(base / 'full-precision' / file) != p[key]:
            raise ValueError('parent binding')
    inputs = read(base / 'full-precision/inputs.json')
    expected = sorted(inputs['series'], key=lambda c: (-c['n'], c['series']))[0]
    equivalent(expected, p['case'], 'length-only choice')
    if digest(root / '.cache/pvldb-full-precision-20261024' / expected['file']) != expected['npz_sha256']:
        raise ValueError('input binding')
    if p['model_count'] != 8 or p['order'] != ['benchopt_pair','radix_pair','radix_pair','benchopt_pair']:
        raise ValueError('fixed consumer design')
    with np.load(root / '.cache/pvldb-full-precision-20261024' / expected['file'], allow_pickle=False) as z:
        if z['scores'].shape != (8, expected['n']):
            raise ValueError('model axes')
        observations = z['observations']
    # Independently execute the hash-bound public width utility, not a producer
    # helper or a value supplied by the timing trace.
    import importlib.util
    width_file = root / '.cache/tsbad-consumer/pkg/TSB_AD/utils/slidingWindows.py'
    spec = importlib.util.spec_from_file_location('audited_public_width', width_file)
    public_width = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(public_width)
    expected_width = int(public_width.find_length_rank(observations.reshape(-1, 1), rank=1))
    rows, workflows = [[json.loads(line) for line in (folder / (n + '.jsonl')).read_text().splitlines()]
                       for n in ('profiles', 'workflows')]
    result = {'status': 'PASS', 'auditor_sha256': digest(__file__),
        'shared_auditor_sha256': digest(Path(__file__).with_name('audit_pvldb20261024.py')),
        'audit_kind': 'trace and paired-output audit; seven non-VUS metrics are not independently reimplemented',
        'protocol_sha256': digest(folder / 'protocol.json'),
        'profiles_sha256': digest(folder / 'profiles.jsonl'), 'workflows_sha256': digest(folder / 'workflows.jsonl'),
        **reconstruct(p, rows, workflows, expected_width)}
    with Path(output).open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.root, args.output)
