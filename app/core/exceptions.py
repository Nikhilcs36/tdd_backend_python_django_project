"""
Custom exception handler for JWT authentication errors.
"""
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
    AuthenticationFailed
)
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns a simplified format for JWT errors.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Handle JWT authentication errors and missing authentication
    if isinstance(exc, (InvalidToken, AuthenticationFailed, NotAuthenticated)):
        return Response(
            {
                "message": "Token is invalid or expired"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    return response
