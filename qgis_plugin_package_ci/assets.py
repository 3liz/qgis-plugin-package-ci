#
# Upload Github assets
#
from pathlib import Path
from typing import Optional

from github import Github, GithubException

from . import logger
from .errors import PluginPackageError
from .parameters import Parameters


def upload_github_asset(
    parameters: Parameters,
    *,
    asset_path: Path,
    tag_ref: str,
    github_token: str,
    asset_name: Optional[str] = None,
) -> str:
    slug = f"{parameters.github_organization_slug}/{parameters.project_slug}"
    repo = Github(github_token).get_repo(slug)
    try:
        logger.debug(f"Getting release on {parameters.github_organization_slug}/{parameters.project_slug}")
        gh_release = repo.get_release(id=tag_ref)
        logger.debug(
            f"Release retrieved from GitHub: {gh_release}, {gh_release.tag_name}, {gh_release.upload_url}"
        )

        logger.info("Uploading asset %s", asset_path)
        if asset_name:
            uploaded_asset = gh_release.upload_asset(
                path=str(asset_path),
                label=asset_name,
                name=asset_name,
            )
        else:
            uploaded_asset = gh_release.upload_asset(str(asset_path))

        logger.info("Asset uploaded to %s", uploaded_asset.url)
        return uploaded_asset.url
    except GithubException as err:
        logger.error(f"{err}")
        raise PluginPackageError(
            f"Failed to upload github asset '{asset_path}' on {slug}",
        ) from None
