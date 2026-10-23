"""Acquisition must preserve bytes, complete-model coverage, and disjointness."""
import importlib.util
import io
from pathlib import Path
import struct
import zipfile
import numpy as np
import pytest

@pytest.fixture
def acq():
    p = Path(__file__).resolve().parents[1] / 'experiments/fetch_msad_score_corpus.py'
    assert p.exists(), 'MSAD acquisition module is not implemented'
    spec = importlib.util.spec_from_file_location('msad_acq_test', p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def archive_bytes():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('TSB/data/A/a.out', '1,0\n2,1\n3,0\n')
    return stream.getvalue()

def test_central_directory_and_member_crc(acq):
    raw = archive_bytes()
    rows, info = acq.read_directory(lambda a,b: raw[a:b+1], len(raw))
    assert len(rows) == 1 and rows[0]['path'] == 'TSB/data/A/a.out'
    row = rows[0]
    assert acq.decode_member(raw[row['offset']:], row) == b'1,0\n2,1\n3,0\n'
    broken = {**row, 'crc32': row['crc32'] ^ 1}
    with pytest.raises(ValueError, match='CRC'):
        acq.decode_member(raw, broken)

def test_central_directory_rejects_duplicate_paths(acq):
    stream = io.BytesIO()
    with pytest.warns(UserWarning):
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('x', 'one'); z.writestr('x', 'two')
    raw=stream.getvalue()
    with pytest.raises(ValueError, match='Duplicate'):
        acq.read_directory(lambda a,b: raw[a:b+1],len(raw))

def test_member_header_name_must_match_frozen_identity(acq):
    raw=archive_bytes();rows,_=acq.read_directory(lambda a,b:raw[a:b+1],len(raw))
    with pytest.raises(ValueError, match='name'):
        acq.decode_member(raw,{**rows[0],'path':'TSB/data/A/b.out'})

def test_parse_preserves_published_scores_and_rejects_missing_models(acq):
    data=b'2,0\n4,1\n6,0\n'; scores={m:b'0.01\n0.01\n0.02\n' for m in acq.MODELS}
    arrays=acq.parse_case(data,scores)
    assert arrays['labels'].dtype==np.int8
    np.testing.assert_array_equal(arrays['AE'],[.01,.01,.02])
    with pytest.raises(ValueError,match='model'):
        acq.parse_case(data,{k:v for k,v in scores.items() if k!='AE'})

@pytest.mark.parametrize('data,score',[(b'2,0\n4,0\n',b'0.1\n0.2\n'),(b'2,0\n4,1\n',b'0.1\n'),(b'2,0\n4,1\n',b'nan\n0.1\n'),(b'2,0\n4,2\n',b'0.1\n0.2\n')])
def test_invalid_arrays_are_rejected_without_repair(acq,data,score):
    with pytest.raises(ValueError):acq.parse_case(data,{m:score for m in acq.MODELS})

def test_array_hash_includes_shape_dtype_and_standardization(acq):
    assert acq.array_sha(np.array([1,2],dtype='i8'))!=acq.array_sha(np.array([1,2],dtype='f8'))
    assert acq.array_sha(np.array([[1.,2.]]))!=acq.array_sha(np.array([1.,2.]))
    assert acq.observation_hashes(np.array([1.,2.,4.]))[1]==acq.observation_hashes(np.array([12.,14.,18.]))[1]

def test_round_robin_is_metadata_deterministic_and_requires_all_models(acq):
    rows=[]
    for family in ('A','B'):
        for filename in ('a.out','b.out','bad.train.out'):
            rows.append({'path':f'TSB/data/{family}/{filename}','bytes':100})
            for model in acq.MODELS:
                if family=='B' and filename=='b.out' and model=='AE':continue
                rows.append({'path':f'TSB/scores/{family}/{model}/score/{filename}','bytes':50})
    candidates=acq.candidate_queue(rows)
    assert len(candidates)==3 and [c['family'] for c in candidates[:2]]==['A','B']
    assert candidates==acq.candidate_queue(list(reversed(rows)))
    assert not any('.train.' in x['series'] for x in candidates)

def test_prior_raw_path_retains_family_subdirectory(acq):
    row={'family':'CalIt2','series':'CalIt2_traffic_test'}
    assert acq.external_raw_path(row).relative_to(acq.ROOT).as_posix()=='cache/saturation-external/raw/CalIt2/CalIt2_traffic_test.csv'
