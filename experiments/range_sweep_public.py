"""Source-pinned public range-F1 comparator study; separate semantic contracts."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
import argparse
from datetime import datetime,timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import signal
import sys
import time
from urllib.request import urlopen
import numpy as np
from range_sweep_study import ROOT,BASE,PRIMARY,CACHE,digest,read,write

OUT=BASE/'range-sweep/public-study-v2'
MANIFEST=BASE/'range-sweep/timesead-sources.json'


def fetch():
    for r in read(MANIFEST):
        p=ROOT/r['local']
        if not p.exists():
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(urlopen(r['url'],timeout=60).read())
        if digest(p)!=r['sha256']: raise ValueError('public TimeSeAD source identity')
    from pvldb_consumer import fetch as tsb_fetch
    tsb_fetch()


def freeze():
    fetch()
    sources={r['local']:r['sha256'] for r in read(MANIFEST)}
    sources.update(read(BASE/'public-consumer/protocol.json')['source_sha256'])
    for s in ('src/sparse_vus/range_sweep.py','experiments/range_sweep_public.py','experiments/range_sweep_study.py'):
        sources[s]=digest(ROOT/s)
    cases=read(PRIMARY/'inputs.json')['series']
    selected=[]
    for family in ('NAB','SMAP','SMD'):
        selected+=sorted([c for c in cases if c['family']==family],key=lambda c:(c['n'],c['series']))[:3]
    OUT.mkdir(exist_ok=False)
    write(OUT/'protocol.json',{
        'status':'FROZEN_BEFORE_PUBLIC_RANGE_BASELINE_OUTCOMES','utc':datetime.now(timezone.utc).isoformat(),
        'source_sha256':sources,'manifest_sha256':digest(MANIFEST),'inputs_sha256':digest(PRIMARY/'inputs.json'),
        'main_protocol_sha256':digest(BASE/'range-sweep/main-study/protocol.json'),
        'cases':selected,'selection':'Three shortest primary recordings in each collection, lexicographic ties; all eight stored profiles. Cost-bounded public comparator panel chosen by length before its outcomes. No representativeness or long-input claim.',
        'contracts':{'tsb_grid':'Unchanged TSB-AD metric_RF1; 100 linspace strict thresholds, flat alpha=.2 reciprocal, double scalar; compare bucket tsb_compat.',
                     'timesead_distinct':'Unchanged TimeSeAD Evaluator.best_ts_fbeta_score_classic(beta=1), alpha=0, strict observed thresholds, unweighted precision, reciprocal; float32 PR/F storage. Compare standard sweep, not TSB alpha=.2.'},
        'orders':[['public','candidate'],['candidate','public']],
        'public_call_limit_seconds':60,
        'amendment':'Before any public timing, the initial unexecuted protocol is preserved at public-study/protocol.json. This version adds a 60s eight-profile API-call budget. A timeout remains a censored lower bound, never an exact time, successful parity check or exclusion.',
        'parity_atol':{'tsb_grid':1e-10,'timesead_distinct':2e-7},
        'timing':'Two balanced AB/BA complete eight-profile in-memory calls per method. Conversion/threshold preparation included, imports/JIT warm, single numerical thread. No training/disk/whole-nine-metric claim.',
        'failure_policy':'No dropped/replaced cases. Public timeout is retained with null outputs and censoring limit, then the next fixed trial continues. Nonfinite completed output or scalar discrepancy above the predeclared contract tolerance halts.',
        'scope':'External API validation and timing on 9 length-selected recordings. Broad compiled-algorithm evidence is separately all73, alpha=.2. Do not combine the two target semantics into one ratio.'})


def evaluate(method,contract,y,scores):
    from sparse_vus.range_sweep import range_metrics
    if method=='candidate':
        result=[]
        for s in scores:
            grid=contract=='tsb_grid'
            t=np.linspace(s.min(),s.max(),100) if grid else np.unique(s)
            a=range_metrics('bucket' if grid else 'sweep',y,s,t,alpha=.2 if grid else 0.,tsb_compat=grid)
            result.append(float(a[:,2].max()))
        return result
    if contract=='tsb_grid':
        from TSB_AD.evaluation.basic_metrics import basic_metricor
        return [float(basic_metricor().metric_RF1(y,s)) for s in scores]
    import torch
    from timesead.evaluation import Evaluator
    labels=torch.as_tensor(y,dtype=torch.long)
    return [float(Evaluator().best_ts_fbeta_score_classic(labels,torch.as_tensor(s,dtype=torch.float64),beta=1)[0]) for s in scores]


def run():
    fetch()
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'.cache/tsbad-consumer/pkg'),str(ROOT/'.cache/range-sweep-timesead')]
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    p=read(OUT/'protocol.json')
    for s,h in p['source_sha256'].items():
        if digest(ROOT/s)!=h: raise ValueError('source binding '+s)
    if digest(MANIFEST)!=p['manifest_sha256'] or digest(PRIMARY/'inputs.json')!=p['inputs_sha256']: raise ValueError('parent binding')
    if digest(BASE/'range-sweep/main-study/protocol.json')!=p['main_protocol_sha256']: raise ValueError('main binding')
    for c in p['cases']:
        if digest(CACHE/c['file'])!=c['npz_sha256']: raise ValueError('input binding')
    write(OUT/'run-start.json',{'utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
                              'packages':{s:importlib.metadata.version(s) for s in ('numpy','torch','numba','scikit-learn')},'protocol_sha256':digest(OUT/'protocol.json')})
    for contract in p['contracts']:
        for m in ('public','candidate'):
            evaluate(m,contract,np.array([0,1,1,0,1,0]),np.array([[.1,.2,.7,.3,.5,.4]]))
    def timeout_handler(signum,frame):
        raise TimeoutError('predeclared public-call budget')
    signal.signal(signal.SIGALRM,timeout_handler)
    with (OUT/'records.jsonl').open('x') as f:
        for c in p['cases']:
            with np.load(CACHE/c['file'],allow_pickle=False) as z: y,scores=z['labels'],z['scores']
            for contract in p['contracts']:
                reference=None
                for trial,order in enumerate(p['orders']):
                    for method in order:
                        censored=False
                        if method=='public': signal.setitimer(signal.ITIMER_REAL,p['public_call_limit_seconds'])
                        start=time.perf_counter_ns()
                        try:
                            values=evaluate(method,contract,y,scores)
                        except TimeoutError:
                            values=None;censored=True
                        finally:
                            signal.setitimer(signal.ITIMER_REAL,0)
                        seconds=(time.perf_counter_ns()-start)*1e-9
                        if censored:
                            f.write(json.dumps({'series':c['series'],'family':c['family'],'n':c['n'],'contract':contract,'trial':trial,
                                                'method':method,'seconds':seconds,'values':None,'max_reference_error':None,
                                                'censored':True,'limit_seconds':p['public_call_limit_seconds']},allow_nan=False)+'\n');f.flush()
                            continue
                        if reference is None: reference=values
                        error=float(np.max(np.abs(np.array(values)-reference)))
                        if not np.isfinite(values).all() or error>p['parity_atol'][contract]: raise ValueError('public parity '+c['series']+' '+contract)
                        f.write(json.dumps({'series':c['series'],'family':c['family'],'n':c['n'],'contract':contract,'trial':trial,
                                            'method':method,'seconds':seconds,'values':values,'max_reference_error':error,'censored':False},allow_nan=False)+'\n');f.flush()
                print(c['series'],contract,'complete',flush=True)
    write(OUT/'complete.json',{'status':'COMPLETE','utc':datetime.now(timezone.utc).isoformat(),
                             'protocol_sha256':digest(OUT/'protocol.json'),'records_sha256':digest(OUT/'records.jsonl')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['fetch','freeze','run']);globals()[parser.parse_args().command]()
