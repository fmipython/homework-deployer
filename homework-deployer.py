"""
Main module
"""

import tempfile
from pathlib import Path

from homework_deployer.config import settings
from homework_deployer.models import CoveConfig, DeploymentConfig
from homework_deployer.services.cove import load_pygrader_config_in_cove
from homework_deployer.services.git import clone_repository


def stage(homework: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        clone_repository(settings.staging_repo, temp_dir)

        # TODO - Read from the actual file
        deployment = DeploymentConfig(test_files=[], config_file="", solution_files=[], structure_file=None)
        cove_config = CoveConfig(
            url=settings.staging_cove_url, api_key=settings.staging_cove_api_key, project=settings.staging_cove_project
        )

        config_uri = load_pygrader_config_in_cove(Path(temp_dir), deployment, cove_config)

        # 3. Run pygrader

        # 4. Collect results

        # 5. Report results


if __name__ == "__main__":
    print("Hello world!")
