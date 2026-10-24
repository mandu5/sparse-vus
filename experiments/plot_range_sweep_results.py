"""Render descriptive case-level views from the frozen, audited range records."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/pvldb-research-20261024/range-sweep/main-study'


def main():
    audit=json.loads((BASE/'independent-report.json').read_text())
    raw=(BASE/'records.jsonl').read_bytes()
    if audit['status']!='PASS' or audit['records_sha256']!=hashlib.sha256(raw).hexdigest():
        raise ValueError('plot requires audited frozen records')
    records=[json.loads(line) for line in raw.splitlines()]
    rows=[]
    for series in sorted({r['series'] for r in records}):
        group=[r for r in records if r['series']==series]
        def med(contract,method):
            return float(np.median([r['seconds'] for r in group if r['contract']==contract and r['method']==method]))
        distinct=next(r for r in group if r['contract']=='distinct' and r['method']=='sweep')
        rows.append({'series':series,'family':distinct['family'],'n':distinct['n'],
                     'mean_distinct_queries':float(np.mean(distinct['query_counts'])),
                     'distinct_raster_over_sweep':med('distinct','raster')/med('distinct','sweep'),
                     'grid100_raster_over_bucket':med('grid100','raster')/med('grid100','bucket')})
    fig,axes=plt.subplots(1,2,figsize=(9.6,3.15),layout='constrained')
    styles={'NAB':('#0072B2','o'),'SMAP':('#D55E00','^'),'SMD':('#009E73','s')}
    for family,(color,marker) in styles.items():
        part=[r for r in rows if r['family']==family]
        axes[0].scatter([r['mean_distinct_queries'] for r in part],[r['distinct_raster_over_sweep'] for r in part],
                        color=color,marker=marker,s=23,alpha=.8,label=family)
        axes[1].scatter([r['n'] for r in part],[r['grid100_raster_over_bucket'] for r in part],
                        color=color,marker=marker,s=23,alpha=.8,label=family)
    for ax in axes:
        ax.axhline(1,color='.35',linestyle='--',linewidth=.8)
        ax.set_xscale('log');ax.grid(True,alpha=.16);ax.set_axisbelow(True)
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_yscale('log');axes[0].set_xlabel('Mean distinct queries per score profile')
    axes[0].set_ylabel('Raster / sweep time')
    axes[1].set_xlabel('Series length n');axes[1].set_ylabel('Raster / bucket time')
    axes[1].legend(frameon=False,fontsize=9)
    loss=next(r for r in rows if r['series'].startswith('534_SMAP'))
    axes[0].annotate(f"SMAP534: {loss['distinct_raster_over_sweep']:.3f}x",xy=(loss['mean_distinct_queries'],loss['distinct_raster_over_sweep']),
                     xytext=(18,.53),fontsize=8,arrowprops={'arrowstyle':'-','color':'.4'})
    out=ROOT/'paper/figures/range_sweep_cases';out.parent.mkdir(exist_ok=True)
    fig.savefig(out.with_suffix('.pdf'));fig.savefig(out.with_suffix('.png'),dpi=160);plt.close(fig)
    receipt={'scope':'Descriptive fixed-panel per-case median ratios; observations are not controlled interventions or independent population samples.',
             'records_sha256':audit['records_sha256'],'audit_sha256':hashlib.sha256((BASE/'independent-report.json').read_bytes()).hexdigest(),
             'rows':rows}
    (ROOT/'artifacts/pvldb-research-20261024/range-sweep/figure-data.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(f'Rendered {len(rows)} audited cases')


if __name__=='__main__':main()
