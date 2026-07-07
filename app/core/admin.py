from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, LoginActivity
from .email_service import send_verification_email, build_verification_url


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""
    ordering = ['id']
    list_display = ['username', 'email', 'role_badge', 'email_verified_status']
    search_fields = ['username', 'email']
    list_filter = ['email_verified', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'email',
                           'password', 'image',)}),
        (
            'Email Verification',
            {
                'fields': (
                    'email_verified',
                )
            }
        ),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2'
            ),
        }),
    )
    readonly_fields = [
        'last_login',
    ]
    actions = ['verify_emails']

    def save_model(self, request, obj, form, change):
        """Override save_model to send verification email for new users."""
        if not change:
            # New user being created
            super().save_model(request, obj, form, change)
            obj.generate_verification_token()
            verification_url = build_verification_url(
                request, obj.verification_token, email=obj.email
            )
            send_verification_email(obj, verification_url)
        else:
            super().save_model(request, obj, form, change)

    @admin.display(description='Email Verified')
    def email_verified_status(self, obj):
        """Return email verification status as a readable string."""
        if obj.email_verified:
            return 'Verified'
        return 'Not Verified'

    @admin.action(description='Mark selected users as email verified')
    def verify_emails(self, request, queryset):
        """Bulk action to mark selected users as email verified."""
        queryset.update(email_verified=True)

    @admin.display(description='Role & Permissions')
    def role_badge(self, obj):
        """Return a colour-coded role badge with permission description."""
        if obj.is_superuser:
            color = '#dc3545'
            label = 'Superuser'
            permission = 'Full Access'
        elif obj.is_staff:
            color = '#ffc107'
            label = 'Staff'
            permission = 'Read-only Access'
        else:
            color = '#28a745'
            label = 'Regular'
            permission = 'Own Data Only'

        return format_html(
            '<span style="color: {}; font-weight: bold; '
            'background: #f8f9fa; padding: 2px 8px; '
            'border-radius: 3px;">{}</span> '
            '<span style="color: #6c757d; font-size: 0.85em;">'
            '- {}</span>',
            color, label, permission
        )

    def permission_notice(self, obj):
        """Return a detailed permission notice for the user."""
        if obj.is_superuser:
            return (
                '<strong>Superuser</strong> — '
                'Full administrative access: Create, Read, Update, '
                'and Delete any user record. Full system configuration.'
            )
        elif obj.is_staff:
            return (
                '<strong>Staff</strong> — '
                'Read-only administrative access: View user list, '
                'view user details. '
                'Cannot add, edit, or delete users.'
            )
        else:
            return (
                '<strong>Regular</strong> — '
                'No admin access. Regular users cannot access the '
                'Django admin panel.'
            )

    def has_module_permission(self, request):
        """Allow staff and superusers to see the admin module."""
        return request.user.is_active and (
            request.user.is_superuser or request.user.is_staff
        )

    def has_view_permission(self, request, obj=None):
        """Allow staff and superusers to view records."""
        return request.user.is_active and (
            request.user.is_superuser or request.user.is_staff
        )

    def has_change_permission(self, request, obj=None):
        """Only superusers can edit records."""
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        """Only superusers can add records."""
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete records."""
        return request.user.is_active and request.user.is_superuser


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    """Admin configuration for LoginActivity model."""
    list_display = ['user', 'timestamp', 'ip_address', 'success']
    list_filter = ['timestamp', 'success']
    search_fields = ['user__username', 'user__email', 'ip_address']
    readonly_fields = [
        'user', 'timestamp', 'ip_address', 'user_agent', 'success'
    ]
    ordering = ['-timestamp']
    list_per_page = 25

    def has_module_permission(self, request):
        """Allow staff and superusers to see the Login Activity module."""
        return request.user.is_active and (
            request.user.is_superuser or request.user.is_staff
        )

    def has_add_permission(self, request):
        """Prevent adding login activity records via admin."""
        return False

    def has_view_permission(self, request, obj=None):
        """Allow both superusers and staff to view login activity records."""
        return request.user.is_active and (
            request.user.is_superuser or request.user.is_staff
        )

    def has_change_permission(self, request, obj=None):
        """Prevent any editing of login activity records."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete login activity records."""
        return request.user.is_superuser
