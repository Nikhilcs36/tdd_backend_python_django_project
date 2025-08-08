"""
Tests for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests (TestCase): 
    """Test models"""

    def test_create_username_with_email_password_successful(self):
        """Test creating a user model with an username and email and password is successful"""
        username = 'testusername'
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
        username=username,
        email=email,
        password=password)
        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password (password))
        