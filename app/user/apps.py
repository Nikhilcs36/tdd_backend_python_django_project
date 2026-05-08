from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user'

    def ready(self):
        """Auto-generate RSA keys if they don't exist on startup."""
        from user.rsa_key_manager import ensure_keys_exist
        ensure_keys_exist()
