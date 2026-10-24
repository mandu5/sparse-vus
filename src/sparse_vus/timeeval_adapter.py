"""Preserve the pinned TimeEval default range-AUC consumer boundary.

TimeEval remains an optional dependency. This adapter changes only the range
curve kernel of its default RANGE_PR_AUC metric. Native validation, constant
handling, endpoints, query sampling, curve ordering and integration stay active.
"""
from copy import deepcopy
from types import MethodType

import numpy as np


def adapt_range_metric(metric, method):
    """Return an independent native metric using ``raster`` or ``bucket``.

The supported contract is TimeEval 7c3622757b1a3afa9a84cbc97ce132d9e379f715's
default RANGE_PR_AUC: zero existence weight, flat bias and cardinality one.
The public implementation's own max_samples setting is retained. This is not
an adapter for its optional reciprocal metric or for arbitrary prts policies.
    """
    if method not in ('public', 'raster', 'bucket'):
        raise ValueError('method must be public, raster, or bucket')
    if (getattr(metric, '_r_alpha', None) != 0
            or getattr(metric, '_p_alpha', None) != 0
            or getattr(metric, '_cardinality', None) != 'one'
            or getattr(metric, '_bias', None) != 'flat'):
        raise ValueError('adapter requires the native default range metric configuration')
    result = deepcopy(metric)
    if method == 'public':
        return result

    def _range_precision_recall_curve(self, y_true, y_score):
        from .weighted_range import weighted_range_metrics

        thresholds = np.unique(y_score)
        thresholds.sort()
        p0, r0 = y_true.sum() / len(y_true), 1.0
        thresholds = thresholds[1:]
        n_thresholds = thresholds.shape[0]
        if n_thresholds > self._max_samples:
            every_nth = n_thresholds // (self._max_samples - 1)
            sampled_thresholds = thresholds[::every_nth]
            if thresholds[-1] == sampled_thresholds[-1]:
                thresholds = sampled_thresholds
            else:
                thresholds = np.r_[sampled_thresholds, thresholds[-1]]
        # prts 1.0.0.3 rejects no-positive labels. The native constant-score
        # shortcut happens in Metric.__call__ before this method is reached.
        if len(thresholds) and not np.any(y_true == 1):
            raise AssertionError('pinned prts requires a positive ground-truth point')
        strict = np.nextafter(thresholds.astype(np.float64), -np.inf)
        values = weighted_range_metrics(method, y_true, y_score, strict,
                                        alpha=0, cardinality='one',
                                        precision_bias='flat', recall_bias='flat')
        recalls, precisions = np.zeros_like(thresholds), np.zeros_like(thresholds)
        recalls[:], precisions[:] = values[:, 1], values[:, 0]
        sorted_idx = np.lexsort((precisions * (-1), recalls))[::-1]
        return (np.r_[p0, precisions[sorted_idx], 1],
                np.r_[r0, recalls[sorted_idx], 0], thresholds)

    # AucMetric._auc uses the callback name to select the precision/recall axes.
    result._range_precision_recall_curve = MethodType(_range_precision_recall_curve, result)
    return result
