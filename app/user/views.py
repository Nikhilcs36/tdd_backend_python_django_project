from rest_framework import generics, permissions
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from core.models import User
from .permissions import IsSuperUser, IsStaffOrSuperUser


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


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a user's details."""
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsSuperUser]
