"""Independent reconstruction using the already audited generic control schema.

Only the stat-comparison mapping changes. Neither this wrapper nor its shared
auditors imports a timing producer or evaluator. Run as a standalone process.
"""
import argparse
import json
from pathlib import Path
import audit_pvldb_klein_control as shared
from audit_pvldb20261024 import digest, read, validate_inputs


def audit(root, output):
    root = Path(root).resolve()
    base = root / 'artifacts/pvldb-research-20261024'
    folder, primary = base / 'compiled-support-control', base / 'full-precision'
    p, start, done = [read(folder / f) for f in ('protocol.json', 'run-start.json', 'complete.json')]
    if done['status'] != 'COMPLETE':
        raise ValueError('incomplete')
    for r in (start, done):
        if r['protocol_sha256'] != digest(folder / 'protocol.json'):
            raise ValueError('protocol binding')
    for name in ('records', 'workflows'):
        if done[name + '_sha256'] != digest(folder / (name + '.jsonl')):
            raise ValueError('record binding')
    for file, h in p['source_sha256'].items():
        if digest(root / file) != h:
            raise ValueError('source binding: ' + file)
    for key, name in [('primary_protocol_sha256', 'protocol.json'), ('inputs_sha256', 'inputs.json'), ('primary_records_sha256', 'records.jsonl')]:
        if digest(primary / name) != p[key]:
            raise ValueError('parent binding')
    parent, inputs = read(primary / 'protocol.json'), read(primary / 'inputs.json')
    if inputs['status'] != 'COMPLETE' or inputs['protocol_sha256'] != digest(primary / 'protocol.json'):
        raise ValueError('input self-binding')
    labels, _, _ = validate_inputs(root, parent, inputs)
    references = shared.reference_vectors(list(map(json.loads, (primary / 'records.jsonl').read_text().splitlines())),
        {c['series'] for c in inputs['series']}, len(parent['models']), p['width'])
    rows, workflows = [[json.loads(line) for line in (folder / (name + '.jsonl')).read_text().splitlines()]
                       for name in ('records', 'workflows')]
    old_comparisons = shared.COMPARISONS
    try:
        shared.COMPARISONS = {'control_over_released': ('support_cumsum', 'released'),
                             'control_over_stream': ('support_cumsum', 'stream'),
                             'released_over_stream': ('released', 'stream')}
        result = shared.reconstruct(p, inputs['series'], rows, workflows, references, labels)
    finally:
        shared.COMPARISONS = old_comparisons
    for c in result['collections'].values():
        for comparison in c['workflow_comparisons'].values():
            comparison['scope'] = 'six balanced trials on fixed inputs; timing uncertainty only'
    result = {'status': 'PASS', 'audit_kind': 'raw-record reconstruction, not fresh timing',
        'auditor_sha256': digest(__file__), 'shared_auditor_sha256': digest(shared.__file__),
        'base_auditor_sha256': digest(Path(__file__).with_name('audit_pvldb20261024.py')),
        'protocol_sha256': digest(folder / 'protocol.json'), 'records_sha256': digest(folder / 'records.jsonl'),
        'workflows_sha256': digest(folder / 'workflows.jsonl'),
        'qualification': 'Post-review author-created compiled control. Same ranking/validation, conventional per-width ramps. Not an unchanged public comparator.', **result}
    with Path(output).open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'max_reference_pr_error', 'records', 'workflows')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.root, args.output)
