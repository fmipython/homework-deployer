import logging

from logging.handlers import RotatingFileHandler


def setup_logger() -> None:
    logger = logging.getLogger("homework_deployer")
    logger.setLevel(logging.DEBUG)

    file_format = "%(asctime)s - %(levelname)s - %(message)s"
    file_handler = RotatingFileHandler(
        filename="homework_deployer.log",
        maxBytes=0,  # No size limit
        backupCount=19,  # -1 because the main file counts as one
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(file_format))
    # Force a rollover on startup to create a new log file each time
    file_handler.doRollover()

    logger.addHandler(file_handler)
