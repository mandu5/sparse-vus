"""Render manuscript tables only after reconstructing the frozen report."""
import json
from pathlib import Path

from benchmark_tie_runs import ROOT, report, digest

study = ROOT/'artifacts/tie-runs/mac-20261023'
checked = report(study)
data = json.loads((study/'report.json').read_text())
assert checked['status'] == 'PASS_PARITY_AND_WORK'
audit_path = ROOT/'artifacts/tie-runs/independent-audit-20261023.json'
audit = json.loads(audit_path.read_text())
assert audit['status'] == 'PASS_RECORDED_CHECKS'
assert audit['randomized_metric_cases'] == 650 and audit['decimal_integral_cases'] == 36
for name, sha in audit['source_sha256'].items():
    assert digest(ROOT/name) == sha, name
lines = [r'''\subsection{Run aggregation: structured ties and a fragmentation control}
The separately frozen run study evaluates 20 constructed cases (five score
families at $L=32,128,512,2048$) and every one-interval case from the previous
development and external corpora: 63 and 48 cases, respectively. This is
reused-data evaluation, not unseen confirmation. All four methods are PR-only
and include validation, ranking, geometry and, for run aggregation, the
square-root table. Each case has one untimed warm call per method and five
seeded randomized serial repetitions on the Apple M1 Pro with one compute
thread (Python 3.12.4, NumPy 1.26.4, Numba 0.59.1).

All 131 cases satisfy the numerical and work assertions. The maximum absolute
discrepancy from released radix is $5.56\times10^{-16}$. Every width visits at
most $3P_0$ score classes. For the all-tied singleton at $L=2048$, run aggregation
inspects 2,049 runs in total, while the position scan visits 2,099,201 positions.
These counts support the proved separation; they do not determine wall time.

A separate untimed verifier compares 650 random cases against direct dense
evaluation (maximum absolute difference $3.34\times10^{-16}$), and 36 small
complete integrals against independently constructed Decimal arithmetic at
80-digit precision (maximum $2.60\times10^{-16}$). It also checks every one of
150,000 integer prefixes against Python integers, 20,009 synthetic limb
subtractions, and 6,569 per-width counter reconstructions. These are internal
implementation checks, separate from benchmark cases and the local error theorem.

Table~\ref{tab:tie-structural} reports every constructed family at the largest
width. Larger ratios favor run aggregation; subunit ratios are regressions.
The alternating-score control defeats compression because each score class is
highly fragmented. Distinct scores also offer little aggregation benefit.
These are constructed witnesses, not a sample of operational detectors.

\begin{table}[t]
\centering\small
\caption{Constructed $L=2048$ cases, $n=8195$: comparator / run-aggregation median
time. All five families retained; full results at every width are in the artifact.}
\label{tab:tie-structural}
\begin{tabular}{lrrr}
\toprule
Scores / labels & Active prefix & Radix & Fast-VUS\\
\midrule''']
names = [('all_tied', 'All tied / singleton'),
         ('distinct_original_last', 'Distinct / original last'),
         ('eight_blocks', 'Eight blocks / singleton'),
         ('alternating', 'Alternating / singleton'),
         ('interval8_all_tied', 'All tied / interval of 8')]
for key, title in names:
    row = data['summary'][key+'|L2048']['comparators']
    values = [row[m]['median_ratio'] for m in ('saturation', 'radix', 'klein')]
    lines.append(title+' & '+' & '.join(f'{v:.3f}' for v in values)+r' \\')
lines += [r'''\bottomrule
\end{tabular}
\end{table}

The real-score results in Table~\ref{tab:tie-real} are deliberately separate.
At $L=300$, run aggregation loses to active prefix on 16 of 21 development
cases and 14 of 16 external cases. It is therefore an option for compressible
ties, not a replacement justified by broad real-data gains. No runtime selector
or population confidence interval is inferred from these reused cases.

\begin{table}[t]
\centering\small
\caption{All reused one-interval cases. Each entry is median comparator/run
ratio, followed by the number of run-aggregation losses.}
\label{tab:tie-real}
\setlength{\tabcolsep}{4pt}
\begin{tabular}{llrrr}
\toprule
Corpus & $L$ & Active prefix & Radix & Fast-VUS\\
\midrule''']
for phase, title in [('development', 'Dev. ($n_c=21$)'), ('external', 'Ext. ($n_c=16$)')]:
    for width in (30, 100, 300):
        row = data['summary'][f'{phase}|L{width}']['comparators']
        cells = [f"{row[m]['median_ratio']:.3f} ({row[m]['losses']})"
                 for m in ('saturation', 'radix', 'klein')]
        lines.append(title+f' & {width} & '+' & '.join(cells)+r' \\')
lines += [r'''\bottomrule
\end{tabular}
\end{table}

The protocol, source inventory, input hashes, five raw repetitions and work
profiles are frozen together. The complete 131-case report includes every
ratio and loss. This study changes neither the whole-method primary PASS nor
the active-prefix primary FAIL decisions.''']
target = ROOT/'paper/tie_run_results.tex'
target.write_text('\n'.join(lines)+'\n')
receipt = {'protocol_sha256': digest(study/'protocol.json'),
           'independent_audit_sha256': digest(audit_path),
           'measurements_sha256': digest(study/'measurements.jsonl'),
           'report_sha256': digest(study/'report.json'),
           'generator_sha256': digest(Path(__file__)),
           'tex_sha256': digest(target), 'cases': data['cases']}
(ROOT/'paper/tie_run_results.receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
