"""
Tests for custom exception handling.
"""
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model


class CustomExceptionHandlerTests(APITestCase):
    """Test custom exception handler for JWT authentication errors."""

    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.valid_token = AccessToken.for_user(self.user)

    def test_invalid_token_returns_custom_401_response(self):
        """Test that invalid token returns custom 401 response format."""
        # Create an invalid token by modifying a valid token
        invalid_token = str(self.valid_token) + 'invalid'

        # Set authorization header with invalid token
        self.client.credentials(
            HTTP_AUTHORIZATION=f'JWT {invalid_token}'
        )

        # Make request to a protected endpoint
        response = self.client.get('/api/user/me/')

        # Assert custom response format
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 401)
        self.assertEqual(
            response.data['message'], 'Token is invalid or expired'
        )

    def test_expired_token_returns_custom_401_response(self):
        """Test that expired token returns custom 401 response format."""
        # Create an expired token (simulate by using very short lifetime)
        from datetime import timedelta
        from rest_framework_simplejwt.tokens import AccessToken

        # Create token with very short lifetime
        expired_token = AccessToken.for_user(self.user)
        expired_token.set_exp(lifetime=timedelta(seconds=-1))  # Expired

        # Set authorization header with expired token
        self.client.credentials(
            HTTP_AUTHORIZATION=f'JWT {expired_token}'
        )

        # Make request to a protected endpoint
        response = self.client.get('/api/user/me/')

        # Assert custom response format
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 401)
        self.assertEqual(
            response.data['message'], 'Token is invalid or expired'
        )

    def test_missing_token_returns_custom_401_response(self):
        """Test that missing token returns custom 401 response format."""
        # Make request without authorization header
        response = self.client.get('/api/user/me/')

        # Assert custom response format
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 401)
        self.assertEqual(
            response.data['message'], 'Token is invalid or expired'
        )
