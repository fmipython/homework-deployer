"""
Tests for the executor module.
"""

import os
import shutil
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from git import Repo
from git.exc import GitCommandError

import homework_deployer.constants as const
from homework_deployer.executor import (
    execute,
    clone_repo,
    copy_files,
    commit_changes,
    expand_patterns,
)
from homework_deployer.event import Event


class TestExecute(unittest.TestCase):
    """
    Test suite for the execute function.
    """

    @patch("homework_deployer.executor.shutil.rmtree")
    @patch("homework_deployer.executor.commit_changes")
    @patch("homework_deployer.executor.copy_files")
    @patch("homework_deployer.executor.expand_patterns")
    @patch("homework_deployer.executor.clone_repo")
    def test_01_successful_execution(
        self,
        mock_clone: MagicMock,
        mock_expand: MagicMock,
        mock_copy: MagicMock,
        mock_commit: MagicMock,
        mock_rmtree: MagicMock,
    ) -> None:
        """
        Verify that execute successfully processes an event.
        """
        # Arrange
        test_date = datetime(2024, 1, 1, 12, 0)
        event = Event(
            id="test1",
            name="test_event",
            description="Test event",
            origin="git@github.com:source/repo.git",
            destination="git@github.com:dest/repo.git",
            date=test_date,
            patterns=[(str("*.txt"), None)],  # Cast to ensure correct type
        )
        mock_source_repo = MagicMock()
        mock_dest_repo = MagicMock()
        mock_clone.side_effect = [mock_source_repo, mock_dest_repo]
        mock_expand.return_value = [(Path("/source/test.txt"), Path("/dest/test.txt"))]

        # Act
        execute(event)

        # Assert
        mock_clone.assert_any_call(event.origin, const.SOURCE_REPO_DIR)
        mock_clone.assert_any_call(event.destination, const.DESTINATION_REPO_DIR)
        mock_expand.assert_called_once()
        mock_copy.assert_called_once()
        mock_commit.assert_called_once()
        mock_rmtree.assert_called_once()


class TestCloneRepo(unittest.TestCase):
    """
    Test suite for the clone_repo function.
    """

    @patch("git.Repo.clone_from")
    def test_01_successful_clone(self, mock_clone_from: MagicMock) -> None:
        """
        Verify that clone_repo successfully clones a repository.
        """
        # Arrange
        url = "git@github.com:test/repo.git"
        destination = "/tmp/test"
        mock_repo = MagicMock()
        mock_clone_from.return_value = mock_repo

        # Act
        result = clone_repo(url, destination)

        # Assert
        self.assertEqual(result, mock_repo)
        mock_clone_from.assert_called_once_with(url, destination)

    @patch("git.Repo.clone_from")
    def test_02_failed_clone(self, mock_clone_from: MagicMock) -> None:
        """
        Verify that clone_repo raises GitCommandError when clone fails.
        """
        # Arrange
        url = "invalid_url"
        destination = "/tmp/test"
        mock_clone_from.side_effect = GitCommandError("clone", "error")

        # Act & Assert
        with self.assertRaises(GitCommandError):
            clone_repo(url, destination)


class TestCopyFiles(unittest.TestCase):
    """
    Test suite for the copy_files function.
    """

    @patch("pathlib.Path.mkdir")
    @patch("shutil.copy2")
    def test_01_successful_copy(self, mock_copy2: MagicMock, mock_mkdir: MagicMock) -> None:
        """
        Verify files are copied correctly.
        """
        # Arrange
        paths = [
            (Path("/source/test.txt"), Path("/dest/test.txt")),
            (Path("/source/dir/file.txt"), Path("/dest/dir/file.txt")),
        ]

        # Act
        copy_files(paths)

        # Assert
        self.assertEqual(mock_mkdir.call_count, 2)
        self.assertEqual(mock_copy2.call_count, 2)

    @patch("pathlib.Path.mkdir")
    @patch("shutil.copy2")
    def test_02_copy_with_error(self, mock_copy2: MagicMock, mock_mkdir: MagicMock) -> None:
        """
        Verify error handling when copy fails.
        """
        # Arrange
        paths = [(Path("/source/test.txt"), Path("/dest/test.txt"))]
        mock_copy2.side_effect = IOError("Permission denied")

        # Act & Assert
        with self.assertRaises(IOError):
            copy_files(paths)


class TestCommitChanges(unittest.TestCase):
    """
    Test suite for the commit_changes function.
    """

    def test_01_with_changes(self) -> None:
        """
        Verify commit and push when changes exist.
        """
        # Arrange
        mock_repo = MagicMock(spec=Repo)
        mock_repo.is_dirty.return_value = True
        mock_origin = MagicMock()
        mock_repo.remote.return_value = mock_origin
        message = "Test commit"

        # Act
        commit_changes(mock_repo, message)

        # Assert
        mock_repo.git.add.assert_called_once_with(A=True)
        mock_repo.index.commit.assert_called_once_with(message)

    def test_02_without_changes(self) -> None:
        """
        Verify no commit or push when no changes exist.
        """
        # Arrange
        mock_repo = MagicMock(spec=Repo)
        mock_repo.is_dirty.return_value = False
        message = "Test commit"

        # Act
        commit_changes(mock_repo, message)

        # Assert
        mock_repo.git.add.assert_called_once_with(A=True)
        mock_repo.index.commit.assert_not_called()
        mock_repo.remote.assert_not_called()


