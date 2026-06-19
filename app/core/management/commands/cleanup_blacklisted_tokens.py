"""
Management command to clean up expired outstanding tokens and their
associated blacklisted token entries.

This command removes:
- OutstandingToken records that have expired (expires_at < now)
- Associated BlacklistedToken records (via cascade delete)

Run this periodically (e.g., daily via cron) to prevent the
token_blacklist tables from growing indefinitely.
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Clean up expired outstanding tokens and their blacklist entries."""

    help = (
        "Remove expired outstanding tokens and their associated "
        "blacklisted tokens."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help=(
                "Only delete tokens that expired more than this many "
                "days ago. If not set, deletes all expired tokens."
            ),
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help="Show what would be deleted without actually deleting.",
        )

    def handle(self, *args, **options):
        """Execute the cleanup command."""
        now = timezone.now()
        days = options.get('days')
        dry_run = options.get('dry_run')

        # Determine the cutoff datetime
        if days is not None:
            cutoff = now - timedelta(days=days)
        else:
            cutoff = now

        # Query expired outstanding tokens
        expired_qs = OutstandingToken.objects.filter(
            expires_at__lt=cutoff
        )

        expired_count = expired_qs.count()

        if expired_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    'No expired tokens found to clean up.'
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would delete {expired_count} expired '
                    f'outstanding token(s) and their associated '
                    f'blacklisted token(s).'
                )
            )
            return

        # Delete expired outstanding tokens
        # BlacklistedToken entries are cascade-deleted automatically
        expired_qs.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {expired_count} expired '
                f'outstanding token(s) and their associated '
                f'blacklisted token(s).'
            )
        )
