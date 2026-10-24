import copy
import importlib.util
from pathlib import Path
import sys
import pytest


def module():
    path=Path(__file__).resolve().parents[1]/'experiments/audit_pvldb_klein_control.py'
    sys.path.insert(0,str(path.parent));spec=importlib.util.spec_from_file_location('klein_audit',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixture():
    methods=['released','stream','klein_support','external']
    p={'methods':methods,'orders':[methods],'workflow_orders':[methods]}
    cases=[{'series':'a','family':'NAB'}];reference={'a':[.2,.4]};labels={'a':'one'}
    rows=[{'series':'a','family':'NAB','method':m,'trial':0,'seconds':t,'values':[.2,.4],'winners':[1],'pr_error':0.}
          for m,t in zip(methods,[2.,1.,4.,8.])]
    wf=[{'family':'NAB','method':r['method'],'trial':0,'seconds':r['seconds'],
         'decisions':[{'series':'a','values':[.2,.4],'winners':[1]}]} for r in rows]
    return p,cases,rows,wf,reference,labels


def test_simple_patch_and_compiled_algorithm_are_distinct_comparisons():
    r=module().reconstruct(*fixture())['collections']['NAB']
    assert r['case_comparisons']['external_over_control']['geometric_speedup']==2.
    assert r['case_comparisons']['control_over_released']['geometric_speedup']==2.
    assert r['workflow_comparisons']['control_over_stream']['median_ratio']==4.


@pytest.mark.parametrize('mutation',['missing','duplicate','nonfinite','wrong_values','wrong_winners',
                                    'wrong_family','wrong_error','wrong_workflow','extra_decision'])
def test_ablation_corruption_is_rejected(mutation):
    p,c,rows,wf,ref,labels=copy.deepcopy(fixture())
    if mutation=='missing':rows.pop()
    if mutation=='duplicate':rows.append(copy.deepcopy(rows[0]))
    if mutation=='nonfinite':rows[0]['seconds']=float('nan')
    if mutation=='wrong_values':rows[0]['values'][0]=.5
    if mutation=='wrong_winners':rows[0]['winners']=[0]
    if mutation=='wrong_family':rows[0]['family']='SMD'
    if mutation=='wrong_error':rows[0]['pr_error']=.1
    if mutation=='wrong_workflow':wf[0]['decisions'][0]['values'][0]=.7
    if mutation=='extra_decision':wf[0]['decisions'].append(copy.deepcopy(wf[0]['decisions'][0]))
    with pytest.raises(ValueError):module().reconstruct(p,c,rows,wf,ref,labels)


def test_reference_extraction_rejects_missing_duplicate_or_wrong_axes():
    row={'series':'a','method':'released','trial':0,'width':30,'values':[.2,.4]}
    extract=module().reference_vectors
    assert extract([row],{'a'},2,30)=={'a':[.2,.4]}
    for rows in ([],[row,row],[{**row,'values':[.2]}],[{**row,'values':[.2,float('nan')]}]):
        with pytest.raises(ValueError):extract(rows,{'a'},2,30)
