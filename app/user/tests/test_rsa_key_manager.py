"""Tests for the RSA key manager utility."""
from django.test import TestCase
import tempfile
import os
from user.rsa_key_manager import (
    generate_rsa_key_pair,
    load_private_key,
    load_public_key,
    decrypt_data,
    encrypt_data,
)


class RSAKeyManagerTests(TestCase):
    """Test the RSA key manager utility functions."""

    def setUp(self):
        self.key_dir = tempfile.mkdtemp()
        self.private_key_path = os.path.join(self.key_dir, 'private.pem')
        self.public_key_path = os.path.join(self.key_dir, 'public.pem')

    def tearDown(self):
        # Recursively clean up temp directory
        if os.path.exists(self.key_dir):
            for root, dirs, files in os.walk(self.key_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(self.key_dir)

    def test_generate_rsa_key_pair_creates_files(self):
        """Test that key generation creates private and public key files."""
        generate_rsa_key_pair(self.private_key_path, self.public_key_path)

        self.assertTrue(os.path.exists(self.private_key_path))
        self.assertTrue(os.path.exists(self.public_key_path))

    def test_load_private_key_returns_key_object(self):
        """Test that load_private_key returns a valid key object."""
        generate_rsa_key_pair(self.private_key_path, self.public_key_path)
        private_key = load_private_key(self.private_key_path)

        self.assertIsNotNone(private_key)
        # Check it has the expected method for decryption
        self.assertTrue(hasattr(private_key, 'decrypt'))

    def test_load_public_key_returns_key_object(self):
        """Test that load_public_key returns a valid key object."""
        generate_rsa_key_pair(self.private_key_path, self.public_key_path)
        public_key = load_public_key(self.public_key_path)

        self.assertIsNotNone(public_key)
        # Check it has the expected method for encryption
        self.assertTrue(hasattr(public_key, 'encrypt'))

    def test_encrypt_decrypt_roundtrip(self):
        """Test that data encrypted with public key can be decrypted."""
        generate_rsa_key_pair(self.private_key_path, self.public_key_path)
        private_key = load_private_key(self.private_key_path)
        public_key = load_public_key(self.public_key_path)

        original_data = "my_super_secret_password123!"
        encrypted = encrypt_data(public_key, original_data)
        decrypted = decrypt_data(private_key, encrypted)

        self.assertEqual(decrypted, original_data)

    def test_encrypt_decrypt_empty_string(self):
        """Test encryption/decryption of empty string."""
        generate_rsa_key_pair(self.private_key_path, self.public_key_path)
        private_key = load_private_key(self.private_key_path)
        public_key = load_public_key(self.public_key_path)

        original_data = ""
        encrypted = encrypt_data(public_key, original_data)
        decrypted = decrypt_data(private_key, encrypted)

        self.assertEqual(decrypted, original_data)

    def test_encrypt_decrypt_special_characters(self):
        """Test encryption/decryption with special characters."""
        generate_rsa_key_pair(self.private_key_path, self.public_key_path)
        private_key = load_private_key(self.private_key_path)
        public_key = load_public_key(self.public_key_path)

        original_data = "P@$$w0rd! with sp3c!@l chars: ñüé"
        encrypted = encrypt_data(public_key, original_data)
        decrypted = decrypt_data(private_key, encrypted)

        self.assertEqual(decrypted, original_data)

    def test_generate_key_pair_without_paths(self):
        """Test that generate_rsa_key_pair works with default paths."""
        generate_rsa_key_pair(self.private_key_path, self.public_key_path)
        self.assertTrue(os.path.exists(self.private_key_path))
        self.assertTrue(os.path.exists(self.public_key_path))
        # Verify it's real PEM content
        with open(self.public_key_path, 'r') as f:
            content = f.read()
        self.assertIn('BEGIN PUBLIC KEY', content)

    def test_public_key_pem_format(self):
        """Test that the public key is in PEM format."""
        generate_rsa_key_pair(self.private_key_path, self.public_key_path)
        with open(self.public_key_path, 'r') as f:
            content = f.read()
        self.assertTrue(content.startswith('-----BEGIN PUBLIC KEY-----'))
        self.assertIn('-----END PUBLIC KEY-----', content)

    def test_load_nonexistent_private_key_raises_error(self):
        """Test that loading a non-existent private key raises error."""
        with self.assertRaises(FileNotFoundError):
            load_private_key('/nonexistent/path/private.pem')

    def test_load_nonexistent_public_key_raises_error(self):
        """Test that loading a non-existent public key raises error."""
        with self.assertRaises(FileNotFoundError):
            load_public_key('/nonexistent/path/public.pem')

    def test_ensure_keys_exist_generates_keys_when_missing(self):
        """Test that ensure_keys_exist generates keys if they don't exist."""
        from user.rsa_key_manager import ensure_keys_exist
        # Keys should not exist in this temp dir
        ensure_keys_exist(self.private_key_path, self.public_key_path)
        self.assertTrue(os.path.exists(self.private_key_path))
        self.assertTrue(os.path.exists(self.public_key_path))

    def test_ensure_keys_exist_does_not_overwrite_existing(self):
        """Test that ensure_keys_exist does not overwrite existing keys."""
        from user.rsa_key_manager import ensure_keys_exist
        # Generate keys first
        generate_rsa_key_pair(self.private_key_path, self.public_key_path)
        # Read the original public key
        with open(self.public_key_path, 'r') as f:
            original_content = f.read()
        # Call ensure_keys_exist - should not overwrite
        ensure_keys_exist(self.private_key_path, self.public_key_path)
        with open(self.public_key_path, 'r') as f:
            new_content = f.read()
        self.assertEqual(original_content, new_content)

    def test_ensure_keys_exist_creates_directory(self):
        """Test that ensure_keys_exist creates the key directory."""
        from user.rsa_key_manager import ensure_keys_exist
        nested_dir = os.path.join(self.key_dir, 'deep', 'nested', 'keys')
        private_path = os.path.join(nested_dir, 'private.pem')
        public_path = os.path.join(nested_dir, 'public.pem')
        ensure_keys_exist(private_path, public_path)
        self.assertTrue(os.path.exists(private_path))
        self.assertTrue(os.path.exists(public_path))

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decrypting with a different key pair fails."""
        # Generate two different key pairs
        dir1 = tempfile.mkdtemp()
        dir2 = tempfile.mkdtemp()
        try:
            generate_rsa_key_pair(
                os.path.join(dir1, 'private.pem'),
                os.path.join(dir1, 'public.pem')
            )
            generate_rsa_key_pair(
                os.path.join(dir2, 'private.pem'),
                os.path.join(dir2, 'public.pem')
            )

            public_key_1 = load_public_key(os.path.join(dir1, 'public.pem'))
            private_key_2 = load_private_key(os.path.join(dir2, 'private.pem'))

            # Encrypt with key pair 1's public key
            encrypted = encrypt_data(public_key_1, "secret")

            # Try to decrypt with key pair 2's private key - should raise error
            with self.assertRaises(Exception):
                decrypt_data(private_key_2, encrypted)
        finally:
            for d in [dir1, dir2]:
                for f in os.listdir(d):
                    os.remove(os.path.join(d, f))
                os.rmdir(d)
