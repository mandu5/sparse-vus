"""Frozen three-method, two-contract study of exact range metrics."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/pvldb-research-20261024'
PRIMARY = BASE / 'full-precision'
CACHE = ROOT / '.cache/pvldb-full-precision-20261024'
OUT = BASE / 'range-sweep/main-study'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def freeze():
    methods=['prefix','raster','sweep','bucket']
    orders=[methods[i:]+methods[:i] for i in range(4)]
    orders += [list(reversed(o)) for o in orders.copy()]
    OUT.mkdir(exist_ok=False)
    write(OUT/'protocol.json', {
        'status':'FROZEN_BEFORE_PRIMARY_RANGE_SWEEP_OUTCOMES',
        'utc':datetime.now(timezone.utc).isoformat(),
        'source_sha256':{s:digest(ROOT/s) for s in ('src/sparse_vus/range_sweep.py','experiments/range_sweep_study.py')},
        'inputs_sha256':digest(PRIMARY/'inputs.json'),
        'primary_protocol_sha256':digest(PRIMARY/'protocol.json'),
        'cohort':'All 73 prior primary recordings and eight fixed fullprecision score vectors. Reused inputs, exploratory successor, not held-out generalization.',
        'contracts':{'grid100':'100 linspace(min,max) strict > thresholds, alpha=.2 flat reciprocal cardinality',
                     'distinct':'Every observed unique score as strict > threshold, alpha=.2; excludes below-min all-positive state, same threshold domain as TimeSeAD classic.'},
        'grid_orders':orders,
        'distinct_orders':[['raster','sweep'],['sweep','raster']],
        'timing':'Complete eight-profile calls including validation, interval extraction, query construction, sort, metric and max selection. Warm compilation; serial one-thread. No file IO, training or whole-nine-metric claim.',
        'parity_atol':1e-10, 'winner_tie_atol':1e-10,
        'uncertainty':'10000 seeded paired case-median log-ratio resamples; familywise95 over three collections separately per method/contract. Equal-label-block sensitivity additionally reported. Fixed-input timing, no population claim.',
        'hypothesis':'Endpoint sweep beats conventional compiled linear scans across observed distinct thresholds; grid100 can favor fused raster and those losses remain. Grid bucket control uses standard exact binary-search offline query grouping instead of score sorting. Public baselines are a separate explicit study.',
        'failure_policy':'No input exclusion or replacement; nonfinite result or complete-curve disagreement above tolerance halts and preserves raw partial records.',
    })


def evaluate(method, y, scores, contract):
    from sparse_vus.range_sweep import range_metrics
    curves, best_thresholds = [], []
    for s in scores:
        thresholds = np.linspace(s.min(),s.max(),100) if contract=='grid100' else np.unique(s)
        curve = range_metrics(method,y,s,thresholds,alpha=.2)
        curves.append(curve)
        best_thresholds.append(float(thresholds[np.argmax(curve[:,2])]))
    values = np.array([c[:,2].max() for c in curves])
    return curves, values, best_thresholds


def output_hash(curves):
    h=hashlib.sha256()
    for a in curves:
        h.update(np.ascontiguousarray(a,dtype=np.float64).tobytes())
    return h.hexdigest()


def run():
    sys.path.insert(0,str(ROOT/'src'))
    p = read(OUT/'protocol.json')
    for path,h in p['source_sha256'].items():
        if digest(ROOT/path)!=h: raise ValueError('source identity '+path)
    if digest(PRIMARY/'inputs.json')!=p['inputs_sha256'] or digest(PRIMARY/'protocol.json')!=p['primary_protocol_sha256']:
        raise ValueError('parent identity')
    cases = read(PRIMARY/'inputs.json')['series']
    for c in cases:
        if digest(CACHE/c['file'])!=c['npz_sha256']: raise ValueError('input identity')
    write(OUT/'run-start.json', {'utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),'python':sys.version,'protocol_sha256':digest(OUT/'protocol.json')})
    for m in ('prefix','raster','sweep','bucket'):
        evaluate(m,np.array([0,1,1,0,1,0]),np.array([[.1,.3,.2,.8,.7,.4]]),'grid100')
    (OUT/'curves').mkdir(exist_ok=False)
    with (OUT/'records.jsonl').open('x') as f:
        for ci,c in enumerate(cases):
            with np.load(CACHE/c['file'],allow_pickle=False) as z:
                y,scores=z['labels'],z['scores']
            label_hash=hashlib.sha256(np.ascontiguousarray(y,dtype=np.int8).tobytes()).hexdigest()
            for contract in ('grid100','distinct'):
                reference=None
                canonical={}
                orders=p['grid_orders' if contract=='grid100' else 'distinct_orders']
                for trial,order in enumerate(orders):
                    for method in order:
                        start=time.perf_counter_ns()
                        curves,values,thresholds=evaluate(method,y,scores,contract)
                        seconds=(time.perf_counter_ns()-start)*1e-9
                        if reference is None: reference=curves
                        error=max(float(np.max(np.abs(a-b))) for a,b in zip(reference,curves))
                        if not np.isfinite(values).all() or error>p['parity_atol']: raise ValueError('curve parity '+c['series'])
                        curve_hash=output_hash(curves)
                        if trial==0:
                            file=f'curves/{ci:03d}-{contract}-{method}.npz'
                            np.savez_compressed(OUT/file,**{f'model{i}':a for i,a in enumerate(curves)})
                            canonical[method]=(file,digest(OUT/file),curve_hash)
                        file,file_hash,first_hash=canonical[method]
                        if curve_hash!=first_hash: raise ValueError('nonrepeatable curve bytes')
                        record={'series':c['series'],'family':c['family'],'label_sha256':label_hash,'n':len(y),
                                'contract':contract,'method':method,'trial':trial,'seconds':seconds,'values':values.tolist(),
                                'best_thresholds':thresholds,'query_counts':[len(a) for a in curves],'max_curve_error':error,
                                'curve_file':file,'curve_file_sha256':file_hash,'output_sha256':curve_hash,
                                'winners':np.flatnonzero(values>=values.max()-p['winner_tie_atol']).tolist()}
                        f.write(json.dumps(record,allow_nan=False)+'\n');f.flush()
            print(ci+1,c['series'],'complete',flush=True)
    write(OUT/'complete.json',{'status':'COMPLETE','utc':datetime.now(timezone.utc).isoformat(),
                             'protocol_sha256':digest(OUT/'protocol.json'),'records_sha256':digest(OUT/'records.jsonl')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','run'])
    globals()[parser.parse_args().command]()
