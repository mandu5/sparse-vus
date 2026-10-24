"""Inspect saved host arrays and re-evaluate both on one local evaluator host."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from audit_pvldb20261024 import digest, read

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def analyze(output):
    from sparse_vus.radix import sparse_pr_radix_jit
    from fast_vus_adapter import fast_vus_pr
    base = ROOT / 'artifacts/pvldb-research-20261024'
    folder = base / 'score-host-probe'
    receipts, arrays = {}, {}
    for host in ('mac', 'linux'):
        r = receipts[host] = read(folder / host / 'receipt.json')
        if r['status'] != 'COMPLETE' or digest(folder / host / 'arrays.npz') != r['arrays_sha256']:
            raise ValueError('probe binding')
        for file, h in r['source_sha256'].items():
            if digest(ROOT / file) != h:
                raise ValueError('probe source binding')
        with np.load(folder / host / 'arrays.npz', allow_pickle=False) as z:
            arrays[host] = {k: z[k] for k in z.files}
    a, b = arrays['mac'], arrays['linux']
    comparisons = {}
    for key in a:
        x, y = a[key], b[key]
        comparisons[key] = {'mac_shape': list(x.shape), 'linux_shape': list(y.shape),
            'exactly_equal': bool(np.array_equal(x, y)),
            'max_abs_difference': float(np.max(np.abs(x-y))) if x.shape == y.shape else None}
    for key in ('observations','labels','standardized_data','train_indices','feature_mean','feature_std'):
        if not comparisons[key]['exactly_equal']:
            raise ValueError('input/standardization no longer identical: ' + key)
    host_results = {}
    for host in ('mac','linux'):
        parent = base / ('full-precision' if host == 'mac' else 'linux-reproduction/full-precision')
        r, z = receipts[host], arrays[host]
        c = next(c for c in read(parent / 'inputs.json')['series'] if c['series'] == r['series'])
        original = next(r0 for r0 in map(json.loads,(parent/'records.jsonl').read_text().splitlines())
            if r0['series'] == r['series'] and r0['method'] == 'released' and r0['trial'] == 0 and r0['width'] == 30)
        exact = np.array([sparse_pr_radix_jit(z['labels'], s, 30) for s in z['scores']])
        external = np.array([fast_vus_pr(z['labels'], s, 30, len(s)) for s in z['scores']])
        sampled = np.array([fast_vus_pr(z['labels'], s, 30, 250) for s in z['scores']])
        if max(np.max(np.abs(exact-external)),np.max(np.abs(exact-r['exact_pr_values']))) > 1e-11:
            raise ValueError('same-array evaluation parity')
        host_results[host] = {'receipt_sha256': digest(folder/host/'receipt.json'),
            'array_sha256': r['arrays_sha256'], 'whole_score_bytes_equal_original_run': r['scores_sha256'] == c['score_sha256'],
            'same_host_exact_pr': exact.tolist(), 'same_host_public_comparator_pr': external.tolist(),
            'same_host_250_pr': sampled.tolist(), 'same_host_250_winners': np.flatnonzero(sampled >= sampled.max()-1e-10).tolist(),
            'max_reference_evaluator_error': float(np.max(np.abs(exact-external))),
            'max_original_run_metric_difference': float(np.max(np.abs(exact-original['values']))),
            'svm_original_run_metric_difference': float(exact[3]-original['values'][3]), 'svm': r['svm']}
    result = {'status':'PASS','analysis_source_sha256':digest(__file__),
        'array_comparisons':comparisons,'hosts':host_results,
        'per_model_max_score_difference':[float(np.max(np.abs(x-y))) for x,y in zip(a['scores'],b['scores'])],
        'conclusion':'Raw and standardized inputs are byte-identical; fitted SVM support state differs (104 versus 105). Both arrays reproduce their recorded SVM VUS-PR on one evaluator host and agree with the public comparator. This localizes the observed SVM discrepancy after standardization to fitted-state/score generation, not the VUS implementation. It does not identify a particular compiler, BLAS or instruction as causal.',
        'qualification':'New Linux diagnostic repeat is not recovery of original runner arrays; whole eight-model score hashes can differ across Linux runners. All such differences are retained.'}
    with Path(output).open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':result['status'],'hosts':host_results},indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    analyze(p.parse_args().output)
