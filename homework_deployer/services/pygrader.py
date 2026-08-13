"""Run pygrader against a solution directory."""

import json
import logging
from logging.handlers import RotatingFileHandler

from grader.exceptions import GraderError
from grader.grader import Grader
from grader.utils.results_reporter import JSONResultsReporter


def run_pygrader(project_dir: str, config_uri: str) -> dict:
    """Grade the solution in `project_dir` using the pygrader config at `config_uri`."""
    grader = Grader("deployment", project_dir, config_path=config_uri, logger=__build_logger())
    try:
        raw_results = grader.grade()
    except GraderError as e:
        return {"status": "failure", "error": str(e)}

    parsed_results = json.loads(JSONResultsReporter().to_string(raw_results, verbose=True))

    return parsed_results


def __build_logger() -> logging.Logger:
    logger = logging.getLogger("grader")
    logger.setLevel(logging.DEBUG)  # Set the logger to the lowest level to capture all messages

    logger.handlers.clear()

    # Rotating file handler setup
    file_format = "%(asctime)s - %(levelname)s - %(message)s"
    file_handler = RotatingFileHandler(
        filename="pygrader.log",
        maxBytes=0,  # No size limit
        backupCount=19,  # -1 because the main file counts as one
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(file_format))
    # Force a rollover on startup to create a new log file each time
    file_handler.doRollover()

    logger.addHandler(file_handler)

    return logger
