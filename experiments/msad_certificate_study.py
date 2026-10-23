"""Frozen accuracy-only study of integer-directed VUS-PR certificates."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import statistics
import sys

os.environ.setdefault('NUMBA_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
MANIFEST=ROOT/'artifacts/msad-corpus-20261023/manifest.json'
MANIFEST_SHA='5617e4fdc0bb082ac910144212546e05cc009622e45b07b672e562a999e6bc59'
OUT=ROOT/'artifacts/msad-certificate-20261023'
SOURCES=['experiments/msad_certificate_study.py','src/sparse_vus/sampling.py',
         'src/sparse_vus/sampling_bounds.py','src/sparse_vus/core.py',
         'src/sparse_vus/radix.py','src/sparse_vus/pr_compiled.py',
         'src/sparse_vus/compiled.py','src/sparse_vus/__init__.py']


def now():return datetime.now(timezone.utc).isoformat()
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_new(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def read(path):return json.loads(Path(path).read_text())
def array_digest(a):
    a=np.ascontiguousarray(a)
    header=json.dumps({'dtype':a.dtype.str,'shape':list(a.shape)},sort_keys=True).encode()
    return hashlib.sha256(header+b'\0'+a.tobytes()).hexdigest()


def freeze():
    if digest(MANIFEST)!=MANIFEST_SHA:raise ValueError('Manifest hash changed')
    manifest=read(MANIFEST)
    assert manifest['series_count']==128 and len(manifest['models'])==12
    OUT.mkdir(exist_ok=False)
    protocol={'study':'msad-certificate-20261023','schema_version':1,
              'frozen_utc':now(),'freeze_status':'before this study reads any corpus metric outcome',
              'manifest':str(MANIFEST.relative_to(ROOT)),'manifest_sha256':MANIFEST_SHA,
              'series_count':128,'models':manifest['models'],'source_families':16,
              'width':30,'budgets':[250,1000],'primary_budget':250,'secondary_budget':1000,
              'target':'Ideal real-arithmetic original dynamic VUS-PR with exact sqrt weights',
              'certificate_method':'certified_sampled_pr','weight_bits':32,'output_bits':56,
              'sampled_method':'sampled_pr_radix_jit','reference_float_method':'sparse_pr_radix_jit',
              'sampled_winner_tolerance':1e-10,
              'winner_certificate':'One model lower endpoint strictly exceeds every other upper endpoint; Python integer cross products only',
              'sampled_set_regret_certificate':'max(model lower)-max(sampled-winner-set upper), clipped at zero; strict positivity certifies every approximate winner is suboptimal',
              'scalar_containment':'Fraction.from_float(exhaustive_float) in exact dyadic interval is informational only; not the certified target and no epsilon assertion',
              'coverage':'Every128series by12models atBOTH budgets; no selection based on outcomes',
              'aggregation':['pooled case counts','per family','equal-family rates'],
              'conditional_rate_scope':'Finite selected published-score corpus; no general population claim',
              'failure_policy':'Append failure record, retain denominator and continue; complete-case rates accompanied by attempted coverage',
              'timeout_seconds_per_model_budget':120,
              'timing':'No runtime measurements or timing claims in this study; ordinary run timestamps are provenance',
              'sources':{p:digest(ROOT/p) for p in SOURCES}}
    write_new(OUT/'protocol.json',protocol)
    (OUT/'ATTRIBUTION.md').write_text((ROOT/'artifacts/msad-corpus-20261023/ATTRIBUTION.md').read_text())
    print(digest(OUT/'protocol.json'))


def verified_protocol(expected=None):
    p=read(OUT/'protocol.json')
    ph=digest(OUT/'protocol.json')
    if expected is not None and ph!=expected:raise ValueError('Protocol hash mismatch')
    if digest(MANIFEST)!=p['manifest_sha256']:raise ValueError('Manifest changed')
    for f,h in p['sources'].items():
        if digest(ROOT/f)!=h:raise ValueError('Source changed: '+f)
    return p,ph


def timeout_handler(*_):raise TimeoutError('Frozen120second limit exceeded')


def run(expected):
    from fractions import Fraction
    from sparse_vus.sampling_bounds import certified_sampled_pr
    from sparse_vus.sampling import sampled_pr_radix_jit
    from sparse_vus.radix import sparse_pr_radix_jit
    p,ph=verified_protocol(expected)
    manifest=read(MANIFEST)
    records=OUT/'records.jsonl'
    done=set()
    if records.exists():
        for line in records.read_text().splitlines():
            r=json.loads(line);key=(r['series_index'],r['model'],r['budget'])
            if key in done or r['protocol_sha256']!=ph:raise ValueError('Conflicting prior records')
            done.add(key)
    if not (OUT/'run.json').exists():
        write_new(OUT/'run.json',{'started_utc':now(),'protocol_sha256':ph,
                                'python':sys.version,'numpy':np.__version__,
                                'platform':platform.platform(),'resume_supported':True})
    signal.signal(signal.SIGALRM,timeout_handler)
    with records.open('a') as stream:
        for index,row in enumerate(manifest['series']):
            verified_protocol(ph)
            source=ROOT/row['npz_path']
            if digest(source)!=row['npz_sha256']:raise ValueError('NPZ hash mismatch')
            with np.load(source,allow_pickle=False) as package:
                arrays={name:package[name] for name in ['labels']+p['models']}
            for name,a in arrays.items():
                if array_digest(a)!=row['array_sha256'][name]:raise ValueError('Array hash mismatch')
            y=arrays['labels']
            for model in p['models']:
                exact=None
                for budget in p['budgets']:
                    key=(index,model,budget)
                    if key in done:continue
                    record={'series_index':index,'series':row['series'],'family':row['family'],
                            'model':model,'n':row['n'],'width':p['width'],'budget':budget,
                            'protocol_sha256':ph,'npz_sha256':row['npz_sha256'],
                            'labels_sha256':row['array_sha256']['labels'],
                            'scores_sha256':row['array_sha256'][model]}
                    try:
                        signal.alarm(p['timeout_seconds_per_model_budget'])
                        scores=arrays[model]
                        if exact is None:exact=float(sparse_pr_radix_jit(y,scores,p['width']))
                        sampled=float(sampled_pr_radix_jit(y,scores,p['width'],budget))
                        cert=certified_sampled_pr(y,scores,p['width'],budget)
                        lo=Fraction(cert.lower_numerator,cert.scale);hi=Fraction(cert.upper_numerator,cert.scale)
                        exact_fraction=Fraction.from_float(exact)
                        record.update(status='ok',lower_numerator=str(cert.lower_numerator),
                                      upper_numerator=str(cert.upper_numerator),scale=str(cert.scale),
                                      lower_display=cert.lower,upper_display=cert.upper,
                                      thresholds_retained=cert.thresholds_retained,
                                      exhaustive_float=exact,sampled_float=sampled,
                                      float_reference_inside=lo<=exact_fraction<=hi,
                                      float_reference_outside_distance=float(max(lo-exact_fraction,exact_fraction-hi,0)))
                    except Exception as exc:
                        record.update(status='failed',exception_type=type(exc).__name__,error=str(exc))
                    finally:signal.alarm(0)
                    stream.write(json.dumps(record,allow_nan=False)+'\n');stream.flush();done.add(key)
            if (index+1)%8==0:print(f'Completed {index+1}/128 series',flush=True)
    verified_protocol(ph)
    write_new(OUT/'completion.json',{'completed_utc':now(),'protocol_sha256':ph,
                                   'record_count':len(done),'records_sha256':digest(records)})
    report()


def report():
    from fractions import Fraction
    p,ph=verified_protocol()
    completion=read(OUT/'completion.json')
    if digest(OUT/'records.jsonl')!=completion['records_sha256']:raise ValueError('Record hash mismatch')
    rows=[json.loads(line) for line in (OUT/'records.jsonl').read_text().splitlines()]
    keys=[(r['series_index'],r['model'],r['budget']) for r in rows]
    expected={(i,m,b) for i in range(128) for m in p['models'] for b in p['budgets']}
    if len(set(keys))!=len(keys) or set(keys)!=expected:raise ValueError('Unexpected/missing case coverage')
    groups=defaultdict(list)
    for r in rows:groups[(r['series_index'],r['budget'])].append(r)
    decisions=[]
    for (index,budget), rr in sorted(groups.items()):
        d={'series_index':index,'series':rr[0]['series'],'family':rr[0]['family'],'budget':budget}
        if any(r['status']!='ok' for r in rr):
            d.update(status='incomplete',failures=[r['model'] for r in rr if r['status']!='ok']);decisions.append(d);continue
        low={r['model']:Fraction(int(r['lower_numerator']),int(r['scale'])) for r in rr}
        high={r['model']:Fraction(int(r['upper_numerator']),int(r['scale'])) for r in rr}
        sample={r['model']:r['sampled_float'] for r in rr}
        floats={r['model']:r['exhaustive_float'] for r in rr}
        best=max(sample.values())
        winners=sorted(m for m,s in sample.items() if best-s<=p['sampled_winner_tolerance'])
        certified=[m for m in p['models'] if low[m]>max(high[o] for o in p['models'] if o!=m)]
        regret=max(Fraction(0),max(low.values())-max(high[m] for m in winners))
        d.update(status='complete',sampled_winner_set=winners,certified_unique_winner=certified,
                 sampled_unique_winner_certified=len(winners)==1 and certified==winners,
                 sampled_set_certifiably_suboptimal=regret>0,
                 regret_lower_numerator=str(regret.numerator),regret_lower_denominator=str(regret.denominator),
                 regret_lower_display=float(regret),
                 float_reference_best_case_regret=max(floats.values())-max(floats[m] for m in winners))
        decisions.append(d)
    bybudget={}
    for budget in p['budgets']:
        dr=[d for d in decisions if d['budget']==budget]
        good=[d for d in dr if d['status']=='complete']
        family={}
        for fam in sorted({d['family'] for d in dr}):
            fr=[d for d in dr if d['family']==fam];fc=[d for d in fr if d['status']=='complete']
            family[fam]={'attempted_series':len(fr),'complete_series':len(fc),
                         'certified_unique_winners':sum(bool(d['certified_unique_winner']) for d in fc),
                         'certified_sampled_unique_winners':sum(d['sampled_unique_winner_certified'] for d in fc),
                         'certified_suboptimal_sampled_sets':sum(d['sampled_set_certifiably_suboptimal'] for d in fc)}
        scalar=[r for r in rows if r['budget']==budget and r['status']=='ok']
        widths=[float(Fraction(int(r['upper_numerator'])-int(r['lower_numerator']),int(r['scale']))) for r in scalar]
        bybudget[str(budget)]={'attempted_series':len(dr),'complete_series':len(good),
            'successful_scalar_calls':len(scalar),'failed_scalar_calls':1536-len(scalar),
            'certified_unique_winners':sum(bool(d['certified_unique_winner']) for d in good),
            'certified_sampled_unique_winners':sum(d['sampled_unique_winner_certified'] for d in good),
            'certified_suboptimal_sampled_sets':sum(d['sampled_set_certifiably_suboptimal'] for d in good),
            'equal_family_certified_winner_fraction_attempted_denominator':statistics.mean(v['certified_unique_winners']/v['attempted_series'] for v in family.values()),
            'interval_width_median':statistics.median(widths) if widths else None,
            'interval_width_max':max(widths) if widths else None,
            'float_reference_outside_count_informational':sum(not r['float_reference_inside'] for r in scalar),
            'float_reference_max_outside_distance_informational':max([r['float_reference_outside_distance'] for r in scalar],default=None),
            'per_family':family}
    result={'status':'COMPLETE_ALL_DECLARED_CASES_RETAINED','protocol_sha256':ph,
            'records_sha256':digest(OUT/'records.jsonl'),'record_count':len(rows),
            'budgets':bybudget,'decisions':decisions,
            'scope':'Finite-corpus conditional certification; no runtime or universal effectiveness claim'}
    write_new(OUT/'report.json',result)
    print(json.dumps({'record_count':len(rows),'budgets':{k:{a:v for a,v in r.items() if a!='per_family'} for k,r in bybudget.items()}},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','run','report'])
    parser.add_argument('--protocol-sha256');args=parser.parse_args()
    if args.command=='freeze':freeze()
    elif args.command=='run':
        if not args.protocol_sha256:parser.error('--protocol-sha256 is required for run')
        run(args.protocol_sha256)
    else:report()
