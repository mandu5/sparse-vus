"""Pinned public nine-metric consumer with an instrumented exact VUS pair.

The upstream get_metrics body is unchanged; only its generate_curve global is
replaced at the scalar consumer boundary. Seven non-VUS outputs/functions remain
upstream. VUS-ROC/PR are both supplied. This is a
stored-profile re-evaluation workload, not a replay of detector training or the
whole upstream HP-tuning script. Output traces separate total and VUS time.
"""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import time
from urllib.request import urlopen
import numpy as np
import pandas as pd
from audit_pvldb20261024 import digest, read

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/pvldb-research-20261024'
OUT = BASE / 'public-consumer'
PRIMARY = BASE / 'full-precision'
CACHE = ROOT / '.cache/pvldb-full-precision-20261024'
PKG = ROOT / '.cache/tsbad-consumer/pkg'
REVISION = '303dffbfc11612995b17b06633f8c9d0ea0e38e5'
FILES = ['TSB_AD/__init__.py', 'TSB_AD/evaluation/__init__.py', 'TSB_AD/evaluation/metrics.py',
         'TSB_AD/evaluation/basic_metrics.py', 'TSB_AD/utils/__init__.py', 'TSB_AD/utils/slidingWindows.py',
         'LICENSE', 'benchmark_exp/HP_Tuning_U.py']
FILES += ['TSB_AD/evaluation/affiliation/' + f + '.py' for f in
          ('__init__', '_affiliation_zone', '_integral_interval', '_single_ground_truth_event', 'generics', 'metrics')]

# Hashes independently re-downloaded from the exact public revision before freeze.
FILE_SHA256 = {'TSB_AD/__init__.py': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'TSB_AD/evaluation/__init__.py': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b', 'TSB_AD/evaluation/metrics.py': '13957d15d3ebb2b743a4bebfa3a68af31e82a58ecc568557b4081ad90e38094d', 'TSB_AD/evaluation/basic_metrics.py': '1fcddedf5ada1d5221f39ee568c7fddb9e7181bd7e1c19636c2cbecf40c97707', 'TSB_AD/utils/__init__.py': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'TSB_AD/utils/slidingWindows.py': '0ba65735c6572cd80e586409d4f653253d847e08fbae8e1da6e474e142e74af6', 'LICENSE': 'c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4', 'benchmark_exp/HP_Tuning_U.py': '3c809dd6dbf868da9698112487909d128947f25c2af9cfb3f065b588f478bb9c', 'TSB_AD/evaluation/affiliation/__init__.py': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b', 'TSB_AD/evaluation/affiliation/_affiliation_zone.py': '3b289bf11cebe614afabe353c873de90ba9debf8831aef8f73532870dce01ba2', 'TSB_AD/evaluation/affiliation/_integral_interval.py': '8177e69eccb0ae4ea76b2f54f6799ae61758b5a103603fae3d1a3a8d331e7cda', 'TSB_AD/evaluation/affiliation/_single_ground_truth_event.py': 'a04b5daa0fb0ef68893807c7ab5d4353b43f0d5231ae06ef0006b2e6cf939165', 'TSB_AD/evaluation/affiliation/generics.py': '16743b204d24feb8ba9deaabceb7b0cf900520136e8a3b77e499448fcaafbfc9', 'TSB_AD/evaluation/affiliation/metrics.py': '9fe83cd2cb1cd4b1b3c7869971e94a18d5ea71b4103f88e347de70c8330cc060'}


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def fetch():
    expected = read(OUT / 'protocol.json')['source_sha256'] if (OUT / 'protocol.json').exists() else {}
    for name in FILES:
        path = PKG / name
        if not path.exists():
            raw = urlopen(f'https://raw.githubusercontent.com/TheDatumOrg/TSB-AD/{REVISION}/{name}', timeout=60).read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        relative = str(path.relative_to(ROOT))
        if digest(path) != FILE_SHA256[name]:
            raise ValueError('pinned upstream identity: ' + name)
        if expected and digest(path) != expected[relative]:
            raise ValueError('public source changed: ' + name)


def evaluate_profile(method, labels, scores, width):
    sys.path[:0] = [str(ROOT / 'src'), str(PKG)]
    from TSB_AD.evaluation import metrics
    from benchopt_vus_adapter import benchopt_vus
    from sparse_vus.radix import sparse_vus_radix_jit
    if method not in ('benchopt_pair', 'radix_pair'):
        raise ValueError('unknown exact backend')
    elapsed = []
    def curve(y, x, w, version='opt', thre=250):
        start = time.perf_counter_ns()
        pair = benchopt_vus(y, x, w, len(x)) if method == 'benchopt_pair' else sparse_vus_radix_jit(y, x, w)
        elapsed.append((time.perf_counter_ns() - start) * 1e-9)
        return (None,) * 6 + tuple(pair)
    previous = metrics.generate_curve
    try:
        metrics.generate_curve = curve
        result = metrics.get_metrics(scores, labels, slidingWindow=width, thre=len(scores))
    finally:
        metrics.generate_curve = previous
    if len(elapsed) != 1 or len(result) != 9 or not np.isfinite(list(result.values())).all():
        raise ValueError('consumer output/call contract')
    return {k: float(v) for k, v in result.items()}, elapsed[0]


