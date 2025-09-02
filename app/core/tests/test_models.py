from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    def test_create_user_with_username_and_email_successful(self):
        """Test creating new user with username and email successfully"""
        username = 'testuser'
        email = 'test@example.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password=password
        )

        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertIsNotNone(user.id)  # Verify ID field exists
        self.assertIsNotNone(user.date_joined)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users"""
        username = 'testuser'
        email = 'test@EXAMPLE.COM'
        user = get_user_model().objects.create_user(
            username=username, email=email, password='test123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                username='testuser', email=None, password='test123')

    def test_create_superuser(self):
        """Test creating new superuser"""
        user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_user_with_duplicate_username(self):
        """Test creating a user with a duplicate username raises an error"""
        get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        with self.assertRaises(Exception):
            get_user_model().objects.create_user(
                username='testuser',
                email='test2@example.com',
                password='testpassword'
            )

    def test_create_user_with_duplicate_email(self):
        """Test creating a user with a duplicate email raises an error"""
        get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        with self.assertRaises(Exception):
            get_user_model().objects.create_user(
                username='testuser2',
                email='test@example.com',
                password='testpassword'
            )
