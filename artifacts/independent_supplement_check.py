import json,math,statistics,hashlib,collections,itertools,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1]; A=R/'artifacts'
def load(p): return json.loads(p.read_text())
def lines(p): return [json.loads(x) for x in p.read_text().splitlines()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b): assert math.isclose(a,b,rel_tol=2e-14,abs_tol=1e-16),(a,b)
def num(x): assert type(x) in (int,float) and math.isfinite(x),repr(x)
def hashes(d):
 for p,h in d.items(): assert sha(R/p)==h,('hash',p,sha(R/p),h)
summary=load(A/'external_supplement_summary.json'); rows=lines(A/'external_supplement.jsonl'); selected=load(A/'external_supplement_selection.json'); protocol=load(A/'external_supplement_protocol.json'); main=lines(A/'public_benchmark.jsonl'); env=load(A/'external_supplement_environment.json')
assert summary['status']=='PASS';hashes(summary['source_sha256']);hashes(summary['input_sha256'])
assert summary['source_sha256']==env['source_sha256'];assert summary['input_sha256']==env['input_sha256']
assert sha(A/'external_supplement.jsonl')==summary['records_sha256'];assert sha(A/'external_supplement_environment.json')==summary['environment_sha256'];assert sha(A/'external_supplement_protocol.json')==summary['protocol_sha256']
lookup={r['series']:r for r in main if r['model']==protocol['model'] and r['max_buffer']==protocol['maximum_buffer']}; family=collections.defaultdict(list)
for r in lookup.values(): family[r['family']].append(r)
expected=[]
for f in sorted(family):
 s=sorted(family[f],key=lambda r:(r['n'],r['series']));expected.extend(s[i]['series'] for i in sorted({0,len(s)//2}))
assert expected==[r['series'] for r in rows]==[s['series'] for s in selected]
assert len(rows)==len(set(expected))==summary['series']==42;assert len(family)==summary['families']==23
scorehash={Path(x['path']).stem:x['sha256'] for x in load(A/'bolt_base_64-download.json')['members']}
errors=[];timeouts=[]
for r,s in zip(rows,selected):
 m=lookup[r['series']]; assert r['family']==s['family']==m['family'];assert r['n']==s['n']==m['n'];assert r['model']==protocol['model'];assert r['max_buffer']==protocol['maximum_buffer'];close(s['support_fraction'],m['support_points']/m['n'])
 assert s['label_sha256']==m['label_member_sha256'];assert s['score_sha256']==scorehash[r['series']]
 assert set(r['methods'])==set(protocol['methods'])
 for method,v in r['methods'].items():
  assert v['method']==method;assert v['status'] in ('COMPLETE','TIMEOUT');assert v['n']==r['n'];assert v['label_sha256']==s['label_sha256'];assert v['score_sha256']==s['score_sha256'];assert v['threads']==1
  assert all(t['num_threads']==1 for t in v['threadpool_info'])
  target=m['sampled250'] if method=='dtaianomaly250' else m['exact']
  for i,c in enumerate(v['calls']):
   assert c['repeat']==i;num(c['seconds']);assert c['seconds']>0;assert len(c['result'])==2
   for value in c['result']: num(value)
   error=max(abs(a-b) for a,b in zip(c['result'],target));close(error,c['target_error']);errors.append(error);assert error<=protocol['parity_tolerance']
  if v['status']=='COMPLETE':
   assert len(v['calls'])==3;assert all(c['seconds']<=protocol['per_call_budget_seconds'] for c in v['calls']);close(v['median_seconds'],statistics.median(c['seconds'] for c in v['calls']))
  else:
   assert 'median_seconds' not in v;assert v['budget_seconds']==10;assert v['elapsed_to_termination_request']>=10;timeouts.append({'series':r['series'],'family':r['family'],'method':method,'completed_calls':len(v['calls'])})
comparison={}
for method in protocol['methods']:
 c=[r for r in rows if r['methods'][method]['status']=='COMPLETE'];p=[r for r in c if r['methods']['sparse_numba']['status']=='COMPLETE'];ratios=[r['methods'][method]['median_seconds']/r['methods']['sparse_numba']['median_seconds'] for r in p]
 recomputed={'complete':len(c),'timeout':len(rows)-len(c),'paired_complete':len(p),'median_ratio_on_complete_pairs':statistics.median(ratios),'min_ratio_on_complete_pairs':min(ratios),'max_ratio_on_complete_pairs':max(ratios)}
 assert recomputed==summary['comparisons'][method];comparison[method]=recomputed
close(max(errors),summary['max_error'])
# Independent mechanism checks from per-call nanoseconds rather than stored medians.
mech=load(A/'mechanism_results.json');receipt=load(A/'mechanism_results/run_receipt.json');mr=lines(A/'mechanism_results/raw_cases.jsonl');mp=load(A/'mechanism_protocol.json');valid=load(A/'mechanism_results/validation.json')
assert mech['status']==receipt['status']=='complete';hashes(mech['source_sha256']);assert mech['source_sha256']==receipt['source_sha256'];assert sha(A/'mechanism_protocol.json')==mech['protocol_sha256']==receipt['protocol_sha256']
assert {r['case_id']:r for r in mech['rows']}=={r['case_id']:r for r in mr};assert mech['summary']==receipt['summary'];assert len(mr)==112
expectedcells={(n,d,k,w) for n in mp['n'] for d in mp['positive_label_densities'] for k in mp['positive_interval_counts'] for w in mp['max_buffer'] if k<=round(n*d)}
assert {(r['n'],r['positive_label_density'],r['intervals'],r['max_buffer']) for r in mr}==expectedcells;assert len({r['case_id'] for r in mr})==112
merrors=[];ratios=collections.defaultdict(list)
methods={'sparse_numba','fullsort_sparse_numba','dense_numpy','dense_numba','dense_direct_numba'}
for r in mr:
 assert r['preparation_arrays_equal'];assert len(r['receipts'])==15;dur=collections.defaultdict(list);first=r['receipts'][0]['value'];re=[]
 for repeat in range(3):
  calls=[c for c in r['receipts'] if c['repetition']==repeat];assert {c['method'] for c in calls}==methods;assert {c['order_position'] for c in calls}==set(range(5))
 for c in r['receipts']:
  assert type(c['elapsed_ns']) is int and c['elapsed_ns']>0;dur[c['method']].append(c['elapsed_ns']/1e9)
  for value in c['value']:num(value)
  error=max(abs(a-b) for a,b in zip(first,c['value']));close(error,c['error_vs_first']);re.append(error)
 med={k:statistics.median(v) for k,v in dur.items()}
 for k,v in med.items():close(v,r['median_seconds'][k]);assert dur[k]==r['seconds'][k]
 dense=min(med[k] for k in methods if k.startswith('dense'))
 rr={'speedup_current_vs_fullsort':med['fullsort_sparse_numba']/med['sparse_numba'],'speedup_current_vs_fastest_dense':dense/med['sparse_numba'],'speedup_fullsort_vs_fastest_dense':dense/med['fullsort_sparse_numba']}
 for k,v in rr.items():close(v,r[k]);ratios[k].append(v)
 close(max(re),r['max_parity_error']);merrors.extend(re)
ms={}
for key,values in ratios.items():
 stats={'count':len(values),'geometric_mean':math.exp(statistics.mean(map(math.log,values))),'median':statistics.median(values),'minimum':min(values),'maximum':max(values),'material_wins':sum(v>mp['reporting']['material_win_ratio'] for v in values),'material_losses':sum(v<mp['reporting']['material_loss_ratio'] for v in values)}
 for k,v in stats.items():close(v,mech['summary']['ratios'][key][k])
 ms[key]=stats
assert mech['summary']['timed_calls']==len(merrors)==1680;close(max(merrors),mech['summary']['max_parity_error']);assert max(merrors)<=mp['tolerance']['absolute']
assert valid['status']=='passed' and valid['cases']==101 and valid['preparation_arrays_equal'];assert receipt['environment']['numba_threads']==1;assert all(x['num_threads']==1 for x in receipt['environment']['threadpool_info'])
result={'status':'PASS','reviewer':'independent automated review agent, same session','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'external':{'rows':len(rows),'families':len(family),'comparisons':comparison,'max_error_recomputed':max(errors),'timeout_details':timeouts,'source_and_input_hashes_match':True,'selection_recomputed':True},'mechanism':{'rows':len(mr),'timed_calls':len(merrors),'max_error_recomputed':max(merrors),'ratios':ms,'full_grid_coverage':True,'source_hashes_match':True,'raw_rows_equal_summary_rows':True},'scope':'Stdlib-only record recomputation, data identity and hash audit; no kernels rerun, no timed experiments repeated.'}
(A/'independent_supplement_review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
