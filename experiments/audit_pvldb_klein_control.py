"""Reconstruct the minimal Klein ablation without importing producers/kernels."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import numpy as np
from audit_pvldb20261024 import digest,read,coverage,check_values,equivalent,ratio_summary,block_summary,validate_inputs

COMPARISONS={'external_over_control':('external','klein_support'),
             'control_over_released':('klein_support','released'),
             'control_over_stream':('klein_support','stream'),
             'released_over_stream':('released','stream')}


def reference_vectors(rows,names,models,width):
    selected=[r for r in rows if r['method']=='released' and r['trial']==0 and r['width']==width]
    coverage([r['series'] for r in selected],names)
    for r in selected:
        values=np.asarray(r['values'],float)
        if values.shape!=(models,) or not np.isfinite(values).all():raise ValueError('reference axes/values')
    return {r['series']:r['values'] for r in selected}


def reconstruct(p,cases,rows,workflows,references,labels):
    cs={c['series']:c for c in cases};coverage([c['series'] for c in cases],set(cs));methods=p['methods']
    coverage([(r['series'],r['method'],r['trial']) for r in rows],{(n,m,t) for n in cs for m in methods for t in range(len(p['orders']))})
    indexed={(r['series'],r['method'],r['trial']):r for r in rows};max_error=0.
    for r in rows:
        n=r['series']
        if r['family']!=cs[n]['family']:raise ValueError('case identity')
        if not np.isfinite(r['seconds']) or r['seconds']<=0:raise ValueError('timing')
        error=check_values(r['values'],r['winners'],references[n]);max_error=max(max_error,error)
        equivalent(r['pr_error'],error,'recorded error')
        equivalent(r['values'],indexed[n,r['method'],0]['values'],'repeat output')
    families=sorted({c['family'] for c in cases});wf={(r['family'],r['method'],r['trial']):r for r in workflows}
    coverage([(r['family'],r['method'],r['trial']) for r in workflows],{(f,m,t) for f in families for m in methods for t in range(len(p['workflow_orders']))})
    for r in workflows:
        if not np.isfinite(r['seconds']) or r['seconds']<=0:raise ValueError('workflow timing')
        coverage([d['series'] for d in r['decisions']],{n for n,c in cs.items() if c['family']==r['family']})
        for d in r['decisions']:
            check_values(d['values'],d['winners'],references[d['series']])
            equivalent(d['values'],indexed[d['series'],r['method'],0]['values'],'workflow values')
    collections={}
    for f in families:
        names=[n for n,c in cs.items() if c['family']==f]
        times={n:{m:statistics.median(indexed[n,m,t]['seconds'] for t in range(len(p['orders']))) for m in methods} for n in names}
        ratios={key:[times[n][a]/times[n][b] for n in names] for key,(a,b) in COMPARISONS.items()}
        wt={m:[wf[f,m,t]['seconds'] for t in range(len(p['workflow_orders']))] for m in methods}
        collections[f]={'series':len(names),'case_medians':times,
            'case_comparisons':{key:ratio_summary(v) for key,v in ratios.items()},
            'label_block_sensitivity':{key:block_summary(v,[labels[n] for n in names]) for key,v in ratios.items()},
            'workflow_seconds':wt,'workflow_medians':{m:statistics.median(v) for m,v in wt.items()},
            'workflow_comparisons':{key:{'median_ratio':statistics.median(wt[a])/statistics.median(wt[b]),
                'paired_trial_ratios':ratio_summary(np.array(wt[a])/wt[b]),'scope':'three fixed-input timing trials, not fully position-balanced; not population uncertainty'} for key,(a,b) in COMPARISONS.items()}}
    return {'collections':collections,'max_reference_pr_error':max_error,'records':len(rows),'workflows':len(workflows)}


def audit(root,output):
    root=Path(root).resolve();base=root/'artifacts/pvldb-research-20261024';folder=base/'klein-support-control';primary=base/'full-precision'
    p,start,done=[read(folder/f) for f in ('protocol.json','run-start.json','complete.json')]
    if done['status']!='COMPLETE':raise ValueError('incomplete')
    for r in (start,done):
        if r['protocol_sha256']!=digest(folder/'protocol.json'):raise ValueError('protocol binding')
    for name in ('records','workflows'):
        if done[name+'_sha256']!=digest(folder/(name+'.jsonl')):raise ValueError('record binding')
    for file,h in p['source_sha256'].items():
        if digest(root/file)!=h:raise ValueError('source binding: '+file)
    for key,name in [('primary_protocol_sha256','protocol.json'),('inputs_sha256','inputs.json'),('primary_records_sha256','records.jsonl')]:
        if digest(primary/name)!=p[key]:raise ValueError('parent binding')
    parent,inputs=read(primary/'protocol.json'),read(primary/'inputs.json')
    if inputs['status']!='COMPLETE' or inputs['protocol_sha256']!=digest(primary/'protocol.json'):raise ValueError('parent input self-binding')
    labels,_,_=validate_inputs(root,parent,inputs)
    references=reference_vectors(list(map(json.loads,(primary/'records.jsonl').read_text().splitlines())),
        {c['series'] for c in inputs['series']},len(parent['models']),p['width'])
    rows,wf=[[json.loads(line) for line in (folder/(name+'.jsonl')).read_text().splitlines()] for name in ('records','workflows')]
    result={'status':'PASS','audit_kind':'raw-record reconstruction, not a fresh timing run','auditor_sha256':digest(__file__),
        'shared_auditor_sha256':digest(Path(__file__).with_name('audit_pvldb20261024.py')),'protocol_sha256':digest(folder/'protocol.json'),
        'records_sha256':digest(folder/'records.jsonl'),'workflows_sha256':digest(folder/'workflows.jsonl'),
        'qualification':'Post-primary author-created control on the unchanged fixed panel; not an unchanged upstream release. Case intervals are per-comparison familywise over three collections; geometry dependence is separately reported.',
        **reconstruct(p,inputs['series'],rows,wf,references,labels)}
    with Path(output).open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','max_reference_pr_error','records','workflows')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();audit(args.root,args.output)
