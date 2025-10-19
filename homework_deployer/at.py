"""
Module to handle scheduling deployment events using the 'at' command-line utility.
"""

import logging
import sys

from subprocess import run
from typing import Optional

import homework_deployer.constants as const
from homework_deployer.event import Event

logger = logging.getLogger("homework_deployer")


def is_at_available() -> bool:
    """
    Check if the 'at' command-line utility is available on the system.
    :return: True if 'at' is available, False otherwise.
    """
    command = ["which", const.AT_BINARY]

    output = run(command, check=False, capture_output=True, text=True)

    return output.returncode == 0


def register(event: Event) -> Optional[int]:
    """
    Register a deployment event using the 'at' command-line utility.

    :param config_path: Path to the event configuration file.
    :return: True if registration is successful, False otherwise.
    """
    at_command = [const.AT_BINARY, "-t", event.date.strftime("%y%m%d%H%M")]
    command_to_execute = build_command(event)

    output = run(at_command, input=command_to_execute, check=False, text=True, capture_output=True)

    logger.debug("at command: %s", " ".join(at_command))
    logger.debug("at command input: %s", command_to_execute)
    logger.debug("at command output: %s/%s", output.stdout, output.stderr)

    if output.returncode != 0:
        logger.error("Failed to register event %s with 'at'", event.id)
        return None

    for line in output.stderr.splitlines():
        if "job" in line:
            at_id = int(line.split()[1])
            logger.info("Registered event %s with at id %d", event.id, at_id)
            return at_id

    logger.error("Failed to parse 'at' output for event %s", event.id)

    return None


def deregister(at_id: int) -> bool:
    """
    Deregister a deployment event using the 'at' command-line utility.

    :param at_id: The ID of the scheduled job to remove.
    :return: True if deregistration is successful, False otherwise.
    """
    at_command = [const.AT_BINARY, "-r", str(at_id)]

    output = run(at_command, check=False, text=True, capture_output=True)

    return output.returncode == 0


def get_time(at_id: int) -> str:
    """
    Get the scheduled execution time of a given event

    :param at_id: _description_
    :return: _description_
    """
    at_command = [const.AT_BINARY, "-l"]

    process_result = run(at_command, check=False, text=True, capture_output=True)

    output = process_result.stdout.split("\n")

    for line in output:
        components = line.split()
        if line == "":
            continue
        if str(at_id) == components[0]:
            return " ".join(components[1:6])

    return ""


def build_command(event: Event) -> str:
    """
    Build the command to be scheduled with 'at' for executing the deployment event.

    :param event: The Event object containing deployment details.
    :return: The command string to be executed.
    """
    command = [sys.executable, "-m", "homework_deployer", "run", event.id]
    if event.is_dry_run:
        command.append("--no-push")
        command.append("--no-remove")
    return " ".join(command)
