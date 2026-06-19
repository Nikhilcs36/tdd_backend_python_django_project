"""
Test custom Django management commands.
"""
from unittest.mock import patch
from datetime import timedelta
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase, SimpleTestCase
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from django.contrib.auth import get_user_model


@patch('core.management.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    """Test commands."""

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for database if database is ready."""
        patched_check.return_value = True

        call_command('wait_for_db')

        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waiting for database when getting OperationalError."""
        # Simulate the database being unavailable 5 times before succeeding
        patched_check.side_effect = [OperationalError] * 5 + [True]

        call_command('wait_for_db')

        self.assertEqual(patched_check.call_count, 6)
        patched_check.assert_called_with(databases=['default'])


class CleanupBlacklistedTokensCommandTests(TestCase):
    """Test the cleanup_blacklisted_tokens management command."""

    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        now = timezone.now()

        # Create an expired outstanding token (expired 1 hour ago)
        self.expired_outstanding = OutstandingToken.objects.create(
            user=self.user,
            jti='expired-jti-1',
            token='expired-token-1',
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )
        # Create a blacklisted token for the expired outstanding token
        self.expired_blacklisted = BlacklistedToken.objects.create(
            token=self.expired_outstanding,
        )

        # Create a non-expired outstanding token (expires in 1 hour)
        self.valid_outstanding = OutstandingToken.objects.create(
            user=self.user,
            jti='valid-jti-1',
            token='valid-token-1',
            created_at=now,
            expires_at=now + timedelta(hours=1),
        )
        # Create a blacklisted token for the valid outstanding token
        self.valid_blacklisted = BlacklistedToken.objects.create(
            token=self.valid_outstanding,
        )

    def test_cleanup_removes_expired_tokens_and_blacklist(self):
        """Test that expired tokens and their blacklist entries are removed."""
        call_command('cleanup_blacklisted_tokens')

        # Expired outstanding token should be deleted
        self.assertFalse(
            OutstandingToken.objects.filter(
                jti='expired-jti-1'
            ).exists()
        )
        # Associated blacklisted token should also be deleted (cascade)
        self.assertFalse(
            BlacklistedToken.objects.filter(
                id=self.expired_blacklisted.id
            ).exists()
        )

    def test_cleanup_preserves_valid_tokens_and_blacklist(self):
        """Test that non-expired tokens and their blacklist are preserved."""
        call_command('cleanup_blacklisted_tokens')

        # Valid outstanding token should still exist
        self.assertTrue(
            OutstandingToken.objects.filter(
                jti='valid-jti-1'
            ).exists()
        )
        # Associated blacklisted token should still exist
        self.assertTrue(
            BlacklistedToken.objects.filter(
                id=self.valid_blacklisted.id
            ).exists()
        )

    def test_cleanup_only_removes_own_blacklisted(self):
        """
        Test that cleanup only removes blacklist entries associated
        with expired tokens, not all blacklisted tokens.
        """
        call_command('cleanup_blacklisted_tokens')

        # Only the expired token's blacklist entry should be gone
        remaining_blacklisted = BlacklistedToken.objects.count()
        self.assertEqual(remaining_blacklisted, 1)
