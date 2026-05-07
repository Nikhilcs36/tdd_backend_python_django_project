"""Tests for timezone handling in dashboard chart functions.

This test verifies that TruncWeek and TruncMonth are called with
explicit UTC timezone info to avoid MySQL timezone table dependency.
"""
from unittest import mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import datetime
from django.db.models.functions import TruncWeek, TruncMonth


User = get_user_model()


class TimezoneFixTests(TestCase):
    """Test that truncation functions use explicit UTC timezone."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def _spy_on_trunc_init(self, trunc_class):
        """Patch __init__ to spy on calls while maintaining normal behavior."""
        original_init = trunc_class.__init__

        def patched_init(self, *args, **kwargs):
            patched_init.called_args = args
            patched_init.called_kwargs = kwargs
            return original_init(self, *args, **kwargs)

        patched_init.called_args = None
        patched_init.called_kwargs = None

        return mock.patch.object(
            trunc_class, '__init__', patched_init
        )

    def test_get_login_comparison_data_uses_utc_tzinfo(self):
        """Test that get_login_comparison_data passes tzinfo=utc to TruncWeek.

        Without explicit tzinfo, Django uses the TIME_ZONE setting which causes
        MySQL's CONVERT_TZ() to be called, requiring timezone tables.
        """
        from user.serializers_dashboard import get_login_comparison_data

        with self._spy_on_trunc_init(TruncWeek) as mock_init:
            start_date = timezone.now() - timedelta(days=7)
            end_date = timezone.now()

            # This will succeed on SQLite (test db) - we just need the mock
            # to capture the constructor arguments
            try:
                get_login_comparison_data(
                    self.user,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception:
                pass

            # Even if query fails during compilation, the __init__ spy
            # should have been called with the right arguments
            if mock_init.called_kwargs is not None:
                self.assertIn(
                    'tzinfo', mock_init.called_kwargs,
                    'TruncWeek must be called with tzinfo parameter'
                )
                self.assertEqual(
                    mock_init.called_kwargs['tzinfo'],
                    datetime.timezone.utc,
                    'TruncWeek must use UTC timezone'
                )
            else:
                self.fail('TruncWeek.__init__ was never called')

    def test_get_login_comparison_data_uses_utc_tzinfo_monthly(self):
        """Test that get_login_comparison_data passes tzinfo=utc to TruncMonth.

        For date ranges > 30 days, TruncMonth is used instead of TruncWeek.
        """
        from user.serializers_dashboard import get_login_comparison_data

        with self._spy_on_trunc_init(TruncMonth) as mock_init:
            start_date = timezone.now() - timedelta(days=90)
            end_date = timezone.now()

            try:
                get_login_comparison_data(
                    self.user,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception:
                pass

            if mock_init.called_kwargs is not None:
                self.assertIn(
                    'tzinfo', mock_init.called_kwargs,
                    'TruncMonth must be called with tzinfo parameter'
                )
                self.assertEqual(
                    mock_init.called_kwargs['tzinfo'],
                    datetime.timezone.utc,
                    'TruncMonth must use UTC timezone'
                )
            else:
                self.fail('TruncMonth.__init__ was never called')

    def test_get_combined_login_comparison_data_uses_utc_tzinfo(self):
        """Test that get_combined_login_comparison_data passes tzinfo=utc."""
        from user.serializers_dashboard import (
            get_combined_login_comparison_data
        )

        with self._spy_on_trunc_init(TruncWeek) as mock_init:
            start_date = timezone.now() - timedelta(days=7)
            end_date = timezone.now()

            try:
                get_combined_login_comparison_data(
                    [self.user],
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception:
                pass

            if mock_init.called_kwargs is not None:
                self.assertIn(
                    'tzinfo', mock_init.called_kwargs,
                    'TruncWeek must be called with tzinfo parameter'
                )
                self.assertEqual(
                    mock_init.called_kwargs['tzinfo'],
                    datetime.timezone.utc,
                    'TruncWeek must use UTC timezone'
                )
            else:
                self.fail('TruncWeek.__init__ was never called')