"""
Tests for the game app admin configuration.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib import admin
from game.models import GameScore


class GameScoreAdminTests(TestCase):
    """Test cases for GameScore admin registration and permissions."""

    def setUp(self):
        self.client = Client()
        self.superuser = get_user_model().objects.create_superuser(
            username='superadmin',
            email='super@example.com',
            password='password123'
        )
        self.staff_user = get_user_model().objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password123',
            is_staff=True
        )
        self.regular_user = get_user_model().objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='password123'
        )

        # Create a game score
        self.game_score = GameScore.objects.create(
            user=self.regular_user,
            score=85.5
        )

    def test_game_score_model_registered_in_admin(self):
        """Test GameScore model is registered in admin."""
        self.assertIn(
            GameScore,
            admin.site._registry,
            'GameScore model should be registered in admin site'
        )

    def test_game_score_module_appears_in_admin_index(self):
        """Test that Game Scores module appears in admin index."""
        self.client.force_login(self.superuser)
        url = reverse('admin:index')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Game scores')

    def test_game_score_module_appears_for_staff(self):
        """Test that Game Scores module appears in admin index
        for staff user."""
        staff_user = get_user_model().objects.create_user(
            username='staffuser0',
            email='staff0@example.com',
            password='password123',
            is_staff=True
        )
        self.client.force_login(staff_user)
        url = reverse('admin:index')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Game scores')

    def test_superuser_can_view_game_score_list(self):
        """Test that superuser can view the game score list."""
        self.client.force_login(self.superuser)
        url = reverse('admin:game_gamescore_changelist')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.regular_user.username)
        self.assertContains(res, '85.5')

    def test_staff_can_view_game_score_list(self):
        """Test that staff can view the game score list."""
        self.client.force_login(self.staff_user)
        url = reverse('admin:game_gamescore_changelist')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.regular_user.username)
        self.assertContains(res, '85.5')

    def test_superuser_can_delete_game_score(self):
        """Test that superuser can delete game scores."""
        self.client.force_login(self.superuser)
        url = reverse(
            'admin:game_gamescore_delete',
            args=[self.game_score.id]
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_staff_cannot_delete_game_score(self):
        """Test that staff cannot delete game scores."""
        self.client.force_login(self.staff_user)
        url = reverse(
            'admin:game_gamescore_delete',
            args=[self.game_score.id]
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, 403)

    def test_no_one_can_add_game_score(self):
        """Test that no one can add game score via admin."""
        self.client.force_login(self.superuser)
        url = reverse('admin:game_gamescore_add')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 403)

    def test_staff_cannot_add_game_score(self):
        """Test that staff cannot add game score."""
        self.client.force_login(self.staff_user)
        url = reverse('admin:game_gamescore_add')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 403)

    def test_change_page_read_only_for_superuser(self):
        """Test that change page loads in read-only mode for superuser."""
        self.client.force_login(self.superuser)
        url = reverse(
            'admin:game_gamescore_change',
            args=[self.game_score.id]
        )
        res = self.client.get(url)
        # Django returns 200 with read-only display when
        # has_change_permission is False
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.regular_user.username)
        self.assertContains(res, '85.5')
