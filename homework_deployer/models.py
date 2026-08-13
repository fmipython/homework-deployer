"""Pydantic models for deployment and Cove configuration."""

from typing import Optional

from pydantic import BaseModel


class DeploymentConfig(BaseModel):
    """Per-homework manifest describing which files to deploy."""

    test_files: list[str] = []
    config_file: str  # TODO - No hidden tests supported for now
    solution_directory: str
    structure_file: Optional[str] = None


class CoveConfig(BaseModel):
    """Connection details for a Cove instance and project."""

    url: str
    api_key: str
    project: str
