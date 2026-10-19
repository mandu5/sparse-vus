"""Illustrate the exact rectangle-plus-transition identity on a fixed example."""
from pathlib import Path
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from sparse_vus.core import ranges, expanded_ranges, sparse_vus


def main():
    y = np.zeros(20, dtype=int)
    y[[5, 14]] = 1
    scores = np.array([16, 3, 18, 14, 12, 17, 10, 2, 11, 19,
                       15, 7, 9, 20, 13, 5, 8, 4, 1, 6], dtype=float)
    w, n, p = 2, len(y), y.sum()
    starts, ends = ranges(y)
    weights = y.astype(float)
    for a, b in zip(starts, ends):
        for i in range(max(0, a-w//2), min(n, b+w//2+1)):
            d = max(a-i, i-b, 0)
            if d:
                weights[i] += np.sqrt(1-d/w)
    weights = np.minimum(weights, 1)
    lo, hi = expanded_ranges(starts, ends, n, w)
    support = weights > 0
    thresholds = np.sort(np.unique(scores))[::-1]
    points = [[0., 0.]]
    event = [False]
    for t in thresholds:
        pred = scores >= t
        tp = np.dot(weights, pred)
        buffer = np.dot(weights*(1-y), pred)
        positive = p+buffer/2
        hits = sum(np.any(pred[a:b+1]) for a, b in zip(lo, hi))
        points.append([(pred.sum()-tp)/(n-positive), min(tp/positive, 1)*hits/len(lo)])
        event.append(bool(np.any(support & (scores == t))))
    points.append([1., 1.]); event.append(False)
    points, event = np.array(points), np.array(event)
    dense_area = np.dot(np.diff(points[:, 0]), (points[:-1, 1]+points[1:, 1])/2)
    _, per_width, _, _ = sparse_vus(y, scores, w, return_per_buffer=True)
    assert abs(dense_area-per_width[-1]) < 1e-13
    kept = points[event]
    naive = np.vstack(([0., 0.], kept, [1., 1.]))
    naive_area = np.dot(np.diff(naive[:, 0]), (naive[:-1, 1]+naive[1:, 1])/2)

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.5), gridspec_kw={'width_ratios': [1, 1.3]})
    a, b = axes
    colors = np.where(support, '#087f8c', '#b8c0c9')
    a.bar(np.arange(n), scores, color=colors, width=.7)
    for i in np.flatnonzero(y):
        a.scatter(i, scores[i]+.8, marker='*', color='#ad5e00', s=80, zorder=4)
    a.set(xlabel='Time position', ylabel='Anomaly score', title='A. Only six positions can change positive state')
    a.set_ylim(0, 23)
    a.text(.03, .96, 'Teal: expanded support\nStars: original anomalies',
           transform=a.transAxes, va='top', fontsize=8)
    b.plot(points[:, 0], points[:, 1], color='#525d6b', lw=1.7, marker='o',
           markersize=3, label='Full threshold curve')
    b.plot(naive[:, 0], naive[:, 1], '--', color='#bb3e03', lw=1.2,
           label='Connecting support endpoints only')
    b.scatter(kept[:, 0], kept[:, 1], color='#087f8c', marker='s', s=25,
              label='Support event', zorder=5)
    first = int(np.flatnonzero(event)[0])
    second = int(np.flatnonzero(event)[1])
    x0, r0 = points[first]
    x1 = points[second-1, 0]
    b.fill_between([x0, x1], [0, 0], [r0, r0], color='#e9c46a', alpha=.65)
    b.annotate('Integrate this rectangle\nbefore the next event',
               xy=((x0+x1)/2, r0/2), xytext=(.26, .18),
               arrowprops={'arrowstyle': '->', 'lw': .8}, fontsize=8)
    b.set(xlabel='False-positive coordinate', ylabel='Range recall',
          title='B. Exact elimination retains the negative-only area', xlim=(-.02, 1.02), ylim=(-.02, 1.05))
    b.legend(loc='lower right', fontsize=7, frameon=False)
    fig.tight_layout(pad=1.5)
    folder = ROOT / 'paper/figures'; folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder/'event-elimination.png', dpi=250)
    fig.savefig(folder/'event-elimination.svg')
    plt.close(fig)
    (ROOT/'artifacts/event_illustration.json').write_text(json.dumps({
        'labels': y.tolist(), 'scores': scores.tolist(), 'buffer_width': w,
        'full_threshold_roc': float(dense_area), 'exact_event_roc': float(per_width[-1]),
        'incorrect_endpoint_only_roc': float(naive_area),
        'exact_absolute_error': float(abs(dense_area-per_width[-1])),
        'purpose': 'Fixed illustrative example, not an empirical benchmark.'}, indent=2)+'\n')


if __name__ == '__main__':
    main()
