import copy
import importlib.util
from pathlib import Path
import sys

import pytest


def module():
    path=Path(__file__).resolve().parents[1]/'experiments/audit_pvldb_operating_range.py'
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location('operating_audit',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixture():
    methods=['released','stream','dense','external','benchopt_pair','radix_pair']
    p={'real_methods':methods,'controlled_methods':methods[:4],
       'real_orders':[methods], 'controlled_orders':[methods[:4]],
       'workflow_orders':[methods], 'parity_atol':1e-11, 'winner_tie_atol':1e-10}
    cases=[{'name':'r','family':'MITDB','kind':'real','width':1,'n':4,'models':2},
           {'name':'c','family':'controlled','kind':'controlled','width':1,'n':4,'models':2}]
    rows=[];workflows=[];diagnostics=[]
    for c in cases:
        for method in methods if c['kind']=='real' else methods[:4]:
            roc=[.6,.7] if method.endswith('_pair') else None
            rows.append({'name':c['name'],'family':c['family'],'kind':c['kind'],
                         'method':method,'trial':0,'seconds':1.0 if method=='stream' else 2.,
                         'values':[.3,.4],'roc':roc,'winners':[1],
                         'pr_error':0.,'roc_error':0. if roc is not None else None})
            if c['kind']=='real':
                workflows.append({'family':'MITDB','method':method,'trial':0,'seconds':2.,
                                  'decisions':[{'name':'r','values':[.3,.4],'roc':roc,'winners':[1]}]})
        for model in range(2):
            diagnostics.append({'name':c['name'],'model':model,'values':{'pr':[.3,.4][model],'roc':[.6,.7][model]},
                                'Q':1,'K':1,'visited':[1,1],'active':[1,1]})
    metadata={c['name']:{'Q':1,'K':1,'active_by_width':[1,1],
                        'label_identity':c['name'],'score_distinct':[4,4],
                        'positive_points':1,'independent_visited':[[1,1],[1,1]]} for c in cases}
    return p,cases,rows,workflows,diagnostics,metadata


def test_complete_records_reconstruct_actual_ratios_and_single_case_scope():
    result=module().reconstruct(*fixture())
    assert result['cases']['r']['median_seconds']['stream']==1.
    assert result['cases']['r']['relative_to_stream']['external']['median_ratio']==2.
    assert result['collections']['MITDB']['case_inference']=='one fixed series; no population interval'


@pytest.mark.parametrize('mutation', ['missing','duplicate','nan_time','nan_value','wrong_winner',
                                    'wrong_family','wrong_roc','wrong_workflow','wrong_Q','extra_visit',
                                    'diagnostic_roc','zero_visits','recorded_pr_error'])
def test_corrupted_records_are_rejected(mutation):
    p,cases,rows,wf,diags,meta=copy.deepcopy(fixture())
    if mutation=='missing':rows.pop()
    elif mutation=='duplicate':rows.append(copy.deepcopy(rows[0]))
    elif mutation=='nan_time':rows[0]['seconds']=float('nan')
    elif mutation=='nan_value':rows[0]['values'][0]=float('nan')
    elif mutation=='wrong_winner':rows[0]['winners']=[0]
    elif mutation=='wrong_family':rows[0]['family']='SWaT'
    elif mutation=='wrong_roc':next(r for r in rows if r['method']=='benchopt_pair')['roc'][0]=.1
    elif mutation=='wrong_workflow':wf[0]['decisions'][0]['values'][0]=.2
    elif mutation=='wrong_Q':diags[0]['Q']=2
    elif mutation=='extra_visit':diags[0]['visited'][0]=2
    elif mutation=='diagnostic_roc':diags[1]['values']['roc']=.6
    elif mutation=='zero_visits':diags[0]['visited']=[0,0]
    elif mutation=='recorded_pr_error':rows[0]['pr_error']=1e-12
    with pytest.raises(ValueError):module().reconstruct(p,cases,rows,wf,diags,meta)


def test_support_geometry_handles_overlap_clipping_and_width_zero():
    m=module()
    assert m.support_counts([1,0,0,1,0],4)==[2,2,5,5,5]


def test_independent_visit_reconstruction_keeps_complete_ties_and_component_hits():
    import numpy as np
    m=module();y=np.array([0,0,1,0,0,0,0,1,0,0],np.int8)
    scores=np.array([[0,9,8,7,6,5,4,3,2,1],[1]*10],float)
    visited=m.independent_visits(y,scores,4)
    assert visited[0][:2]==[2,2]
    assert visited[1]==m.support_counts(y,4)
    # At width 4 both expanded intervals stay separate: the final low-scored
    # component still must be hit, even if enough weighted mass was predicted.
    assert visited[0][4]>=5
