"""A new ablation of pinned Klein fast-VUS, not an upstream released method.

Only the threshold-list expression changes: use every distinct score on the
maximum-width support. Global predicted-positive denominators are unchanged.
The original source and Apache-2.0 license remain intact in the verified cache.
"""
from functools import lru_cache
import hashlib
from fast_vus_adapter import CACHE, SOURCE_HASH

OLD = 'th = asc[::-1][np.linspace(0, n - 1, thre).astype(int)]'
NEW = 'th = np.unique(x[np.flatnonzero(_cover(*_merge(s, e, window // 2, n), n))])[::-1]'


def patch(source):
    if source.count(OLD)!=1:raise ValueError('expected exactly one pinned threshold expression')
    return source.replace(OLD,NEW,1)


@lru_cache(maxsize=1)
def load():
    path=CACHE/'fast_vus.py';raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_HASH:raise ValueError('Klein source identity mismatch')
    namespace={'__name__':'klein_support_ablation','__file__':str(path)}
    exec(compile(patch(raw.decode()),str(path)+'[support-ablation]','exec'),namespace)
    return namespace['vus_pr']


def klein_support_pr(labels,scores,width):
    return load()(labels,scores,width,thre=len(scores))
