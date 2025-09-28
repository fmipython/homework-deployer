import shutil
from pathlib import Path
from typing import Optional

from git import Repo

import src.constants as const
from src.event import Event


def execute(event: Event) -> None:
    print(f"Executing event: {event.name} from {event.origin} to {event.destination} on {event.date}")

    cloned_source_repo = clone_repo(event.origin, const.SOURCE_REPO_DIR)
    cloned_destination_repo = clone_repo(event.destination, const.DESTINATION_REPO_DIR)

    paths = expand_patterns(
        str(cloned_source_repo.working_dir),
        str(cloned_destination_repo.working_dir),
        event.patterns,
    )

    for source_path, destination_path in paths:
        print(f"Copying from {source_path} to {destination_path}")

    shutil.rmtree(const.WORK_DIR)


def clone_repo(url: str, destination: str) -> Repo:
    repo = Repo.clone_from(url, destination)
    return repo


def expand_patterns(
    source_path: str, destination_path: str, patterns: list[tuple[str, Optional[str]]]
) -> list[tuple[Path, Path]]:

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
    source_file = source_file.relative_to(source_repo)

    source_full_path = source_repo / source_file
    destination_full_path = destination_repo / (source_file if dest_pattern is None else Path(dest_pattern))

    return source_full_path, destination_full_path
