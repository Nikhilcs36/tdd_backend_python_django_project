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

        self.assertContains(res, self.user.name)
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
        self.assertContains(res, 'name')
        self.assertContains(res, 'password')
        self.assertContains(res, 'image')

        # Also check for proper field labels (capitalized)
        self.assertContains(res, 'Email')
        self.assertContains(res, 'Name')
        self.assertContains(res, 'Password')
        self.assertContains(res, 'Image')

    def test_create_user_page(self):
        """Test that the create user page works"""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_admin_fieldsets_contain_name_and_image(self):
        """Test that admin fieldsets configuration includes name and image"""
        # This test verifies that the admin configuration has expected fields

        # Get the registered admin class
        user_admin = admin.site._registry[User]

        # Check that name and image are in the first fieldset
        first_fieldset_fields = user_admin.fieldsets[0][1]['fields']
        self.assertIn('name', first_fieldset_fields)
        self.assertIn('image', first_fieldset_fields)

        # Check that name is in list_display
        self.assertIn('name', user_admin.list_display)

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
