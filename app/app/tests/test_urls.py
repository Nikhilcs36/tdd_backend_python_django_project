"""
Tests for the main app URLs.
"""
from django.test import TestCase
from django.conf import settings


class TestAppUrls(TestCase):
    """Test the URLs for the main app."""

    def test_media_url_is_served_in_debug(self):
        """Test that the media URL is served when DEBUG is True."""
        with self.settings(DEBUG=True):
            # We need to reload the urls to apply the new settings
            from app import urls
            import importlib
            importlib.reload(urls)

            self.assertTrue(
                any(
                    p.pattern.prefix == settings.MEDIA_URL.lstrip('/')
                    for p in urls.urlpatterns
                )
            )

    def test_media_url_is_not_served_in_production(self):
        """Test that the media URL is not served when DEBUG is False."""
        with self.settings(DEBUG=False):
            # We need to reload the urls to apply the new settings
            from app import urls
            import importlib
            importlib.reload(urls)

            self.assertFalse(
                any(
                    p.pattern.prefix == settings.MEDIA_URL.lstrip('/')
                    for p in urls.urlpatterns
                )
            )
