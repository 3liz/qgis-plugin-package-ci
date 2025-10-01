from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def rootdir(request: pytest.FixtureRequest) -> Path:
    return request.config.rootpath


@pytest.fixture(scope="session")
def fixtures(rootdir: Path) -> Path:
    return rootdir.joinpath("fixtures")
