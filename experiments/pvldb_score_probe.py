"""Archive an inspectable repeat of the diagnosed 539-SMAP host difference.

This post-review diagnostic cannot recover missing arrays from the earlier
runner. It executes the unchanged score generator and saves a new host pair.
"""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import sys
import zipfile
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
SERIES = '539_SMAP_id_9_Sensor_tr_1857_1st_4270'
ARCHIVE_SHA = '0c47020d3423723c70773736dbd800369f2b487328becbf339450d1ae5020961'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(output, archive):
    from pvldb_full_precision import generate_scores, evaluate
    from sklearn.svm import OneClassSVM
    from threadpoolctl import threadpool_info, threadpool_limits
    output.mkdir(parents=True, exist_ok=False)
    if sha(archive) != ARCHIVE_SHA:
        raise ValueError('archive identity')
    with zipfile.ZipFile(archive) as z:
        raw = z.read('TSB-AD-U/' + SERIES + '.csv')
    if hashlib.sha256(raw).hexdigest() != '102c5c69acb67557a87822cb234a39ccf28882ba00f742f4f09ff8730075765a':
        raise ValueError('raw identity')
    frame = pd.read_csv(io.BytesIO(raw))
    x, y = frame.iloc[:, 0].to_numpy(float), frame.iloc[:, -1].to_numpy(np.int8)
    scores, generation = generate_scores(x)
    windows = np.lib.stride_tricks.sliding_window_view(np.pad(x, (15, 0), mode='edge'), 16)
    indices = np.linspace(0, len(x) - 1, min(2048, len(x))).astype(np.int64)
    reference = windows[indices]
    mean, std = reference.mean(axis=0), reference.std(axis=0)
    std[std == 0] = 1.
    data = np.ascontiguousarray((windows - mean) / std)
    with threadpool_limits(limits=1):
        svm = OneClassSVM(kernel='rbf', gamma=1/16, nu=.05).fit(data[indices])
        diagnostic_score = -svm.score_samples(data)
        if not np.array_equal(diagnostic_score, scores[3]):
            raise ValueError('diagnostic refit differs from unchanged generator')
        backends = threadpool_info()
    values, winners = evaluate('released', y, scores, 30)
    np.savez_compressed(output / 'arrays.npz', observations=x, labels=y, scores=scores,
        standardized_data=data, train_indices=indices, feature_mean=mean, feature_std=std,
        svm_support_indices=svm.support_, svm_support_vectors=svm.support_vectors_,
        svm_dual_coef=svm.dual_coef_, svm_intercept=svm.intercept_, svm_n_iter=svm.n_iter_)
    config = io.StringIO()
    with contextlib.redirect_stdout(config):
        np.show_config()
    result = {'status': 'COMPLETE', 'utc': datetime.now(timezone.utc).isoformat(),
        'series': SERIES, 'platform': platform.platform(), 'machine': platform.machine(),
        'python': sys.version, 'packages': {p: importlib.metadata.version(p) for p in
            ('numpy', 'scipy', 'scikit-learn', 'numba', 'pandas', 'threadpoolctl')},
        'threadpools_with_limit_one': backends, 'numpy_config': config.getvalue(),
        'source_sha256': {file: sha(ROOT / file) for file in
            ('experiments/pvldb_score_probe.py', 'experiments/pvldb_full_precision.py', 'src/sparse_vus/radix.py')},
        'archive_sha256': ARCHIVE_SHA, 'arrays_sha256': sha(output / 'arrays.npz'),
        'scores_sha256': hashlib.sha256(scores.tobytes()).hexdigest(),
        'generation': generation, 'exact_pr_values': values.tolist(), 'exact_winners': winners,
        'svm': {'fit_status': int(svm.fit_status_), 'n_iter': np.asarray(svm.n_iter_).tolist(),
                'support_vectors': len(svm.support_), 'parameters': svm.get_params()},
        'scope': 'New diagnostic repeat, not recovery of original Linux runner arrays. No causal attribution to a particular backend from host correlation alone.'}
    (output / 'receipt.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'platform': result['platform'], 'scores_sha256': result['scores_sha256'],
                      'exact_pr_values': result['exact_pr_values'], 'exact_winners': winners}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--archive', type=Path, default=ROOT / 'cache/TSB-AD-U.zip')
    args = parser.parse_args()
    run(args.output, args.archive)
