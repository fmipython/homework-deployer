"""
Constants used across the application.
"""

import os

VERSION = "1.0.0"

WORK_DIR = os.path.join("/tmp", "homework_deployer")

SOURCE_REPO_DIR = os.path.join(WORK_DIR, "source_repo")
DESTINATION_REPO_DIR = os.path.join(WORK_DIR, "destination_repo")
