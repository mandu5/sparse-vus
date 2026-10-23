"""A fresh-cache reproduction is bound to the public manifest, never local inputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest

@pytest.fixture
def rep():
    p=Path(__file__).resolve().parents[1]/'experiments/reproduce_msad_corpus.py'
    assert p.exists(), 'MSAD reproduction wrapper is not implemented'
    spec=importlib.util.spec_from_file_location('msad_reproduction_test',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value));return hashlib.sha256(path.read_bytes()).hexdigest()

def fixture_manifest(root):
    study=root/'artifacts/study';source=root/'experiments/source.py';source.parent.mkdir(parents=True);source.write_text('frozen')
    protocol={'source_sha256':{'experiments/source.py':hashlib.sha256(source.read_bytes()).hexdigest()},'metadata_sha256':{}}
    ph=write_json(study/'protocol.json',protocol)
    models=[str(i) for i in range(12)]
    manifest={'status':'INPUTS_VERIFIED_NO_METRIC_OUTCOMES','metric_outcomes_computed':False,'protocol_sha256':ph,'models':models,'series_count':1,'score_vectors':12,'series':[{'series':'A/a','candidate_index':0}]}
    mh=write_json(study/'manifest.json',manifest)
    return study/'manifest.json',mh

def test_manifest_and_frozen_source_are_both_verified(rep,tmp_path):
    path,expected=fixture_manifest(tmp_path)
    m,p=rep.load_bound_manifest(path,expected,root=tmp_path)
    assert m['series_count']==1 and p['source_sha256']
    with pytest.raises(ValueError,match='manifest'):
        rep.load_bound_manifest(path,'0'*64,root=tmp_path)
    (tmp_path/'experiments/source.py').write_text('changed')
    with pytest.raises(ValueError,match='source'):
        rep.load_bound_manifest(path,expected,root=tmp_path)

def test_cache_reservation_rejects_reuse_and_escaping_symlinks(rep,tmp_path):
    root=tmp_path/'repo';shared=tmp_path/'shared';outside=tmp_path/'outside'
    root.mkdir();shared.mkdir();outside.mkdir();(root/'.cache').symlink_to(shared,target_is_directory=True)
    p=rep.reserve_cache(root,'.cache/msad-reproduction/one')
    assert p.resolve()==shared/'msad-reproduction/one'
    with pytest.raises(ValueError):rep.reserve_cache(root,'.cache/msad-reproduction/one')
    (shared/'escape').symlink_to(outside,target_is_directory=True)
    with pytest.raises(ValueError):rep.reserve_cache(root,'.cache/escape/other')
    with pytest.raises(ValueError):rep.reserve_cache(root,'../other')

def test_array_identity_checks_every_model(rep):
    spec=importlib.util.spec_from_file_location('frozen_msad',Path(__file__).resolve().parents[1]/'experiments/fetch_msad_score_corpus.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    arrays={'labels':np.array([0,1,0],dtype='i1'),'observations':np.array([1.,2.,3.]),**{m:np.array([.1,.1,.2]) for m in a.MODELS}}
    row={'array_sha256':{k:a.array_sha(v) for k,v in arrays.items()},'n':3,'positive_points':1}
    rep.verify_arrays(arrays,row,a)
    arrays['AE']=np.array([.1,.2,.2])
    with pytest.raises(ValueError,match='AE'):rep.verify_arrays(arrays,row,a)

def test_limit_is_explicit_and_cannot_silently_mean_complete(rep):
    manifest={'series':[{'series':str(i)} for i in range(4)]}
    assert len(rep.selected_rows(manifest,None))==4
    assert len(rep.selected_rows(manifest,2))==2
    for bad in (0,5,-1):
        with pytest.raises(ValueError):rep.selected_rows(manifest,bad)
