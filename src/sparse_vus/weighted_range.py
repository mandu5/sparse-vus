"""Exact threshold trajectories for canonical position-weighted range metrics.

Supports flat/front/back/middle weights and one/reciprocal/TimeSeAD-improved
local cardinality. Integer prefix moments avoid cancellation in weighted overlap.
All predictions use binary64 score > threshold. Empty-base averages are zero.
Optional length-weighted precision uses *all* predicted windows in its denominator;
it does not emulate TimeSeAD's trailing-window denominator discrepancy.
"""
import numpy as np
from numba import njit

from .range_sweep import _bucket_order

_BIASES = {'flat':0, 'front':1, 'back':2, 'middle':3}
_CARDINALITIES = {'one':0, 'reciprocal':1, 'improved':2}


@njit(cache=True)
def _normalizer(length, bias):
    if bias == 0: return length
    if bias < 3: return length*(length+1)//2
    half=length//2
    return (half+1)*(length-half)


@njit(cache=True)
def _point_weight(i, a, b, bias):
    if bias == 0: return 1
    if bias == 1: return b-i+1
    if bias == 2: return i-a+1
    return min(i-a+1,b-i+1)


@njit(cache=True)
def _gamma(count, length, cardinality):
    if cardinality == 0: return 1.
    if cardinality == 1: return 1./count
    if count == 1: return 1.
    # Avoid amplifying the rounded near-one base for long fragmented windows.
    return np.exp((count-1)*np.log1p(-1./length))


@njit(cache=True)
def _weighted_overlap(a,b,pref,moments,bias):
    count=pref[b+1]-pref[a]
    if bias == 0: return count
    moment=moments[b+1]-moments[a]
    if bias == 1: return (b+1)*count-moment
    if bias == 2: return moment-(a-1)*count
    mid=(a+b)//2
    lc=pref[mid+1]-pref[a]
    lm=moments[mid+1]-moments[a]
    return lm-(a-1)*lc+(b+1)*(count-lc)-(moment-lm)


@njit(cache=True)
def _component(a,b,pref,moments,spref,ids,bias,cardinality,weighted):
    if pref[b+1] == pref[a]: return 0.
    count=spref[b+1]-spref[a]
    if ids[a]>=0 and spref[a+1]==spref[a]:count+=1
    length=b-a+1
    value=(_weighted_overlap(a,b,pref,moments,bias)/_normalizer(length,bias)
           *_gamma(count,length,cardinality))
    return value*length if weighted else value


@njit(cache=True)
def _raster(y,x,t,starts,ends,alpha,pbias,rbias,cardinality,weighted):
    """Independent recomputation with O(n) work/query and O(1) reducers."""
    out=np.zeros((len(t),3));n=len(y);k=len(starts)
    for q in range(len(t)):
        rs=0.
        for j in range(k):
            a,b=starts[j],ends[j];mass=0;count=0;previous=False
            for i in range(a,b+1):
                active=x[i]>t[q]
                if active:
                    mass+=_point_weight(i,a,b,rbias)
                    if not previous:count+=1
                previous=active
            if count:
                rs+=alpha+(1-alpha)*mass/_normalizer(b-a+1,rbias)*_gamma(count,b-a+1,cardinality)
        ps=0.;denom=0;i=0
        while i<n:
            if x[i]<=t[q]:
                i+=1
                continue
            a=i
            while i<n and x[i]>t[q]:i+=1
            b=i-1;length=b-a+1;mass=0;count=0;previous=False
            for j in range(a,b+1):
                if y[j]:
                    mass+=_point_weight(j,a,b,pbias)
                    if not previous:count+=1
                previous=y[j]!=0
            denom+=length if weighted else 1
            if count:
                contribution=mass/_normalizer(length,pbias)*_gamma(count,length,cardinality)
                ps+=contribution*length if weighted else contribution
        p=ps/denom if denom else 0.;r=rs/k if k else 0.
        out[q,0],out[q,1]=p,r
        out[q,2]=2*p*r/(p+r) if p+r else 0.
    return out


