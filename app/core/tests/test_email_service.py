"""
Tests for email service URL building functions.
Tests follow TDD approach - verifying email URLs point to frontend.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from core.email_service import (
    build_verification_url,
    build_password_reset_url,
)


class EmailServiceURLTests(TestCase):
    """Test email service URL building functions."""

    def setUp(self):
        """Set up test user."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Testpass123'
        )

    @override_settings(FRONTEND_BASE_URL='http://localhost:5173')
    def test_build_verification_url_uses_frontend_url(self):
        """
        Test that verification URL points to frontend, not backend API.

        This is important because:
        - Users clicking email links should see React app, not DRF API
        - Frontend handles the verification flow with better UX
        - Backend API should only be called programmatically by frontend
        """
        token = self.user.generate_verification_token()

        url = build_verification_url(None, token)

        # URL should point to frontend
        self.assertEqual(url, f"http://localhost:5173/verify-email/{token}/")
        # URL should NOT contain backend API path
        self.assertNotIn('/api/user/verify-email/', url)
        # URL should contain frontend path
        self.assertIn('/verify-email/', url)

    @override_settings(FRONTEND_BASE_URL='http://localhost:5173')
    def test_build_verification_url_with_trailing_slash_setting(self):
        """Test URL is built correctly even if setting has trailing slash."""
        token = self.user.generate_verification_token()

        with override_settings(FRONTEND_BASE_URL='http://localhost:5173/'):
            url = build_verification_url(None, token)
            # Should not have double slashes
            expected = f"http://localhost:5173/verify-email/{token}/"
            self.assertEqual(url, expected)

    @override_settings(FRONTEND_BASE_URL='https://myapp.example.com')
    def test_build_verification_url_with_https_production_url(self):
        """Test verification URL with production HTTPS frontend URL."""
        token = self.user.generate_verification_token()

        url = build_verification_url(None, token)

        expected = f"https://myapp.example.com/verify-email/{token}/"
        self.assertEqual(url, expected)
        self.assertTrue(url.startswith('https://'))

    @override_settings(FRONTEND_BASE_URL='http://localhost:5173')
    def test_build_password_reset_url_uses_frontend_url(self):
        """Test that password reset URL points to frontend, not backend API."""
        token = self.user.generate_password_reset_token()

        url = build_password_reset_url(None, token)

        # URL should point to frontend
        self.assertEqual(url, f"http://localhost:5173/reset-password/{token}/")
        # URL should NOT contain backend API path
        self.assertNotIn('/api/user/reset-password/', url)
        # URL should contain frontend path
        self.assertIn('/reset-password/', url)

    @override_settings(FRONTEND_BASE_URL='http://localhost:5173')
    def test_build_password_reset_url_with_trailing_slash_setting(self):
        """Test URL is built correctly even if setting has trailing slash."""
        token = self.user.generate_password_reset_token()

        with override_settings(FRONTEND_BASE_URL='http://localhost:5173/'):
            url = build_password_reset_url(None, token)
            # Should not have double slashes
            expected = f"http://localhost:5173/reset-password/{token}/"
            self.assertEqual(url, expected)

    @override_settings(FRONTEND_BASE_URL='https://myapp.example.com')
    def test_build_password_reset_url_with_https_production_url(self):
        """Test password reset URL with production HTTPS frontend URL."""
        token = self.user.generate_password_reset_token()

        url = build_password_reset_url(None, token)

        expected = f"https://myapp.example.com/reset-password/{token}/"
        self.assertEqual(url, expected)
        self.assertTrue(url.startswith('https://'))

    @override_settings(FRONTEND_BASE_URL='http://localhost:5173')
    def test_verification_url_includes_correct_token(self):
        """Test that the verification URL includes the exact token provided."""
        token = self.user.generate_verification_token()

        url = build_verification_url(None, token)

        # Extract token from URL and verify it matches
        token_from_url = url.rstrip('/').split('/')[-1]
        self.assertEqual(token_from_url, token)
        self.assertEqual(len(token_from_url), 43)  # Standard token length

    @override_settings(FRONTEND_BASE_URL='http://localhost:5173')
    def test_password_reset_url_includes_correct_token(self):
        """Test password reset URL includes the exact token provided."""
        token = self.user.generate_password_reset_token()

        url = build_password_reset_url(None, token)

        # Extract token from URL and verify it matches
        token_from_url = url.rstrip('/').split('/')[-1]
        self.assertEqual(token_from_url, token)
        self.assertEqual(len(token_from_url), 43)  # Standard token length
