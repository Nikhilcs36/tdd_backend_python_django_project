"""
Views for the game app with feature flag support.
"""
import logging
from collections import OrderedDict
from django.conf import settings
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema, OpenApiExample
)
from drf_spectacular.types import OpenApiTypes

from game.models import GameScore
from game.serializers import (
    GameScoreSerializer,
    GameScoreListSerializer,
    LeaderboardSerializer,
)
from user.permissions import IsStaffOrSuperUser
from user.pagination import SafePageNumberPagination

logger = logging.getLogger(__name__)


class GameSectionCheckMixin:
    """Mixin to check if game section is enabled before processing requests."""

    def initial(self, request, *args, **kwargs):
        """Check feature flags before processing the request."""
        if not getattr(settings, 'GAME_SECTION_ENABLED', True):
            raise PermissionDenied(
                detail="Game section is disabled"
            )
        super().initial(request, *args, **kwargs)


class LeaderboardCheckMixin:
    """Mixin to check if leaderboard is enabled before processing requests."""

    def initial(self, request, *args, **kwargs):
        """Check leaderboard feature flag before processing the request."""
        if not getattr(settings, 'GAME_LEADERBOARD_ENABLED', True):
            raise PermissionDenied(
                detail="Leaderboard is disabled"
            )
        super().initial(request, *args, **kwargs)


class CreateGameScoreView(GameSectionCheckMixin, generics.CreateAPIView):
    """Create a new game score for the authenticated user."""
    serializer_class = GameScoreSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id="create_game_score",
        summary="Submit Game Score",
        description=(
            "Submit a new game score for the authenticated user. "
            "The score is associated with the current user automatically. "
            "Scores can be viewed via the 'My Scores' endpoint."
        ),
        responses={
            201: GameScoreSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Score Submission",
                value={
                    "id": 1,
                    "score": 85.00,
                    "created_at": "2025-12-13T14:30:25Z"
                },
                response_only=True,
                status_codes=["201"]
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        """Handle POST request to submit a game score."""
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Save the score with the current user."""
        logger.info(
            'User %s created game score: %.2f',
            self.request.user.username,
            serializer.validated_data['score']
        )
        serializer.save(user=self.request.user)


class MyGameScoresView(GameSectionCheckMixin, generics.ListAPIView):
    """List the authenticated user's game scores with best score."""
    serializer_class = GameScoreListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SafePageNumberPagination

    @extend_schema(
        operation_id="list_my_game_scores",
        summary="Get My Game Scores",
        description=(
            "Retrieve the authenticated user's game scores, ordered by "
            "highest score first. Returns paginated results along with the "
            "user's best score. Includes pagination metadata (count, next, "
            "previous)."
        ),
        responses={
            200: GameScoreListSerializer(many=True),
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "best_score": 95.00,
                    "count": 3,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "score": 95.00,
                            "created_at": "2025-12-13T14:30:25Z"
                        },
                        {
                            "id": 2,
                            "score": 82.50,
                            "created_at": "2025-12-12T10:15:30Z"
                        }
                    ]
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """Handle GET request to list my game scores."""
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        """Return only the current user's scores, ordered by best first."""
        return GameScore.objects.filter(
            user=self.request.user
        ).order_by('-score')

    def list(self, request, *args, **kwargs):
        """Add best_score to the response."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        best_score = queryset.first().score if queryset.exists() else None

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'best_score': best_score,
                'results': serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'best_score': best_score,
            'results': serializer.data
        })

    def get_paginated_response(self, data):
        """Override to include best_score in paginated response."""
        return Response(OrderedDict([
            ('best_score', data.get('best_score')),
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data.get('results')),
        ]))


class LeaderboardPagination(SafePageNumberPagination):
    """Pagination for the leaderboard with a default page size."""
    page_size = 10


class GameLeaderboardView(
    GameSectionCheckMixin,
    LeaderboardCheckMixin,
    generics.ListAPIView
):
    """
    Admin-only leaderboard showing the best score per user.
    Ordered by score descending.
    Uses manual deduplication to ensure only one score per user.
    Supports pagination via LeaderboardPagination.
    """
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrSuperUser]
    pagination_class = LeaderboardPagination

    @extend_schema(
        operation_id="get_game_leaderboard",
        summary="Get Game Leaderboard (Admin Only)",
        description=(
            "Retrieve the game leaderboard showing the best score per user. "
            "Only one entry per user is included (their highest score). "
            "Ordered by score descending. Supports pagination. Requires "
            "admin or staff privileges."
        ),
        responses={
            200: LeaderboardSerializer(many=True),
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Successful Response",
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "username": "champion",
                            "score": 95.00,
                            "created_at": "2025-12-13T14:30:25Z"
                        },
                        {
                            "username": "player2",
                            "score": 82.50,
                            "created_at": "2025-12-12T10:15:30Z"
                        }
                    ]
                },
                response_only=True,
                status_codes=["200"]
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """Handle GET request to retrieve leaderboard."""
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return scores sorted by score descending.
        Override list to deduplicate by user.
        """
        return GameScore.objects.all().order_by('-score', 'created_at')

    def list(self, request, *args, **kwargs):
        """
        Return leaderboard with one entry per user (their best score).
        Paginates the deduplicated results.
        """
        queryset = self.get_queryset()
        seen_users = set()
        unique_scores = []

        for score in queryset:
            if score.user_id not in seen_users:
                seen_users.add(score.user_id)
                unique_scores.append(score)

        page = self.paginate_queryset(unique_scores)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(unique_scores, many=True)
        return Response({
            'results': serializer.data
        })
