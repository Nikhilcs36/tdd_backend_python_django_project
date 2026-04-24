"""Tests for JWT-aware login tracking middleware."""
import json
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import Mock
from core.middleware import LoginTrackingMiddleware
from core.models import LoginActivity

User = get_user_model()


class MiddlewareJWTTrackingTests(TestCase):
    """Test middleware handles JWT token endpoint correctly."""

    def setUp(self):
        self.factory = RequestFactory()

        def get_response(req):
            return Mock(status_code=200)

        self.middleware = LoginTrackingMiddleware(get_response)

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.email_verified = True
        self.user.save()

    def test_middleware_matches_user_token_url(self):
        """Test that middleware matches /api/user/token/ URL."""
        request = self.factory.post('/api/user/token/')
        is_auth = any(
            pattern.match(request.path)
            for pattern in self.middleware.auth_patterns
        )
        self.assertTrue(
            is_auth,
            "Middleware should match /api/user/token/ endpoint"
        )

    def test_middleware_tracks_successful_login_from_json_body(self):
        """Test middleware tracks successful login with JSON body."""
        request = self.factory.post(
            '/api/user/token/',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'testpass123'
            }),
            content_type='application/json'
        )
        request.user = self.user

        response = Mock(status_code=200)
        self.middleware._track_login_activity(request, response)

        activities = LoginActivity.objects.filter(
            user=self.user, success=True)
        self.assertEqual(activities.count(), 1)

    def test_middleware_tracks_failed_login_from_json_body(self):
        """Test middleware tracks failed login with JSON body."""
        request = self.factory.post(
            '/api/user/token/',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        request.user = Mock(is_authenticated=False)

        response = Mock(status_code=400)
        self.middleware._track_login_activity(request, response)

        activities = LoginActivity.objects.filter(
            user=self.user, success=False)
        self.assertEqual(activities.count(), 1)

    def test_middleware_tracks_failed_login_by_user_lookup(self):
        """
        Test middleware finds user from JSON body even when
        request.user is not authenticated.
        """
        request = self.factory.post(
            '/api/user/token/',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        request.user = Mock(is_authenticated=False)

        response = Mock(status_code=400)
        self.middleware._track_login_activity(request, response)

        activities = LoginActivity.objects.filter(
            user=self.user, success=False)
        self.assertEqual(activities.count(), 1)

    def test_middleware_uses_authenticated_user_when_available(self):
        """Test middleware prefers authenticated request.user."""
        request = self.factory.post('/api/user/token/')
        request.user = self.user

        response = Mock(status_code=200)
        self.middleware._track_login_activity(request, response)

        activities = LoginActivity.objects.filter(
            user=self.user, success=True)
        self.assertEqual(activities.count(), 1)

    def test_middleware_does_not_track_nonexistent_user(self):
        """Test middleware skips tracking when user doesn't exist."""
        request = self.factory.post(
            '/api/user/token/',
            data=json.dumps({
                'email': 'nonexistent@example.com',
                'password': 'testpass123'
            }),
            content_type='application/json'
        )
        request.user = Mock(is_authenticated=False)

        response = Mock(status_code=400)
        self.middleware._track_login_activity(request, response)

        # Should not create any activity
        self.assertEqual(LoginActivity.objects.count(), 0)

    def test_middleware_handles_invalid_json_gracefully(self):
        """Test middleware handles invalid JSON body gracefully."""
        request = self.factory.post(
            '/api/user/token/',
            data='not json',
            content_type='application/json'
        )
        request.user = Mock(is_authenticated=False)

        response = Mock(status_code=400)
        # Should not raise
        try:
            self.middleware._track_login_activity(request, response)
        except Exception:
            self.fail(
                "Middleware should handle invalid JSON gracefully")

        self.assertEqual(LoginActivity.objects.count(), 0)

    def test_middleware_handles_empty_body(self):
        """Test middleware handles empty request body."""
        request = self.factory.post('/api/user/token/')
        request.user = Mock(is_authenticated=False)

        response = Mock(status_code=400)
        try:
            self.middleware._track_login_activity(request, response)
        except Exception:
            self.fail(
                "Middleware should handle empty body gracefully")

        self.assertEqual(LoginActivity.objects.count(), 0)

    def test_middleware_extracts_ip_and_user_agent_correctly(self):
        """Test middleware captures IP and user agent from request."""
        request = self.factory.post('/api/user/token/')
        request.user = self.user
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.100, 10.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'TestAgent/1.0'

        response = Mock(status_code=200)
        self.middleware._track_login_activity(request, response)

        activity = LoginActivity.objects.get(user=self.user)
        self.assertEqual(activity.ip_address, '192.168.1.100')
        self.assertEqual(activity.user_agent, 'TestAgent/1.0')

    def test_middleware_captures_user_agent_when_long(self):
        """Test middleware truncates long user agent."""
        request = self.factory.post('/api/user/token/')
        request.user = self.user
        request.META['HTTP_USER_AGENT'] = 'A' * 600

        response = Mock(status_code=200)
        self.middleware._track_login_activity(request, response)

        activity = LoginActivity.objects.get(user=self.user)
        self.assertEqual(len(activity.user_agent), 500)


class MiddlewareIntegrationAPITests(TestCase):
    """Integration tests for middleware via actual API calls."""

    @override_settings(MIDDLEWARE=[
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'core.middleware.LoginTrackingMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ])
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.email_verified = True
        self.user.save()

    def test_api_login_tracked_by_middleware(self):
        """Test actual API login is tracked by middleware."""
        url = reverse('user:token')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        activities = LoginActivity.objects.filter(
            user=self.user, success=True)
        self.assertEqual(activities.count(), 1)

    def test_api_failed_login_tracked_by_middleware(self):
        """Test actual failed API login is tracked by middleware."""
        url = reverse('user:token')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        activities = LoginActivity.objects.filter(
            user=self.user, success=False)
        self.assertEqual(activities.count(), 1)

    def test_api_multiple_logins_count_correctly(self):
        """Test multiple API logins count correctly via middleware."""
        url = reverse('user:token')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        for _ in range(3):
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            LoginActivity.objects.filter(user=self.user, success=True).count(),
            3
        )

    def test_serializer_no_longer_creates_duplicate_activity(self):
        """
        Test that serializer no longer creates LoginActivity,
        so middleware creates exactly one per login.
        """
        url = reverse('user:token')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should be exactly 1, not 2 (which would indicate duplication)
        self.assertEqual(LoginActivity.objects.count(), 1)

    def test_non_auth_endpoints_not_tracked(self):
        """Test non-auth endpoints don't create login activities."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user:me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(LoginActivity.objects.count(), 0)
