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
            LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=True,
                timestamp=timezone.now() - timedelta(days=i)
            )

        # Create some failed logins
        for i in range(2):
            LoginActivity.objects.create(
                user=self.user,
                ip_address=f'192.168.2.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=False,
                timestamp=timezone.now() - timedelta(days=i+10)
            )

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

    def test_admin_dashboard_includes_user_growth_data(self):
        """Test that admin dashboard includes user growth data."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-dashboard')
        response = self.client.get(url)

        # Should include user growth data by month
        self.assertIsInstance(response.data['user_growth'], dict)
        self.assertTrue(len(response.data['user_growth']) > 0)
