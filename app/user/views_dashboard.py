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
    get_admin_chart_data,
    get_combined_login_trends_data,
    get_combined_login_comparison_data,
    get_combined_login_distribution_data
)
from core.models import LoginActivity
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


class UserStatsView(generics.GenericAPIView):
    """API endpoint to get user statistics."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserStatsSerializer

    @extend_schema(
        operation_id="get_user_statistics",
        summary="Get User Statistics",
        description=(
            "Retrieve comprehensive statistics for the authenticated user "
            "including total logins, last login timestamp, weekly/monthly "
            "data, and login trend percentage. Supports optional date "
            "filtering with start_date and end_date parameters."
        ),
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering statistics",
                required=False
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering statistics",
                required=False
            )
        ],
        responses={
            200: UserStatsSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "total_logins": 42,
                    "last_login": "2025-12-13 14:30:25",
                    "weekly_data": {
                        "2025-12-07": 5, "2025-12-08": 3, "2025-12-09": 7},
                    "monthly_data": {"2025-11": 15, "2025-12": 27},
                    "login_trend": 80
                },
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Successful Response with Date Filtering",
                value={
                    "total_logins": 15,
                    "last_login": "2025-12-10 14:30:25",
                    "weekly_data": {"2025-12-09": 5, "2025-12-10": 10},
                    "monthly_data": {"2025-12": 15},
                    "login_trend": 25
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
    def get(self, request):
        """Return comprehensive statistics for the authenticated user."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Convert string dates to datetime objects if provided
        if start_date or end_date:
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

        user_stats = get_user_stats(request.user, start_date, end_date)
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
        description=(
            "Retrieve paginated login activity history for the authenticated "
            "user including timestamps, IP addresses, user agents, and "
            "success status. Supports optional date filtering with "
            "start_date and end_date parameters."
        ),
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering activities (YYYY-MM-DD)",
                required=False
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering activities (YYYY-MM-DD)",
                required=False
            )
        ],
        responses={
            200: LoginActivitySerializer(many=True),
            400: OpenApiTypes.OBJECT,
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
                        "user_agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36"
                        ),
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
            ),
            OpenApiExample(
                "Successful Response with Date Filtering",
                value=[
                    {
                        "id": 125,
                        "username": "testuser",
                        "timestamp": "2025-12-12 14:30:25",
                        "ip_address": "192.168.1.102",
                        "user_agent": "Chrome/91.0",
                        "success": True
                    }
                ],
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
    def get(self, request):
        """Return paginated login activity history for the authenticated
        user."""
        return super().get(request)

    def get_queryset(self):
        """Return login activities for the authenticated user."""
        queryset = LoginActivity.objects.filter(user=self.request.user) \
            .select_related('user') \
            .order_by('-timestamp')

        # Apply date filtering if parameters are provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date or end_date:
            try:
                if start_date:
                    start_date = timezone.make_aware(
                        datetime.strptime(start_date, '%Y-%m-%d'))
                if end_date:
                    end_date = timezone.make_aware(
                        datetime.strptime(end_date, '%Y-%m-%d'))
            except ValueError:
                # Raise validation error for invalid date format
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    {'error': 'Invalid date format. Use YYYY-MM-DD format.'}
                )

            if start_date and end_date:
                queryset = queryset.filter(timestamp__range=(start_date, end_date))  # noqa: E501
            elif start_date:
                queryset = queryset.filter(timestamp__gte=start_date)
            elif end_date:
                queryset = queryset.filter(timestamp__lte=end_date)

        return queryset


