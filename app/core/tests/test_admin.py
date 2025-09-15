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
