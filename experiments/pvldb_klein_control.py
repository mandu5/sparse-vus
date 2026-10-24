"""Post-primary ablation: a one-expression support-threshold change to Klein.

The patched implementation is an author-created control, not an upstream
release. This design is fixed before measuring it on the stored 73-case panel.
"""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np
from audit_pvldb20261024 import digest,read

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/pvldb-research-20261024'
PRIMARY=BASE/'full-precision';OUT=BASE/'klein-support-control'
CACHE=ROOT/'.cache/pvldb-full-precision-20261024'
METHODS=['released','stream','klein_support','external']


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def freeze():
    from klein_support_control import OLD,NEW
    parent=read(PRIMARY/'protocol.json');sources=dict(parent['source_sha256'])
    for file in ('experiments/pvldb_klein_control.py','experiments/klein_support_control.py','experiments/audit_pvldb20261024.py'):sources[file]=digest(ROOT/file)
    orders=[METHODS[i:]+METHODS[:i] for i in range(len(METHODS))]
    orders+=list(map(lambda x:list(reversed(x)),orders.copy()))
    OUT.mkdir(exist_ok=False)
    write(OUT/'protocol.json',{'status':'FROZEN_AFTER_PRIMARY_AND_LONG_FOLLOWUP_BEFORE_THIS_CONTROL_TIMING',
        'created_utc':datetime.now(timezone.utc).isoformat(),'primary_protocol_sha256':digest(PRIMARY/'protocol.json'),
        'inputs_sha256':digest(PRIMARY/'inputs.json'),'primary_records_sha256':digest(PRIMARY/'records.jsonl'),
        'source_sha256':sources,'methods':METHODS,'orders':orders,'workflow_orders':orders[:3],
        'width':30,'parity_atol':1e-11,'winner_tie_atol':1e-10,'patch':{'old':OLD,'new':NEW},
        'cohort':'All 73 fixed primary recordings and eight stored float64 scores; no new scores or exclusions.',
        'hypothesis':'Measure how much one support-threshold expression explains the unchanged public Klein gap; compare remaining gain to the single-model released evaluator separately from batching.',
        'timing':'Serial single numerical thread, warm imports/JIT, complete public calls and winner selection; eight case orders balance each position twice. Three file-to-decision collection passes are not fully position balanced.',
        'comparisons':['external_over_control','control_over_released','control_over_stream','released_over_stream'],
        'uncertainty':'10000 seeded paired log-ratio resamples of case medians, familywise95 over three collections per comparison; identical-label-block sensitivity. Workflow intervals concern only three fixed-input trials.',
        'failure_policy':'Retain every loss. Nonfinite output, PR discrepancy above tolerance or different winner set halts with no replacement.',
        'scope':'The modified Klein implementation is a new author-created ablation, not an unchanged public baseline or a claim that the idea is absent from prior work.'})


def verify():
    p=read(OUT/'protocol.json')
    for path,h in p['source_sha256'].items():
        if digest(ROOT/path)!=h:raise ValueError('source changed: '+path)
    for key,name in [('primary_protocol_sha256','protocol.json'),('inputs_sha256','inputs.json'),('primary_records_sha256','records.jsonl')]:
        if digest(PRIMARY/name)!=p[key]:raise ValueError('parent binding: '+name)
    return p


def evaluate(method,y,scores):
    if method=='klein_support':
        from klein_support_control import klein_support_pr
        values=np.asarray([klein_support_pr(y,s,30) for s in scores])
        return values,np.flatnonzero(values>=values.max()-1e-10).tolist()
    from pvldb_full_precision import evaluate as original
    return original(method,y,scores,30)


def run():
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments')];p=verify();cases=read(PRIMARY/'inputs.json')['series']
    for c in cases:
        if digest(CACHE/c['file'])!=c['npz_sha256']:raise ValueError('input bytes')
    references={r['series']:r['values'] for r in map(json.loads,(PRIMARY/'records.jsonl').read_text().splitlines()) if r['method']=='released' and r['trial']==0 and r['width']==30}
    write(OUT/'run-start.json',{'utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':digest(OUT/'protocol.json'),'platform':platform.platform(),'python':sys.version})
    for method in METHODS:evaluate(method,np.array([0,1,0,0,1,0],np.int8),np.tile(np.arange(6.),(8,1)))
    with (OUT/'records.jsonl').open('x') as f:
        for c in cases:
            with np.load(CACHE/c['file'],allow_pickle=False) as z:y,scores=z['labels'],z['scores']
            reference=np.asarray(references[c['series']]);truth=np.flatnonzero(reference>=reference.max()-p['winner_tie_atol']).tolist()
            for trial,order in enumerate(p['orders']):
                for method in order:
                    start=time.perf_counter_ns();values,winners=evaluate(method,y,scores);seconds=(time.perf_counter_ns()-start)*1e-9
                    error=float(np.max(np.abs(values-reference)))
                    if not np.isfinite(values).all() or error>p['parity_atol'] or winners!=truth:raise ValueError('parity: '+c['series']+' '+method)
                    f.write(json.dumps({'series':c['series'],'family':c['family'],'method':method,'trial':trial,'seconds':seconds,
                        'values':values.tolist(),'winners':winners,'pr_error':error},allow_nan=False)+'\n');f.flush()
            print(c['series'],'complete',flush=True)
    with (OUT/'workflows.jsonl').open('x') as f:
        for family in ('NAB','SMAP','SMD'):
            group=[c for c in cases if c['family']==family]
            for trial,order in enumerate(p['workflow_orders']):
                for method in order:
                    start=time.perf_counter_ns();decisions=[]
                    for c in group:
                        with np.load(CACHE/c['file'],allow_pickle=False) as z:values,winners=evaluate(method,z['labels'],z['scores'])
                        decisions.append({'series':c['series'],'values':values.tolist(),'winners':winners})
                    with (CACHE/'last-klein-control-output.json').open('w') as target:json.dump(decisions,target,allow_nan=False)
                    seconds=(time.perf_counter_ns()-start)*1e-9
                    f.write(json.dumps({'family':family,'method':method,'trial':trial,'seconds':seconds,'decisions':decisions},allow_nan=False)+'\n');f.flush()
            print(family,'workflow complete',flush=True)
    write(OUT/'complete.json',{'status':'COMPLETE','utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':digest(OUT/'protocol.json'),
        'records_sha256':digest(OUT/'records.jsonl'),'workflows_sha256':digest(OUT/'workflows.jsonl')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','run']);globals()[parser.parse_args().command]()
