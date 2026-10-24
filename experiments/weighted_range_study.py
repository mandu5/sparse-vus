"""Prospectively frozen weighted range study; input generation is separate.

The complete curve, not just its maximum, is checked and saved. A failed case
halts the study without removing the case or relabelling it as a success.
"""
import os
for _key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
             'NUMBA_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_key] = '1'
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import itertools
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/pvldb-research-20261024/strengthening'
SOURCES = ('src/sparse_vus/weighted_range.py', 'src/sparse_vus/range_sweep.py',
           'experiments/weighted_range_study.py', 'experiments/audit_weighted_range_study.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def input_path(case):
    return ROOT/case.get('npz_relative_path',case['npz_path'])


def write(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write('\n')


def freeze(args):
    inputs = read(args.inputs)
    cases = inputs['cases']
    assert len(cases) == 26
    assert {f: sum(c['family'] == f for c in cases) for f in ('WSD', 'Stock', 'MSL')} == {'WSD':12, 'Stock':12, 'MSL':2}
    for c in cases:
        assert sha(input_path(c)) == c['npz_sha256']
        with np.load(input_path(c), allow_pickle=False) as z:
            assert z['scores'].shape == (2, c['n']) and z['labels'].shape == (c['n'],)
            assert np.isfinite(z['scores']).all()
    args.output.mkdir(parents=True, exist_ok=False)
    write(args.output/'protocol.json', {
        'status':'FROZEN_BEFORE_WEIGHTED_METRIC_TIMINGS',
        'utc':datetime.now(timezone.utc).isoformat(),
        'sources':{s:sha(ROOT/s) for s in SOURCES},
        'inputs_path':str(args.inputs.resolve().relative_to(ROOT)),
        'inputs_sha256':sha(args.inputs),
        'model_order':['FFT','COPOD'],
        'cases':cases,
        'biases':['flat','front','back','middle'],
        'cardinalities':['one','reciprocal','improved'],
        'alpha':.2,
        'precision_weighting':'unweighted average over all predicted windows',
        'queries':{
            'grid100':'np.linspace(min(score),max(score),100), strict score > threshold',
            'distinct':'np.unique(score), strict >, all observed thresholds; excludes below-min state'},
        'orders':[list(p) for p in itertools.permutations(['raster','sweep','bucket'])],
        'timing':'Serial one thread. Each measurement includes both detector profiles, validation, interval/prefix construction, queries, sorting/bucketing, metric computation and maximum selection. Excludes compilation, training and file IO. All 12 bias/cardinality contracts and both query contracts are retained.',
        'parity_atol':1e-10,
        'winner_atol':1e-10,
        'bootstrap_seed':20261024,
        'bootstrap_resamples':10000,
        'uncertainty':'Point estimate: median method time per case/semantic/query, geometric ratio over fixed cases. Primary approximate paired-order resampling: resample six paired trial indices within each case, same indices for both methods and all12 semantics, recompute method medians and geometric ratio. Conditional on this panel/host; balanced orders are not independent workloads. Separately report case-log-ratio resampling as recording-reweighting sensitivity, not fixed-workload timing uncertainty or population coverage. For each prespecified comparison simultaneous95 adjustment over3 collections x12 semantics (Bonferroni36); aggregate all12 semantics equally per case with adjustment over3. MSL has2 recordings and cannot support population inference.',
        'comparisons':[['grid100','raster','bucket'],['grid100','sweep','bucket'],['distinct','raster','sweep']],
        'hypothesis':'The maintained local statistics apply to four published positional biases and three local cardinality rules, across separately selected real recordings and unchanged public FFT/COPOD APIs. Generality and costs are measured, not assumed.',
        'failure_policy':'No replacement/exclusion. Any input/source mismatch, nonfinite curve or complete-curve error>1e-10 halts, preserves partial outputs and requires explicit new protocol/version if code changes.',
        'data_note':'No exact/normalized array duplicate of prior panels found. Shared physical sources may remain. No raw public data are redistributed because license terms are unverified.'})


def evaluate(method, y, scores, query, bias, card):
    from sparse_vus.weighted_range import weighted_range_metrics
    curves, values = [], []
    for x in scores:
        thresholds = np.linspace(x.min(), x.max(), 100) if query == 'grid100' else np.unique(x)
        c = weighted_range_metrics(method, y, x, thresholds, alpha=.2,
            precision_bias=bias, recall_bias=bias, cardinality=card)
        curves.append(c)
        values.append(float(np.max(c[:,2])))
    return curves, values


def curve_sha(curves):
    h=hashlib.sha256()
    for a in curves:
        h.update(np.ascontiguousarray(a, dtype=np.float64).tobytes())
    return h.hexdigest()


def run(args):
    sys.path.insert(0, str(ROOT/'src'))
    p=read(args.output/'protocol.json')
    for path,h in p['sources'].items():
        if sha(ROOT/path)!=h: raise ValueError('source identity '+path)
    if sha(ROOT/p['inputs_path'])!=p['inputs_sha256']:raise ValueError('inputs identity')
    for c in p['cases']:
        if sha(input_path(c))!=c['npz_sha256']:raise ValueError('array identity '+c['id'])
    write(args.output/'run-start.json', {
        'utc':datetime.now(timezone.utc).isoformat(), 'platform':platform.platform(),
        'python':sys.version, 'processor':platform.processor(),
        'packages':{k:importlib.metadata.version(k) for k in ('numpy','numba','pandas','scipy','scikit-learn')},
        'protocol_sha256':sha(args.output/'protocol.json')})
    y=np.array([0,1,1,0,1,0]);s=np.array([[.1,.3,.2,.8,.7,.4],[.2,.4,.4,.8,.3,.1]])
    for method,bias,card in itertools.product(p['orders'][0],p['biases'],p['cardinalities']):
        evaluate(method,y,s,'grid100',bias,card)
    (args.output/'curves').mkdir(exist_ok=False)
    with (args.output/'records.jsonl').open('x') as f:
        for ci,c in enumerate(p['cases']):
            with np.load(input_path(c),allow_pickle=False) as z:
                y,scores=z['labels'],z['scores']
            for query in p['queries']:
                saved={m:{} for m in p['orders'][0]}
                records=[]
                for bias,card in itertools.product(p['biases'],p['cardinalities']):
                    reference=None; canonical={}
                    for trial,order in enumerate(p['orders']):
                        for method in order:
                            start=time.perf_counter_ns()
                            curves,values=evaluate(method,y,scores,query,bias,card)
                            seconds=(time.perf_counter_ns()-start)*1e-9
                            if reference is None:reference=curves
                            error=max(float(np.max(np.abs(a-b))) for a,b in zip(reference,curves))
                            if any(not np.isfinite(a).all() for a in curves) or error>p['parity_atol']:
                                raise ValueError(f'curve parity {c["id"]} {query} {bias} {card} {method} {error}')
                            h=curve_sha(curves)
                            if trial==0:
                                canonical[method]=h
                                for mi,a in enumerate(curves):saved[method][f'{bias}_{card}_{mi}']=a
                            if h!=canonical[method]:raise ValueError('nonrepeatable curve bytes')
                            records.append({'id':c['id'],'family':c['family'],'n':c['n'],
                                'query':query,'bias':bias,'cardinality':card,'trial':trial,
                                'method':method,'seconds':seconds,'max_curve_error':error,
                                'query_counts':[len(a) for a in curves],'values':values,
                                'output_sha256':h,
                                'winners':np.flatnonzero(np.array(values)>=max(values)-p['winner_atol']).tolist()})
                identities={}
                for method,arrays in saved.items():
                    file=f'curves/{ci:03d}-{query}-{method}.npz'
                    np.savez_compressed(args.output/file,**arrays)
                    identities[method]=(file,sha(args.output/file))
                for r in records:
                    r['curve_file'],r['curve_file_sha256']=identities[r['method']]
                    f.write(json.dumps(r,allow_nan=False)+'\n')
                f.flush()
            print(ci+1,c['id'],'complete',flush=True)
    write(args.output/'complete.json',{'status':'COMPLETE',
        'utc':datetime.now(timezone.utc).isoformat(),
        'protocol_sha256':sha(args.output/'protocol.json'),
        'records_sha256':sha(args.output/'records.jsonl')})


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['freeze','run'])
    parser.add_argument('--output',type=Path,default=BASE/'weighted-mac-v2')
    parser.add_argument('--inputs',type=Path,default=BASE/'workload-generation.json')
    args=parser.parse_args()
    globals()[args.command](args)
