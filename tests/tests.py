"""Black-box tests for the `stage` and `prod` CLI flows.

Git is real but every "remote" is a throwaway local repo; Cove and pygrader are faked in-process.
"""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest import mock

from cove_sdk import ResourceType, build_uri
from cove_sdk.models import Project
from git import Repo

from homework_deployer.cli import main
from homework_deployer.config import Settings

STAGING_COVE_URL = "staging-cove.test"
STAGING_PROJECT = "staging-project"
PROD_COVE_URL = "prod-cove.test"
PROD_PROJECT = "prod-project"

TEST_CODE = "def test_add():\n    assert 1 + 1 == 2\n"
TEST_KEY = "test_code_tests_test_solution"
STATEMENT = "# Homework 0\n"
GRADER_RESULTS = {"score": 10}

HOMEWORK_FILES = {
    "hw0/deployment_config.json": json.dumps(
        {
            "statement_file": "README.md",
            "test_files": ["tests/test_solution.py"],
            "config_file": "pygrader.json",
            "solution_directory": "solution",
        }
    ),
    "hw0/README.md": STATEMENT,
    "hw0/tests/test_solution.py": TEST_CODE,
    "hw0/pygrader.json": json.dumps({"checks": [{"name": "tests"}]}),
    "hw0/solution/solution.py": "def add(a, b):\n    return a + b\n",
}


def commit_files(path: Path, files: dict[str, str], message: str = "Add files") -> str:
    """Write `files` into the repo at `path` (initialising it if needed), commit them and return the SHA."""
    repo = Repo.init(path)
    for name, content in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(content)
    repo.index.add(list(files))
    return repo.index.commit(message).hexsha


class FakeCoveClient:
    """In-memory stand-in for `cove_sdk.CoveClient`, backed by `store = {project_id: {key: value}}`."""

    store: dict[str, dict[str, Any]] = {}

    def __init__(self, base_url: str, api_key: str) -> None:
        self.projects = SimpleNamespace(get=self._get_project, delete_items=lambda project_id: self.store[project_id].clear())
        self.python_items = SimpleNamespace(create=self._create)
        self.json_items = SimpleNamespace(create=self._create)

    def __enter__(self) -> "FakeCoveClient":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def _get_project(self, project_id: str) -> Project | None:
        return Project(id=project_id, name=project_id, is_public=False) if project_id in self.store else None

    def _create(self, project_id: str, key: str, code: Any = None, value: Any = None) -> None:
        self.store[project_id][key] = code if code is not None else value


class DeployerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

        self.staging = self.tmp / "staging"
        self.staging_sha = commit_files(self.staging, HOMEWORK_FILES)

        commit_files(self.tmp / "production-src", {"README.md": "# Course\n"})
        self.production = self.tmp / "production.git"
        Repo.clone_from(self.tmp / "production-src", self.production, bare=True)

        self.settings = Settings(
            _env_file=None,
            current_homework="hw0",
            staging_repo=str(self.staging),
            staging_cove_url=STAGING_COVE_URL,
            staging_cove_api_key="staging-key",
            staging_cove_project=STAGING_PROJECT,
            production_repo=str(self.production),
            production_cove_url=PROD_COVE_URL,
            production_cove_api_key="prod-key",
            production_cove_project=PROD_PROJECT,
        )
        FakeCoveClient.store = {STAGING_PROJECT: {}, PROD_PROJECT: {}}
        self.grader_calls: list[tuple[str, str, bool, str | None]] = []

        for patcher in (
            mock.patch("homework_deployer.deploy.settings", self.settings),
            mock.patch("homework_deployer.services.cove.CoveClient", FakeCoveClient),
            mock.patch("homework_deployer.deploy.run_pygrader", self._fake_run_pygrader),
            mock.patch.dict(os.environ),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def _fake_run_pygrader(self, project_dir: str, config_uri: str) -> dict:
        # The clone is deleted once the action returns, so check the solution is there while grading
        solution_present = (Path(project_dir) / "solution.py").exists()
        self.grader_calls.append((project_dir, config_uri, solution_present, os.environ.get("COVE_API_KEY")))
        return GRADER_RESULTS

    def run_cli(self, *args: str) -> dict:
        out = io.StringIO()
        with mock.patch("sys.argv", ["homework-deployer", *args]), contextlib.redirect_stdout(out):
            main()
        return json.loads(out.getvalue())

    def production_head(self) -> Any:
        return Repo(self.production).head.commit


class StageTests(DeployerTestCase):
    def test_stage_success(self) -> None:
        result = self.run_cli("stage")

        self.assertEqual(result, {"status": "success", "results": GRADER_RESULTS})

        items = FakeCoveClient.store[STAGING_PROJECT]
        self.assertEqual(items[TEST_KEY], TEST_CODE)
        test_uri = build_uri(STAGING_COVE_URL, ResourceType.PYTHON_ITEM, STAGING_PROJECT, TEST_KEY)
        self.assertEqual(items["config"], {"checks": [{"name": "tests", "tests_path": [test_uri]}]})
        self.assertEqual(FakeCoveClient.store[PROD_PROJECT], {})

        config_uri = build_uri(STAGING_COVE_URL, ResourceType.JSON_ITEM, STAGING_PROJECT, "config")
        [(project_dir, called_uri, solution_present, api_key)] = self.grader_calls
        self.assertTrue(project_dir.endswith(os.path.join("hw0", "solution")))
        self.assertEqual(called_uri, config_uri)
        self.assertTrue(solution_present)
        self.assertEqual(api_key, "staging-key")

    def test_stage_with_commit(self) -> None:
        commit_files(self.staging, {"hw0/tests/test_solution.py": "def test_new():\n    pass\n"}, "Update tests")

        result = self.run_cli("stage", "--commit", self.staging_sha)

        self.assertEqual(result["status"], "success")
        self.assertEqual(FakeCoveClient.store[STAGING_PROJECT][TEST_KEY], TEST_CODE)

    def test_stage_clone_failure(self) -> None:
        self.settings.staging_repo = str(self.tmp / "missing")

        result = self.run_cli("stage")

        self.assertEqual(result["status"], "failure")
        self.assertIn("Failed to clone staging repo", result["error"])
        self.assertEqual(self.grader_calls, [])

    def test_stage_missing_homework_dir(self) -> None:
        self.settings.current_homework = "hw42"

        result = self.run_cli("stage")

        self.assertEqual(result["status"], "failure")
        self.assertIn("does not exist", result["error"])
        self.assertEqual(self.grader_calls, [])


class ProdTests(DeployerTestCase):
    def test_prod_staging_clone_failure(self) -> None:
        self.settings.staging_repo = str(self.tmp / "missing")

        result = self.run_cli("prod")

        self.assertEqual(result["status"], "failure")
        self.assertIn("Failed to clone staging repo", result["error"])

    def test_prod_missing_homework_dir(self) -> None:
        self.settings.current_homework = "hw42"

        result = self.run_cli("prod")

        self.assertEqual(result["status"], "failure")
        self.assertIn("does not exist", result["error"])

    def test_prod_production_clone_failure(self) -> None:
        self.settings.production_repo = str(self.tmp / "missing")

        result = self.run_cli("prod")

        self.assertEqual(result["status"], "failure")
        self.assertIn("Failed to clone production repo", result["error"])

    def test_prod_uploads_to_production_cove(self) -> None:
        result = self.run_cli("prod")

        config_uri = build_uri(PROD_COVE_URL, ResourceType.JSON_ITEM, PROD_PROJECT, "config")
        self.assertEqual(result, {"status": "success", "config_uri": config_uri})
        items = FakeCoveClient.store[PROD_PROJECT]
        self.assertEqual(items[TEST_KEY], TEST_CODE)
        self.assertIn("config", items)
        self.assertEqual(FakeCoveClient.store[STAGING_PROJECT], {})

    def test_prod_pushes_homework_to_production_repo(self) -> None:
        before = self.production_head().hexsha

        result = self.run_cli("prod")

        self.assertEqual(result["status"], "success")
        # prod's clone lives in a deleted temp dir, so a new commit on the remote can only come from a push
        head = self.production_head()
        self.assertNotEqual(head.hexsha, before)
        self.assertEqual(head.parents[0].hexsha, before)
        self.assertEqual(head.message, "Deploying homework hw0")
        self.assertEqual((head.tree / "homeworks/hw0/README.md").data_stream.read().decode(), STATEMENT)
        # copy_test_files currently flattens test files into the homework directory
        self.assertEqual((head.tree / "homeworks/hw0/test_solution.py").data_stream.read().decode(), TEST_CODE)

    def test_prod_reports_rejected_push(self) -> None:
        hook = self.production / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        before = self.production_head().hexsha

        result = self.run_cli("prod")

        self.assertEqual(result["status"], "failure")
        self.assertEqual(self.production_head().hexsha, before)

    def test_prod_rerun_is_noop(self) -> None:
        before = self.production_head().hexsha

        first = self.run_cli("prod")
        second = self.run_cli("prod")

        self.assertEqual(first["status"], "success")
        self.assertEqual(second["status"], "success")
        self.assertEqual(self.production_head().parents[0].hexsha, before)


if __name__ == "__main__":
    unittest.main()
