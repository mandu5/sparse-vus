"""Bind unified-paper layout and absolute costs to frozen raw measurements."""
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

bindings = {
    'Mac': ('artifacts/pr-engine/mac-holdout', '499f69e0e767f0c4971b8cc9cd839e3eedec3cb20f945b1cc6221f2604dd3228'),
    'Linux': ('artifacts/reproductions/linux-pr-engine-39523992616', 'a54fd4ec9107e2b9517b455d221c9f6dfbc7ae6f1f84070f0cb6a37ddbc62060'),
}
stats = {}
for host, (folder, sha) in bindings.items():
    raw = ROOT/folder/'measurements.jsonl'
    if digest(raw) != sha:
        raise ValueError('Frozen measurement identity changed: '+host)
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    for width in (30, 300):
        selected = [r for r in rows if r['max_buffer'] == width]
        if len(selected) != 308:
            raise ValueError('Task coverage differs')
        stats[f'{host}-{width}'] = {
            m: {'sum_seconds': sum(statistics.median(r['seconds'][m]) for r in selected),
                'median_ms': 1000*statistics.median(statistics.median(r['seconds'][m]) for r in selected)}
            for m in ('radix_pr', 'dense_pr_nearest_radix', 'klein_pr')}

text = r'''\paragraph{Absolute workload costs.}
For the 308 primary three-score tasks, sums of per-task median times are
'''
for host in ('Mac', 'Linux'):
    s = stats[f'{host}-30']
    vals = [s[m]['sum_seconds'] for m in ('radix_pr', 'dense_pr_nearest_radix', 'klein_pr')]
    text += f'{host}: {vals[0]:.3f}, {vals[1]:.3f}, and {vals[2]:.3f} seconds '
    text += '(sparse radix, matched nearest dense radix, and fast-VUS, respectively).\n'
text += r'At $L=300$, the corresponding sums are '
for host in ('Mac', 'Linux'):
    s = stats[f'{host}-300']
    vals = [s[m]['sum_seconds'] for m in ('radix_pr', 'dense_pr_nearest_radix', 'klein_pr')]
    text += f'{host}: {vals[0]:.3f}, {vals[1]:.3f}, and {vals[2]:.3f} seconds.\n'
text += r'''These quantify operator cost across a stored-score collection; they are
sums of separately timed medians, not measured batch wall times. They exclude
score generation and I/O and do not establish a detector-pipeline speedup.
'''
(ROOT/'paper/sparse_vus_absolute_results.tex').write_text(text)
original = ROOT/'paper/pr_engine_results.tex'
if digest(original) != 'e03f24e19114a05d3928f1f870bf5aa4072388676feabcfe7506d03313166ee9':
    raise ValueError('Frozen paper fragment changed')
layout = original.read_text().replace(r'\begin{table}[tbp]', r'\begin{table*}[t]').replace(r'\end{table}', r'\end{table*}')
layout = layout.replace(r'\begin{figure}[tbp]', r'\begin{figure*}[t]').replace(r'\end{figure}', r'\end{figure*}')
(ROOT/'paper/sparse_vus_engine_results.tex').write_text('% Layout-only copy of frozen pr_engine_results.tex; all numbers/text unchanged.\n'+layout)
outputs = ['paper/sparse_vus_absolute_results.tex', 'paper/sparse_vus_engine_results.tex']
receipt = {'measurement_bindings': bindings, 'statistics': stats,
           'frozen_tex_sha256': digest(original), 'generator_sha256': digest(Path(__file__)),
           'outputs_sha256': {p: digest(ROOT/p) for p in outputs}}
(ROOT/'paper/sparse_vus_context.receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
