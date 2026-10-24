import importlib.util
from pathlib import Path
import sys

import pytest


def module():
    path=Path(__file__).resolve().parents[1]/'experiments/reproduce_pvldb_operating_range.py'
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location('operating_reproduce',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_fresh_timestamp_is_the_only_allowed_followup_design_change():
    p={'created_utc':'old','real_cases':[{'name':'MITDB','n':650000}],
       'controlled_cases':[{'n':100000,'positive_fraction':.5}],
       'source_sha256':{'kernel':'abc'},'seed':20261024,'parity_atol':1e-11,
       'real_methods':['released','stream'],'real_orders':[['released','stream']],
       'model_protocol':{'fit_points':2048},'failure_policy':'halt'}
    check=module().same_design
    check(p,{**p,'created_utc':'new'})
    for key,value in [('real_cases',[]),('controlled_cases',[]),('source_sha256',{'kernel':'changed'}),
                      ('real_methods',['stream']),('seed',3),('model_protocol',{'fit_points':4096}),
                      ('failure_policy','drop adverse cases')]:
        with pytest.raises(ValueError,match='design drift'):check(p,{**p,key:value})


def test_existing_followup_destination_is_preserved(tmp_path):
    path=tmp_path/'keep';path.mkdir();(path/'important').write_text('preserve')
    with pytest.raises(FileExistsError):module().prepare_workspace(path)
    assert (path/'important').read_text()=='preserve'
