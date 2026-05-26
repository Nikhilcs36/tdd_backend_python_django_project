"""
URL configuration for the game app.
"""
from django.urls import path
from game.views import (
    CreateGameScoreView,
    MyGameScoresView,
    GameLeaderboardView,
)

app_name = 'game'

urlpatterns = [
    path('scores/', CreateGameScoreView.as_view(), name='create-score'),
    path('scores/me/', MyGameScoresView.as_view(), name='my-scores'),
    path('leaderboard/', GameLeaderboardView.as_view(), name='leaderboard'),
]
