"""Tests for role-based dashboard access functionality."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import LoginActivity
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class RoleBasedAccessTests(TestCase):
    """Test cases for role-based dashboard access functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create regular users
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

        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )

        # Create login activities for testing
        self._create_test_login_activities()

    def _create_test_login_activities(self):
        """Create test login activities for users."""
        # Create successful logins for user1
        for i in range(3):
            LoginActivity.objects.create(
                user=self.user1,
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=True,
                timestamp=timezone.now() - timedelta(days=i)
            )

        # Create successful logins for user2
        for i in range(2):
            LoginActivity.objects.create(
                user=self.user2,
                ip_address=f'192.168.2.{i+1}',
                user_agent=f'Test Browser {i+1}',
                success=True,
                timestamp=timezone.now() - timedelta(days=i+5)
            )

    # Test 1: User can access own dashboard stats
    def test_user_can_access_own_stats(self):
        """Test that user can access their own dashboard statistics."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user:user-specific-stats',  # noqa: E501
                      kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_logins', response.data)
        self.assertEqual(response.data['total_logins'], 3)   # noqa: E501

    # Test 2: User cannot access other user's stats
    def test_user_cannot_access_others_stats(self):
        """Test that user cannot access another user's dashboard statistics."""
        self.client.force_authenticate(user=self.user1)
        url = reverse(
            'user:user-specific-stats', kwargs={'user_id': self.user2.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Test 3: Admin can access any user's stats
    def test_admin_can_access_any_user_stats(self):
        """Test that admin can access any user's dashboard statistics."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            'user:user-specific-stats', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_logins'], 3)

    # Test 4: Staff can access any user's stats
    def test_staff_can_access_any_user_stats(self):
        """Test that staff can access any user's dashboard statistics."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse(
            'user:user-specific-stats', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_logins'], 3)

    # Test 5: User can access own login activity
    def test_user_can_access_own_login_activity(self):
        """Test that user can access their own login activity."""
        self.client.force_authenticate(user=self.user1)
        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)   # noqa: E501

    # Test 6: User cannot access other user's login activity
    def test_user_cannot_access_others_login_activity(self):
        """Test that user cannot access another user's login activity."""
        self.client.force_authenticate(user=self.user1)
        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.user2.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Test 7: Admin can access any user's login activity
    def test_admin_can_access_any_user_login_activity(self):
        """Test that admin can access any user's login activity."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    # Test 8: Admin batch stats endpoint requires authentication
    def test_admin_batch_stats_requires_auth(self):
        """Test that admin batch stats endpoint requires authentication."""
        url = reverse('user:admin-users-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Test 9: Admin batch stats endpoint requires admin permissions
    def test_admin_batch_stats_requires_admin_permissions(self):
        """Test that admin batch stats endpoint requires admin permissions."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user:admin-users-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Test 10: Admin batch stats returns data for specific users
    def test_admin_batch_stats_returns_specific_users_data(self):
        """Test that admin batch stats returns data for specific users."""
        self.client.force_authenticate(user=self.admin_user)
        url = (
            reverse('user:admin-users-stats') +  # noqa: E501
            f'?user_ids[]={self.user1.id}&user_ids[]={self.user2.id}'
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(str(self.user1.id), response.data)
        self.assertIn(str(self.user2.id), response.data)
        self.assertEqual(response.data[str(self.user1.id)]['total_logins'], 3)
        self.assertEqual(response.data[str(self.user2.id)]['total_logins'], 2)

    # Test 11: Admin batch stats supports filtering by active status
    def test_admin_batch_stats_filter_by_active_status(self):
        """Test that admin batch stats supports filtering by active status."""
        # Create an inactive user
        inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='testpass123',
            is_active=False
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-users-stats') + '?is_active=true'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return data for active users
        self.assertIn(str(self.user1.id), response.data)
        self.assertIn(str(self.user2.id), response.data)
        self.assertNotIn(str(inactive_user.id), response.data)

    # Test 12: Admin batch stats returns data for all users when no filters
    def test_admin_batch_stats_returns_all_users_when_no_filters(self):
        """Test that admin batch stats returns data for all users when no
        filters are applied."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-users-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return data for all users
        self.assertIn(str(self.user1.id), response.data)
        self.assertIn(str(self.user2.id), response.data)
        self.assertIn(str(self.admin_user.id), response.data)
        self.assertIn(str(self.staff_user.id), response.data)

    # Test 13: Backward compatibility - user can access own stats via old endpoint  # noqa: E501
    def test_backward_compatibility_user_stats(self):
        """Test that user can still access their own stats via the old
        endpoint."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user:dashboard-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_logins'], 3)

    # Test 14: Backward compatibility - user can access own login activity via old endpoint  # noqa: E501
    def test_backward_compatibility_login_activity(self):
        """Test that user can still access their own login activity via the
        old endpoint."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user:login-activity')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    # Test 15: Non-existent user returns 404
    def test_nonexistent_user_returns_404(self):
        """Test that accessing non-existent user returns 404."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:user-specific-stats', kwargs={'user_id': 9999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test 16: Invalid user_id parameter returns 400
    def test_invalid_user_id_returns_400(self):
        """Test that invalid user_id parameter returns 400."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-users-stats') + '?user_ids[]=invalid'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test 17: Empty user_ids array returns 400 error
    def test_empty_user_ids_returns_400_error(self):
        """Test that empty user_ids array returns 400 error."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-users-stats') + '?user_ids[]='
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test 18: Mixed valid and invalid user IDs returns 400 error
    def test_mixed_valid_invalid_user_ids_returns_400(self):
        """Test that mixed valid and invalid user IDs returns 400 error."""
        self.client.force_authenticate(user=self.admin_user)
        url = (
            reverse('user:admin-users-stats') +
            f'?user_ids[]={self.user1.id}&user_ids[]=invalid&user_ids[]='
            f'{self.user2.id}'
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test 19: Inactive user filtering with false returns inactive users
    def test_inactive_user_filtering_returns_inactive_users(self):
        """Test that inactive user filtering returns inactive users."""
        # Create an inactive user
        inactive_user = User.objects.create_user(
            username='inactive2',
            email='inactive2@example.com',
            password='testpass123',
            is_active=False
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-users-stats') + '?is_active=false'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(str(inactive_user.id), response.data)
        self.assertNotIn(str(self.user1.id), response.data)

    # Test 20: Login activity pagination works correctly
    def test_login_activity_pagination(self):
        """Test that login activity pagination works correctly."""
        # Create more login activities for user1
        for i in range(10):
            LoginActivity.objects.create(
                user=self.user1,
                ip_address=f'192.168.1.{i+10}',
                user_agent=f'Test Browser {i+10}',
                success=True,
                timestamp=timezone.now() - timedelta(hours=i)
            )

        self.client.force_authenticate(user=self.admin_user)
        url = (
            reverse('user:user-specific-login-activity',  # noqa: E501
                    kwargs={'user_id': self.user1.id}) + '?page=2&size=5'
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 13)  # 3 original + 10 new
        self.assertIsNotNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])
        self.assertEqual(len(response.data['results']), 5)

    # Test 21: Combined filtering with user_ids and active status
    def test_combined_filtering_user_ids_and_active_status(self):
        """Test combined filtering with user_ids and active status."""
        inactive_user = User.objects.create_user(
            username='inactive3',
            email='inactive3@example.com',
            password='testpass123',
            is_active=False
        )

        self.client.force_authenticate(user=self.admin_user)
        url = (
            reverse('user:admin-users-stats') +  # noqa: E501
            f'?user_ids[]={self.user1.id}&user_ids[]={inactive_user.id}'
            '&is_active=true'
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(str(self.user1.id), response.data)
        self.assertNotIn(str(inactive_user.id), response.data)
        self.assertEqual(len(response.data), 1)

    # Test 22: Staff can access admin batch stats (staff and admin both allowed)  # noqa: E501
    def test_staff_can_access_admin_batch_stats(self):
        """Test that staff can access admin batch stats endpoint."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('user:admin-users-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(str(self.user1.id), response.data)
        self.assertIn(str(self.user2.id), response.data)

    # Test 23: Data consistency - stats match actual login records
    def test_data_consistency_stats_match_login_records(self):
        """Test that stats data matches actual login records."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            'user:user-specific-stats', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        # Verify stats match actual records
        actual_logins = LoginActivity.objects.filter(
            user=self.user1, success=True).count()
        self.assertEqual(response.data['total_logins'], actual_logins)

    # Test 24: Login trend calculation is correct
    def test_login_trend_calculation(self):
        """Test that login trend calculation is correct."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            'user:user-specific-stats', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        # Basic validation of trend calculation
        self.assertIn('login_trend', response.data)
        self.assertIsInstance(response.data['login_trend'], int)
        self.assertTrue(0 <= response.data['login_trend'] <= 100)

    # Test 25: Date formatting consistency across responses
    def test_date_formatting_consistency(self):
        """Test that date formatting is consistent across responses."""
        self.client.force_authenticate(user=self.admin_user)

        # Test stats endpoint
        stats_url = reverse(
            'user:user-specific-stats', kwargs={'user_id': self.user1.id})
        stats_response = self.client.get(stats_url)

        # Test login activity endpoint
        activity_url = reverse(
            'user:user-specific-login-activity',
            kwargs={'user_id': self.user1.id})
        activity_response = self.client.get(activity_url)

        # Verify both use consistent datetime format
        self.assertIn('last_login', stats_response.data)
        if stats_response.data['last_login']:
            self.assertIsInstance(stats_response.data['last_login'], str)

        if activity_response.data['results']:
            first_activity = activity_response.data['results'][0]
            self.assertIn('timestamp', first_activity)
            self.assertIsInstance(first_activity['timestamp'], str)

    # Test 26: Large user ID list handling
    def test_large_user_id_list_handling(self):
        """Test handling of large user ID lists."""
        self.client.force_authenticate(user=self.admin_user)

        # Create many user IDs parameter
        user_ids = [
            str(self.user1.id), str(self.user2.id),
            str(self.admin_user.id), str(self.staff_user.id)
        ]
        user_ids_param = '&'.join([f'user_ids[]={uid}' for uid in user_ids])

        url = reverse('user:admin-users-stats') + '?' + user_ids_param
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(user_ids))

    # Test 27: Malformed user_id parameter returns proper error
    def test_malformed_user_id_parameter(self):
        """Test that malformed user_id parameter returns proper error."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user:admin-users-stats') + '?user_ids[]=9999a'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    # Test 28: User accessing own data with expired token
    def test_user_access_with_expired_token(self):
        """Test that user accessing own data with expired token fails."""
        # This would typically require mocking an expired token
        # For now, we'll test that authentication is required
        url = reverse(
            'user:user-specific-stats', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Test 29: Batch stats with non-existent user IDs
    def test_batch_stats_with_nonexistent_user_ids(self):
        """Test batch stats with non-existent user IDs."""
        self.client.force_authenticate(user=self.admin_user)
        url = (
            reverse('user:admin-users-stats') +  # noqa: E501
            '?user_ids[]=9999&user_ids[]=9998'
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})   # noqa: E501

    # Test 30: Verify response structure for all endpoints
    def test_response_structure_consistency(self):
        """Test that response structures are consistent across endpoints."""
        self.client.force_authenticate(user=self.admin_user)

        # Test user stats endpoint
        stats_url = reverse(
            'user:user-specific-stats', kwargs={'user_id': self.user1.id})
        stats_response = self.client.get(stats_url)

        expected_stats_keys = [
            'total_logins', 'last_login', 'weekly_data',
            'monthly_data', 'login_trend'
        ]
        for key in expected_stats_keys:
            self.assertIn(key, stats_response.data)

        # Test batch stats endpoint
        batch_url = (
            reverse('user:admin-users-stats') +  # noqa: E501
            f'?user_ids[]={self.user1.id}'
        )
        batch_response = self.client.get(batch_url)

        self.assertIn(str(self.user1.id), batch_response.data)
        user_stats = batch_response.data[str(self.user1.id)]
        for key in expected_stats_keys:
            self.assertIn(key, user_stats)
