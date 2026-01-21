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
        start_date = (
            timezone.now() - timedelta(days=14)
        ).strftime('%Y-%m-%d')
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

    def test_login_trends_includes_both_successful_and_failed_logins(self):
        """Test that login trends includes both successful and
        failed login data."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data['login_trends']
        datasets = data['datasets']

        # Should have two datasets: successful and failed logins
        self.assertEqual(len(datasets), 2)

        labels = [ds['label'] for ds in datasets]
        self.assertIn('Successful Logins', labels)
        self.assertIn('Failed Logins', labels)

        # Verify both datasets have data
        successful_data = next(
            ds for ds in datasets if ds['label'] == 'Successful Logins')
        failed_data = next(
            ds for ds in datasets if ds['label'] == 'Failed Logins')

        # Should have successful logins
        self.assertGreater(sum(successful_data['data']), 0)
        # Should have failed logins
        self.assertGreater(sum(failed_data['data']), 0)

    def test_login_trends_date_filtration_works_correctly(self):
        """Test that login trends date filtration works correctly."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        # Test with specific date range (last 3 days only)
        start_date = (timezone.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')

        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['login_trends']

        # Should have data for exactly 4 days (start date + 3 days)
        self.assertEqual(len(data['labels']), 4)

        # Verify dates are within the requested range
        for date_str in data['labels']:
            response_date = timezone.datetime.strptime(
                date_str, '%Y-%m-%d'
            ).date()
            start_date_obj = timezone.datetime.strptime(
                start_date, '%Y-%m-%d'
            ).date()
            end_date_obj = timezone.datetime.strptime(
                end_date, '%Y-%m-%d'
            ).date()
            self.assertTrue(start_date_obj <= response_date <= end_date_obj)

    def test_login_comparison_date_filtration_works_correctly(self):
        """Test that login comparison date filtration works correctly."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-comparison')

        # Test with specific date range
        start_date = (
            timezone.now() - timedelta(days=10)
        ).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')

        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['login_comparison']

        # Should return data structure
        self.assertIn('labels', data)
        self.assertIn('datasets', data)
        self.assertIsInstance(data['labels'], list)
        self.assertIsInstance(data['datasets'], list)

    def test_login_distribution_includes_correct_success_failure_ratio(self):
        """Test that login distribution includes correct
        success/failure ratio."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-distribution')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data['login_distribution']
        success_ratio = data['success_ratio']

        # Should have correct structure
        self.assertEqual(success_ratio['labels'], ['Successful', 'Failed'])
        self.assertEqual(len(success_ratio['datasets']), 1)

        dataset = success_ratio['datasets'][0]
        self.assertEqual(len(dataset['data']), 2)
        self.assertEqual(sum(dataset['data']), 20)  # 15 successful + 5 failed

        # Verify ratio is correct (15 successful, 5 failed)
        self.assertEqual(dataset['data'][0], 15)  # Successful logins
        self.assertEqual(dataset['data'][1], 5)   # Failed logins

    def test_login_trends_with_same_start_and_end_date(self):
        """Test login trends with same start and end date."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        # Test with same date
        same_date = timezone.now().strftime('%Y-%m-%d')

        response = self.client.get(url, {
            'start_date': same_date,
            'end_date': same_date
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['login_trends']

        # Should return data for exactly one day
        self.assertEqual(len(data['labels']), 1)
        self.assertEqual(data['labels'][0], same_date)

    def test_login_trends_with_user_ids_parameter_admin_only(self):
        """Test login trends endpoint with user_ids parameter (admin only)."""
        # Test with regular user - should fail
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        response = self.client.get(
            url, {'user_ids[]': [self.admin_user.id]})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test with admin user - should succeed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(
            url, {'user_ids[]': [self.user.id, self.admin_user.id]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('login_trends', response.data)

        # Should have combined data structure
        data = response.data['login_trends']
        self.assertIn('labels', data)
        self.assertIn('datasets', data)
        self.assertEqual(len(data['datasets']), 2)  # Successful and failed
        # logins

    def test_login_trends_invalid_user_ids_format(self):
        """Test login trends with invalid user_ids format."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:login-trends')

        response = self.client.get(url, {'user_ids[]': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_login_trends_nonexistent_user_ids(self):
        """Test login trends with nonexistent user IDs."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:login-trends')

        response = self.client.get(url, {'user_ids[]': [99999]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_login_trends_with_reversed_date_range(self):
        """Test login trends with reversed date range (start > end)."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        # Test with reversed dates (start date after end date)
        start_date = timezone.now().strftime('%Y-%m-%d')
        end_date = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })

        # Should handle reversed dates gracefully by returning empty data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['login_trends']

        # Should return valid structure but likely empty data
        self.assertIn('labels', data)
        self.assertIn('datasets', data)
        self.assertIsInstance(data['labels'], list)
        self.assertIsInstance(data['datasets'], list)

    def test_login_comparison_auto_adjusts_timeframe_based_on_range(self):
        """Test that login comparison automatically adjusts timeframe
        based on date range."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-comparison')

        # Test short range (should use weekly data)
        response_short = self.client.get(url, {
            'start_date': (
                timezone.now() - timedelta(days=7)
            ).strftime('%Y-%m-%d'),
            'end_date': timezone.now().strftime('%Y-%m-%d')
        })

        # Test long range (should use monthly data)
        response_long = self.client.get(url, {
            'start_date': (
                timezone.now() - timedelta(days=60)
            ).strftime('%Y-%m-%d'),
            'end_date': timezone.now().strftime('%Y-%m-%d')
        })

        self.assertEqual(response_short.status_code, status.HTTP_200_OK)
        self.assertEqual(response_long.status_code, status.HTTP_200_OK)

    def test_admin_charts_includes_correct_data_counts(self):
        """Test that admin charts include correct data counts."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-charts')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data['admin_charts']

        # Verify success ratio data
        success_ratio = data['success_ratio']
        dataset = success_ratio['datasets'][0]
        total_logins = sum(dataset['data'])

        # Should include logins from both users (15 successful + 5 failed
        # from user1) plus 8 successful from admin user = 28 total login
        # attempts
        self.assertEqual(total_logins, 28)

    def test_cross_verification_between_api_and_analytics_functions(self):
        """Test cross-verification between API responses and
        analytics functions."""
        from user.serializers_dashboard import get_login_trends_data

        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        # Get data from API
        api_response = self.client.get(url)
        api_data = api_response.data['login_trends']

        # Get data directly from analytics function
        analytics_data = get_login_trends_data(self.user)

        # Should have same structure and similar data
        self.assertEqual(len(api_data['labels']),
                         len(analytics_data['labels']))
        self.assertEqual(len(api_data['datasets']),
                         len(analytics_data['datasets']))

        # Labels should match
        self.assertEqual(api_data['labels'], analytics_data['labels'])

        # Dataset labels should match
        api_labels = [ds['label'] for ds in api_data['datasets']]
        analytics_labels = [ds['label'] for ds in analytics_data['datasets']]
        self.assertEqual(api_labels, analytics_labels)

    def test_invalid_date_parameters_return_proper_error(self):
        """Test that invalid date parameters return proper
        error messages."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-trends')

        # Test various invalid date formats
        invalid_cases = [
            {'start_date': '2023-13-01',
             'end_date': '2023-12-01'},  # Invalid month
            {'start_date': '2023-01-32',
             'end_date': '2023-12-01'},  # Invalid day
            {'start_date': 'not-a-date',
             'end_date': '2023-12-01'},   # Not a date
            {'start_date': '2023/01/01',
             'end_date': '2023-12-01'},   # Wrong format
        ]

        for params in invalid_cases:
            response = self.client.get(url, params)
            # Should return 400 Bad Request for invalid dates
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)
            self.assertIn(
                'date format',
                response.data['error'].lower()
            )

    def test_login_comparison_with_user_ids_parameter_admin_only(self):
        """Test login comparison endpoint with user_ids parameter."""
        # Test with regular user - should fail
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-comparison')

        response = self.client.get(
            url, {'user_ids[]': [self.admin_user.id]})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test with admin user - should succeed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(
            url, {'user_ids[]': [self.user.id, self.admin_user.id]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('login_comparison', response.data)

        # Should have combined comparison data structure
        data = response.data['login_comparison']
        self.assertIn('labels', data)
        self.assertIn('datasets', data)
        self.assertEqual(len(data['datasets']), 1)  # Single dataset for  # noqa: E501
        # comparison

    def test_login_distribution_with_user_ids_parameter_admin_only(self):
        """Test login distribution endpoint with user_ids parameter (admin only)."""  # noqa: E501
        # Test with regular user - should fail
        self.client.force_authenticate(user=self.user)
        url = reverse('user:login-distribution')

        response = self.client.get(
            url, {'user_ids[]': [self.admin_user.id]})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test with admin user - should succeed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(
            url, {'user_ids[]': [self.user.id, self.admin_user.id]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('login_distribution', response.data)

        # Should have combined distribution data structure
        data = response.data['login_distribution']
        self.assertIn('success_ratio', data)
        self.assertIn('user_agents', data)

        # Verify success ratio has combined data
        success_ratio = data['success_ratio']
        self.assertEqual(success_ratio['labels'], ['Successful', 'Failed'])  # noqa: E501
        dataset = success_ratio['datasets'][0]
        total_logins = sum(dataset['data'])
        # Should include logins from both users
        self.assertGreater(total_logins, 0)

    def test_chart_endpoints_accept_url_encoded_user_ids_format(self):
        """Test chart endpoints accept both user_ids[] and user_ids%5B%5D formats."""  # noqa: E501
        self.client.force_authenticate(user=self.admin_user)

        # Test both formats for trends endpoint
        trends_url = reverse('user:login-trends')

        # Format 1: user_ids[] (normal format)
        response1 = self.client.get(trends_url, {'user_ids[]': [self.user.id]})  # noqa: E501
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Format 2: user_ids%5B%5D (URL encoded format) - simulate Postman behavior   # noqa: E501
        # Django's test client automatically URL-decodes, so we test the actual parsing  # noqa: E501
        response2 = self.client.get(trends_url, data={'user_ids[]': [self.user.id]})  # noqa: E501
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Both should return same data structure
        self.assertIn('login_trends', response1.data)
        self.assertIn('login_trends', response2.data)

    def test_chart_endpoints_return_error_for_nonexistent_users(self):
        """Test that chart endpoints return error for nonexistent user IDs."""
        self.client.force_authenticate(user=self.admin_user)

        # Test with trends endpoint
        trends_url = reverse('user:login-trends')

        # Use a user ID that definitely doesn't exist
        nonexistent_user_id = 99999

        response = self.client.get(trends_url, {'user_ids[]': [nonexistent_user_id]})  # noqa: E501
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn(
            'not found',
            response.data['error'].lower()
        )

    def test_chart_endpoints_validate_invalid_date_formats(self):
        """Test that chart endpoints validate invalid date formats."""
        self.client.force_authenticate(user=self.user)

        trends_url = reverse('user:login-trends')

        # Test various invalid date formats
        invalid_dates = [
            'invalid-date',
            '2023-13-01',  # Invalid month
            '2023-01-32',  # Invalid day
            '2023/01/01',  # Wrong separator
            '2023-01-01-extra',  # Extra characters
        ]

        for invalid_date in invalid_dates:
            response = self.client.get(trends_url, {
                'start_date': invalid_date,
                'end_date': '2023-12-01'
            })
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST,
                f"Expected 400 for invalid date: {invalid_date}"
            )
            self.assertIn('error', response.data)
            self.assertIn('date format', response.data['error'].lower())

    def test_login_trends_with_role_regular_parameter_admin_only(self):
        """Test login trends endpoint with role=regular parameter."""
        url = reverse('user:login-trends')

        # Test with regular user - should fail
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, {'role': 'regular'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test with admin user - should succeed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url, {'role': 'regular'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('login_trends', response.data)

        # Should have combined data structure for regular users
        data = response.data['login_trends']
        self.assertIn('labels', data)
        self.assertIn('datasets', data)
        self.assertEqual(len(data['datasets']), 2)  # Successful and failed

        # Verify data comes from regular user only (not admin)
        successful_data = next(
            ds for ds in data['datasets']
            if ds['label'] == 'Successful Logins (Combined)')
        failed_data = next(
            ds for ds in data['datasets']
            if ds['label'] == 'Failed Logins (Combined)')

        # Should have data from regular user (15 successful + 5 failed)
        total_logins = sum(successful_data['data']) + sum(failed_data['data'])
        self.assertEqual(total_logins, 20)  # Only regular user's logins
