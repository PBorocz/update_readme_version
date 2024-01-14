"""."""
import tomllib
from datetime import datetime
from pathlib import Path

import pytest

from update_readme_version import _get_current_version, run, validate


class Args():
    """."""
    def __init__(self):
        """."""
        self.verbose = False
        self.debug = False
        self.version = None

################################################################################
# Fixtures
################################################################################
@pytest.fixture
def path_readme_no_unreleased():
    readme = """
# Release History

## 1.9.10
   - open text open text open text open text open text open text open text open text open text open text open text.

## 1.9.09
   - open text open text open text open text open text open text open text open text open text open text open text.
"""
    path_ = Path("/tmp/README.md")
    path_.write_text(readme)
    yield path_
    if path_.exists():
        path_.unlink()

@pytest.fixture
def path_readme():
    readme = """
# Release History

## Unreleased
   - [[https://towardsdatascience.com/should-we-use-custom-exceptions-in-python-b4b4bca474ac][custom exceptions]]

## 1.9.10
   - open text open text open text open text open text open text open text open text open text open text open text.

## 1.9.09
   - open text open text open text open text open text open text open text open text open text open text open text.
"""
    path_ = Path("/tmp/README.md")
    path_.write_text(readme)
    yield path_
    if path_.exists():
        path_.unlink()

################################################################################
# Tests
################################################################################
def test_validate_error_invalid_file():
    """Non-existent file if provided."""
    fails = validate(Path("asdf/ewrasdfaer"))
    assert fails
    assert len(fails) == 1
    assert "could not be found." in fails[0]

# def test_validate_error_missing_file():
#     """Mising file."""
#     fails = validate()
#     assert fails
#     assert len(fails) == 1
#     assert "couldn't find either" in fails[0]


def test_readme_no_unreleased(capsys, path_readme_no_unreleased):
    """Test case where we have a README that has no Unreleased section."""
    assert not run(Args(), path_readme_no_unreleased)
    out, err = capsys.readouterr()
    assert "Sorry, couldn't find a header-line" in out


def test_readme(capsys, path_readme):
    """Test normal case with a "given" version to use."""
    assert run(Args(), path_readme, "1.9.11")

    # Confirm file still exists
    assert path_readme.exists()

    # Confirm it got updated
    readme = path_readme.read_text()
    assert "## Unreleased" in readme
    assert "1.9.10" in readme
    assert "1.9.11" in readme


def test_readme_version_already_exists(capsys, path_readme):
    """Test case when version already exists."""
    # Get size of current readme..
    pre_readme_contents = path_readme.read_text()

    # Test
    assert run(Args(), path_readme, "1.9.10") # This version already appears above!

    # Confirm nothing's done in the file.
    post_readme_contents = path_readme.read_text()
    assert len(pre_readme_contents) == len(post_readme_contents)


def test_get_current_version_pyproject(capsys, path_readme):
    """Test get_current_version by reading pyproject.toml."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    pyproject_version = pyproject.get("tool", {}).get("poetry", {}).get("version", None)

    # Test
    version = _get_current_version()

    # Confirm
    assert version == pyproject_version
