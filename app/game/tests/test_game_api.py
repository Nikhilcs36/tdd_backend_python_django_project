"""
Tests for the game API.
Tests cover:
- GameScore model creation
- Creating game scores via API
- Retrieving own scores and best score
- Admin leaderboard with feature flag gating
- Feature flag disabling (game_section_enabled, game_leaderboard_enabled)
"""
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User
from game.models import GameScore


CREATE_SCORE_URL = reverse('game:create-score')
MY_SCORES_URL = reverse('game:my-scores')
LEADERBOARD_URL = reverse('game:leaderboard')


def create_user(username='testuser', email='test@example.com',
                password='Password123', is_staff=False):
    """Helper function to create a user."""
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_staff=is_staff
    )


class GameScoreModelTests(TestCase):
    """Test the GameScore model."""

    def setUp(self):
        self.user = create_user()

    def test_create_game_score_successful(self):
        """Test creating a game score is successful."""
        score = GameScore.objects.create(
            user=self.user,
            score=85.5
        )
        self.assertEqual(score.user, self.user)
        self.assertEqual(score.score, 85.5)
        self.assertIsNotNone(score.id)
        self.assertIsNotNone(score.created_at)

    def test_game_score_str_representation(self):
        """Test the string representation of a game score."""
        score = GameScore.objects.create(
            user=self.user,
            score=92.3
        )
        expected_str = f"{self.user.username} - 92.3%"
        self.assertEqual(str(score), expected_str)

    def test_game_score_ordering_by_score_descending(self):
        """Test GameScore Meta ordering is by score descending."""
        self.assertIn('-score', GameScore._meta.ordering)

    def test_game_score_score_validation_positive(self):
        """Test creating a score with valid positive value."""
        score = GameScore.objects.create(
            user=self.user,
            score=0.0
        )
        self.assertEqual(score.score, 0.0)

    def test_game_score_score_validation_high_value(self):
        """Test creating a score with 100.0 is valid."""
        score = GameScore.objects.create(
            user=self.user,
            score=100.0
        )
        self.assertEqual(score.score, 100.0)

    def test_game_score_default_attempts(self):
        """Test the default attempts value."""
        score = GameScore.objects.create(
            user=self.user,
            score=75.0
        )
        self.assertEqual(score.attempts, 1)


