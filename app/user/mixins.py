"""Shared mixins and utility functions for dashboard and report views."""
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class DateFilterMixin:
    """Mixin providing date filtering functionality for API views."""

    def get_date_filters(self, request):
        """Extract and validate date filters from request.

        Returns:
            tuple: (start_date, end_date) - both can be None if not provided
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date or end_date:
            try:
                if start_date:
                    start_date = timezone.make_aware(
                        datetime.strptime(start_date, '%Y-%m-%d'),
                        timezone=timezone.utc)
                if end_date:
                    end_date = timezone.make_aware(
                        datetime.strptime(end_date, '%Y-%m-%d'),
                        timezone=timezone.utc)
                    # Make end_date inclusive of the full day
                    end_date = end_date.replace(
                        hour=23, minute=59, second=59, microsecond=999999
                    )
            except ValueError:
                raise ValidationError(
                    {'error': 'Invalid date format. Use YYYY-MM-DD format.'}
                )

        return start_date, end_date


def filter_users_by_role(role):
    """
    Filter users by role.

    Args:
        role: 'admin' or 'regular'

    Returns:
        QuerySet of User objects
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if role == 'admin':
        return User.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True)
        )
    else:  # role == 'regular'
        return User.objects.filter(
            is_staff=False, is_superuser=False
        )


def parse_and_validate_user_ids(user_ids, require_admin=True, request=None):
    """
    Parse and validate user_ids[] parameter.

    Args:
        user_ids: List of user ID strings from request.GET.getlist()
        require_admin: If True, the calling code must handle admin check
        request: Optional request object for admin check

    Returns:
        tuple: (users_list, error_response_or_None)
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Check admin permission if request is provided
    if request and require_admin:
        is_admin = request.user.is_staff or request.user.is_superuser
        if not is_admin:
            return None, Response(
                {'error': 'Only admin users can specify user IDs.'},
                status=status.HTTP_403_FORBIDDEN
            )

    try:
        user_ids = [int(uid) for uid in user_ids]
    except ValueError:
        return None, Response(
            {'error': 'Invalid user_ids format. Must be integers.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    users = list(User.objects.filter(id__in=user_ids))
    if len(users) != len(user_ids):
        return None, Response(
            {'error': 'One or more user IDs not found.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return users, None


def get_filtered_login_activities(
    users, start_date=None, end_date=None, limit=None
):
    """
    Get login activities for specified users with optional date filtering.

    Args:
        users: Single User object or list of User objects
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        limit: Optional max number of records to return

    Returns:
        list of dicts with login activity data
    """
    from core.models import LoginActivity
    from django.utils import timezone

    if not isinstance(users, (list, tuple)):
        users = [users]

    queryset = LoginActivity.objects.filter(
        user__in=users
    ).select_related('user').order_by('-timestamp')

    if start_date and end_date:
        queryset = queryset.filter(timestamp__range=(start_date, end_date))
    elif start_date:
        queryset = queryset.filter(timestamp__gte=start_date)
    elif end_date:
        queryset = queryset.filter(timestamp__lte=end_date)

    if limit:
        queryset = queryset[:limit]

    return [
        {
            'id': activity.id,
            'username': activity.user.username,
            'timestamp': timezone.localtime(
                activity.timestamp
            ).strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': activity.ip_address,
            'user_agent': activity.user_agent,
            'success': activity.success,
        }
        for activity in queryset
    ]
