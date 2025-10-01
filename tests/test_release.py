import datetime

from pathlib import Path

from qgis_plugin_package_ci.parameters import load_parameters
from qgis_plugin_package_ci.release import release


def test_release_package(fixtures: Path, rootdir: Path):
    parameters = load_parameters(fixtures)
    repository_url = f"https://packages.3liz.org/pub/{parameters.plugin_slug}/"

    expected_archive = parameters.rootdir.joinpath("qgis_plugin_ci_testing.10.1.0-beta1.zip")
    if expected_archive.exists():
        expected_archive.unlink()

    assert not expected_archive.exists()

    repo_xml = parameters.rootdir.joinpath("plugins.xml")
    if repo_xml.exists():
        repo_xml.unlink()

    assert not repo_xml.exists()

    archive = release(
        parameters,
        release_version=None,  # Get the latest
        create_plugin_repository=True,
        repository_url=repository_url,
    )

    print("::test_release_package::archive", archive)
    assert archive == expected_archive

    # Check for repo xml
    assert repo_xml.exists()

    expected = rootdir.joinpath("plugins.xml.expected").read_text()
    expected = expected.replace("__TODAY__", datetime.date.today().strftime("%Y-%m-%d"))
    assert repo_xml.read_text() == expected
