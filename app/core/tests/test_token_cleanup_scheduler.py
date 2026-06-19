"""
Tests for the token cleanup scheduler.
"""
from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from core.token_cleanup_scheduler import start_scheduler, _scheduler_started


class TokenCleanupSchedulerTests(SimpleTestCase):
    """Test the token cleanup scheduler."""

    def setUp(self):
        """Reset the scheduler started flag before each test."""
        _scheduler_started.clear()

    @patch('core.token_cleanup_scheduler.schedule')
    @patch('core.token_cleanup_scheduler.threading')
    def test_scheduler_schedules_daily_cleanup(
        self, mock_threading, mock_schedule
    ):
        """Test that the cleanup command is scheduled every day."""
        mock_thread = MagicMock()
        mock_threading.Thread.return_value = mock_thread

        start_scheduler()

        # Verify schedule.every(1).day.do(run_cleanup) was called
        mock_schedule.every.assert_called_once_with(1)
        mock_schedule.every.return_value.day.do.assert_called_once()
        mock_thread.start.assert_called_once()

    @patch('core.token_cleanup_scheduler.schedule')
    @patch('core.token_cleanup_scheduler.threading')
    def test_run_cleanup_calls_command(
        self, mock_threading, mock_schedule
    ):
        """Test that run_cleanup calls the management command."""
        from core.token_cleanup_scheduler import run_cleanup
        with patch(
            'core.token_cleanup_scheduler.call_command'
        ) as mock_call_command:
            run_cleanup()
            mock_call_command.assert_called_once_with(
                'cleanup_blacklisted_tokens',
                days=1,
            )

    @patch('core.token_cleanup_scheduler.schedule')
    @patch('core.token_cleanup_scheduler.threading')
    def test_run_cleanup_handles_errors_gracefully(
        self, mock_threading, mock_schedule
    ):
        """Test that run_cleanup does not crash on errors."""
        from core.token_cleanup_scheduler import run_cleanup
        with patch(
            'core.token_cleanup_scheduler.call_command'
        ) as mock_call_command:
            mock_call_command.side_effect = Exception('Test error')
            # Should not raise
            run_cleanup()

    @patch('core.token_cleanup_scheduler.schedule')
    @patch('core.token_cleanup_scheduler.threading')
    def test_scheduler_only_runs_once(
        self, mock_threading, mock_schedule
    ):
        """Test that calling start_scheduler twice only creates one thread."""
        mock_thread = MagicMock()
        mock_threading.Thread.return_value = mock_thread

        start_scheduler()
        start_scheduler()

        # Thread should only be created and started once
        mock_threading.Thread.assert_called_once()
        mock_thread.start.assert_called_once()
        # schedule.every should only be called once
        mock_schedule.every.assert_called_once()
