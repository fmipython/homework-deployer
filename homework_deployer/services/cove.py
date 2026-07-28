import json
from copy import deepcopy
from pathlib import Path
from typing import Optional

from cove_sdk import CoveClient, ResourceType, build_uri

from homework_deployer.exceptions import CoveException
from homework_deployer.models import CoveConfig, DeploymentConfig


def load_pygrader_config_in_cove(homework_dir: Path, deployment: DeploymentConfig, cove_config: CoveConfig) -> str:
    cove_base_url = "http://" + cove_config.url.strip("/")
    with CoveClient(base_url=cove_base_url, api_key=cove_config.api_key) as client:
        project = client.projects.get(cove_config.project)

        if project is None or project.id is None:
            raise CoveException(f"Project '{cove_config.project}' not found in Cove.")

        client.projects.delete_items(project.id)

        test_file_keys = []

        for test_file in deployment.test_files:
            test_file_path = homework_dir / test_file
            test_file_key = f"test_code/{test_file}"

            _upload_python_code(client, project.id, test_file_key, test_file_path)

            test_file_keys.append(test_file_key)

        structure_file_uri = None

        if deployment.structure_file is not None:
            structure_file_path = homework_dir / deployment.structure_file

            with open(structure_file_path, "r") as f:
                structure_content = json.load(f)

            client.json_items.create(project_id=project.id, key="structure", value=structure_content)

            structure_file_uri = build_uri(cove_config.url, ResourceType.JSON_ITEM, cove_config.project, "structure")

        raw_config_path = homework_dir / deployment.config_file

        with open(raw_config_path, "r") as f:
            raw_config = json.load(f)

        config = _patch_raw_config(raw_config, test_file_keys, structure_file_uri, cove_config)

        client.json_items.create(project_id=project.id, key="config", value=config)

        return build_uri(cove_config.url, ResourceType.JSON_ITEM, cove_config.project, "config")


def _upload_python_code(client: CoveClient, project_id: str, key: str, code_file: Path) -> None:
    content = code_file.read_text()

    client.python_items.create(project_id=project_id, key=key.replace("/", "_"), code=content)


def _patch_raw_config(
    raw_config: dict, test_file_keys: list[str], structure_file_uri: Optional[str], cove_config: CoveConfig
) -> dict:
    config = deepcopy(raw_config)

    for check in config["checks"]:
        if check["name"] == "tests":
            check["tests_path"] = [
                build_uri(cove_config.url, ResourceType.PYTHON_ITEM, cove_config.project, test_file_key)
                for test_file_key in test_file_keys
            ]

    return config
