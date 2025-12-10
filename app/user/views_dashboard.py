"""Views for dashboard API endpoints."""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from datetime import datetime
from django.utils import timezone
from .permissions import IsStaffOrSuperUser
from .pagination import UserPagination
from .serializers_dashboard import (
    LoginActivitySerializer,
    UserStatsSerializer,
    AdminDashboardSerializer,
    ChartDataSerializer,
    get_user_stats,
    get_admin_dashboard_data,
    get_login_trends_data,
    get_login_comparison_data,
    get_login_distribution_data,
    get_admin_chart_data
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


# Chart Data API Views
class LoginTrendsView(generics.GenericAPIView):
    """API endpoint to get login trends data for line charts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChartDataSerializer

    def get(self, request):
        """Return login trends data for the authenticated user."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Convert string dates to datetime objects if provided
        try:
            if start_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d'))
            if end_date:
                end_date = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d'))
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        trends_data = get_login_trends_data(request.user, start_date, end_date)

        return Response({
            'login_trends': trends_data
        })


class LoginComparisonView(generics.GenericAPIView):
    """API endpoint to get login comparison data for bar charts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChartDataSerializer

    def get(self, request):
        """Return login comparison data for the authenticated user."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Convert string dates to datetime objects if provided
        try:
            if start_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d'))
            if end_date:
                end_date = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d'))
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        comparison_data = get_login_comparison_data(
            request.user, start_date, end_date)

        return Response({
            'login_comparison': comparison_data
        })


class LoginDistributionView(generics.GenericAPIView):
    """API endpoint to get login distribution data for pie charts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChartDataSerializer

    def get(self, request):
        """Return login distribution data for the authenticated user."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Convert string dates to datetime objects if provided
        try:
            if start_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d'))
            if end_date:
                end_date = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d'))
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        distribution_data = get_login_distribution_data(
            request.user, start_date, end_date)

        return Response({
            'login_distribution': distribution_data
        })


class AdminChartsView(generics.GenericAPIView):
    """API endpoint to get admin-level chart data."""
    permission_classes = [IsStaffOrSuperUser]
    serializer_class = ChartDataSerializer

    def get(self, request):
        """Return comprehensive chart data for administrators."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Convert string dates to datetime objects if provided
        try:
            if start_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d'))
            if end_date:
                end_date = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d'))
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        admin_chart_data = get_admin_chart_data(start_date, end_date)

        return Response({
            'admin_charts': admin_chart_data
        })
