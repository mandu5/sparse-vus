"""Consumer-boundary parity against the installed, pinned public TimeEval API.

These catch changed threshold eligibility, sampler endpoints, floating recall
plateau ordering, native constant/error handling, and accidental source mutation.
They use only tiny arrays; no performance assertions or real workload timings.
"""
import warnings

import numpy as np
import pytest

timeeval = pytest.importorskip('timeeval')
from timeeval import DefaultMetrics
from timeeval.metrics import RangePrecisionRangeRecallAUC


@pytest.mark.parametrize('method', ['raster', 'bucket'])
@pytest.mark.parametrize('case', ['ties','plateaus','all_positive','minimum_subnormal','float32'])
def test_native_curve_and_scalar_preserved(method, case):
    from sparse_vus.timeeval_adapter import adapt_range_metric
    if case == 'ties':
        y = np.array([0,1,1,0,0,1,0,1], np.int64)
        x = np.array([0,0,1,1,2,2,3,3], float)
    elif case == 'plateaus':
        y = np.array([1,1,1,0,0,0,1,1,1,1,1,0,0,0,0,1,1,0,0], np.int64)
        x = np.array([17,1,7,2,3,4,16,8,6,14,9,5,10,11,12,15,13,0,18], float)
    elif case == 'all_positive':
        y = np.ones(12, np.int64)
        x = np.array([0,11,1,10,2,9,3,8,4,7,5,6], float)
    elif case == 'minimum_subnormal':
        y = np.array([0,1,0,1,0,1], np.int64)
        x = np.array([-1.,-0.,0.,np.nextafter(0.,1.),1.,2.])
    else:
        y = np.array([0,1,1,0,1,0,1,0], np.int64)
        x = np.array([0,.1,.1,.2,.4,.3,.2,.5], np.float32)
    source = DefaultMetrics.RANGE_PR_AUC
    adapted = adapt_range_metric(source, method)
    expected = source._range_precision_recall_curve(y,x)
    actual = adapted._range_precision_recall_curve(y,x)
    np.testing.assert_array_equal(actual[2], expected[2])
    np.testing.assert_allclose(actual[:2], expected[:2], rtol=0, atol=2e-7 if x.dtype==np.float32 else 1e-12)
    assert adapted(y,x) == pytest.approx(source(y,x), abs=1e-10, rel=0)
    assert source._range_precision_recall_curve.__func__.__module__ == 'timeeval.metrics.range_metrics'


@pytest.mark.parametrize('method', ['raster', 'bucket'])
@pytest.mark.parametrize('n,want', [(12,[1.,4.,7.,10.,11.]),(11,[1.,4.,7.,10.])])
def test_source_sampler_can_exceed_requested_cap_and_keeps_last(method,n,want):
    from sparse_vus.timeeval_adapter import adapt_range_metric
    source=RangePrecisionRangeRecallAUC(max_samples=4,r_alpha=0,cardinality='one')
    metric=adapt_range_metric(source,method)
    y=np.arange(n)%2;x=np.arange(n,dtype=float)
    np.testing.assert_array_equal(metric._range_precision_recall_curve(y,x)[2],want)
    assert metric(y,x)==pytest.approx(source(y,x),abs=1e-10,rel=0)


@pytest.mark.parametrize('method', ['raster','bucket'])
@pytest.mark.parametrize('labels', [[0,1,0,1],[0,0,0,0],[1,1,1,1]])
def test_constant_score_uses_native_zero_before_curve_or_label_error(method,labels):
    from sparse_vus.timeeval_adapter import adapt_range_metric
    metric=adapt_range_metric(DefaultMetrics.RANGE_PR_AUC,method)
    with pytest.warns(UserWarning,match='constant'):
        assert metric(np.array(labels),np.ones(4)) == 0.


@pytest.mark.parametrize('method', ['raster','bucket'])
def test_no_positive_nonconstant_labels_preserve_native_assertion(method):
    from sparse_vus.timeeval_adapter import adapt_range_metric
    y=np.zeros(4,np.int64);x=np.arange(4,dtype=float)
    with pytest.raises(AssertionError):DefaultMetrics.RANGE_PR_AUC(y,x)
    with pytest.raises(AssertionError):adapt_range_metric(DefaultMetrics.RANGE_PR_AUC,method)(y,x)


