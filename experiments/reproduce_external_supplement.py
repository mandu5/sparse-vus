"""Repeat the supplement without overwriting the published experimental records."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

import external_supplement


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='A new directory inside this repository')
    args = parser.parse_args()
    root = external_supplement.ROOT
    destination = (args.output or root / 'artifacts' /
                   ('external-rerun-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))).resolve()
    if not destination.is_relative_to(root):
        raise ValueError('Output must be inside the repository so receipt paths remain portable')
    destination.mkdir(parents=True, exist_ok=False)
    for name in ('external_supplement_protocol.json', 'public_benchmark.jsonl',
                 'final_artifact_gate.json', 'bolt_base_64-download.json'):
        shutil.copyfile(root / 'artifacts' / name, destination / name)
    external_supplement.ART = destination
    sys.argv = [str(root / 'experiments/external_supplement.py')]
    print(f'Reproduction output: {destination}', flush=True)
    external_supplement.main()


if __name__ == '__main__':
    main()
