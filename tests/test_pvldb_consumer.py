import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))


def test_public_consumer_keeps_all_nine_outputs_under_exact_pair_replacement():
    if not (ROOT / '.cache/tsbad-consumer/pkg/TSB_AD/evaluation/metrics.py').exists():
        pytest.skip('optional pinned TSB-AD consumer cache absent')
    from pvldb_consumer import evaluate_profile
    y = np.zeros(32, np.int8)
    y[7:11] = 1
    y[21:24] = 1
    x = np.random.default_rng(13).normal(size=32)
    a, ta = evaluate_profile('benchopt_pair', y, x, 8)
    b, tb = evaluate_profile('radix_pair', y, x, 8)
    assert len(a) == len(b) == 9
    assert set(a) == set(b)
    for name in a:
        assert np.isfinite(a[name])
        assert a[name] == pytest.approx(b[name], abs=1e-11)
    assert ta > 0 and tb > 0


@pytest.mark.parametrize('corruption', ['missing', 'metric', 'vus_sum', 'nested_time', 'all_wrong_width'])
def test_trace_audit_rejects_corruption(corruption):
    import copy
    from audit_pvldb_consumer import KEYS, reconstruct
    p = {'order': ['benchopt_pair', 'radix_pair', 'radix_pair', 'benchopt_pair'],
         'model_count': 2, 'parity_atol': 1e-11, 'case': {'series': 'fixture', 'n': 32}}
    rows = [{'trial': t, 'model': m, 'method': method, 'width': 8,
             'seconds': .2, 'vus_seconds': .1, 'metrics': {k: .5 for k in KEYS}}
            for t, method in enumerate(p['order']) for m in range(2)]
    workflows = [{'trial': t, 'method': method, 'series': 'fixture', 'width': 8,
                  'seconds': .5, 'vus_seconds': .2, 'outputs': [{k: .5 for k in KEYS} for _ in range(2)]}
                 for t, method in enumerate(p['order'])]
    assert reconstruct(p, rows, workflows, 8)['metric_calls'] == 8
    rows, workflows = copy.deepcopy(rows), copy.deepcopy(workflows)
    if corruption == 'missing':
        rows.pop()
    elif corruption == 'metric':
        rows[-1]['metrics']['VUS-PR'] = .6
    elif corruption == 'vus_sum':
        workflows[-1]['vus_seconds'] = .3
    elif corruption == 'nested_time':
        rows[-1]['vus_seconds'] = .3
    else:
        for r in rows + workflows:
            r['width'] = 0
    with pytest.raises(ValueError):
        reconstruct(p, rows, workflows, 8)


def test_fetch_rejects_preexisting_unpinned_public_source(tmp_path, monkeypatch):
    import pvldb_consumer as c
    name = 'TSB_AD/__init__.py'
    path = tmp_path / name
    path.parent.mkdir()
    path.write_text('modified upstream')
    monkeypatch.setattr(c, 'PKG', tmp_path)
    monkeypatch.setattr(c, 'ROOT', tmp_path)
    monkeypatch.setattr(c, 'FILES', [name])
    monkeypatch.setattr(c, 'OUT', tmp_path / 'absent-protocol')
    with pytest.raises(ValueError, match='pinned upstream identity'):
        c.fetch()
