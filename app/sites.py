"""Custom AdminSite to block regular users with a clear message."""
from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.utils.translation import gettext_lazy as _


class StaffOnlyAuthenticationForm(AdminAuthenticationForm):
    """Authentication form that only allows staff/superuser logins."""

    def confirm_login_allowed(self, user):
        """Ensure only staff or superusers can log into the admin."""
        if not user.is_active or not (
            user.is_superuser or user.is_staff
        ):
            raise forms.ValidationError(
                _(
                    'Your account does not have admin access. '
                    'Please log in again with a staff or superuser '
                    'account. Regular users cannot access the '
                    'Django admin panel.'
                ),
                code='no_admin_access',
            )
