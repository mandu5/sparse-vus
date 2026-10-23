"""Independent stored-text/array audit. Does not import acquisition or metrics."""
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zlib
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/msad-corpus-20261023'
CACHE=ROOT/'.cache/msad-corpus-20261023'

def sha_bytes(value):return hashlib.sha256(value).hexdigest()
def digest(path):return sha_bytes(Path(path).read_bytes())
def need(condition,message):
    if not condition:raise AssertionError(message)
def array_sha(a):
    b=np.ascontiguousarray(a)
    header=json.dumps({'dtype':b.dtype.str,'shape':list(b.shape)},sort_keys=True).encode()
    return sha_bytes(header+b'\0'+b.tobytes())

def member(receipt):
    data=(CACHE/'members'/(sha_bytes(receipt['path'].encode())+'.data')).read_bytes()
    need(len(data)==receipt['bytes'],'Member byte length changed')
    need(sha_bytes(data)==receipt['sha256'],'Member SHA changed')
    need(zlib.crc32(data)==receipt['crc32'],'Member CRC changed')
    return data

manifest=json.loads((OUT/'manifest.json').read_text())
protocol=json.loads((OUT/'protocol.json').read_text())
need(digest(OUT/'protocol.json')==manifest['protocol_sha256'],'Protocol binding')
for p,v in protocol['source_sha256'].items():need(digest(ROOT/p)==v,'Source binding '+p)
for p,v in protocol['metadata_sha256'].items():need(digest(OUT/p)==v,'Metadata binding '+p)
need(digest(OUT/'acquisition.jsonl')==manifest['acquisition_log_sha256'],'Acquisition log changed')
log=[json.loads(line) for line in (OUT/'acquisition.jsonl').read_text().splitlines()]
completed=[r for r in log if r['status'] in ('ACCEPTED','EXCLUDED')]
need([r['candidate_index'] for r in completed]==list(range(completed[-1]['candidate_index']+1)),'Fixed queue prefix changed')
need([r['input'] for r in completed if r['status']=='ACCEPTED']==manifest['series'],'Log/manifests differ')
need(len(manifest['series'])==manifest['series_count']==128,'Series coverage')
need(len(manifest['models'])==12 and manifest['score_vectors']==1536,'Model coverage')
prior=json.loads((OUT/'prior-identity-index.json').read_text())['entries']
old={}
for line in (ROOT/'artifacts/public_benchmark.jsonl').read_text().splitlines():
    r=json.loads(line);old[r['series']]=r['label_member_sha256']
need(sum(r['source']=='prior-tsb-ad' for r in prior)==350,'Prior TSB coverage')
need(all(old[r['series']]==r['raw_sha256'] for r in prior if r['source']=='prior-tsb-ad'),'Prior TSB raw provenance')
prior_labels={r['label_hash'] for r in prior}
new_labels=set()
counts={'raw_members':0,'score_members':0,'array_members':0,'time_positions':0,'score_scalars':0}
for i,row in enumerate(manifest['series']):
    need(digest(ROOT/row['npz_path'])==row['npz_sha256'],'NPZ byte identity')
    raw=member(row['raw']);counts['raw_members']+=1
    matrix=np.array([[float(v) for v in values] for values in csv.reader(io.StringIO(raw.decode('utf-8')))],dtype=np.float64)
    need(matrix.ndim==2 and matrix.shape==(row['n'],2),'Independent raw shape')
    need(np.isfinite(matrix).all() and np.isin(matrix[:,1],[0.,1.]).all(),'Independent raw validity')
    independent={'observations':matrix[:,0].copy(),'labels':matrix[:,1].astype(np.int8)}
    need(array_sha(independent['labels']) not in prior_labels|new_labels,'Duplicate label identity')
    new_labels.add(array_sha(independent['labels']))
    with np.load(ROOT/row['npz_path'],allow_pickle=False) as arrays:
        need(set(arrays.files)==set(row['array_sha256'])=={'observations','labels',*manifest['models']},'NPZ key coverage')
        for model in manifest['models']:
            payload=member(row['scores'][model]);counts['score_members']+=1
            values=np.fromiter((float(line) for line in payload.splitlines()),dtype=np.float64)
            need(values.ndim==1 and len(values)==row['n'] and np.isfinite(values).all(),'Independent score validity')
            need(np.array_equal(values,arrays[model]),'Independent score parse differs: '+row['series']+'/'+model)
            need(array_sha(values)==row['array_sha256'][model],'Score hash differs')
            counts['score_scalars']+=len(values);counts['array_members']+=1
        for name,values in independent.items():
            need(np.array_equal(values,arrays[name]),'Independent raw parse differs')
            need(array_sha(values)==row['array_sha256'][name],'Raw array hash differs')
            counts['array_members']+=1
    counts['time_positions']+=row['n']
    if (i+1)%16==0:print(json.dumps({'audited_series':i+1,**counts}),flush=True)
result={'status':'PASS_INDEPENDENT_STORED_TEXT_TO_ARRAY_IDENTITIES','source_sha256':digest(__file__),
    'manifest_sha256':digest(OUT/'manifest.json'),'protocol_sha256':manifest['protocol_sha256'],
    'series':128,'models':manifest['models'],'families':manifest['families'],'counts':counts,
    'prior_raw_provenance_checked':350,'prior_identity_rows':len(prior),'fixed_candidate_prefix_checked':len(completed),
    'exclusion_count':sum(r['status']=='EXCLUDED' for r in completed),
    'parser':'Python csv.reader and scalar float; NumPy only for arrays, membership, and container IO',
    'scope':'Verifies original stored member hashes/CRC, independent raw/score text parsing, arrays, prior source hashes, queue and receipts; no VUS or model-ranking outcome.',
    'metric_outcomes_computed':False}
with (OUT/'independent-input-audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
