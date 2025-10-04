"""
Tests for the db module.
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
from datetime import datetime

from homework_deployer.db import load, add, remove
from homework_deployer.event import Event


class TestLoad(unittest.TestCase):
    """
    Test suite for the load function.
    """

    @patch("builtins.open")
    def test_01_successful_load(self, mock_file: MagicMock) -> None:
        """
        Verify that load returns correct data when file exists.
        """
        # Arrange
        test_data = {"test1": (42, "/path/to/config")}
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(test_data)

        # Act
        actual_result = load("test.json")

        # Assert
        self.assertEqual(actual_result, test_data)

    @patch("builtins.open")
    def test_02_file_not_found(self, mock_file: MagicMock) -> None:
        """
        Verify that load returns empty dict when file doesn't exist.
        """
        # Arrange
        mock_file.side_effect = FileNotFoundError()

        # Act
        actual_result = load("test.json")

        # Assert
        self.assertEqual(actual_result, {})


class TestAdd(unittest.TestCase):
    """
    Test suite for the add function.
    """

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("homework_deployer.db.load")
    def test_01_add_new_event(self, mock_load: MagicMock, mock_json_dump: MagicMock, mock_file: MagicMock) -> None:
        """
        Verify that add correctly stores a new event.
        """
        # Arrange
        mock_load.return_value = {}
        expected_id = "test1"
        event = Event(
            id=expected_id,
            name="test_event",
            description="Test event",
            origin="/source",
            destination="/dest",
            date=datetime(2024, 1, 1, 12, 0),
            patterns=[("*.txt", None)],
        )

        expected_path = "/config/path"
        expected_at_id = 42

        expected_entry = {expected_id: (expected_at_id, expected_path)}
        # Act
        add("test.json", event, expected_path, expected_at_id)

        # Assert
        mock_json_dump.assert_called_once_with(expected_entry, mock_file(), indent=4)


class TestRemove(unittest.TestCase):
    """
    Test suite for the remove function.
    """

    @patch("builtins.open", new_callable=mock_open)
    @patch("homework_deployer.db.load")
    def test_01_remove_existing_event(self, mock_load: MagicMock, mock_file: MagicMock) -> None:
        """
        Verify that remove correctly deletes an existing event.
        """
        # Arrange
        mock_load.return_value = {"test1": [42, "/config/path"]}

        # Act
        remove("test.json", "test1")

        # Assert
        mock_file().write.assert_called_once()
        written_data = json.loads(mock_file().write.call_args[0][0])
        self.assertEqual(written_data, {})

    @patch("builtins.open", new_callable=mock_open)
    @patch("homework_deployer.db.load")
    def test_02_remove_non_existing_event(self, mock_load: MagicMock, mock_file: MagicMock) -> None:
        """
        Verify that remove does nothing for non-existing event.
        """
        # Arrange
        mock_load.return_value = {"test1": [42, "/config/path"]}

        # Act
        remove("test.json", "test2")

        # Assert
        mock_file().write.assert_not_called()
