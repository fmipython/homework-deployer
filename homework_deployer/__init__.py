import logging
import homework_deployer.at as at
import homework_deployer.constants as const
import homework_deployer.db as db

from homework_deployer.cli import get_args
from homework_deployer.event import Event
from homework_deployer.executor import execute
from homework_deployer.logger import setup_logger


def main() -> None:
    args = get_args()
    setup_logger()
    logger = logging.getLogger("homework_deployer")

    logger.info("Starting homework_deployer with action: %s", args["command"])

    match args["command"]:
        case const.ActionType.REGISTER:
            config_path = args["config"]
            register(config_path)
        case const.ActionType.DEREGISTER:
            event_id = args["event_id"]
            deregister(event_id)
        case const.ActionType.LIST:
            list_events()
        case const.ActionType.RUN:
            event_id = args["event_id"]
            is_no_push = args["no_push"]
            is_no_remove = args["no_remove"]
            run(logger, event_id, is_no_push, is_no_remove)
        case _:
            print("Unknown command")


def run(logger: logging.Logger, event_id: str, is_no_push: bool, is_no_remove: bool) -> None:
    events = db.load(const.DB_PATH)
    config_path = events[event_id][1]
    with open(config_path, "r", encoding="utf-8") as config:
        event = Event.model_validate_json(config.read())

    logger.info("Manually running event %s", event.id)
    execute(event, is_no_push, is_no_remove)


def list_events() -> None:
    """
    List all registered deployment events.
    """
    events = db.load(const.DB_PATH)
    for event_id, (at_id, config_path) in events.items():
        print(f"Event ID: {event_id}, Config Path: {config_path}, At id: {at_id}")


def deregister(event_id: str) -> None:
    """
    Deregister a deployment event by its ID.
    :param event_id: The ID of the event to deregister.
    """
    events = db.load(const.DB_PATH)
    at_id = events[event_id][0]
    db.remove(const.DB_PATH, event_id)
    at.deregister(at_id)


def register(config_path: str) -> None:
    """
    Register a deployment event from a configuration file.
    :param config_path: Path to the event configuration file.
    """
    with open(config_path, "r", encoding="utf-8") as config:
        event = Event.model_validate_json(config.read())

    at_id = at.register(event)

    if at_id is not None:
        db.add(const.DB_PATH, event, config_path, at_id)
        print("Registered event with id:", event.id)
