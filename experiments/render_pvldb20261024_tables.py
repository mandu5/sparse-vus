"""Render manuscript tables from audited JSON; no timing or metric execution."""
from pathlib import Path
import argparse
import json

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence',type=Path,default=ROOT/'artifacts/pvldb-research-20261024')
parser.add_argument('--output',type=Path,default=ROOT/'paper/pvldb20261024_tables.tex')
args=parser.parse_args();BASE=args.evidence.resolve()
def report(folder,stem):
 path=BASE/folder/(stem+'-v3.json')
 if not path.exists():path=BASE/folder/(stem+'.json')
 return json.loads(path.read_text())
p=report('full-precision','independent-audit')
s=report('supplement','independent-report')
r=json.loads((BASE/'resources/report.json').read_text()) if (BASE/'resources/report.json').exists() else None
if p['status']!='PASS' or s['status']!='PASS' or (r is not None and r['status']!='COMPLETE'):
 raise ValueError('Evidence is not complete and audited')
lines=[]
def add(text):lines.append(text)
def interval(d):
 lo,hi=d['ci_familywise95_3collections']
 return f"{d['geometric_speedup']:.3f} [{lo:.3f}, {hi:.3f}]"
add(r'''\begin{table*}[t]
\centering\small
\begin{tabular}{lrlll}\toprule
Collection & Cases & Released / stream & Dense / stream & Klein exact / stream\\\midrule''')
for f,n in [('NAB',20),('SMAP',17),('SMD',36)]:
 d=p['verified_principal_summaries'][f+'_L30']
 add(f"{f} & {n} & {interval(d['released'])} & {interval(d['dense'])} & {interval(d['external'])}"+r'\\')
add(r'''\bottomrule\end{tabular}
\caption{Primary complete-call geometric speedups at width 30. Brackets give
paired-series 95\% bounds adjusted across three collections for each comparator.
All include public validation, preparation, allocation and eight-model winner
selection. Hardware is identified by the selected evidence receipt; per-series intervals are
conditional on the fixed panel and supplemented with label-block sensitivity.}
\label{tab:primary-new}\end{table*}''')
add(r'''\begin{table}[t]\centering\small
\begin{tabular}{lrrrr}\toprule
Collection & Stream & Released & Dense & Klein\\\midrule''')
for f in ['NAB','SMAP','SMD']:
 d=p['verified_workflows'][f]['median_seconds']
 add(f"{f} & {d['stream']:.4f} & {d['released']:.4f} & {d['dense']:.4f} & {d['external']:.4f}"+r'\\')
add(r'''\bottomrule\end{tabular}
\caption{Directly timed primary collection workflow medians, seconds. Each pass
reads all score files and writes/closes its selected-model output. Detector
fitting, cold storage and JIT compilation are excluded.}
\label{tab:workflow-new}\end{table}''')
add(r'''\begin{table*}[t]\centering\small
\begin{tabular}{llllr}\toprule
Collection & Paired case Benchopt / radix & Benchopt workflow (s) & Radix workflow (s) & Workflow ratio\\\midrule''')
for f in ['NAB','SMAP','SMD']:
 d=s['matched_pair'][f];w=s['workflow_summaries'][f]['median_seconds']
 add(f"{f} & {interval(d['case_paired'])} & {w['benchopt_pair']:.4f} & {w['radix_pair']:.4f} & {d['workflow_median_ratio']:.2f}"+r'\\')
add(r'''\bottomrule\end{tabular}
\caption{Supplementary matched-output comparison: both methods return exact
numerical ROC and PR. Width 30, unchanged Benchopt source, same 73 series and
scores. Case bounds use the same three-collection adjustment. This gain belongs
to the complete sparse evaluator, not solely to the new PR batch loop.}
\label{tab:supp-new}\end{table*}''')
add(r'''\begin{table*}[t]\centering\small
\begin{tabular}{lrrrrrr}\toprule
& \multicolumn{3}{c}{Klein, 250 thresholds} & \multicolumn{2}{c}{Klein, 1,000 thresholds} &\\
Collection & Changed sets & Regret $\ge0.01$ & Max regret & Changed sets & Max regret & 250 / exact workflow\\\midrule''')
for f in ['NAB','SMAP','SMD']:
 a=s['accuracy'][f]['klein250'];b=s['accuracy'][f]['klein1000'];w=s['workflow_summaries'][f]['median_seconds']
 add(f"{f} & {a['winner_set_changes']} & {a['minimum_regret_at_least_threshold']} & {a['maximum_regret']:.5f} & {b['winner_set_changes']} & {b['maximum_regret']:.5f} & {w['klein250']/w['stream']:.2f}"+r'\\')
