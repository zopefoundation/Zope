#!/bin/env python 3.7
# Update the index for all release tags

from distutils.version import StrictVersion
import pathlib
import subprocess


def create_master():
    """Create the config files for the master branch."""
    path = get_dir("master")
    README.write("## latest\n\n")
    README.write(
        "(files created from master but not necessarily in sync with it)\n\n"
    )
    copy_files("master", path)


def create_tag(tag):
    """Create the config files for a 4.x tag."""
    path = get_dir(tag)
    README.write(f"\n## {tag}\n\n")
    copy_files(tag, path)


def create_tag_2_13(tag):
    """Create the config files for a 2.13.x tag."""
    path = get_dir(tag)
    README.write(f"\n## {tag}\n\n")
    with open(path / "versions-prod.cfg", "wb") as f:
        f.write(b"[versions]\n")
        content = subprocess.check_output(
            f"git show {tag}:requirements.txt".split()
        )
        f.write(content.replace(b"==", b" = "))
    README.write(f'* [versions-prod.cfg]({path / "versions-prod.cfg"})\n')
    copy_file(tag, "requirements.txt", path)


def pre_egg_releases():
    """Create links for releases older than 2.12."""
    README.write("\n## Pre egg releases\n")
    src_path = pathlib.Path("pre-egg-releases")
    releases = {x.name.split("-")[1]: x for x in src_path.iterdir()}
    release_order = sorted(releases.keys(), key=StrictVersion, reverse=True)
    for release in release_order:
        print(release)
        path = releases[release]
        README.write(f"\n* [{path.name}]({path})")


def get_dir(tag):
    """Return the directory to store the config files for tag.

    Create it if it does not exist.
    """
    print(tag)
    path = pathlib.Path("releases") / tag
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_files(tag, path):
    """Copy the files needed in most releases."""
    filenames = [
        "versions.cfg",
        "versions-prod.cfg",
        "requirements-full.txt",
        "requirements.txt",
        "constraints.txt",
    ]
    for name in filenames:
        copy_file(tag, name, path)


def copy_file(tag, name, path):
    """Copy a single file if it exists at the tag."""
    try:
        content = subprocess.check_output(
            f"git show {tag}:{name}".split(), stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        pass
    else:
        with open(path / name, "wb") as f:
            f.write(content)
        README.write(f"* [{name}]({path / name})\n")


def main():
    README.write("# Zope Releases\n\n")

    create_master()

    tags_4_x = subprocess.check_output(
        "git tag -l 4*".split(), encoding="ascii"
    ).splitlines()
    tags_4_x.sort(key=StrictVersion, reverse=True)
    for tag in tags_4_x:
        create_tag(tag)

    for tag in ["2.13.29", "2.13.28", "2.13.27", "2.13.26"]:
        create_tag_2_13(tag)

    create_tag("2.12.28")

    pre_egg_releases()

    README.write("\n\n_____\n\n")
    README.write("[How to maintain this page](HOWTO.md)\n")


if __name__ == "__main__":
    with open("README.md", "w") as README:
        main()
