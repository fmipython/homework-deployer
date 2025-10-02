"""
Module to handle scheduling deployment events using the 'at' command-line utility.
"""

from subprocess import run
from typing import Optional

import src.constants as const
from src.event import Event


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
    command_to_execute = "touch /tmp/at_test_file"  # Placeholder command

    output = run(at_command, input=command_to_execute, check=False, text=True, capture_output=True)

    if output.returncode != 0:
        return None

    at_id = int(output.stderr.split()[1])
    return at_id


def deregister(at_id: int) -> bool:
    """
    Deregister a deployment event using the 'at' command-line utility.

    :param at_id: The ID of the scheduled job to remove.
    :return: True if deregistration is successful, False otherwise.
    """
    at_command = [const.AT_BINARY, "-r", str(at_id)]

    output = run(at_command, check=False, text=True, capture_output=True)

    return output.returncode == 0
