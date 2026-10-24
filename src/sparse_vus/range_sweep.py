"""Flat reciprocal-cardinality range PR/F1 at strict score thresholds.

Research prototype. Standard mathematical ranges include all-one inputs.
``tsb_compat`` preserves the pinned TSB-AD all-one range-parser behavior.
No detector accuracy or optimal deployment threshold is inferred.
"""
import numpy as np
from numba import njit


def _validate(labels, scores, thresholds, alpha):
    y, x, t = np.asarray(labels), np.asarray(scores), np.asarray(thresholds)
    if y.ndim != 1 or x.ndim != 1 or t.ndim != 1 or not len(y) or len(y) != len(x):
        raise ValueError('nonempty aligned vectors and one-dimensional thresholds required')
    if not np.all((y == 0) | (y == 1)) or not np.isfinite(x).all() or np.isnan(t).any():
        raise ValueError('binary labels, finite scores, non-NaN thresholds required')
    if not np.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError('alpha must lie in [0,1]')
    return y.astype(np.int8), x.astype(np.float64), t.astype(np.float64)


def _prepare(y, x, t):
    edges = np.diff(np.r_[0, y, 0])
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1) - 1
    ids = np.full(len(y), -1, np.int64)
    for j, (a, b) in enumerate(zip(starts, ends)):
        ids[a:b+1] = j
    pref = np.r_[0, np.cumsum(y, dtype=np.int64)]
    start_marks = np.zeros(len(y), np.int64)
    start_marks[starts] = 1
    spref = np.r_[0, np.cumsum(start_marks)]
    return y, x, t, ids, starts, ends, pref, spref


@njit(cache=True)
def _component(a, b, pref, spref, ids):
    mass = pref[b+1] - pref[a]
    if mass == 0:
        return 0.
    count = spref[b+1] - spref[a]
    if ids[a] >= 0 and spref[a+1] == spref[a]:
        count += 1
    return mass / ((b-a+1)*count)


@njit(cache=True)
def _raster(y, x, t, alpha, compat):
    """Fused linear scan, constant reducer space, no per-threshold arrays."""
    n = len(x)
    out = np.zeros((len(t), 3))
    if compat and np.all(y):
        return out
    for q in range(len(t)):
        pc, ps, active_count, start = 0, 0., 0, -1
        k, rs, true_start = 0, 0., -1
        pmass, pover, tmass, tover = 0, 0, 0, 0
        previous = False
        for i in range(n):
            active = x[i] > t[q]
            new_true = y[i] != 0 and (i == 0 or y[i-1] == 0)
            if new_true:
                true_start, tmass, tover = i, 0, 0
            if active:
                active_count += 1
                if not previous:
                    start, pmass, pover = i, 0, 0
                if y[i]:
                    pmass += 1
                    tmass += 1
                    if new_true or not previous:
                        pover += 1
                        tover += 1
            elif previous:
                if pmass:
                    ps += pmass/((i-start)*pover)
                pc += 1
            if y[i] and (i+1 == n or y[i+1] == 0):
                k += 1
                if tmass:
                    rs += alpha+(1-alpha)*tmass/((i-true_start+1)*tover)
            previous = active
        if previous:
            if pmass:
                ps += pmass/((n-start)*pover)
            pc += 1
        r = rs/k if k else 0.
        p = ps/pc if pc else 0.
        if compat and active_count == n and k:
            p, r = 0., alpha
        out[q, 0], out[q, 1] = p, r
        out[q, 2] = 2*p*r/(p+r) if p+r else 0.
    return out


