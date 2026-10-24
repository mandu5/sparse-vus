"""Pinned TimeEval default range-AUC adapter for the interval control only."""
from types import MethodType

import numpy as np

from .timeeval_adapter import adapt_range_metric


def adapt_range_metric_interval_control(metric):
    """Copy a native default range metric and replace only its curve kernel.

    The supported configuration and all native validation/constant handling are
    inherited from the frozen adapter's public path. Query selection, inclusive
    masks, source dtype, endpoint conventions, recall sorting and integration
    follow TimeEval revision 7c3622757b1a3afa9a84cbc97ce132d9e379f715.
    """
    result = adapt_range_metric(metric, 'public')

    def _range_precision_recall_curve(self, y_true, y_score):
        from .weighted_range_control import weighted_range_interval_control

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
        if len(thresholds) and not np.any(y_true == 1):
            raise AssertionError('pinned prts requires a positive ground-truth point')
        strict = np.nextafter(thresholds.astype(np.float64), -np.inf)
        values = weighted_range_interval_control(
            y_true, y_score, strict, alpha=0, cardinality='one',
            precision_bias='flat', recall_bias='flat')
        recalls, precisions = np.zeros_like(thresholds), np.zeros_like(thresholds)
        recalls[:], precisions[:] = values[:, 1], values[:, 0]
        sorted_idx = np.lexsort((precisions * (-1), recalls))[::-1]
        return (np.r_[p0, precisions[sorted_idx], 1],
                np.r_[r0, recalls[sorted_idx], 0], thresholds)

    # The callback name selects the PR integration axes in the native AucMetric.
    result._range_precision_recall_curve = MethodType(_range_precision_recall_curve, result)
    return result
