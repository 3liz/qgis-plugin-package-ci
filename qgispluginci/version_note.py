from typing import (
    NamedTuple,
    Optional,
)


class VersionNote(NamedTuple):
    major: Optional[str] = None
    minor: Optional[str] = None
    patch: Optional[str] = None
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
