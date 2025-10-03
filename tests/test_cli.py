
from contextlib import chdir
from pathlib import Path

from click.testing import CliRunner

from qgis_plugin_package_ci.main import cli

# XXX Click and log-cli-level option raise error:
# See https://github.com/pallets/click/issues/824

def test_cli_release(fixtures: Path):
    with chdir(fixtures):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-vv",
                "release",
                "latest",
                "--github-token", "foo",
                "--osgeo-username", "bar",
                "--osgeo-password", "baz",
                "--dry-run",
            ],
        )

        print("\n::test_cli_release::", result.output)
        
        assert result.exit_code == 0


def test_cli_package(fixtures: Path):
    with chdir(fixtures):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-vv",
                "package",
                "latest",
                "--plugin-repo-url", "https://packages.3liz.org/pub/test-plugin",
                "--dry-run",
            ],
        )
        
        print("\n::test_cli_package::", result.output)

        assert result.exit_code == 0


def test_cli_changelog(fixtures: Path):
    with chdir(fixtures):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-vv",
                "changelog",
                "latest",
            ],
        )
    
        expected = """
- This is the latest documented version in this changelog
- The changelog module is tested against these lines
- Be careful modifying this file
"""
        print("\n::test_cli_changelog::", result.output)
        
        assert result.exit_code == 0
        assert result.stdout == expected.lstrip("\n")
