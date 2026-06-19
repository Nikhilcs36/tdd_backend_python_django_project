from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        Start the daily token cleanup scheduler when Django starts.

        This runs the scheduler in a background daemon thread that
        calls cleanup_blacklisted_tokens --days 1 every 24 hours.
        """
        # Import here to avoid AppRegistryNotReady errors
        from core.token_cleanup_scheduler import start_scheduler
        start_scheduler()
