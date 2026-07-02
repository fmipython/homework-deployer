import json
from copy import deepcopy
from pathlib import Path

from cove_sdk import CoveAPIError, CoveClient

from homework_deployer.config import settings
from homework_deployer.exceptions import CoveException
from homework_deployer.models import DeploymentConfig


def build_config(homework_dir: Path, deployment: DeploymentConfig) -> str:
    with CoveClient(base_url=settings.cove_url, api_key=settings.cove_api_key) as client:
        project = client.projects.get(settings.cove_project)

        if project is None:
            raise CoveException(f"Project '{settings.cove_project}' not found in Cove.")

        # TODO - Reset project

        test_file_keys = []

        for test_file in deployment.test_files:
            test_file_path = homework_dir / test_file
            test_file_key = f"test_code/{test_file}"

            _upload_python_code(client, project.id, test_file_key, test_file_path)

            test_file_keys.append(test_file_key)

        raw_config_path = homework_dir / deployment.config_file

        with open(raw_config_path, "r") as f:
            raw_config = json.load(f)

        config = _patch_raw_config(raw_config, test_file_keys)

        client.json_items.create(project_id=project.id, key="config", value=config)

        return _generate_cove_url(settings.cove_url, settings.cove_project, "json_item", "config")


def _upload_python_code(client: CoveClient, project_id: str, key: str, code_file: Path) -> None:
    content = code_file.read_text()

    client.python_items.create(project_id=project_id, key=key, code=content)


def _generate_cove_url(base_url: str, project_id: str, item_type: str, key: str) -> str:
    # TODO - This could move to cove ?
    return f"cove://{base_url}/{item_type}/{project_id}/{key}"


def _patch_raw_config(raw_config: dict, test_file_keys: list[str]) -> dict:
    config = deepcopy(raw_config)

    for check in config["checks"]:
        if check["name"] == "tests":
            check["tests_path"] = [
                _generate_cove_url(settings.cove_url, settings.cove_project, "python_item", test_file_key)
                for test_file_key in test_file_keys
            ]

    return config
