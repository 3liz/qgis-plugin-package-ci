import shutil
import tarfile

from configparser import ConfigParser
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import git

from semver import Version

from . import logger
from .changelog import ChangeLog
from .parameters import Parameters


def create_archive(
    parameters: Parameters,
    *,
    release_version: Version,
    archive_dest: Path,
    archive_name: str,
    experimental: bool = False,
    changelog: Optional[ChangeLog] = None,
) -> Path:
    repo = git.Repo(search_parent_directories=True)

    # Plugin relative path to repository
    plugin_relative_path = parameters.plugin_path.relative_to(repo.working_dir)

    with TemporaryDirectory(dir=parameters.rootdir) as tmpdir:
        git_archive = parameters.rootdir.joinpath(f"{parameters.plugin_slug}.tar")
        try:
            _create_git_archive(repo, plugin_relative_path, git_archive)
            with tarfile.open(git_archive) as tt:
                tt.extractall(path=tmpdir, filter="data")
        finally:
            if git_archive.exists():
                git_archive.unlink()

        # Get the location of the source
        source = Path(tmpdir, parameters.plugin_slug)
        shutil.move(Path(tmpdir, plugin_relative_path), source)

        metadata = source.joinpath("metadata.txt")

        # Prepare plugin metadata
        config = ConfigParser()
        config.optionxform = str  # type: ignore [assignment]
        config.read(metadata)

        date_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        config.set("general", "description", parameters.metadata.description)
        config.set("general", "author", parameters.metadata.author)
        config.set("general", "email", parameters.metadata.email)
        config.set("general", "tags", ",".join(parameters.metadata.tags))
        config.set("general", "homepage", str(parameters.metadata.homepage))
        config.set("general", "repository", str(parameters.metadata.repository))
        config.set("general", "tracker", str(parameters.metadata.tracker))

        config.set("general", "version", str(release_version))
        config.set("general", "commitNumber", str(sum(1 for _ in repo.iter_commits())))
        config.set("general", "commitSha1", repo.head.object.hexsha)
        config.set("general", "dateTime", date_time)
        config.set("general", "experimental", "True" if experimental else "False")

        # Add licence file
        _copy_license_file(repo, source)

        # Copy i18 n files
        _copy_i18n_files(parameters.plugin_path, source)

        if changelog and not changelog.empty:
            changes = changelog.format_last_items(parameters.changelog_max_entries)
            logger.info("Added changelog")
            logger.debug("Changelog: %s", changes)
            config.set("general", "changelog", changes)
        else:
            logger.info("No changelog found")
            config.remove_option("general", "changelog")

        # Replace metadata file
        with metadata.open("w") as fh:
            config.write(fh)

        logger.debug("Written %s: \n%s", metadata, metadata.read_text())

        # Create the pagkage
        logger.info("Creating archive")
        package = shutil.make_archive(
            str(archive_dest.joinpath(archive_name)),
            "zip",
            root_dir=source.parent,
            base_dir=source.name,
        )

        return Path(package)


def _copy_i18n_files(plugin_path: Path, source: Path):
    src = plugin_path.joinpath("i18n")
    dst = source.joinpath("i18n")
    if src.is_dir() and not dst.exists():
        logger.info("Copying i18n files")
        dst.mkdir()
        for file in src.glob("*.qm"):
            logger.debug("= Copying %s", file.name)
            shutil.copy(file, dst.joinpath(file.name))


def _copy_license_file(repo: git.Repo, source: Path):
    license_file = source.joinpath("LICENCE")
    if not license_file.exists():
        licen = Path(repo.working_dir, "LICENSE")
        if licen.exists():
            shutil.copy(licen, license_file)


# Create a intermediate git archive with all plugin files
def _create_git_archive(repo: git.Repo, plugin_path: Path, git_archive: Path):
    # Note 'plugin_path' is RELATIVE
    if git_archive.exists():
        logger.debug("Removing existing git archive '%s'", git_archive)
        git_archive.unlink()

    logger.debug("== Creating git archive '%s'", git_archive)
    repo.git.archive("HEAD", "-o", str(git_archive), plugin_path)
