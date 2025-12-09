"""Serializers for dashboard API endpoints with TypeScript-friendly responses."""  # noqa: E501
from rest_framework import serializers
from core.models import LoginActivity, User
from datetime import timedelta
from django.utils import timezone
from collections import defaultdict


class LoginActivitySerializer(serializers.ModelSerializer):
    """Serializer for login activity data."""

    timestamp = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = LoginActivity
        fields = (
            'id', 'username', 'timestamp', 'ip_address',
            'user_agent', 'success'
        )
        read_only_fields = fields


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics data."""

    total_logins = serializers.IntegerField()
    last_login = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    weekly_data = serializers.JSONField()
    monthly_data = serializers.JSONField()
    login_trend = serializers.IntegerField()


class AdminDashboardSerializer(serializers.Serializer):
    """Serializer for admin dashboard data."""

    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_logins = serializers.IntegerField()
    login_activity = LoginActivitySerializer(many=True)
    user_growth = serializers.JSONField()


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


def get_user_stats(user):
    """Get comprehensive statistics for a user."""
    # Refresh the user from database to get actual values
    # (not CombinedExpression)
    user.refresh_from_db()

    return {
        'total_logins': user.login_count or 0,
        'last_login': user.last_login_timestamp,
        'weekly_data': user.weekly_logins or {},
        'monthly_data': user.monthly_logins or {},
        'login_trend': calculate_login_trend(user)
    }


def get_admin_dashboard_data():
    """Get comprehensive data for admin dashboard."""
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_logins = LoginActivity.objects.filter(success=True).count()

    # Recent login activity (last 10 activities)
    login_activity = LoginActivity.objects.select_related('user') \
        .order_by('-timestamp')[:10]

    # User growth by month
    user_growth = defaultdict(int)
    for user in User.objects.all():
        join_month = user.date_joined.strftime('%Y-%m')
        user_growth[join_month] += 1

    return {
        'total_users': total_users,
        'active_users': active_users,
        'total_logins': total_logins,
        'login_activity': login_activity,
        'user_growth': dict(user_growth)
    }
