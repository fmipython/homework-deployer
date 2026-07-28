"""
Main module
"""

import json
import os
import tempfile
from pathlib import Path

from grader.exceptions import GraderError
from grader.grader import Grader
from grader.utils.results_reporter import JSONResultsReporter

from homework_deployer.config import settings
from homework_deployer.models import CoveConfig, DeploymentConfig
from homework_deployer.services.cove import load_pygrader_config_in_cove
from homework_deployer.services.git import clone_repository


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

        grader_dir = Path(temp_dir) / deployment.solution_directory

        # pygrader requires COVE_API_KEY
        os.environ["COVE_API_KEY"] = cove_config.api_key
        grader = Grader("deployment", str(grader_dir), logger=None, config_path=config_uri)
        try:
            grader_results = grader.grade()
        except GraderError as e:
            return {"status": "failure", "error": str(e)}

        results_json = json.loads(JSONResultsReporter().to_string(grader_results, verbose=True))

        return {"status": "success", "results": results_json}


if __name__ == "__main__":
    print(stage())
