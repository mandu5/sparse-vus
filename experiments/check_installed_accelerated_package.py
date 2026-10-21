"""Smoke-check the installed accelerated wheel, outside the source checkout.

Run after the separate NumPy-only wheel check, in a fresh environment with
the wheel's accelerate extra installed. This is packaging/parity verification,
not a timing experiment; JIT initialization is intentionally included.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import tomllib


def installed_package(repository, package_file, distribution, prefix):
    """Reject checkout imports or a package unrelated to the installed metadata."""
    installed = Path(package_file).resolve().parent
    if installed.is_relative_to(Path(repository).resolve()):
        raise AssertionError("Smoke check imported repository source, not the installed wheel")
    expected = Path(distribution.locate_file("sparse_vus")).resolve()
    if installed != expected:
        raise AssertionError("Imported package does not belong to the installed distribution")
    if not installed.is_relative_to(Path(prefix).resolve()):
        raise AssertionError("Installed package is outside the active Python environment")
    return installed


def main():
    import numpy as np
    import sparse_vus
    from sparse_vus.radix import sparse_pr_radix_jit, sparse_vus_radix_jit

    repository = Path(__file__).resolve().parents[1]
    distribution = importlib.metadata.distribution("sparse-vus")
    installed = installed_package(repository, sparse_vus.__file__, distribution, sys.prefix)
    source = repository / "src/sparse_vus"
    originals = {path.relative_to(source): path for path in source.rglob("*.py")}
    packaged = {path.relative_to(installed): path for path in installed.rglob("*.py")}
    if originals.keys() != packaged.keys():
        raise AssertionError("Installed module inventory differs from source")
    for name, path in originals.items():
        if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(packaged[name].read_bytes()).digest():
            raise AssertionError("Installed source bytes differ: " + name.as_posix())
    declared = tomllib.loads((repository / "pyproject.toml").read_text())["project"]["version"]
    version = distribution.version
    if version != declared:
        raise AssertionError("Installed distribution version differs from pyproject.toml")

    cases = [
        ([0, 1, 0, 0, 1, 0], [1, 2, 3, 4, 5, 6], 4),
        ([0, 1], [-0., 0.], 0),
        ([1, 0, 1, 0], [-4., -1., -1., -2.], 3),
        ([0, 1, 0, 1], np.array([2**53, 2**53 + 1, 0, 1], dtype=np.uint64), 2),
    ]
    for labels, scores, width in cases:
        expected = sparse_vus.sparse_vus(labels, scores, width)
        pair = sparse_vus_radix_jit(labels, scores, max_buffer=width)
        pr = sparse_pr_radix_jit(labels, scores, max_buffer=width)
        np.testing.assert_allclose(pair, expected, rtol=0, atol=1e-11)
        np.testing.assert_allclose(pr, expected[1], rtol=0, atol=1e-11)
        if not isinstance(pair, tuple) or len(pair) != 2 or type(pr) is not float:
            raise AssertionError("Public radix return contract differs")
    np.testing.assert_allclose(sparse_vus_radix_jit(*cases[0]),
                               (0.6892652251673258, 0.6834092121537311), rtol=0, atol=1e-12)
    if sparse_pr_radix_jit([0, 1], [-0., 0.], 0) != .5:
        raise AssertionError("Signed-zero tie semantics differ")
    print(json.dumps({"status": "PASS", "scope": "installed accelerated wheel; no timing claim",
                      "version": version, "source_identical_modules": len(originals),
                      "parity_cases": len(cases), "numpy": np.__version__,
                      "numba": importlib.metadata.version("numba")}))


if __name__ == "__main__":
    main()
