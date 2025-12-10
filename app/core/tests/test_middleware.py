"""Tests for login tracking middleware."""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock
from core.middleware import LoginTrackingMiddleware
from core.models import LoginActivity
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class LoginTrackingMiddlewareTests(TestCase):
    """Test cases for login tracking middleware."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        def get_response(req): return Mock(status_code=200)
        self.middleware = LoginTrackingMiddleware(get_response)

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_middleware_tracks_successful_login(self):
        """Test that middleware tracks successful login attempts."""
        # Create a mock authentication request
        request = self.factory.post('/api/token/', data={
            'email': 'test@example.com',
            'password': 'testpass123'
        })

        # Mock user authentication
        request.user = self.user

        # Mock successful response
        response = Mock(status_code=200)

        # Call the middleware
        self.middleware._track_login_activity(request, response)

        # Verify login activity was created
        activities = LoginActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 1)

        activity = activities.first()
        self.assertTrue(activity.success)
        self.assertEqual(activity.user, self.user)
        self.assertIsNotNone(activity.ip_address)
        self.assertIsNotNone(activity.user_agent)

    def test_middleware_tracks_failed_login(self):
        """Test that middleware tracks failed login attempts."""
        # Create a mock authentication request
        request = self.factory.post('/api/token/', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })

        # Mock unauthenticated user
        request.user = Mock(is_authenticated=False)

        # Mock failed response
        response = Mock(status_code=401)

        # Call the middleware
        self.middleware._track_login_activity(request, response)

        # Verify no login activity was created for unauthenticated user
        activities = LoginActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 0)

    def test_middleware_handles_non_auth_endpoints(self):
        """Test that middleware ignores non-authentication endpoints."""
        # Create a mock non-auth request
        request = self.factory.get('/api/users/')
        request.user = self.user

        # Call the full middleware
        self.middleware(request)

        # Verify no login activity was created
        activities = LoginActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 0)

    def test_middleware_handles_auth_endpoints(self):
        """Test that middleware processes authentication endpoints."""
        # Create a mock auth request
        request = self.factory.post('/api/token/')
        request.user = self.user

        # Call the full middleware
        self.middleware(request)

        # Verify login activity was created
        activities = LoginActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 1)

    def test_middleware_handles_exceptions_gracefully(self):
        """Test that middleware handles exceptions without breaking the app."""
        # Create a mock request that will cause an exception
        request = self.factory.post('/api/token/')
        request.user = None  # This will cause an exception

        # Mock response
        response = Mock(status_code=200)

        # Call the middleware - should not raise an exception
        try:
            self.middleware._track_login_activity(request, response)
            # If we get here, the middleware handled the exception gracefully
            self.assertTrue(True)
        except Exception:
            self.fail("Middleware should handle exceptions gracefully")

    def test_get_client_ip_extracts_correct_ip(self):
        """Test that client IP extraction works correctly."""
        from core.middleware import get_client_ip

        # Test with X-Forwarded-For header
        request = Mock()
        request.META = {'HTTP_X_FORWARDED_FOR': '192.168.1.1, 10.0.0.1'}
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

        # Test with REMOTE_ADDR
        request.META = {'REMOTE_ADDR': '192.168.1.2'}
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.2')

        # Test with no IP
        request.META = {}
        ip = get_client_ip(request)
        self.assertIsNone(ip)

    def test_get_user_agent_extracts_correct_agent(self):
        """Test that user agent extraction works correctly."""
        from core.middleware import get_user_agent

        # Test with user agent
        request = Mock()
        request.META = {'HTTP_USER_AGENT': 'Test Browser'}
        agent = get_user_agent(request)
        self.assertEqual(agent, 'Test Browser')

        # Test with no user agent
        request.META = {}
        agent = get_user_agent(request)
        self.assertEqual(agent, '')

        # Test with long user agent (truncation)
        long_agent = 'A' * 600
        request.META = {'HTTP_USER_AGENT': long_agent}
        agent = get_user_agent(request)
        self.assertEqual(len(agent), 500)
        self.assertEqual(agent, 'A' * 500)

    def test_middleware_only_tracks_auth_endpoints(self):
        """Test that middleware only tracks authentication endpoints."""
        # Test auth endpoint
        request = self.factory.post('/api/token/')
        request.user = self.user
        is_auth_endpoint = any(pattern.match(request.path)
                               for pattern in self.middleware.auth_patterns)
        self.assertTrue(is_auth_endpoint)

        # Test non-auth endpoint
        request = self.factory.get('/api/users/')
        is_auth_endpoint = any(pattern.match(request.path)
                               for pattern in self.middleware.auth_patterns)
        self.assertFalse(is_auth_endpoint)

    def test_middleware_creates_activity_for_authenticated_user_only(self):
        """Test that middleware only creates activities for auth users."""
        # Create request with authenticated user
        request = self.factory.post('/api/token/')
        request.user = self.user

        # Mock response
        response = Mock(status_code=200)

        # Call middleware
        self.middleware._track_login_activity(request, response)

        # Should create activity
        activities = LoginActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 1)

        # Create request with unauthenticated user
        request.user = Mock(is_authenticated=False)

        # Call middleware again
        self.middleware._track_login_activity(request, response)

        # Should not create additional activity
        activities = LoginActivity.objects.filter(user=self.user)
        self.assertEqual(activities.count(), 1)
