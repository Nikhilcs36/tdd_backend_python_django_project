"""Tests for auto-staff access after 3 logins and role switching.

TDD approach: These tests are written first (RED phase).
Implementation will follow to make them pass (GREEN phase).
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class AutoStaffAccessModelTests(TestCase):
    """Tests for auto-granting staff access after 3 successful logins."""

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

    def test_new_user_defaults(self):
        """Test that a new user has default values for staff fields."""
        self.assertFalse(self.user.staff_access_granted)
        self.assertEqual(self.user.active_role, 'regular')

    def test_successful_login_count_increments(self):
        """Test that login_count increments on successful login."""
        url = reverse('user:token')
        data = {'email': 'test@example.com', 'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_count, 1)

    def test_no_staff_access_after_1_login(self):
        """Test that staff access is NOT granted after 1 successful login."""
        url = reverse('user:token')
        data = {'email': 'test@example.com', 'password': 'testpass123'}
        self.client.post(url, data, format='json')
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.staff_access_granted)
        self.assertEqual(self.user.active_role, 'regular')

    def test_no_staff_access_after_2_logins(self):
        """Test that staff access is NOT granted after 2 successful logins."""
        url = reverse('user:token')
        data = {'email': 'test@example.com', 'password': 'testpass123'}
        for _ in range(2):
            self.client.post(url, data, format='json')
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_count, 2)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.staff_access_granted)
        self.assertEqual(self.user.active_role, 'regular')

    def test_auto_staff_after_3_logins(self):
        """Test that staff access IS granted after 3 successful logins."""
        url = reverse('user:token')
        data = {'email': 'test@example.com', 'password': 'testpass123'}
        for _ in range(3):
            self.client.post(url, data, format='json')
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_count, 3)
        self.assertTrue(self.user.is_staff)
        self.assertTrue(self.user.staff_access_granted)
        self.assertEqual(self.user.active_role, 'staff')

    def test_staff_grant_only_happens_once(self):
        """Test that auto-staff grant only happens once."""
        url = reverse('user:token')
        data = {'email': 'test@example.com', 'password': 'testpass123'}
        for _ in range(4):
            self.client.post(url, data, format='json')
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_count, 4)
        self.assertTrue(self.user.is_staff)
        self.assertTrue(self.user.staff_access_granted)
        self.assertEqual(self.user.active_role, 'staff')

    def test_failed_logins_dont_count(self):
        """Test that failed login attempts don't count toward threshold."""
        url = reverse('user:token')
        for _ in range(2):
            self.client.post(url, {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }, format='json')
        self.client.post(url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        }, format='json')
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_count, 1)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.staff_access_granted)


class LoginResponseTests(TestCase):
    """Tests for login response fields related to staff access."""

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
        self.url = reverse('user:token')
        self.data = {'email': 'test@example.com', 'password': 'testpass123'}

    def _login(self):
        """Helper to login and get response."""
        return self.client.post(self.url, self.data, format='json')

    def test_login_response_has_logins_remaining(self):
        """Test that login response includes logins_remaining_for_staff."""
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('logins_remaining_for_staff', response.data)
        self.assertEqual(response.data['logins_remaining_for_staff'], 3)

    def test_login_response_countdown_after_2nd_login(self):
        """Test countdown is 2 after 2nd login."""
        self._login()
        response = self._login()
        self.assertEqual(response.data['logins_remaining_for_staff'], 2)

    def test_login_response_countdown_after_3_logins(self):
        """Test countdown is 1 after 3 successful logins."""
        for _ in range(3):
            response = self._login()
        self.assertEqual(response.data['logins_remaining_for_staff'], 1)

    def test_login_response_has_staff_access_granted(self):
        """Test that login response includes staff_access_granted field."""
        response = self._login()
        self.assertIn('staff_access_granted', response.data)
        self.assertFalse(response.data['staff_access_granted'])

    def test_login_response_has_active_role(self):
        """Test that login response includes active_role field."""
        response = self._login()
        self.assertIn('active_role', response.data)
        self.assertEqual(response.data['active_role'], 'regular')

    def test_login_response_after_staff_granted(self):
        """Test login response fields after staff access is granted."""
        for _ in range(3):
            self._login()
        response = self._login()
        self.assertTrue(response.data['staff_access_granted'])
        self.assertEqual(response.data['logins_remaining_for_staff'], 0)
        self.assertEqual(response.data['active_role'], 'staff')


