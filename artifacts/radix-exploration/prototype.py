"""Exploratory only. Never imported into production or the frozen benchmark."""
import sys
from pathlib import Path
import numpy as np
from numba import njit
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from sparse_vus.core import _validate_inputs, ranges, expanded_ranges
from sparse_vus.pr_compiled import _sparse_pr_kernel

@njit(cache=True)
def descending_keys(scores):
    bits=scores.view(np.uint64)
    keys=np.empty(len(scores),dtype=np.uint64)
    sign=np.uint64(1)<<np.uint64(63)
    for i in range(len(scores)):
        # Python and NumPy regard signed zeros as one score tie.
        u=np.uint64(0) if scores[i] == 0. else bits[i]
        ascending=~u if u & sign else u ^ sign
        keys[i]=~ascending
    return keys

def order_u16(keys):
    # Four stable least-significant 16-bit digit sorts. uint16 stable argsort
    # dispatches to aradixsort_ushort in NumPy 1.26.4; uint64 does not.
    order=np.arange(len(keys),dtype=np.int64)
    mask=np.uint64(65535)
    for shift in (0,16,32,48):
        digit=((keys[order]>>np.uint64(shift))&mask).astype(np.uint16)
        order=order[np.argsort(digit,kind='stable')]
    return order

@njit(cache=True)
def order_counting(keys):
    # True eight-pass stable LSD radix, fixed uint64 words, no comparison sort.
    n=len(keys)
    order=np.arange(n,dtype=np.int64)
    scratch=np.empty(n,dtype=np.int64)
    counts=np.zeros(256,dtype=np.int64)
    for shift in range(0,64,8):
        counts[:]=0
        for i in range(n):
            counts[int((keys[order[i]]>>np.uint64(shift)) & np.uint64(255))]+=1
        offset=0
        for b in range(256):
            count=counts[b]
            counts[b]=offset
            offset+=count
        for i in range(n):
            index=order[i]
            digit=int((keys[index]>>np.uint64(shift))&np.uint64(255))
            scratch[counts[digit]]=index
            counts[digit]+=1
        order,scratch=scratch,order
    return order

@njit(cache=True)
def nearest_two_linear(pos, starts, ends):
    d1=np.empty(len(pos),dtype=np.float64)
    d2=np.empty(len(pos),dtype=np.float64)
    k=0
    for i in range(len(pos)):
        x=pos[i]
        while k < len(starts) and starts[k] <= x:
            k+=1
        first,second=np.inf,np.inf
        for j in range(max(0,k-2),min(len(starts),k+2)):
            d=float(max(starts[j]-x,x-ends[j],0))
            if d < first:
                second,first=first,d
            elif d < second:
                second=d
        d1[i],d2[i]=first,second
    return d1,d2

@njit(cache=True)
def support_ranks(keys,order,support_index,q):
    group=np.empty(q,dtype=np.int64)
    before=np.empty(q,dtype=np.int64)
    after=np.empty(q,dtype=np.int64)
    rank,event,n=0,0,len(order)
    while rank < n:
        start=rank
        key=keys[order[rank]]
        found=False
        while rank < n and keys[order[rank]] == key:
            si=support_index[order[rank]]
            if si >= 0:
                group[si]=event
                found=True
            rank+=1
        if found:
            before[event],after[event]=start,rank
            event+=1
    return group,before[:event],after[:event]

def prepare_radix(y,scores,max_buffer,mode='counting'):
    y,scores=_validate_inputs(y,scores,max_buffer)
    starts,ends=ranges(y)
    lo,hi=expanded_ranges(starts,ends,len(y),max_buffer)
    pos=np.concatenate([np.arange(a,b+1) for a,b in zip(lo,hi)])
    original=y[pos].astype(bool)
    d1,d2=nearest_two_linear(pos,starts,ends)
    support_index=np.full(len(y),-1,dtype=np.int64)
    support_index[pos]=np.arange(len(pos))
    keys=descending_keys(scores)
    if mode == 'u16':
        order=order_u16(keys)
    elif mode == 'counting':
        order=order_counting(keys)
    elif mode == 'u64_timsort':
        order=np.argsort(keys,kind='stable')
    else:
        raise ValueError(mode)
    group,before,after=support_ranks(keys,order,support_index,len(pos))
    return y,scores,starts,ends,pos,original,d1,d2,group,before,after,support_index

def sparse_pr_radix(y,scores,width,mode='counting'):
    y,_,starts,ends,pos,original,d1,d2,group,_,after,_=prepare_radix(y,scores,width,mode)
    return float(_sparse_pr_kernel(len(y),float(y.sum()),starts,ends,pos,original,d1,d2,group,after,width))
