"""
Module contains functions to execute deployment events.
"""

import shutil
from pathlib import Path
from typing import Optional

from git import Repo

import src.constants as const
from src.event import Event


def execute(event: Event) -> None:
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

    return [
        expand_pattern(path, dest_pattern, source_repo, destination_repo)
        for source_pattern, dest_pattern in patterns
        for path in source_repo.glob(source_pattern)
    ]


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
    source_file = source_file.relative_to(source_repo)

    source_full_path = source_repo / source_file
    destination_full_path = destination_repo / (source_file if dest_pattern is None else Path(dest_pattern))

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
        # origin = repo.remote(name='origin')
        # origin.push()
