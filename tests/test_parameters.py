from pathlib import Path

from qgis_plugin_package_ci.parameters import (
    find_config_file,
    load_parameters,
    read_config_from_file,
)


def test_find_config_file(fixtures: Path):
    path = find_config_file(fixtures)
    assert path is not None
    assert path.name == "pyproject.toml"

    path = find_config_file(fixtures.parent)
    assert path is None


def test_read_config(fixtures: Path):
    config = read_config_from_file(fixtures.joinpath(".qgis-plugin-package-ci.toml"))
    assert config.get("github_organization_slug") == "3liz"


def test_parameters(fixtures: Path):
    parameters = load_parameters(fixtures)
    assert parameters is not None

    meta = parameters.metadata
    assert meta.qgis_minimum_version == "3.2"
