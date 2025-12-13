"""Views for dashboard API endpoints."""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from datetime import datetime
from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample
)
from drf_spectacular.types import OpenApiTypes
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

    @extend_schema(
        operation_id="get_user_statistics",
        summary="Get User Statistics",
        description="Retrieve comprehensive statistics for the authenticated user including total logins, last login timestamp, weekly/monthly data, and login trend percentage.",
        responses={
            200: UserStatsSerializer,
            401: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "total_logins": 42,
                    "last_login": "2025-12-13 14:30:25",
                    "weekly_data": {"2025-12-07": 5, "2025-12-08": 3, "2025-12-09": 7},
                    "monthly_data": {"2025-11": 15, "2025-12": 27},
                    "login_trend": 80
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
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

    @extend_schema(
        operation_id="get_login_activity",
        summary="Get Login Activity History",
        description="Retrieve paginated login activity history for the authenticated user including timestamps, IP addresses, user agents, and success status.",
        responses={
            200: LoginActivitySerializer(many=True),
            401: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value=[
                    {
                        "id": 123,
                        "username": "testuser",
                        "timestamp": "2025-12-13 14:30:25",
                        "ip_address": "192.168.1.100",
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "success": True
                    },
                    {
                        "id": 124,
                        "username": "testuser",
                        "timestamp": "2025-12-13 10:15:30",
                        "ip_address": "192.168.1.101",
                        "user_agent": "PostmanRuntime/7.36.0",
                        "success": False
                    }
                ],
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
    def get(self, request):
        """Return paginated login activity history for the authenticated user."""
        return super().get(request)

    def get_queryset(self):
        """Return login activities for the authenticated user."""
        return LoginActivity.objects.filter(user=self.request.user) \
            .select_related('user') \
            .order_by('-timestamp')


class AdminDashboardView(generics.GenericAPIView):
    """API endpoint to get admin dashboard data."""
    permission_classes = [IsStaffOrSuperUser]
    serializer_class = AdminDashboardSerializer

    @extend_schema(
        operation_id="get_admin_dashboard",
        summary="Get Admin Dashboard Data",
        description="Retrieve comprehensive dashboard data for administrators including total users, active users, total logins, recent login activity, and user growth statistics.",
        responses={
            200: AdminDashboardSerializer,
            403: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "total_users": 150,
                    "active_users": 125,
                    "total_logins": 2540,
                    "login_activity": [
                        {
                            "id": 123,
                            "username": "admin",
                            "timestamp": "2025-12-13 14:30:25",
                            "ip_address": "192.168.1.100",
                            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "success": True
                        }
                    ],
                    "user_growth": {"2025-11": 25, "2025-12": 15}
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
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

    @extend_schema(
        operation_id="get_login_trends",
        summary="Get Login Trends Data",
        description="Retrieve login trends data for line charts showing successful and failed login attempts over time. Supports date filtering with optional start_date and end_date parameters.",
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering (format: YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering (format: YYYY-MM-DD)"
            )
        ],
        responses={
            200: ChartDataSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "login_trends": {
                        "labels": ["2025-12-10", "2025-12-11", "2025-12-12", "2025-12-13"],
                        "datasets": [
                            {
                                "label": "Successful Logins",
                                "data": [12, 8, 15, 10],
                                "borderColor": "#4caf50",
                                "backgroundColor": "rgba(76, 175, 80, 0.1)"
                            },
                            {
                                "label": "Failed Logins",
                                "data": [2, 1, 3, 0],
                                "borderColor": "#f44336",
                                "backgroundColor": "rgba(244, 67, 54, 0.1)"
                            }
                        ]
                    }
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
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

    @extend_schema(
        operation_id="get_login_comparison",
        summary="Get Login Comparison Data",
        description="Retrieve login comparison data for bar charts showing login counts by week or month. Automatically adjusts timeframe based on date range. Supports date filtering with optional start_date and end_date parameters.",
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering (format: YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering (format: YYYY-MM-DD)"
            )
        ],
        responses={
            200: ChartDataSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "login_comparison": {
                        "labels": ["Week 49", "Week 50", "Week 51"],
                        "datasets": [
                            {
                                "label": "Login Count",
                                "data": [25, 32, 28],
                                "backgroundColor": "#2196f3"
                            }
                        ]
                    }
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
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

    @extend_schema(
        operation_id="get_login_distribution",
        summary="Get Login Distribution Data",
        description="Retrieve login distribution data for pie charts showing success/failure ratio and user agent distribution. Supports date filtering with optional start_date and end_date parameters.",
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering (format: YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering (format: YYYY-MM-DD)"
            )
        ],
        responses={
            200: ChartDataSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "login_distribution": {
                        "success_ratio": {
                            "labels": ["Successful", "Failed"],
                            "datasets": [
                                {
                                    "data": [85, 15],
                                    "backgroundColor": ["#4caf50", "#f44336"]
                                }
                            ]
                        },
                        "user_agents": {
                            "labels": ["Chrome", "Firefox", "Safari"],
                            "datasets": [
                                {
                                    "data": [60, 25, 15],
                                    "backgroundColor": ["#2196f3", "#4caf50", "#ff9800"]
                                }
                            ]
                        }
                    }
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
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

    @extend_schema(
        operation_id="get_admin_charts",
        summary="Get Admin Charts Data",
        description="Retrieve comprehensive admin-level chart data including user growth trends, daily login activity, and success ratio statistics. Supports date filtering with optional start_date and end_date parameters.",
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering (format: YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering (format: YYYY-MM-DD)"
            )
        ],
        responses={
            200: ChartDataSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "admin_charts": {
                        "user_growth": {
                            "labels": ["2025-11", "2025-12"],
                            "datasets": [
                                {
                                    "label": "New Users",
                                    "data": [25, 15],
                                    "borderColor": "#2196f3"
                                }
                            ]
                        },
                        "login_activity": {
                            "labels": ["2025-12-10", "2025-12-11", "2025-12-12"],
                            "datasets": [
                                {
                                    "label": "Daily Logins",
                                    "data": [120, 95, 150],
                                    "borderColor": "#4caf50"
                                }
                            ]
                        },
                        "success_ratio": {
                            "labels": ["Successful", "Failed"],
                            "datasets": [
                                {
                                    "data": [2400, 140],
                                    "backgroundColor": ["#4caf50", "#f44336"]
                                }
                            ]
                        }
                    }
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
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
