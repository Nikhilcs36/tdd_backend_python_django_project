"""Tests for dashboard API endpoints."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import LoginActivity
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class DashboardAPITests(TestCase):
    """Test cases for dashboard API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123'
        )

        # Create some login activities for testing
        self._create_test_login_activities()

    def _create_test_login_activities(self):
        """Create test login activities for the user."""
        # Create successful logins for the user
        for i in range(5):
            activity = LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=True
            )
            # Manually set timestamp since auto_now_add ignores the parameter
            activity.timestamp = timezone.now() - timedelta(days=i)
            activity.save()

        # Create some failed logins
        for i in range(2):
            activity = LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.2.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=False
            )
            # Manually set timestamp since auto_now_add ignores the parameter
            activity.timestamp = timezone.now() - timedelta(days=i+10)
            activity.save()

    def test_user_stats_endpoint_requires_authentication(self):
        """Test that user stats endpoint requires authentication."""
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_stats_endpoint_returns_correct_data(self):
        """Test that user stats endpoint returns correct data structure."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_logins', response.data)
        self.assertIn('last_login', response.data)
        self.assertIn('weekly_data', response.data)
        self.assertIn('monthly_data', response.data)
        self.assertIn('login_trend', response.data)

        # Verify data types
        self.assertIsInstance(response.data['total_logins'], int)
        self.assertIsInstance(response.data['last_login'], str)
        self.assertIsInstance(response.data['weekly_data'], dict)
        self.assertIsInstance(response.data['monthly_data'], dict)
        self.assertIsInstance(response.data['login_trend'], int)

    def test_login_activity_endpoint_requires_authentication(self):
        """Test that login activity endpoint requires authentication."""
        url = reverse('user:login-activity')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_activity_endpoint_returns_paginated_data(self):
        """Test that login activity endpoint returns paginated data."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-activity')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)

        # Should return all login activities for the user
        self.assertEqual(response.data['count'], 7)  # 5 successful + 2 failed

    def test_admin_dashboard_endpoint_requires_admin_permissions(self):
        """Test that admin dashboard endpoint requires admin permissions."""
        # Regular user should not have access
        self.client.force_authenticate(user=self.user)
        url = reverse('user:admin-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin user should have access
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_dashboard_returns_correct_data(self):
        """Test admin dashboard endpoint returns correct data structure."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-dashboard')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
        self.assertIn('active_users', response.data)
        self.assertIn('total_logins', response.data)
        self.assertIn('login_activity', response.data)
        self.assertIn('user_growth', response.data)

        # Verify data types
        self.assertIsInstance(response.data['total_users'], int)
        self.assertIsInstance(response.data['active_users'], int)
        self.assertIsInstance(response.data['total_logins'], int)
        self.assertIsInstance(response.data['login_activity'], list)
        self.assertIsInstance(response.data['user_growth'], dict)

    def test_login_activity_endpoint_supports_pagination(self):
        """Test that login activity endpoint supports pagination."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-activity')
        response = self.client.get(url, {'page': 1, 'page_size': 3})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['count'], 7)

    def test_user_stats_includes_correct_login_count(self):
        """Test that user stats includes correct login count."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)

        # Should only count successful logins (5)
        self.assertEqual(response.data['total_logins'], 5)

    def test_user_stats_includes_login_trend_calculation(self):
        """Test that user stats includes login trend calculation."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)

        # Login trend should be calculated (could be positive or negative)
        self.assertIsInstance(response.data['login_trend'], int)

    def test_user_stats_last_login_format(self):
        """Test that last_login field uses correct datetime format."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)

        # Verify last_login uses YYYY-MM-DD HH:MM:SS format
        last_login = response.data['last_login']
        self.assertIsInstance(last_login, str)

        # Check format using regex pattern
        pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        error_msg = (
            f"last_login '{last_login}' doesn't match expected format "
            "YYYY-MM-DD HH:MM:SS"
        )  # noqa: E501
        self.assertRegex(last_login, pattern, error_msg)

    def test_user_stats_data_structure(self):
        """Test that user stats returns expected data structure."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)

        # Verify complete response structure
        expected_keys = [
            'total_logins', 'last_login', 'weekly_data',
            'monthly_data', 'login_trend'
        ]
        self.assertEqual(set(response.data.keys()), set(expected_keys))

        # Verify data types
        self.assertIsInstance(response.data['total_logins'], int)
        self.assertIsInstance(response.data['last_login'], str)
        self.assertIsInstance(response.data['weekly_data'], dict)
        self.assertIsInstance(response.data['monthly_data'], dict)
        self.assertIsInstance(response.data['login_trend'], int)

        # Verify weekly_data format (YYYY-WW format like "2025-50")
        for key in response.data['weekly_data'].keys():
            self.assertRegex(
                key, r'^\d{4}-\d{1,2}$',
                f"Weekly data key '{key}' doesn't match YYYY-WW format"
            )

        # Verify monthly_data format (YYYY-MM format like "2025-12")
        for key in response.data['monthly_data'].keys():
            self.assertRegex(
                key, r'^\d{4}-\d{2}$',
                f"Monthly data key '{key}' doesn't match YYYY-MM format"
            )

    def test_user_stats_last_login_accuracy(self):
        """Test that last_login shows the correct actual timestamp."""
        # Clear existing login activities for this user
        LoginActivity.objects.filter(user=self.user).delete()

        # Create a login activity with current timestamp
        login_activity = LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.100',
            user_agent='Test Browser',
            success=True
        )
        # Use the actual timestamp that was set by auto_now_add
        actual_timestamp = login_activity.timestamp

        # Refresh user to get updated stats
        self.user.refresh_from_db()

        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)

        # Verify the last_login matches our actual timestamp
        last_login_str = response.data['last_login']
        from datetime import datetime
        last_login_dt = timezone.make_aware(
            datetime.strptime(last_login_str, '%Y-%m-%d %H:%M:%S')
        )

        # Allow for small time differences due to processing
        time_difference = abs(
            (last_login_dt - actual_timestamp).total_seconds()
        )
        self.assertLessEqual(time_difference, 5)

    def test_user_stats_example_data_format(self):
        """Test that user stats matches the expected example format."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)

        # Verify all expected fields are present with correct types
        self.assertIn('total_logins', response.data)
        self.assertIn('last_login', response.data)
        self.assertIn('weekly_data', response.data)
        self.assertIn('monthly_data', response.data)
        self.assertIn('login_trend', response.data)

        # Verify last_login format specifically
        last_login = response.data['last_login']
        self.assertRegex(last_login, r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')

    def test_admin_dashboard_includes_user_growth_data(self):
        """Test that admin dashboard includes user growth data."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-dashboard')
        response = self.client.get(url)

        # Should include user growth data by month
        self.assertIsInstance(response.data['user_growth'], dict)
        self.assertTrue(len(response.data['user_growth']) > 0)

    # Date filtering tests for USER_STATS endpoint
    def test_user_stats_accepts_date_parameters(self):
        """Test that user stats endpoint accepts start_date and end_date parameters."""  # noqa: E501
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')

        start_date = (timezone.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')

        response = self.client.get(url, {'start_date': start_date, 'end_date': end_date})  # noqa: E501

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_logins', response.data)

    def test_user_stats_date_filtering_works(self):
        """Test that user stats correctly filters data by date range."""
        # Clear existing activities
        LoginActivity.objects.filter(user=self.user).delete()

        # Create activities in specific date ranges
        base_time = timezone.now()

        # Activities within date range (should be counted)
        for i in range(3):
            activity = LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Browser {i+1}',
                success=True
            )
            # Manually set timestamp since auto_now_add ignores the parameter
            activity.timestamp = base_time - timedelta(days=i+1)  # 1-3 days ago  # noqa: E501
            activity.save()

        # Activities outside date range (should not be counted)
        for i in range(2):
            activity = LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.2.{i+1}',
                user_agent=f'Browser {i+1}',
                success=True
            )
            # Manually set timestamp since auto_now_add ignores the parameter
            activity.timestamp = base_time - timedelta(days=i+10)  # 10-11 days ago  # noqa: E501
            activity.save()

        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')

        # Date range: 5 days ago to now
        start_date = (base_time - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = base_time.strftime('%Y-%m-%d')

        response = self.client.get(url, {'start_date': start_date, 'end_date': end_date})  # noqa: E501

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should count only the 3 activities within the date range
        self.assertEqual(response.data['total_logins'], 3)

    def test_user_stats_invalid_date_format_returns_400(self):
        """Test that invalid date format returns 400 error with exact message."""  # noqa: E501
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')

        response = self.client.get(url, {'start_date': 'invalid-date', 'end_date': '2025-12-31'})  # noqa: E501

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid date format. Use YYYY-MM-DD format.'})  # noqa: E501

    def test_user_stats_no_date_parameters_uses_default_behavior(self):
        """Test that without date parameters, endpoint uses default behavior from User model."""  # noqa: E501
        self.client.force_authenticate(user=self.user)
        url = reverse('user:dashboard-stats')

        # Get response without date parameters (should use User model stats)
        response = self.client.get(url)

        # Should return successful response with expected structure
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_logins', response.data)
        self.assertIn('last_login', response.data)
        self.assertIn('weekly_data', response.data)
        self.assertIn('monthly_data', response.data)
        self.assertIn('login_trend', response.data)

        # Should have some login count from setUp activities
        self.assertGreaterEqual(response.data['total_logins'], 0)

    # Date filtering tests for LOGIN_ACTIVITY endpoint
    def test_login_activity_date_filtering_works(self):
        """Test that login activity endpoint correctly filters by date range."""  # noqa: E501
        # Clear existing activities
        LoginActivity.objects.filter(user=self.user).delete()

        base_time = timezone.now()

        # Create activities in different date ranges
        # Within date range
        for i in range(3):
            activity = LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Browser {i+1}',
                success=True
            )
            # Manually set timestamp since auto_now_add ignores the parameter
            activity.timestamp = base_time - timedelta(days=i+1)
            activity.save()

        # Outside date range
        for i in range(2):
            activity = LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.2.{i+1}',
                user_agent=f'Browser {i+1}',
                success=False
            )
            # Manually set timestamp since auto_now_add ignores the parameter
            activity.timestamp = base_time - timedelta(days=i+10)
            activity.save()

        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-activity')

        # Date range: 5 days ago to now
        start_date = (base_time - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = base_time.strftime('%Y-%m-%d')

        response = self.client.get(url, {'start_date': start_date, 'end_date': end_date})  # noqa: E501

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return only 3 activities within the date range
        self.assertEqual(response.data['count'], 3)

    def test_login_activity_invalid_date_format_returns_400(self):
        """Test that invalid date format in login activity returns 400 error with exact message."""  # noqa: E501
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-activity')

        response = self.client.get(url, {'start_date': 'not-a-date', 'end_date': '2025-12-31'})  # noqa: E501

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid date format. Use YYYY-MM-DD format.'})  # noqa: E501

    def test_login_activity_no_date_parameters_returns_all(self):
        """Test that without date parameters, login activity returns all activities."""  # noqa: E501
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-activity')

        # Get total count of activities for this user
        total_activities = LoginActivity.objects.filter(user=self.user).count()

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], total_activities)

    def test_login_activity_date_filtering_with_pagination(self):
        """Test that date filtering works correctly with pagination."""
        # Clear existing activities
        LoginActivity.objects.filter(user=self.user).delete()

        base_time = timezone.now()

        # Create many activities within date range
        for i in range(10):
            activity = LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Browser {i+1}',
                success=True
            )
            # Manually set timestamp since auto_now_add ignores the parameter
            activity.timestamp = base_time - timedelta(days=i+1)
            activity.save()

        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-activity')

        # Date range that includes all activities
        start_date = (base_time - timedelta(days=15)).strftime('%Y-%m-%d')
        end_date = base_time.strftime('%Y-%m-%d')

        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date,
            'page': 1,
            'size': 5
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 10)

    def test_admin_dashboard_me_parameter_shows_current_user_data(self):
        """Test that me=true parameter shows only current admin user's data in dashboard format."""  # noqa: E501
        # Create additional users and login activities to ensure filtering works  # noqa: E501
        other_admin = User.objects.create_superuser(
            username='otheradmin',
            email='otheradmin@example.com',
            password='adminpass123'
        )

        # Create login activities for the other admin
        for i in range(3):
            activity = LoginActivity.objects.create(
                user=other_admin,
                ip_address=f'192.168.3.{i+1}',
                user_agent=f'Other Admin Browser {i+1}',
                success=True
            )
            activity.timestamp = timezone.now() - timedelta(days=i)
            activity.save()

        # Create login activities for the current admin user
        for i in range(2):
            activity = LoginActivity.objects.create(
                user=self.admin_user,
                ip_address=f'192.168.4.{i+1}',
                user_agent=f'Current Admin Browser {i+1}',
                success=True
            )
            activity.timestamp = timezone.now() - timedelta(days=i)
            activity.save()

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-dashboard')

        # Get dashboard with me=true
        response = self.client.get(url, {'me': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should show data for only the current admin user
        # total_users should be 1 (only current admin)
        self.assertEqual(response.data['total_users'], 1)
        self.assertEqual(response.data['active_users'], 1)

        # total_logins should be only current admin's logins (2)
        self.assertEqual(response.data['total_logins'], 2)

        # login_activity should only show current admin's activities
        self.assertIsInstance(response.data['login_activity'], list)
        for activity in response.data['login_activity']:
            self.assertEqual(activity['username'], self.admin_user.username)

    def test_admin_dashboard_me_parameter_takes_precedence_over_role(self):
        """Test that me=true parameter takes precedence over role parameter."""
        # Create additional users (intentionally unused for this test)
        other_admin = User.objects.create_superuser(  # noqa: F841
            username='otheradmin2',
            email='otheradmin2@example.com',
            password='adminpass123'
        )
        regular_user = User.objects.create_user(  # noqa: F841
            username='regularuser2',
            email='regularuser2@example.com',
            password='userpass123'
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-dashboard')

        # Use both me=true and role=regular - me should take precedence
        response = self.client.get(url, {'me': 'true', 'role': 'regular'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should show only current admin user's data, not regular users
        self.assertEqual(response.data['total_users'], 1)
        self.assertEqual(response.data['active_users'], 1)
