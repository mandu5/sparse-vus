"""Prepare a separately frozen v2 fixed-score realization; measure only with --run.

The default acquires the pinned native source and raw public archive, generates
the fixed 52 detector profiles ONCE, independently verifies them, compares their
raw identities with both prior Linux executions, retains every score/query
difference diagnostically, and freezes the first complete new score realization.
It does not evaluate or time metrics. --run explicitly starts five fresh Python
children on that same runner after the successful freeze. No old study is run,
overwritten, pooled, or selected. Install requirements-strengthening.txt and
CPU torch==2.10.0 first, using Python 3.11.9 on Linux.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load('_affinity_original_acquisition', ROOT / 'experiments/reproduce_strengthening.py')
SESSION = load('_affinity_session_design', ROOT / 'scripts/run_timeeval_affinity_blocks_v2.py')
REL = BASE.REL


def committed_sources(root, names):
    """Reject uncommitted study orchestration before any acquisition or fitting."""
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    hashes = {}
    for name in names:
        committed = subprocess.check_output(['git', '-C', str(root), 'show', head + ':' + name])
        expected = hashlib.sha256(committed).hexdigest()
        if BASE.sha(root / name) != expected:
            raise ValueError('study source must be committed before preparation: ' + name)
        hashes[name] = expected
    return {'source_commit': head, 'committed_source_sha256': hashes}


def prepare(args, dest, out, source_receipt):
    # These are source-only copies. No prior arrays, score files or run outputs
    # enter the fresh workload; the four JSON references are identity metadata.
    for directory in ('src', 'experiments', 'scripts', 'tests'):
        shutil.copytree(ROOT / directory, dest / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in SESSION.NEW_SOURCES:
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    for name in ('source-discovery.json', 'provenance/source-manifest.json',
                 'provenance/float-decoding-contract.json',
                 'timeeval-consumer-global-v1.json',
                 'linux-original-replay/workload-generation.json',
                 'linux-original-replay/timeeval-global.json',
                 'linux-interval-replay/workload-generation.json',
                 'linux-interval-replay/timeeval-control-global.json'):
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / REL / name, target)
    selection = Path('artifacts/pvldb-research-20261024/full-precision/protocol.json')
    (dest / selection).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / selection, dest / selection)
    env = dict(os.environ)
    env.update({key: '1' for key in SESSION.THREADS})
    env['PYTHONPATH'] = str(dest / 'src')
    env['PYTHONOPTIMIZE'] = '0'

    def call(relative, *arguments):
        subprocess.run([sys.executable, str(dest / relative), *map(str, arguments)],
                       cwd=dest, env=env, check=True)

    SESSION.write_new(out / 'affinity-reproduction-start.json', {
        'status': 'PREPARING_WITHOUT_METRIC_EVALUATION',
        'utc': datetime.now(timezone.utc).isoformat(), **source_receipt,
        'requested_measurement': args.run, 'native_cpu': SESSION.cpu_receipt(),
        'ci_environment': {key: os.environ.get(key) for key in
                           ('GITHUB_SHA', 'GITHUB_REF', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT',
                            'RUNNER_OS', 'RUNNER_ARCH', 'ImageOS', 'ImageVersion')},
        'thread_environment_for_children': {key: env[key] for key in SESSION.THREADS},
        'scope': SESSION.design()['unit'],
        'raw_data_and_detector_scores_redistributed': False})
    SESSION.write_new(out / 'affinity-design-v2.json', SESSION.design())
    for name, expected in source_receipt['committed_source_sha256'].items():
        if BASE.sha(dest / name) != expected:
            raise ValueError('copied source differs from committed file: ' + name)

    source_manifest = json.loads((out / 'provenance/source-manifest.json').read_text())
    for entry in source_manifest['files']:
        BASE.download(entry['url'], dest / entry['path'], entry['sha256'])
    shutil.copy2(out / 'provenance/source-manifest.json',
                 dest / '.cache/strengthening-tsbad/source-manifest.json')
    archive = dest / 'cache/TSB-AD-U.zip'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if args.archive:
        archive.symlink_to(args.archive.resolve())
        if BASE.sha(archive) != BASE.RAW_SHA:
            raise ValueError('raw archive identity differs')
    else:
        BASE.download('https://www.thedatum.org/datasets/TSB-AD-U.zip', archive, BASE.RAW_SHA)
    tar = dest / '.cache/strengthening-timeeval-full.tar.gz'
    transport_sha = BASE.download(
        f'https://codeload.github.com/TimeEval/TimeEval/tar.gz/{BASE.TIMEVAL_COMMIT}', tar)
    native = dest / '.cache/strengthening-timeeval-full'
    BASE.extract_native(tar, native)
    frozen_native = json.loads((out / 'timeeval-consumer-global-v1.json').read_text())['timeeval_consumer']
    count = BASE.verify_source_tree(native, frozen_native['source_sha256'])
    SESSION.write_new(out / 'native-source-acquisition.json', {
        'revision': BASE.TIMEVAL_COMMIT, 'transport_sha256': transport_sha,
        'transport_bytes': tar.stat().st_size, 'source_files_verified': count,
        'source_tree_equals_frozen_source': True,
        'frozen_manifest_sha256': BASE.sha(out / 'timeeval-consumer-global-v1.json')})
    if importlib.util.find_spec('pip'):
        install = [sys.executable, '-m', 'pip', 'install', '--no-deps', str(native)]
        freeze = [sys.executable, '-m', 'pip', 'freeze']
    else:
        install = ['uv', 'pip', 'install', '--python', sys.executable, '--no-deps', str(native)]
        freeze = ['uv', 'pip', 'freeze', '--python', sys.executable]
    subprocess.run(install, cwd=dest, env=env, check=True)
    (out / 'environment-freeze.txt').write_text(
        subprocess.check_output(freeze, text=True, env=env))

    workload = dest / '.cache/strengthening-workload'
    generation = out / 'workload-generation.json'
    call('scripts/prepare_strengthening_workload.py', '--archive', archive,
         '--output', workload, '--protocol', out / 'workload-protocol.json',
         '--generation', generation)
    input_audit = out / 'native-input-audit.json'
    call('experiments/audit_strengthening_inputs.py', '--generation', generation,
         '--timeeval-source', native, '--out', input_audit)
    protocol = out / 'affinity-blocks-protocol-v2.json'
    call('scripts/run_timeeval_affinity_blocks_v2.py', 'freeze', '--workload', workload,
         '--source', native, '--generation', generation, '--input-audit', input_audit,
         '--protocol', protocol)
    protocol_sha = BASE.sha(protocol)
    consumer = out / 'affinity-blocks-linux-v2'
    command = [sys.executable, str(dest / 'scripts/run_timeeval_affinity_blocks_v2.py'), 'run',
               '--protocol', str(protocol), '--protocol-sha256', protocol_sha,
               '--out', str(consumer)]
    SESSION.write_new(out / 'affinity-prepared.json', {
        'status': 'FROZEN_READY_NOT_MEASURED', 'utc': datetime.now(timezone.utc).isoformat(),
        'protocol_sha256': protocol_sha, 'generation_sha256': BASE.sha(generation),
        'native_input_audit_sha256': BASE.sha(input_audit),
        'design_sha256': BASE.sha(out / 'affinity-design-v2.json'),
        'source_commit': source_receipt['source_commit'],
        'measurement_command': command, 'metric_evaluation_performed': False})
    if args.run:
        subprocess.run(command, cwd=dest, env=env, check=True)
        SESSION.write_new(out / 'affinity-reproduction-complete.json', {
            'status': 'COMPLETE', 'utc': datetime.now(timezone.utc).isoformat(),
            'protocol_sha256': protocol_sha,
            'sessions_complete_sha256': BASE.sha(consumer / 'complete.json'),
            'scope': SESSION.design()['unit'],
            'public_reference_evaluated': False,
            'raw_data_and_detector_scores_redistributed': False})
    print(json.dumps({'status': 'COMPLETE' if args.run else 'FROZEN_READY_NOT_MEASURED',
                      'evidence': str(out), 'protocol_sha256': protocol_sha}), flush=True)


def run(args):
    # Linux identity and committed-source gates run before downloads or fits.
    SESSION.cpu_receipt()
    receipt = committed_sources(ROOT, SESSION.NEW_SOURCES)
    if os.environ.get('GITHUB_SHA') not in (None, receipt['source_commit']):
        raise ValueError('CI requested commit differs from the source checkout')
    dest = args.output.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    out = dest / REL
    out.mkdir(parents=True)
    try:
        prepare(args, dest, out, receipt)
    except BaseException as exc:
        SESSION.write_new(out / 'affinity-reproduction-failure.json', {
            'utc': datetime.now(timezone.utc).isoformat(), 'error': str(exc),
            'traceback': traceback.format_exc(), 'source_commit': receipt['source_commit'],
            'partial_evidence_retained': True, 'automatic_retries_or_replacements': False})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='new directory; any existing output is refused')
    parser.add_argument('--archive', type=Path,
                        help='optional existing checksum-identical raw archive, never score vectors')
    parser.add_argument('--run', action='store_true',
                        help='explicitly start all five measured sessions after the successful freeze')
    run(parser.parse_args())
