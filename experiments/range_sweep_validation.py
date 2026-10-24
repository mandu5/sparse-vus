"""Public binary-prediction checks and long-input numerical stress, no timing claim."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import numpy as np
from range_sweep_study import ROOT,BASE,PRIMARY,CACHE,digest,read,write

OUT=BASE/'range-sweep/validation'


def freeze():
    OUT.mkdir(exist_ok=False)
    from pvldb_consumer import FILE_SHA256,PKG
    write(OUT/'protocol.json',{'status':'FROZEN_BEFORE_VALIDATION','utc':datetime.now(timezone.utc).isoformat(),
      'source_sha256':{**{s:digest(ROOT/s) for s in ('src/sparse_vus/range_sweep.py','experiments/range_sweep_validation.py','experiments/range_sweep_study.py')},
                       str((PKG/'TSB_AD/evaluation/basic_metrics.py').relative_to(ROOT)):FILE_SHA256['TSB_AD/evaluation/basic_metrics.py']},
      'records_sha256':digest(BASE/'range-sweep/main-study/records.jsonl'),'inputs_sha256':digest(PRIMARY/'inputs.json'),
      'scope':'All 584 profiles at their grid and observed-distinct maximizing thresholds: unchanged TSB public binary-prediction RF1. This validates values at chosen cuts, not independent maximality over every cut. Separate long-input numerical stress has no runtime claim.',
      'stress':[{'n':1000000,'geometry':'alternating','scores':'normal'},
                {'n':1000000,'geometry':'single','scores':'normal'},
                {'n':1000000,'geometry':'dense','scores':'ties'}],
      'thresholds':257,'seed':20261024,'alpha':.2,'atol':1e-9})


def run():
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'.cache/tsbad-consumer/pkg')]
    from TSB_AD.evaluation.basic_metrics import basic_metricor
    from sparse_vus.range_sweep import range_metrics
    p=read(OUT/'protocol.json')
    for s,h in p['source_sha256'].items():assert digest(ROOT/s)==h
    assert digest(BASE/'range-sweep/main-study/records.jsonl')==p['records_sha256']
    assert digest(PRIMARY/'inputs.json')==p['inputs_sha256']
    records=[json.loads(l) for l in (BASE/'range-sweep/main-study/records.jsonl').read_text().splitlines()]
    selected={(r['series'],r['contract']):r for r in records if r['method']=='sweep' and r['trial']==0}
    checks=[];g=basic_metricor()
    for case in read(PRIMARY/'inputs.json')['series']:
        assert digest(CACHE/case['file'])==case['npz_sha256']
        with np.load(CACHE/case['file'],allow_pickle=False) as z:y,scores=z['labels'],z['scores']
        for contract in ('grid100','distinct'):
            r=selected[(case['series'],contract)]
            for i,s in enumerate(scores):
                value=float(g.metric_RF1(y,s,preds=(s>r['best_thresholds'][i]).astype(int)))
                error=abs(value-r['values'][i]);assert error<=p['atol']
                checks.append({'series':case['series'],'contract':contract,'model':i,'public_value':value,'candidate_value':r['values'][i],'absolute_error':error})
    stress=[];rng=np.random.default_rng(p['seed'])
    for c in p['stress']:
        n=c['n'];y=np.zeros(n,np.int8)
        if c['geometry']=='alternating':y[::2]=1
        elif c['geometry']=='single':y[n//4:3*n//4]=1
        else:y[:]=1;y[::101]=0
        x=rng.normal(size=n) if c['scores']=='normal' else rng.integers(0,16,n).astype(float)
        t=np.r_[-np.inf,np.linspace(x.min(),x.max(),p['thresholds']-2),np.inf]
        reference=range_metrics('raster',y,x,t)
        for method in ('prefix','sweep','bucket'):
            actual=range_metrics(method,y,x,t)
            error=float(np.max(np.abs(actual-reference)));assert error<=p['atol']
            assert np.isfinite(actual).all() and actual.min()>=-p['atol'] and actual.max()<=1+p['atol']
            stress.append({**c,'method':method,'absolute_error':error,'min':float(actual.min()),'max':float(actual.max()),
                           'argmax_index_equal':bool(np.argmax(actual[:,2])==np.argmax(reference[:,2]))})
    write(OUT/'report.json',{'status':'PASS','utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':digest(OUT/'protocol.json'),
                           'public_check_count':len(checks),'max_public_value_error':max(r['absolute_error'] for r in checks),
                           'public_checks':checks,'stress':stress,'max_stress_error':max(r['absolute_error'] for r in stress)})
    print('PASS',len(checks),max(r['absolute_error'] for r in checks),max(r['absolute_error'] for r in stress),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','run']);globals()[parser.parse_args().command]()
