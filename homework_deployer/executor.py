"""
Module contains functions to execute deployment events.
"""

import datetime
import logging
import shutil
from pathlib import Path
from typing import Optional

from git import Repo

import homework_deployer.constants as const
from homework_deployer.event import Event

logger = logging.getLogger("homework_deployer")


def execute(event: Event, is_no_push: bool = False, is_no_remove: bool = False) -> None:
    """
    Execute the deployment event by cloning repositories, copying files according to patterns,
    committing changes, and cleaning up the working directory.

    :param event: The Event object containing deployment details.
    """
    now = datetime.datetime.now()
    run_id = f"run_{event.id}{now.strftime('%y%m%d%H%M%S')}"
    run_dir = Path(const.WORK_DIR) / run_id
    source_repo_dir = run_dir / const.SOURCE_REPO_DIR
    destination_repo_dir = run_dir / const.DESTINATION_REPO_DIR

    cloned_source_repo = clone_repo(event.origin, source_repo_dir)
    cloned_destination_repo = clone_repo(event.destination, destination_repo_dir)

    paths = expand_patterns(
        str(cloned_source_repo.working_dir),
        str(cloned_destination_repo.working_dir),
        event.patterns,
    )

    logger.info("Event %s: Copying %d files", event.id, len(paths))

    copy_files(paths)
    commit_changes(cloned_destination_repo, f"Automated commit for event {event.id}")

    if not is_no_push:
        push_changes(cloned_destination_repo)

    if not is_no_remove:
        shutil.rmtree(const.WORK_DIR)


def clone_repo(url: str, destination: Path) -> Repo:
    """
    Clone a git repository to a specified destination.

    :param url: The URL of the git repository to clone.
    :param destination: The local path where the repository should be cloned.
    :return: The cloned Repo object.
    """
    return Repo.clone_from(url, str(destination))


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

    result = [
        extract_pattern(source_repo, destination_repo, destination_pattern, source)
        for source_pattern, destination_pattern in patterns
        for source in list(source_repo.glob(source_pattern))
    ]
    return result


def extract_pattern(
    source_repo: Path, destination_repo: Path, destination_pattern: Optional[str], source: Path
) -> tuple[Path, Path]:
    """
    Expand file pattern

    :param source_repo: _description_
    :param destination_repo: _description_
    :param destination_pattern: _description_
    :param source: _description_
    :return: _description_
    """
    source = source.relative_to(source_repo)

    # Calling relative_to, to strip the repo, if present
    source_full_path = source_repo / source

    if destination_pattern is None:
        destination_full_path = destination_repo / source
    else:
        destination = Path(destination_pattern)
        if source_full_path.is_file():
            if destination.suffix != "":
                destination_full_path = destination_repo / destination
            else:
                destination_full_path = destination_repo / destination / source.name
        else:
            destination_full_path = destination_repo / destination
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
