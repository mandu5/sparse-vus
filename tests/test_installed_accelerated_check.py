"""Installation identity checks; no compilation, downloads, or metric calls."""
import importlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))


class DistributionFixture:
    def __init__(self, root):
        self.root = root

    def locate_file(self, relative):
        return self.root / relative


def check():
    return importlib.import_module("check_installed_accelerated_package").installed_package


def test_package_must_match_distribution_inside_active_environment(tmp_path):
    repository, environment = tmp_path / "checkout", tmp_path / "venv"
    site = environment / "lib/python3.12/site-packages"
    package = site / "sparse_vus"
    assert check()(repository, package / "__init__.py", DistributionFixture(site), environment) == package.resolve()


def test_identical_external_source_cannot_impersonate_installed_wheel(tmp_path):
    repository, environment = tmp_path / "checkout", tmp_path / "venv"
    site = environment / "lib/python3.12/site-packages"
    package = site / "sparse_vus"
    external = tmp_path / "other-checkout/sparse_vus"
    for directory in (package, external):
        directory.mkdir(parents=True)
        (directory / "__init__.py").write_text("# identical source bytes\n")
    with pytest.raises(AssertionError, match="does not belong"):
        check()(repository, external / "__init__.py", DistributionFixture(site), environment)


def test_matching_distribution_outside_active_environment_is_rejected(tmp_path):
    site = tmp_path / "other-environment/site-packages"
    with pytest.raises(AssertionError, match="outside the active"):
        check()(tmp_path / "checkout", site / "sparse_vus/__init__.py",
                DistributionFixture(site), tmp_path / "venv")


def test_checkout_import_is_rejected_even_when_metadata_agrees(tmp_path):
    repository = tmp_path / "checkout"
    with pytest.raises(AssertionError, match="repository source"):
        check()(repository, repository / "src/sparse_vus/__init__.py",
                DistributionFixture(repository / "src"), repository)
