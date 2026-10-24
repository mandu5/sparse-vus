"""Fresh replay of the post-review conventional interval control.

This is a separately frozen supplemental ablation. It does not overwrite,
select from, or replace the original weighted/native studies. Public callback
timings are not repeated: this run compares three compiled implementations.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_original_reproduction', ROOT / 'experiments/reproduce_strengthening.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
REL = base.REL


def run(args):
    dest = args.output.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    out = dest / REL
    out.mkdir(parents=True)
    for directory in ('src', 'experiments', 'scripts', 'tests'):
        shutil.copytree(ROOT / directory, dest / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for rel in ('source-discovery.json', 'provenance/source-manifest.json',
                'provenance/float-decoding-contract.json'):
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / REL / rel, target)
    original = Path('artifacts/pvldb-research-20261024/full-precision/protocol.json')
    (dest / original).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / original, dest / original)
    env = dict(os.environ)
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                'NUMBA_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        env[key] = '1'
    env['PYTHONPATH'] = str(dest / 'src')
    env['PYTHONOPTIMIZE'] = '0'

    def call(relative, *argv):
        subprocess.run([sys.executable, str(dest / relative), *map(str, argv)],
                       cwd=dest, env=env, check=True)

    base.write(out / 'control-reproduction-start.json', {
        'status': 'RUNNING', 'utc': datetime.now(timezone.utc).isoformat(),
        'source_script_sha256': base.sha(Path(__file__)),
        'imported_reproduction_sha256': base.sha(ROOT / 'experiments/reproduce_strengthening.py'),
        'source_commit': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
        'scope': 'Fresh same-panel public-detector generation, conventional interval control and compiled native workflow ablation. No reused score vectors or public timing reruns.'})
    source_manifest = json.loads((out / 'provenance/source-manifest.json').read_text())
    for entry in source_manifest['files']:
        base.download(entry['url'], dest / entry['path'], entry['sha256'])
    shutil.copy2(out / 'provenance/source-manifest.json', dest / '.cache/strengthening-tsbad/source-manifest.json')
    archive = dest / 'cache/TSB-AD-U.zip'
    archive.parent.mkdir(parents=True)
    if args.archive:
        archive.symlink_to(args.archive.resolve())
        if base.sha(archive) != base.RAW_SHA:
            raise ValueError('raw archive identity')
    else:
        base.download('https://www.thedatum.org/datasets/TSB-AD-U.zip', archive, base.RAW_SHA)
    tar = dest / '.cache/strengthening-timeeval-full.tar.gz'
    transport_sha = base.download(f'https://codeload.github.com/TimeEval/TimeEval/tar.gz/{base.TIMEVAL_COMMIT}', tar)
    native = dest / '.cache/strengthening-timeeval-full'
    base.extract_native(tar, native)
    mac_source = json.loads((ROOT / REL / 'timeeval-consumer-global-v1.json').read_text())['timeeval_consumer']
    count = base.verify_source_tree(native, mac_source['source_sha256'])
    base.write(out / 'native-source-acquisition.json', {
        'revision': base.TIMEVAL_COMMIT, 'transport_sha256': transport_sha,
        'transport_bytes': tar.stat().st_size,
        'frozen_manifest_sha256': base.sha(ROOT / REL / 'timeeval-consumer-global-v1.json'),
        'source_files_verified': count, 'source_tree_equals_frozen_mac': True})
    if importlib.util.find_spec('pip'):
        install = [sys.executable, '-m', 'pip', 'install', '--no-deps', str(native)]
        freeze = [sys.executable, '-m', 'pip', 'freeze']
    else:
        install = ['uv', 'pip', 'install', '--python', sys.executable, '--no-deps', str(native)]
        freeze = ['uv', 'pip', 'freeze', '--python', sys.executable]
    subprocess.run(install, cwd=dest, env=env, check=True)
    (out / 'environment-freeze.txt').write_text(subprocess.check_output(freeze, text=True, env=env))
    subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_weighted_range_control.py',
                    'tests/test_timeeval_interval_adapter.py', 'tests/test_timeeval_interval_control.py',
                    'tests/test_strengthening_input_audit.py', '-q'], cwd=dest, env=env, check=True)
    workload = dest / '.cache/strengthening-workload'
    generation = out / 'workload-generation.json'
    call('scripts/prepare_strengthening_workload.py', '--archive', archive, '--output', workload,
         '--protocol', out / 'workload-protocol.json', '--generation', generation)
    input_audit = out / 'native-input-audit.json'
    call('experiments/audit_strengthening_inputs.py', '--generation', generation,
         '--timeeval-source', native, '--out', input_audit)
    weighted = out / 'weighted-control-linux-v1'
    call('experiments/weighted_range_control_study.py', 'freeze', '--inputs', generation, '--output', weighted)
    base.check_weighted_design(json.loads((ROOT / REL / 'weighted-control-mac-v1/protocol.json').read_text()),
                               json.loads((weighted / 'protocol.json').read_text()))
    call('experiments/weighted_range_control_study.py', 'run', '--output', weighted)
    call('experiments/audit_weighted_range_study.py', '--output', weighted,
         '--report', weighted / 'independent-report.json')
    manifest = out / 'timeeval-control-manifest.json'
    call('scripts/run_timeeval_interval_control.py', 'manifest', '--workload', workload,
         '--source', native, '--generation-receipt', generation,
         '--native-input-audit', input_audit, '--out', manifest)
    payload = json.loads(manifest.read_text())
    previous = json.loads((ROOT / REL / 'timeeval-control-global-v1.json').read_text())['timeeval_consumer']
    for key in ('schema', 'source_revision', 'design', 'row_ids', 'records', 'project_sha256'):
        if previous[key] != payload[key]:
            raise ValueError('native control design/source changed: ' + key)
    def fixed_batches(p):
        return [{k: v for k, v in b.items() if k != 'query_counts'} for b in p['batches']]
    if fixed_batches(previous) != fixed_batches(payload):
        raise ValueError('native batch selection changed')
    protocol = out / 'timeeval-control-global.json'
    base.write(protocol, {'status': 'FROZEN_BEFORE_FRESH_HOST_INTERVAL_CONSUMER_TIMINGS',
                          'utc': datetime.now(timezone.utc).isoformat(),
                          'timeeval_consumer': payload})
    consumer = out / 'timeeval-control-linux-v1'
    call('scripts/run_timeeval_interval_control.py', 'run', '--protocol', protocol,
         '--protocol-sha256', base.sha(protocol), '--out', consumer)
    output_audit = out / 'native-control-output-audit.json'
    call('experiments/audit_timeeval_interval_control.py', '--run', consumer,
         '--protocol', protocol, '--out', output_audit)
    base.write(out / 'control-reproduction-complete.json', {
        'status': 'COMPLETE', 'utc': datetime.now(timezone.utc).isoformat(),
        'weighted_report_sha256': base.sha(weighted / 'independent-report.json'),
        'native_complete_sha256': base.sha(consumer / 'complete.json'),
        'generation_sha256': base.sha(generation), 'native_input_audit_sha256': base.sha(input_audit),
        'native_output_audit_sha256': base.sha(output_audit),
        'scope': 'Supplemental interval control; unchanged cohort and semantic design; fresh host-dependent scores; no host pooling.'})
    print(out, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--archive', type=Path)
    run(parser.parse_args())
