from pathlib import Path

from qgis_plugin_package_ci.changelog import ChangeLog


def test_changelog_parse(fixtures: Path):
    path = fixtures.joinpath("CHANGELOG.md")

    chlog = ChangeLog.parse(path)
    assert len(chlog) == 7

    print("::test_changelog_parse::", chlog._versions[0])

    latest = chlog.latest
    assert latest is not None

    assert latest.version == "10.1.0-beta1"
    assert latest.date == "2021/02/08"
    assert latest.is_prerelease

    text = chlog.format_last_items(3)
    print("::test_changelog_parse::format::", text)

    expected = """
Version 10.1.0-beta1:
- This is the latest documented version in this changelog
- The changelog module is tested against these lines
- Be careful modifying this file

Version 10.1.0-alpha1:
- This is a version with a prerelease in this changelog
- The changelog module is tested against these lines
- Be careful modifying this file

Version 10.0.1:
- End of year version

"""
    assert text == expected

    found = chlog.find("10.0.1")
    assert found is not None
    assert found.version == "10.0.1"

    expected_content = "- End of year version"
    assert found.text == expected_content

    found = chlog.find("99.0.0")
    assert found is None
