"""Views for report download API endpoints."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .mixins import (
    DateFilterMixin,
    filter_users_by_role,
    parse_and_validate_user_ids,
)
from .reports import (
    ReportDataCollector, ExcelReportGenerator
)

User = get_user_model()


class ReportDownloadView(DateFilterMixin, APIView):
    """
    API endpoint to download login tracking summary report.

    Supports Excel format with professional formatting.
    Individual and grouped modes available.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id="download_login_report",
        summary="Download Login Activity Summary Report",
        description=(
            "Download a comprehensive login activity summary report in "
            "Excel format. Supports individual mode (single user data) "
            "and grouped mode (combined data for multiple users). Regular "
            "users can only download their own report in individual mode. "
            "Admin users can download reports for any user or group of users."
        ),
        parameters=[
            OpenApiParameter(
                name="mode",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Report mode: 'individual' (single user) or 'grouped' "
                    "(multiple users combined)"
                ),
                required=True,
                enum=["individual", "grouped"]
            ),
            OpenApiParameter(
                name="user_ids[]",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description=(
                    "Array of user IDs for report (admin only). In "
                    "individual mode, uses first user. In grouped mode, "
                    "uses all users."
                ),
                many=True,
                required=False
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for filtering (YYYY-MM-DD)",
                required=False
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for filtering (YYYY-MM-DD)",
                required=False
            ),
            OpenApiParameter(
                name="filter",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter users by type: 'all', 'admin_only', "
                    "'regular_users', 'me'. Requires admin permissions "
                    "for non-'me' filters."
                ),
                enum=["all", "admin_only", "regular_users", "me"],
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
        ],
        responses={
            200: OpenApiTypes.BINARY,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Excel Download Success",
                value=b"PK...",
                response_only=True,
                status_codes=["200"],
                media_type=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                )
            ),
            OpenApiExample(
                "Feature Disabled Error",
                value={
                    "error": "Report download is currently disabled."
                },
                response_only=True,
                status_codes=["403"]
            ),
        ]
    )
    def get(self, request):
        """Handle GET request for report download."""
        # Get and validate parameters
        mode = request.query_params.get('mode')
        user_ids = request.GET.getlist('user_ids[]')
        filter_type = request.query_params.get('filter')
        role = request.query_params.get('role')
        selected_user_id = request.query_params.get('selected_user_id')

        # Check feature flag
        if not getattr(settings, 'ENABLE_REPORT_DOWNLOAD', True):
            return Response(
                {'error': 'Report download is currently disabled.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate mode parameter
        if not mode:
            return Response(
                {'error': "Missing required parameter: 'mode'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if mode not in ['individual', 'grouped']:
            return Response(
                {
                    'error': "Invalid mode. "
                             "Must be 'individual' or 'grouped'."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check permissions for grouped mode
        is_admin = request.user.is_staff or request.user.is_superuser
        if mode == 'grouped' and not is_admin:
            return Response(
                {'error': 'Only admin users can use grouped mode.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate filter parameter
        valid_filters = ['all', 'admin_only', 'regular_users', 'me']
        if filter_type and filter_type not in valid_filters:
            return Response(
                {'error': (
                    f"Invalid filter. Must be one of: "
                    f"{', '.join(valid_filters)}."
                )},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate role parameter
        valid_roles = ['admin', 'regular']
        if role and role not in valid_roles:
            return Response(
                {'error': (
                    f"Invalid role. Must be one of: "
                    f"{', '.join(valid_roles)}."
                )},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check permissions for role filter
        if role and not is_admin:
            return Response(
                {'error': 'Admin permissions required to filter by role.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check permissions for non-'me' filter
        if filter_type and filter_type != 'me' and not is_admin:
            return Response(
                {'error': 'Admin permissions required for this filter.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Parse date parameters
        try:
            start_date, end_date = self.get_date_filters(request)
        except Exception:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Determine users for the report
        users, error_response = self._get_users(
            request, mode, user_ids, is_admin, filter_type, role
        )
        if error_response:
            return error_response

        # Determine filter info for report
        filter_info = self._build_filter_info(
            user_ids, mode, filter_type, role
        )

        # Resolve selected_user if selected_user_id is provided
        selected_user = None
        if selected_user_id is not None:
            try:
                selected_user_id = int(selected_user_id)
            except (ValueError, TypeError):
                return Response(
                    {
                        'error': 'Invalid selected_user_id. '
                                 'Must be an integer.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                selected_user = User.objects.get(id=selected_user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Selected user not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ensure selected_user is part of the users list
            if selected_user not in users:
                return Response(
                    {
                        'error': 'Selected user must be one of '
                                 'the report users.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Collect report data
        collector = ReportDataCollector(
            users=users,
            start_date=start_date,
            end_date=end_date,
            mode=mode,
            filter_info=filter_info,
            requesting_user=request.user,
            selected_user=selected_user
        )
        report_data = collector.collect_all_data()

        # Generate Excel report
        return self._generate_excel(report_data, mode, users)

    def _get_users(self, request, mode, user_ids, is_admin,
                   filter_type=None, role=None):
        """
        Get users for the report based on parameters and permissions.

        Supports filter and role parameters for admin filtering
        matching dashboard functionality.

        Returns:
            tuple: (users list, error_response or None)
        """
        # Prioritize user_ids parameter
        if user_ids:
            users, error_response = parse_and_validate_user_ids(
                user_ids, require_admin=False, request=request
            )
            if error_response:
                return None, error_response

            if mode == 'individual':
                users = [users[0]]
            return users, None

        # Handle filter parameter
        if filter_type:
            if filter_type == 'me':
                return [request.user], None

            if filter_type == 'admin_only':
                users = list(filter_users_by_role('admin'))
            elif filter_type == 'regular_users':
                users = list(filter_users_by_role('regular'))
            elif filter_type == 'all':
                users = list(User.objects.all())
            else:
                return [request.user], None

            if mode == 'individual' and users:
                users = [users[0]]
            return users, None

        # Handle role parameter
        if role:
            users = list(filter_users_by_role(role))

            if mode == 'individual' and users:
                users = [users[0]]
            return users, None

        # Default behavior: grouped for admin, individual for regular
        if mode == 'grouped' and is_admin:
            users = list(User.objects.all())
        else:
            users = [request.user]

        return users, None

    def _build_filter_info(self, user_ids, mode, filter_type, role):
        """Build filter info dict for report context."""
        filter_info = {}
        if user_ids:
            filter_info['type'] = 'user_ids'
        elif filter_type:
            filter_info['type'] = filter_type
        elif mode == 'grouped':
            filter_info['type'] = 'all'
        # If filter_type was explicitly provided (dashboard filter),
        # use it instead of user_ids so Excel shows the dashboard context
        if filter_type:
            filter_info['type'] = filter_type
        if role:
            filter_info['role'] = role
        return filter_info

    def _generate_excel(self, report_data, mode, users):
        """Generate and return Excel report."""
        generator = ExcelReportGenerator(report_data)
        excel_content = generator.generate()

        if mode == 'individual' and users:
            filename = f"login_report_{users[0].username}_individual"
        else:
            filename = f"login_report_grouped_{len(users)}_users"

        filename += f"_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        response = HttpResponse(
            excel_content,
            content_type=(
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{filename}"'
        )
        return response
