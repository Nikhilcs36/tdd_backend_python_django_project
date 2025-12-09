"""Views for dashboard API endpoints."""
from rest_framework import generics, permissions
from rest_framework.response import Response
from .permissions import IsStaffOrSuperUser
from .pagination import UserPagination
from .serializers_dashboard import (
    LoginActivitySerializer,
    UserStatsSerializer,
    AdminDashboardSerializer,
    get_user_stats,
    get_admin_dashboard_data
)
from core.models import LoginActivity


class UserStatsView(generics.GenericAPIView):
    """API endpoint to get user statistics."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserStatsSerializer

    def get(self, request):
        """Return comprehensive statistics for the authenticated user."""
        user_stats = get_user_stats(request.user)
        serializer = self.get_serializer(user_stats)
        return Response(serializer.data)


class LoginActivityView(generics.ListAPIView):
    """API endpoint to get user login activity."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoginActivitySerializer
    pagination_class = UserPagination

    def get_queryset(self):
        """Return login activities for the authenticated user."""
        return LoginActivity.objects.filter(user=self.request.user) \
            .select_related('user') \
            .order_by('-timestamp')


class AdminDashboardView(generics.GenericAPIView):
    """API endpoint to get admin dashboard data."""
    permission_classes = [IsStaffOrSuperUser]
    serializer_class = AdminDashboardSerializer

    def get(self, request):
        """Return comprehensive dashboard data for administrators."""
        dashboard_data = get_admin_dashboard_data()
        serializer = self.get_serializer(dashboard_data)
        return Response(serializer.data)
