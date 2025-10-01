"""
Parameters management.
"""

import datetime
import tomllib

from configparser import ConfigParser
from functools import cached_property
from pathlib import Path
from typing import (
    Annotated,
    Optional,
    Self,
    Sequence,
)

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    HttpUrl,
    PositiveInt,
)
from slugify import slugify

from . import logger


def _parse_str_sequence(value: Sequence[str] | str) -> Sequence[str]:
    if isinstance(value, str):
        # Parse comma separated list
        value = value.split(",") if value else ()
    return value


class PluginMetadata(BaseModel):
    name: str
    author: str = ""
    description: str = ""
    qgis_minimum_version: str = Field(alias="qgisminimumversion")
    qgis_maximum_version: Optional[str] = Field(None, alias="qgismaximumversion")
    icon: Optional[Path] = None
    tags: Annotated[
        Sequence[str],
        BeforeValidator(_parse_str_sequence),
    ] = ()
    experimental: bool = False
    deprecated: bool = False
    # Note homepage is mandatory for publishing
    homepage: Optional[HttpUrl] = None
    tracker: Optional[HttpUrl] = None
    repository: Optional[HttpUrl] = None

    @classmethod
    def read(cls, path: Path) -> Self:
        """Read plugin metadata"""
        config = ConfigParser()
        config.read(path.joinpath("metadata.txt"))
        return cls.model_validate({k: v for (k, v) in config["general"].items()})


class Parameters(BaseModel, extra="forbid"):
    rootdir: Path = Field(title="Root directory")

    plugin_source: Path = Field(
        title="Plugin source",
        description="The directory of the source code in the repository",
    )
    github_organization_slug: str = Field(
        title="The organization slug",
        description="""
        The organization slug on SCM host (e.g. Github) and translation
        platform (e.g. Transifex).
        Not required when running on Travis since deduced from `$TRAVIS_REPO_SLUG`
        environment variable.
        """,
    )
    project_slug: str = Field(
        title="The project slug",
        description="""
        The project slug on SCM host (e.g. Github) and translation
        platform (e.g. Transifex).
        """,
    )
    changelog_file: str = Field(
        default="CHANGELOG.md",
        title="Changelog file",
        description="""
        changelog file relative to the configuration file.
        Defaults to CHANGELOG.md.
        Must be relative to the configuration file.
        """,
    )
    changelog_max_entries: PositiveInt = Field(
        default=3,
        title="Number of changelo entries",
        description="""
        Number of changelog eries to add in the metdata.txt
        Defaults to 3
        """,
    )
    create_date: datetime.date = Field(
        default=datetime.date.today(),
        title="Creation date",
        description="""
        The date of creation of the plugin.
        The would be used in the custom repository XML.
        """,
    )
    upload_url: HttpUrl = Field(
        default=HttpUrl("https://plugins.qgis.org:443/plugins/RPC2/"),
        title="Server url",
        description="Server endpoint for uploading plugin",
    )

    @cached_property
    def plugin_path(self) -> Path:
        return self.rootdir.joinpath(self.plugin_source)

    @cached_property
    def changelog_path(self) -> Path:
        return self.rootdir.joinpath(self.changelog_file)

    @cached_property
    def plugin_slug(self) -> str:
        return slugify(self.metadata.name, separator="_").replace("-", "_")

    @cached_property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata.read(self.plugin_path)


def find_config_file(rootdir: Path) -> Optional[Path]:
    """Find candidate config file"""
    for file in (
        "pyproject.toml",
        "qgis-plugin-package-ci.toml",
        ".qgis-plugin-package-ci.toml",
    ):
        p = rootdir.joinpath(file)
        if p.exists():
            return p
    else:
        return None


def read_config_from_file(path: Path) -> dict:
    """Read bare configuration from file"""
    with path.open("rb") as fh:
        config = tomllib.load(fh)
        logger.debug("== Read config from %s", path)
        if path.stem == "pyproject":
            config = config.get("tool", {})
        return config.get("package-ci", {})


def load_parameters(rootdir: Optional[Path] = None) -> Parameters:
    """Load parameters from config files"""
    rootdir = rootdir or Path.cwd()
    path = find_config_file(rootdir)
    config = read_config_from_file(path) if path else {}
    config.update(rootdir=rootdir)

    return Parameters.model_validate(config)
