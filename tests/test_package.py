from pathlib import Path

import git
import semver

from qgis_plugin_package_ci.package import (
    _create_git_archive,
    create_archive,
)
from qgis_plugin_package_ci.parameters import load_parameters


def test_package_git_archive(rootdir: Path, fixtures: Path):
    parameters = load_parameters(fixtures)

    repo = git.Repo(search_parent_directories=True)

    plugin_relative_path = parameters.plugin_path.relative_to(repo.working_dir)
    arch = rootdir.joinpath("__test_package_git_archive__.tar")

    _create_git_archive(repo, plugin_relative_path, arch)
    assert arch.exists()
    assert arch.stat().st_size > 0


def test_package_create(rootdir: Path, fixtures: Path):
    parameters = load_parameters(fixtures)

    name = "__test_package_create__"

    expected_pkg = rootdir.joinpath(f"{name}.zip")
    if expected_pkg.exists():
        expected_pkg.unlink()

    pkg = create_archive(
        parameters,
        release_version=semver.Version.parse("1.2.3"),
        archive_dest=rootdir,
        archive_name="__test_package_create__",
    )
    print("::test_package_create::", pkg)
    assert pkg == expected_pkg
    assert pkg.exists()

    # XXX Check content
