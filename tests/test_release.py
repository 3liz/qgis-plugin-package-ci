#! /usr/bin/env python

# standard
import argparse
import filecmp
import os
import re
import unittest
import urllib.request
from itertools import product
from pathlib import Path
from tempfile import mkstemp
from zipfile import ZipFile

import pytest

# 3rd party
import yaml
from github import Github, GithubException

# Tests
from .utils import can_skip_test_github

# Project
from qgispluginci.changelog import ChangelogParser
from qgispluginci.exceptions import GithubReleaseNotFound
from qgispluginci.parameters import DASH_WARNING, Parameters
from qgispluginci.release import release
from qgispluginci.translation import Translation
from qgispluginci.utils import replace_in_file

# If changed, also update CHANGELOG.md
RELEASE_VERSION_TEST = "0.1.2"


class Setup:
    def __init__(self, fixtures: Path):
        self.setup_params = Parameters.make_from(
            path_to_config_file=fixtures.joinpath("setup.cfg")
        )
        self.qgis_plugin_config_params = Parameters.make_from(
            path_to_config_file=fixtures.joinpath(".qgis-plugin-ci")
        )
        self.pyproject_params = Parameters.make_from(
            path_to_config_file=fixtures.joinpath("pyproject.toml")
        )
        self.tx_api_token = os.getenv("tx_api_token")
        self.github_token = os.getenv("github_token")
        self.repo = None
        self.t = None
        if self.github_token:
            print("init Github")
            self.repo = Github(self.github_token).get_repo("opengisch/qgis-plugin-ci")
        self.clean_assets()

    def clean_assets(self):
        if self.repo:
            rel = None
            try:
                rel = self.repo.get_release(id=RELEASE_VERSION_TEST)
            except GithubException:
                raise GithubReleaseNotFound(f"Release {RELEASE_VERSION_TEST} not found")
            if rel:
                print("deleting release assets")
                for asset in rel.get_assets():
                    print(f"  delete {asset.name}")
                    asset.delete_asset()
        if self.t:
            self.t._t.delete_project(self.qgis_plugin_config_params.project_slug)


@pytest.fixture
def setup(fixtures: Path) -> Setup:
    test = Setup(fixtures)
    yield test
    test.clean_assets()


case = unittest.TestCase()


def test_dict_from_config(setup: Setup):
    case.assertTrue(dict(setup.qgis_plugin_config_params))
    case.assertTrue(dict(setup.pyproject_params))
    case.assertTrue(dict(setup.setup_params))


def test_release_from_dot_qgis_plugin_ci(setup: Setup):
    release(
        setup.qgis_plugin_config_params,
        RELEASE_VERSION_TEST,
        allow_uncommitted_changes=True,
    )


def test_release_from_pyproject(setup: Setup):
    print(setup.pyproject_params)
    release(
        setup.pyproject_params,
        RELEASE_VERSION_TEST,
        allow_uncommitted_changes=True,
    )


def test_release_with_empty_tx_token(setup: Setup):
    release(
        setup.qgis_plugin_config_params,
        RELEASE_VERSION_TEST,
        tx_api_token="",
        allow_uncommitted_changes=True,
    )

@pytest.mark.skipif(can_skip_test_github(), reason="Missing tx_api_token")
def test_release_with_transifex(setup: Setup):
    Translation(setup.qgis_plugin_config_params, tx_api_token=setup.tx_api_token)
    release(
        setup.qgis_plugin_config_params,
        RELEASE_VERSION_TEST,
        tx_api_token=setup.tx_api_token,
        allow_uncommitted_changes=True,
        dry_run=True,
    )


def test_zipname():
    """Tests about the zipname for the QGIS plugin manager.

    See #22 about dash
    and also capital letters
    """
    case.assertEqual(
        "my_plugin.0.0.0.zip",
        Parameters.archive_name("my_plugin", "0.0.0"),
    )

    with case.assertLogs(
        logger="qgispluginci.parameters", level="WARNING"
    ) as captured:
        Parameters.archive_name("my-plugin", "0.0.0")
    case.assertEqual(
        len(captured.records), 1
    )  # check that there is only one log message
    case.assertEqual(captured.records[0].getMessage(), DASH_WARNING)


