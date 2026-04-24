"""Integration tests for login count tracking via actual API."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import LoginActivity
from django.utils import timezone
from unittest.mock import patch

User = get_user_model()


class LoginCountIntegrationTests(TestCase):
    """Integration tests verifying login counts update via actual API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.email_verified = True
        self.user.save()

    def _login_user(self):
        """Helper to login the test user via API."""
        url = reverse('user:token')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        return self.client.post(url, data, format='json')

    def test_login_via_api_creates_login_activity(self):
        """Test that a successful login via API creates a LoginActivity."""
        response = self._login_user()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        activities = LoginActivity.objects.filter(
            user=self.user, success=True)
        self.assertEqual(activities.count(), 1)

    def test_multiple_logins_increment_total_logins(self):
        """
        Test that logging in multiple times updates total_logins correctly.
        This reproduces the bug where login/logout 4 times
        doesn't update count.
        """
        # Login 4 times
        for _ in range(4):
            response = self._login_user()
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check dashboard stats
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_logins'], 4)
        self.assertEqual(
            response.data['total_successful_logins'], 4)
        self.assertEqual(
            response.data['total_failed_logins'], 0)

    def test_failed_login_via_api_creates_failed_activity(self):
        """Test that failed login via API creates failed LoginActivity."""
        url = reverse('user:token')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        activities = LoginActivity.objects.filter(
            user=self.user, success=False)
        self.assertEqual(activities.count(), 1)

    def test_mixed_successful_and_failed_logins_count_correctly(self):
        """Test that mixed login attempts count correctly."""
        # 2 successful logins
        for _ in range(2):
            self._login_user()

        # 2 failed logins
        url = reverse('user:token')
        for _ in range(2):
            self.client.post(url, {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }, format='json')

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user:dashboard-stats'))

        self.assertEqual(response.data['total_logins'], 4)
        self.assertEqual(
            response.data['total_successful_logins'], 2)
        self.assertEqual(
            response.data['total_failed_logins'], 2)


class LoginTimeAccuracyTests(TestCase):
    """Tests for login time record accuracy."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_last_login_timestamp_matches_activity_timestamp(self):
        """
        Test that user.last_login_timestamp exactly matches
        the LoginActivity.timestamp.
        """
        login_time = timezone.now()
        activity = LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            success=True,
            timestamp=login_time
        )

        self.user.refresh_from_db()
        self.assertEqual(
            self.user.last_login_timestamp,
            activity.timestamp,
            "last_login_timestamp must exactly match "
            "LoginActivity.timestamp"
        )

    def test_weekly_and_monthly_keys_use_activity_timestamp(self):
        """
        Test that weekly_logins and monthly_logins keys are derived
        from the LoginActivity.timestamp, not a separate
        timezone.now() call.
        """
        # Use a specific timestamp
        specific_time = timezone.make_aware(
            timezone.datetime(2025, 12, 15, 14, 30, 0)
        )

        LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            success=True,
            timestamp=specific_time
        )

        self.user.refresh_from_db()

        expected_week_key = specific_time.strftime('%Y-%U')
        expected_month_key = specific_time.strftime('%Y-%m')

        self.assertIn(
            expected_week_key,
            self.user.weekly_logins,
            f"Weekly logins should contain key {expected_week_key}"
        )
        self.assertIn(
            expected_month_key,
            self.user.monthly_logins,
            f"Monthly logins should contain key {expected_month_key}"
        )

    def test_time_accuracy_near_boundary(self):
        """
        Test that time-based stats are accurate even when created
        near a week/month boundary where timezone.now() could differ
        from the activity timestamp.
        """
        # Simulate a scenario where super().save() and timezone.now()
        # could produce different week/month keys
        # We mock timezone.now() to return a time AFTER the boundary
        # while the activity timestamp is BEFORE the boundary
        just_before_midnight = timezone.make_aware(
            timezone.datetime(2025, 12, 31, 23, 59, 59)
        )
        just_after_midnight = timezone.make_aware(
            timezone.datetime(2026, 1, 1, 0, 0, 1)
        )

        with patch(
            'django.utils.timezone.now',
            return_value=just_after_midnight
        ):
            LoginActivity.objects.create(
                user=self.user,
                ip_address='192.168.1.1',
                user_agent='Test Browser',
                success=True,
                timestamp=just_before_midnight
            )

        self.user.refresh_from_db()

        # Weekly/monthly keys should be based on activity timestamp
        # (2025-12-31), NOT the mocked timezone.now() (2026-01-01)
        expected_week_key = just_before_midnight.strftime('%Y-%U')
        expected_month_key = just_before_midnight.strftime('%Y-%m')

        self.assertIn(expected_week_key, self.user.weekly_logins)
        self.assertIn(expected_month_key, self.user.monthly_logins)

        # Should NOT contain keys from the mocked later time
        wrong_week_key = just_after_midnight.strftime('%Y-%U')
        wrong_month_key = just_after_midnight.strftime('%Y-%m')

        if wrong_week_key != expected_week_key:
            self.assertNotIn(
                wrong_week_key,
                self.user.weekly_logins,
                "Weekly key should not be based on timezone.now()"
            )
        if wrong_month_key != expected_month_key:
            self.assertNotIn(
                wrong_month_key,
                self.user.monthly_logins,
                "Monthly key should not be based on timezone.now()"
            )
