"""Figure-only postprocessing; never reruns a metric or changes timing data.

The initial run's PNG/SVG remain unchanged at their receipt-bound paths.
An explicit receipt binds new readable figures to the unchanged timed results.
Run only after the external timing supplement releases the shared CPU.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR'] = str(OUT / '.cache' / 'matplotlib')
sys.dont_write_bytecode = True


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cpu-clearance', required=True)
    args = parser.parse_args()
    receipt_path = OUT / 'figure_receipt.json'
    if receipt_path.exists():
        raise FileExistsError('A figure postprocessing receipt already exists.')
    results_path = ROOT / 'artifacts' / 'mechanism_results.json'
    run_receipt_path = OUT / 'run_receipt.json'
    results = json.loads(results_path.read_text())
    run_receipt = json.loads(run_receipt_path.read_text())
    protocol_path = ROOT / 'artifacts' / 'mechanism_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert results['status'] == run_receipt['status'] == 'complete'
    assert digest(results_path) == run_receipt['results_sha256']
    assert digest(OUT / 'raw_cases.jsonl') == run_receipt['raw_cases_sha256']
    for name, expected in run_receipt['source_sha256'].items():
        assert digest(ROOT / name) == expected, name
    original_figures = [f for f in results['figures'] if Path(f['path']).suffix in ('.png', '.svg')]
    assert len(original_figures) == 2
    for item in original_figures:
        assert digest(ROOT / item['path']) == item['sha256']

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter

    rows = results['rows']
    colors = dict(zip(protocol['max_buffer'], ['#0072B2', '#E69F00', '#009E73', '#CC79A7']))
    columns = [('speedup_current_vs_fullsort', 'Global-sort ablation'),
               ('speedup_current_vs_fastest_dense', 'Fastest-dense comparison')]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, constrained_layout=True)
    for row_index, n in enumerate(protocol['n']):
        for column, (key, title) in enumerate(columns):
            ax = axes[row_index, column]
            for width in protocol['max_buffer']:
                selected = [r for r in rows if r['n'] == n and r['max_buffer'] == width]
                ax.scatter([r['support_fraction'] for r in selected], [r[key] for r in selected],
                           color=colors[width], s=27, alpha=.8, edgecolors='white', linewidths=.35)
            ax.set_xscale('log')
            ax.xaxis.set_major_locator(FixedLocator([.001, .01, .1, .5, 1]))
            ax.xaxis.set_major_formatter(FixedFormatter(['0.1%', '1%', '10%', '50%', '100%']))
            ax.xaxis.set_minor_formatter(NullFormatter())
            if column == 0:
                # A common linear scale makes the modest incremental gains explicit.
                ticks = [.5, 1, 1.25, 1.5, 2]
                ax.set_ylim(.5, 2)
            else:
                ticks = [.25, .5, 1, 2, 4, 8]
                ax.set_yscale('log', base=2)
                ax.set_ylim(.2, 10)
            ax.yaxis.set_major_locator(FixedLocator(ticks))
            ax.yaxis.set_major_formatter(FixedFormatter([f'{tick:g}×' for tick in ticks]))
            ax.yaxis.set_minor_formatter(NullFormatter())
            ax.axhline(1, color='#555555', lw=1, linestyle='--')
            ax.set_title(f'n = {n:,}: {title}', fontsize=10)
            ax.set_ylabel('Runtime ratio (comparator / current sparse)')
            ax.grid(alpha=.2, which='major')
            if row_index == 1:
                ax.set_xlabel('Realized maximum-support fraction Q/n (log scale)')
    handles = [Line2D([], [], marker='o', linestyle='', color=colors[w], label=f'L = {w}')
               for w in protocol['max_buffer']]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, 1.05),
               ncol=len(handles), frameon=False)

    new_figures = []
    for suffix in ['png', 'svg']:
        path = ROOT / 'paper' / 'figures' / f'mechanism.readable.{suffix}'
        if path.exists():
            raise FileExistsError(f'Readable figure already exists: {path}')
        fig.savefig(path, dpi=180, bbox_inches='tight')
        new_figures.append({'path': str(path.relative_to(ROOT)), 'sha256': digest(path)})
    plt.close(fig)
    assert digest(results_path) == run_receipt['results_sha256']
    assert digest(OUT / 'raw_cases.jsonl') == run_receipt['raw_cases_sha256']
    for item in original_figures:
        assert digest(ROOT / item['path']) == item['sha256']
    receipt = {
        'status': 'complete', 'completed_utc': datetime.now(timezone.utc).isoformat(),
        'cpu_clearance': args.cpu_clearance,
        'helper_path': str(Path(__file__).resolve().relative_to(ROOT)),
        'helper_sha256': digest(__file__),
        'input_results_sha256': digest(results_path),
        'input_run_receipt_sha256': digest(run_receipt_path),
        'input_raw_cases_sha256': digest(OUT / 'raw_cases.jsonl'),
        'protocol_sha256': digest(protocol_path),
        'timings_and_benchmark_source_unchanged': True,
        'unchanged_initial_figures': original_figures,
        'readable_figures': new_figures,
        'changes': 'Explicit ratio tick labels, shared linear 0.5–2 scale for sort ablation, '
                   'shared logarithmic 0.2–10 scale for dense comparison, percentage Q/n ticks. '
                   'Data points unchanged; ratios >1 favor the current sparse implementation.',
        'pdf_generated': False,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
