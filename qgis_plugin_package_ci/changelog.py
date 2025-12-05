"""
Changelog parser. Following <https://keepachangelog.com/en/1.0.0/>.
"""

# standard library
import re

from pathlib import Path
from typing import (
    NamedTuple,
    Optional,
    Self,
    Sequence,
)


class VersionNote(NamedTuple):
    major: str
    minor: str
    patch: str
    url: Optional[str] = None
    prerelease: Optional[str] = None
    separator: Optional[str] = None
    date: Optional[str] = None
    text_raw: Optional[str] = None

    @property
    def text(self) -> Optional[str]:
        """Remove many \n at the start and end of the string."""
        return self.text_raw.strip() if self.text_raw else None

    @property
    def is_prerelease(self) -> bool:
        return bool(self.prerelease)

    @property
    def version(self) -> str:
        if self.prerelease:
            return f"{self.major}.{self.minor}.{self.patch}-{self.prerelease}"
        else:
            return f"{self.major}.{self.minor}.{self.patch}"


# see: https://regex101.com/r/8JROUv/1
CHANGELOG_REGEXP = r"(?<=##)\s*\[*(v?0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\]?(\(.*\))?(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?\]*\s-\s*([\d\-/]{10})(.*?)(?=##|\Z)"


class ChangeLog:
    def __init__(self, versions: Sequence[tuple]):
        self._versions = versions

    @property
    def empty(self) -> bool:
        return len(self._versions) == 0

    def format_last_items(self, count: int) -> str:
        """Content to add in the metadata.txt.

        Args:
            count (int): Maximum number of tags to include in the file.

        Returns:
            str: changelog extraction ready to be added to metadata.txt
        """
        if self.empty:
            return ""

        output = "\n"
        so_far = 0

        for ver in self._versions:
            version = VersionNote(*ver)
            output += f"Version {version.version}:\n"

            text = version.text
            if text:
                output += text
            output += "\n\n"
            so_far += 1
            if so_far >= count:
                break

        return output

    def find(self, tag: str) -> Optional[VersionNote]:
        """Get the tuple for a given version."""
        if self.empty:
            return None

        if tag == "latest":
            return VersionNote(*self._versions[0])

        for ver in self._versions:
            version = VersionNote(*ver)
            if version.version == tag:
                return version

        return None

    @property
    def latest(self) -> Optional[VersionNote]:
        """Return the latest tag described in the changelog file."""
        return self.find("latest")

    def __len__(self):
        return len(self._versions)

    @classmethod
    def parse(cls, changelog_path: Path) -> Self:
        content = changelog_path.read_text()

        versions = re.findall(pattern=CHANGELOG_REGEXP, string=content, flags=re.MULTILINE | re.DOTALL)

        return cls(tuple(versions))
