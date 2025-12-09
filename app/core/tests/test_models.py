from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import LoginActivity
from django.utils import timezone
from datetime import timedelta


class ModelTests(TestCase):
    def test_create_user_with_username_and_email_successful(self):
        """Test creating new user with username and email successfully"""
        username = 'testuser'
        email = 'test@example.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password=password
        )

        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertIsNotNone(user.id)  # Verify ID field exists
        self.assertIsNotNone(user.date_joined)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users"""
        username = 'testuser'
        email = 'test@EXAMPLE.COM'
        user = get_user_model().objects.create_user(
            username=username, email=email, password='test123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                username='testuser', email=None, password='test123')

    def test_create_superuser(self):
        """Test creating new superuser"""
        user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_user_with_duplicate_username(self):
        """Test creating a user with a duplicate username raises an error"""
        get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        with self.assertRaises(Exception):
            get_user_model().objects.create_user(
                username='testuser',
                email='test2@example.com',
                password='testpassword'
            )

    def test_create_user_with_duplicate_email(self):
        """Test creating a user with a duplicate email raises an error"""
        get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        with self.assertRaises(Exception):
            get_user_model().objects.create_user(
                username='testuser2',
                email='test@example.com',
                password='testpassword'
            )


class LoginActivityModelTests(TestCase):
    """Test the LoginActivity model functionality"""

    def setUp(self):
        """Set up test user for login activity tests"""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Testpass123'
        )

    def test_create_login_activity_successful(self):
        """Test creating a successful login activity record"""

        login_activity = LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 (Test Browser)',
            success=True
        )

        self.assertEqual(login_activity.user, self.user)
        self.assertEqual(login_activity.ip_address, '192.168.1.1')
        self.assertEqual(login_activity.user_agent,
                         'Mozilla/5.0 (Test Browser)')
        self.assertTrue(login_activity.success)
        self.assertIsNotNone(login_activity.timestamp)
        self.assertIsNotNone(login_activity.id)

    def test_create_login_activity_failed(self):
        """Test creating a failed login activity record"""

        login_activity = LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 (Test Browser)',
            success=False
        )

        self.assertEqual(login_activity.user, self.user)
        self.assertFalse(login_activity.success)

    def test_login_activity_ordering(self):
        """Test that login activities are ordered by timestamp descending"""

        # Create login activities with different timestamps
        LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Browser 1',
            success=True,
            timestamp=timezone.now() - timedelta(hours=1)
        )

        LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.2',
            user_agent='Browser 2',
            success=True,
            timestamp=timezone.now()
        )

        # Get all activities ordered by timestamp descending
        activities = LoginActivity.objects.all()

        # Most recent should be first
        self.assertEqual(activities[0].ip_address, '192.168.1.2')
        self.assertEqual(activities[1].ip_address, '192.168.1.1')

    def test_login_activity_string_representation(self):
        """Test the string representation of LoginActivity"""

        login_activity = LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            success=True
        )

        expected_str = f"LoginActivity for {self.user.username} at "\
                       f"{login_activity.timestamp}"
        self.assertEqual(str(login_activity), expected_str)

    def test_login_activity_without_user(self):
        """Test creating login activity without user raises error"""

        with self.assertRaises(Exception):
            LoginActivity.objects.create(
                ip_address='192.168.1.1',
                user_agent='Test Browser',
                success=True
            )


class UserStatisticsTests(TestCase):
    """Test user statistics functionality"""

    def setUp(self):
        """Set up test user for statistics tests"""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Testpass123'
        )

    def test_user_login_count_increment(self):
        """Test that user login_count increments on login"""

        # Initial login count should be 0
        self.assertEqual(self.user.login_count, 0)

        # Create a login activity
        LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            success=True
        )

        # Refresh user from database
        self.user.refresh_from_db()

        # Login count should now be 1
        self.assertEqual(self.user.login_count, 1)

        # Create another login activity
        LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.2',
            user_agent='Test Browser 2',
            success=True
        )

        # Refresh user from database
        self.user.refresh_from_db()

        # Login count should now be 2
        self.assertEqual(self.user.login_count, 2)

    def test_user_last_login_timestamp_update(self):
        """Test that last_login_timestamp updates on successful login"""

        # Initial last login should be None
        self.assertIsNone(self.user.last_login_timestamp)

        # Create a login activity
        login_time = timezone.now()
        LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            success=True,
            timestamp=login_time
        )

        # Refresh user from database
        self.user.refresh_from_db()

        # Last login timestamp should be updated
        self.assertIsNotNone(self.user.last_login_timestamp)
        # Check that the timestamp is approximately equal (within 1 second)
        time_difference = abs(
            (self.user.last_login_timestamp - login_time).total_seconds())
        self.assertLessEqual(time_difference, 1)

    def test_failed_login_does_not_update_stats(self):
        """Test that failed login doesn't update login count or timestamp"""

        initial_login_count = self.user.login_count
        initial_last_login = self.user.last_login_timestamp

        # Create a failed login activity
        LoginActivity.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            success=False
        )

        # Refresh user from database
        self.user.refresh_from_db()

        # Login count and last login should remain unchanged
        self.assertEqual(self.user.login_count, initial_login_count)
        self.assertEqual(self.user.last_login_timestamp, initial_last_login)