add(r'''\bottomrule\end{tabular}
\caption{Approximation accuracy--cost comparison. Minimum and maximum regret
threshold counts coincide in this panel; both are retained in the artifact.
The final column compares directly timed PR-only workflows. Zero losses,
including all NAB selections and every 1,000-threshold loss below 0.01, are
retained. Values describe these fixed detector-score inputs, not detector quality.}
\label{tab:accuracy-new}\end{table*}''')
if r is not None:
 add(r'''\begin{table}[t]\centering\small
\begin{tabular}{lrrrr}\toprule
Positive fraction & Released & Geometry & Stream & Dense\\\midrule''')
 for fraction in [.01,.5]:
  d=r['cases'][f'synthetic_n500000_M8_p{fraction}']
  add(f"{fraction:.2f} & "+' & '.join(f"{d[m]['peak_process_mib_median']:.1f}" for m in ['released','geometry','stream','dense'])+r'\\')
 add(r'''\bottomrule\end{tabular}
\caption{Median OS lifetime peak RSS (MiB), three fresh processes per method,
$n=500{,}000$, $M=8$, one centered anomaly interval, width 30. These synthetic
resource cases include interpreter, libraries, inputs and warm-up; they are not
measurements of auxiliary space or additional real datasets.}
\label{tab:memory-new}\end{table}''')
args.output.write_text('\n'.join(lines)+'\n')
print(f'Wrote primary, workflow, matched-output and accuracy tables from {BASE}; resource table included: {r is not None}.')

# Follow-up evidence belongs to a separate freeze. Never borrow it from another
# host or silently synthesize a table when only the primary study is available.
followup=BASE/'operating-range/independent-report.json'
if followup.exists():
 o=json.loads(followup.read_text())
 if o['status']!='PASS':raise ValueError('Follow-up audit did not pass')
 extra=[r'''\begin{table*}[t]\centering\small
\begin{tabular}{lrrrrl r}\toprule
Collection & Series & Stream (s) & Klein (s) & Released (s) & Paired geometric Klein/stream [95\% CI] & Matched pair ratio\\\midrule''']
 for family in ['MITDB','SWaT']:
  d=o['collections'][family];t=d['workflow_median_seconds'];a=d['workflow_ratios']['external'];lo,hi=a['paired_trial_ci95']
  extra.append(f"{family} & {d['series']} & {t['stream']:.3f} & {t['external']:.3f} & {t['released']:.3f} & {a['paired_geometric_ratio']:.2f} [{lo:.2f}, {hi:.2f}] & {d['workflow_matched_pair_ratio']:.2f}"+r'\\')
 extra.append(r'''\bottomrule\end{tabular}
\caption{Separately frozen long-recording follow-up, $M=8$, width 30, Apple M1 Pro.
Times are medians of three complete collection passes. PR intervals resample
paired timing trials on fixed inputs and are unadjusted; three workflow orders
are not fully position-balanced. The matched-pair column is the ratio of median
Benchopt and radix workflow times for ROC+PR. SWaT is one recording, not an estimate
over a population of independent series.}
\label{tab:long-new}\end{table*}''')
 with args.output.open('a') as f:f.write('\n'.join(extra)+'\n')
 print('Included separately frozen operating-range workflow table.')

control=BASE/'klein-support-control/independent-report.json'
if control.exists():
 k=json.loads(control.read_text())
 if k['status']!='PASS':raise ValueError('Klein-control audit did not pass')
 extra=[r'''\begin{table*}[t]\centering\small
\begin{tabular}{llllr}\toprule
Collection & Klein / patched Klein & Patched Klein / released & Patched Klein / stream & Workflow patched/stream\\\midrule''']
 for family in ['NAB','SMAP','SMD']:
  d=k['collections'][family];c=d['case_comparisons']
  extra.append(f"{family} & {interval(c['external_over_control'])} & {interval(c['control_over_released'])} & {interval(c['control_over_stream'])} & {d['workflow_comparisons']['control_over_stream']['median_ratio']:.2f}"+r'\\')
 extra.append(r'''\bottomrule\end{tabular}
\caption{Author-created minimal ablation: replace only Klein's threshold list
with all distinct maximum-support scores; retain global counts and other code.
Eight balanced case orders on the original 73 series, width 30, Apple M1 Pro;
case intervals are 95\% bounds adjusted across three collections per comparison.
The final column uses three not-fully-balanced workflow passes. Remaining
gains include implementation differences; the compiled dense control separately
isolates support compression. The patched code is not an upstream release.}
\label{tab:klein-control}\end{table*}''')
 with args.output.open('a') as f:f.write('\n'.join(extra)+'\n')
 print('Included separately frozen minimal Klein support-threshold ablation.')

compiled_control = BASE / 'compiled-support-control/independent-report.json'
if compiled_control.exists():
 c = json.loads(compiled_control.read_text())
 if c['status'] != 'PASS': raise ValueError('Compiled-control audit did not pass')
 extra = [r'''\begin{table*}[t]\centering\small
\begin{tabular}{llllr}\toprule
Collection & Control / released & Control / stream & Released / stream & Workflow control/stream\\\midrule''' ]
 for family in ['NAB','SMAP','SMD']:
  d = c['collections'][family]; a = d['case_comparisons']
  extra.append(f"{family} & {interval(a['control_over_released'])} & {interval(a['control_over_stream'])} & {interval(a['released_over_stream'])} & {d['workflow_comparisons']['control_over_stream']['median_ratio']:.3f}" + r'\\')
 extra.append(r'''\bottomrule\end{tabular}
\caption{New author-created compiled conventional support-cumsum control, with
matched validation, radix ordering and global counts, direct per-width ramps
and cached original-positive mass. Six balanced orders for all 73 primary
cases and six balanced workflow passes, width 30, Apple M1 Pro. Brackets are
three-collection-adjusted 95\% intervals. Ratios below one favor the control;
all scalar cases favor it over released. This is not unchanged public Klein.}
\label{tab:compiled-control}\end{table*}''')
 with args.output.open('a') as f: f.write('\n'.join(extra) + '\n')
 print('Included compiled conventional-support attribution control.')