def test_release_changelog(setup: Setup, fixtures: Path):
    """Test if changelog in metadata.txt inside zipped plugin after release command."""
    # variables
    cli_config_changelog = fixtures.joinpath(".qgis-plugin-ci-test-changelog.yaml")
    version_to_release = "0.1.2"

    # load specific parameters
    with cli_config_changelog.open() as in_cfg:
        arg_dict = yaml.safe_load(in_cfg)
    parameters = Parameters(arg_dict)
    case.assertIsInstance(parameters, Parameters)

    # get output zip path
    archive_name = parameters.archive_name(
        plugin_name=parameters.plugin_path, release_version=version_to_release
    )

    # extract last items from changelog
    parser = ChangelogParser()
    case.assertTrue(parser.has_changelog())
    changelog_lastitems = parser.last_items(
        count=parameters.changelog_number_of_entries
    )

    # Include a changelog
    release(
        parameters=parameters,
        release_version=version_to_release,
        allow_uncommitted_changes=True,
    )

    # open archive and compare
    with ZipFile(archive_name, "r") as zip_file:
        data = zip_file.read(f"{parameters.plugin_path}/metadata.txt")
        license_data = zip_file.read(f"{parameters.plugin_path}/LICENSE")

    # Changelog
    case.assertGreater(
        data.find(bytes(changelog_lastitems, "utf8")),
        0,
        f"changelog detection failed in release: {data}",
    )

    # License
    case.assertGreater(
        license_data.find(bytes("GNU GENERAL PUBLIC LICENSE", "utf8")),
        0,
        "license file content mismatch",
    )

    # Commit number
    case.assertEqual(1, len(re.findall(r"commitNumber=\d+", str(data))))

    # Commit sha1 not in the metadata.txt
    case.assertEqual(0, len(re.findall(r"commitSha1=\d+", str(data))))


def test_release_version_valid_invalid(setup: Setup):
    valid_tags = [
        "v1.1.1",
        "v1.1",
        "1.0.1",
        "1.1",
        "1.0.0-alpha",
        "1.0.0-dev",
        "latest",
    ]
    invalid_tags = ["1", "v1", ".", ".1"]
    expected_valid_results = {
        "v1.1.1": ["v3"],
        "v1.1": ["v2"],
        "1.0.1": ["double", "semver"],
        "1.1": ["simple"],
        "1.0.0-alpha": ["semver"],
        "1.0.0-dev": ["semver"],
        "latest": ["latest"],
    }
    valid_results = {tag: [] for tag in valid_tags}
    patterns = Parameters.get_release_version_patterns()
    for key, cand in product(patterns, valid_results):
        if re.match(patterns[key], cand):
            valid_results[cand].append(key)
    case.assertEqual(valid_results, expected_valid_results)

    invalid_results = {tag: [] for tag in invalid_tags}
    for key, cand in product(patterns, invalid_results):
        if re.match(patterns[key], cand):
            invalid_results[cand].append(key)
    case.assertFalse(any(invalid_results.values()))


def test_release_version_validation_on(setup: Setup):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="commands", description="qgis-plugin-ci command", dest="command"
    )
    sub_parser = subparsers.add_parser("package")
    sub_parser.add_argument("release_version")
    sub_parser.add_argument("--no-validation", action="store_true")
    args = parser.parse_args(["package", "v1"])
    with case.assertRaises(ValueError):
        Parameters.validate_args(args)


def test_release_version_validation_off():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="commands", description="qgis-plugin-ci command", dest="command"
    )
    sub_parser = subparsers.add_parser("package")
    sub_parser.add_argument("release_version")
    sub_parser.add_argument("--no-validation", action="store_true")
    args = parser.parse_args(["package", "v1", "--no-validation"])
    Parameters.validate_args(args)
