"""
Main module
"""

import json
import os
import tempfile
from pathlib import Path

from homework_deployer.config import settings
from homework_deployer.models import CoveConfig, DeploymentConfig
from homework_deployer.services.cove import load_pygrader_config_in_cove
from homework_deployer.services.git import clone_repository
from homework_deployer.services.pygrader import run_pygrader


def stage() -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        clone_repository(settings.staging_repo, temp_dir)

        homework_directory = Path(temp_dir) / settings.current_homework

        if not homework_directory.exists():
            return {"status": "failure", "error": f"Homework directory {homework_directory} does not exist"}

        deployment = DeploymentConfig.model_validate_json((homework_directory / "deployment_config.json").read_text())

        cove_config = CoveConfig(
            url=settings.staging_cove_url, api_key=settings.staging_cove_api_key, project=settings.staging_cove_project
        )

        config_uri = load_pygrader_config_in_cove(homework_directory, deployment, cove_config)

        grader_dir = homework_directory / deployment.solution_directory

        os.environ["COVE_API_KEY"] = cove_config.api_key

        grader_results = run_pygrader(str(grader_dir), config_uri)

        return {"status": "success", "results": grader_results}


if __name__ == "__main__":
    print(json.dumps(stage()))
