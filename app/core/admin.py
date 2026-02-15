from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""
    ordering = ['id']
    list_display = ['email', 'name', 'email_verified_status']
    list_filter = ['email_verified', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = (
        (None, {'fields': ('email', 'name', 'password', 'image',)}),
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
                'email',
                'password',
                'password2'
            ),
        }),
    )
    readonly_fields = [
        'last_login',
    ]
    actions = ['verify_emails']

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
