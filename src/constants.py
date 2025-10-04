"""
Constants used across the application.
"""

import os
import enum

VERSION = "1.0.0"

WORK_DIR = os.path.join("/tmp", "homework_deployer")

SOURCE_REPO_DIR = os.path.join(WORK_DIR, "source_repo")
DESTINATION_REPO_DIR = os.path.join(WORK_DIR, "destination_repo")


AT_BINARY = "at"
DB_PATH = "db.json"

SCRIPT_PATH = os.path.abspath("homework-deployer.py")


class ActionType(enum.Enum):
    REGISTER = "register"
    DEREGISTER = "deregister"
    LIST = "list"
    RUN = "run"
