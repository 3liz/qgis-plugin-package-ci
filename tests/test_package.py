from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

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

    release_version = semver.Version.parse("1.2.3")

    pkg = create_archive(
        parameters,
        release_version=release_version,
        archive_dest=rootdir,
        archive_name="__test_package_create__",
    )
    print("::test_package_create::", pkg)
    assert pkg == expected_pkg
    assert pkg.exists()

    repo = git.Repo(search_parent_directories=True)
    commit_number = str(sum(1 for _ in repo.iter_commits()))
    commit_sha1 = repo.head.object.hexsha

    expected_metadata = f"""[general]
name = QGIS Plugin CI Testing
qgisMinimumVersion = 3.2
about = Downloading would be useless
version = {release_version}
tags = foo,bar,baz
category = plugins
experimental = False
icon = icons/opengisch.png
description = This is a testing plugin for QGIS Plugin CI
author = David Marteau
email = david@3liz.com
homepage = https://github.com/3liz/qgis-plugin-package-ci
repository = https://github.com/3liz/qgis-plugin-package-ci
tracker = https://github.com/3liz/qgis-plugin-package-ci/issues
commitNumber = {commit_number}
commitSha1 = {commit_sha1}
dateTime = {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
"""

    # Check content
    with ZipFile(pkg, "r") as zf:
        with zf.open("qgis_plugin_ci_testing/metadata.txt") as md:
            metadata = md.read().decode()
            print("====================", metadata)
            assert metadata.strip("\n") == expected_metadata.strip("\n")
