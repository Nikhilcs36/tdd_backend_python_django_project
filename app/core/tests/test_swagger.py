from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SwaggerTests(APITestCase):
    """Test the swagger documentation."""

    def test_swagger_ui_is_available(self):
        """Test that the swagger ui is available."""
        url = reverse('api-docs')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_schema_is_available(self):
        """Test that the swagger schema is available."""
        url = reverse('api-schema')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
