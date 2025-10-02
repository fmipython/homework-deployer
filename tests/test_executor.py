"""
Tests for the executor module.
"""

import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from git import Repo
from git.exc import GitCommandError

from src.executor import execute, clone_repo, expand_patterns, expand_pattern, copy_files, commit_changes
from src.event import Event


class TestExecute(unittest.TestCase):
    """
    Test suite for the execute function.
    """

    @patch("src.executor.shutil.rmtree")
    @patch("src.executor.commit_changes")
    @patch("src.executor.copy_files")
    @patch("src.executor.expand_patterns")
    @patch("src.executor.clone_repo")
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
        mock_clone.assert_any_call(event.origin, "/tmp/homework-deployer/source")
        mock_clone.assert_any_call(event.destination, "/tmp/homework-deployer/destination")
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
        mock_glob.return_value = [Path("/source/test.txt")]

        # Act
        result = expand_patterns(source_path, dest_path, patterns)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (Path("/source/test.txt"), Path("/dest/test.txt")))

    @patch("pathlib.Path.glob")
    def test_02_multiple_patterns_with_destination(self, mock_glob: MagicMock) -> None:
        """
        Verify correct path transformations for patterns with destinations.
        """
        # Arrange
        source_path = "/source"
        dest_path = "/dest"
        patterns: list[tuple[str, str | None]] = [("c/e.txt", "d/g.txt"), ("c/*.py", "h")]
        mock_glob.side_effect = [[Path("/source/c/e.txt")], [Path("/source/c/test.py")]]

        # Act
        result = expand_patterns(source_path, dest_path, patterns)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], (Path("/source/c/e.txt"), Path("/dest/d/g.txt")))
        self.assertEqual(result[1], (Path("/source/c/test.py"), Path("/dest/h/test.py")))


class TestExpandPattern(unittest.TestCase):
    """
    Test suite for the expand_pattern function.
    """

    def test_01_without_destination_pattern(self) -> None:
        """
        Verify path generation without destination pattern.
        """
        # Arrange
        source_file = Path("/source/test/file.txt")
        source_repo = Path("/source")
        destination_repo = Path("/dest")

        # Act
        result = expand_pattern(source_file, None, source_repo, destination_repo)

        # Assert
        self.assertEqual(result, (source_file, Path("/dest/test/file.txt")))

    def test_02_with_destination_pattern(self) -> None:
        """
        Verify path generation with destination pattern.
        """
        # Arrange
        source_file = Path("/source/test/file.txt")
        dest_pattern = "new/path/renamed.txt"
        source_repo = Path("/source")
        destination_repo = Path("/dest")

        # Act
        result = expand_pattern(source_file, dest_pattern, source_repo, destination_repo)

        # Assert
        self.assertEqual(result, (source_file, Path("/dest/new/path/renamed.txt")))


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
        mock_origin.push.assert_called_once()

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
