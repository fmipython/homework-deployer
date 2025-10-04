import homework_deployer.at as at
import homework_deployer.constants as const
import homework_deployer.db as db

from homework_deployer.cli import get_args
from homework_deployer.event import Event

from homework_deployer.executor import execute


def main() -> None:
    args = get_args()

    match args["command"]:
        case const.ActionType.REGISTER:
            config_path = args["config"]
            with open(config_path, "r", encoding="utf-8") as config:
                event = Event.model_validate_json(config.read())

            at_id = at.register(event)

            if at_id is not None:
                db.add(const.DB_PATH, event, config_path, at_id)

            print("Registered event with id:", event.id)
        case const.ActionType.DEREGISTER:
            event_id = args["event_id"]
            events = db.load(const.DB_PATH)
            at_id = events[event_id][0]
            db.remove(const.DB_PATH, event_id)
            at.deregister(at_id)
        case const.ActionType.LIST:
            events = db.load(const.DB_PATH)
            for event_id, (at_id, config_path) in events.items():
                print(f"Event ID: {event_id}, Config Path: {config_path}, At id: {at_id}")

        case const.ActionType.RUN:
            event_id = args["event_id"]
            is_no_push = args["no_push"]
            is_no_remove = args["no_remove"]
            events = db.load(const.DB_PATH)
            config_path = events[event_id][1]
            with open(config_path, "r", encoding="utf-8") as config:
                event = Event.model_validate_json(config.read())

            execute(event, is_no_push, is_no_remove)
        case _:
            print("Unknown command")
