"""
Module contains functions to execute deployment events.
"""

import shutil
from pathlib import Path
from typing import Optional

from git import Repo

import src.constants as const
from src.event import Event


def execute(event: Event, is_no_push: bool = False, is_no_remove: bool = False) -> None:
    """
    Execute the deployment event by cloning repositories, copying files according to patterns,
    committing changes, and cleaning up the working directory.

    :param event: The Event object containing deployment details.
    """
    cloned_source_repo = clone_repo(event.origin, const.SOURCE_REPO_DIR)
    cloned_destination_repo = clone_repo(event.destination, const.DESTINATION_REPO_DIR)

    paths = expand_patterns(
        str(cloned_source_repo.working_dir),
        str(cloned_destination_repo.working_dir),
        event.patterns,
    )
    copy_files(paths)
    commit_changes(cloned_destination_repo, f"Automated commit for event {event.id}")

    if not is_no_push:
        push_changes(cloned_destination_repo)

    if not is_no_remove:
        shutil.rmtree(const.WORK_DIR)


def clone_repo(url: str, destination: str) -> Repo:
    """
    Clone a git repository to a specified destination.

    :param url: The URL of the git repository to clone.
    :param destination: The local path where the repository should be cloned.
    :return: The cloned Repo object.
    """
    return Repo.clone_from(url, destination)


def expand_patterns(
    source_path: str, destination_path: str, patterns: list[tuple[str, Optional[str]]]
) -> list[tuple[Path, Path]]:
    """
    Expand file patterns to generate source and destination file path pairs.

    :param source_path: Path to the source repository.
    :param destination_path: Path to the destination repository.
    :param patterns: List of tuples containing source glob patterns and optional destination patterns.
    :return: List of tuples with source and destination file paths.
    """

    source_repo = Path(source_path)
    destination_repo = Path(destination_path)

    result = []

    for source_pattern, dest_pattern in patterns:
        if (
            any(char in source_pattern for char in ("*", "?", "[", "]"))
            and dest_pattern is not None
            and Path(dest_pattern).is_file()
        ):
            raise PatternError("Destination pattern cannot be file if source pattern is a glob")
        for path in source_repo.glob(source_pattern):
            result.append(expand_pattern(path, dest_pattern, source_repo, destination_repo))

    return result


def expand_pattern(
    source_file: Path, dest_pattern: Optional[str], source_repo: Path, destination_repo: Path
) -> tuple[Path, Path]:
    """
    Generate source and destination file paths for a single file and pattern.

    :param source_file: Path object for the source file.
    :param dest_pattern: Optional destination pattern.
    :param source_repo: Path object for the source repository root.
    :param destination_repo: Path object for the destination repository root.
    :return: Tuple of source and destination file paths.
    """

    if source_file.is_absolute():
        source_file = source_file.relative_to(source_repo)

    source_full_path = source_repo / source_file

    if dest_pattern is None:
        destination_full_path = destination_repo / source_file
    else:
        dest_pattern_path = Path(dest_pattern)

        if source_file.is_dir() and dest_pattern_path.is_file():
            raise PatternError("Cannot use directory pattern for file source")

        if source_file.is_file() and dest_pattern_path.is_dir():
            dest_pattern_path = dest_pattern_path / source_file.name

        destination_full_path = destination_repo / dest_pattern_path

    return source_full_path, destination_full_path


def copy_files(paths: list[tuple[Path, Path]]) -> None:
    """
    Copy files from source paths to destination paths.

    :param paths: List of tuples containing source and destination file paths.
    """
    for source_path, destination_path in paths:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)


def commit_changes(repo: Repo, message: str) -> None:
    """
    Commit changes to the git repository if there are any changes.

    :param repo: The Repo object representing the git repository.
    :param message: The commit message to use.
    """
    repo.git.add(A=True)
    if repo.is_dirty():
        repo.index.commit(message)


def push_changes(repo: Repo) -> None:
    """
    Push changes to the remote repository.

    :param repo: The Repo object representing the git repository.
    """
    origin = repo.remote(name="origin")
    origin.push()


class PatternError(Exception):
    """
    Custom exception for pattern expansion errors.
    """
