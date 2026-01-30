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
    LogoutSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from core.models import User
from .permissions import IsSuperUser, IsStaffOrSuperUser
from .pagination import UserPagination


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer


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
        context['include_roles'] = True  # Tell serializer to include role fields  # noqa: E501
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