class SuperuserRoleTests(TestCase):
    """Tests for superuser role handling and temporary switch."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.superuser.email_verified = True
        self.superuser.save()
        self.url = reverse('user:token')
        self.data = {'email': 'admin@example.com', 'password': 'adminpass123'}

    def _login(self):
        """Helper to login and get response."""
        return self.client.post(self.url, self.data, format='json')

    def test_superuser_active_role_is_superuser(self):
        """Test that superuser's active_role is 'superuser' on login."""
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_role'], 'superuser')

    def test_superuser_staff_access_granted_on_login(self):
        """Test that superuser has staff_access_granted on login."""
        response = self._login()
        self.assertTrue(response.data['staff_access_granted'])

    def test_superuser_logins_remaining_is_zero(self):
        """Test that superuser's logins_remaining is 0."""
        response = self._login()
        self.assertEqual(response.data['logins_remaining_for_staff'], 0)

    def test_superuser_can_switch_to_regular(self):
        """Test that superuser can switch to regular role temporarily."""
        self._login()
        self.superuser.refresh_from_db()

        self.client.force_authenticate(user=self.superuser)
        url = reverse('user:switch-role')
        response = self.client.post(
            url, {'role': 'regular'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_role'], 'regular')

        self.superuser.refresh_from_db()
        self.assertEqual(self.superuser.active_role, 'regular')

    def test_superuser_can_switch_to_staff(self):
        """Test that superuser can switch to staff role temporarily."""
        self._login()
        self.superuser.refresh_from_db()

        self.client.force_authenticate(user=self.superuser)
        url = reverse('user:switch-role')
        response = self.client.post(
            url, {'role': 'staff'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_role'], 'staff')

    def test_superuser_can_switch_back_to_superuser(self):
        """Test that superuser can switch back to superuser role."""
        self._login()
        self.superuser.refresh_from_db()

        self.client.force_authenticate(user=self.superuser)
        url = reverse('user:switch-role')
        self.client.post(url, {'role': 'regular'}, format='json')

        response = self.client.post(
            url, {'role': 'superuser'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_role'], 'superuser')

    def test_superuser_role_resets_on_relogin(self):
        """Test that superuser active_role resets to 'superuser'
        on every login."""
        self._login()
        self.superuser.refresh_from_db()

        self.client.force_authenticate(user=self.superuser)
        url = reverse('user:switch-role')
        self.client.post(url, {'role': 'regular'}, format='json')

        self.superuser.refresh_from_db()
        self.assertEqual(self.superuser.active_role, 'regular')

        response = self._login()
        self.assertEqual(response.data['active_role'], 'superuser')

        self.superuser.refresh_from_db()
        self.assertEqual(self.superuser.active_role, 'superuser')


class SwitchRoleEndpointTests(TestCase):
    """Tests for the role switch endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpass123'
        )
        self.regular_user.email_verified = True
        self.regular_user.save()

        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123'
        )
        self.staff_user.email_verified = True
        self.staff_user.is_staff = True
        self.staff_user.staff_access_granted = True
        self.staff_user.active_role = 'staff'
        self.staff_user.save()

        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.superuser.email_verified = True
        self.superuser.save()

        self.url = reverse('user:switch-role')

    def test_unauthenticated_user_cannot_switch_role(self):
        """Test that unauthenticated user gets 401."""
        response = self.client.post(
            self.url, {'role': 'regular'}, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_switch_role(self):
        """Test that regular user (no staff access) cannot switch."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(
            self.url, {'role': 'staff'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_can_switch_to_regular(self):
        """Test that staff user can switch to regular role."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            self.url, {'role': 'regular'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_role'], 'regular')

    def test_staff_user_can_switch_to_staff(self):
        """Test that staff user can switch back to staff role."""
        self.client.force_authenticate(user=self.staff_user)
        self.client.post(
            self.url, {'role': 'regular'}, format='json')
        response = self.client.post(
            self.url, {'role': 'staff'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_role'], 'staff')

    def test_invalid_role_returns_400(self):
        """Test that invalid role value returns 400."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            self.url, {'role': 'invalid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_role_switch_persists_across_logins(self):
        """Test that staff user role switch persists after logout/login."""
        url = reverse('user:token')
        data = {'email': 'staff@example.com', 'password': 'staffpass123'}

        # Login and switch to regular
        self.client.post(url, data, format='json')
        self.client.force_authenticate(user=self.staff_user)
        switch_url = reverse('user:switch-role')
        self.client.post(
            switch_url, {'role': 'regular'}, format='json')

        # Re-login
        self.client.post(url, data, format='json')
        self.staff_user.refresh_from_db()
        self.assertEqual(self.staff_user.active_role, 'regular')

    def test_regular_user_without_staff_access_gets_403(self):
        """Test that regular user with login_count < 3 gets 403."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(
            self.url, {'role': 'staff'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)


class RoleBasedAdminAccessTests(TestCase):
    """Tests for admin endpoint access after role switch."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Staff user who has been auto-activated
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123'
        )
        self.staff_user.email_verified = True
        self.staff_user.is_staff = True
        self.staff_user.staff_access_granted = True
        self.staff_user.active_role = 'staff'
        self.staff_user.save()

        # Superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.superuser.email_verified = True
        self.superuser.save()

        # Admin dashboard endpoint URL
        self.admin_url = reverse('user:admin-dashboard')

    def test_staff_with_staff_role_can_access_admin(self):
        """Test that staff user with active_role='staff' can access."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_with_regular_role_cannot_access_admin(self):
        """Test that staff user with active_role='regular' gets 403."""
        self.client.force_authenticate(user=self.staff_user)
        # Switch to regular role
        self.staff_user.active_role = 'regular'
        self.staff_user.save()
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_with_superuser_role_can_access_admin(self):
        """Test that superuser with active_role='superuser' can access."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superuser_with_regular_role_cannot_access_admin(self):
        """Test that superuser with active_role='regular' gets 403."""
        self.client.force_authenticate(user=self.superuser)
        self.superuser.active_role = 'regular'
        self.superuser.save()
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_with_staff_role_can_access_admin(self):
        """Test that superuser with active_role='staff' can access."""
        self.client.force_authenticate(user=self.superuser)
        self.superuser.active_role = 'staff'
        self.superuser.save()
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
