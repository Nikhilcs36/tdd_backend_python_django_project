"""Middleware for tracking user login activities."""
import json
import re
from django.utils import timezone
from django.contrib.auth import get_user_model
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


def _extract_email_from_request(request):
    """Extract email from request body before DRF consumes it."""
    email = None

    # Check if body was already parsed (DRF/APIClient)
    if hasattr(request, 'data') and isinstance(request.data, dict):
        email = request.data.get('email')
    # Try POST data
    elif request.POST:
        email = request.POST.get('email')
    # Try JSON body
    elif request.content_type == 'application/json':
        try:
            body = request.body.decode('utf-8')
            if body:
                data = json.loads(body)
                email = data.get('email')
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    return email


def _get_user_from_request(request, pre_extracted_email=None):
    """
    Extract user from request.

    Always queries the database when email is available to get the
    latest user data. Falls back to request.user when email is not
    available (e.g., for non-JSON requests).
    """
    # Get email from pre-extracted value or request body
    email = pre_extracted_email
    if not email:
        email = _extract_email_from_request(request)

    # Always query DB when email is available for fresh data
    if email:
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            pass

    # Fallback to request.user when email is not available
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        return user

    return None


class LoginTrackingMiddleware:
    """Middleware to track user login activities."""

    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response
        # Regex pattern to match authentication endpoints
        self.auth_patterns = [
            re.compile(r'^/api/user/token/?$'),  # Token endpoint  # noqa: E501
        ]

    def __call__(self, request):
        """Process the request and track login activities."""
        # Check if this is an authentication endpoint
        is_auth_endpoint = any(
            pattern.match(request.path) for pattern in self.auth_patterns
        )

        if is_auth_endpoint:
            # Pre-extract email before DRF consumes the request body
            pre_extracted_email = _extract_email_from_request(request)
            # Process the request first to get the response
            response = self.get_response(request)

            # Track login activity based on response status and authentication
            self._track_login_activity(
                request, response, email=pre_extracted_email)

            return response
        else:
            # For non-auth endpoints, just process normally
            return self.get_response(request)

    def _track_login_activity(self, request, response, email=None):
        """Track login activity based on request and response."""
        try:
            # Determine if login was successful
            # Successful if response is 200
            is_successful = response.status_code == 200

            # Get client information
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)

            # Try to get the user (from authenticated request or body lookup)
            user = _get_user_from_request(request, pre_extracted_email=email)

            # Only track if we have a valid user object
            if user and hasattr(user, 'id'):
                LoginActivity.objects.create(
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=is_successful,
                    timestamp=timezone.now()
                )

                # Auto-grant staff access after 3 successful logins
                if is_successful:
                    user.refresh_from_db()
                    if (not user.staff_access_granted and
                            user.login_count >= 3):
                        user.is_staff = True
                        user.staff_access_granted = True
                        user.active_role = 'staff'
                        user.save()

        except Exception:
            # Log the error but don't break the request
            # In production, you might want to use proper logging
            pass
