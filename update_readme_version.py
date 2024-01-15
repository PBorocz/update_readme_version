"""'Manage' primary entry point."""
import argparse
import sys
import tomllib
from datetime import datetime
from pathlib import Path

from yachalk import chalk


def get_args() -> [argparse.Namespace, list[str]]:
    """Parse -all- the command-line arguments provide, both known/expected and unknown/step associated."""
    parser = argparse.ArgumentParser(add_help=True)

    parser.add_argument(
        "--version",
        help="Override and use this version instead of pyproject.toml.",
        default=None,
    )

    # Parse all the command-line args/parameters provided (both those above and unknown ones)
    return parser.parse_known_args()


def validate(path_readme: Path = None) -> list[str]:
    """Perform any pre-method validation."""
    fails = []
    # Check to see if optional argument exists if provided
    if path_readme:
        if not path_readme.exists():
            fails.append(f"Sorry, '{path_readme}' could not be found.")
            return fails
        return []

    # Check to see if we have one in the current directory
    cwd = Path.cwd()
    for format_ in ("org", "md"):
        readme_name = f"README.{format_}"
        path_readme = cwd / readme_name
        if path_readme.exists():
            break
    else:
        fails.append("Sorry, couldn't find either a README.org or " "README.md in the top-level directory!")

    return fails

def run(args: argparse.Namespace, path_readme: Path, version: str | None = None) -> bool:
    """Search for 'Unreleased...' header in Changelog portion of README, update *current* pyproject.toml.

    We essentially take the portion of the README that looks like this:
    ...
    * Release History
    ** Unreleased
       - changed this
       - changed that
    ** vA.B.C <older date>
    ...

    To this (for a patch release)
    ...
    * Release History
    ** Unreleased
    ** A.B.D - <today>    <-- Adding this line based on pyproject.version_ and today
       - changed this
       - changed that
    ** A.B.C - <older date>
    ...
    """
    readme_suffix = path_readme.suffix.replace(".", "").casefold()
    readme_contents = path_readme.read_text()

    # Since we don't know what particular heading level "Unreleased" is, we need to scan through
    # the contents to find out...
    unreleased_header = None
    for line in readme_contents.split("\n"):
        if " unreleased" in line.casefold():
            unreleased_header = line

    # Confirm that we actually *found* the "Unreleased" header (irrespective of format):
    if not unreleased_header:
        print(chalk.red_bright(f"Sorry, couldn't find a header-line with 'Unreleased' in {path_readme}!"))
        return False            # Error condition..

    # If the current version already exists in the file, DO NOTHING!
    if f" {version}" in readme_contents:
        print(chalk.green(f"Already had version {version} in README; Nothing done!"))
        return True             # NOT an error..

    # We want to place the new version header at the same level as the current 'Unreleased', so
    # we "build" the new release header line FROM the existing unreleased one; thus ensuring
    # we'll match header levels!
    now_iso = datetime.now().strftime('%Y-%m-%d')
    new_release_header = unreleased_header.lower().replace("unreleased", f"{version} - {now_iso}")

    # Finally, we can replace the current unrelease_header line with the new contents..
    # (note that .org files don't usually have extra spaces between headings while markdown ones do)
    new_line_s = "\n\n" if readme_suffix == "md" else "\n"
    readme_contents = readme_contents.replace(unreleased_header, unreleased_header + new_line_s + new_release_header)

    print(chalk.green(f"Running update on {path_readme.name} version to: '{new_release_header}'"))
    path_readme.write_text(readme_contents)

    return True  # Success


def _get_current_version() -> str | None:
    """."""
    fp_pyproject = Path("pyproject.toml")
    if not fp_pyproject.exists():
        print(chalk.red_bright("Sorry, if you don't pass an explicit version, pyproject.toml must exist in the current directory"))
        return None

    raw_pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    raw_version = raw_pyproject.get("tool", {}).get("poetry", {}).get("version", None)
    if not raw_version:
        print(chalk.red_bright("Sorry, your pyproject.toml file doesn't have a version, ",
              "either set one of pass a version on the command-line."))
        return None

    return raw_version


def main():
    # Get command-line flags and arguments
    args_static, dynamic = get_args()

    # Get path to valid README file.
    s_readme: str | None = dynamic[0]
    if s_readme:
        # If we're given a README file, validate it...
        if fails := validate(Path(s_readme)):
            for msg in fails:
                print(chalk.red_bright(msg))
            sys.exit(1)

    # Get the new release "tag" to use..
    if not (version := args_static.version):
        version = _get_current_version()
    if not version:
        return False

    # Run!
    if not run(args_static, Path(s_readme), version):
        sys.exit(1)


if __name__ == "__main__":
    main()
