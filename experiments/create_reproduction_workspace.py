"""Create an empty experimental workspace while preserving published results."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


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
