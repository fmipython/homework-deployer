"""
Main module
"""

import src.at as at
import src.constants as const
import src.db as db

from src.cli import get_args
from src.event import Event

# from src.executor import execute

if __name__ == "__main__":
    args = get_args()

    match args["command"]:
        case const.ActionType.REGISTER:
            config_path = args["config"]

            print(f"Register command, Config path: {config_path}")
            with open(config_path, "r", encoding="utf-8") as config:
                event = Event.model_validate_json(config.read())

            at.register(event)
            db.add(const.DB_PATH, event, config_path)
        case const.ActionType.DEREGISTER:
            event_id = args["event_id"]

            print(f"Deregister command, Event ID: {event_id}")
            db.remove(const.DB_PATH, event_id)
        case const.ActionType.LIST:
            print("List command")

            events = db.load(const.DB_PATH)
            for event_id, config_path in events.items():
                print(f"Event ID: {event_id}, Config Path: {config_path}")

        case const.ActionType.RUN:
            event_id = args["event_id"]
            print("Run command")
        case _:
            print("Unknown command")

    # execute(e)
    # at.register(e)
