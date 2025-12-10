"""Tests for chart analytics functions."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from core.models import LoginActivity
from user.serializers_dashboard import (
    get_login_trends_data,
    get_login_comparison_data,
    get_login_distribution_data,
    get_admin_chart_data
)

User = get_user_model()


class ChartAnalyticsTests(TestCase):
    """Test cases for chart analytics functions."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Create login activities for testing
        self._create_test_login_activities()

    def _create_test_login_activities(self):
        """Create test login activities."""
        # Create successful logins for user1 (last 30 days)
        for i in range(15):
            LoginActivity.objects.create(
                user=self.user1,
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=True,
                timestamp=timezone.now() - timedelta(days=i)
            )

        # Create failed logins for user1
        for i in range(5):
            LoginActivity.objects.create(
                user=self.user1,
                ip_address=f'192.168.2.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=False,
                timestamp=timezone.now() - timedelta(days=i+5)
            )

        # Create successful logins for user2
        for i in range(8):
            LoginActivity.objects.create(
                user=self.user2,
                ip_address=f'192.168.3.{i+1}',
                user_agent=f'Chrome Browser {i+1}',
                success=True,
                timestamp=timezone.now() - timedelta(days=i+2)
            )

    def test_get_login_trends_data_returns_correct_structure(self):
        """Test that get_login_trends_data returns correct structure."""
        result = get_login_trends_data(self.user1)

        self.assertIn('labels', result)
        self.assertIn('datasets', result)
        self.assertIsInstance(result['labels'], list)
        self.assertIsInstance(result['datasets'], list)
        self.assertTrue(len(result['datasets']) > 0)

        # Check dataset structure
        dataset = result['datasets'][0]
        self.assertIn('label', dataset)
        self.assertIn('data', dataset)
        self.assertIn('borderColor', dataset)
        self.assertIsInstance(dataset['data'], list)

    def test_get_login_trends_data_with_date_range(self):
        """Test get_login_trends_data with custom date range."""
        start_date = timezone.now() - timedelta(days=7)
        end_date = timezone.now()

        result = get_login_trends_data(
            self.user1,
            start_date=start_date,
            end_date=end_date
        )

        self.assertIsInstance(result, dict)
        self.assertIn('labels', result)

    def test_get_login_comparison_data_returns_correct_structure(self):
        """Test that get_login_comparison_data returns correct structure."""
        result = get_login_comparison_data(self.user1)

        self.assertIn('labels', result)
        self.assertIn('datasets', result)
        self.assertIsInstance(result['labels'], list)
        self.assertIsInstance(result['datasets'], list)
        self.assertTrue(len(result['datasets']) > 0)

    def test_get_login_distribution_data_returns_correct_structure(self):
        """Test that get_login_distribution_data returns correct structure."""
        result = get_login_distribution_data(self.user1)

        self.assertIn('success_ratio', result)
        self.assertIn('user_agents', result)

        # Check success ratio structure
        self.assertIn('labels', result['success_ratio'])
        self.assertIn('datasets', result['success_ratio'])
        self.assertIsInstance(result['success_ratio']['labels'], list)
        self.assertIsInstance(result['success_ratio']['datasets'], list)

        # Check user agents structure
        self.assertIn('labels', result['user_agents'])
        self.assertIn('datasets', result['user_agents'])
        self.assertIsInstance(result['user_agents']['labels'], list)
        self.assertIsInstance(result['user_agents']['datasets'], list)

        # For pie charts, should have backgroundColor
        dataset = result['success_ratio']['datasets'][0]
        self.assertIn('backgroundColor', dataset)

    def test_get_admin_chart_data_returns_correct_structure(self):
        """Test that get_admin_chart_data returns correct structure."""
        result = get_admin_chart_data()

        self.assertIn('user_growth', result)
        self.assertIn('login_activity', result)
        self.assertIn('success_ratio', result)

        # Check each chart data structure
        self.assertIn('labels', result['user_growth'])
        self.assertIn('datasets', result['user_growth'])

    def test_get_login_trends_data_includes_success_and_failed_data(self):
        """Test that login trends includes both successful and failed data."""
        result = get_login_trends_data(self.user1)

        # Should have at least two datasets (successful and failed)
        self.assertTrue(len(result['datasets']) >= 2)

        labels = [ds['label'] for ds in result['datasets']]
        self.assertIn('Successful Logins', labels)
        self.assertIn('Failed Logins', labels)

    def test_get_login_distribution_data_includes_correct_ratios(self):
        """Test that distribution data includes correct success/failure ratios."""  # noqa: E501
        result = get_login_distribution_data(self.user1)

        dataset = result['success_ratio']['datasets'][0]
        total_logins = sum(dataset['data'])

        # Should have 2 data points (successful and failed)
        self.assertEqual(len(dataset['data']), 2)
        self.assertEqual(total_logins, 20)  # 15 successful + 5 failed

    def test_empty_data_returns_valid_structure(self):
        """Test that functions return valid structure even with empty data."""
        # Create user with no login activities
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )

        result = get_login_trends_data(new_user)
        self.assertIn('labels', result)
        self.assertIn('datasets', result)

        # Should still have datasets but with zero data
        self.assertTrue(len(result['datasets']) > 0)
        for dataset in result['datasets']:
            self.assertEqual(sum(dataset['data']), 0)

    def test_date_range_filtering_works_correctly(self):
        """Test that date range filtering works correctly."""
        # Get data for last 7 days only (inclusive of both start and end dates)
        start_date = timezone.now() - timedelta(days=7)
        end_date = timezone.now()

        result = get_login_trends_data(
            self.user1,
            start_date=start_date,
            end_date=end_date
        )

        # Should have data for the specified range
        self.assertIsInstance(result, dict)
        # The range includes both start and end dates, so it should be 8 days total  # noqa: E501
        # (7 days ago, 6 days ago, ..., today = 8 days)
        self.assertEqual(len(result['labels']), 8)
        self.assertGreater(len(result['labels']), 0)
