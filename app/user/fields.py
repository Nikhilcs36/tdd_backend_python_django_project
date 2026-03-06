"""Custom DRF fields for user app."""
from django.conf import settings
from rest_framework import serializers


class RelativeURLFileField(serializers.FileField):
    """
    A FileField that returns relative URLs instead of absolute URLs.

    Returns: /media/uploads/user/image.jpg
    Instead of: http://backend:8000/media/uploads/user/image.jpg
    """

    def to_representation(self, value):
        """Return relative URL for the file."""
        if not value:
            return None
        return f"{settings.MEDIA_URL}{value.name}"
