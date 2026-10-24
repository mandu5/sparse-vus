"""Fresh raw-data/source-to-table replay of the weighted and native studies.

Install requirements-strengthening.txt and CPU torch2.10.0 first. This command
downloads checksum-bound sources/data, regenerates detector scores, freezes
per-host protocols, runs serial studies and audits. It never copies old scores.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
REL=Path('artifacts/pvldb-research-20261024/strengthening')
TIMEVAL_COMMIT='7c3622757b1a3afa9a84cbc97ce132d9e379f715'
RAW_SHA='0c47020d3423723c70773736dbd800369f2b487328becbf339450d1ae5020961'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def write(path,value):
    with Path(path).open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def download(url,path,expected=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['curl','-fL','--retry','2','--max-time','900',url,'-o',str(path)],check=True)
    actual=sha(path)
    if expected is not None and actual!=expected:raise ValueError('download identity '+url)
    return actual


def extract_native(archive,dest):
    dest.mkdir(exist_ok=False)
    with tarfile.open(archive) as tf:
        members=[]
        for member in tf.getmembers():
            parts=member.name.split('/',1)
            if len(parts)<2 or not parts[1]:continue
            member.name=parts[1]
            members.append(member)
        tf.extractall(dest,members=members,filter='data')


def verify_source_tree(root,expected):
    actual={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
    if actual!=expected:raise ValueError('native complete source tree identity differs')
    return len(actual)


def check_weighted_design(previous,current):
    ignore={'utc','inputs_sha256','cases'}
    if {k:v for k,v in previous.items() if k not in ignore}!={k:v for k,v in current.items() if k not in ignore}:
        raise ValueError('weighted study semantic/source design changed')
    def selected(p):
        return [(c['id'],c['family'],c['n'],c['model_order'],c['model_status']) for c in p['cases']]
    if selected(previous)!=selected(current):raise ValueError('cohort/model selection changed')


def run(args):
    dest=args.output.resolve();dest.mkdir(parents=True,exist_ok=False)
    out=dest/REL;out.mkdir(parents=True)
    for directory in ('src','experiments','scripts','tests'):
        shutil.copytree(ROOT/directory,dest/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for rel in ('source-discovery.json','provenance/source-manifest.json'):
        target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/REL/rel,target)
    original=Path('artifacts/pvldb-research-20261024/full-precision/protocol.json')
    (dest/original).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/original,dest/original)
    env=dict(os.environ)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
        env[key]='1'
    env['PYTHONPATH']=str(dest/'src');env['PYTHONOPTIMIZE']='0'
    def call(relative,*argv):
        subprocess.run([sys.executable,str(dest/relative),*map(str,argv)],cwd=dest,env=env,check=True)
    write(out/'reproduction-start.json',{'status':'RUNNING','utc':datetime.now(timezone.utc).isoformat(),
        'source_script_sha256':sha(Path(__file__)),
        'scope':'Fresh 26-case/52-profile generation and weighted/native consumer studies; no reused scores. Raw data are not redistributed.',
        'source_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()})
    source_manifest=json.loads((out/'provenance/source-manifest.json').read_text())
    for entry in source_manifest['files']:
        download(entry['url'],dest/entry['path'],entry['sha256'])
    manifest_path=dest/'.cache/strengthening-tsbad/source-manifest.json'
    shutil.copy2(out/'provenance/source-manifest.json',manifest_path)
    archive=dest/'cache/TSB-AD-U.zip';archive.parent.mkdir(parents=True)
    if args.archive:
        archive.symlink_to(args.archive.resolve())
        if sha(archive)!=RAW_SHA:raise ValueError('raw archive identity')
    else:download('https://www.thedatum.org/datasets/TSB-AD-U.zip',archive,RAW_SHA)
    tar=dest/'.cache/strengthening-timeeval-full.tar.gz'
    transport_sha=download(f'https://codeload.github.com/TimeEval/TimeEval/tar.gz/{TIMEVAL_COMMIT}',tar)
    native=dest/'.cache/strengthening-timeeval-full';extract_native(tar,native)
    mac_native=json.loads((ROOT/REL/'timeeval-consumer-global-v1.json').read_text())['timeeval_consumer']
    # GitHub may regenerate compression/container bytes for the same commit.
    # Verify every extracted file, including an exact file set, before execution.
    count=verify_source_tree(native,mac_native['source_sha256'])
    write(out/'native-source-acquisition.json',{'revision':TIMEVAL_COMMIT,
        'transport_sha256':transport_sha,'transport_bytes':tar.stat().st_size,
        'source_files_verified':count,'source_tree_equals_frozen_mac':True,
        'frozen_manifest_sha256':sha(ROOT/REL/'timeeval-consumer-global-v1.json')})
    if importlib.util.find_spec('pip'):
        install=[sys.executable,'-m','pip','install','--no-deps',str(native)]
        freeze=[sys.executable,'-m','pip','freeze']
    else:
        install=['uv','pip','install','--python',sys.executable,'--no-deps',str(native)]
        freeze=['uv','pip','freeze','--python',sys.executable]
    subprocess.run(install,cwd=dest,env=env,check=True)
    packages=subprocess.check_output(freeze,text=True,env=env)
    (out/'environment-freeze.txt').write_text(packages)
    subprocess.run([sys.executable,'-m','pytest','tests/test_weighted_range.py',
        'tests/test_weighted_study_audit.py','tests/test_strengthening_input_audit.py',
        'tests/test_strengthening_workload.py','tests/test_timeeval_adapter.py',
        'tests/test_timeeval_audit.py','tests/test_strengthening_reproduce.py','-q'],
        cwd=dest,env=env,check=True)
    workload=dest/'.cache/strengthening-workload'
    generation=out/'workload-generation.json'
    call('scripts/prepare_strengthening_workload.py','--archive',archive,'--output',workload,
         '--protocol',out/'workload-protocol.json','--generation',generation)
    native_audit=out/'native-input-audit.json'
    call('experiments/audit_strengthening_inputs.py','--generation',generation,
         '--timeeval-source',native,'--out',native_audit)
    weighted=out/'weighted-linux-v2'
    call('experiments/weighted_range_study.py','freeze','--inputs',generation,'--output',weighted)
    check_weighted_design(json.loads((ROOT/REL/'weighted-mac-v2/protocol.json').read_text()),
                          json.loads((weighted/'protocol.json').read_text()))
    call('experiments/weighted_range_study.py','run','--output',weighted)
    call('experiments/audit_weighted_range_study.py','--output',weighted,
         '--report',weighted/'independent-report.json')
    manifest=out/'timeeval-manifest.json'
    call('scripts/run_timeeval_strengthening.py','manifest','--workload',workload,'--source',native,
         '--generation-receipt',generation,'--native-input-audit',native_audit,'--out',manifest)
    payload=json.loads(manifest.read_text())
    previous=json.loads((ROOT/REL/'timeeval-consumer-global-v1.json').read_text())['timeeval_consumer']
    for key in ('schema','source_revision','design','row_ids','records','project_sha256'):
        if previous[key]!=payload[key]:raise ValueError('native design/source changed: '+key)
    # Query counts are measured from freshly generated, host-dependent scores;
    # freeze their local values, but compare only the prespecified batch design.
    def fixed_batches(p):
        return [{k:v for k,v in b.items() if k!='query_counts'} for b in p['batches']]
    if fixed_batches(previous)!=fixed_batches(payload):
        raise ValueError('native batch selection changed')
    protocol=out/'timeeval-global.json'
    write(protocol,{'status':'FROZEN_BEFORE_FRESH_HOST_NATIVE_CONSUMER_OUTCOMES',
        'utc':datetime.now(timezone.utc).isoformat(),'timeeval_consumer':payload})
    consumer=out/'timeeval-linux-v1'
    call('scripts/run_timeeval_strengthening.py','run','--protocol',protocol,
         '--protocol-sha256',sha(protocol),'--out',consumer)
    native_output_audit=out/'native-output-audit.json'
    call('experiments/audit_timeeval_strengthening.py','--run',consumer,
         '--protocol',protocol,'--out',native_output_audit)
    write(out/'reproduction-complete.json',{'status':'COMPLETE','utc':datetime.now(timezone.utc).isoformat(),
        'weighted_report_sha256':sha(weighted/'independent-report.json'),
        'native_complete_sha256':sha(consumer/'complete.json'),
        'generation_sha256':sha(generation),'native_input_audit_sha256':sha(native_audit),
        'native_output_audit_sha256':sha(native_output_audit),
        'scope':'Fresh source/data execution with per-host source bindings and same prespecified design. Host-dependent generated scores may differ; timings are not pooled.'})
    print(out,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--archive',type=Path)
    run(parser.parse_args())
