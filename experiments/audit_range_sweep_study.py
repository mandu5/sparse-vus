"""Reconstruct timing/selection tables without importing the candidate kernel."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/pvldb-research-20261024'
OUT = BASE/'range-sweep/main-study'
CACHE = ROOT/'.cache/pvldb-full-precision-20261024'


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())


def interval(logs, seed=20261024):
    logs=np.asarray(logs)
    rng=np.random.default_rng(seed)
    sampled=logs[rng.integers(0,len(logs),(10000,len(logs)))].mean(axis=1)
    return {'geometric_ratio':float(np.exp(logs.mean())),
            'familywise95_ci':np.exp(np.quantile(sampled,[.05/6,1-.05/6])).tolist(),
            'units':len(logs),'wins':int(np.count_nonzero(logs>0)),
            'min_ratio':float(np.exp(logs.min())),'max_ratio':float(np.exp(logs.max()))}


def audit():
    p,c=read(OUT/'protocol.json'),read(OUT/'complete.json')
    assert c['status']=='COMPLETE' and c['protocol_sha256']==digest(OUT/'protocol.json')
    assert c['records_sha256']==digest(OUT/'records.jsonl')
    for s,h in p['source_sha256'].items(): assert digest(ROOT/s)==h
    assert p['inputs_sha256']==digest(BASE/'full-precision/inputs.json')
    assert p['primary_protocol_sha256']==digest(BASE/'full-precision/protocol.json')
    cases=read(BASE/'full-precision/inputs.json')['series']
    records=[json.loads(x) for x in (OUT/'records.jsonl').read_text().splitlines()]
    expected={(c['series'],contract,method,trial) for c in cases for contract in ('grid100','distinct')
              for trial,order in enumerate(p['grid_orders' if contract=='grid100' else 'distinct_orders']) for method in order}
    indexed={(r['series'],r['contract'],r['method'],r['trial']):r for r in records}
    assert len(indexed)==len(records) and set(indexed)==expected
    reconstructed_error=0.
    for case in cases:
        assert digest(CACHE/case['file'])==case['npz_sha256']
        with np.load(CACHE/case['file'],allow_pickle=False) as z:
            assert z['scores'].shape==(8,len(z['labels']))
            label_hash=hashlib.sha256(np.ascontiguousarray(z['labels'],dtype=np.int8).tobytes()).hexdigest()
            counts=[len(np.unique(s)) for s in z['scores']]
            queries={'grid100':[np.linspace(s.min(),s.max(),100) for s in z['scores']],
                     'distinct':[np.unique(s) for s in z['scores']]}
        for contract in ('grid100','distinct'):
            reference=indexed[(case['series'],contract,'sweep',0)]
            reference_curves=np.load(OUT/reference['curve_file'],allow_pickle=False)
            checked={}
            for key,r in indexed.items():
                if key[:2]!=(case['series'],contract): continue
                assert r['family']==case['family'] and r['n']==case['n'] and r['label_sha256']==label_hash
                assert r['query_counts']==([100]*8 if contract=='grid100' else counts)
                if r['curve_file'] not in checked:
                    assert digest(OUT/r['curve_file'])==r['curve_file_sha256']
                    with np.load(OUT/r['curve_file'],allow_pickle=False) as curves:
                        assert set(curves.files)=={f'model{i}' for i in range(8)}
                        h=hashlib.sha256();vs=[];ts=[]
                        for i in range(8):
                            a=curves[f'model{i}'];assert a.shape==(r['query_counts'][i],3) and np.isfinite(a).all()
                            error=float(np.max(np.abs(a-reference_curves[f'model{i}'])))
                            assert error<=p['parity_atol']
                            reconstructed_error=max(reconstructed_error,error)
                            h.update(np.ascontiguousarray(a,dtype=np.float64).tobytes())
                            vs.append(float(a[:,2].max()));ts.append(float(queries[contract][i][np.argmax(a[:,2])]))
                        checked[r['curve_file']]=(h.hexdigest(),vs,ts,r['curve_file_sha256'])
                h,vs,ts,fh=checked[r['curve_file']]
                assert r['output_sha256']==h and r['values']==vs and r['best_thresholds']==ts and r['curve_file_sha256']==fh
                assert np.isfinite(r['seconds']) and r['seconds']>0 and len(r['values'])==8
                assert 0<=r['max_curve_error']<=p['parity_atol']
                assert np.isfinite(r['values']).all() and min(r['values'])>=-1e-10 and max(r['values'])<=1+1e-10
                assert np.max(np.abs(np.array(r['values'])-reference['values']))<=p['parity_atol']
                values=np.array(r['values'])
                assert r['winners']==np.flatnonzero(values>=values.max()-p['winner_tie_atol']).tolist()
            reference_curves.close()
    tables=[]
    for family in ('NAB','SMAP','SMD'):
        group=[c for c in cases if c['family']==family]
        for contract,control,candidate in (('grid100','prefix','bucket'),('grid100','raster','bucket'),('grid100','sweep','bucket'),('distinct','raster','sweep')):
            ratios=[];blocks={}
            for case in group:
                a=np.median([r['seconds'] for r in records if r['series']==case['series'] and r['contract']==contract and r['method']==control])
                b=np.median([r['seconds'] for r in records if r['series']==case['series'] and r['contract']==contract and r['method']==candidate])
                log=float(np.log(a/b));ratios.append(log)
                label=indexed[(case['series'],contract,'sweep',0)]['label_sha256']
                blocks.setdefault(label,[]).append(log)
            tables.append({'family':family,'contract':contract,'control':control,'candidate':candidate,'case':interval(ratios),
                           'equal_label_blocks':interval([np.mean(v) for v in blocks.values()])})
    selection=[]
    for family in ('NAB','SMAP','SMD'):
        group=[c for c in cases if c['family']==family]
        details=[]
        for case in group:
            g=indexed[(case['series'],'grid100','sweep',0)]
            d=indexed[(case['series'],'distinct','sweep',0)]
            delta=np.array(d['values'])-g['values']
            assert min(delta)>=-1e-10
            regret=max(d['values'])-max(d['values'][i] for i in g['winners'])
            details.append({'series':case['series'],'winner_set_changes':g['winners']!=d['winners'],
                            'nonoverlap':not bool(set(g['winners'])&set(d['winners'])),
                            'best_grid_winner_regret':float(regret),'max_profile_gain':float(max(delta))})
        selection.append({'family':family,'cases':len(details),'winner_set_changes':sum(d['winner_set_changes'] for d in details),
                          'nonoverlap':sum(d['nonoverlap'] for d in details),'regret_ge_01':sum(d['best_grid_winner_regret']>=.01 for d in details),
                          'max_regret':max(d['best_grid_winner_regret'] for d in details),'details':details})
    winner_disagreements=sum(r['winners']!=indexed[(r['series'],r['contract'],'sweep',0)]['winners'] for r in records)
    return {'status':'PASS','scope':'Saved complete-curve parity, timing/selection/provenance reconstruction; no independent all-input mathematical oracle.',
            'protocol_sha256':digest(OUT/'protocol.json'),'records_sha256':digest(OUT/'records.jsonl'),
            'record_count':len(records),'series_count':len(cases),'max_curve_error':reconstructed_error,
            'producer_reported_max_curve_error':max(r['max_curve_error'] for r in records),
            'winner_set_disagreements_between_methods':winner_disagreements,
            'timing':tables,'grid_to_distinct_selection':selection}


if __name__=='__main__':
    print(json.dumps(audit(),indent=2,allow_nan=False))
