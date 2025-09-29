"""
Argument parser for the application.
"""

import argparse

from typing import Any

from src.constants import VERSION


def get_args() -> dict[str, Any]:
    """
    Create the CLI parser and return the parsed arguments as a dictionary.
    :return: Dictionary of parsed arguments.
    """

    parser = argparse.ArgumentParser(
        "homework-deployer", description="Automate deployment tasks between git repositories."
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    subparsers.add_parser("register", help="Register a deployment event")
    subparsers.add_parser("deregister", help="Deregister a deployment event")
    subparsers.add_parser("list", help="List all deployment event")
    subparsers.add_parser("run", help="Run a deployment event")

    parser.add_argument("--version", action="version", help="Show the version of the tool", version=VERSION)

    return parser.parse_args().__dict__
