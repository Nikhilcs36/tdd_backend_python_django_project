from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, \
    OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    UserSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    VerifyEmailSerializer,
    EmailRequestSerializer,
    PasswordResetSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from core.models import User
from .permissions import IsSuperUser, IsStaffOrSuperUser
from .pagination import UserPagination

from core.email_service import (
    send_verification_email,
    send_welcome_email,
    build_verification_url,
    build_password_reset_url,
    send_password_reset_email
)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        """
        Create user, generate verification token, and send verification email.
        """
        user = serializer.save()

        # Generate verification token
        token = user.generate_verification_token()

        # Build verification URL
        verification_url = build_verification_url(self.request, token)

        # Send verification email
        try:
            send_verification_email(user, verification_url)
        except Exception:
            # Log error but don't fail registration
            # The email verification can be resent later
            pass


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain pair view."""
    serializer_class = CustomTokenObtainPairSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user

    def get_serializer(self, *args, **kwargs):
        """
        Instantiate the serializer with partial=True for PUT requests.
        """
        kwargs['partial'] = True
        return super().get_serializer(*args, **kwargs)


class UserListView(generics.ListAPIView):
    """List all users with role filtering support."""
    serializer_class = UserSerializer
    permission_classes = [IsStaffOrSuperUser]
    pagination_class = UserPagination  # Enable pagination

    @extend_schema(
        operation_id="list_users",
        summary="List Users with Role Filtering",
        description=(
            "Retrieve paginated list of all users. Supports role-based "
            "filtering with the 'role' parameter and 'me' parameter for "
            "current user filtering. Includes 'is_admin' field to indicate "
            "user privileges."
        ),
        parameters=[
            OpenApiParameter(
                name="role",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter users by role. Options: 'admin' (staff/superuser), "  # noqa: E501
                    "'regular' (non-admin users). Omit to return all users."
                ),
                required=False,
                enum=["admin", "regular"]
            ),
            OpenApiParameter(
                name="me",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description=(
                    "Show only current authenticated user. Available to all "
                    "authenticated users."
                ),
                required=False
            )
        ],
        responses={
            200: UserSerializer(many=True),
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response - All Users",
                value=[
                    {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com",
                        "is_admin": True
                    },
                    {
                        "id": 2,
                        "username": "user",
                        "email": "user@example.com",
                        "is_admin": False
                    }
                ],
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Successful Response - Admin Users Only",
                value=[
                    {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com",
                        "is_admin": True
                    }
                ],
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """Handle GET request with proper documentation."""
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Return queryset with optional role and me filtering."""
        queryset = User.objects.all()

        # Check for 'me' parameter first (takes precedence)
        me = self.request.query_params.get('me')
        if me and me.lower() == 'true':
            return queryset.filter(id=self.request.user.id)

        # Add role filtering with validation
        role = self.request.query_params.get('role')
        if role:
            if role not in ['admin', 'regular']:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    {'error': 'Invalid role. Must be "admin" or "regular".'}
                )
            if role == 'admin':
                queryset = queryset.filter(
                    Q(is_staff=True) | Q(is_superuser=True)
                )
            elif role == 'regular':
                queryset = queryset.filter(
                    is_staff=False, is_superuser=False
                )

        return queryset

    def get_serializer_context(self):
        """Add context to tell serializer to include role fields."""
        context = super().get_serializer_context()
        # Tell serializer to include role fields
        context['include_roles'] = True
        return context


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a user's details."""
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsSuperUser]

    def get_serializer(self, *args, **kwargs):
        """
        Instantiate the serializer with partial=True for PUT/PATCH requests.
        """
        kwargs['partial'] = True
        return super().get_serializer(*args, **kwargs)


class LogoutView(generics.GenericAPIView):
    """Logout the authenticated user."""
    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Blacklist the refresh token."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'message': 'logout_Success'},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {'detail': 'refresh_token_not_valid'},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerifyEmailView(generics.GenericAPIView):
    """Verify user's email with token."""
    serializer_class = VerifyEmailSerializer

    def post(self, request, token):
        """Handle email verification."""
        # Use serializer even though token comes from URL
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()

        try:
            user = User.objects.get(verification_token=token)

            # Check if token is expired
            if user.is_verification_token_expired():
                return Response(
                    {'error': 'Verification token has expired. '
                     'Please request a new one.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify email
            if user.verify_email(token):
                # Send welcome email
                send_welcome_email(user)
                return Response(
                    {'message': 'Email verified successfully. '
                     'You can now log in.'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Invalid verification token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid verification token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationEmailView(generics.GenericAPIView):
    """Resend verification email."""
    serializer_class = EmailRequestSerializer

    def post(self, request):
        """Handle resend verification email request."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        try:
            user = User.objects.get(email=email)

            if user.email_verified:
                return Response(
                    {'message': 'Email is already verified.'},
                    status=status.HTTP_200_OK
                )

            # Generate new verification token
            token = user.generate_verification_token()
            verification_url = build_verification_url(request, token)

            # Send verification email
            send_verification_email(user, verification_url)

            return Response(
                {'message': 'Verification email sent successfully.'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            return Response(
                {'message': 'If an account exists with this email, '
                 'a verification email has been sent.'},
                status=status.HTTP_200_OK
            )


class RequestPasswordResetView(generics.GenericAPIView):
    """Request password reset for verified users."""
    serializer_class = EmailRequestSerializer

    def post(self, request):
        """Handle password reset request."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        try:
            user = User.objects.get(email=email)

            # Only allow password reset for verified users
            if not user.email_verified:
                return Response(
                    {'error': 'Please verify your email before '
                     'resetting password.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate password reset token
            token = user.generate_password_reset_token()
            reset_url = build_password_reset_url(request, token)

            # Send password reset email
            send_password_reset_email(user, reset_url)

            return Response(
                {'message': 'Password reset email sent successfully.'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            return Response(
                {'message': 'If an account exists with this email, '
                 'a password reset email has been sent.'},
                status=status.HTTP_200_OK
            )


class ResetPasswordView(generics.GenericAPIView):
    """Reset password with token."""
    serializer_class = PasswordResetSerializer

    def post(self, request, token):
        """Handle password reset."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data.get('password')

        try:
            user = User.objects.get(password_reset_token=token)

            # Reset password
            if user.reset_password(token, new_password):
                return Response(
                    {'message': 'Password reset successful. '
                     'You can now login with your new password.'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Invalid or expired password reset token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid password reset token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
