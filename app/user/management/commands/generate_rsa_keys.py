"""
Management command to generate RSA key pair for login encryption.

This command generates an RSA public/private key pair and saves them
to the specified files (or default locations). The public key is served
to the frontend for encrypting login credentials, and the private key
is used by the backend to decrypt them.

Usage:
    python manage.py generate_rsa_keys
    python manage.py generate_rsa_keys --private-key-path=path/to/private.pem
    python manage.py generate_rsa_keys --public-key-path=path/to/public.pem
"""
from django.core.management.base import BaseCommand
from user.rsa_key_manager import generate_rsa_key_pair


class Command(BaseCommand):
    """Generate RSA key pair for login credential encryption."""
    help = 'Generate RSA key pair for encrypting login credentials'

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            '--private-key-path',
            type=str,
            help='Path to save the private key PEM file'
        )
        parser.add_argument(
            '--public-key-path',
            type=str,
            help='Path to save the public key PEM file'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        private_key_path = options.get('private_key_path')
        public_key_path = options.get('public_key_path')

        kwargs = {}
        if private_key_path:
            kwargs['private_key_path'] = private_key_path
        if public_key_path:
            kwargs['public_key_path'] = public_key_path

        generate_rsa_key_pair(**kwargs)

        self.stdout.write(
            self.style.SUCCESS('RSA key pair generated successfully')
        )