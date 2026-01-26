import datetime

from importlib import resources
from pathlib import Path
from typing import Optional

import semver

from . import logger
from .assets import upload_github_asset
from .changelog import ChangeLog
from .errors import (
    VersionNotFoundError,
)
from .package import create_archive
from .parameters import Parameters


def release(
    parameters: Parameters,
    *,
    release_version: Optional[semver.Version] = None,
    github_token: Optional[str] = None,
    tag_ref: Optional[str] = None,
    osgeo_username: Optional[str] = None,
    create_plugin_repository: bool = False,
    repository_url: Optional[str] = None,
    dry_run: bool = False,
) -> Path:
    changelog = (
        ChangeLog.parse(
            parameters.changelog_path,
        )
        if parameters.changelog_path.exists()
        else None
    )

    if not changelog:
        logger.warning("No changelog found")

    if not release_version and changelog:
        # Get the latest version
        latest = changelog.latest
        if latest:
            release_version = semver.Version.parse(latest.version)

    if not release_version:
        raise VersionNotFoundError()

    archive_path = create_archive(
        parameters,
        release_version=release_version,
        archive_dest=parameters.rootdir,
        archive_name=f"{parameters.plugin_slug}.{release_version}",
        experimental=release_version.prerelease is not None,
        changelog=changelog,
    )

    if not tag_ref:
        # Assume that the release verison is the git ref (tag)
        tag_ref = str(release_version)

    #
    # Create a repository located on github
    #
    if create_plugin_repository:
        xml = create_plugin_repository_xml(
            parameters,
            dest_dir=parameters.rootdir,
            release_version=release_version,
            tag_ref=tag_ref,
            archive_path=archive_path,
            osgeo_username=osgeo_username,
            prerelease=release_version.prerelease is not None,
            repository_url=repository_url,
        )
        logger.info("Local XML repository file created : %s", xml)

        if github_token is not None:
            #
            # Push the local xml to the github repository
            #
            if dry_run:
                logger.notice(f"Not uploading {xml} because it is a dry run.")
            else:
                logger.info("Uploading  %s", xml)
                upload_github_asset(
                    parameters,
                    asset_path=xml,
                    tag_ref=tag_ref,
                    github_token=github_token,
                    asset_name="plugins.xml",
                )
    #
    # Upload the plugin archive to github
    #
    if github_token is not None:
        if dry_run:
            logger.notice(f"Not uploading {archive_path} to github because it is a dry run.")
        else:
            logger.info("Uploading %s", archive_path)
            upload_github_asset(
                parameters,
                asset_path=archive_path,
                tag_ref=tag_ref,
                github_token=github_token,
            )

    return archive_path


#
# Create a local plugin repository
#
def create_plugin_repository_xml(
    parameters: Parameters,
    *,
    dest_dir: Path,
    release_version: semver.Version,
    tag_ref: str,
    archive_path: Path,
    osgeo_username: Optional[str],
    prerelease: bool = False,
    repository_url: Optional[str] = None,
) -> Path:
    """
    Creates the plugin repo as an XML file
    """
    from string import Template

    if not repository_url:
        download_url = (
            f"https://github.com/{parameters.github_organization_slug}/{parameters.project_slug}"
            f"/releases/download/{tag_ref}/{archive_path.name}"
        )
    else:
        download_url = f"{repository_url}{archive_path.name}"

    context = {
        "RELEASE_VERSION": release_version,
        "RELEASE_TAG": tag_ref,
        "PLUGIN_NAME": parameters.metadata.name,
        "RELEASE_DATE": datetime.date.today().strftime("%Y-%m-%d"),
        "CREATE_DATE": parameters.create_date.strftime("%Y-%m-%d"),
        "ORG": parameters.github_organization_slug,
        "REPO": parameters.project_slug,
        "PLUGINZIP": archive_path.name,
        "OSGEO_USERNAME": osgeo_username or parameters.metadata.author,
        "DEPRECATED": str(parameters.metadata.deprecated),
        "EXPERIMENTAL": str(prerelease),
        "TAGS": ",".join(parameters.metadata.tags),
        "ICON": str(parameters.metadata.icon),
        "AUTHOR": parameters.metadata.author,
        "QGIS_MIN_VERSION": parameters.metadata.qgis_minimum_version,
        "DESCRIPTION": parameters.metadata.description,
        "ISSUE_TRACKER": str(parameters.metadata.tracker or ""),
        "HOMEPAGE": str(parameters.metadata.homepage or ""),
        "REPO_URL": str(parameters.metadata.repository or ""),
        "DOWNLOAD_URL": download_url,
    }

    if parameters.metadata.qgis_maximum_version:
        context["QGIS_MAX_VERSION"] = parameters.metadata.qgis_maximum_version
    else:
        context["QGIS_MAX_VERSION"] = "3.99"

    xml = dest_dir.joinpath("plugins.xml")
    with resources.path("qgis_plugin_package_ci", "plugins.xml.template") as fsrc:
        xml.write_text(Template(fsrc.read_text()).substitute(context))
    return Path(fsrc)
