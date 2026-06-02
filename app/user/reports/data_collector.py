"""Data collector for report generation."""
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import LoginActivity
from user.serializers_dashboard import (
    get_user_stats,
    get_login_trends_data,
    get_login_comparison_data,
    get_login_distribution_data,
    get_combined_login_trends_data,
    get_combined_login_comparison_data,
    get_combined_login_distribution_data,
)

User = get_user_model()


class ReportDataCollector:
    """Collects and organizes data for report generation."""

    def __init__(
        self, users, start_date=None, end_date=None, mode='individual',
        filter_info=None, requesting_user=None, selected_user=None
    ):
        """
        Initialize the data collector.

        Args:
            users: List of User objects or single User object
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            mode: 'individual' or 'grouped'
            filter_info: Optional dict describing applied filters
            requesting_user: The user who requested the report
                (for admin context)
            selected_user: Optional specific user to use for
                'Selected User' label in reports. If provided,
                this user's data is used for summary stats and
                activities, while all users in 'users' are used
                for grouped chart data.
        """
        if isinstance(users, (list, tuple)):
            self.users = users
        else:
            self.users = [users]

        self.start_date = start_date
        self.end_date = end_date
        self.mode = mode
        self.filter_info = filter_info or {}
        self.requesting_user = requesting_user
        self.selected_user = selected_user

        # Set default date range if not provided
        if self.start_date is None:
            self.start_date = timezone.now() - timedelta(days=30)
        if self.end_date is None:
            self.end_date = timezone.now() + timedelta(minutes=1)

    def collect_all_data(self):
        """
        Collect all data needed for the report.

        Dashboard logic:
        - Summary + Activities: always show selected user's data
        - Charts (trends/comparison/distribution):
          - Individual mode: selected user's data
          - Grouped mode: combined data for selected users

        When an admin selects a user via dropdown
        (user_ids[] in individual mode), the report data should
        reflect that selected user, and the header should
        distinguish between the logged user and the selected
        dropdown user.
        """
        user_details = self._get_user_details()

        # Use selected_user if explicitly provided (for grouped mode
        # with selected_user_id), otherwise fall back to first user
        primary_user = (
            self.selected_user if self.selected_user is not None
            else self.users[0]
        )

        # Determine if a dropdown user was selected by an admin
        has_dropdown_selection = (
            self.requesting_user is not None
            and self.requesting_user != primary_user
            and self.mode in ('individual', 'grouped')
        )

        # Summary + Activities: always for the primary (selected) user
        user_stats = get_user_stats(
            primary_user, self.start_date, self.end_date
        )
        login_activities = self._get_login_activities([primary_user])

        # Charts: individual or combined based on mode
        if self.mode == 'individual' or len(self.users) == 1:
            login_trends = get_login_trends_data(
                primary_user, self.start_date, self.end_date
            )
            login_comparison = get_login_comparison_data(
                primary_user, self.start_date, self.end_date
            )
            login_distribution = get_login_distribution_data(
                primary_user, self.start_date, self.end_date
            )
        else:
            login_trends = get_combined_login_trends_data(
                self.users, self.start_date, self.end_date
            )
            login_comparison = get_combined_login_comparison_data(
                self.users, self.start_date, self.end_date
            )
            login_distribution = get_combined_login_distribution_data(
                self.users, self.start_date, self.end_date
            )

            # TOP USER AGENTS should reflect the selected user only,
            # not the aggregated group (consistent with RECENT LOGIN
            # ACTIVITIES and SUMMARY STATISTICS behavior)
            primary_user_agents = get_login_distribution_data(
                primary_user, self.start_date, self.end_date
            )['user_agents']
            login_distribution['user_agents'] = primary_user_agents

        # Grouped summary only relevant in grouped mode
        grouped_summary = None
        if self.mode == 'grouped' and len(self.users) > 1:
            grouped_summary = self._calculate_combined_stats()

        return {
            'mode': self.mode,
            'user': primary_user,
            'users': self.users,
            'user_details': user_details,
            'user_count': len(self.users),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'generated_at': timezone.now(),
            'filter_info': self.filter_info,
            'filter_description': self._get_filter_description(),
            'summary': user_stats,
            'grouped_summary': grouped_summary,
            'login_trends': login_trends,
            'login_comparison': login_comparison,
            'login_distribution': login_distribution,
            'login_activities': login_activities,
            'requesting_user': self.requesting_user,
            'has_dropdown_selection': has_dropdown_selection,
        }

    def _get_user_details(self):
        """Get readable user details for all users."""
        return [
            {
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'is_admin': u.is_staff or u.is_superuser,
            }
            for u in self.users
        ]

    def _calculate_combined_stats(self):
        """Calculate combined statistics for all selected users."""
        total_logins = 0
        total_successful = 0
        total_failed = 0

        for user in self.users:
            stats = get_user_stats(user, self.start_date, self.end_date)
            total_logins += stats.get('total_logins', 0)
            total_successful += stats.get('total_successful_logins', 0)
            total_failed += stats.get('total_failed_logins', 0)

        success_rate = 0
        if total_logins > 0:
            success_rate = round(
                (total_successful / total_logins) * 100, 2
            )

        return {
            'total_logins': total_logins,
            'total_successful_logins': total_successful,
            'total_failed_logins': total_failed,
            'success_rate': success_rate,
        }

    def _get_filter_description(self):
        """Build a human-readable filter description."""
        parts = []
        ft = self.filter_info.get('type')
        role = self.filter_info.get('role')

        if ft == 'all':
            parts.append('All system users')
        elif ft == 'user_ids':
            user_details = self._get_user_details()
            count = len(user_details)
            names = ', '.join(
                [u['username'] for u in user_details]
            )
            if count <= 3:
                parts.append(f'Specific users: {names}')
            else:
                parts.append(f'{count} specific users')
        elif ft == 'admin_only':
            parts.append('Admin users only')
        elif ft == 'regular_users':
            parts.append('Regular users only')
        elif ft == 'me':
            parts.append('Own data only')
        elif role:
            parts.append(f'Filtered by role: {role}')
        else:
            if self.mode == 'individual':
                parts.append('Current user only')
            else:
                parts.append('All selected users')

        if self.filter_info.get('me'):
            parts.append('Own data only')

        return ' | '.join(parts) if parts else 'No filters'

    def _get_login_activities(self, users):
        """Get login activities for specified users."""
        queryset = LoginActivity.objects.filter(
            user__in=users,
            timestamp__range=(self.start_date, self.end_date)
        ).select_related('user').order_by('-timestamp')

        activities = list(queryset[:100])

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
            for activity in activities
        ]