@pytest.mark.parametrize('method', ['raster','bucket'])
def test_maximum_threshold_keeps_prediction_and_empty_terminal_is_synthetic(method):
    from sparse_vus.timeeval_adapter import adapt_range_metric
    y=np.array([0,1,0,1]);x=np.array([0.,1.,1.,2.])
    p,r,t=adapt_range_metric(DefaultMetrics.RANGE_PR_AUC,method)._range_precision_recall_curve(y,x)
    np.testing.assert_array_equal(t,[1.,2.])
    # Native >=2 retains the final true point; appending (1,0) is separate.
    np.testing.assert_allclose(p,[.5,2/3,1,1],atol=1e-15,rtol=0)
    np.testing.assert_allclose(r,[1,1,.5,0],atol=1e-15,rtol=0)


@pytest.mark.parametrize('method', ['raster','bucket'])
def test_public_validation_and_nonfinite_score_sanitization_remain_active(method):
    from sparse_vus.timeeval_adapter import adapt_range_metric
    y=np.array([0,1,0,1,0,1]);x=np.array([np.nan,np.inf,-np.inf,.2,.5,.8])
    actual=adapt_range_metric(DefaultMetrics.RANGE_PR_AUC,method)(y,x)
    assert actual==pytest.approx(DefaultMetrics.RANGE_PR_AUC(y,x),abs=1e-10,rel=0)
    with pytest.raises(ValueError,match='floats'):
        adapt_range_metric(DefaultMetrics.RANGE_PR_AUC,method)(y,np.arange(6))


@pytest.mark.parametrize('method', ['raster','bucket'])
def test_small_fragmented_profiles_do_not_reorder_recall_plateaus(method):
    from sparse_vus.timeeval_adapter import adapt_range_metric
    rng=np.random.default_rng(202610240907)
    metric=adapt_range_metric(DefaultMetrics.RANGE_PR_AUC,method)
    for _ in range(18):
        n=int(rng.integers(9,54));y=rng.integers(0,2,n);y[0]=0;y[-1]=1
        x=rng.integers(-4,9,n).astype(float)
        a=metric._range_precision_recall_curve(y,x)
        b=DefaultMetrics.RANGE_PR_AUC._range_precision_recall_curve(y,x)
        np.testing.assert_allclose(a[:2],b[:2],atol=1e-12,rtol=0)
        assert metric(y,x)==pytest.approx(DefaultMetrics.RANGE_PR_AUC(y,x),abs=1e-10,rel=0)


def test_nondefault_range_semantics_are_not_silently_changed():
    from sparse_vus.timeeval_adapter import adapt_range_metric
    with pytest.raises(ValueError,match='native default'):
        adapt_range_metric(DefaultMetrics.FIXED_RANGE_PR_AUC,'bucket')


@pytest.mark.parametrize('method',['raster','bucket'])
def test_all_observed_contract_keeps_every_nonminimum_score(method):
    from sparse_vus.timeeval_adapter import adapt_range_metric
    y=(np.arange(111)%7<3).astype(np.int64)
    x=np.random.default_rng(71).permutation(111).astype(float)
    source=RangePrecisionRangeRecallAUC(max_samples=float('inf'),r_alpha=0,cardinality='one')
    adapted=adapt_range_metric(source,method)
    a=adapted._range_precision_recall_curve(y,x)
    b=source._range_precision_recall_curve(y,x)
    np.testing.assert_array_equal(a[2],np.arange(1.,111.))
    assert len(DefaultMetrics.RANGE_PR_AUC._range_precision_recall_curve(y,x)[2])<110
    np.testing.assert_allclose(a[:2],b[:2],atol=1e-12,rtol=0)
    assert adapted(y,x)==pytest.approx(source(y,x),abs=1e-10,rel=0)


def _tiny_native_layout(root):
    """Actual CSV layout reached by the public consumer, with three families."""
    import csv
    data=root/'datasets';results=root/'results'
    data.mkdir(parents=True);results.mkdir()
    index=[];rows=[]
    for family in ('A','B','C'):
        for model in ('FFT','COPOD'):
            case=family+'-tiny';relative=family+'/'+case+'.csv'
            p=data/relative;p.parent.mkdir(exist_ok=True)
            p.write_text('timestamp,value,is_anomaly\n'+''.join(
                f'{i},{i/8},{v}\n' for i,v in enumerate([0,1,1,0,0,1,0,0])))
            if model=='FFT':index.append(dict(collection_name=family,dataset_name=case,
                                             test_path=relative,train_path=''))
            q=results/model/'tiny'/family/case/'1';q.mkdir(parents=True)
            np.savetxt(q/'anomaly_scores.ts',np.array([0.,3.,2.,1.,1.,4.,0.,2.]),fmt='%.17g')
            rows.append(dict(algorithm=model,hyper_params_id='tiny',collection=family,
                             dataset=case,repetition=1,status='Status.OK'))
    for path,records in [(data/'datasets.csv',index),(results/'results.csv',rows)]:
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    return root


