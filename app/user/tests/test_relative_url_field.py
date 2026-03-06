"""Tests for RelativeURLFileField."""
from django.test import TestCase
from rest_framework import serializers
from unittest.mock import MagicMock

from user.fields import RelativeURLFileField


class TestSerializer(serializers.Serializer):
    """Test serializer using RelativeURLFileField."""
    image = RelativeURLFileField(required=False, allow_null=True)


class RelativeURLFileFieldTests(TestCase):
    """Test cases for RelativeURLFileField."""

    def test_returns_relative_url_with_media_url(self):
        """Test that the field returns a relative URL with MEDIA_URL prefix."""
        field = RelativeURLFileField()
        mock_file = MagicMock()
        mock_file.name = 'uploads/user/test-image.jpg'

        result = field.to_representation(mock_file)

        self.assertEqual(result, '/media/uploads/user/test-image.jpg')

    def test_returns_none_for_null_value(self):
        """Test that the field returns None when value is None."""
        field = RelativeURLFileField()

        result = field.to_representation(None)

        self.assertIsNone(result)

    def test_returns_none_for_empty_string(self):
        """Test that the field returns None when value is empty string."""
        field = RelativeURLFileField()

        result = field.to_representation('')

        self.assertIsNone(result)

    def test_serializer_outputs_relative_url(self):
        """Test serializer outputs relative URL in API response."""
        mock_file = MagicMock()
        mock_file.name = 'uploads/user/profile.png'

        serializer = TestSerializer({'image': mock_file})

        self.assertEqual(
            serializer.data['image'],
            '/media/uploads/user/profile.png'
        )

    def test_url_does_not_contain_domain(self):
        """Test that the returned URL does not contain http:// or domain."""
        field = RelativeURLFileField()
        mock_file = MagicMock()
        mock_file.name = 'uploads/user/photo.jpg'

        result = field.to_representation(mock_file)

        self.assertNotIn('http://', result)
        self.assertNotIn('https://', result)
        self.assertNotIn('backend:8000', result)
        self.assertTrue(result.startswith('/media/'))
