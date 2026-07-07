"""
Admin configuration for the game app.
"""
from django.contrib import admin
from game.models import GameScore


@admin.register(GameScore)
class GameScoreAdmin(admin.ModelAdmin):
    """Admin configuration for GameScore model."""
    list_display = ['user', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['user', 'score', 'created_at']
    ordering = ['-score']

    def has_module_permission(self, request):
        """Allow staff and superusers to see the Game Scores module."""
        return request.user.is_active and (
            request.user.is_superuser or request.user.is_staff
        )

    def has_view_permission(self, request, obj=None):
        """Allow staff and superusers to view game scores."""
        return request.user.is_active and (
            request.user.is_superuser or request.user.is_staff
        )

    def has_add_permission(self, request):
        """Prevent anyone from adding game scores via admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing game scores via admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete game scores."""
        return request.user.is_superuser
