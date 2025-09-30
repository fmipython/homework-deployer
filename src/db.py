import json

from src.event import Event


def load(db_path: str) -> dict[str, tuple[int, str]]:
    """
    Load the database from a JSON file.

    :param db_path: Path to the database file.
    :return: List of event dictionaries.
    """

    try:
        with open(db_path, "r", encoding="utf-8") as db_file:
            return json.load(db_file)
    except FileNotFoundError:
        return {}


def add(db_path: str, event: Event, config_path: str, at_id: int) -> None:
    """
    Add a new event to the database.

    :param db_path: Path to the database file.
    :param event: The Event object to add.
    """
    db = load(db_path)
    db[event.id] = at_id, config_path

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
