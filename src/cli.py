"""
Argument parser for the application.
"""

import argparse

from typing import Any

from src.constants import VERSION, ActionType


def get_args() -> dict[str, Any]:
    """
    Create the CLI parser and return the parsed arguments as a dictionary.
    :return: Dictionary of parsed arguments.
    """

    parser = argparse.ArgumentParser(
        "homework-deployer", description="Automate deployment tasks between git repositories."
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    register_parser = subparsers.add_parser("register", help="Register a deployment event")
    register_parser.add_argument("config", type=str, help="Path to the event configuration file")

    deregister_parser = subparsers.add_parser("deregister", help="Deregister a deployment event")
    deregister_parser.add_argument("event_id", type=str, help="ID of the event to deregister")

    subparsers.add_parser("list", help="List all deployment event")

    run_parser = subparsers.add_parser("run", help="Run a deployment event")
    run_parser.add_argument("event_id", type=str, help="ID of the event to run")
    run_parser.add_argument("--no-push", action="store_true", help="Skip pushing changes to remote")

    parser.add_argument("--version", action="version", help="Show the version of the tool", version=VERSION)

    # TODO - Can this be improved?
    args = parser.parse_args().__dict__
    if args["command"]:
        args["command"] = ActionType[args["command"].upper()]
    return args
