"""Render the prespecified operating-range axes from an audited result."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--evidence',type=Path,default=ROOT/'artifacts/pvldb-research-20261024/operating-range')
    parser.add_argument('--output',type=Path,default=ROOT/'paper/figures/pvldb_operating_range')
    args=parser.parse_args()
    protocol=json.loads((args.evidence/'protocol.json').read_text())
    report=json.loads((args.evidence/'independent-report.json').read_text())
    if report['status']!='PASS' or report['protocol_sha256']!=hashlib.sha256((args.evidence/'protocol.json').read_bytes()).hexdigest():
        raise ValueError('audited protocol mismatch')
    anchor={'n':100000,'models':8,'positive_fraction':.01,'components':1,'width':30,'levels':None}
    axes=[('n','Length n'),('positive_fraction','Original positive fraction'),
          ('components','Original components K'),('models','Score columns M')]
    colors={'released':'#666666','dense':'#0072B2','external':'#D55E00'}
    labels={'released':'Released / stream','dense':'Dense / stream','external':'Klein exact / stream'}
    plt.rcParams.update({'font.size':8,'axes.labelsize':8,'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42})
    fig,axs=plt.subplots(2,2,figsize=(7.0,4.5),layout='constrained')
    for ax,(key,label) in zip(axs.flat,axes):
        chosen=sorted([c for c in protocol['controlled_cases'] if all(c[k]==v for k,v in anchor.items() if k!=key)],key=lambda c:c[key])
        x=np.array([c[key] for c in chosen])
        for method,color in colors.items():
            stats=[report['cases'][c['name']]['relative_to_stream'][method] for c in chosen]
            center=np.array([s['paired_geometric_ratio'] for s in stats]);ci=np.array([s['paired_trial_ci95'] for s in stats])
            ax.errorbar(x,center,yerr=np.array([center-ci[:,0],ci[:,1]-center]),label=labels[method],
                        color=color,marker='o',markersize=3.5,linewidth=1.2,capsize=2)
        ax.axhline(1.,color='black',linestyle=':',linewidth=.8)
        ax.set_xscale('log');ax.set_yscale('log');ax.set_xlabel(label)
        ax.set_xticks(x,[f'{v:g}' for v in x]);ax.grid(axis='y',which='major',alpha=.18)
        ax.spines[['top','right']].set_visible(False)
    axs[0,0].set_ylabel('Baseline / stream time');axs[1,0].set_ylabel('Baseline / stream time')
    handles,labels_=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels_,loc='outside upper center',ncol=3,frameon=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.output.with_suffix('.pdf'),bbox_inches='tight')
    fig.savefig(args.output.with_suffix('.png'),dpi=180,bbox_inches='tight')
    print(args.output.with_suffix('.pdf'))


if __name__=='__main__':main()
