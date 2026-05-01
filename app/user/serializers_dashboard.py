"""Serializers for dashboard API with TypeScript-friendly responses."""
from typing import Optional

from rest_framework import serializers
from core.models import LoginActivity, User
from datetime import timedelta
from django.utils import timezone
from collections import defaultdict
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth


class LoginActivitySerializer(serializers.ModelSerializer):
    """Serializer for login activity data."""

    timestamp = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = LoginActivity
        fields = (
            'id', 'username', 'timestamp', 'ip_address',
            'user_agent', 'success'
        )
        read_only_fields = fields

    def get_timestamp(self, obj) -> Optional[str]:
        """Return timestamp in local timezone."""
        if obj.timestamp:
            local_dt = timezone.localtime(obj.timestamp)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        return None


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics data."""

    total_logins = serializers.IntegerField()
    last_login = serializers.SerializerMethodField()
    weekly_data = serializers.JSONField()
    monthly_data = serializers.JSONField()
    login_trend = serializers.IntegerField()
    total_successful_logins = serializers.IntegerField()
    total_failed_logins = serializers.IntegerField()

    def get_last_login(self, obj) -> Optional[str]:
        """Return last_login in local timezone."""
        last_login = obj.get('last_login')
        if last_login:
            if isinstance(last_login, str):
                return last_login
            local_dt = timezone.localtime(last_login)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        return None


class AdminDashboardSerializer(serializers.Serializer):
    """Serializer for admin dashboard data."""

    total_users = serializers.IntegerField()
    total_logins = serializers.IntegerField()
    total_successful_logins = serializers.IntegerField()
    total_failed_logins = serializers.IntegerField()
    login_activity = LoginActivitySerializer(many=True)
    user_growth = serializers.JSONField()


# Chart Data Serializers
class LineChartSerializer(serializers.Serializer):
    """Serializer for line chart data."""

    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())


class BarChartSerializer(serializers.Serializer):
    """Serializer for bar chart data."""

    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())


class PieChartSerializer(serializers.Serializer):
    """Serializer for pie chart data."""

    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())


class ChartDataSerializer(serializers.Serializer):
    """Comprehensive chart data serializer for multiple chart types."""

    login_trends = LineChartSerializer(required=False)
    login_comparison = BarChartSerializer(required=False)
    login_distribution = serializers.DictField(required=False)
    admin_charts = serializers.DictField(required=False)

    def to_representation(self, instance):
        """Convert data to TypeScript-friendly format."""
        data = super().to_representation(instance)

        # Ensure proper structure for frontend
        if 'login_trends' in data:
            data['login_trends'] = self._ensure_chart_structure(
                data['login_trends'])
        if 'login_comparison' in data:
            data['login_comparison'] = self._ensure_chart_structure(
                data['login_comparison'])

        return data

    def _ensure_chart_structure(self, chart_data):
        """Ensure chart data has proper structure for frontend."""
        if not chart_data:
            return {
                'labels': [],
                'datasets': []
            }
        return chart_data


def calculate_login_trend(user):
    """Calculate login trend percentage for the user."""
    if not user.monthly_logins:
        return 0

        # Get current and previous month data
    current_month = timezone.now().strftime('%Y-%m')
    prev_month = (timezone.now() - timedelta(days=30)).strftime('%Y-%m')

    current_logins = user.monthly_logins.get(current_month, 0)
    prev_logins = user.monthly_logins.get(prev_month, 0)

    if prev_logins == 0:
        return 100 if current_logins > 0 else 0

    login_difference = current_logins - prev_logins
    trend_percentage = (login_difference / prev_logins) * 100
    return int(trend_percentage)


def get_user_stats(user, start_date=None, end_date=None):
    """Get comprehensive statistics for a user."""
    if start_date and end_date:
        # Compute stats dynamically from LoginActivity records
        activities = LoginActivity.objects.filter(
            user=user,
            timestamp__range=(start_date, end_date)
        )
        successful_activities = activities.filter(success=True)

        # Calculate successful and failed login counts
        total_successful_logins = successful_activities.count()
        total_failed_logins = activities.filter(success=False).count()

        # Calculate total logins (all attempts: successful + failed)
        total_logins = total_successful_logins + total_failed_logins

        # Calculate last login in date range
        last_login_activity = successful_activities.order_by(
            '-timestamp'
        ).first()
        last_login = (
            last_login_activity.timestamp if last_login_activity else None
        )

        # Calculate weekly data
        weekly_data = {}
        for activity in successful_activities:
            week_key = activity.timestamp.strftime('%Y-%U')
            weekly_data[week_key] = weekly_data.get(week_key, 0) + 1

        # Calculate monthly data
        monthly_data = {}
        for activity in successful_activities:
            month_key = activity.timestamp.strftime('%Y-%m')
            monthly_data[month_key] = monthly_data.get(month_key, 0) + 1

        # Calculate login trend (simplified - compare first half vs second
        # half of period)
        if successful_activities.exists():
            period_days = (end_date - start_date).days
            midpoint = start_date + timedelta(days=period_days // 2)

            first_half = successful_activities.filter(
                timestamp__lt=midpoint
            ).count()
            second_half = successful_activities.filter(
                timestamp__gte=midpoint
            ).count()

            if first_half == 0:
                login_trend = 100 if second_half > 0 else 0
            else:
                trend_calc = (
                    (second_half - first_half) / first_half
                ) * 100
                login_trend = int(trend_calc)
        else:
            login_trend = 0

        return {
            'total_logins': total_logins,
            'last_login': (
                timezone.localtime(last_login).strftime('%Y-%m-%d %H:%M:%S')
                if last_login else None
            ),
            'weekly_data': weekly_data,
            'monthly_data': monthly_data,
            'login_trend': login_trend,
            'total_successful_logins': total_successful_logins,
            'total_failed_logins': total_failed_logins,
        }
    else:
        # Use default behavior - pre-computed stats from User model
        user.refresh_from_db()

        # Calculate successful and failed from LoginActivity records
        total_successful_logins = LoginActivity.objects.filter(
            user=user, success=True
        ).count()
        total_failed_logins = LoginActivity.objects.filter(
            user=user, success=False
        ).count()

        # Calculate total logins (all attempts: successful + failed)
        total_logins = total_successful_logins + total_failed_logins

        return {
            'total_logins': total_logins,
            'last_login': (
                timezone.localtime(user.last_login_timestamp).strftime(
                    '%Y-%m-%d %H:%M:%S')
                if user.last_login_timestamp else None
            ),
            'weekly_data': user.weekly_logins or {},
            'monthly_data': user.monthly_logins or {},
            'login_trend': calculate_login_trend(user),
            'total_successful_logins': total_successful_logins,
            'total_failed_logins': total_failed_logins,
        }


def get_admin_dashboard_data(
    role=None,
    me=None,
    user_ids=None,
    filter_type=None,
    start_date=None,
    end_date=None
):
    """Get comprehensive data for admin dashboard.

    Args:
        role: Optional role filter ('admin', 'regular', or None for all users)
        me: Optional user object to show data for single user
        (takes precedence over role and user_ids)
        user_ids: Optional list of user IDs to filter by
        (takes precedence over role)
        filter_type: Optional user type filter ('admin_only', 'regular_users', 'me')
        start_date: Optional start date for filtering login activities
        end_date: Optional end date for filtering login activities
    """
    # Handle 'me' parameter - takes precedence over all others
    if me:
        users = User.objects.filter(id=me.id)
        login_filter = Q(user=me)
    # Handle user_ids parameter - takes precedence over role
    elif user_ids is not None:
        users = User.objects.filter(id__in=user_ids)
        login_filter = Q(user__in=users)
    # Filter users based on role if specified
    elif role == 'admin':
        user_filter = Q(is_staff=True) | Q(is_superuser=True)
        users = User.objects.filter(user_filter)
        login_filter = Q(user__in=users)
    elif role == 'regular':
        user_filter = Q(is_staff=False, is_superuser=False)
        users = User.objects.filter(user_filter)
        login_filter = Q(user__in=users)
    else:
        # Start with all users, then apply filter_type if specified
        users = User.objects.all()
        login_filter = Q()  # No filter on logins

        if filter_type == 'admin_only':
            users = users.filter(Q(is_staff=True) | Q(is_superuser=True))
            login_filter = Q(user__in=users)
        elif filter_type == 'regular_users':
            users = users.filter(is_staff=False, is_superuser=False)
            login_filter = Q(user__in=users)
        elif filter_type == 'me':
            # When filter_type='me', we need the me parameter to be passed
            # This will be handled in the view by setting me=request.user
            # So this case should not normally be reached here
            pass

    # Apply date filtering to login activities if dates provided
    if start_date or end_date:
        date_filter = Q()
        if start_date and end_date:
            date_filter = Q(timestamp__range=(start_date, end_date))
        elif start_date:
            date_filter = Q(timestamp__gte=start_date)
        elif end_date:
            date_filter = Q(timestamp__lte=end_date)
        login_filter &= date_filter

    # User statistics
    total_users = users.count()
    total_logins = LoginActivity.objects.filter(login_filter).count()

    # Calculate successful and failed login counts
    total_successful_logins = LoginActivity.objects.filter(
        login_filter & Q(success=True)
    ).count()
    total_failed_logins = LoginActivity.objects.filter(
        login_filter & Q(success=False)
    ).count()

    # Recent login activity (last 10 activities for filtered users)
    if me or role or user_ids or filter_type:
        login_activity = LoginActivity.objects.filter(login_filter) \
            .select_related('user') \
            .order_by('-timestamp')[:10]
    else:
        login_activity = LoginActivity.objects.filter(login_filter) \
            .select_related('user') \
            .order_by('-timestamp')[:10]

    # User growth by month (filtered by role, user_ids, filter_type, or single user)  # noqa: E501
    # Note: User growth is not affected by date filtering as it shows user registration dates  # noqa: E501
    user_growth = defaultdict(int)
    for user in users:
        join_month = user.date_joined.strftime('%Y-%m')
        user_growth[join_month] += 1

    return {
        'total_users': total_users,
        'total_logins': total_logins,
        'total_successful_logins': total_successful_logins,
        'total_failed_logins': total_failed_logins,
        'login_activity': login_activity,
        'user_growth': dict(user_growth)
    }


# Chart Analytics Functions
def get_login_trends_data(user, start_date=None, end_date=None):
    """
    Get login trends data for line charts.
    Returns data in Chart.js compatible format optimized for TypeScript.
    """
    if start_date is None:
        start_date = timezone.now() - timedelta(days=30)
    if end_date is None:
        # Add buffer to include activities created in the same minute
        end_date = timezone.now() + timedelta(minutes=1)

    # Optimized query using conditional aggregation
    login_data = LoginActivity.objects.filter(
        user=user,
        timestamp__range=(start_date, end_date)
    ).annotate(
        date=TruncDate('timestamp', tzinfo=timezone.utc)
    ).values('date').annotate(
        successful=Count('id', filter=Q(success=True)),
        failed=Count('id', filter=Q(success=False))
    ).order_by('date')

    # Prepare data structure
    dates = []
    successful_data = []
    failed_data = []

    # Generate all dates in range for consistent data structure
    current_date = start_date.date()
    end_date_date = end_date.date()
    # If end_date has a time component (not exactly midnight),
    # include the full day by treating it as the next day
    if end_date.time() != timezone.datetime.min.time():
        end_date_date += timedelta(days=1)

    # Create date to data mapping for fast lookup
    data_map = {}
    for entry in login_data:
        date_str = entry['date'].strftime('%Y-%m-%d')
        data_map[date_str] = {
            'successful': entry['successful'],
            'failed': entry['failed']
        }

    # Build complete data arrays
    while current_date < end_date_date:
        date_str = current_date.strftime('%Y-%m-%d')
        dates.append(date_str)

        if date_str in data_map:
            successful_data.append(data_map[date_str]['successful'])
            failed_data.append(data_map[date_str]['failed'])
        else:
            successful_data.append(0)
            failed_data.append(0)

        current_date += timedelta(days=1)

    return {
        'labels': dates,
        'datasets': [
            {
                'label': 'Successful Logins',
                'data': successful_data,
                'borderColor': '#4caf50',
                'backgroundColor': 'rgba(76, 175, 80, 0.1)'
            },
            {
                'label': 'Failed Logins',
                'data': failed_data,
                'borderColor': '#f44336',
                'backgroundColor': 'rgba(244, 67, 54, 0.1)'
            }
        ]
    }


def get_login_comparison_data(user, start_date=None, end_date=None):
    """
    Get login comparison data for bar charts.
    Returns weekly or monthly comparison data optimized for TypeScript.
    """
    if start_date is None:
        start_date = timezone.now() - timedelta(days=30)
    if end_date is None:
        end_date = timezone.now()

    # Determine timeframe (weekly or monthly)
    date_range = (end_date - start_date).days
    if date_range <= 30:
        # Use weekly data
        trunc_func = TruncWeek
        date_format = '%Y-%m-%d'
    else:
        # Use monthly data
        trunc_func = TruncMonth
        date_format = '%Y-%m'

    login_data = LoginActivity.objects.filter(
        user=user,
        timestamp__range=(start_date, end_date),
        success=True
    ).annotate(
        period=trunc_func('timestamp')
    ).values('period').annotate(
        count=Count('id')
    ).order_by('period')

    labels = []
    data = []

    for entry in login_data:
        labels.append(entry['period'].strftime(date_format))
        data.append(entry['count'])

    return {
        'labels': labels,
        'datasets': [{
            'label': 'Login Count',
            'data': data,
            'backgroundColor': '#2196f3'
        }]
    }


def get_login_distribution_data(user, start_date=None, end_date=None):
    """
    Get login distribution data for pie charts.
    Returns success/failure ratio and user agent distribution.
    """
    if start_date is None:
        start_date = timezone.now() - timedelta(days=30)
    if end_date is None:
        end_date = timezone.now()

    # Get success/failure ratio
    success_count = LoginActivity.objects.filter(
        user=user,
        timestamp__range=(start_date, end_date),
        success=True
    ).count()

    failure_count = LoginActivity.objects.filter(
        user=user,
        timestamp__range=(start_date, end_date),
        success=False
    ).count()

    # Get user agent distribution (top 5)
    user_agents = LoginActivity.objects.filter(
        user=user,
        timestamp__range=(start_date, end_date)
    ).values('user_agent').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    return {
        'success_ratio': {
            'labels': ['Successful', 'Failed'],
            'datasets': [{
                'data': [success_count, failure_count],
                'backgroundColor': ['#4caf50', '#f44336']
            }]
        },
        'user_agents': {
            'labels': [ua['user_agent'] for ua in user_agents],
            'datasets': [{
                'data': [ua['count'] for ua in user_agents],
                'backgroundColor': [
                    '#2196f3', '#4caf50', '#ff9800', '#9c27b0', '#607d8b'
                ]
            }]
        }
    }


def get_combined_login_comparison_data(users, start_date=None, end_date=None):
    """
    Get combined login comparison data for multiple users.
    Aggregates login data across all specified users.
    """
    if start_date is None:
        start_date = timezone.now() - timedelta(days=30)
    if end_date is None:
        end_date = timezone.now()

    # Determine timeframe (weekly or monthly)
    date_range = (end_date - start_date).days
    if date_range <= 30:
        # Use weekly data
        trunc_func = TruncWeek
        date_format = '%Y-%m-%d'
    else:
        # Use monthly data
        trunc_func = TruncMonth
        date_format = '%Y-%m'

    login_data = LoginActivity.objects.filter(
        user__in=users,
        timestamp__range=(start_date, end_date),
        success=True
    ).annotate(
        period=trunc_func('timestamp')
    ).values('period').annotate(
        count=Count('id')
    ).order_by('period')

    labels = []
    data = []

    for entry in login_data:
        labels.append(entry['period'].strftime(date_format))
        data.append(entry['count'])

    return {
        'labels': labels,
        'datasets': [{
            'label': 'Login Count (Combined)',
            'data': data,
            'backgroundColor': '#2196f3'
        }]
    }


def get_combined_login_distribution_data(
    users, start_date=None, end_date=None
):
    """
    Get combined login distribution data for multiple users.
    Aggregates login data across all specified users.
    """
    if start_date is None:
        start_date = timezone.now() - timedelta(days=30)
    if end_date is None:
        end_date = timezone.now()

    # Get success/failure ratio across all users
    success_count = LoginActivity.objects.filter(
        user__in=users,
        timestamp__range=(start_date, end_date),
        success=True
    ).count()

    failure_count = LoginActivity.objects.filter(
        user__in=users,
        timestamp__range=(start_date, end_date),
        success=False
    ).count()

    # Get user agent distribution (top 5 across all users)
    user_agents = LoginActivity.objects.filter(
        user__in=users,
        timestamp__range=(start_date, end_date)
    ).values('user_agent').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    return {
        'success_ratio': {
            'labels': ['Successful', 'Failed'],
            'datasets': [{
                'data': [success_count, failure_count],
                'backgroundColor': ['#4caf50', '#f44336']
            }]
        },
        'user_agents': {
            'labels': [ua['user_agent'] for ua in user_agents],
            'datasets': [{
                'data': [ua['count'] for ua in user_agents],
                'backgroundColor': [
                    '#2196f3', '#4caf50', '#ff9800', '#9c27b0', '#607d8b'
                ]
            }]
        }
    }


def get_combined_login_trends_data(users, start_date=None, end_date=None):
    """
    Get combined login trends data for multiple users.
    Aggregates login data across all specified users.
    """
    if start_date is None:
        start_date = timezone.now() - timedelta(days=30)
    if end_date is None:
        # Add buffer to include activities created in the same minute
        end_date = timezone.now() + timedelta(minutes=1)

    # Get login data for all users
    login_data = LoginActivity.objects.filter(
        user__in=users,
        timestamp__range=(start_date, end_date)
    ).annotate(
        date=TruncDate('timestamp', tzinfo=timezone.utc)
    ).values('date').annotate(
        successful=Count('id', filter=Q(success=True)),
        failed=Count('id', filter=Q(success=False))
    ).order_by('date')

    # Prepare data structure
    dates = []
    successful_data = []
    failed_data = []

    # Generate all dates in range for consistent data structure
    current_date = start_date.date()
    end_date_date = end_date.date()
    # If end_date has a time component (not exactly midnight),
    # include the full day by treating it as the next day
    if end_date.time() != timezone.datetime.min.time():
        end_date_date += timedelta(days=1)

    # Create date to data mapping for fast lookup
    data_map = {}
    for entry in login_data:
        date_str = entry['date'].strftime('%Y-%m-%d')
        data_map[date_str] = {
            'successful': entry['successful'],
            'failed': entry['failed']
        }

    # Build complete data arrays
    while current_date < end_date_date:
        date_str = current_date.strftime('%Y-%m-%d')
        dates.append(date_str)

        if date_str in data_map:
            successful_data.append(data_map[date_str]['successful'])
            failed_data.append(data_map[date_str]['failed'])
        else:
            successful_data.append(0)
            failed_data.append(0)

        current_date += timedelta(days=1)

    return {
        'labels': dates,
        'datasets': [
            {
                'label': 'Successful Logins (Combined)',
                'data': successful_data,
                'borderColor': '#4caf50',
                'backgroundColor': 'rgba(76, 175, 80, 0.1)'
            },
            {
                'label': 'Failed Logins (Combined)',
                'data': failed_data,
                'borderColor': '#f44336',
                'backgroundColor': 'rgba(244, 67, 54, 0.1)'
            }
        ]
    }


def get_admin_chart_data(start_date=None, end_date=None):
    """
    Get admin-level chart data.
    Returns system-wide analytics for admin dashboard.
    """
    if start_date is None:
        start_date = timezone.now() - timedelta(days=30)
    if end_date is None:
        end_date = timezone.now()

    # User growth by month
    user_growth = User.objects.filter(
        date_joined__range=(start_date, end_date)
    ).annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    # Login activity by day
    login_activity = LoginActivity.objects.filter(
        timestamp__range=(start_date, end_date),
        success=True
    ).annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Success ratio
    success_count = LoginActivity.objects.filter(
        timestamp__range=(start_date, end_date),
        success=True
    ).count()

    failure_count = LoginActivity.objects.filter(
        timestamp__range=(start_date, end_date),
        success=False
    ).count()

    return {
        'user_growth': {
            'labels': [
                entry['month'].strftime('%Y-%m') for entry in user_growth
            ],
            'datasets': [{
                'label': 'New Users',
                'data': [entry['count'] for entry in user_growth],
                'borderColor': '#2196f3'
            }]
        },
        'login_activity': {
            'labels': [
                entry['date'].strftime('%Y-%m-%d') for entry in login_activity
            ],
            'datasets': [{
                'label': 'Daily Logins',
                'data': [entry['count'] for entry in login_activity],
                'borderColor': '#4caf50'
            }]
        },
        'success_ratio': {
            'labels': ['Successful', 'Failed'],
            'datasets': [{
                'data': [success_count, failure_count],
                'backgroundColor': ['#4caf50', '#f44336']
            }]
        }
    }
