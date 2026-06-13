from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib import admin
from ..models import User


class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123'
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            name='Test User'
        )
        # Get the registered admin class for reuse
        self.user_admin = admin.site._registry[User]

    def test_users_listed(self):
        """Test that users are listed on the user page"""
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.email)
        self.assertContains(res, self.user.username)

    def test_user_change_page(self):
        """Test that the user edit page works"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_user_change_page_contains_fields(self):
        """Test that the user edit page contains all expected fields"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        # Check that the response contains all expected fields
        # These should be present as field names in the form
        self.assertContains(res, 'email')
        self.assertContains(res, 'password')
        self.assertContains(res, 'image')
        self.assertContains(res, 'username')

        # Also check for proper field labels (capitalized)
        self.assertContains(res, 'Email')
        self.assertContains(res, 'Password')
        self.assertContains(res, 'Image')
        self.assertContains(res, 'Username')

        # Name field is intentionally removed from admin UI
        self.assertNotContains(res, 'Name')

    def test_create_user_page(self):
        """Test that the create user page works"""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page_contains_username(self):
        """Test that the create user page contains username field"""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertContains(res, 'username')
        self.assertContains(res, 'Username')

    def test_admin_fieldsets_contain_image_and_username(self):
        """Test that admin fieldset includes image not name"""
        # This test verifies that the admin configuration has expected fields

        # Get the registered admin class
        user_admin = admin.site._registry[User]

        # Check that image and username are in the first fieldset
        first_fieldset_fields = user_admin.fieldsets[0][1]['fields']
        self.assertIn('image', first_fieldset_fields)
        self.assertIn('username', first_fieldset_fields)
        # Name field should NOT be in the fieldset anymore
        self.assertNotIn('name', first_fieldset_fields)

        # Check that name is NOT in list_display anymore
        self.assertNotIn('name', user_admin.list_display)

    def test_username_in_list_display(self):
        """Test that username is in list_display"""
        self.assertIn('username', self.user_admin.list_display)

    def test_username_in_search_fields(self):
        """Test that username is in search_fields"""
        self.assertIn('username', self.user_admin.search_fields)

    def test_username_in_add_fieldsets(self):
        """Test that username is in add_fieldsets"""
        add_fields = self.user_admin.add_fieldsets[0][1]['fields']
        self.assertIn('username', add_fields)

    def test_add_fieldsets_uses_correct_password_field_name(self):
        """Test that add_fieldsets uses 'password1' not 'password'"""
        add_fields = self.user_admin.add_fieldsets[0][1]['fields']
        self.assertIn('password1', add_fields)
        self.assertNotIn('password', add_fields)

    @patch('core.admin.send_verification_email')
    def test_create_user_via_admin_form(self, mock_send_email):
        """Test that a user can be created successfully via the admin form"""
        url = reverse('admin:core_user_add')
        data = {
            'username': 'newadminuser',
            'email': 'newadmin@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        res = self.client.post(url, data, follow=True)
        self.assertEqual(res.status_code, 200)

        # Verify the user was actually created
        user_exists = get_user_model().objects.filter(
            username='newadminuser'
        ).exists()
        self.assertTrue(user_exists)

    def test_staff_can_view_user_change_page(self):
        """Test that staff can view the user change page (read-only)."""
        staff_user = get_user_model().objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password123',
            is_staff=True
        )
        self.client.force_login(staff_user)
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        # Staff should see the form but fields should be readonly
        self.assertContains(res, 'email')

    def test_staff_can_view_user_list(self):
        """Test that staff can view the user list in admin."""
        staff_user = get_user_model().objects.create_user(
            username='staffuser2',
            email='staff2@example.com',
            password='password123',
            is_staff=True
        )
        self.client.force_login(staff_user)
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.user.username)

    def test_staff_cannot_add_user_via_admin(self):
        """Test that staff cannot access the add user page."""
        staff_user = get_user_model().objects.create_user(
            username='staffuser3',
            email='staff3@example.com',
            password='password123',
            is_staff=True
        )
        self.client.force_login(staff_user)
        url = reverse('admin:core_user_add')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 403)

    def test_staff_cannot_delete_user_via_admin(self):
        """Test that staff cannot access the delete user page."""
        staff_user = get_user_model().objects.create_user(
            username='staffuser4',
            email='staff4@example.com',
            password='password123',
            is_staff=True
        )
        self.client.force_login(staff_user)
        url = reverse('admin:core_user_delete', args=[self.user.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 403)

    def test_staff_cannot_change_user_via_admin_post(self):
        """Test that staff cannot submit changes to a user via admin."""
        staff_user = get_user_model().objects.create_user(
            username='staffuser5',
            email='staff5@example.com',
            password='password123',
            is_staff=True
        )
        self.client.force_login(staff_user)
        url = reverse('admin:core_user_change', args=[self.user.id])
        data = {
            'username': 'hacked_username',
            'email': self.user.email,
        }
        res = self.client.post(url, data, follow=True)
        # Should be forbidden
        self.assertEqual(res.status_code, 403)
        # Verify the username was NOT changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')

    def test_superuser_can_add_user_via_admin(self):
        """Test that superuser can access the add user page."""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_superuser_can_delete_user_via_admin(self):
        """Test that superuser can access the delete user page."""
        url = reverse('admin:core_user_delete', args=[self.user.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    @patch('core.admin.send_verification_email')
    def test_create_user_via_admin_form_sends_verification_email(
        self, mock_send_email
    ):
        """Test that creating a user via admin sends verification email"""
        url = reverse('admin:core_user_add')
        data = {
            'username': 'verifyemailuser',
            'email': 'verifyemail@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        res = self.client.post(url, data, follow=True)
        self.assertEqual(res.status_code, 200)

        # Verify the user was created
        user = get_user_model().objects.get(
            username='verifyemailuser'
        )
        self.assertEqual(user.email, 'verifyemail@example.com')
        self.assertFalse(user.email_verified)

        # Verify that send_verification_email was called exactly once
        self.assertEqual(mock_send_email.call_count, 1)

        # Verify that the user has a verification token
        self.assertIsNotNone(user.verification_token)
        self.assertIsNotNone(user.verification_token_created_at)

    # Email Verification Admin Tests
    def test_email_verified_status_in_list_display(self):
        """Test that email_verified_status is in list_display"""
        self.assertIn('email_verified_status', self.user_admin.list_display)

    def test_email_verified_status_returns_verified(self):
        """Test email_verified_status returns 'Verified' for verified user"""
        self.user.email_verified = True
        self.user.save()
        result = self.user_admin.email_verified_status(self.user)
        self.assertEqual(result, 'Verified')

    def test_email_verified_status_returns_not_verified(self):
        """Test email_verified_status returns 'Not Verified'
        for unverified user"""
        self.user.email_verified = False
        self.user.save()
        result = self.user_admin.email_verified_status(self.user)
        self.assertEqual(result, 'Not Verified')

    def test_email_verified_in_list_filter(self):
        """Test that email_verified is in list_filter"""
        self.assertIn('email_verified', self.user_admin.list_filter)

    def test_email_verification_fieldset_exists(self):
        """Test that Email Verification fieldset exists"""
        fieldset_names = [
            fieldset[0] for fieldset in self.user_admin.fieldsets
        ]
        self.assertIn('Email Verification', fieldset_names)

    def test_email_verification_fieldset_has_correct_fields(self):
        """Test that Email Verification fieldset has correct fields"""
        email_verification_fieldset = None
        for fieldset in self.user_admin.fieldsets:
            if fieldset[0] == 'Email Verification':
                email_verification_fieldset = fieldset
                break

        self.assertIsNotNone(email_verification_fieldset)
        fields = email_verification_fieldset[1]['fields']
        self.assertIn('email_verified', fields)

    def test_verify_emails_action_exists(self):
        """Test that verify_emails action exists in actions"""
        self.assertIn('verify_emails', self.user_admin.actions)

    def test_admin_site_header_displayed(self):
        """Test that admin site header is set to 'Login Tracking Dashboard'"""
        url = reverse('admin:index')
        res = self.client.get(url)
        self.assertContains(res, 'Login Tracking Dashboard')

    def test_admin_site_title_set_correctly(self):
        """Test that admin site title is set to 'Login Tracking Dashboard'"""
        self.assertEqual(admin.site.site_header, 'Login Tracking Dashboard')
        self.assertEqual(admin.site.site_title, 'Login Tracking Dashboard')

    def test_admin_index_title_set_correctly(self):
        """Test that admin index title is set to 'Dashboard'"""
        self.assertEqual(admin.site.index_title, 'Dashboard')

    def test_admin_site_header_appears_on_change_page(self):
        """Test that site header appears on the user change page"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)
        self.assertContains(res, 'Login Tracking Dashboard')

    def test_admin_site_header_appears_on_user_list_page(self):
        """Test that site header appears on the user list page"""
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)
        self.assertContains(res, 'Login Tracking Dashboard')

    def test_verify_emails_action_marks_users_verified(self):
        """Test that verify_emails bulk action marks users as verified"""
        # Create another unverified user
        unverified_user = get_user_model().objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='password123',
            name='Unverified User',
            email_verified=False
        )

        # Ensure users are unverified
        self.assertFalse(self.user.email_verified)
        self.assertFalse(unverified_user.email_verified)

        # Call the action
        queryset = get_user_model().objects.filter(
            id__in=[self.user.id, unverified_user.id]
        )
        self.user_admin.verify_emails(None, queryset)

        # Refresh from db and verify
        self.user.refresh_from_db()
        unverified_user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertTrue(unverified_user.email_verified)
