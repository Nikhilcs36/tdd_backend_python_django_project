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
    readonly_fields = ['created_at']
    ordering = ['-score']
