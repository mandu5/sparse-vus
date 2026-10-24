"""Audit completed public comparisons; retain censoring without imputing times."""
import json
from pathlib import Path
import numpy as np
from audit_range_sweep_study import digest,read,interval

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/pvldb-research-20261024'
OUT=BASE/'range-sweep/public-study-v2'


def audit():
    p,c=read(OUT/'protocol.json'),read(OUT/'complete.json')
    assert c['status']=='COMPLETE' and c['protocol_sha256']==digest(OUT/'protocol.json')
    assert c['records_sha256']==digest(OUT/'records.jsonl')
    for path,h in p['source_sha256'].items(): assert digest(ROOT/path)==h
    assert p['manifest_sha256']==digest(BASE/'range-sweep/timesead-sources.json')
    assert p['main_protocol_sha256']==digest(BASE/'range-sweep/main-study/protocol.json')
    assert p['inputs_sha256']==digest(BASE/'full-precision/inputs.json')
    parent=read(BASE/'full-precision/inputs.json')['series']
    selected=[]
    for family in ('NAB','SMAP','SMD'):
        selected+=sorted([r for r in parent if r['family']==family],key=lambda r:(r['n'],r['series']))[:3]
    assert selected==p['cases']
    records=[json.loads(s) for s in (OUT/'records.jsonl').read_text().splitlines()]
    ix={(r['series'],r['contract'],r['method'],r['trial']):r for r in records}
    expected={(c['series'],contract,method,trial) for c in selected for contract in p['contracts']
              for trial,order in enumerate(p['orders']) for method in order}
    assert len(ix)==len(records) and set(ix)==expected
    maxerror={contract:0. for contract in p['contracts']}
    table=[]
    for contract in p['contracts']:
        for family in ('NAB','SMAP','SMD'):
            details=[];logs=[]
            for case in [c for c in selected if c['family']==family]:
                assert digest(ROOT/'.cache/pvldb-full-precision-20261024'/case['file'])==case['npz_sha256']
                public=[];candidate=[];censored=0;reference=None
                for method in ('candidate','public'):
                    for trial in range(2):
                        r=ix[(case['series'],contract,method,trial)]
                        assert r['family']==family and r['n']==case['n'] and np.isfinite(r['seconds']) and r['seconds']>0
                        if r['censored']:
                            assert method=='public' and r['values'] is None and r['max_reference_error'] is None
                            assert r['limit_seconds']==p['public_call_limit_seconds'] and r['seconds']>=r['limit_seconds']*.99
                            public.append(float(r['limit_seconds']));censored+=1
                        else:
                            assert len(r['values'])==8 and np.isfinite(r['values']).all()
                            if reference is None: reference=r['values']
                            error=float(np.max(np.abs(np.array(r['values'])-reference)))
                            assert error<=p['parity_atol'][contract]
                            maxerror[contract]=max(maxerror[contract],error)
                            (public if method=='public' else candidate).append(r['seconds'])
                ratio=float(np.median(public)/np.median(candidate))
                details.append({'series':case['series'],'censored_public_calls':censored,'ratio_or_censored_lower_bound':ratio,
                                'candidate_seconds':float(np.median(candidate)),
                                'public_seconds_or_censoring_limit':float(np.median(public)),
                                'public_completed_parity_calls':2-censored})
                logs.append(np.log(ratio))
            censored=any(d['censored_public_calls'] for d in details)
            table.append({'family':family,'contract':contract,'details':details,
                          'censored_bound':censored,'ratio_summary':interval(logs),
                          'interval_scope':'If censored, bootstrap summarizes conservative substituted lower limits, not a confidence interval for actual speedup. Only 3 length-selected cases per family.'})
    return {'status':'PASS','scope':'Source/input/raw-API scalar and timing audit; censored calls are not parity evidence.',
            'protocol_sha256':digest(OUT/'protocol.json'),'records_sha256':digest(OUT/'records.jsonl'),
            'record_count':len(records),'max_public_scalar_error':maxerror,
            'censored_public_calls':sum(r['censored'] for r in records),'tables':table}


if __name__=='__main__': print(json.dumps(audit(),indent=2,allow_nan=False))
