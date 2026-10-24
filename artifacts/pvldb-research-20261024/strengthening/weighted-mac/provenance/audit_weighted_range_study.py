"""Reconstruct the weighted study from saved curves; never imports its kernel."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def interval(logs, correction):
    a=np.asarray(logs,dtype=float)
    rng=np.random.default_rng(20261024)
    means=a[rng.integers(0,len(a),(10000,len(a)))].mean(axis=1)
    return {'geometric_ratio':float(np.exp(a.mean())),
        'simultaneous95_ci':np.exp(np.quantile(means,[.025/correction,1-.025/correction])).tolist(),
        'units':len(a),'wins':int(np.count_nonzero(a>0)),
        'min_ratio':float(np.exp(a.min())),'max_ratio':float(np.exp(a.max())),
        'correction_comparisons':correction}


def audit(out,verify_local_inputs=True):
    p,c=read(out/'protocol.json'),read(out/'complete.json')
    assert c['status']=='COMPLETE' and c['protocol_sha256']==sha(out/'protocol.json')
    assert c['records_sha256']==sha(out/'records.jsonl')
    for source,h in p['sources'].items():assert sha(ROOT/source)==h
    if verify_local_inputs:
        assert sha(ROOT/p['inputs_path'])==p['inputs_sha256']
        for case in p['cases']:assert sha(ROOT/case['npz_path'])==case['npz_sha256']
    records=[json.loads(line) for line in (out/'records.jsonl').read_text().splitlines()]
    def key(r):return (r['id'],r['query'],r['bias'],r['cardinality'],r['trial'],r['method'])
    indexed={key(r):r for r in records}
    expected={(case['id'],q,b,g,t,m) for case in p['cases'] for q in p['queries']
        for b,g in itertools.product(p['biases'],p['cardinalities'])
        for t,order in enumerate(p['orders']) for m in order}
    assert len(indexed)==len(records) and set(indexed)==expected
    maximum_error=0.;winner_disagreements=0;checked_files=set()
    for case in p['cases']:
        for query in p['queries']:
            curves={}
            for method in p['orders'][0]:
                r=indexed[(case['id'],query,'flat','one',0,method)]
                path=out/r['curve_file']
                assert sha(path)==r['curve_file_sha256']
                with np.load(path,allow_pickle=False) as z:curves[method]={k:z[k] for k in z.files}
                checked_files.add(str(path))
                assert set(curves[method])=={f'{b}_{g}_{i}' for b,g in itertools.product(p['biases'],p['cardinalities']) for i in range(2)}
            for bias,card in itertools.product(p['biases'],p['cardinalities']):
                ref=[curves['raster'][f'{bias}_{card}_{i}'] for i in range(2)]
                refvalues=[float(np.max(a[:,2])) for a in ref]
                refwin=np.flatnonzero(np.array(refvalues)>=max(refvalues)-p['winner_atol']).tolist()
                for method in p['orders'][0]:
                    arrays=[curves[method][f'{bias}_{card}_{i}'] for i in range(2)]
                    h=hashlib.sha256()
                    for a,b in zip(arrays,ref):
                        assert a.ndim==2 and a.shape[1]==3 and a.shape==b.shape and np.isfinite(a).all()
                        assert a.min()>=-1e-10 and a.max()<=1+1e-10
                        maximum_error=max(maximum_error,float(np.max(np.abs(a-b))))
                        h.update(np.ascontiguousarray(a,dtype=np.float64).tobytes())
                    values=[float(np.max(a[:,2])) for a in arrays]
                    winners=np.flatnonzero(np.array(values)>=max(values)-p['winner_atol']).tolist()
                    winner_disagreements+=winners!=refwin
                    canonical=indexed[(case['id'],query,bias,card,0,method)]
                    for trial in range(len(p['orders'])):
                        r=indexed[(case['id'],query,bias,card,trial,method)]
                        assert r['family']==case['family'] and r['n']==case['n']
                        assert r['seconds']>0 and np.isfinite(r['seconds'])
                        assert r['output_sha256']==h.hexdigest() and r['values']==values and r['winners']==winners
                        assert r['curve_file']==canonical['curve_file'] and r['curve_file_sha256']==canonical['curve_file_sha256']
                        assert r['query_counts']==[len(a) for a in arrays]
                        assert 0<=r['max_curve_error']<=p['parity_atol']
    assert maximum_error<=p['parity_atol']
    def seconds(case,query,bias,card,method):
        return np.median([indexed[(case['id'],query,bias,card,t,method)]['seconds'] for t in range(6)])
    tables=[];aggregates=[]
    for family in ('WSD','Stock','MSL'):
        cases=[c for c in p['cases'] if c['family']==family]
        for query,control,candidate in p['comparisons']:
            all_logs=[]
            for bias,card in itertools.product(p['biases'],p['cardinalities']):
                logs=[np.log(seconds(c,query,bias,card,control)/seconds(c,query,bias,card,candidate)) for c in cases]
                all_logs.append(logs)
                tables.append({'family':family,'query':query,'bias':bias,'cardinality':card,
                    'control':control,'candidate':candidate,**interval(logs,36)})
            aggregates.append({'family':family,'query':query,'control':control,'candidate':candidate,
                'aggregation':'Equal log weight to each of12 semantic contracts per case; then case bootstrap',
                **interval(np.mean(all_logs,axis=0),3)})
    selection=[]
    for bias,card in itertools.product(p['biases'],p['cardinalities']):
        details=[]
        for case in p['cases']:
            g=indexed[(case['id'],'grid100',bias,card,0,'raster')]
            d=indexed[(case['id'],'distinct',bias,card,0,'raster')]
            assert min(np.array(d['values'])-g['values'])>=-1e-10
            details.append({'id':case['id'],'family':case['family'],
                'nonoverlap':not bool(set(g['winners'])&set(d['winners'])),
                'best_grid_winner_regret':max(d['values'])-max(d['values'][i] for i in g['winners'])})
        selection.append({'bias':bias,'cardinality':card,'details':details,
            'nonoverlap':sum(d['nonoverlap'] for d in details),
            'regret_ge_01':sum(d['best_grid_winner_regret']>=.01 for d in details),
            'max_regret':max(d['best_grid_winner_regret'] for d in details)})
    return {'status':'PASS','scope':'Independent saved-curve/output/statistical reconstruction; mathematical oracle is a separate test suite.',
        'local_input_bytes_verified':verify_local_inputs,'protocol_sha256':sha(out/'protocol.json'),
        'records_sha256':sha(out/'records.jsonl'),'records':len(records),'curve_files':len(checked_files),
        'cases':len(p['cases']),'max_curve_error':maximum_error,'winner_disagreements':winner_disagreements,
        'interval_limit':'Fixed selected cohort, shared physical sources not excluded. MSL2 gives no credible population-coverage claim. Bootstrap95 is approximate, not a finite-sample coverage theorem.',
        'semantic_timing':tables,'aggregate_timing':aggregates,'grid_to_distinct_selection':selection}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--report',type=Path)
    parser.add_argument('--without-local-inputs',action='store_true',help='Explicitly weaker archive-only verification for a second host.')
    args=parser.parse_args();result=audit(args.output,not args.without_local_inputs)
    payload=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if args.report:
        with args.report.open('x') as f:f.write(payload)
    else:print(payload,end='')