@njit(cache=True)
def _sweep(x,t,order,ids,starts,ends,pref,moments,spref,alpha,pbias,rbias,cardinality,weighted):
    n=len(x);k=len(starts);out=np.zeros((len(t),3))
    if not k:return out
    active=np.zeros(n,np.bool_);left=np.empty(n,np.int64);right=np.empty(n,np.int64)
    mass=np.zeros(k,np.int64);count=np.zeros(k,np.int64)
    pc,hit,pos=0,0,0;ps,rs,pcomp,rcomp=0.,0.,0.,0.
    for q in range(len(t)):
        while pos<n and x[order[pos]]>t[q]:
            i=order[pos];a,b,change=i,i,0.
            lhit=i>0 and active[i-1];rhit=i+1<n and active[i+1]
            if lhit:
                a=left[i-1]
                change-=_component(a,i-1,pref,moments,spref,ids,pbias,cardinality,weighted)
            if rhit:
                b=right[i+1]
                change-=_component(i+1,b,pref,moments,spref,ids,pbias,cardinality,weighted)
            change+=_component(a,b,pref,moments,spref,ids,pbias,cardinality,weighted)
            delta=change-pcomp;updated=ps+delta;pcomp=(updated-ps)-delta;ps=updated
            pc+=1-int(lhit)-int(rhit)
            j=ids[i]
            if j>=0:
                length=ends[j]-starts[j]+1
                old=mass[j]/_normalizer(length,rbias)*_gamma(count[j],length,cardinality) if count[j] else 0.
                if count[j]==0:hit+=1
                mass[j]+=_point_weight(i,starts[j],ends[j],rbias)
                count[j]+=1-int(lhit and ids[i-1]==j)-int(rhit and ids[i+1]==j)
                change=mass[j]/_normalizer(length,rbias)*_gamma(count[j],length,cardinality)-old
                delta=change-rcomp;updated=rs+delta;rcomp=(updated-rs)-delta;rs=updated
            left[b],right[a],active[i]=a,b,True
            pos+=1
        denom=pos if weighted else pc
        p=max(0.,ps/denom) if denom else 0.
        r=max(0.,(alpha*hit+(1-alpha)*rs)/k)
        out[q,0],out[q,1]=p,r
        out[q,2]=2*p*r/(p+r) if p+r else 0.
    return out


def weighted_range_metrics(method, labels, scores, thresholds, *, alpha=.2,
                           precision_bias='flat', recall_bias='flat',
                           cardinality='reciprocal', weighted_precision=False):
    """Return H×3 precision, recall, F1, including complete strict score ties.

    Canonical positional weights use integer coordinates relative to each window.
    n <= 2**31-1 bounds every intermediate int64 product/prefix moment. Real
    finite binary64 scores are required; integer magnitudes >2**53 are rejected
    rather than silently coalescing score classes. Threshold infinities are valid.
    Sweep: O(n log n + H log H + n + H). Bucket: O(n log(H+1)+H log H+n+H).
    """
    if method not in ('raster','sweep','bucket'):raise ValueError('unknown method')
    if precision_bias not in _BIASES or recall_bias not in _BIASES:raise ValueError('unknown positional bias')
    if cardinality not in _CARDINALITIES:raise ValueError('unknown cardinality')
    if not isinstance(weighted_precision,(bool,np.bool_)):raise ValueError('weighted_precision must be boolean')
    try:
        y,x,t=np.asarray(labels),np.asarray(scores),np.asarray(thresholds)
        if y.ndim!=1 or x.ndim!=1 or t.ndim!=1 or not len(y) or len(y)!=len(x):raise ValueError('aligned nonempty vectors required')
        if len(y)>2**31-1:raise ValueError('integer-moment domain exceeded')
        if y.dtype.kind not in 'biuf' or x.dtype.kind not in 'biuf' or t.dtype.kind not in 'biuf':raise ValueError('real numeric arrays required')
        if not np.all((y==0)|(y==1)):raise ValueError('binary labels required')
        for v in (x,t):
            if v.dtype.kind in 'iu' and (np.any(v>2**53) or np.any(v<-(2**53))):raise ValueError('integer score/threshold cannot be silently rounded')
        y=y.astype(np.int8);x=x.astype(np.float64);t=t.astype(np.float64);alpha=float(alpha)
        if not np.isfinite(x).all() or np.isnan(t).any():raise ValueError('finite scores and non-NaN queries required')
        if not np.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('alpha must lie in [0,1]')
    except (TypeError,OverflowError) as exc:
        raise ValueError('invalid numeric domain') from exc
    edges=np.diff(np.r_[0,y,0]);starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)-1
    pb,rb,card=_BIASES[precision_bias],_BIASES[recall_bias],_CARDINALITIES[cardinality]
    if method=='raster':return _raster(y,x,t,starts,ends,alpha,pb,rb,card,weighted_precision)
    ids=np.full(len(y),-1,np.int64)
    for j,(a,b) in enumerate(zip(starts,ends)):ids[a:b+1]=j
    pref=np.r_[0,np.cumsum(y,dtype=np.int64)]
    moments=np.r_[0,np.cumsum(np.arange(len(y),dtype=np.int64)*y,dtype=np.int64)]
    marks=np.zeros(len(y),np.int64);marks[starts]=1;spref=np.r_[0,np.cumsum(marks)]
    qo=np.argsort(t,kind='stable')[::-1]
    if method=='sweep':order=np.argsort(x,kind='stable')[::-1]
    else:
        bins=len(t)-np.searchsorted(t[qo][::-1],x,side='left')
        order=_bucket_order(bins,len(t))
    result=_sweep(x,t[qo],order,ids,starts,ends,pref,moments,spref,alpha,pb,rb,card,weighted_precision)
    restored=np.empty_like(result);restored[qo]=result
    return restored
