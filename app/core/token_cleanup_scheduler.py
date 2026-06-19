"""
Scheduler for daily token cleanup.

Uses the `schedule` library to run cleanup_blacklisted_tokens --days 1
every 24 hours in a background daemon thread. This prevents the
OutstandingToken and BlacklistedToken tables from growing indefinitely.

The scheduler is started automatically when Django starts
(via core/apps.py -> CoreConfig.ready()).
"""
import logging
import threading
import schedule
import time
from django.core.management import call_command

logger = logging.getLogger(__name__)

# Threading event to ensure the scheduler starts only once
_scheduler_started = threading.Event()


def run_cleanup():
    """Execute the cleanup_blacklisted_tokens management command."""
    logger.info('Running scheduled cleanup of expired tokens...')
    try:
        call_command('cleanup_blacklisted_tokens', days=1)
    except Exception as e:
        logger.error('Token cleanup failed: %s', e, exc_info=True)


def _run_pending_loop():
    """
    Continuously run pending scheduled jobs.

    This function runs indefinitely in a daemon thread.
    """
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_scheduler():
    """
    Start the daily token cleanup scheduler in a background thread.

    This function is idempotent: calling it more than once will
    not create additional threads or duplicate scheduled jobs.
    Uses a daemon thread so it does not block Django from shutting down.
    """
    if _scheduler_started.is_set():
        return

    # Schedule the cleanup job to run every day
    schedule.every(1).day.do(run_cleanup)

    # Start the scheduler loop in a daemon thread
    thread = threading.Thread(
        target=_run_pending_loop,
        daemon=True,
    )
    thread.start()

    _scheduler_started.set()
    logger.info(
        'Daily token cleanup scheduler started (interval: 24 hours).'
    )
