"""Tests for the generate_rsa_keys management command."""
from django.test import TestCase
from django.core.management import call_command
import tempfile
import os


class GenerateRSAKeysCommandTests(TestCase):
    """Test the generate_rsa_keys management command."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.private_key_path = os.path.join(self.temp_dir, 'private.pem')
        self.public_key_path = os.path.join(self.temp_dir, 'public.pem')

    def tearDown(self):
        # Recursively clean up temp directory and all files
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(self.temp_dir)

    def test_command_generates_key_files(self):
        """Test that the manage.py command generates RSA key files."""
        call_command(
            'generate_rsa_keys',
            private_key_path=self.private_key_path,
            public_key_path=self.public_key_path
        )

        self.assertTrue(os.path.exists(self.private_key_path))
        self.assertTrue(os.path.exists(self.public_key_path))

    def test_command_generates_valid_pem_files(self):
        """Test that the command generates valid PEM key files."""
        call_command(
            'generate_rsa_keys',
            private_key_path=self.private_key_path,
            public_key_path=self.public_key_path
        )

        # Check public key PEM format
        with open(self.public_key_path, 'r') as f:
            public_content = f.read()
        self.assertIn('BEGIN PUBLIC KEY', public_content)
        self.assertIn('END PUBLIC KEY', public_content)

        # Check private key PEM format
        with open(self.private_key_path, 'r') as f:
            private_content = f.read()
        self.assertIn('BEGIN PRIVATE KEY', private_content)
        self.assertIn('END PRIVATE KEY', private_content)

    def test_command_creates_directory_if_not_exists(self):
        """Test that the command creates the key directory if it doesn't exist."""
        nested_dir = os.path.join(self.temp_dir, 'nested', 'keys')
        private_path = os.path.join(nested_dir, 'private.pem')
        public_path = os.path.join(nested_dir, 'public.pem')

        call_command(
            'generate_rsa_keys',
            private_key_path=private_path,
            public_key_path=public_path
        )

        self.assertTrue(os.path.exists(private_path))
        self.assertTrue(os.path.exists(public_path))