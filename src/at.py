from subprocess import run

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


def register(event: Event) -> bool:
    """
    Register a deployment event using the 'at' command-line utility.

    :param config_path: Path to the event configuration file.
    :return: True if registration is successful, False otherwise.
    """
    at_command = [const.AT_BINARY, "-t", event.date.strftime("%y%m%d%H%M")]
    command_to_execute = "touch /tmp/at_test_file"  # Placeholder command

    output = run(at_command, input=command_to_execute, check=False, text=True, capture_output=True)

    return output.returncode == 0