@njit(cache=True)
def _sweep(x, t, order, ids, lengths, pref, spref, alpha, compat):
    n, k = len(x), len(lengths)
    out = np.zeros((len(t), 3))
    if not k or (compat and pref[-1] == n):
        return out
    active = np.zeros(n, np.bool_)
    left, right = np.empty(n, np.int64), np.empty(n, np.int64)
    mass, count = np.zeros(k, np.int64), np.zeros(k, np.int64)
    pc, hit, pos = 0, 0, 0
    ps, rs, pcomp, rcomp = 0., 0., 0., 0.
    for q in range(len(t)):
        while pos < n and x[order[pos]] > t[q]:
            i = order[pos]
            a, b, change = i, i, 0.
            lhit, rhit = i > 0 and active[i-1], i+1 < n and active[i+1]
            if lhit:
                a = left[i-1]
                change -= _component(a, i-1, pref, spref, ids)
            if rhit:
                b = right[i+1]
                change -= _component(i+1, b, pref, spref, ids)
            change += _component(a, b, pref, spref, ids)
            delta = change - pcomp
            updated = ps + delta
            pcomp = (updated-ps)-delta
            ps = updated
            pc += 1 - int(lhit) - int(rhit)
            j = ids[i]
            if j >= 0:
                old = mass[j]/(lengths[j]*count[j]) if mass[j] else 0.
                if mass[j] == 0:
                    hit += 1
                mass[j] += 1
                count[j] += 1
                if lhit and ids[i-1] == j:
                    count[j] -= 1
                if rhit and ids[i+1] == j:
                    count[j] -= 1
                change = mass[j]/(lengths[j]*count[j]) - old
                delta = change - rcomp
                updated = rs + delta
                rcomp = (updated-rs)-delta
                rs = updated
            left[b], right[a], active[i] = a, b, True
            pos += 1
        p = max(0., ps/pc) if pc else 0.
        r = (alpha*hit+(1-alpha)*rs)/k
        if compat and pos == n:
            p, r = 0., alpha
        out[q, 0], out[q, 1] = p, r
        out[q, 2] = 2*p*r/(p+r) if p+r else 0.
    return out


def _prefix(y, x, t, starts, ends, pref, spref, ids, alpha, compat):
    out = np.zeros((len(t), 3))
    k, n = len(starts), len(y)
    if not k or (compat and pref[-1] == n):
        return out
    lengths = ends-starts+1
    for q, threshold in enumerate(t):
        pred = x > threshold
        edges = np.diff(np.r_[0, pred, 0])
        a, b = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)-1
        if not len(a):
            continue
        ppref = np.r_[0, np.cumsum(pred, dtype=np.int64)]
        marks = np.zeros(n, np.int64)
        marks[a] = 1
        pstarts = np.r_[0, np.cumsum(marks)]
        mass = ppref[ends+1]-ppref[starts]
        counts = pstarts[ends+1]-pstarts[starts]+pred[starts]-marks[starts]
        good = mass > 0
        r = (alpha*np.count_nonzero(good)+(1-alpha)*np.sum(mass[good]/(lengths[good]*counts[good])))/k
        pmass = pref[b+1]-pref[a]
        pcounts = spref[b+1]-spref[a]+y[a]-(spref[a+1]-spref[a])
        goodp = pmass > 0
        p = np.sum(pmass[goodp]/((b[goodp]-a[goodp]+1)*pcounts[goodp]))/len(a)
        if compat and pred.all():
            p, r = 0., alpha
        out[q] = p, r, 2*p*r/(p+r) if p+r else 0.
    return out


@njit(cache=True)
def _bucket_order(bins, h):
    counts = np.zeros(h+1, np.int64)
    for b in bins:
        counts[b] += 1
    offsets = np.zeros(h+1, np.int64)
    for i in range(1, h+1):
        offsets[i] = offsets[i-1]+counts[i-1]
    order = np.empty(len(bins), np.int64)
    for i in range(len(bins)):
        b = bins[i]
        order[offsets[b]] = i
        offsets[b] += 1
    return order


def range_metrics(method, labels, scores, thresholds, *, alpha=.2, tsb_compat=False):
    """Return columns precision, recall, F1; every prediction is score > t.

    ``sweep`` uses a 1-D endpoint merge, not disjoint-set search. Total cost
    includes sorting scores/queries and common validation/preprocessing.
    ``bucket`` groups activations by the first eligible ordered query, avoiding
    score sorting when H is small. ``raster`` is a fused linear-per-query control.
    """
    y, x, t = _validate(labels, scores, thresholds, alpha)
    if method == 'raster':
        return _raster(y, x, t, alpha, tsb_compat)
    y, x, t, ids, starts, ends, pref, spref = _prepare(y, x, t)
    if method == 'prefix':
        return _prefix(y, x, t, starts, ends, pref, spref, ids, alpha, tsb_compat)
    if method not in ('sweep', 'bucket'):
        raise ValueError('unknown method')
    query_order = np.argsort(t, kind='stable')[::-1]
    if method == 'sweep':
        score_order = np.argsort(x, kind='stable')[::-1]
    else:
        bins = len(t)-np.searchsorted(t[query_order][::-1], x, side='left')
        score_order = _bucket_order(bins, len(t))
    result = _sweep(x, t[query_order], score_order, ids, ends-starts+1, pref, spref, alpha, tsb_compat)
    restored = np.empty_like(result)
    restored[query_order] = result
    return restored
