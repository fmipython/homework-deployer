from typing import Optional

from pydantic import BaseModel


class DeploymentConfig(BaseModel):
    test_files: list[str] = []
    config_file: str
    solution_files: list[str]
    structure_file: Optional[str] = None
