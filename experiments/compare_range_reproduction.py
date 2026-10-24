"""Post hoc cross-host input/result accounting; never recompute metric timings."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path('artifacts/pvldb-research-20261024')
CACHE = Path('.cache/pvldb-full-precision-20261024')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compare(replica):
    old, new = ROOT/EVIDENCE, replica/EVIDENCE
    a, b = read(old/'full-precision/inputs.json'), read(new/'full-precision/inputs.json')
    models = read(old/'full-precision/protocol.json')['models']
    require(models == read(new/'full-precision/protocol.json')['models'], 'model order mismatch')
    require([c['series'] for c in a['series']] == [c['series'] for c in b['series']], 'case order mismatch')
    reports = [read(p/'range-sweep/main-study/independent-report.json') for p in (old, new)]
    for base, inputs, report in zip((old, new), (a, b), reports):
        main = base/'range-sweep/main-study'
        protocol = read(main/'protocol.json')
        require(report['status'] == 'PASS', 'audit not passing')
        require(report['protocol_sha256'] == sha(main/'protocol.json'), 'audit protocol binding')
        require(report['records_sha256'] == sha(main/'records.jsonl'), 'audit record binding')
        require(protocol['inputs_sha256'] == sha(base/'full-precision/inputs.json'), 'range input binding')
        require(protocol['primary_protocol_sha256'] == sha(base/'full-precision/protocol.json'), 'range parent binding')
        require(inputs['protocol_sha256'] == sha(base/'full-precision/protocol.json'), 'primary input binding')
        names = [c['series'] for c in inputs['series']]
        require(len(set(names)) == len(names), 'duplicate input series')
        details = [d['series'] for f in report['grid_to_distinct_selection'] for d in f['details']]
        require(sorted(details) == sorted(names), 'selection coverage mismatch')
    rows = []
    for x, y in zip(a['series'], b['series']):
        require(x['family'] == y['family'] and x['n'] == y['n'], 'case metadata mismatch')
        require(x['observation_label_identity'] == y['observation_label_identity'], 'raw identity mismatch')
        pa, pb = ROOT/CACHE/x['file'], replica/CACHE/y['file']
        require(sha(pa) == x['npz_sha256'] and sha(pb) == y['npz_sha256'], 'NPZ binding mismatch')
        with np.load(pa, allow_pickle=False) as za, np.load(pb, allow_pickle=False) as zb:
            for z, case in ((za, x), (zb, y)):
                identity = hashlib.sha256(z['observations'].astype(np.float64).tobytes()+z['labels'].astype(np.int8).tobytes()).hexdigest()
                require(identity == case['observation_label_identity'], 'actual raw-array identity mismatch')
                require(hashlib.sha256(z['scores'].tobytes()).hexdigest() == case['score_sha256'], 'actual score digest mismatch')
                require(z['scores'].dtype == np.float64 and np.isfinite(z['scores']).all(), 'score domain mismatch')
            require(np.array_equal(za['labels'], zb['labels']) and np.array_equal(za['observations'], zb['observations']), 'raw arrays differ')
            require(za['scores'].shape == zb['scores'].shape == (len(models), x['n']), 'score shape mismatch')
            exact_scores_equal = bool(np.array_equal(za['scores'], zb['scores']))
            differences = []
            for i, model in enumerate(models):
                aa, bb = za['scores'][i], zb['scores'][i]
                differences.append({'model': model, 'exact_array_equal': bool(np.array_equal(aa, bb)),
                                    'max_abs_difference': float(np.max(np.abs(aa-bb))),
                                    'different_positions': int(np.count_nonzero(aa != bb)),
                                    'distinct_counts': [len(np.unique(aa)), len(np.unique(bb))]})
        details = []
        for r in reports:
            details.append(next(d for f in r['grid_to_distinct_selection'] for d in f['details']
                                if d['series'] == x['series']))
        rows.append({'series': x['series'], 'family': x['family'], 'score_sha256': [x['score_sha256'], y['score_sha256']],
                     'exact_scores_equal': exact_scores_equal,
                     'scores': differences, 'original_selection': details[0], 'replica_selection': details[1]})
    return {'scope': 'Post hoc comparison of generated scores and already audited selection summaries; no timing rerun or causal attribution of platform differences.',
            'original_inputs_sha256': sha(old/'full-precision/inputs.json'),
            'replica_inputs_sha256': sha(new/'full-precision/inputs.json'),
            'source_sha256': sha(Path(__file__)),
            'original_audit_sha256': sha(old/'range-sweep/main-study/independent-report.json'),
            'replica_audit_sha256': sha(new/'range-sweep/main-study/independent-report.json'),
            'series': len(rows), 'all_observation_label_identities_equal': True,
            'exact_score_arrays_equal': sum(x['exact_scores_equal'] for x in rows),
            'profile_array_equal_counts': {m: sum(x['scores'][i]['exact_array_equal'] for x in rows) for i, m in enumerate(models)},
            'grid_winner_change_indicator_disagreements': sum(x['original_selection']['winner_set_changes'] != x['replica_selection']['winner_set_changes'] for x in rows),
            'nonoverlap_indicator_disagreements': sum(x['original_selection']['nonoverlap'] != x['replica_selection']['nonoverlap'] for x in rows),
            'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--replica', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.replica.resolve())
    with args.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
