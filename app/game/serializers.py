"""
Serializers for the game app.
"""
from rest_framework import serializers
from game.models import GameScore


class GameScoreSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing game scores."""

    class Meta:
        model = GameScore
        fields = ['id', 'score', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_score(self, value):
        """Validate score is within valid range."""
        if value < 0.0 or value > 100.0:
            raise serializers.ValidationError(
                'Score must be between 0.0 and 100.0'
            )
        return value


class GameScoreListSerializer(serializers.ModelSerializer):
    """Serializer for listing game scores."""

    class Meta:
        model = GameScore
        fields = ['id', 'score', 'created_at']


class LeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for admin leaderboard showing top scores per user."""
    username = serializers.CharField(source='user.username')

    class Meta:
        model = GameScore
        fields = ['username', 'score', 'created_at']