class TestPatterns(unittest.TestCase):
    temp_dir = os.path.join("/tmp", "test_patterns")

    def setUp(self) -> None:
        if os.path.exists(TestPatterns.temp_dir):
            shutil.rmtree(TestPatterns.temp_dir)

        os.makedirs(TestPatterns.temp_dir)

        first_dir = os.path.join(TestPatterns.temp_dir, "A")
        os.makedirs(first_dir)

        first_sub_dir = os.path.join(first_dir, "c")
        os.makedirs(first_sub_dir)

        first_file = os.path.join(first_sub_dir, "e.txt")

        with open(first_file, "w+") as file:
            file.write("Temp file")

        second_file = os.path.join(first_sub_dir, "j.txt")

        with open(second_file, "w+") as file:
            file.write("Temp file")

        return super().setUp()

    def tearDown(self) -> None:
        shutil.rmtree(TestPatterns.temp_dir)
        return super().tearDown()

    def test_01_file_to_none(self) -> None:
        # Arrange
        file_pattern = os.path.join("c", "e.txt")
        source_path = os.path.join(TestPatterns.temp_dir, "A")
        destination_path = os.path.join(TestPatterns.temp_dir, "B")

        expected_paths = [(Path(source_path) / file_pattern, Path(destination_path) / file_pattern)]

        # Act
        actual_paths = expand_patterns(source_path, destination_path, [(file_pattern, None)])

        # Assert
        self.assertEqual(actual_paths, expected_paths)

    def test_02_file_to_file(self) -> None:
        # Arrange
        file_pattern = os.path.join("c", "e.txt")
        source_path = os.path.join(TestPatterns.temp_dir, "A")
        destination_path = os.path.join(TestPatterns.temp_dir, "B")
        destination_pattern = os.path.join("d", "g.txt")

        expected_paths = [(Path(source_path) / file_pattern, Path(destination_path) / destination_pattern)]

        # Act
        actual_paths = expand_patterns(source_path, destination_path, [(file_pattern, destination_pattern)])

        # Assert
        self.assertEqual(actual_paths, expected_paths)

    def test_03_file_to_directory(self) -> None:
        # Arrange
        file_pattern = os.path.join("c", "e.txt")
        source_path = os.path.join(TestPatterns.temp_dir, "A")
        destination_path = os.path.join(TestPatterns.temp_dir, "B")
        destination_pattern = os.path.join("h")

        expected_paths = [(Path(source_path) / file_pattern, Path(destination_path) / destination_pattern / "e.txt")]

        # Act
        actual_paths = expand_patterns(source_path, destination_path, [(file_pattern, destination_pattern)])

        # Assert
        self.assertEqual(actual_paths, expected_paths)

    def test_04_directory_to_none(self) -> None:
        # Arrange
        file_pattern = "c"
        source_path = os.path.join(TestPatterns.temp_dir, "A")
        destination_path = os.path.join(TestPatterns.temp_dir, "B")

        expected_paths = [(Path(source_path) / file_pattern, Path(destination_path) / file_pattern)]

        # Act
        actual_paths = expand_patterns(source_path, destination_path, [(file_pattern, None)])

        # Assert
        self.assertEqual(actual_paths, expected_paths)

    def test_05_directory_to_directory(self) -> None:
        # Arrange
        file_pattern = "c"
        source_path = os.path.join(TestPatterns.temp_dir, "A")
        destination_path = os.path.join(TestPatterns.temp_dir, "B")
        destination_pattern = "h"

        expected_paths = [(Path(source_path) / file_pattern, Path(destination_path) / destination_pattern)]

        # Act
        actual_paths = expand_patterns(source_path, destination_path, [(file_pattern, destination_pattern)])

        # Assert
        self.assertEqual(actual_paths, expected_paths)

    def test_06_glob_to_none(self) -> None:
        # Arrange
        file_pattern = "c/*.txt"
        source_path = os.path.join(TestPatterns.temp_dir, "A")
        destination_path = os.path.join(TestPatterns.temp_dir, "B")

        expected_paths = set(
            [
                (Path(source_path) / "c" / "e.txt", Path(destination_path) / "c" / "e.txt"),
                (Path(source_path) / "c" / "j.txt", Path(destination_path) / "c" / "j.txt"),
            ]
        )

        # Act
        actual_paths = set(expand_patterns(source_path, destination_path, [(file_pattern, None)]))

        # Assert
        self.assertEqual(actual_paths, expected_paths)

    def test_07_glob_to_directory(self) -> None:
        # Arrange
        file_pattern = "c/*.txt"
        source_path = os.path.join(TestPatterns.temp_dir, "A")
        destination_path = os.path.join(TestPatterns.temp_dir, "B")
        destination_pattern = "h"

        expected_paths = set(
            [
                (Path(source_path) / "c" / "e.txt", Path(destination_path) / destination_pattern / "e.txt"),
                (Path(source_path) / "c" / "j.txt", Path(destination_path) / destination_pattern / "j.txt"),
            ]
        )

        # Act
        actual_paths = set(expand_patterns(source_path, destination_path, [(file_pattern, destination_pattern)]))

        # Assert
        self.assertEqual(actual_paths, expected_paths)
