"""Tests for login activity pagination with role-based access."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import LoginActivity
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class LoginActivityPaginationTests(TestCase):
    """Test cases for login activity pagination edge cases."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123'
        )

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123'
        )

    def _create_login_activities(self, user, count):
        """
        Create login activities for a user with staggered timestamps
        so all records are unique and within the same date range.
        """
        base_time = timezone.now()
        for i in range(count):
            activity = LoginActivity.objects.create(
                user=user,
                ip_address=f'192.168.1.{i + 1}',
                user_agent=f'Test Browser {i + 1}',
                success=True
            )
            activity.timestamp = base_time - timedelta(minutes=i)
            activity.save()

    def _create_login_activities_spread(self, user, count, max_days_back=30):
        """
        Create login activities spread over a date range.
        """
        base_time = timezone.now()
        for i in range(count):
            activity = LoginActivity.objects.create(
                user=user,
                ip_address=f'192.168.1.{i + 1}',
                user_agent=f'Test Browser {i + 1}',
                success=True
            )
            days_back = (i / count) * max_days_back
            activity.timestamp = base_time - timedelta(days=days_back,
                                                       minutes=i)
            activity.save()

    def test_regular_user_own_login_activity_page_2_with_date_filter(self):
        """
        Test that a regular user can access page 2 of their own login
        activity with date filters. (Exact scenario from reported bug)
        """
        # Create 150 login activities spread across last 30 days
        self._create_login_activities_spread(
            self.regular_user, 150, max_days_back=30
        )

        self.client.force_authenticate(user=self.regular_user)

        start_date = (timezone.now() - timedelta(days=31)).strftime(
            '%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')

        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.regular_user.id}
        )

        # Request page 1 (mimics frontend's initial load)
        response_page1 = self.client.get(url, {
            'page': 1,
            'size': 100,
            'start_date': start_date,
            'end_date': end_date,
        })

        self.assertEqual(response_page1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_page1.data['results']), 100)
        self.assertIsNotNone(response_page1.data['next'])

        # Request page 2 (mimics frontend's load more)
        response_page2 = self.client.get(url, {
            'page': 2,
            'size': 100,
            'start_date': start_date,
            'end_date': end_date,
        })

        # Should return 200, not 404!
        self.assertEqual(response_page2.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response_page2.data['previous'])
        self.assertEqual(len(response_page2.data['results']), 50)

    def test_regular_user_own_login_activity_page_2_no_date_filter(self):
        """
        Test that a regular user can access page 2 of their own login
        activity WITHOUT date filters.
        """
        self._create_login_activities(self.regular_user, 150)

        self.client.force_authenticate(user=self.regular_user)

        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.regular_user.id}
        )

        response = self.client.get(url, {
            'page': 2,
            'size': 100,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 50)
        self.assertEqual(response.data['count'], 150)

    def test_admin_user_other_user_login_activity_page_2(self):
        """
        Test that an admin can access page 2 of another user's login
        activity with date filters.
        """
        self._create_login_activities_spread(
            self.regular_user, 150, max_days_back=30
        )

        self.client.force_authenticate(user=self.admin_user)

        start_date = (timezone.now() - timedelta(days=31)).strftime(
            '%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')

        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.regular_user.id}
        )

        # Page 1
        response_page1 = self.client.get(url, {
            'page': 1,
            'size': 100,
            'start_date': start_date,
            'end_date': end_date,
        })
        self.assertEqual(response_page1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_page1.data['results']), 100)

        # Page 2
        response_page2 = self.client.get(url, {
            'page': 2,
            'size': 100,
            'start_date': start_date,
            'end_date': end_date,
        })
        self.assertEqual(response_page2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_page2.data['results']), 50)

    def test_regular_user_cannot_access_page_2_of_other_user(self):
        """
        Test that a regular user gets 403 when trying to access another
        user's login activity with pagination.
        """
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self._create_login_activities(other_user, 150)

        self.client.force_authenticate(user=self.regular_user)

        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': other_user.id}
        )

        response = self.client.get(url, {
            'page': 2,
            'size': 100,
        })

        # Should be 403 forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_page_beyond_range_returns_last_page(self):
        """
        Test that requesting a page beyond available data returns
        the last page (not 404).
        """
        self._create_login_activities(self.regular_user, 50)

        self.client.force_authenticate(user=self.regular_user)

        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.regular_user.id}
        )

        # Request page 99 (way beyond available data - only 50 records)
        response = self.client.get(url, {
            'page': 99,
            'size': 100,
        })

        # Should return 200 with the last page (page 1 with 50 items)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 50)
        self.assertEqual(len(response.data['results']), 50)

    def test_regular_user_page_1_with_default_size(self):
        """
        Test that a regular user accessing their own login activity
        with default pagination works correctly.
        """
        self._create_login_activities(self.regular_user, 50)

        self.client.force_authenticate(user=self.regular_user)

        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.regular_user.id}
        )

        response = self.client.get(url, {'page': 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 50)
        self.assertEqual(len(response.data['results']), 50)
        self.assertIsNone(response.data['next'])

    def test_regular_user_page_2_when_exactly_one_page(self):
        """
        Test that requesting page 2 when there are exactly 100
        records (one full page) returns that page (not 404).
        """
        self._create_login_activities(self.regular_user, 100)

        self.client.force_authenticate(user=self.regular_user)

        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.regular_user.id}
        )

        # Page 1 should have 100 items
        response_page1 = self.client.get(url, {
            'page': 1,
            'size': 100,
        })
        self.assertEqual(response_page1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_page1.data['results']), 100)
        self.assertIsNone(response_page1.data['next'])

        # Page 2 should return last page (page 1) not 404
        response_page2 = self.client.get(url, {
            'page': 2,
            'size': 100,
        })
        self.assertEqual(response_page2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_page2.data['count'], 100)
        # Returns last available page (page 1 with 100 items)
        self.assertEqual(len(response_page2.data['results']), 100)
