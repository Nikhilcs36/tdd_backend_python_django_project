"""
Management command to seed the database with sample data.
This generates realistic demo data so that new users
can see a fully populated application immediately.

Data is generated programmatically to ensure dates are always
relative to the current time (last 3 months).
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from core.models import User, LoginActivity
from game.models import GameScore

# Seed for reproducibility - same data every time
RANDOM_SEED = 42

# User definitions: (username, email, is_superuser, is_staff,
#                    email_verified, staff_access_granted, active_role)
USERS = [
    ('admin', 'admin@demo.com', True, True, True, True, 'superuser'),
    ('normal', 'normal@demo.com', False, False, True, True, 'regular'),
    ('staff', 'staff@demo.com', False, True, True, True, 'staff'),
    ('abcd', 'abcd@demo.com', False, False, False, False, 'regular'),
    ('testuser', 'testuser@demo.com', False, False, True, False, 'regular'),
]

# Password for admin
ADMIN_PASSWORD = 'Admin@123'
# Default password for all other users
DEFAULT_PASSWORD = 'Test@123456'

# User agents to choose from
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 '
    '(KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'PostmanRuntime/7.53.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148',
]

# IP addresses to choose from
IP_ADDRESSES = [
    '172.20.0.1', '172.20.0.2', '172.20.0.3',
    '192.168.1.100', '192.168.1.101', '192.168.1.102',
    '10.0.0.1', '10.0.0.2',
    '203.0.113.1', '203.0.113.2',
]


def _get_user_login_targets():
    """
    Return the number of login activities to generate per user.
    Total ~135 logins across all users.
    """
    return {
        'admin': 100,       # Most active
        'normal': 25,
        'staff': 10,
        'abcd': 0,          # Unverified - no activity
        'testuser': 0,      # No activity
    }


def _get_game_score_data():
    """
    Return game scores to generate.
    Each entry: (username, score)
    Total ~13 scores.
    """
    return [
        ('admin', 65.7), ('admin', 69.7), ('admin', 78.3),
        ('admin', 72.1), ('admin', 85.0), ('admin', 88.4),
        ('normal', 59.6), ('normal', 63.2), ('normal', 71.5),
        ('normal', 55.0),
        ('staff', 92.1), ('staff', 88.7), ('staff', 95.0),
    ]


class Command(BaseCommand):
    """Django command to seed the database with sample data."""

    help = 'Seeds the database with 3 months of sample data'

    def _create_users(self):
        """Create demo users."""
        for username, email, is_super, is_staff, email_verified, \
                staff_granted, active_role in USERS:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=DEFAULT_PASSWORD,
                is_superuser=is_super,
                is_staff=is_staff,
                email_verified=email_verified,
                staff_access_granted=staff_granted,
                active_role=active_role,
            )
            # Set admin password separately
            if username == 'admin':
                user.set_password(ADMIN_PASSWORD)
                user.save(update_fields=['password'])

        self.stdout.write(
            self.style.SUCCESS(f'  ✓ Created {len(USERS)} users')
        )

    def _create_login_activities(self):
        """Create login activities spanning the last 3 months."""
        now = timezone.now()
        three_months_ago = now - timedelta(days=90)
        rng = random.Random(RANDOM_SEED)

        user_map = {
            u.username: u for u in User.objects.all()
        }
        login_targets = _get_user_login_targets()
        total_created = 0

        for username, count in login_targets.items():
            user = user_map[username]
            for _ in range(count):
                # Random timestamp within the last 3 months
                random_seconds = rng.randint(
                    0, int((now - three_months_ago).total_seconds())
                )
                timestamp = three_months_ago + timedelta(
                    seconds=random_seconds
                )

                # 90% success rate
                success = rng.random() < 0.9

                LoginActivity.objects.create(
                    user=user,
                    timestamp=timestamp,
                    ip_address=rng.choice(IP_ADDRESSES),
                    user_agent=rng.choice(USER_AGENTS),
                    success=success,
                )
                total_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ Created {total_created} login activities'
            )
        )

    def _create_game_scores(self):
        """Create game scores with timestamps in the last 3 months."""
        now = timezone.now()
        three_months_ago = now - timedelta(days=90)
        rng = random.Random(RANDOM_SEED)

        user_map = {
            u.username: u for u in User.objects.all()
        }
        scores_data = _get_game_score_data()
        total_created = 0

        for username, score in scores_data:
            user = user_map[username]

            # Random timestamp within the last 3 months
            random_seconds = rng.randint(
                0, int((now - three_months_ago).total_seconds())
            )
            timestamp = three_months_ago + timedelta(
                seconds=random_seconds
            )

            GameScore.objects.create(
                user=user,
                score=score,
                created_at=timestamp,
            )
            total_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ Created {total_created} game scores'
            )
        )

    def _reset_passwords(self):
        """
        Reset all user passwords to known demo passwords.
        (Double-check to ensure passwords match expected values.)
        """
        for user in User.objects.all():
            if user.username == 'admin':
                user.set_password(ADMIN_PASSWORD)
            else:
                user.set_password(DEFAULT_PASSWORD)
            user.save(update_fields=['password'])

        self.stdout.write(
            self.style.SUCCESS('  ✓ Reset passwords for all users')
        )
        self.stdout.write('    ────────────────────────────────────')
        self.stdout.write('    Demo Credentials:')
        self.stdout.write('    ────────────────────────────────────')
        self.stdout.write(
            '    admin (superuser): admin@demo.com / Admin@123'
        )
        self.stdout.write(
            '    normal (regular):  normal@demo.com / Test@123456'
        )
        self.stdout.write(
            '    staff (staff):     staff@demo.com / Test@123456'
        )
        self.stdout.write(
            '    abcd (regular):    abcd@demo.com / Test@123456'
        )
        self.stdout.write(
            '    testuser (regular): '
            'testuser@demo.com / Test@123456'
        )
        self.stdout.write('    ────────────────────────────────────')

    def handle(self, *args, **options):
        """Entrypoint for command."""
        # Check if data already exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM core_user")
            user_count = cursor.fetchone()[0]

        if user_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Database already has {user_count} user(s). '
                    'Skipping seed data load.'
                )
            )
            return

        self.stdout.write(
            'Generating 3 months of demo data (this may take a moment)...'
        )

        self._create_users()
        self._create_login_activities()
        self._create_game_scores()
        self._reset_passwords()

        self.stdout.write(self.style.SUCCESS('Seed data loaded successfully!'))