def freeze():
    fetch()
    cases = read(PRIMARY / 'inputs.json')['series']
    # Input-length choice, fixed without any nine-metric consumer outcomes.
    case = sorted(cases, key=lambda c: (-c['n'], c['series']))[0]
    sources = dict(read(BASE / 'supplement/protocol.json')['source_sha256'])
    sources['experiments/pvldb_consumer.py'] = digest(__file__)
    for name in FILES:
        path = PKG / name
        sources[str(path.relative_to(ROOT))] = digest(path)
    OUT.mkdir(exist_ok=False)
    write(OUT / 'protocol.json', {
        'status': 'FROZEN_AFTER_REVIEW_AND_COMPILED_CONTROL_BEFORE_CONSUMER_OUTCOMES',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'source_sha256': sources,
        'primary_protocol_sha256': digest(PRIMARY / 'protocol.json'), 'inputs_sha256': digest(PRIMARY / 'inputs.json'),
        'case': case, 'model_count': 8, 'order': ['benchopt_pair', 'radix_pair', 'radix_pair', 'benchopt_pair'],
        'public_repository': 'https://github.com/TheDatumOrg/TSB-AD', 'public_revision': REVISION,
        'consumer': 'Unchanged get_metrics with an injected exact ROC+PR scalar pair; all nine metric outputs including upstream oracle-threshold loops. Unchanged find_length_rank(rank=1) selects width from observations.',
        'workload': 'Largest n in the fixed 73-case primary panel, lexicographic tie break. Eight stored float64 profiles, no fitting. Four complete read-to-CSV-close passes in ABBA order, two per method.',
        'hypothesis': 'Measure actual evaluator share and end-to-end benefit inside a public multi-metric consumer; retain Amdahl-limited or negative outcomes.',
        'parity_atol': 1e-11, 'timing': 'Serial one numerical thread, warm imports/JIT. Workflow includes NPZ reads, width selection, all nine metrics and CSV close. No cold-disk/fsync/training/production-service claim.',
        'uncertainty': 'Two fixed-input repetitions per method are descriptive timing evidence, not population or deployment uncertainty.',
        'failure_policy': 'No replacement; invalid/nonfinite public output, different metric keys or parity above tolerance halts and preserves partial trace.',
    })


def run():
    sys.path[:0] = [str(ROOT / 'src'), str(PKG)]
    from TSB_AD.utils.slidingWindows import find_length_rank
    p = read(OUT / 'protocol.json')
    for path, h in p['source_sha256'].items():
        if digest(ROOT / path) != h:
            raise ValueError('source binding: ' + path)
    for key, name in [('primary_protocol_sha256', 'protocol.json'), ('inputs_sha256', 'inputs.json')]:
        if digest(PRIMARY / name) != p[key]:
            raise ValueError('parent binding')
    if digest(CACHE / p['case']['file']) != p['case']['npz_sha256']:
        raise ValueError('input binding')
    write(OUT / 'run-start.json', {'utc': datetime.now(timezone.utc).isoformat(), 'platform': platform.platform(),
        'protocol_sha256': digest(OUT / 'protocol.json'), 'packages': {x: importlib.metadata.version(x) for x in ('numpy','scipy','scikit-learn','statsmodels','numba','pandas')}})
    y = np.zeros(32, np.int8)
    y[7:11], y[21:24] = 1, 1
    x = np.random.default_rng(13).normal(size=32)
    for method in ('benchopt_pair', 'radix_pair'):
        evaluate_profile(method, y, x, 8)
    reference = None
    with (OUT / 'profiles.jsonl').open('x') as trace, (OUT / 'workflows.jsonl').open('x') as wf:
        for trial, method in enumerate(p['order']):
            start = time.perf_counter_ns()
            with np.load(CACHE / p['case']['file'], allow_pickle=False) as z:
                observations, labels, scores = z['observations'], z['labels'], z['scores']
            width = int(find_length_rank(observations.reshape(-1, 1), rank=1))
            rows, vus_total = [], 0.
            for model, score in enumerate(scores):
                t = time.perf_counter_ns()
                metrics, vus_seconds = evaluate_profile(method, labels, score, width)
                profile_seconds = (time.perf_counter_ns() - t) * 1e-9
                row = {'trial': trial, 'method': method, 'model': model, 'width': width,
                       'seconds': profile_seconds, 'vus_seconds': vus_seconds, 'metrics': metrics}
                trace.write(json.dumps(row, allow_nan=False) + '\n')
                trace.flush()
                rows.append(metrics)
                vus_total += vus_seconds
            pd.DataFrame(rows).to_csv(CACHE / 'last-public-consumer-output.csv', index=False)
            seconds = (time.perf_counter_ns() - start) * 1e-9
            if reference is None:
                reference = rows
            for expected, actual in zip(reference, rows):
                if expected.keys() != actual.keys() or max(abs(actual[k]-expected[k]) for k in expected) > p['parity_atol']:
                    raise ValueError('nine-metric output parity')
            record = {'trial': trial, 'method': method, 'series': p['case']['series'], 'width': width,
                      'seconds': seconds, 'vus_seconds': vus_total, 'outputs': rows}
            wf.write(json.dumps(record, allow_nan=False) + '\n')
            wf.flush()
            print(trial, method, seconds, 'VUS', vus_total, flush=True)
    write(OUT / 'complete.json', {'status': 'COMPLETE', 'utc': datetime.now(timezone.utc).isoformat(),
        'protocol_sha256': digest(OUT / 'protocol.json'), 'profiles_sha256': digest(OUT / 'profiles.jsonl'),
        'workflows_sha256': digest(OUT / 'workflows.jsonl')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['fetch','freeze','run'])
    globals()[parser.parse_args().command]()
