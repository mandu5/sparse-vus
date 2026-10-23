"""Check installed sampling APIs against exact rational, cache-free examples."""
from fractions import Fraction
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np
import sparse_vus
from sparse_vus import sampling, sampling_bounds
from check_installed_accelerated_package import installed_package

root = Path(__file__).resolve().parents[1]
dist = importlib.metadata.distribution("sparse-vus")
installed = installed_package(root, sparse_vus.__file__, dist, sys.prefix)
identities = {}
for module in (sampling, sampling_bounds):
    path = Path(module.__file__).resolve()
    if path.parent != installed:
        raise AssertionError("Sampling module is not from installed wheel")
    expected = root / "src/sparse_vus" / path.name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != hashlib.sha256(expected.read_bytes()).hexdigest():
        raise AssertionError("Installed sampling source differs")
    identities[path.name] = digest

labels = np.array([0, 1, 1, 0], dtype=np.int8)
scores = np.array([4., 3., 2., 1.])
# With zero buffer, exact right-step AP is (1/2)(1/2)+(1/2)(2/3).
expected = Fraction(7, 12)
for budget in (2, 4, np.uint64(9)):
    cert = sampling_bounds.certified_sampled_pr(labels, scores, np.int64(0), budget)
    lo = Fraction(cert.lower_numerator, cert.scale)
    hi = Fraction(cert.upper_numerator, cert.scale)
    if not lo <= expected <= hi:
        raise AssertionError("Certificate misses exact rational target")
    if Fraction.from_float(cert.lower) > lo or Fraction.from_float(cert.upper) < hi:
        raise AssertionError("Display endpoints are not outward")
    sampled = sampling.sampled_pr_radix_jit(labels, scores, 0, budget)
    target = .5 if budget == 2 else float(expected)
    if abs(sampled-target) > 1e-15:
        raise AssertionError("Installed sampled integral differs")

winner = sampling_bounds.certified_sampled_pr(labels, [0, 3, 2, 1], 0, 4)
loser = sampling_bounds.certified_sampled_pr(labels, [4, 2, 1, 3], 0, 4)
if not winner.certifies_greater_than(loser):
    raise AssertionError("Exact integer ordering decision failed")
if loser.certifies_greater_than(winner):
    raise AssertionError("Reversed exact integer ordering decision")
print(json.dumps({"status": "PASS", "scope": "installed source identity, rational AP enclosure, outward display and integer ordering",
                  "budgets": [2, 4, 9], "module_sha256": identities}, sort_keys=True))
