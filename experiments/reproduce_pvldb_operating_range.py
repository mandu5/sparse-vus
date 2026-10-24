"""Fresh long-recording/controlled follow-up; keeps frozen evidence untouched."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from reproduce_pvldb20261024 import ROOT,EVIDENCE,ARCHIVE_SHA,sha,prepare_workspace


def same_design(reference,actual):
    if {k:v for k,v in reference.items() if k!='created_utc'}!={k:v for k,v in actual.items() if k!='created_utc'}:
        raise ValueError('follow-up design drift')


def run(args):
    dest=prepare_workspace(args.output)
    for name in ('pvldb_operating_range.py','audit_pvldb_operating_range.py'):
        shutil.copy2(ROOT/'experiments'/name,dest/'experiments'/name)
    archive=args.archive
    if archive is None and (ROOT/'cache/TSB-AD-U.zip').exists():archive=ROOT/'cache/TSB-AD-U.zip'
    target=dest/'cache/TSB-AD-U.zip';target.parent.mkdir()
    if archive is None:
        subprocess.run(['curl','-fL','--retry','2','--max-time','900','https://www.thedatum.org/datasets/TSB-AD-U.zip','-o',str(target)],check=True)
    else:target.symlink_to(Path(archive).resolve())
    if sha(target)!=ARCHIVE_SHA:raise ValueError('archive identity')
    env=dict(os.environ);env['PYTHONPATH']=str(dest/'src')
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMBA_NUM_THREADS'):env[key]='1'
    def call(name,*arguments):subprocess.run([sys.executable,str(dest/'experiments'/name),*map(str,arguments)],cwd=dest,env=env,check=True)
    for name in ('fast_vus_adapter.py','benchopt_vus_adapter.py'):call(name,'--fetch')
    call('pvldb_full_precision.py','freeze')
    call('pvldb_operating_range.py','freeze')
    relative=EVIDENCE/'operating-range';folder=dest/relative
    same_design(json.loads((ROOT/relative/'protocol.json').read_text()),json.loads((folder/'protocol.json').read_text()))
    receipt={'status':'RUNNING','started_utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
             'python':sys.version,'fresh_scores':True,'protocol_sha256':sha(folder/'protocol.json')}
    (folder/'reproduction-start.json').write_text(json.dumps(receipt,indent=2)+'\n')
    call('pvldb_operating_range.py','generate');call('pvldb_operating_range.py','run')
    call('audit_pvldb_operating_range.py','--root',dest,'--output',folder/'independent-report.json')
    receipt.update(status='COMPLETE',completed_utc=datetime.now(timezone.utc).isoformat(),audit_sha256=sha(folder/'independent-report.json'))
    (folder/'reproduction-complete.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--archive',type=Path)
    run(parser.parse_args())
