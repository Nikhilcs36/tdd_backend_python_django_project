import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
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
from .permissions import IsStaffOrSuperUser, UserDetailPermission
from .pagination import UserPagination
from .rsa_key_manager import load_public_key, get_public_key_path

from core.email_service import (
    send_verification_email,
    send_welcome_email,
    build_verification_url,
    build_password_reset_url,
    send_password_reset_email
)

logger = logging.getLogger(__name__)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer

    @extend_schema(
        operation_id="create_user",
        summary="Register New User",
        description=(
            "Create a new user account. Accepts user details such as email, "
            "username, and password. Automatically sends a verification email "
            "to the provided email address. The user must verify their email "
            "before they can log in."
        ),
        responses={
            201: UserSerializer,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Registration",
                value={
                    "id": 1,
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "image": None
                },
                response_only=True,
                status_codes=["201"]
            ),
            OpenApiExample(
                "Validation Error",
                value={
                    "email": ["user with this email already exists."],
                    "username": ["A user with that username already exists."]
                },
                response_only=True,
                status_codes=["400"]
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        """Handle POST request for user registration."""
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Create user, generate verification token, and send verification email.
        """
        user = serializer.save()

        # Generate verification token
        token = user.generate_verification_token()

        # Build verification URL with email
        verification_url = build_verification_url(
            self.request, token, email=user.email
        )

        # Send verification email
        try:
            send_verification_email(user, verification_url)
            logger.info('Verification email sent to %s', user.email)
        except Exception as e:
            logger.error(
                'Failed to send verification email to %s: %s',
                user.email, e,
                exc_info=True
            )
            # Don't fail registration - email can be resent later


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain pair view."""
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        operation_id="login_obtain_token",
        summary="User Login / Obtain JWT Token",
        description=(
            "Authenticate a user with email and encrypted password. "
            "Returns access and refresh JWT tokens. The password should be "
            "encrypted using the RSA public key obtained from the "
            "/public-key/ endpoint before sending. Returns user details "
            "including username, email, privilege, and verification status."
        ),
        responses={
            200: CustomTokenObtainPairSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Login",
                value={
                    "access": "eyJ0eXAiOiJKV1Qi...",
                    "refresh": "eyJ0eXAiOiJKV1Qi...",
                    "id": 1,
                    "username": "testuser",
                    "email": "testuser@example.com",
                    "is_staff": False,
                    "is_superuser": False,
                    "email_verified": True
                },
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Invalid Credentials",
                value={
                    "detail": "No active account found "
                              "with the given credentials"
                },
                response_only=True,
                status_codes=["401"]
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        """Handle POST request for user login."""
        return super().post(request, *args, **kwargs)


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id="manage_authenticated_user",
        summary="Get / Update Authenticated User Profile",
        description=(
            "Retrieve or update the profile of the currently authenticated "
            "user. GET returns the current user's details including username, "
            "email, and role. PUT/PATCH allows updating profile fields such "
            "as name, email, and password."
        ),
        responses={
            200: UserSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Response - GET",
                value={
                    "id": 1,
                    "username": "testuser",
                    "email": "testuser@example.com",
                    "image": None
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """Handle GET request for current user profile."""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        operation_id="update_authenticated_user",
        summary="Update Authenticated User Profile",
        description=(
            "Partially or fully update the profile of the currently "
            "authenticated user. Supports updating name, email, and password "
            "fields."
        ),
        responses={
            200: UserSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        }
    )
    def put(self, request, *args, **kwargs):
        """Handle PUT request to update current user profile."""
        return super().put(request, *args, **kwargs)

    @extend_schema(
        operation_id="partial_update_authenticated_user",
        summary="Partially Update Authenticated User Profile",
        description=(
            "Partially update the profile of the currently authenticated "
            "user. Only the provided fields will be updated."
        ),
        responses={
            200: UserSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        }
    )
    def patch(self, request, *args, **kwargs):
        """Handle PATCH request to partially update current user profile."""
        return super().patch(request, *args, **kwargs)

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
    permission_classes = [UserDetailPermission]

    @extend_schema(
        operation_id="get_user_detail",
        summary="Get User Details",
        description=(
            "Retrieve details for a specific user by ID. Requires "
            "appropriate permissions. Admin and staff users can access "
            "any user's details. Regular users can only access their own."
        ),
        responses={
            200: UserSerializer,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, *args, **kwargs):
        """Handle GET request for user details."""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        operation_id="update_user_detail",
        summary="Update User Details",
        description=(
            "Update details for a specific user by ID. Supports partial "
            "updates. Admin and staff users can update any user. Regular "
            "users can only update their own profile."
        ),
        responses={
            200: UserSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def put(self, request, *args, **kwargs):
        """Handle PUT request to update user details."""
        return super().put(request, *args, **kwargs)

    @extend_schema(
        operation_id="partial_update_user_detail",
        summary="Partially Update User Details",
        description=(
            "Partially update details for a specific user by ID. "
            "Only provided fields will be updated."
        ),
        responses={
            200: UserSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def patch(self, request, *args, **kwargs):
        """Handle PATCH request to partially update user details."""
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        operation_id="delete_user",
        summary="Delete User",
        description=(
            "Delete a specific user by ID. Requires appropriate permissions. "
            "Admin and staff users can delete any user."
        ),
        responses={
            204: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def delete(self, request, *args, **kwargs):
        """Handle DELETE request to remove a user."""
        return super().delete(request, *args, **kwargs)

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

    @extend_schema(
        operation_id="logout_user",
        summary="Logout User",
        description=(
            "Logout the authenticated user by blacklisting their refresh "
            "token. Requires the refresh token to be sent in the request "
            "body. After successful logout, the refresh token can no longer "
            "be used to obtain new access tokens."
        ),
        request=LogoutSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Logout",
                value={"message": "logout_Success"},
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Invalid Refresh Token",
                value={"detail": "refresh_token_not_valid"},
                response_only=True,
                status_codes=["400"]
            )
        ]
    )
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

    @extend_schema(
        operation_id="verify_email",
        summary="Verify Email Address",
        description="""
        Verify user's email address using a verification token sent to email.

        This endpoint accepts email and token in the request body.
        For security, it first validates the token, then checks
        if the email is already verified, and marks the user's
        email as verified if valid.
        """,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Verification",
                value={"message": "Email verified successfully. "
                       "You can now log in."},
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Already Verified",
                value={"message": "Email is already verified.",
                       "already_verified": True},
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Invalid Token",
                value={"error": "Invalid verification token."},
                response_only=True,
                status_codes=["400"]
            ),
            OpenApiExample(
                "Expired Token",
                value={"error": "Verification token has expired. "
                       "Please request a new one.",
                       "expired": True},
                response_only=True,
                status_codes=["400"]
            ),
        ]
    )
    def post(self, request):
        """Handle email verification."""
        email = request.data.get('email')
        token = request.data.get('token')

        # Validate required fields
        if not email:
            return Response(
                {'email': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not token:
            return Response(
                {'token': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            # SECURITY: Check token FIRST
            # (don't reveal verified status for wrong token)
            if user.verification_token != token:
                return Response(
                    {'error': 'Invalid verification token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if token is expired
            if user.is_verification_token_expired():
                return Response(
                    {
                        'error': 'Verification token has expired. '
                        'Please request a new one.',
                        'expired': True
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if email is already verified
            # (only after token is validated)
            if user.email_verified:
                return Response(
                    {
                        'message': 'Email is already verified.',
                        'already_verified': True
                    },
                    status=status.HTTP_200_OK
                )

            # Verify email
            # (token preserved for future "already verified" checks)
            user.verify_email(token)
            # Send welcome email
            send_welcome_email(user)
            return Response(
                {'message': 'Email verified successfully. '
                 'You can now log in.'},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            # Don't reveal if user exists or not
            return Response(
                {'error': 'Invalid verification token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationEmailView(generics.GenericAPIView):
    """Resend verification email."""
    serializer_class = EmailRequestSerializer

    @extend_schema(
        operation_id="resend_verification_email",
        summary="Resend Verification Email",
        description="""
        Resend email verification link to user's email address.

        This endpoint accepts an email address and sends a new verification
        email if the user exists and their email is not already verified.

        For security reasons, the response is the same whether the user exists
        or not.
        """,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Email Sent Successfully",
                value={"message": "Verification email sent successfully."},
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Email Already Verified",
                value={"message": "Email is already verified."},
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Generic Success Response (Security)",
                value={"message": "If an account exists with this email, "
                       "a verification email has been sent."},
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Invalid Email Format",
                value={"email": ["Enter a valid email address."]},
                response_only=True,
                status_codes=["400"]
            ),
        ]
    )
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
            verification_url = build_verification_url(
                request, token, email=user.email
            )

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

    @extend_schema(
        operation_id="request_password_reset",
        summary="Request Password Reset",
        description=(
            "Request a password reset email for verified users. "
            "This endpoint accepts an email address and sends a password "
            "reset link if the user exists and their email is verified. "
            "For security, unverified users receive an error message, and "
            "the response is the same whether a verified user exists or not."
        ),
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Password Reset Email Sent",
                value={"message": "Password reset email sent successfully."},
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Email Not Verified",
                value={"error":
                       "Please verify your email before resetting password."},
                response_only=True,
                status_codes=["400"]
            ),
            OpenApiExample(
                "Generic Success Response (Security)",
                value={"message": "If an account exists with this email, "
                       "a password reset email has been sent."},
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Invalid Email Format",
                value={"email": ["Enter a valid email address."]},
                response_only=True,
                status_codes=["400"]
            ),
        ]
    )
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

    @extend_schema(
        operation_id="reset_password",
        summary="Reset Password",
        description=(
            "Reset user's password using password reset token. "
            "The token is included in the URL path. This endpoint validates "
            "the token, checks if it's expired, and updates the user's "
            "password if valid. Requires new password and password "
            "confirmation in the request body."
        ),
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Password Reset Successful",
                value={"message": "Password reset successful. "
                       "You can now login with your new password."},
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Invalid Token",
                value={"error": "Invalid password reset token."},
                response_only=True,
                status_codes=["400"]
            ),
            OpenApiExample(
                "Expired Token",
                value={"error": "Invalid or expired password reset token."},
                response_only=True,
                status_codes=["400"]
            ),
            OpenApiExample(
                "Password Mismatch",
                value={"passwordRepeat": ["password_mismatch"]},
                response_only=True,
                status_codes=["400"]
            ),
            OpenApiExample(
                "Missing Password Fields",
                value={
                    "password": ["password_required"],
                    "passwordRepeat": ["password_repeat_null"]
                },
                response_only=True,
                status_codes=["400"]
            ),
        ]
    )
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


class SwitchRoleView(generics.GenericAPIView):
    """Switch the active role of the authenticated user.

    Superusers can switch between 'regular', 'staff', and 'superuser'.
    Staff users (auto-granted via 3 logins) can switch between
    'regular' and 'staff'.
    Regular users cannot switch roles.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id="switch_user_role",
        summary="Switch Active User Role",
        description=(
            "Switch the active role for the authenticated user. "
            "Superusers can switch between 'regular', 'staff', and "
            "'superuser'. Staff users can switch between 'regular' "
            "and 'staff'. Regular users cannot switch roles."
        ),
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'role': {
                        'type': 'string',
                        'enum': ['regular', 'staff', 'superuser'],
                        'description': 'Role to switch to'
                    }
                },
                'required': ['role']
            }
        },
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Switch",
                value={"active_role": "regular",
                       "message": "Switched to regular mode"},
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
    def post(self, request):
        """Handle POST request to switch active role."""
        role = request.data.get('role')
        user = request.user

        # Validate role value
        valid_roles = ['regular', 'staff']
        if user.is_superuser:
            valid_roles.append('superuser')

        if not role or role not in valid_roles:
            return Response(
                {'error': 'Invalid role. Must be one of: '
                 + ', '.join(valid_roles) + '.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is allowed to switch
        if (not user.is_superuser and
                not user.staff_access_granted):
            return Response(
                {'error': 'Staff access not yet granted. '
                 'Keep logging in to unlock staff access.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user.active_role = role
        user.save()

        return Response({
            'active_role': user.active_role,
            'message': f'Switched to {role} mode'
        }, status=status.HTTP_200_OK)


class PublicKeyView(APIView):
    """Return the RSA public key for login credential encryption."""

    permission_classes = []  # Public endpoint - no authentication required

    @extend_schema(
        operation_id="get_public_key",
        summary="Get RSA Public Key",
        description=(
            "Return the RSA public key in PEM format for encrypting "
            "login credentials before sending them to the server."
        ),
        responses={
            200: OpenApiTypes.OBJECT,
            503: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "public_key": "-----BEGIN PUBLIC KEY-----\n..."
                },
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Key Not Available",
                value={"error": "Public key not available."},
                response_only=True,
                status_codes=["503"]
            ),
        ]
    )
    def get(self, request):
        """Return the RSA public key in PEM format."""
        try:
            public_key_path = get_public_key_path()
            public_key = load_public_key(public_key_path)
            from cryptography.hazmat.primitives import serialization
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return Response(
                {'public_key': public_key_pem.decode('utf-8')},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Public key not available.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
