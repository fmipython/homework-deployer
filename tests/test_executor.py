"""
Tests for the executor module.
"""

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
    expand_patterns,
    expand_pattern,
    copy_files,
    commit_changes,
    PatternError,
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


class TestExpandPatterns(unittest.TestCase):
    """
    Test suite for the expand_patterns function.
    """

    @patch("pathlib.Path.glob")
    def test_01_single_pattern_no_destination(self, mock_glob: MagicMock) -> None:
        """
        Verify correct path pairs for pattern without destination.
        """
        # Arrange
        source_path = "/source"
        dest_path = "/dest"
        patterns: list[tuple[str, str | None]] = [("*.txt", None)]
        mock_glob.return_value = [Path("test.txt")]

        # Act
        result = expand_patterns(source_path, dest_path, patterns)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (Path("/source/test.txt"), Path("/dest/test.txt")))

    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.is_file")
    def test_03_source_glob_with_file_destination(self, mock_is_file: MagicMock, mock_glob: MagicMock) -> None:
        """
        Verify correct path transformations for patterns with destinations.
        """
        # Arrange
        source_path = "/source"
        dest_path = "/dest"
        patterns: list[tuple[str, str | None]] = [("c/*.py", "h/a.py")]
        mock_glob.side_effect = [[Path("/source/c/e.txt")], [Path("/source/c/test.py")]]
        mock_is_file.return_value = True

        # Act
        with self.assertRaises(PatternError):
            _ = expand_patterns(source_path, dest_path, patterns)


class TestExpandPattern(unittest.TestCase):
    """
    Test suite for the expand_pattern function.
    """

    def test_01_file_to_none_pattern(self) -> None:
        """
        Verify correct path pair for file-to-file pattern.
        """
        # Arrange
        source_repo = Path("/source")
        destination_repo = Path("/dest")
        source_file = Path("c/e.txt")
        destination_pattern = None

        expected_source = source_repo / source_file
        expected_destination = destination_repo / source_file

        # Act
        actual_source, actual_destination = expand_pattern(
            source_file, destination_pattern, source_repo, destination_repo
        )

        # Assert
        self.assertEqual(actual_source, expected_source)
        self.assertEqual(actual_destination, expected_destination)

    def test_02_file_to_file_pattern(self) -> None:
        """
        Verify correct path pair for file-to-file pattern.
        """
        # Arrange
        source_repo = Path("/source")
        destination_repo = Path("/dest")
        source_file = Path("c/e.txt")
        destination_pattern = "d/g.txt"

        expected_source = source_repo / source_file
        expected_destination = destination_repo / Path(destination_pattern)

        # Act
        actual_source, actual_destination = expand_pattern(
            source_file, destination_pattern, source_repo, destination_repo
        )

        # Assert
        self.assertEqual(actual_source, expected_source)
        self.assertEqual(actual_destination, expected_destination)

    @patch("pathlib.Path.is_dir")
    def test_03_file_to_directory_pattern(self, mock_is_dir: MagicMock) -> None:
        """
        Verify correct path pair for file-to-file pattern.
        """
        # Arrange
        source_repo = Path("/source")
        destination_repo = Path("/dest")
        source_file = MagicMock(spec=Path, path=Path("c/e.txt"))
        source_file.name = "e.txt"
        source_file.is_absolute.return_value = False
        source_file.is_file.return_value = True

        mock_is_dir.return_value = True

        destination_pattern = "h"

        expected_source = source_repo / source_file
        expected_destination = destination_repo / Path(destination_pattern) / source_file.name

        # Act
        actual_source, actual_destination = expand_pattern(
            source_file, destination_pattern, source_repo, destination_repo
        )

        # Assert
        self.assertEqual(actual_source, expected_source)
        self.assertEqual(actual_destination, expected_destination)

    def test_04_directory_to_none_pattern(self) -> None:
        """
        Verify correct path pair for file-to-file pattern.
        """
        # Arrange
        source_repo = Path("/source")
        destination_repo = Path("/dest")
        source_file = Path("c")
        destination_pattern = None

        expected_source = source_repo / source_file
        expected_destination = destination_repo / source_file

        # Act
        actual_source, actual_destination = expand_pattern(
            source_file, destination_pattern, source_repo, destination_repo
        )

        # Assert
        self.assertEqual(actual_source, expected_source)
        self.assertEqual(actual_destination, expected_destination)

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.is_dir")
    def test_05_directory_to_file_pattern(self, mock_is_dir: MagicMock, mock_is_file: MagicMock) -> None:
        """
        Verify correct path pair for file-to-file pattern.
        """
        # Arrange
        source_repo = Path("/source")
        destination_repo = Path("/dest")
        source_file = Path("c/e.txt")
        destination_pattern = "d/g.txt"

        mock_is_file.return_value = True
        mock_is_dir.return_value = True
        # Act
        with self.assertRaises(PatternError):
            _ = expand_pattern(source_file, destination_pattern, source_repo, destination_repo)

    def test_06_directory_to_directory_pattern(self) -> None:
        """
        Verify correct path pair for file-to-file pattern.
        """
        # Arrange
        source_repo = Path("/source")
        destination_repo = Path("/dest")
        source_file = Path("c")
        destination_pattern = "h"

        expected_source = source_repo / source_file
        expected_destination = destination_repo / Path(destination_pattern)

        # Act
        actual_source, actual_destination = expand_pattern(
            source_file, destination_pattern, source_repo, destination_repo
        )

        # Assert
        self.assertEqual(actual_source, expected_source)
        self.assertEqual(actual_destination, expected_destination)


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
