"""Generate the paper's collection results from independently audited receipts."""
from pathlib import Path
import hashlib
import json
import statistics

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'artifacts/collection-workflow/mac-20261023'
PROTOCOL = '69ee646b505297e0feb124cb3206b0d600a6ad2a0a021c8fcea1c195dd4f56ea'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    from audit_vus_collection import audit
    checked = audit(STUDY, PROTOCOL, root=ROOT)
    data = json.loads((STUDY / 'report.json').read_text())
    for key in ('median_seconds', 'whole_seconds', 'median_speedup_over_radix',
                'max_pairwise_pr_difference', 'all_selected_sets_agree'):
        require(checked[key] == data[key], f'Independent reconstruction disagrees: {key}')
    require(data['status'] == 'PASS', 'Recorded collection criterion did not pass')
    entries = json.loads((STUDY / 'inputs.json').read_text())
    times, medians = data['whole_seconds'], data['median_seconds']
    rows = data['passes']
    methods = [('radix_pr', 'Sparse radix PR'),
               ('dense_pr_nearest_radix', 'Dense nearest radix PR'),
               ('klein_pr', 'Klein fast-VUS PR')]
    lines = [r'''\subsection{Directly timed stored-score collection workflow}
\label{sec:collection-workflow}
A separate protocol measures an actual local collection operation, beyond
sums of separately timed task medians. Each pass reopens 308 uncompressed
NPZ files, materializes the labels and three original score arrays, makes
924 full PR calls at $L=30$, selects all best-model ties per series, and
serializes the values and decisions into one JSON file. Inputs are the same
17-family policy holdout; no detector inference occurs in this operation.
The stored files total 379,354,532 bytes. Each method uses the unchanged
released implementation and exhaustive thresholds. All validation and
preparation inside the public calls are timed.

The whole monotonic clock runs from before the first NPZ open until the
result file is closed. Imports and synthetic dtype-matched JIT warmup occur
once before timing; input hashing and explicit filesystem-cache warming
precede every pass. Every measured
pass rereads and decodes the files; it is a warm-filesystem workflow, not a
cold-disk or durable-write benchmark (no \texttt{fsync}). Three replications
run serially with one numerical thread on the M1 Pro. Seeded method order
was frozen before timing; its draw places dense last in all three
replications, so order is randomized but not position-balanced. The active
desktop was not isolated; background OCR/Python activity was recorded before
execution. Agent tests, builds and other benchmarks were stopped.

\begin{table*}[t]
\centering\small
\caption{Measured collection wall times in seconds. The last two columns
are separately summarized phase medians, not additive whole-time estimates.
All nine passes and all numeric outputs are retained.}
\label{tab:collection-workflow}
\begin{tabular}{lrrrrrr}
\toprule
Method & Run 1 & Run 2 & Run 3 & Whole median & Metric median & Read median\\
\midrule''']
    for method, title in methods:
        phase = [r['phase_ns'] for r in rows if r['method'] == method]
        values = times[method] + [medians[method],
                  statistics.median(p['metric'] for p in phase)/1e9,
                  statistics.median(p['read'] for p in phase)/1e9]
        lines.append(title + ' & ' + ' & '.join(f'{v:.3f}' for v in values) + r' \\')
    lines += [r'\bottomrule', r'\end{tabular}', r'\end{table*}']
    ratios = data['median_speedup_over_radix']
    mantissa, exponent = f"{data['max_pairwise_pr_difference']:.3e}".split('e')
    error_tex = mantissa + r'\times10^{' + str(int(exponent)) + '}'
    lines.append(
        'Every selected-model set agrees across all nine passes for all 308 series.\n'
        + f'The maximum pairwise PR difference is ${error_tex}$, below the frozen\n'
        + '$10^{-11}$ tolerance; model ties use $10^{-10}$. '
        + f'Sparse radix takes {medians["radix_pr"]:.3f} seconds at the median,\n'
        + f'giving descriptive whole-workflow ratios of ${ratios["dense_pr_nearest_radix"]:.3f}\\times$\n'
        + f'against matched dense radix and ${ratios["klein_pr"]:.3f}\\times$ against Klein.\n'
        + 'Both comparisons satisfy the frozen median-time criterion. Three observations\n'
        + 'per method do not establish a confidence interval or timing significance.\n'
        + 'This directly demonstrates savings for the specified stored-score operation;\n'
        + 'it does not measure a full training/inference pipeline, production deployment,\n'
        + 'or a new-domain evaluation. An independent standard-library auditor\n'
        + 'checks recorded order, counts and clock consistency and recomputes\n'
        + 'numeric comparisons and decisions from public hash-bound receipts,\n'
        + 'without raw input arrays or a new timing measurement.\n')
    target = ROOT / 'paper/sparse_vus_collection_results.tex'
    target.write_text('\n'.join(lines).rstrip() + '\n')
    receipt = {'protocol_sha256': PROTOCOL,
               'report_sha256': digest(STUDY / 'report.json'),
               'independent_auditor_sha256': digest(ROOT / 'experiments/audit_vus_collection.py'),
               'generator_sha256': digest(__file__), 'tex_sha256': digest(target),
               'series': len(entries), 'rows': sum(r['n'] for r in entries), 'passes': len(rows)}
    (ROOT / 'paper/sparse_vus_collection_results.receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
