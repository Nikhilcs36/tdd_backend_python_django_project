"""
Tests for email verification API endpoints
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User
from datetime import timedelta

VERIFY_EMAIL_URL = reverse('user:verify-email')


class EmailVerificationAPITests(TestCase):
    """Test email verification API"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Testpass123'
        )

    def test_verify_email_success(self):
        """Test successful email verification with email+token"""
        token = self.user.generate_verification_token()

        res = self.client.post(VERIFY_EMAIL_URL, {
            'email': self.user.email,
            'token': token
        })

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data['message'],
            'Email verified successfully. You can now log in.'
        )
        self.assertNotIn('already_verified', res.data)

        # Refresh user and verify email is marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        # Token should be preserved (not cleared)
        self.assertEqual(self.user.verification_token, token)

    def test_verify_email_already_verified_with_valid_token(self):
        """Test that verifying with valid token returns already_verified"""
        # First verify the email (token preserved)
        token = self.user.generate_verification_token()
        self.user.email_verified = True
        self.user.save()

        # Try to verify with valid token
        res = self.client.post(VERIFY_EMAIL_URL, {
            'email': self.user.email,
            'token': token
        })

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['message'], 'Email is already verified.')
        self.assertTrue(res.data['already_verified'])

    def test_verify_email_wrong_token_does_not_reveal_verified_status(self):
        """Test security: wrong token should NOT reveal verified status"""
        # Verify email first (token preserved)
        self.user.generate_verification_token()
        self.user.email_verified = True
        self.user.save()

        # Try with wrong token
        res = self.client.post(VERIFY_EMAIL_URL, {
            'email': self.user.email,
            'token': 'wrong-token-123'
        })

        # Should return "Invalid token" - NOT reveal that email is verified
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['error'], 'Invalid verification token.')
        self.assertNotIn('already_verified', res.data)

    def test_verify_email_expired_token_returns_expired_flag(self):
        """Test that expired token returns expired flag for frontend"""
        token = self.user.generate_verification_token()

        # Manually set token creation to 25 hours ago (expired)
        self.user.verification_token_created_at = \
            timezone.now() - timedelta(hours=25)
        self.user.save()

        res = self.client.post(VERIFY_EMAIL_URL, {
            'email': self.user.email,
            'token': token
        })

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expired', res.data)
        self.assertTrue(res.data['expired'])
        self.assertEqual(
            res.data['error'],
            'Verification token has expired. Please request a new one.'
        )

    def test_verify_email_invalid_token(self):
        """Test that invalid token returns error"""
        self.user.generate_verification_token()  # Generate valid token

        res = self.client.post(VERIFY_EMAIL_URL, {
            'email': self.user.email,
            'token': 'invalid-token-123'
        })

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['error'], 'Invalid verification token.')
        self.assertNotIn('expired', res.data)
        self.assertNotIn('already_verified', res.data)

    def test_verify_email_old_token_after_resend(self):
        """Test that old token is invalid after resend (new token generated)"""
        old_token = self.user.generate_verification_token()

        # Simulate resend - generate new token
        new_token = self.user.generate_verification_token()
        self.assertNotEqual(old_token, new_token)

        # Try with old token
        res = self.client.post(VERIFY_EMAIL_URL, {
            'email': self.user.email,
            'token': old_token
        })

        # Old token should be invalid
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['error'], 'Invalid verification token.')

    def test_verify_email_missing_email(self):
        """Test that missing email returns error"""
        token = self.user.generate_verification_token()

        res = self.client.post(VERIFY_EMAIL_URL, {
            'token': token
        })

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data)

    def test_verify_email_missing_token(self):
        """Test that missing token returns error"""
        res = self.client.post(VERIFY_EMAIL_URL, {
            'email': self.user.email
        })

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', res.data)

    def test_verify_email_user_not_found(self):
        """Test that non-existent email returns error"""
        res = self.client.post(VERIFY_EMAIL_URL, {
            'email': 'nonexistent@example.com',
            'token': 'some-token'
        })

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['error'], 'Invalid verification token.')