class GameScoreAPITests(TestCase):
    """Test the game score API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        # Generate JWT token for authentication
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'JWT {refresh.access_token}'
        )

    def test_create_game_score_authenticated(self):
        """Test creating a game score as an authenticated user."""
        payload = {'score': 92.5}
        res = self.client.post(CREATE_SCORE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GameScore.objects.count(), 1)
        self.assertEqual(res.data['score'], 92.5)
        self.assertIn('id', res.data)
        self.assertIn('created_at', res.data)

    def test_create_game_score_unauthenticated(self):
        """Test creating a game score without authentication returns 401."""
        self.client.credentials()  # Remove auth
        payload = {'score': 92.5}
        res = self.client.post(CREATE_SCORE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_game_score_invalid_data(self):
        """Test creating a game score with invalid data returns 400."""
        payload = {'score': -10}
        res = self.client.post(CREATE_SCORE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_game_score_missing_score(self):
        """Test creating a game score with missing score returns 400."""
        payload = {}
        res = self.client.post(CREATE_SCORE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_my_scores_authenticated(self):
        """Test retrieving own game scores."""
        # Create some scores for this user
        GameScore.objects.create(user=self.user, score=80.0)
        GameScore.objects.create(user=self.user, score=95.0)

        res = self.client.get(MY_SCORES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 2)
        # Best score should be first (descending order)
        self.assertEqual(res.data['results'][0]['score'], 95.0)
        self.assertEqual(res.data['results'][1]['score'], 80.0)

    def test_get_my_scores_shows_best_score_in_response(self):
        """Test that the my-scores endpoint returns the best score."""
        GameScore.objects.create(user=self.user, score=80.0)
        GameScore.objects.create(user=self.user, score=95.0)
        GameScore.objects.create(user=self.user, score=70.0)

        res = self.client.get(MY_SCORES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('best_score', res.data)
        self.assertEqual(res.data['best_score'], 95.0)

    def test_get_my_scores_no_scores(self):
        """Test retrieving scores when user has none."""
        res = self.client.get(MY_SCORES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 0)
        self.assertEqual(res.data['best_score'], None)

    def test_get_my_scores_only_own_scores(self):
        """Test that users only see their own scores."""
        other_user = create_user(
            username='otheruser',
            email='other@example.com'
        )
        GameScore.objects.create(user=self.user, score=95.0)
        GameScore.objects.create(user=other_user, score=99.0)

        res = self.client.get(MY_SCORES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['score'], 95.0)

    def test_get_my_scores_unauthenticated(self):
        """Test retrieving scores without auth returns 401."""
        self.client.credentials()
        res = self.client.get(MY_SCORES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class GameLeaderboardAPITests(TestCase):
    """Test the admin leaderboard API endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            username='normaluser',
            email='normal@example.com'
        )
        self.admin_user = create_user(
            username='adminuser',
            email='admin@example.com',
            is_staff=True
        )

    def authenticate_as_admin(self):
        """Helper to authenticate as admin user."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'JWT {refresh.access_token}'
        )

    def authenticate_as_normal_user(self):
        """Helper to authenticate as normal user."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'JWT {refresh.access_token}'
        )

    def test_leaderboard_admin_access_allowed(self):
        """Test admin user can access leaderboard."""
        self.authenticate_as_admin()
        # Create scores for different users
        GameScore.objects.create(user=self.user, score=80.0)
        GameScore.objects.create(user=self.admin_user, score=95.0)

        res = self.client.get(LEADERBOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 2)
        self.assertIn('results', res.data)

    def test_leaderboard_regular_user_denied(self):
        """Test regular user cannot access leaderboard (403)."""
        self.authenticate_as_normal_user()
        res = self.client.get(LEADERBOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_leaderboard_unauthenticated_denied(self):
        """Test unauthenticated user cannot access leaderboard (401)."""
        res = self.client.get(LEADERBOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_leaderboard_sorted_by_best_score(self):
        """Test leaderboard is sorted by score descending."""
        self.authenticate_as_admin()
        user2 = create_user(
            username='user2',
            email='user2@example.com'
        )
        GameScore.objects.create(user=self.user, score=80.0)
        GameScore.objects.create(user=user2, score=95.0)

        res = self.client.get(LEADERBOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'][0]['score'], 95.0)
        self.assertEqual(res.data['results'][1]['score'], 80.0)

    def test_leaderboard_shows_username(self):
        """Test leaderboard includes username for each score."""
        self.authenticate_as_admin()
        GameScore.objects.create(user=self.user, score=80.0)

        res = self.client.get(LEADERBOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data['results'][0]['username'],
            self.user.username
        )

    def test_leaderboard_only_best_score_per_user(self):
        """Test leaderboard shows only the best score per user."""
        self.authenticate_as_admin()
        GameScore.objects.create(user=self.user, score=80.0)
        GameScore.objects.create(user=self.user, score=95.0)

        res = self.client.get(LEADERBOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Despite 2 scores, only 1 entry per user (best score)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['score'], 95.0)

    def test_leaderboard_no_scores(self):
        """Test leaderboard when no scores exist."""
        self.authenticate_as_admin()
        res = self.client.get(LEADERBOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 0)
        self.assertIn('results', res.data)

    def test_leaderboard_tiebreaker_earliest_score_first(self):
        """
        Test that when 3 of 5 users have the same top score,
        they are ordered by who achieved it first (earliest created_at).
        """
        self.authenticate_as_admin()
        user_a = create_user(username='user_a', email='a@example.com')
        user_b = create_user(username='user_b', email='b@example.com')
        user_c = create_user(username='user_c', email='c@example.com')
        user_d = create_user(username='user_d', email='d@example.com')
        user_e = create_user(username='user_e', email='e@example.com')

        now = timezone.now()

        # User A: best=95.0 (created earliest)
        GameScore.objects.create(
            user=user_a, score=95.0,
            created_at=now - timedelta(hours=4)
        )
        # User B: best=80.0
        GameScore.objects.create(
            user=user_b, score=80.0,
            created_at=now - timedelta(hours=3)
        )
        # User C: best=95.0 (created middle)
        GameScore.objects.create(
            user=user_c, score=95.0,
            created_at=now - timedelta(hours=2)
        )
        # User D: best=60.0
        GameScore.objects.create(
            user=user_d, score=60.0,
            created_at=now - timedelta(hours=1)
        )
        # User E: best=95.0 (created latest)
        GameScore.objects.create(
            user=user_e, score=95.0,
            created_at=now
        )

        res = self.client.get(LEADERBOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 5)

        # Expected order: A(95), C(95), E(95), B(80), D(60)
        self.assertEqual(res.data['results'][0]['username'], 'user_a')
        self.assertEqual(res.data['results'][0]['score'], 95.0)
        self.assertEqual(res.data['results'][1]['username'], 'user_c')
        self.assertEqual(res.data['results'][1]['score'], 95.0)
        self.assertEqual(res.data['results'][2]['username'], 'user_e')
        self.assertEqual(res.data['results'][2]['score'], 95.0)
        self.assertEqual(res.data['results'][3]['username'], 'user_b')
        self.assertEqual(res.data['results'][3]['score'], 80.0)
        self.assertEqual(res.data['results'][4]['username'], 'user_d')
        self.assertEqual(res.data['results'][4]['score'], 60.0)


class GameFeatureFlagTests(TestCase):
    """Test the game feature flag gating."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.admin_user = create_user(
            username='adminuser',
            email='admin@example.com',
            is_staff=True
        )
        from rest_framework_simplejwt.tokens import RefreshToken

        # Authenticate as normal user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'JWT {refresh.access_token}'
        )

        # Auth token for admin
        refresh_admin = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh_admin.access_token)

    @override_settings(GAME_SECTION_ENABLED=False)
    def test_create_score_when_game_disabled(self):
        """Test creating a score returns 403 when game section is disabled."""
        payload = {'score': 85.0}
        res = self.client.post(CREATE_SCORE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Game section is disabled', str(res.data))

    @override_settings(GAME_SECTION_ENABLED=False)
    def test_get_my_scores_when_game_disabled(self):
        """Test retrieving scores returns 403 when game section is disabled."""
        res = self.client.get(MY_SCORES_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Game section is disabled', str(res.data))

    @override_settings(GAME_LEADERBOARD_ENABLED=False)
    def test_leaderboard_when_leaderboard_disabled(self):
        """Test leaderboard returns 403 when leaderboard is disabled."""
        # Authenticate as admin
        self.client.credentials(
            HTTP_AUTHORIZATION=f'JWT {self.admin_token}'
        )
        res = self.client.get(LEADERBOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Leaderboard is disabled', str(res.data))

    @override_settings(
        GAME_SECTION_ENABLED=True,
        GAME_LEADERBOARD_ENABLED=True
    )
    def test_game_works_when_both_flags_enabled(self):
        """Test both game and leaderboard work when flags are enabled."""
        # User can create score
        payload = {'score': 85.0}
        res = self.client.post(CREATE_SCORE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # User can get own scores
        res = self.client.get(MY_SCORES_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Admin can access leaderboard
        self.client.credentials(
            HTTP_AUTHORIZATION=f'JWT {self.admin_token}'
        )
        res = self.client.get(LEADERBOARD_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @override_settings(
        GAME_SECTION_ENABLED=False,
        GAME_LEADERBOARD_ENABLED=False
    )
    def test_all_game_endpoints_disabled_when_flags_off(self):
        """Test all game endpoints return 403 when both flags are off."""
        # Create score fails
        payload = {'score': 85.0}
        res = self.client.post(CREATE_SCORE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # My scores fails
        res = self.client.get(MY_SCORES_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Leaderboard fails for admin
        self.client.credentials(
            HTTP_AUTHORIZATION=f'JWT {self.admin_token}'
        )
        res = self.client.get(LEADERBOARD_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
