"""Middleware for tracking user login activities."""
import re
from django.utils import timezone
from core.models import LoginActivity


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Extract user agent from request."""
    # Truncate to max length of 500 characters
    return request.META.get('HTTP_USER_AGENT', '')[:500]


class LoginTrackingMiddleware:
    """Middleware to track user login activities."""

    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response
        # Regex pattern to match authentication endpoints
        self.auth_patterns = [
            re.compile(r'^/api/token/?$'),  # Token endpoint  # noqa: E501
        ]

    def __call__(self, request):
        """Process the request and track login activities."""
        # Check if this is an authentication endpoint
        is_auth_endpoint = any(
            pattern.match(request.path) for pattern in self.auth_patterns
        )

        if is_auth_endpoint:
            # Process the request first to get the response
            response = self.get_response(request)

            # Track login activity based on response status and authentication
            self._track_login_activity(request, response)

            return response
        else:
            # For non-auth endpoints, just process normally
            return self.get_response(request)

    def _track_login_activity(self, request, response):
        """Track login activity based on request and response."""
        try:
            # Determine if login was successful
            # Successful if user is authenticated and response is 200
            user = getattr(request, 'user', None)
            is_authenticated = user and user.is_authenticated
            is_successful = response.status_code == 200 and is_authenticated

            # Get client information
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)

            # Only track if we have a user (even for failed attempts)
            if user and hasattr(user, 'id'):
                LoginActivity.objects.create(
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=is_successful,
                    timestamp=timezone.now()
                )

        except Exception:
            # Log the error but don't break the request
            # In production, you might want to use proper logging
            pass
