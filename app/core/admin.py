from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .email_service import send_verification_email, build_verification_url


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""
    ordering = ['id']
    list_display = ['username', 'email', 'name', 'email_verified_status']
    search_fields = ['username', 'email', 'name']
    list_filter = ['email_verified', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'email', 'name',
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
