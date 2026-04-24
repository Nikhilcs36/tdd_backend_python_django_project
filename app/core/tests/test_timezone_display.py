"""Tests for timezone-aware timestamp display."""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
from core.models import LoginActivity
from user.serializers_dashboard import LoginActivitySerializer

User = get_user_model()


class TimezoneDisplayTests(TestCase):
    """Test that timestamps display in local timezone consistently."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @override_settings(TIME_ZONE='Asia/Kolkata', USE_TZ=True)
    def test_login_activity_shows_local_time_not_utc(self):
        """
        Test that LoginActivity timestamp is stored and displayed
        in local timezone, not UTC.
        """
        with timezone.override('Asia/Kolkata'):
            # Create activity at a known local time: 22:00 IST
            local_time = timezone.make_aware(
                datetime(2026, 4, 24, 22, 0, 0)
            )

            activity = LoginActivity.objects.create(
                user=self.user,
                ip_address='192.168.1.1',
                user_agent='Test Browser',
                success=True,
                timestamp=local_time
            )

            # Verify DB stores local time (22:00) when read back
            activity.refresh_from_db()
            db_hour = timezone.localtime(activity.timestamp).hour
            self.assertEqual(
                db_hour, 22,
                f"DB should store 22:00 local time, got {db_hour}"
            )

            # Verify API serializer shows local time
            serializer = LoginActivitySerializer(activity)
            timestamp_str = serializer.data['timestamp']
            self.assertIn('22:00:00', timestamp_str)

    @override_settings(TIME_ZONE='Asia/Kolkata', USE_TZ=True)
    def test_db_and_api_show_same_time(self):
        """
        Test that DB timestamp and API response show the same hour,
        preventing debugging confusion.
        """
        with timezone.override('Asia/Kolkata'):
            local_time = timezone.make_aware(
                datetime(2026, 4, 24, 15, 30, 0)
            )

            activity = LoginActivity.objects.create(
                user=self.user,
                ip_address='192.168.1.1',
                user_agent='Test Browser',
                success=True,
                timestamp=local_time
            )

            activity.refresh_from_db()
            db_hour = timezone.localtime(activity.timestamp).hour
            db_minute = timezone.localtime(activity.timestamp).minute

            serializer = LoginActivitySerializer(activity)
            api_time = serializer.data['timestamp']

            # Extract hour:minute from API string
            # (format: YYYY-MM-DD HH:MM:SS)
            api_time_part = api_time.split(' ')[1]
            api_hour, api_minute = api_time_part.split(':')[:2]

            self.assertEqual(
                db_hour, int(api_hour),
                f"DB hour ({db_hour}) must match API hour ({api_hour})"
            )
            self.assertEqual(
                db_minute, int(api_minute),
                f"DB minute ({db_minute}) must match API minute ({api_minute})"
            )

    @override_settings(TIME_ZONE='Asia/Kolkata', USE_TZ=True)
    def test_user_last_login_timestamp_matches_db(self):
        """
        Test that user.last_login_timestamp in DB matches
        what's returned via API.
        """
        with timezone.override('Asia/Kolkata'):
            local_time = timezone.make_aware(
                datetime(2026, 4, 24, 20, 45, 0)
            )

            LoginActivity.objects.create(
                user=self.user,
                ip_address='192.168.1.1',
                user_agent='Test Browser',
                success=True,
                timestamp=local_time
            )

            self.user.refresh_from_db()
            db_hour = timezone.localtime(
                self.user.last_login_timestamp).hour

            # The API uses strftime('%Y-%m-%d %H:%M:%S')
            api_time = timezone.localtime(
                self.user.last_login_timestamp).strftime(
                    '%Y-%m-%d %H:%M:%S')
            api_hour = int(api_time.split(' ')[1].split(':')[0])

            self.assertEqual(
                db_hour, api_hour,
                f"DB hour ({db_hour}) must match API hour ({api_hour})"
            )
