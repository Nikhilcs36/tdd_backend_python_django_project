from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
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
    """List all users."""
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsStaffOrSuperUser]
    pagination_class = UserPagination  # Enable pagination


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
