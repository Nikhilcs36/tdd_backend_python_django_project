from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User

CREATE_USER_URL = reverse('user:create')


class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user with a valid payload is successful."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'passwordRepeat': 'password123',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.username, payload['username'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'passwordRepeat': 'password123',

        }
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',

        )

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if the password is too short."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'pw',
            'passwordRepeat': 'pw',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = User.objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_user_with_password_repeat_success(self):
        """Test creating a user with a valid payload including
        passwordRepeat is successful."""
        payload = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'password123',
            'passwordRepeat': 'password123',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.username, payload['username'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
        self.assertNotIn('passwordRepeat', res.data)

    def test_create_user_with_mismatched_password_error(self):
        """Test error returned if password and passwordRepeat do not match."""
        payload = {
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': 'password123',
            'passwordRepeat': 'password124',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_blank_username_error(self):
        """Test error returned if username is blank."""
        payload = {
            'username': '',
            'email': 'test4@example.com',
            'password': 'password123',
            'passwordRepeat': 'password123',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
