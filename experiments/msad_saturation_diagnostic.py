"""Exploratory attribution after the primary MSAD results were observed.

Insert the exact first saturation threshold (at most one per width) into the
same sampled grid. This is a diagnostic intervention, not a new runtime claim.
All twelve models on all eight prespecified-primary harmful cases are retained.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from sparse_vus.core import expanded_ranges
from sparse_vus.radix import _prepare_radix, sparse_pr_radix_jit
from sparse_vus.sampling import _prepare_sampled, sampled_pr_radix_jit
from sparse_vus.sampling_bounds import _integer_states, _sqrt_bracket

OUT = ROOT/"artifacts/msad-saturation-diagnostic-20261023"
MANIFEST = ROOT/"artifacts/msad-corpus-20261023/manifest.json"
EXTRACTION = ROOT/"artifacts/msad-sampling-20261023/primary-signed-error-extraction.json"


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def diagnose(y, scores, L=30, H=250):
    (y, _, starts, ends, pos, original, d1, d2, group, _, after, _) = _prepare_radix(y, scores, L)
    counts = _prepare_sampled(y, scores, L, H)[9]
    A = np.cumsum(np.bincount(group, weights=original, minlength=len(after)))
    p0 = int(y.sum())
    rows = []
    for w in range(L+1):
        weights = original.astype(float)
        if w >= 2:
            active = (~original) & (d1 <= w//2)
            weights[active] = np.sqrt(1-d1[active]/w)
            weights[(~original) & (d2 <= w//2)] = 1.
        B = np.cumsum(np.bincount(group, weights=weights*(~original), minlength=len(after)))
        T = A+B
        lo, hi = expanded_ranges(starts, ends, len(y), w)
        first = np.array([np.min(group[np.searchsorted(pos,a):np.searchsorted(pos,b,side='right')]) for a,b in zip(lo,hi)])
        hits = np.cumsum(np.bincount(first, minlength=len(after)))
        R = np.minimum(T/(p0+B/2), 1)*hits/len(lo)
        exact = float(np.dot(np.diff(np.r_[0., R]), T/after))
        sat = int(np.flatnonzero(R == 1.)[0])
        sat_count = int(after[sat])
        def integral(cc):
            jj = np.searchsorted(after, cc, side='right')-1
            rr, tt = np.r_[0., R][jj+1], np.r_[0., T][jj+1]
            return float(np.dot(np.diff(np.r_[0., rr]), tt/cc)), jj, rr
        sampled, jj, rr = integral(counts)
        inserted = integral(np.unique(np.r_[counts, sat_count]))[0]
        ib = int(np.searchsorted(counts, sat_count))
        b = int(jj[ib]); cb = int(counts[ib])
        remaining = 1-(float(rr[ib-1]) if ib else 0.)
        buffer_term = remaining*float(B[b]-B[sat])/cb
        original_term = remaining*float(A[b]-A[sat])/cb
        dilution = -remaining*float(T[sat])*(cb-sat_count)/(cb*sat_count)
        tail = buffer_term+original_term+dilution
        assert abs((sampled-inserted)-tail) < 3e-13
        # Independently enclose both sides of the saturation stopping test.
        radius = min(w//2, len(y)-1)
        rl, rh = np.zeros(radius+1, dtype=np.int64), np.zeros(radius+1, dtype=np.int64)
        rl[0] = rh[0] = 1 << 32
        for d in range(1, radius+1): rl[d],rh[d] = _sqrt_bracket(w,d)
        ia,bl,bh,ih,kk = _integer_states(len(y),starts,ends,pos,original,d1,d2,group,len(after),w,rl,rh,1<<32)
        saturated = int(ih[sat]) == kk and int(bl[sat]) >= 2*(p0-int(ia[sat]))*(1<<32)
        before = sat == 0 or int(ih[sat-1]) < kk or int(bh[sat-1]) < 2*(p0-int(ia[sat-1]))*(1<<32)
        rows.append({'width':w,'exact':exact,'sampled':sampled,'saturation_inserted':inserted,
                     'total_error':sampled-exact,'post_saturation_change':tail,
                     'remaining_pre_saturation_error':inserted-exact,
                     'post_saturation_buffer_mass_term':buffer_term,
                     'post_saturation_original_mass_term':original_term,
                     'post_saturation_count_dilution_term':dilution,
                     'saturation_global_count':sat_count,'next_sampled_global_count':cb,
                     'first_saturation_index_integer_verified':bool(saturated and before)})
    means = {k:float(np.mean([r[k] for r in rows])) for k in rows[0] if k not in
             ('width','saturation_global_count','next_sampled_global_count','first_saturation_index_integer_verified')}
    assert abs(means['exact']-sparse_pr_radix_jit(y,scores,L)) < 3e-12
    assert abs(means['sampled']-sampled_pr_radix_jit(y,scores,L,H)) < 3e-12
    return {'means':means,'all_saturation_indices_integer_verified':all(r['first_saturation_index_integer_verified'] for r in rows),'per_width':rows}


def main():
    extraction = json.loads(EXTRACTION.read_text())
    manifest = json.loads(MANIFEST.read_text())
    ids = [r['series'] for r in extraction['harmful_cases']]
    assert len(ids) == 8
    OUT.mkdir(exist_ok=False)
    protocol = {'kind':'Exploratory mechanism attribution AFTER observing primary results',
                'created_utc':datetime.now(timezone.utc).isoformat(),
                'selection':'All eight cases meeting frozen primary best-case regret >=.01, all twelve models; not a prevalence estimate',
                'series':ids,'models':manifest['models'],'width':30,'thresholds':250,
                'intervention':'Insert first exact saturation threshold separately at every width, at most one extra retained threshold',
                'decomposition':'sampled-exact = (sampled-saturation_inserted)+(saturation_inserted-exact); first term splits admitted buffer, original mass and count dilution',
                'extraction_sha256':digest(EXTRACTION),'manifest_sha256':digest(MANIFEST),
                'sources':{p:digest(ROOT/p) for p in ['experiments/msad_saturation_diagnostic.py','src/sparse_vus/sampling_bounds.py','src/sparse_vus/sampling.py','src/sparse_vus/core.py','src/sparse_vus/radix.py','src/sparse_vus/pr_compiled.py']}}
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    # Constructed singleton witness: adding its saturation event recovers exact.
    n,q,m = 2491,10,3
    y=np.zeros(n,dtype=np.int8); y[0]=1
    order=np.r_[np.arange(n-m,n),np.arange(n-m)]
    scores=np.empty(n); scores[order]=np.arange(n,0,-1)
    witness=diagnose(y,scores)
    assert abs(witness['means']['saturation_inserted']-.25) < 1e-14
    assert witness['all_saturation_indices_integer_verified']
    (OUT/'constructed-control.json').write_text(json.dumps(witness,indent=2)+'\n')
    records=[]
    with (OUT/'records.jsonl').open('x') as stream:
        for row in manifest['series']:
            if row['series'] not in ids: continue
            p=ROOT/row['npz_path']
            if digest(p)!=row['npz_sha256']: raise ValueError('Input hash changed')
            with np.load(p,allow_pickle=False) as arrays:
                for model in manifest['models']:
                    result=diagnose(arrays['labels'],arrays[model])
                    record={'series':row['series'],'family':row['family'],'model':model,'npz_sha256':row['npz_sha256'],**result}
                    stream.write(json.dumps(record,allow_nan=False)+'\n');stream.flush();records.append(record)
            print(row['series'],flush=True)
    decisions=[]
    for sid in ids:
        rr=[r for r in records if r['series']==sid]
        sets={}
        for key in ('exact','sampled','saturation_inserted'):
            best=max(r['means'][key] for r in rr)
            sets[key]=sorted(r['model'] for r in rr if best-r['means'][key]<=1e-10)
        decisions.append({'series':sid,'winner_sets':sets})
    report={'protocol_sha256':digest(OUT/'protocol.json'),'records_sha256':digest(OUT/'records.jsonl'),
            'count':len(records),'all_saturation_indices_integer_verified':all(r['all_saturation_indices_integer_verified'] for r in records),
            'decisions':decisions,'scope':'Exploratory followup on selected harmful cases; diagnostic is not a faster algorithm or independent prevalence estimate'}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
