"""Development-only exploratory probe. Never reads holdout series."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMBA_NUM_THREADS'):
    os.environ[name]='1'
import sys,json,time,statistics,hashlib,platform
from pathlib import Path
import numpy as np
import numba
from prototype import prepare_radix,sparse_pr_radix,ROOT
from sparse_vus.core import _prepare,sparse_vus
from sparse_vus.pr_compiled import sparse_pr_jit
sys.path.insert(0,str(ROOT/'experiments'))
from benchmark_advancement import Corpus,corpus_rows
from threadpoolctl import threadpool_limits
numba.set_num_threads(1);threadpool_limits(1)
OUT=Path('/tmp/vus-radix-20261021')
rng=np.random.default_rng(12971920261021)
names=['labels','scores','starts','ends','pos','original','d1','d2','group','before','after','support_index']
checks=0
metric_checks=0
max_error=0.
fixtures=[]
special=np.array([-np.finfo(float).max,-1.,-np.finfo(float).tiny,-np.nextafter(0.,1.),-0.,0.,np.nextafter(0.,1.),np.finfo(float).tiny,1.,np.finfo(float).max])
for seed in range(80):
    n=int(rng.integers(2,257)); y=(rng.random(n)<rng.choice([.01,.2,.8])).astype(np.int8);y[0],y[-1]=0,1
    s=(rng.normal(size=n) if seed%4==0 else rng.integers(-3,4,n).astype(float))
    if seed%4==2: s=rng.choice(special,n)
    if seed%4==3:
        raw=np.zeros(n*2);raw[::2]=s;s=raw[::2]
    width=int(rng.choice([0,1,2,3,30,300]))
    fixtures.append((y,s,width))
fixtures += [(np.array([0,1]),np.array([-0.,0.]),0),
             (np.array([0,1]),np.array([0.,-0.]),2),
             (np.array([0,1,0,1,0]),np.array([1,0,1,0,1],dtype='>f8'),5)]
for y,s,width in fixtures:
    expected=_prepare(y,s,width)
    before_y,before_s=y.copy(),s.copy()
    for mode in ('counting','u16','u64_timsort'):
        actual=prepare_radix(y,s,width,mode)
        for name,a,b in zip(names,expected,actual):
            np.testing.assert_array_equal(a,b,err_msg=f'{name} mode={mode}, n={len(y)}, width={width}')
        checks+=1
        if len(y)<90:
            value=sparse_pr_radix(y,s,width,mode)
            reference=sparse_pr_jit(y,s,width)
            max_error=max(max_error,abs(value-reference));assert abs(value-reference)<1e-13
            metric_checks+=1
    np.testing.assert_array_equal(y,before_y);np.testing.assert_array_equal(s,before_s)
# Freeze the six largest n among the already selected 42 development series.
meta=json.loads((ROOT/'artifacts/external_supplement_selection.json').read_text())
selected=sorted(meta,key=lambda r:(-r['n'],r['series']))[:6]
series={r['series'] for r in selected}
rows=[r for r in corpus_rows('baseline') if r['series'] in series and r['max_buffer']==30]
rows=sorted(rows,key=lambda r:(r['series'],r['model']))
assert len(rows)==18
(OUT/'protocol.json').write_text(json.dumps({'scope':'Exploratory only; six largest development series by existing metadata, all 3 models, width30; no holdout', 'selection':selected,'cases':len(rows),'repetitions':3,'seed':12971920261021,'methods':['current','counting','u16','u64_timsort'],'no_publishable_timing_claim':True},indent=2)+'\n')
corpus=Corpus();records=[]
methods={'current':sparse_pr_jit,'counting':lambda y,s,w:sparse_pr_radix(y,s,w,'counting'), 'u16':lambda y,s,w:sparse_pr_radix(y,s,w,'u16'),'u64_timsort':lambda y,s,w:sparse_pr_radix(y,s,w,'u64_timsort')}
# All method compilation happens before data timing.
y=np.array([0,1,0,0,1,0],dtype=np.int8);s=np.array([1.,-0.,0.,2.,-1.,3.])
for fn in methods.values():fn(y,s,30)
for row in rows:
    y,s=corpus.load(row)
    reference=_prepare(y,s,30)
    for mode in ('counting','u16','u64_timsort'):
        actual=prepare_radix(y,s,30,mode)
        for name,a,b in zip(names,reference,actual):np.testing.assert_array_equal(a,b,err_msg=f'{row["series"]}/{row["model"]}: {name}')
        checks+=1
    timings={m:[] for m in methods};values={}
    for rep in range(3):
        order=list(methods);rng.shuffle(order)
        for name in order:
            t=time.perf_counter();v=methods[name](y,s,30);timings[name].append(time.perf_counter()-t);values[name]=float(v)
    for name,v in values.items():
        error=abs(v-values['current']);max_error=max(max_error,error);assert error<1e-12
        metric_checks+=1
    med={k:statistics.median(v) for k,v in timings.items()}
    rec={'series':row['series'],'model':row['model'],'n':len(y),'Q':len(reference[4]),'G':len(reference[10]),'width':30,'pr':values,'seconds':timings,'median_seconds':med,'speedup_vs_current':{k:med['current']/v for k,v in med.items() if k!='current'}}
    records.append(rec)
    print(row['series'],row['model'],rec['speedup_vs_current'],flush=True)
summary={}
for method in ('counting','u16','u64_timsort'):
    speeds=[r['speedup_vs_current'][method] for r in records]
    summary[method]={'median_speedup':statistics.median(speeds),'min_speedup':min(speeds),'max_speedup':max(speeds),'wins':sum(s>1 for s in speeds),'sum_case_medians_current':sum(r['median_seconds']['current'] for r in records),'sum_case_medians_candidate':sum(r['median_seconds'][method] for r in records)}
result={'status':'PASS','numpy':np.__version__,'numba':numba.__version__,'platform':platform.platform(),'array_parity_fixtures':checks,'metric_checks':metric_checks,'max_metric_error':max_error,'summary':summary,'records':records,'prototype_sha256':hashlib.sha256((OUT/'prototype.py').read_bytes()).hexdigest(),'no_publishable_timing_claim':True}
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
