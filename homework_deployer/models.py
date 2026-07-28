from typing import Optional

from pydantic import BaseModel


class DeploymentConfig(BaseModel):
    test_files: list[str] = []
    config_file: str  # TODO - No hidden tests supported for now
    solution_directory: str
    structure_file: Optional[str] = None


class CoveConfig(BaseModel):
    url: str
    api_key: str
    project: str
