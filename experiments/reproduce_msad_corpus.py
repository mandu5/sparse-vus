"""Reacquire the frozen MSAD corpus into a fresh ignored cache, with byte checks."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def require(value,message):
    if not value:raise ValueError(message)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while b:=f.read(1<<20):h.update(b)
    return h.hexdigest()


def repo_file(root,relative):
    relative=Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts,'Invalid repository-relative source path')
    path=Path(root)/relative
    require(Path(root).resolve() in path.resolve().parents,'Bound source escapes repository')
    return path


def load_bound_manifest(path,expected,*,root=ROOT):
    path=Path(path)
    require(digest(path)==expected,'Public manifest SHA256 mismatch')
    manifest=json.loads(path.read_text())
    protocol_path=path.parent/'protocol.json'
    require(digest(protocol_path)==manifest['protocol_sha256'],'Bound protocol changed')
    protocol=json.loads(protocol_path.read_text())
    require(manifest['status']=='INPUTS_VERIFIED_NO_METRIC_OUTCOMES' and manifest['metric_outcomes_computed'] is False,'Invalid acquisition status')
    require(len(manifest['series'])==manifest['series_count'] and len(manifest['models'])==len(set(manifest['models']))==12,'Manifest coverage mismatch')
    require(manifest['score_vectors']==12*manifest['series_count'],'Manifest score coverage mismatch')
    require(len({r['series'] for r in manifest['series']})==manifest['series_count'],'Duplicate manifest case')
    for relative,sha in protocol['source_sha256'].items():
        require(digest(repo_file(root,relative))==sha,'Frozen source changed: '+relative)
    for relative,sha in protocol['metadata_sha256'].items():
        require(digest(path.parent/relative)==sha,'Frozen corpus metadata changed: '+relative)
    return manifest,protocol


def reserve_cache(root,relative):
    root=Path(root).resolve();relative=Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts and relative.parts and relative.parts[0]=='.cache','Output must be below ignored .cache')
    target=root/relative;shared=(root/'.cache').resolve()
    require(shared in target.resolve().parents,'Output escapes ignored cache root')
    require(not target.exists(),'Reproduction cache must be new')
    (target/'members').mkdir(parents=True,exist_ok=False)
    (target/'arrays').mkdir()
    return target


def selected_rows(manifest,limit):
    if limit is None:return manifest['series']
    require(1<=limit<=len(manifest['series']),'Limit must select a nonempty bounded prefix')
    return manifest['series'][:limit]


def verify_arrays(arrays,row,acq):
    require(set(arrays)==set(row['array_sha256']),'Array key coverage differs')
    require(len(arrays['labels'])==row['n'] and int(arrays['labels'].sum())==row['positive_points'],'Label count mismatch')
    for key,expected in row['array_sha256'].items():
        require(acq.array_sha(arrays[key])==expected,'Regenerated array identity differs: '+key)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=ROOT/'artifacts/msad-corpus-20261023/manifest.json')
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--cache',required=True,help='New repository-relative ignored .cache path')
    parser.add_argument('--limit',type=int,help='Explicit smoke-test prefix; omitted reproduces every selected case')
    args=parser.parse_args()
    manifest,protocol=load_bound_manifest(args.manifest,args.manifest_sha256)
    rows=selected_rows(manifest,args.limit)
    cache=reserve_cache(ROOT,args.cache)
    spec=importlib.util.spec_from_file_location('frozen_msad_acquisition',ROOT/'experiments/fetch_msad_score_corpus.py')
    acq=importlib.util.module_from_spec(spec);spec.loader.exec_module(acq)
    require(tuple(manifest['models'])==acq.MODELS,'Model order differs from frozen source')
    acq.CACHE=cache
    candidates=json.loads((args.manifest.parent/'candidate-queue.json').read_text())
    reader=acq.Ranges()
    reproduced=[]
    started=datetime.now(timezone.utc).isoformat()
    with ThreadPoolExecutor(max_workers=12) as pool:
        for row in rows:
            candidate=candidates[row['candidate_index']]
            require(candidate['family']+'/'+candidate['series']==row['series'],'Candidate queue identity mismatch')
            raw,receipt=acq.get_member(reader,candidate['raw'])
            require(receipt['sha256']==row['raw']['sha256'],'Original observation/label member changed')
            fetched=list(pool.map(lambda m:acq.get_member(reader,candidate['scores'][m]),acq.MODELS))
            for model,result in zip(acq.MODELS,fetched):
                require(result[1]['sha256']==row['scores'][model]['sha256'],'Original stored-score member changed: '+model)
            arrays=acq.parse_case(raw,{m:f[0] for m,f in zip(acq.MODELS,fetched)})
            verify_arrays(arrays,row,acq)
            path=cache/'arrays'/f"{row['candidate_index']:04d}.npz"
            with path.open('xb') as stream:np.savez_compressed(stream,**arrays)
            reproduced.append({'series':row['series'],'candidate_index':row['candidate_index'],
                'npz_path':path.relative_to(ROOT).as_posix(),'npz_sha256':digest(path),
                'original_npz_bytes_equal':digest(path)==row['npz_sha256'],
                'all_member_and_array_hashes_match':True})
            print(json.dumps({'reproduced':len(reproduced),'requested':len(rows),'series':row['series']}),flush=True)
    receipt={'status':'PASS_ALL_REQUESTED_MEMBER_AND_ARRAY_IDENTITIES','started_utc':started,
        'completed_utc':datetime.now(timezone.utc).isoformat(),'manifest_sha256':args.manifest_sha256,
        'protocol_sha256':manifest['protocol_sha256'],'source_series':len(manifest['series']),
        'requested_series':len(rows),'reproduced_series':len(reproduced),
        'full_selected_corpus_reproduced':len(rows)==len(manifest['series']),
        'score_vectors':len(reproduced)*len(acq.MODELS),'array_count':len(reproduced)*(len(acq.MODELS)+2),
        'metric_outcomes_computed':False,'expected_range_response_bytes':reader.bytes,
        'series':reproduced}
    acq.write_new(cache/'reproduction.json',receipt)
    print(json.dumps({'status':receipt['status'],'complete_corpus':receipt['full_selected_corpus_reproduced'],
        'receipt':str(cache/'reproduction.json'),'receipt_sha256':digest(cache/'reproduction.json')}),flush=True)


if __name__=='__main__':main()
