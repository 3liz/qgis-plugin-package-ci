#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest test.test_changelog
    # for specific test
    python -m unittest test.test_changelog.TestChangelog.test_has_changelog
"""

# standard library
import tempfile
import unittest
from pathlib import Path

# project
from qgispluginci.changelog import ChangelogParser
from qgispluginci.version_note import VersionNote

# ############################################################################
# ########## Classes #############
# ################################


case = unittest.TestCase()


def test_has_changelog(fixtures: Path):
    """Test changelog path logic."""

    # using the fixture subfolder as string
    case.assertTrue(ChangelogParser.has_changelog(parent_folder=fixtures))
    case.assertIsInstance(ChangelogParser.CHANGELOG_FILEPATH, Path)

    # using the fixture subfolder as pathlib.Path
    case.assertTrue(
        ChangelogParser.has_changelog(parent_folder=fixtures)
    )
    case.assertIsInstance(ChangelogParser.CHANGELOG_FILEPATH, Path)

    # with a path to a file, must raise a type error
    with case.assertRaises(SystemExit):
        ChangelogParser.has_changelog(parent_folder=Path(__file__))
    case.assertIsNone(ChangelogParser.CHANGELOG_FILEPATH, None)

    # with a path to a folder which doesn't exist, must raise a file exists error
    with case.assertRaises(SystemExit):
        ChangelogParser.has_changelog(parent_folder=Path("imaginary_path"))


def test_changelog_content(fixtures: Path):
    """Test version content from changelog."""
    # parser
    parser = ChangelogParser(parent_folder=fixtures)
    case.assertIsInstance(parser.CHANGELOG_FILEPATH, Path)

    # Unreleased doesn't count
    case.assertEqual(7, len(parser._parse()))

    # This version doesn't exist
    case.assertIsNone(parser.content("0.0.0"))

    expected_checks = {
        "10.1.0-beta1": (
            "- This is the latest documented version in this changelog\n"
            "- The changelog module is tested against these lines\n"
            "- Be careful modifying this file"
        ),
        "10.1.0-alpha1": (
            "- This is a version with a prerelease in this changelog\n"
            "- The changelog module is tested against these lines\n"
            "- Be careful modifying this file"
            # "\n" TODO Fixed section is missing
            # "- trying with a subsection in a version note"
        ),
        "10.0.1": "- End of year version",
        "10.0.0": "- A\n- B\n- C",
        "9.10.1": "- D\n- E\n- F",
        "v0.1.1": (
            '* Tag with a "v" prefix to check the regular expression\n'
            "* Previous version"
        ),
        "0.1.0": "* Very old version",
    }
    for version, expected in expected_checks.items():
        with case.subTest(i=version):
            case.assertEqual(parser.content(version), expected)


def test_changelog_content_latest(fixtures: Path):
    """Test against the latest special option value. \
    See: https://github.com/opengisch/qgis-plugin-ci/pull/33
    """
    # expected result
    expected_latest = (
        "- This is the latest documented version in this changelog\n"
        "- The changelog module is tested against these lines\n"
        "- Be careful modifying this file"
    )

    # get latest
    parser = ChangelogParser(parent_folder=fixtures)
    case.assertEqual(expected_latest, parser.content("latest"))

    case.assertEqual("10.1.0-beta1", parser.latest_version())


def test_changelog_content_ci_fake():
    """Test specific fake version used in tests."""
    parser = ChangelogParser()
    fake_version_content = parser.content(tag="0.1.2")

    # expected result
    expected = (
        "(This version note is used in unit-tests)\n\n"
        '* Tag without "v" prefix\n'
        "* Add a CHANGELOG.md file for testing"
    )

    case.assertIsInstance(fake_version_content, str)
    case.assertEqual(expected, fake_version_content)


def test_different_changelog_file(fixtures: Path):
    """Test against a different changelog filename."""
    old = fixtures.joinpath("CHANGELOG.md")
    new_folder = Path(tempfile.mkdtemp())
    new_path = new_folder / Path("CHANGELOG-branch-X.md")
    case.assertFalse(new_path.exists())

    new_path.write_text(old.read_text())

    case.assertTrue(
        ChangelogParser.has_changelog(
            parent_folder=new_folder,
            changelog_path=new_path,
        )
    )


def test_changelog_last_items(fixtures):
    """Test last items from changelog."""
    # on fixture changelog
    parser = ChangelogParser(parent_folder=fixtures)
    last_items = parser.last_items(3)
    case.assertIsInstance(last_items, str)

    # on repository changelog
    parser = ChangelogParser()
    last_items = parser.last_items(3)
    case.assertIsInstance(last_items, str)



def test_changelog_version_note(fixtures: Path):
    """Test version note named tuple structure and mechanisms."""
    # parser
    parser = ChangelogParser(parent_folder=fixtures)
    case.assertIsInstance(parser.CHANGELOG_FILEPATH, Path)

    # content parsed
    changelog_content = parser._parse()
    case.assertEqual(len(changelog_content), 7)

    # loop on versions
    for version in changelog_content:
        version_note = VersionNote(*version)
        case.assertIsInstance(version_note.date, str)
        case.assertTrue(hasattr(version_note, "is_prerelease"))
        case.assertTrue(hasattr(version_note, "version"))
        if len(version_note.prerelease):
            case.assertEqual(version_note.is_prerelease, True)


def test_version_note_tuple(fixtures: Path):
    """Test the version note tuple."""
    parser = ChangelogParser(parent_folder=fixtures)

    version = parser._version_note("0.0.0")
    case.assertIsNone(version)

    version = parser._version_note("10.1.0-beta1")
    case.assertEqual("10", version.major)
    case.assertEqual("1", version.minor)
    case.assertEqual("0", version.patch)
    case.assertEqual("", version.url)
    case.assertEqual("beta1", version.prerelease)
    case.assertTrue(version.is_prerelease)
    case.assertEqual("", version.separator)  # Not sure what is the separator
    case.assertEqual("2021/02/08", version.date)
    case.assertEqual(
        (
            "- This is the latest documented version in this changelog\n"
            "- The changelog module is tested against these lines\n"
            "- Be careful modifying this file"
        ),
        version.text,
    )

    version = parser._version_note("10.0.1")
    case.assertEqual("", version.prerelease)
    case.assertFalse(version.is_prerelease)

