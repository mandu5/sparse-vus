"""Reconstruct the follow-up from raw records without importing metric code.

The operating-range experiment is post-primary conditional evidence. Synthetic
cases test mechanisms; MITDB/SWaT do not increase the original cohort size.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
import statistics
import zipfile
import numpy as np

from audit_pvldb20261024 import digest, read, coverage, equivalent

PAIRS={'benchopt_pair','radix_pair'}


def support_counts(labels,width):
    y=np.asarray(labels,np.int8);delta=np.diff(np.r_[0,y,0])
    starts=np.flatnonzero(delta==1);ends=np.flatnonzero(delta==-1)-1
    counts=[]
    for w in range(width+1):
        radius=w//2;total=0;last=-1
        for a,b in zip(starts,ends):
            lo=max(0,int(a)-radius);hi=min(len(y)-1,int(b)+radius)
            total+=max(0,hi-max(lo,last+1)+1);last=max(last,hi)
        counts.append(total)
    return counts


def independent_visits(labels,scores,width):
    """Dense reconstruction of the first complete tie with saturated recall.

    This deliberately uses direct interval ramps, ordinary comparison sorting
    and dense cumulative sums, independently of the instrumented linked-list,
    radix and union-find implementation. Only diagnostic work is reconstructed.
    """
    y=np.asarray(labels,np.int8);scores=np.asarray(scores,np.float64)
    edges=np.diff(np.r_[0,y,0]);starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)-1
    orders=[np.argsort(-s,kind='stable') for s in scores]
    result=[[] for _ in scores];positives=int(y.sum());n=len(y)
    for w in range(width+1):
        weight=y.astype(float);merged=[];radius=w//2
        for a,b in zip(starts,ends):
            a,b=int(a),int(b);lo=max(0,a-radius);hi=min(n-1,b+radius)
            if radius:
                left=np.arange(lo,a);right=np.arange(b+1,hi+1)
                weight[left]+=np.sqrt(1.-(a-left)/w)
                weight[right]+=np.sqrt(1.-(right-b)/w)
            if merged and lo<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],hi)
            else:merged.append([lo,hi])
        np.minimum(weight,1.,out=weight)
        for model,(score,order) in enumerate(zip(scores,orders)):
            active=order[weight[order]>0];values=score[active]
            group_ends=np.r_[np.flatnonzero(values[:-1]!=values[1:]),len(active)-1]
            a=np.cumsum(y[active],dtype=np.int64)
            b=np.cumsum(weight[active]*(1-y[active]))
            last_component=min(float(np.max(score[lo:hi+1])) for lo,hi in merged)
            saturated=(a[group_ends]+b[group_ends]/2.>=positives)&(values[group_ends]<=last_component)
            hits=np.flatnonzero(saturated)
            result[model].append(int(group_ends[hits[0]]+1) if len(hits) else len(active))
    return result


def positive_seconds(value):
    if not np.isfinite(value) or value<=0:raise ValueError('invalid timing')
    return float(value)


def vector(values,size):
    a=np.asarray(values,float)
    if a.shape!=(size,) or not np.isfinite(a).all():raise ValueError('invalid metric vector')
    return a


def trial_ratio(a,b):
    a,b=np.asarray(a,float),np.asarray(b,float)
    log=np.log(a/b);rng=np.random.default_rng(20261024)
    resampled=log[rng.integers(0,len(log),size=(4000,len(log)))].mean(axis=1)
    return {'median_ratio':float(np.median(a)/np.median(b)),
            'paired_geometric_ratio':float(np.exp(log.mean())),
            'paired_trial_ci95':np.exp(np.quantile(resampled,[.025,.975])).tolist(),
            'trials':len(log),'inference':'timing trials on fixed inputs; no population claim'}


def reconstruct(p,cases,rows,workflows,diagnostics,metadata):
    cs={c['name']:c for c in cases}
    coverage([c['name'] for c in cases],set(cs))
    def methods(c):return p['real_methods'] if c['kind']=='real' else p['controlled_methods']
    def orders(c):return p['real_orders'] if c['kind']=='real' else p['controlled_orders']
    expected={(n,m,t) for n,c in cs.items() for m in methods(c) for t in range(len(orders(c)))}
    coverage([(r['name'],r['method'],r['trial']) for r in rows],expected)
    indexed={(r['name'],r['method'],r['trial']):r for r in rows}
    refs={n:vector(indexed[n,'radix_pair' if c['kind']=='real' else 'released',0]['values'],c['models']) for n,c in cs.items()}
    rocs={n:vector(indexed[n,'radix_pair',0]['roc'],c['models']) for n,c in cs.items() if c['kind']=='real'}
    max_pr=max_roc=0.
    for r in rows:
        n,m,t=r['name'],r['method'],r['trial'];c=cs[n]
        if r['kind']!=c['kind'] or r['family']!=c['family']:raise ValueError('case identity mismatch')
        positive_seconds(r['seconds']);a=vector(r['values'],c['models'])
        err=float(np.max(np.abs(a-refs[n])));max_pr=max(max_pr,err)
        if err>p['parity_atol']:raise ValueError('PR parity')
        winners=np.flatnonzero(a>=a.max()-p['winner_tie_atol']).tolist()
        truth=np.flatnonzero(refs[n]>=refs[n].max()-p['winner_tie_atol']).tolist()
        if r['winners']!=winners or winners!=truth:raise ValueError('winner parity')
        if not np.isfinite(r['pr_error']) or not 0<=r['pr_error']<=p['parity_atol']:raise ValueError('recorded PR error')
        if c['kind']=='real':equivalent(r['pr_error'],err,'recorded PR error')
        if m in PAIRS:
            aroc=vector(r['roc'],c['models']);re=float(np.max(np.abs(aroc-rocs[n])));max_roc=max(max_roc,re)
            if re>p['parity_atol']:raise ValueError('ROC parity')
            equivalent(r['roc_error'],re,'recorded ROC error')
        elif r['roc'] is not None or r['roc_error'] is not None:raise ValueError('unexpected ROC output')
        equivalent(r['values'],indexed[n,m,0]['values'],'deterministic output')
    families=sorted({c['family'] for c in cases if c['kind']=='real'})
    coverage([(w['family'],w['method'],w['trial']) for w in workflows],
             {(f,m,t) for f in families for m in p['real_methods'] for t in range(len(p['workflow_orders']))})
    wf_times=defaultdict(dict)
    for w in workflows:
        f,m,t=w['family'],w['method'],w['trial'];positive_seconds(w['seconds'])
        coverage([d['name'] for d in w['decisions']],{n for n,c in cs.items() if c['kind']=='real' and c['family']==f})
        for d in w['decisions']:
            n=d['name'];r=indexed[n,m,0]
            equivalent(d['values'],r['values'],'workflow PR')
            equivalent(d['roc'],r['roc'],'workflow ROC')
            if d['winners']!=r['winners']:raise ValueError('workflow winners')
        wf_times[f,m][t]=w['seconds']
    coverage([(d['name'],d['model']) for d in diagnostics],{(n,i) for n,c in cs.items() for i in range(c['models'])})
    work=defaultdict(list)
    for d in diagnostics:
        n=d['name'];c=cs[n];meta=metadata[n]
        if d['Q']!=meta['Q'] or d['K']!=meta['K']:raise ValueError('support diagnostic geometry')
        active=np.asarray(d['active']);visited=np.asarray(d['visited'])
        if active.tolist()!=meta['active_by_width'] or visited.shape!=(c['width']+1,):raise ValueError('diagnostic width counts')
        if not np.isfinite(visited).all() or np.any(visited!=visited.astype(np.int64)) or np.any(visited<0) or np.any(visited>active):raise ValueError('diagnostic visits')
        if visited.tolist()!=meta['independent_visited'][d['model']]:raise ValueError('independent diagnostic visits')
        if not np.isfinite(d['values']['pr']) or abs(d['values']['pr']-refs[n][d['model']])>p['parity_atol']:raise ValueError('diagnostic PR parity')
        if not np.isfinite(d['values']['roc']):raise ValueError('invalid diagnostic ROC')
        if c['kind']=='real' and abs(d['values']['roc']-rocs[n][d['model']])>p['parity_atol']:raise ValueError('diagnostic ROC parity')
        work[n].append({'model':d['model'],'active_sum':int(active.sum()),'visited_sum':int(visited.sum())})
    result_cases={}
    for n,c in cs.items():
        times={m:[indexed[n,m,t]['seconds'] for t in range(len(orders(c)))] for m in methods(c)}
        med={m:statistics.median(v) for m,v in times.items()}
        result_cases[n]={**{k:c[k] for k in ('kind','family','n','models','width')},**metadata[n],
            'Q_fraction':metadata[n]['Q']/c['n'],'median_seconds':med,
            'relative_to_stream':{m:trial_ratio(v,times['stream']) for m,v in times.items() if m!='stream'},
            'dense_over_released':trial_ratio(times['dense'],times['released']),
            'prefix_diagnostics':work[n],
            'prefix_count_scope':'Separate active-prefix instrumentation, not the width-major stream implementation.'}
        if c['kind']=='real':result_cases[n]['matched_pair']=trial_ratio(times['benchopt_pair'],times['radix_pair'])
    collections={}
    for f in families:
        names=[n for n,c in cs.items() if c['kind']=='real' and c['family']==f]
        med={m:statistics.median(wf_times[f,m].values()) for m in p['real_methods']}
        series={m:np.array([result_cases[n]['median_seconds'][m]/result_cases[n]['median_seconds']['stream'] for n in names]) for m in p['real_methods'] if m!='stream'}
        collections[f]={'series':len(names),'unique_label_blocks':len({metadata[n]['label_identity'] for n in names}),
            'case_inference':'one fixed series; no population interval' if len(names)==1 else 'fixed follow-up panel; correlated source/labels, no population interval',
            'case_geometric_ratios':{m:float(np.exp(np.log(v).mean())) for m,v in series.items()},
            'case_losses':{m:[n for n,v in zip(names,a) if v<1.] for m,a in series.items()},
            'workflow_median_seconds':med,
            'workflow_ratios':{m:trial_ratio([wf_times[f,m][t] for t in range(len(p['workflow_orders']))],
                                           [wf_times[f,'stream'][t] for t in range(len(p['workflow_orders']))]) for m in p['real_methods'] if m!='stream'},
            'workflow_matched_pair_ratio':med['benchopt_pair']/med['radix_pair']}
    return {'cases':result_cases,'collections':collections,'max_reference_pr_error':max_pr,'max_reference_roc_error':max_roc}


def validate_inputs(root,p,ip):
    import pandas as pd
    cases=ip['cases'];planned=p['real_cases']+p['controlled_cases'];mapping={c['name']:c for c in cases}
    coverage([c['name'] for c in cases],{c['name'] for c in planned});metadata={}
    with zipfile.ZipFile(root/'cache/TSB-AD-U.zip') as z:
        for planned_case in planned:
            c=mapping[planned_case['name']]
            for key,value in planned_case.items():equivalent(c[key],value,'planned input metadata')
            expected_kind='real' if 'member' in planned_case else 'controlled'
            if c['kind']!=expected_kind:raise ValueError('input kind')
            if c['file']!=c['name']+'.npz':raise ValueError('input file identity')
            path=root/'.cache/pvldb-operating-range-20261024'/c['file']
            if digest(path)!=c['npz_sha256']:raise ValueError('input bytes')
            with np.load(path,allow_pickle=False) as data:
                y=data['labels'];scores=data['scores']
                if y.shape!=(c['n'],) or not np.isin(y,[0,1]).all() or not 0<y.sum()<len(y):raise ValueError('invalid labels')
                if scores.dtype!=np.float64 or scores.shape!=(c['models'],c['n']) or not np.isfinite(scores).all():raise ValueError('invalid scores')
                if hashlib.sha256(scores.tobytes()).hexdigest()!=c['score_sha256']:raise ValueError('score identity')
                if c['kind']=='real':
                    raw=z.read(c['member'])
                    if hashlib.sha256(raw).hexdigest()!=c['raw_sha256']:raise ValueError('raw member bytes')
                    df=pd.read_csv(io.BytesIO(raw));x=df['Data'].to_numpy(np.float64);yr=df['Label'].to_numpy(np.int8)
                    if not np.array_equal(data['observations'],x) or not np.array_equal(y,yr):raise ValueError('raw decoded input')
                    if hashlib.sha256(x.tobytes()+yr.tobytes()).hexdigest()!=c['observation_label_identity']:raise ValueError('raw identity')
                else:
                    count=int(c['n']*c['positive_fraction']);yr=np.zeros(c['n'],np.int8)
                    for j in range(c['components']):
                        size=count//c['components']+(j<count%c['components']);start=int((j+.5)*c['n']/c['components'])-size//2
                        yr[start:start+size]=1
                    expected=np.random.default_rng(p['seed']).random(scores.shape)
                    if c['levels'] is not None:expected=np.floor(expected*c['levels'])
                    if not np.array_equal(y,yr) or not np.array_equal(scores,expected):raise ValueError('controlled construction')
                active=support_counts(y,c['width']);k=int(np.count_nonzero(np.diff(np.r_[0,y,0])==1))
                if k!=c['components']:raise ValueError('component count')
                metadata[c['name']]={'Q':active[-1],'K':k,'active_by_width':active,'positive_points':int(y.sum()),
                    'label_identity':hashlib.sha256(y.tobytes()).hexdigest(),
                    'score_distinct':[len(np.unique(s)) for s in scores],
                    'independent_visited':independent_visits(y,scores,c['width'])}
    return metadata


def audit(root,output):
    root=Path(root).resolve();folder=root/'artifacts/pvldb-research-20261024/operating-range'
    p,ip,start,complete=[read(folder/name) for name in ('protocol.json','inputs.json','run-start.json','complete.json')]
    if complete['status']!='COMPLETE' or ip['status']!='COMPLETE':raise ValueError('unfinished experiment')
    for receipt in (ip,start,complete):
        if receipt['protocol_sha256']!=digest(folder/'protocol.json'):raise ValueError('protocol binding')
    for receipt in (start,complete):
        if receipt['inputs_sha256']!=digest(folder/'inputs.json'):raise ValueError('inputs binding')
    for name in ('records','workflows','diagnostics'):
        if complete[name+'_sha256']!=digest(folder/(name+'.jsonl')):raise ValueError('record binding')
    for file,h in p['source_sha256'].items():
        if digest(root/file)!=h:raise ValueError('source binding: '+file)
    if digest(root/'cache/TSB-AD-U.zip')!=p['archive_sha256']:raise ValueError('archive binding')
    metadata=validate_inputs(root,p,ip)
    rows,workflows,diagnostics=[[json.loads(s) for s in (folder/(name+'.jsonl')).read_text().splitlines()] for name in ('records','workflows','diagnostics')]
    result={'status':'PASS','audit_kind':'independent record reconstruction, not a fresh numerical run',
        'auditor_sha256':digest(__file__),'shared_auditor_sha256':digest(Path(__file__).with_name('audit_pvldb20261024.py')),
        'protocol_sha256':digest(folder/'protocol.json'),'inputs_sha256':digest(folder/'inputs.json'),
        **{name+'_sha256':digest(folder/(name+'.jsonl')) for name in ('records','workflows','diagnostics')},
        'records':len(rows),'workflows':len(workflows),'diagnostics':len(diagnostics),
        'qualifications':['Follow-up fixed after primary results, before its own scores/timings.',
            'All MITDB and SWaT recordings included; prior-name reuse is not unseen-data evidence.',
            'Synthetic one-factor cases describe evaluator cost, not detector accuracy.',
            'Increasing component count also changes expanded support; this is not a pure K intervention.',
            'Trial intervals are unadjusted conditional timing uncertainty, not population generalization.',
            'Seven/four cyclic case orders balance positions; three workflow orders do not.',
            'Visited counts instrument a separate active-prefix implementation, not stream; independently reconstructed with dense interval ramps and comparison sorting.',
            'Diagnostic ROC is checked against recorded radix-pair outputs on real cases; controlled ROC is finite-checked only because that reference was not recorded.',
            'Recorded PR error is reconstructed on real cases; controlled error is bounded only because its untimed radix reference was not recorded.'],
        **reconstruct(p,ip['cases'],rows,workflows,diagnostics,metadata)}
    with Path(output).open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','records','workflows','diagnostics','max_reference_pr_error','max_reference_roc_error','collections')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();audit(args.root,args.output)
