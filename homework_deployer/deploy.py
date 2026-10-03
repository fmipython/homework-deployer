"""Deployment logic."""

import os
import tempfile
from pathlib import Path
from typing import Optional

from homework_deployer.config import settings
from homework_deployer.models import CoveConfig, DeploymentConfig
from homework_deployer.services.cove import load_pygrader_config_in_cove
from homework_deployer.services.files import copy_statement, copy_test_files
from homework_deployer.services.git import clone_repository
from homework_deployer.services.pygrader import run_pygrader


def stage(commit: Optional[str] = None) -> dict:
    """Clone the staging repo, push the homework's tests to Cove, and grade the solution."""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            clone_repository(settings.staging_repo, temp_dir, commit)
        except Exception as e:
            return {"status": "failure", "error": f"Failed to clone staging repo: {e}"}

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


def prod(commit: Optional[str] = None) -> dict:
    """Promote a verified homework from staging to production."""
    with tempfile.TemporaryDirectory() as staging_dir, tempfile.TemporaryDirectory() as prod_dir:
        try:
            clone_repository(settings.staging_repo, staging_dir, commit)
        except Exception as e:
            return {"status": "failure", "error": f"Failed to clone staging repo: {e}"}

        staging_homework_directory = Path(staging_dir) / settings.current_homework

        if not staging_homework_directory.exists():
            return {"status": "failure", "error": f"Homework directory {staging_homework_directory} does not exist"}

        try:
            production_repo = clone_repository(settings.production_repo, prod_dir)
        except Exception as e:
            return {"status": "failure", "error": f"Failed to clone production repo: {e}"}

        deployment = DeploymentConfig.model_validate_json(
            (staging_homework_directory / "deployment_config.json").read_text()
        )

        production_homework_directory = Path(prod_dir) / "homeworks" / settings.current_homework

        cove_config = CoveConfig(
            url=settings.production_cove_url,
            api_key=settings.production_cove_api_key,
            project=settings.production_cove_project,
        )

        config_uri = load_pygrader_config_in_cove(staging_homework_directory, deployment, cove_config)

        production_homework_directory.mkdir(parents=True, exist_ok=True)

        # Copy statement file
        copy_statement(staging_homework_directory, deployment, production_homework_directory)

        # Copy test files
        copy_test_files(staging_homework_directory, deployment, production_homework_directory)

        production_repo.git.add(A=True)
        if production_repo.is_dirty():
            production_repo.index.commit(f"Deploying homework {settings.current_homework}")

        try:
            # push() doesn't raise on a rejected push, raise_if_error() does
            production_repo.remote().push().raise_if_error()
        except Exception as e:
            return {"status": "failure", "error": f"Failed to push to production repo: {e}"}

    return {"status": "success", "config_uri": config_uri}
