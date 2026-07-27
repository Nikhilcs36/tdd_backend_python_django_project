"""
Tests for the seed_data management command.
"""
from datetime import timedelta
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from core.models import User, LoginActivity
from game.models import GameScore


class SeedDataCommandTests(TestCase):
    """Test the seed_data management command."""

    def setUp(self):
        """Ensure clean state before each test."""
        # The command checks if users exist, so we start with empty DB
        pass

    def test_creates_users(self):
        """Test that seed_data creates 5 users with correct usernames."""
        call_command('seed_data')
        self.assertEqual(User.objects.count(), 5)

        usernames = set(User.objects.values_list('username', flat=True))
        expected = {'admin', 'normal', 'staff', 'abcd', 'testuser'}
        self.assertEqual(usernames, expected)

    def test_admin_user(self):
        """Test admin user has correct role and credentials."""
        call_command('seed_data')
        admin = User.objects.get(username='admin')
        self.assertEqual(admin.email, 'admin@demo.com')
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.email_verified)
        self.assertEqual(admin.active_role, 'superuser')
        self.assertTrue(admin.check_password('Admin@123'))

    def test_regular_user(self):
        """Test regular user has no staff access."""
        call_command('seed_data')
        normal = User.objects.get(username='normal')
        self.assertEqual(normal.email, 'normal@demo.com')
        self.assertFalse(normal.is_superuser)
        self.assertFalse(normal.is_staff)
        self.assertTrue(normal.email_verified)
        self.assertEqual(normal.active_role, 'regular')
        self.assertTrue(normal.check_password('Test@123456'))

    def test_staff_user(self):
        """Test staff user has staff access."""
        call_command('seed_data')
        staff = User.objects.get(username='staff')
        self.assertEqual(staff.email, 'staff@demo.com')
        self.assertFalse(staff.is_superuser)
        self.assertTrue(staff.is_staff)
        self.assertTrue(staff.email_verified)
        self.assertEqual(staff.active_role, 'staff')
        self.assertTrue(staff.check_password('Test@123456'))

    def test_testuser_no_staff_access(self):
        """Test testuser has no staff access and no activity."""
        call_command('seed_data')
        testuser = User.objects.get(username='testuser')
        self.assertEqual(testuser.email, 'testuser@demo.com')
        self.assertFalse(testuser.staff_access_granted)
        self.assertFalse(testuser.is_staff)
        self.assertEqual(testuser.active_role, 'regular')

    def test_abcd_unverified(self):
        """Test abcd user is created as unverified."""
        call_command('seed_data')
        abcd = User.objects.get(username='abcd')
        self.assertEqual(abcd.email, 'abcd@demo.com')
        self.assertFalse(abcd.email_verified)

    def test_creates_login_activities(self):
        """Test that seed_data creates login activity records."""
        call_command('seed_data')
        count = LoginActivity.objects.count()
        self.assertGreaterEqual(count, 100,
                                f'Expected at least 100 login activities, '
                                f'got {count}')

    def test_login_activities_span_3_months(self):
        """Test login activities span the last 3 months."""
        call_command('seed_data')
        now = timezone.now()
        three_months_ago = now - timedelta(days=90)

        # Get the earliest and latest login timestamps
        activities = LoginActivity.objects.all()
        earliest = activities.earliest('timestamp')
        latest = activities.latest('timestamp')

        # Earliest should be within the last 3 months
        self.assertGreaterEqual(
            earliest.timestamp, three_months_ago,
            f'Earliest login {earliest.timestamp} is older than 3 months'
        )
        # Latest should be recent (within last day)
        self.assertLessEqual(
            latest.timestamp, now + timedelta(minutes=5),
            f'Latest login {latest.timestamp} is in the future'
        )

    def test_creates_game_scores(self):
        """Test that seed_data creates game score records."""
        call_command('seed_data')
        count = GameScore.objects.count()
        self.assertGreaterEqual(count, 10,
                                f'Expected at least 10 game scores, '
                                f'got {count}')

    def test_game_scores_have_valid_scores(self):
        """Test game scores are within valid range (0-100)."""
        call_command('seed_data')
        for score in GameScore.objects.all():
            self.assertGreaterEqual(score.score, 0.0)
            self.assertLessEqual(score.score, 100.0)

    def test_idempotent(self):
        """Test running seed_data twice doesn't create duplicates."""
        call_command('seed_data')
        first_count_users = User.objects.count()
        first_count_logins = LoginActivity.objects.count()
        first_count_scores = GameScore.objects.count()

        # Run again
        call_command('seed_data')

        self.assertEqual(User.objects.count(), first_count_users)
        self.assertEqual(LoginActivity.objects.count(), first_count_logins)
        self.assertEqual(GameScore.objects.count(), first_count_scores)

    def test_all_users_can_login_with_demo_passwords(self):
        """Test all users can authenticate with their demo passwords."""
        call_command('seed_data')
        password_map = {
            'admin': 'Admin@123',
        }
        default_password = 'Test@123456'

        for user in User.objects.all():
            password = password_map.get(user.username, default_password)
            self.assertTrue(
                user.check_password(password),
                f'Password check failed for {user.username}'
            )

    def test_login_activities_have_varied_success(self):
        """Test login activities have a mix of success and failure."""
        call_command('seed_data')
        successful = LoginActivity.objects.filter(success=True).count()
        failed = LoginActivity.objects.filter(success=False).count()

        self.assertGreater(successful, failed,
                           'Expected more successful logins than failures')
        # At least some failures should exist
        self.assertGreaterEqual(failed, 5,
                                f'Expected at least 5 failed logins, '
                                f'got {failed}')
