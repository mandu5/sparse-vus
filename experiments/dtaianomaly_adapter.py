"""Run actual dtaianomaly metric methods without its detector dependencies.

The AST loader removes only the package base class, metadata declarations and
unrelated metric classes. All RangeAucMetric function bodies and the decorated
Numba kernel are executed unchanged from the hash-pinned upstream source.
Both metrics are obtained from one shared curve calculation, not two calls.
"""
from __future__ import annotations

import ast
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
import warnings

import numba as nb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REVISION = '557b435790bebc57307d8e7f22047273ac923f36'
SOURCE_HASH = '728045cd8ddf0caa6aab10a9ab66f5f876ee77e5d0ae80dfbce5029eab9ed5b7'
LICENSE_HASH = 'ac80681ee5240fb2b22fa282733dd0576fc4eaf28c66bcf50b21798b37fa2ce6'
SOURCE_URL = (f'https://raw.githubusercontent.com/ML-KULeuven/dtaianomaly/{REVISION}/'
              'dtaianomaly/evaluation/_volume_under_surface_metrics.py')


def fetch_reference():
    cache = ROOT / '.cache/dtaianomaly'
    cache.mkdir(parents=True, exist_ok=True)
    entries = [('_volume_under_surface_metrics.py', SOURCE_URL, SOURCE_HASH),
               ('LICENSE', f'https://raw.githubusercontent.com/ML-KULeuven/dtaianomaly/{REVISION}/LICENSE', LICENSE_HASH)]
    for name, url, expected in entries:
        path = cache / name
        if not path.exists():
            subprocess.run(['curl', '-fsSL', '--retry', '2', '--max-time', '60', url, '-o', str(path)], check=True)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'dtaianomaly {name} hash mismatch')
    receipt = {'repository': 'https://github.com/ML-KULeuven/dtaianomaly',
               'revision': REVISION, 'upstream_commit_date': '2026-10-13T14:42:21Z',
               'source_url': SOURCE_URL, 'source_sha256': SOURCE_HASH,
               'license': 'MIT', 'license_sha256': LICENSE_HASH,
               'adapter': 'Unchanged method and compiled kernel AST; metric-only dependency isolation.',
               'thread_control': 'Set NUMBA_NUM_THREADS=1 before import for single-thread comparisons.',
               'timing_contract': 'Includes threshold sort, label expansion, and all buffer curves; both ROC and PR returned from one curve call.',
               'jit': 'Upstream fastmath=True, parallel=True preserved; compile warm-up excluded from warm timing.'}
    (ROOT / 'artifacts').mkdir(exist_ok=True)
    (ROOT / 'artifacts/dtaianomaly_source.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return cache / '_volume_under_surface_metrics.py'


@lru_cache(maxsize=1)
def _load_class():
    path = ROOT / '.cache/dtaianomaly/_volume_under_surface_metrics.py'
    if not path.exists():
        raise FileNotFoundError('Run python experiments/dtaianomaly_adapter.py --fetch first.')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError('dtaianomaly metric source hash mismatch')
    parsed = ast.parse(raw, filename=str(path))
    chosen = []
    for node in parsed.body:
        if isinstance(node, ast.FunctionDef) and node.name == '_range_curves':
            chosen.append(node)
        if isinstance(node, ast.ClassDef) and node.name == 'RangeAucMetric':
            # The omitted base implements the public framework's generic
            # compute/input-validation interface, not the metric calculation.
            node.bases, node.keywords = [], []
            node.body = [x for x in node.body if isinstance(x, ast.FunctionDef)]
            chosen.append(node)
    if len(chosen) != 2:
        raise ValueError('Pinned source AST structure changed')
    namespace = {'np': np, 'nb': nb, 'warnings': warnings, '_DEFAULT_MAX_SAMPLES': 250,
                 '__name__': 'pinned_dtaianomaly_vus', '__file__': str(path)}
    module = ast.fix_missing_locations(ast.Module(body=chosen, type_ignores=[]))
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace['RangeAucMetric']


def dtaianomaly_vus(y, scores, max_buffer, max_samples=250):
    """Return (ROC, PR) with the third-party metric's exact threshold grid."""
    y = np.asarray(y)
    scores = np.asarray(scores, dtype=float)
    if y.ndim != 1 or scores.ndim != 1 or y.shape != scores.shape or len(y) < 2:
        raise ValueError('equal-length one-dimensional inputs required')
    if not np.isin(y, [0, 1]).all() or not 0 < y.sum() < len(y) or not np.isfinite(scores).all():
        raise ValueError('finite scores and binary labels with both classes required')
    if not isinstance(max_buffer, (int, np.integer)) or max_buffer < 0:
        raise ValueError('max_buffer must be a nonnegative integer')
    if not isinstance(max_samples, (int, np.integer)) or max_samples < 1:
        raise ValueError('max_samples must be a positive integer')
    metric = _load_class()(max_samples=int(max_samples))
    thresholds, n_pred = metric._uniform_threshold_sampling(scores)
    results = [metric._range_pr_roc_auc_support(y, scores, width, thresholds, n_pred)
               for width in range(int(max_buffer) + 1)]
    pr, roc = np.mean(results, axis=0)
    return float(roc), float(pr)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    if args.fetch:
        print(fetch_reference())
