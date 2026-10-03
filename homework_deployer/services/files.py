import shutil
from pathlib import Path

from homework_deployer.models import DeploymentConfig


def copy_test_files(
    staging_homework_directory: Path, deployment: DeploymentConfig, production_homework_directory: Path
) -> None:
    """Copy test files."""
    for test_file in deployment.test_files:
        test_file_path = str(staging_homework_directory / test_file)
        test_file_dest = str(production_homework_directory)
        shutil.copy(test_file_path, test_file_dest)


def copy_statement(
    staging_homework_directory: Path, deployment: DeploymentConfig, production_homework_directory: Path
) -> None:
    """Copy statement file."""
    statement_file_path = str(staging_homework_directory / deployment.statement_file)
    statement_file_dest = str(production_homework_directory)
    shutil.copy(statement_file_path, statement_file_dest)
