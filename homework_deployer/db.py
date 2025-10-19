"""
Persistent storage for deployment events using a JSON file.
"""

import json

from homework_deployer.event import Event


def load(db_path: str) -> dict[str, tuple[int, str]]:
    """
    Load the database from a JSON file.

    :param db_path: Path to the database file.
    :return: List of event dictionaries.
    """

    try:
        with open(db_path, "r", encoding="utf-8") as db_file:
            content = json.load(db_file)
            content = {k: tuple(v) for k, v in content.items()}
            return content
    except FileNotFoundError:
        with open(db_path, "w", encoding="utf-8") as db_file:
            json.dump({}, db_file)
        return {}


def add(db_path: str, event: Event, config_path: str, at_id: int) -> None:
    """
    Add a new event to the database.

    :param db_path: Path to the database file.
    :param event: The Event object to add.
    """
    db = load(db_path)
    db[event.id] = (at_id, config_path)

    with open(db_path, "w", encoding="utf-8") as db_file:
        json.dump(db, db_file, indent=4)


def remove(db_path: str, event_id: str) -> None:
    """
    Remove an event from the database by its ID.

    :param db_path: Path to the database file.
    :param event_id: The ID of the event to remove.
    """
    db = load(db_path)
    if event_id in db:
        del db[event_id]

        with open(db_path, "w", encoding="utf-8") as db_file:
            json.dump(db, db_file, indent=4)


def get_next_free_id(db_path: str) -> str:
    existing_ids = set(int(_id) for _id in load(db_path).keys())

    highest_id = max(existing_ids)

    # If there is a hole in ids, this will find it
    for candidate_id in range(highest_id):
        if candidate_id not in existing_ids:
            return str(candidate_id)

    return str(highest_id + 1)
