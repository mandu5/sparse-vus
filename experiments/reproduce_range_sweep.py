"""Fresh data-to-table reproduction of the separately frozen range successor."""
import argparse
from datetime import datetime,timezone
import json
import importlib.metadata
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from reproduce_pvldb20261024 import ROOT,EVIDENCE,ARCHIVE_SHA,prepare_workspace,same_design,same_supplement_design,sha

SCRIPTS=['range_sweep_study.py','audit_range_sweep_study.py','range_sweep_public.py',
         'audit_range_sweep_public.py','range_sweep_validation.py','pvldb_consumer.py']


def run(args):
    dest=prepare_workspace(args.output)
    for name in SCRIPTS:shutil.copy2(ROOT/'experiments'/name,dest/'experiments'/name)
    for rel in ('public-consumer/protocol.json','range-sweep/timesead-sources.json'):
        target=dest/EVIDENCE/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/EVIDENCE/rel,target)
    (dest/'cache').mkdir()
    archive=args.archive or (ROOT/'cache/TSB-AD-U.zip' if (ROOT/'cache/TSB-AD-U.zip').exists() else None)
    target=dest/'cache/TSB-AD-U.zip'
    if archive is None:
        subprocess.run(['curl','-fL','--retry','2','--max-time','900','https://www.thedatum.org/datasets/TSB-AD-U.zip','-o',str(target)],check=True)
    else:target.symlink_to(Path(archive).resolve())
    if sha(target)!=ARCHIVE_SHA:raise ValueError('raw data identity')
    env=dict(os.environ)
    env['PYTHONOPTIMIZE']='0'
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):env[key]='1'
    env['PYTHONPATH']=str(dest/'src')
    def call(name,*arguments):
        subprocess.run([sys.executable,str(dest/'experiments'/name),*map(str,arguments)],cwd=dest,env=env,check=True)
    def audit(name,relative):
        with (dest/EVIDENCE/relative).open('x') as f:
            subprocess.run([sys.executable,str(dest/'experiments'/name)],cwd=dest,env=env,stdout=f,check=True)
    for name in ('fast_vus_adapter.py','benchopt_vus_adapter.py'):call(name,'--fetch')
    call('pvldb_full_precision.py','freeze')
    same_design(json.loads((ROOT/EVIDENCE/'full-precision/protocol.json').read_text()),json.loads((dest/EVIDENCE/'full-precision/protocol.json').read_text()))
    processor=platform.processor()
    if Path('/proc/cpuinfo').exists():
        processor=next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),processor)
    receipt={'status':'RUNNING','utc':datetime.now(timezone.utc).isoformat(),
             'platform':platform.platform(),'machine':platform.machine(),'processor':processor,'logical_cpus':os.cpu_count(),
             'packages':{k:importlib.metadata.version(k) for k in ('numpy','numba','scipy','pandas','scikit-learn','torch')},
             'host_note':'One serial numerical process; public hosted-runner background load is not controlled.',
             'include_vus':args.include_vus,
             'scope':'Fresh raw download, 73-case score generation, range main/public/validation and numerical JSON audits; optional original VUS primary/supplement; source/semantic design matches, host-dependent scores/timings may differ.'}
    (dest/EVIDENCE/'range-reproduction-start.json').write_text(json.dumps(receipt,indent=2)+'\n')
    call('pvldb_full_precision.py','generate')
    if args.include_vus:
        call('pvldb_full_precision.py','run')
        call('audit_pvldb20261024.py','--root',dest,'--output',dest/EVIDENCE/'full-precision/independent-audit.json')
        call('pvldb_supplement.py','freeze')
        olds=json.loads((ROOT/EVIDENCE/'supplement/protocol.json').read_text())
        news=json.loads((dest/EVIDENCE/'supplement/protocol.json').read_text())
        same_supplement_design(olds,news)
        if news['primary_protocol_sha256']!=sha(dest/EVIDENCE/'full-precision/protocol.json') or news['inputs_sha256']!=sha(dest/EVIDENCE/'full-precision/inputs.json'):raise ValueError('supplement parent binding')
        call('pvldb_supplement.py','run')
        call('audit_pvldb_supplement.py','--root',dest,'--output',dest/EVIDENCE/'supplement/independent-report.json')
    call('range_sweep_study.py','freeze')
    original=json.loads((ROOT/EVIDENCE/'range-sweep/main-study/protocol.json').read_text())
    fresh=json.loads((dest/EVIDENCE/'range-sweep/main-study/protocol.json').read_text())
    ignore={'utc','inputs_sha256','primary_protocol_sha256'}
    if {k:v for k,v in original.items() if k not in ignore}!={k:v for k,v in fresh.items() if k not in ignore}:raise ValueError('range design drift')
    call('range_sweep_study.py','run')
    audit('audit_range_sweep_study.py','range-sweep/main-study/independent-report.json')
    call('range_sweep_public.py','freeze')
    oldp=json.loads((ROOT/EVIDENCE/'range-sweep/public-study-v2/protocol.json').read_text())
    newp=json.loads((dest/EVIDENCE/'range-sweep/public-study-v2/protocol.json').read_text())
    ignore={'utc','inputs_sha256','main_protocol_sha256','cases'}
    if {k:v for k,v in oldp.items() if k not in ignore}!={k:v for k,v in newp.items() if k not in ignore}:raise ValueError('public design drift')
    if [(c['series'],c['n']) for c in oldp['cases']]!=[(c['series'],c['n']) for c in newp['cases']]:raise ValueError('public cohort drift')
    call('range_sweep_public.py','run')
    audit('audit_range_sweep_public.py','range-sweep/public-study-v2/independent-report.json')
    call('range_sweep_validation.py','freeze')
    oldv=json.loads((ROOT/EVIDENCE/'range-sweep/validation/protocol.json').read_text())
    newv=json.loads((dest/EVIDENCE/'range-sweep/validation/protocol.json').read_text())
    ignore={'utc','records_sha256','inputs_sha256'}
    if {k:v for k,v in oldv.items() if k not in ignore}!={k:v for k,v in newv.items() if k not in ignore}:raise ValueError('validation design drift')
    if newv['records_sha256']!=sha(dest/EVIDENCE/'range-sweep/main-study/records.jsonl') or newv['inputs_sha256']!=sha(dest/EVIDENCE/'full-precision/inputs.json'):raise ValueError('validation parent binding')
    call('range_sweep_validation.py','run')
    reports=['range-sweep/main-study/independent-report.json','range-sweep/public-study-v2/independent-report.json','range-sweep/validation/report.json']
    if args.include_vus:reports+=['full-precision/independent-audit.json','supplement/independent-report.json']
    receipt.update(status='COMPLETE',completed_utc=datetime.now(timezone.utc).isoformat(),
        reports={p:sha(dest/EVIDENCE/p) for p in reports})
    (dest/EVIDENCE/'range-reproduction-complete.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--archive',type=Path)
    parser.add_argument('--include-vus',action='store_true',help='Also reproduce original VUS primary and supplement on the same fresh score arrays.')
    run(parser.parse_args())
