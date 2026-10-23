"""Check installed optional tie-run APIs and source identity outside checkout."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import sys

import numpy as np
import sparse_vus
from sparse_vus import tie_runs
from check_installed_accelerated_package import installed_package

root = Path(__file__).resolve().parents[1]
dist = importlib.metadata.distribution('sparse-vus')
installed = installed_package(root, sparse_vus.__file__, dist, sys.prefix)
module = Path(tie_runs.__file__).resolve()
if module.parent != installed:
    raise AssertionError('Tie-run module is not from installed wheel')
if hashlib.sha256(module.read_bytes()).digest() != hashlib.sha256((root/'src/sparse_vus/tie_runs.py').read_bytes()).digest():
    raise AssertionError('Installed tie-run source differs')
cases = [([0, 0, 1, 0, 0], [1., 1., 1., 1., 1.], 32),
         ([1, 1, 0, 0, 0], [0., -0., 2., 1., 2.], 0),
         ([0, 1, 0], np.array([2**60, 2**60+1, -1], dtype=np.int64), 13)]
for y, s, width in cases:
    expected = sparse_vus.dense_vus(y, s, width)
    pair = tie_runs.interval_vus_tie_runs_jit(y, s, width)
    pr = tie_runs.interval_pr_tie_runs_jit(y, s, width)
    prof = tie_runs.profile_tie_runs(y, s, width)
    np.testing.assert_allclose(pair, expected, rtol=0, atol=1e-11)
    np.testing.assert_allclose(pr, expected[1], rtol=0, atol=1e-11)
    if max(prof['events']) > 3*sum(y):
        raise AssertionError('Event bound violated')
try:
    tie_runs.interval_vus_tie_runs_jit([1, 0, 1], [1., 2., 3.], 2)
except ValueError:
    pass
else:
    raise AssertionError('Multiple intervals were not rejected')
print(json.dumps({'status': 'PASS', 'scope': 'installed tie-run APIs and source identity',
                  'cases': len(cases), 'module_sha256': hashlib.sha256(module.read_bytes()).hexdigest()}))