def test_runner_validation_executes_native_default_three_and_preserves_template(tmp_path):
    import hashlib
    import json
    from pathlib import Path
    import subprocess
    import sys
    root=Path(__file__).resolve().parents[1]
    source=root/'.cache/strengthening-timeeval-full'
    if not source.exists():pytest.skip('pinned native source cache is optional')
    workload=_tiny_native_layout(tmp_path/'workload');out=tmp_path/'validation'
    before=hashlib.sha256((workload/'results/results.csv').read_bytes()).hexdigest()
    result=subprocess.run([sys.executable,str(root/'scripts/run_timeeval_strengthening.py'),
        'validate','--workload',str(workload),'--source',str(source),'--out',str(out)],
        text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    receipt=json.loads((out/'complete.json').read_text())
    assert receipt['status']=='TINY_NATIVE_CONSUMER_VALIDATED'
    assert receipt['row_count']==6
    assert receipt['contracts']==['native_default50','all_observed']
    assert receipt['methods']==['public','raster','bucket']
    assert receipt['timing_performed'] is False
    assert hashlib.sha256((workload/'results/results.csv').read_bytes()).hexdigest()==before


def test_runner_refuses_timing_before_global_freeze(tmp_path):
    import hashlib
    import json
    from pathlib import Path
    import subprocess
    import sys
    root=Path(__file__).resolve().parents[1]
    protocol=tmp_path/'draft.json';protocol.write_text(json.dumps({'status':'DRAFT','timeeval_consumer':{}}))
    out=tmp_path/'attempt'
    result=subprocess.run([sys.executable,str(root/'scripts/run_timeeval_strengthening.py'),
        'run','--protocol',str(protocol),'--protocol-sha256',hashlib.sha256(protocol.read_bytes()).hexdigest(),
        '--out',str(out)],text=True,capture_output=True,timeout=15)
    assert result.returncode!=0
    failure=json.loads((out/'failure.json').read_text())
    assert 'FROZEN' in failure['error']
    assert not (out/'trials.jsonl').exists()


def _runner():
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'scripts/run_timeeval_strengthening.py'
    spec=importlib.util.spec_from_file_location('_test_native_consumer_runner',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_workflow_deadline_escapes_native_exception_guard_and_restores_handler():
    import signal
    import time
    runner=_runner()
    handler=signal.getsignal(signal.SIGALRM)
    with pytest.raises(runner.WorkflowTimeout):
        with runner.deadline(.02):
            try:
                time.sleep(.1)
            except Exception:
                pytest.fail('native-style broad Exception handler swallowed the deadline')
    assert signal.getsignal(signal.SIGALRM)==handler
    assert signal.getitimer(signal.ITIMER_REAL)[0]==0


def test_summaries_keep_contracts_separate_and_do_not_fabricate_censored_intervals():
    runner=_runner();records=[]
    payload={'batches':[{'name':'combined'}]}
    for contract in runner.CONTRACTS:
        for repeat in range(6):
            for method,seconds in [('public',12.),('raster',6.),('bucket',3.)]:
                if contract=='all_observed' and method=='public':
                    status='TIMEOUT' if repeat==0 else 'notrun_due_to_prespecified_censor'
                    record=dict(contract=contract,batch='combined',round=repeat,method=method,status=status)
                    if repeat==0:record.update(seconds=600.01,completion_seconds_lower_bound=600)
                else:
                    record=dict(contract=contract,batch='combined',round=repeat,method=method,
                                status='COMPLETE',seconds=seconds)
                records.append(record)
    actual=runner.summarize(records,payload)
    default=actual['native_default50']['combined']['comparisons']['public_over_bucket']
    assert default['completed_paired_rounds']==6
    assert default['geometric_speedup']==pytest.approx(4.)
    assert default['approximate_paired_order_ci95']==pytest.approx([4.,4.])
    exact=actual['all_observed']['combined']['comparisons']['public_over_bucket']
    assert exact['completed_paired_rounds']==0
    assert exact['paired_speedups']==[]
    assert exact['approximate_paired_order_ci95'] is None
    assert 'geometric_speedup' not in exact
    assert exact['censored_bounds']==[{'round':0,'strict_speedup_lower_bound':200.}]
    assert actual['all_observed']['combined']['status_counts']=={
        'COMPLETE':12,'TIMEOUT':1,'notrun_due_to_prespecified_censor':5}
    compiled=actual['all_observed']['combined']['comparisons']['raster_over_bucket']
    assert compiled['completed_paired_rounds']==6
    assert compiled['geometric_speedup']==pytest.approx(2.)


def test_added_native_metric_cache_is_a_binding_change(tmp_path):
    runner=_runner();workload=_tiny_native_layout(tmp_path/'workload')
    initial=runner.input_hashes(workload)
    metric_cache=next((workload/'results').rglob('anomaly_scores.ts')).with_name('metrics.csv')
    metric_cache.write_text('RANGE_PR_AUC\n0.5\n')
    assert runner.input_hashes(workload)!=initial
    assert str(metric_cache.relative_to(workload)) in runner.input_hashes(workload)


def test_output_audit_rejects_native_swallowed_metric_failures(tmp_path):
    import pandas as pd
    runner=_runner();workload=_tiny_native_layout(tmp_path/'workload')
    rows=runner.workload_rows(workload);path=tmp_path/'result.csv'
    rows.to_csv(path,index=False)
    with pytest.raises(ValueError,match='omitted'):
        runner.audit_output(path,rows)
    for metric in runner.METRICS:rows[metric]=.5
    rows.loc[0,'RANGE_PR_AUC']=np.nan
    rows.to_csv(path,index=False)
    with pytest.raises(ValueError,match='nonfinite'):
        runner.audit_output(path,rows)


def test_generation_receipts_bind_native_score_files(tmp_path):
    import json
    runner=_runner();workload=_tiny_native_layout(tmp_path/'workload')
    rows=runner.workload_rows(workload)
    profiles=[]
    for row in rows.itertuples(index=False):
        score=workload/'results'/row.algorithm/row.hyper_params_id/row.collection/row.dataset/str(row.repetition)/'anomaly_scores.ts'
        profiles.append({'model':row.algorithm,'case_id':row.dataset,'status':'Status.OK',
                         'native_score_sha256':runner.digest(score)})
    generation=tmp_path/'generation.json'
    generation.write_text(json.dumps({'status':'ALL_SELECTED_PROFILES_GENERATED',
        'metric_evaluation_performed':False,'selected_profiles':6,'successful_profiles':6,
        'profiles':profiles,'native_layout':{
            'datasets_sha256':runner.digest(workload/'datasets/datasets.csv'),
            'results_sha256':runner.digest(workload/'results/results.csv')}}))
    audit=tmp_path/'audit.json'
    audit.write_text(json.dumps({'status':'NATIVE_INPUTS_VERIFIED_WITHOUT_METRIC_EVALUATION',
        'metric_evaluation_performed':False,'profiles_verified':6,
        'generation_sha256':runner.digest(generation)}))
    bindings=runner.workload_receipts(workload,rows,generation,audit)
    assert bindings['generation']['sha256']==runner.digest(generation)
    next((workload/'results').rglob('anomaly_scores.ts')).write_text('0\n')
    with pytest.raises(ValueError,match='native score differs'):
        runner.workload_receipts(workload,rows,generation,audit)


def test_nominal_50_query_plan_records_actual_source_counts_without_metrics(tmp_path):
    runner=_runner();workload=_tiny_native_layout(tmp_path/'workload')
    rows=runner.workload_rows(workload)
    plan=runner.query_plan(workload,rows)
    assert len(plan)==6
    for profile in plan:
        assert profile['n']==8
        assert profile['distinct_scores']==5
        assert profile['constant_score_shortcut'] is False
        assert profile['contracts']['native_default50']['emitted_queries']==4
        assert profile['contracts']['all_observed']['emitted_queries']==4
    # A source-derived counterexample to treating max_samples as a hard cap.
    queries=runner.source_thresholds(np.arange(98,dtype=float),50)
    np.testing.assert_array_equal(queries,np.arange(1.,98.))
    np.testing.assert_array_equal(runner.source_thresholds(np.arange(98,dtype=float),float('inf')),queries)
