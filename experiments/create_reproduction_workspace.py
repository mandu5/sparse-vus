"""Create an empty experimental workspace while preserving published results."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_REQUIRED = {
    'LICENSE', 'experiments/audit_pr_engine.py', 'experiments/advancement_data_gate.py',
    'experiments/benchmark_advancement.py', 'experiments/benchmark_pr_engine.py',
    'experiments/fast_vus_adapter.py', 'experiments/benchopt_vus_adapter.py',
    'experiments/data_hashes.json', 'experiments/data_manifest.json',
    'artifacts/public_benchmark.jsonl', 'artifacts/public_benchmark_receipt.json',
    'artifacts/selected_series.json', 'artifacts/external_supplement_selection.json',
    'artifacts/bolt_base_64-download.json', 'artifacts/TimeMoE-200M_64-download.json',
    'artifacts/timesfm-1.0-200m_64-download.json',
    'src/sparse_vus/core.py', 'src/sparse_vus/compiled.py',
    'src/sparse_vus/pr_compiled.py', 'src/sparse_vus/radix.py',
    'src/sparse_vus/certified.py', 'src/sparse_vus/selection.py',
    'src/sparse_vus/racing.py', 'src/sparse_vus/fast_racing.py',
}


def copy_historical_snapshot(root: Path, destination: Path):
    """Copy every inventoried v2 source/anchor byte, without cache links.

    Historical release bindings remain under their snapshot root. Root-level
    benchmark outputs are intentionally left absent for the original rerun.
    No downloader or current source file replaces a historical snapshot entry.
    """
    relative = Path('artifacts/pr-engine/source-v2')
    source = root / relative
    if not source.exists():
        return
    manifest_path = source / 'source-manifest.json'
    if source.is_symlink() or manifest_path.is_symlink():
        raise ValueError('Historical snapshot and inventory must be local files')
    manifest_bytes = manifest_path.read_bytes()
    inventory = json.loads(manifest_bytes)['files']
    paths = [entry['path'] for entry in inventory]
    if len(paths) != len(set(paths)) or not SNAPSHOT_REQUIRED <= set(paths):
        raise ValueError('Historical inventory omits source/attribution/release anchors or repeats a path')
    contents = {}
    for entry in inventory:
        name = Path(entry['path'])
        if (name.is_absolute() or not name.parts or name.as_posix() != entry['path']
                or any(part.startswith('.') or part == 'cache' for part in name.parts)):
            raise ValueError('Unsafe historical inventory path')
        path = source
        for part in name.parts:
            path = path / part
            if path.is_symlink():
                raise ValueError('Historical inventory may not follow symlinks')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256'] or len(data) != entry['bytes']:
            raise ValueError('Historical inventory byte/hash mismatch: ' + entry['path'])
        contents[name] = data
    target = destination / relative
    target.mkdir(parents=True, exist_ok=False)
    for name, data in contents.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (target / 'source-manifest.json').write_bytes(manifest_bytes)


def prepare_data_fetch(root: Path, output: Path):
    """Stage unchanged downloader inputs; keep new receipts under the rerun.

    Only the local input cache is shared. This prepares paths without running a
    downloader, and also works before any reference has created the cache.
    """
    staging = output.resolve() / 'data-fetch'
    (staging / 'experiments').mkdir(parents=True, exist_ok=False)
    (staging / 'artifacts').mkdir()
    for name in ('fetch_score_ranges.py', 'fetch_data.py', 'data_manifest.json', 'data_hashes.json'):
        shutil.copyfile(root / 'experiments' / name, staging / 'experiments' / name)
    cache = root / 'cache'
    cache.mkdir(parents=True, exist_ok=True)
    (staging / 'cache').symlink_to(cache.resolve(), target_is_directory=True)
    return staging


def create_workspace(destination: Path):
    destination = destination.resolve()
    if destination == ROOT or destination.is_relative_to(ROOT):
        raise ValueError('Choose a new directory outside the source repository')
    destination.mkdir(parents=True, exist_ok=False)
    for name in ('src', 'tests', 'experiments', 'docs', '.github'):
        shutil.copytree(ROOT / name, destination / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.egg-info'))
    for name in ('pyproject.toml', 'README.md', 'LICENSE', 'THIRD_PARTY.md', 'CITATION.cff', '.gitignore'):
        shutil.copyfile(ROOT / name, destination / name)
    (destination / 'paper').mkdir()
    shutil.copyfile(ROOT / 'paper/main.tex', destination / 'paper/main.tex')
    (destination / 'artifacts').mkdir()
    for name in ('mechanism_protocol.json', 'external_supplement_protocol.json'):
        shutil.copyfile(ROOT / 'artifacts' / name, destination / 'artifacts' / name)
    copy_historical_snapshot(ROOT, destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    destination = create_workspace(args.output or ROOT.parent /
        ('sparse-vus-reproduction-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')))
    print(destination)
    print('Create and activate a Python 3.12 virtual environment in that directory, then run:')
    print('bash experiments/run_reproduction.sh')


if __name__ == '__main__':
    main()
