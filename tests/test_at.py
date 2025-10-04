"""
Tests for the at module.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime


from homework_deployer.at import is_at_available, register, deregister, build_command
from homework_deployer.event import Event


class TestIsAtAvailable(unittest.TestCase):
    """
    Test suite for the is_at_available function.
    """

    @patch("homework_deployer.at.run")
    def test_01_run_returns_0(self, mock_run: MagicMock) -> None:
        """
        Verify that is_at_available returns True when 'which at' command succeeds.
        """
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)

        # Act
        actual_result = is_at_available()

        # Assert
        self.assertTrue(actual_result)

    @patch("homework_deployer.at.run")
    def test_02_run_returns_non_zero(self, mock_run: MagicMock) -> None:
        """
        Verify that is_at_available returns False when 'which at' command fails.
        """
        # Arrange
        mock_run.return_value = MagicMock(returncode=1)

        # Act
        actual_result = is_at_available()

        # Assert
        self.assertFalse(actual_result)


class TestRegister(unittest.TestCase):
    """
    Test suite for the register function.
    """

    @patch("homework_deployer.at.run")
    def test_01_successful_registration(self, mock_run: MagicMock) -> None:
        """
        Verify that register returns the correct job ID when 'at' command succeeds.
        """
        # Arrange
        mock_run.return_value = MagicMock(returncode=0, stderr="job 42 at Mon Jan 01 12:00:00 2024")
        test_date = datetime(2024, 1, 1, 12, 0)
        event = Event(
            id="test1",
            name="test_event",
            description="Test event",
            origin="/source",
            destination="/dest",
            date=test_date,
            patterns=[("*.txt", None)],
        )

        # Act
        actual_result = register(event)

        # Assert
        self.assertEqual(actual_result, 42)

    @patch("homework_deployer.at.run")
    def test_02_failed_registration(self, mock_run: MagicMock) -> None:
        """
        Verify that register returns None when 'at' command fails.
        """
        # Arrange
        mock_run.return_value = MagicMock(returncode=1)
        test_date = datetime(2024, 1, 1, 12, 0)
        event = Event(
            id="test2",
            name="test_event",
            description="Test event",
            origin="/source",
            destination="/dest",
            date=test_date,
            patterns=[("*.txt", None)],
        )

        # Act
        actual_result = register(event)

        # Assert
        self.assertIsNone(actual_result)

    @patch("homework_deployer.at.run")
    def test_03_verify_command_execution(self, mock_run: MagicMock) -> None:
        """
        Verify that register executes 'at' command with correct parameters.
        """
        # Arrange
        mock_run.return_value = MagicMock(returncode=0, stderr="job 42 at Mon Jan 01 12:00:00 2024")
        test_date = datetime(2024, 1, 1, 12, 0)
        event = Event(
            id="test3",
            name="test_event",
            description="Test event",
            origin="/source",
            destination="/dest",
            date=test_date,
            patterns=[("*.txt", None)],
        )
        expected_command = ["at", "-t", "2401011200"]
        expected_input = build_command(event)

        # Act
        register(event)

        # Assert
        mock_run.assert_called_once_with(
            expected_command, input=expected_input, check=False, text=True, capture_output=True
        )


class TestDeregister(unittest.TestCase):
    """
    Test suite for the deregister function.
    """

    @patch("homework_deployer.at.run")
    def test_01_successful_deregistration(self, mock_run: MagicMock) -> None:
        """
        Verify that deregister returns True when 'at' command succeeds.
        """
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)
        at_id = 42

        # Act
        actual_result = deregister(at_id)

        # Assert
        self.assertTrue(actual_result)

    @patch("homework_deployer.at.run")
    def test_02_failed_deregistration(self, mock_run: MagicMock) -> None:
        """
        Verify that deregister returns False when 'at' command fails.
        """
        # Arrange
        mock_run.return_value = MagicMock(returncode=1)
        at_id = 42

        # Act
        actual_result = deregister(at_id)

        # Assert
        self.assertFalse(actual_result)

    @patch("homework_deployer.at.run")
    def test_03_verify_command_execution(self, mock_run: MagicMock) -> None:
        """
        Verify that deregister executes 'at' command with correct parameters.
        """
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)
        at_id = 42
        expected_command = ["at", "-r", "42"]

        # Act
        deregister(at_id)

        # Assert
        mock_run.assert_called_once_with(expected_command, check=False, text=True, capture_output=True)
