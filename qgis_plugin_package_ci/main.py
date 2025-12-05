import sys

from typing import (
    Optional,
)

import click
import semver

from . import logger
from .errors import (
    PluginPackageError,
    VersionNotFoundError,
)


@click.group()
@click.version_option(
    package_name="qgis-plugin-package-ci",
    message="Qgis plugin ci: %(version)s",
)
@click.option("-v", "--verbose", count=True, help="Increase verbosity")
def cli(verbose: int):
    match verbose:
        case 0:
            logger.setup(logger.LogLevel.WARNING)
        case 1:
            logger.setup(logger.LogLevel.INFO)
        case n if n > 1:
            logger.setup(logger.LogLevel.DEBUG)


#
# Changelog
#
class NoChangeLog(Exception):
    pass


@cli.command("changelog")
@click.argument("release-version")
def make_changelog(release_version: str):
    """Returns the changelog content"""
    from .changelog import ChangeLog
    from .parameters import load_parameters

    parameters = load_parameters()
    if not parameters.changelog_path.exists():
        click.echo("No changelog", err=True)
        raise NoChangeLog()

    changelog = ChangeLog.parse(parameters.changelog_path)

    ver = changelog.find(release_version)
    if ver:
        click.echo(ver.text)


#
# Package
#
@cli.command("package")
@click.argument("release-version")
@click.option("--plugin-repo-url", "repository_url", help="Plugin repository URL")
@click.option("--dry-run", is_flag=True, help="Do not upload")
def make_package(release_version: str, repository_url: Optional[str], dry_run: bool):
    """Create plugin archive"""
    from .parameters import load_parameters
    from .release import create_release_package, upload_github_release

    parameters = load_parameters()
    plugin_archive, version = create_release_package(
        parameters,
        validate_version(release_version),
    )
    click.echo(
        click.style(
            (f"Plugin archive created: {plugin_archive.name} ({hsize(plugin_archive.stat().st_size)})"),
            fg="green",
        ),
    )

    if repository_url is not None:
        upload_github_release(
            parameters,
            version,
            plugin_archive,
            create_plugin_repository=True,
            repository_url=repository_url,
            dry_run=dry_run,
        )


#
# Release
#
@cli.command("release")
@click.argument("release-version")
@click.option(
    "--github-token",
    help="The Github API token for uploading a GitHub release",
)
@click.option(
    "--create-plugin-repo",
    is_flag=True,
    help="Will create a XML repo as a Github release asset. Github token is required.",
)
@click.option("--plugin-repo-url", "repository_url", help="Aternate Plugin repository URL")
@click.option("--git-tag", help="The release tag")
@click.option("--osgeo-username", help="The Osgeo user name to publish the plugin.")
@click.option("--osgeo-password", help="The Osgeo password to publish the plugin.")
@click.option("--dry-run", is_flag=True, help="Do not upload")
def make_release(
    release_version: str,
    github_token: Optional[str],
    create_plugin_repo: bool,
    repository_url: Optional[str],
    git_tag: Optional[str],
    osgeo_username: Optional[str],
    osgeo_password: Optional[str],
    dry_run: bool,
):
    """Release plugin

    If git tag is not specified then it will use the release_version.
    The tag ref is required for uploading assets to the github release
    """
    from .parameters import load_parameters
    from .release import create_release_package, upload_github_release
    from .upload import upload_plugin

    parameters = load_parameters()
    plugin_archive, version = create_release_package(
        parameters,
        validate_version(release_version),
    )
    click.echo(
        click.style(
            (f"Plugin archive created: {plugin_archive.name} ({hsize(plugin_archive.stat().st_size)})"),
            fg="green",
        ),
    )

    create_plugin_repository = create_plugin_repo or repository_url is not None

    upload_github_release(
        parameters,
        version,
        plugin_archive,
        github_token=github_token,
        tag_ref=git_tag,
        osgeo_username=osgeo_username,
        create_plugin_repository=create_plugin_repository,
        repository_url=repository_url,
        dry_run=dry_run,
    )

    if osgeo_username and osgeo_password:
        upload_plugin(
            parameters,
            username=osgeo_username,
            password=osgeo_password,
            archive=plugin_archive,
            dry_run=dry_run,
        )


def main():
    try:
        cli()
    except NoChangeLog:
        sys.exit(1)
    except VersionNotFoundError as err:
        click.echo(click.style(f"ERROR: The vers {err}", fg="red"), err=True)
        sys.exit(1)
    except PluginPackageError as err:
        click.echo(click.style(f"ERROR: {err}", fg="red"), err=True)
        sys.exit(1)


def validate_version(release_version: str) -> Optional[semver.Version]:
    if release_version == "latest":
        return None
    try:
        return semver.Version.parse(release_version)
    except ValueError:
        raise PluginPackageError(f"'{release_version}' is not following SemVer specification")


def hsize(octets: int) -> str:
    """Convert a mount of octets in readable size"""
    import math

    # check zero
    if octets == 0:
        return "0 octet"

    # conversion
    size_name = ("octets", "Ko", "Mo", "Go", "To", "Po")
    i = math.floor(math.log(octets, 1024))
    p = math.pow(1024, i)
    s = round(octets / p, 2)

    return f"{s} {size_name[i]}"
