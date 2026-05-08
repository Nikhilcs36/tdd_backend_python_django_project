"""Tests for the user app configuration (auto-generation of RSA keys)."""
from django.test import TestCase
from django.apps import apps


class UserAppConfigTests(TestCase):
    """Test the UserConfig app configuration."""

    def test_user_app_is_configured(self):
        """Test that the user app is properly configured."""
        self.assertTrue(apps.is_installed('user'))

    def test_app_config_has_ready_method(self):
        """Test that UserConfig has a ready method for key generation."""
        from user.apps import UserConfig
        self.assertTrue(hasattr(UserConfig, 'ready'))
        self.assertTrue(callable(UserConfig.ready))
