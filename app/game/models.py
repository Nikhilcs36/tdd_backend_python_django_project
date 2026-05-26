"""
Game models for the circle drawing game.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class GameScore(models.Model):
    """Model to store user game scores for the circle drawing game."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_scores'
    )
    score = models.FloatField(
        help_text="Accuracy percentage (0.0 - 100.0)"
    )
    attempts = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-score']

    def __str__(self):
        return f"{self.user.username} - {self.score}%"