class AdminDashboardView(generics.GenericAPIView):
    """API endpoint to get admin dashboard data."""
    permission_classes = [IsStaffOrSuperUser]
    serializer_class = AdminDashboardSerializer

    @extend_schema(
        operation_id="get_admin_dashboard",
        summary="Get Admin Dashboard Data",
        description=(
            "Retrieve comprehensive dashboard data for administrators "
            "including total users, active users, total logins, recent "
            "login activity, and user growth statistics. Supports various "
            "filtering options for dynamic statistics."
        ),
        parameters=[
            OpenApiParameter(
                name="user_ids[]",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description=(
                    "Array of user IDs to filter statistics (e.g., "
                    "user_ids[]=1&user_ids[]=2)"
                ),
                many=True,
                required=False
            ),
            OpenApiParameter(
                name="role",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter by user role: 'admin' or 'regular'"
                ),
                enum=["admin", "regular"],
                required=False
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering login activities (YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering login activities (YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="filter",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter users by type: 'all', 'admin_only', 'regular_users', "
                    "'active_only', 'me'"
                ),
                enum=["all", "admin_only", "regular_users", "active_only", "me"],
                required=False
            ),
            OpenApiParameter(
                name="me",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description=(
                    "Show only current authenticated user's data. "
                    "Available to admin users for debugging purposes."
                ),
                required=False
            )
        ],
        responses={
            200: AdminDashboardSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response - All Users",
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
                            "user_agent": (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36"
                            ),
                            "success": True
                        }
                    ],
                    "user_growth": {"2025-11": 25, "2025-12": 15}
                },
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Successful Response - Regular Users Only",
                value={
                    "total_users": 125,
                    "active_users": 100,
                    "total_logins": 1800,
                    "login_activity": [
                        {
                            "id": 124,
                            "username": "regular_user",
                            "timestamp": "2025-12-13 14:30:25",
                            "ip_address": "192.168.1.101",
                            "user_agent": "Chrome/91.0",
                            "success": True
                        }
                    ],
                    "user_growth": {"2025-11": 20, "2025-12": 10}
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
    def get(self, request):
        """Return comprehensive dashboard data for administrators."""
        role = request.query_params.get('role')
        me = request.query_params.get('me')
        user_ids = request.GET.getlist('user_ids[]')
        filter_type = request.query_params.get('filter')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Parse and validate dates if provided
        if start_date or end_date:
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

        # Validate parameters regardless of precedence
        # Validate role parameter if provided
        if role and role not in ['admin', 'regular']:
            return Response(
                {'error': 'Invalid role. Must be "admin" or "regular".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate filter parameter if provided
        if filter_type and filter_type not in ['all', 'admin_only', 'regular_users', 'active_only', 'me']:
            return Response(
                {'error': 'Invalid filter. Must be one of: all, admin_only, regular_users, active_only, me.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user_ids format if provided
        if user_ids is not None:
            try:
                user_ids = [int(uid) for uid in user_ids]
            except ValueError:
                return Response(
                    {'error': 'Invalid user_ids format. Must be integers.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate that users exist (only if user_ids is not empty)
            if user_ids:  # Empty list means no users selected
                users = User.objects.filter(id__in=user_ids)
                if len(users) != len(user_ids):
                    return Response(
                        {'error': 'One or more user IDs not found.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # Parameter precedence: me or filter=me > user_ids > role/filter_type
        if (me and me.lower() == 'true') or filter_type == 'me':
            dashboard_data = get_admin_dashboard_data(me=request.user, start_date=start_date, end_date=end_date)
        elif user_ids:
            # user_ids provided and not empty
            dashboard_data = get_admin_dashboard_data(user_ids=user_ids, start_date=start_date, end_date=end_date)
        else:
            dashboard_data = get_admin_dashboard_data(role=role, filter_type=filter_type, start_date=start_date, end_date=end_date)

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
        description=(
            "Retrieve login trends data for line charts showing successful "
            "and failed login attempts over time. Supports date filtering "
            "with optional start_date and end_date parameters. "
            "Supports user filtering with user_ids parameter for admin users. "
            "Supports role-based filtering with role parameter."
        ),
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering (YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering (YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="user_ids[]",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description=(
                    "Array of user IDs to get data for (e.g., "
                    "user_ids[]=1&user_ids[]=2). Requires admin "
                    "permissions."
                ),
                many=True,
                required=False
            ),
            OpenApiParameter(
                name="role",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter by user role: 'admin' or 'regular'. "
                    "Requires admin permissions."
                ),
                enum=["admin", "regular"],
                required=False
            ),
            OpenApiParameter(
                name="me",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description=(
                    "Show only current authenticated user's data. "
                    "Available to all authenticated users."
                ),
                required=False
            )
        ],
        responses={
            200: ChartDataSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response - Current User",
                value={
                    "login_trends": {
                        "labels": [
                            "2025-12-10", "2025-12-11", "2025-12-12",
                            "2025-12-13"
                        ],
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
            ),
            OpenApiExample(
                "Successful Response - Multiple Users (Admin)",
                value={
                    "login_trends": {
                        "labels": [
                            "2025-12-10", "2025-12-11", "2025-12-12",
                            "2025-12-13"
                        ],
                        "datasets": [
                            {
                                "label": "Successful Logins (Combined)",
                                "data": [24, 16, 30, 20],
                                "borderColor": "#4caf50",
                                "backgroundColor": "rgba(76, 175, 80, 0.1)"
                            },
                            {
                                "label": "Failed Logins (Combined)",
                                "data": [4, 2, 6, 0],
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
        """Return login trends data for the authenticated user or specified users."""  # noqa: E501
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        user_ids = request.GET.getlist('user_ids[]')
        role = request.query_params.get('role')

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

        # Check if role parameter is provided
        if role:
            # Validate admin permissions
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {'error': 'Admin permissions required to filter by role.'},  # noqa: E501
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate role parameter
            if role not in ['admin', 'regular']:
                return Response(
                    {'error': 'Invalid role. Must be "admin" or "regular".'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get users by role
            if role == 'admin':
                users = User.objects.filter(
                    Q(is_staff=True) | Q(is_superuser=True)
                )
            else:  # role == 'regular'
                users = User.objects.filter(
                    is_staff=False, is_superuser=False
                )

            # Get combined data for users with specified role
            trends_data = get_combined_login_trends_data(
                users, start_date, end_date)

        # Check if user_ids parameter is provided
        elif user_ids:
            # Validate admin permissions
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {'error': 'Admin permissions required to filter by user IDs.'},  # noqa: E501
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate user_ids format
            try:
                user_ids = [int(uid) for uid in user_ids]
            except ValueError:
                return Response(
                    {'error': 'Invalid user_ids format. Must be integers.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get users and check access permissions
            users = User.objects.filter(id__in=user_ids)
            if len(users) != len(user_ids):
                return Response(
                    {'error': 'One or more user IDs not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get combined data for specified users
            trends_data = get_combined_login_trends_data(
                users, start_date, end_date)
        else:
            # Default: current user's data
            trends_data = get_login_trends_data(
                request.user, start_date, end_date)

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
        description=(
            "Retrieve login comparison data for bar charts showing login "
            "counts by week or month. Automatically adjusts timeframe based "
            "on date range. Supports date filtering with optional start_date "
            "and end_date parameters. Supports user filtering with user_ids "
            "parameter for admin users. Supports role-based filtering with "
            "role parameter for admin users."
        ),
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering (YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering (YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="user_ids[]",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description=(
                    "Array of user IDs to get data for (e.g., "
                    "user_ids[]=1&user_ids[]=2). Requires admin "
                    "permissions."
                ),
                many=True,
                required=False
            ),
            OpenApiParameter(
                name="role",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter by user role: 'admin' or 'regular'. "
                    "Requires admin permissions."
                ),
                enum=["admin", "regular"],
                required=False
            ),
            OpenApiParameter(
                name="me",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description=(
                    "Show only current authenticated user's data. "
                    "Available to all authenticated users."
                ),
                required=False
            )
        ],
        responses={
            200: ChartDataSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response - Current User",
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
            ),
            OpenApiExample(
                "Successful Response - Multiple Users (Admin)",
                value={
                    "login_comparison": {
                        "labels": ["Week 49", "Week 50", "Week 51"],
                        "datasets": [
                            {
                                "label": "Login Count (Combined)",
                                "data": [50, 64, 56],
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
        """Return login comparison data for the authenticated user or specified users."""  # noqa: E501
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        user_ids = request.GET.getlist('user_ids[]')
        role = request.query_params.get('role')

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

        # Check if role parameter is provided
        if role:
            # Validate admin permissions
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {'error': 'Admin permissions required to filter by role.'},  # noqa: E501
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate role parameter
            if role not in ['admin', 'regular']:
                return Response(
                    {'error': 'Invalid role. Must be "admin" or "regular".'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get users by role
            if role == 'admin':
                users = User.objects.filter(
                    Q(is_staff=True) | Q(is_superuser=True)
                )
            else:  # role == 'regular'
                users = User.objects.filter(
                    is_staff=False, is_superuser=False
                )

            # Get combined data for users with specified role
            comparison_data = get_combined_login_comparison_data(
                users, start_date, end_date)

        # Check if user_ids parameter is provided
        elif user_ids:
            # Validate admin permissions
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {'error': 'Admin permissions required to filter by user IDs.'},  # noqa: E501
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate user_ids format
            try:
                user_ids = [int(uid) for uid in user_ids]
            except ValueError:
                return Response(
                    {'error': 'Invalid user_ids format. Must be integers.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get users and check access permissions
            users = User.objects.filter(id__in=user_ids)
            if len(users) != len(user_ids):
                return Response(
                    {'error': 'One or more user IDs not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get combined data for specified users
            comparison_data = get_combined_login_comparison_data(
                users, start_date, end_date)
        else:
            # Default: current user's data
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
        description=(
            "Retrieve login distribution data for pie charts showing "
            "success/failure ratio and user agent distribution. Supports "
            "date filtering with optional start_date and end_date parameters. "
            "Supports user filtering with user_ids parameter for admin users. "
            "Supports role-based filtering with role parameter."
        ),
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
            ),
            OpenApiParameter(
                name="user_ids[]",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description=(
                    "Array of user IDs to get data for (e.g., "
                    "user_ids[]=1&user_ids[]=2). Requires admin "
                    "permissions."
                ),
                many=True,
                required=False
            ),
            OpenApiParameter(
                name="role",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter by user role: 'admin' or 'regular'. "
                    "Requires admin permissions."
                ),
                enum=["admin", "regular"],
                required=False
            ),
            OpenApiParameter(
                name="me",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description=(
                    "Show only current authenticated user's data. "
                    "Available to all authenticated users."
                ),
                required=False
            )
        ],
        responses={
            200: ChartDataSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response - Current User",
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
                                    "backgroundColor": [
                                        "#2196f3", "#4caf50", "#ff9800"
                                    ]
                                }
                            ]
                        }
                    }
                },
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Successful Response - Multiple Users (Admin)",
                value={
                    "login_distribution": {
                        "success_ratio": {
                            "labels": ["Successful", "Failed"],
                            "datasets": [
                                {
                                    "data": [170, 30],
                                    "backgroundColor": ["#4caf50", "#f44336"]
                                }
                            ]
                        },
                        "user_agents": {
                            "labels": ["Chrome", "Firefox", "Safari"],
                            "datasets": [
                                {
                                    "data": [120, 50, 30],
                                    "backgroundColor": [
                                        "#2196f3", "#4caf50", "#ff9800"
                                    ]
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
        """Return login distribution data for the authenticated user or specified users."""  # noqa: E501
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        user_ids = request.GET.getlist('user_ids[]')
        role = request.query_params.get('role')

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

        # Check if role parameter is provided
        if role:
            # Validate admin permissions
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {'error': 'Admin permissions required to filter by role.'},  # noqa: E501
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate role parameter
            if role not in ['admin', 'regular']:
                return Response(
                    {'error': 'Invalid role. Must be "admin" or "regular".'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get users by role
            if role == 'admin':
                users = User.objects.filter(
                    Q(is_staff=True) | Q(is_superuser=True)
                )
            else:  # role == 'regular'
                users = User.objects.filter(
                    is_staff=False, is_superuser=False
                )

            # Get combined data for users with specified role
            distribution_data = get_combined_login_distribution_data(
                users, start_date, end_date)

        # Check if user_ids parameter is provided
        elif user_ids:
            # Validate admin permissions
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {'error': 'Admin permissions required to filter by user IDs.'},  # noqa: E501
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate user_ids format
            try:
                user_ids = [int(uid) for uid in user_ids]
            except ValueError:
                return Response(
                    {'error': 'Invalid user_ids format. Must be integers.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get users and check access permissions
            users = User.objects.filter(id__in=user_ids)
            if len(users) != len(user_ids):
                return Response(
                    {'error': 'One or more user IDs not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get combined data for specified users
            distribution_data = get_combined_login_distribution_data(
                users, start_date, end_date)
        else:
            # Default: current user's data
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
        description=(
            "Retrieve comprehensive admin-level chart data including user "
            "growth trends, daily login activity, and success ratio "
            "statistics. Supports date filtering with optional start_date "
            "and end_date parameters."
        ),
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering (YYYY-MM-DD)"
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering (YYYY-MM-DD)"
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
                            "labels": [
                                "2025-12-10", "2025-12-11", "2025-12-12"
                            ],
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


def check_user_access(request, target_user_id):
    """
    Check if the requesting user has access to the target user's data.
    Users can access their own data, admins/staff can access any user's data.

    Args:
        request: The HTTP request object
        target_user_id: ID of the user whose data is being accessed

    Returns:
        bool: True if access is granted, False otherwise
    """
    if request.user.id == target_user_id:
        return True  # User accessing own data
    if request.user.is_staff or request.user.is_superuser:
        return True  # Admin accessing user data
    return False  # Unauthorized access


class UserSpecificStatsView(generics.GenericAPIView):
    """
    API endpoint to get user login activity with role-based access control.
    Provides paginated login activity history for a specific user with proper
    authorization. Users can access their own data, admins can access any
    user's data.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserStatsSerializer

    @extend_schema(
        operation_id="get_user_specific_statistics",
        summary="Get User Statistics (Role-Based)",
        description=(
            "Retrieve comprehensive statistics for a specific user. Users "
            "can access their own data, admins/staff can access any user's "
            "data. Requires user_id path parameter."
        ),
        responses={
            200: UserStatsSerializer,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "total_logins": 42,
                    "last_login": "2025-12-13 14:30:25",
                    "weekly_data": {
                        "2025-12-07": 5, "2025-12-08": 3, "2025-12-09": 7},
                    "monthly_data": {"2025-11": 15, "2025-12": 27},
                    "login_trend": 80
                },
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Permission Denied",
                value={
                    "error": "You do not have permission to access this user's data"  # noqa: E501
                },
                response_only=True,
                status_codes=["403"]
            ),
            OpenApiExample(
                "User Not Found",
                value={"error": "User not found"},
                response_only=True,
                status_codes=["404"]
            )
        ]
    )
    def get(self, request, user_id):
        """
        Return comprehensive statistics for a specific user with access control.  # noqa: E501

        Args:
            request: HTTP request object
            user_id: ID of the target user

        Returns:
            Response: User statistics data or error response
        """
        # Authorization check - ensure user has permission to access this data
        if not check_user_access(request, user_id):
            raise PermissionDenied(
                "You do not have permission to access this user's data")

        # Get user object or return 404 if not found
        user = get_object_or_404(User, id=user_id)

        # Retrieve statistics using existing get_user_stats function
        user_stats = get_user_stats(user)

        # Serialize and return data
        serializer = self.get_serializer(user_stats)
        return Response(serializer.data)


class UserSpecificLoginActivityView(generics.ListAPIView):
    """
    API endpoint to get user login activity with role-based access control.
    Provides paginated login activity history for a specific user with proper
    authorization. Users can access their own data, admins can access any
    user's data.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoginActivitySerializer
    pagination_class = UserPagination

    @extend_schema(
        operation_id="get_user_specific_login_activity",
        summary="Get Login Activity History (Role-Based)",
        description=(
            "Retrieve paginated login activity history for a specific user. "
            "Users can access their own data, admins/staff can access any "
            "user's data. Supports pagination with page and size parameters."  # noqa: E501
        ),
        responses={
            200: LoginActivitySerializer(many=True),
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "count": 42,
                    "next": (
                        "http://localhost:8000/api/user/123/dashboard/"
                        "login-activity/?page=2&size=10"
                    ),
                    "previous": None,
                    "results": [
                        {
                            "id": 123,
                            "username": "testuser",
                            "timestamp": "2025-12-13 14:30:25",
                            "ip_address": "192.168.1.100",
                            "user_agent": (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36"
                            ),
                            "success": True
                        }
                    ]
                },
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Permission Denied",
                value={
                    "error": "You do not have permission to access this user's data"  # noqa: E501
                },
                response_only=True,
                status_codes=["403"]
            ),
            OpenApiExample(
                "User Not Found",
                value={"error": "User not found"},
                response_only=True,
                status_codes=["404"]
            )
        ]
    )
    def get(self, request, user_id):
        """
        Return paginated login activity history for a specific user with access
        control.

        Args:
            request: HTTP request object
            user_id: ID of the target user

        Returns:
            Response: Paginated login activity data or error response
        """
        # Authorization check - ensure user has permission to access this data
        if not check_user_access(request, user_id):
            raise PermissionDenied(
                "You do not have permission to access this user's data")

        # Get user object or return 404 if not found
        user = get_object_or_404(User, id=user_id)

        # Retrieve login activities for the user
        activities = LoginActivity.objects.filter(user=user)

        # Apply pagination
        paginator = self.pagination_class()
        page_obj = paginator.paginate_queryset(activities, request)

        # Serialize and return paginated response
        serializer = self.get_serializer(page_obj, many=True)

        return paginator.get_paginated_response(serializer.data)


class AdminUsersStatsView(generics.GenericAPIView):
    """
    API endpoint to get batch statistics for multiple users (admin only).
    Provides comprehensive statistics for multiple users with filtering
    capabilities. Supports filtering by user IDs and active status.
    """
    permission_classes = [IsStaffOrSuperUser]
    serializer_class = UserStatsSerializer

    @extend_schema(
        operation_id="get_admin_users_statistics",
        summary="Get Batch User Statistics (Admin Only)",
        description=(
            "Retrieve comprehensive statistics for multiple users. Supports "
            "filtering by user IDs and active status. Returns a dictionary "
            "with user IDs as keys and their statistics as values."  # noqa: E501
        ),
        parameters=[
            OpenApiParameter(
                name="user_ids[]",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description=(
                    "Array of user IDs to get statistics for (e.g., "
                    "user_ids[]=1&user_ids[]=2)"
                ),
                many=True
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter by active status (true/false). When not "
                    "specified, returns all users."
                )
            )
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Response - Specific Users",
                value={
                    "1": {
                        "total_logins": 42,
                        "last_login": "2025-12-13 14:30:25",
                        "weekly_data": {
                            "2025-12-07": 5, "2025-12-08": 3,
                            "2025-12-09": 7
                        },
                        "monthly_data": {"2025-11": 15, "2025-12": 27},
                        "login_trend": 80
                    },
                    "2": {
                        "total_logins": 25,
                        "last_login": "2025-12-12 10:15:30",
                        "weekly_data": {
                            "2025-12-07": 2, "2025-12-08": 4,
                            "2025-12-09": 3
                        },
                        "monthly_data": {"2025-11": 12, "2025-12": 13},
                        "login_trend": 65
                    }
                },
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Successful Response - Active Users Only",
                value={
                    "1": {
                        "total_logins": 42,
                        "last_login": "2025-12-13 14:30:25",
                        "weekly_data": {
                            "2025-12-07": 5, "2025-12-08": 3,
                            "2025-12-09": 7
                        },
                        "monthly_data": {"2025-11": 15, "2025-12": 27},
                        "login_trend": 80
                    }
                },
                response_only=True,
                status_codes=["200"]
            ),
            OpenApiExample(
                "Permission Denied",
                value={
                    "error": "You do not have permission to access this endpoint"  # noqa: E501
                },
                response_only=True,
                status_codes=["403"]
            ),
            OpenApiExample(
                "Invalid Parameters",
                value={"error": "Invalid user_ids format. Must be integers."},
                response_only=True,
                status_codes=["400"]
            )
        ]
    )
    def get(self, request):
        """
        Return batch statistics for multiple users with filtering.

        Args:
            request: HTTP request object

        Returns:
            Response: Dictionary of user statistics or error response
        """
        # Get query parameters
        user_ids = request.GET.getlist('user_ids[]')
        is_active = request.GET.get('is_active')

        # Build query filters using Django Q objects
        filters = Q()

        # Filter by specific user IDs if provided
        if user_ids:
            try:
                user_ids = [int(uid) for uid in user_ids]
                filters &= Q(id__in=user_ids)
            except ValueError:
                return Response(
                    {"error": "Invalid user_ids format. Must be integers."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Filter by active status if provided
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            filters &= Q(is_active=is_active_bool)

        # Get users with applied filters
        users = User.objects.filter(filters)

        # Get stats for each user using existing get_user_stats function
        stats_data = {}
        for user in users:
            stats_data[str(user.id)] = get_user_stats(user)

        return Response(stats_data)
