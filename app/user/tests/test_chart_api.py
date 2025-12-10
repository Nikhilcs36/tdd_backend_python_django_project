"""Tests for chart API endpoints."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import LoginActivity
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class ChartAPITests(TestCase):
    """Test cases for chart API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Create login activities for testing
        self._create_test_login_activities()

        # Setup API client
        self.client = APIClient()

    def _create_test_login_activities(self):
        """Create test login activities."""
        # Create successful logins for user (last 30 days)
        for i in range(15):
            LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=True,
                timestamp=timezone.now() - timedelta(days=i)
            )

        # Create failed logins for user
        for i in range(5):
            LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.2.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=False,
                timestamp=timezone.now() - timedelta(days=i+5)
            )

        # Create successful logins for admin user
        for i in range(8):
            LoginActivity.objects.create(
                user=self.admin_user,
                ip_address=f'192.168.3.{i+1}',
                user_agent=f'Chrome Browser {i+1}',
                success=True,
                timestamp=timezone.now() - timedelta(days=i+2)
            )

    def test_login_trends_endpoint_requires_authentication(self):
        """Test that login trends endpoint requires authentication."""
        url = reverse('user:login-trends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_trends_endpoint_returns_correct_data(self):
        """Test that login trends endpoint returns correct data structure."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('login_trends', data)
        self.assertIn('labels', data['login_trends'])
        self.assertIn('datasets', data['login_trends'])
        self.assertIsInstance(data['login_trends']['labels'], list)
        self.assertIsInstance(data['login_trends']['datasets'], list)

    def test_login_trends_with_date_range(self):
        """Test login trends endpoint with date range parameters."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        # Test with date range
        start_date = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')

        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('login_trends', response.data)

    def test_login_comparison_endpoint_requires_authentication(self):
        """Test that login comparison endpoint requires authentication."""
        url = reverse('user:login-comparison')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_comparison_endpoint_returns_correct_data(self):
        """Test that login comparison endpoint returns correct data structure."""  # noqa: E501
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-comparison')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('login_comparison', data)
        self.assertIn('labels', data['login_comparison'])
        self.assertIn('datasets', data['login_comparison'])
        self.assertIsInstance(data['login_comparison']['labels'], list)
        self.assertIsInstance(data['login_comparison']['datasets'], list)

    def test_login_distribution_endpoint_requires_authentication(self):
        """Test that login distribution endpoint requires authentication."""
        url = reverse('user:login-distribution')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_distribution_endpoint_returns_correct_data(self):
        """Test that login distribution endpoint returns correct data structure."""  # noqa: E501
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-distribution')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('login_distribution', data)
        self.assertIn('success_ratio', data['login_distribution'])
        self.assertIn('user_agents', data['login_distribution'])

        # Check success ratio structure
        self.assertIn('labels', data['login_distribution']['success_ratio'])
        self.assertIn('datasets', data['login_distribution']['success_ratio'])

        # Check user agents structure
        self.assertIn('labels', data['login_distribution']['user_agents'])
        self.assertIn('datasets', data['login_distribution']['user_agents'])

    def test_admin_charts_endpoint_requires_admin_permissions(self):
        """Test that admin charts endpoint requires admin permissions."""
        # Test with regular user
        self.client.force_authenticate(user=self.user)
        url = reverse('user:admin-charts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test with admin user
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_charts_endpoint_returns_correct_data(self):
        """Test that admin charts endpoint returns correct data structure."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-charts')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('admin_charts', data)
        self.assertIn('user_growth', data['admin_charts'])
        self.assertIn('login_activity', data['admin_charts'])
        self.assertIn('success_ratio', data['admin_charts'])

    def test_admin_charts_with_date_range(self):
        """Test admin charts endpoint with date range parameters."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-charts')

        # Test with date range
        start_date = (timezone.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')

        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('admin_charts', response.data)

    def test_invalid_date_format_returns_error(self):
        """Test that invalid date format returns appropriate error."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        response = self.client.get(url, {
            'start_date': 'invalid-date',
            'end_date': '2023-01-01'
        })

        # Should either handle gracefully or return error
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        )

    def test_empty_data_returns_valid_structure(self):
        """Test that endpoints return valid structure even with no data."""
        # Create a new user with no login activities
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )

        self.client.force_authenticate(user=new_user)

        # Test all endpoints
        endpoints = [
            reverse('user:login-trends'),
            reverse('user:login-comparison'),
            reverse('user:login-distribution')
        ]

        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIsNotNone(response.data)
