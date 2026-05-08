"""RSA key management utility for encrypting/decrypting login credentials.

This module provides functions to generate RSA key pairs, load them,
and encrypt/decrypt data using RSA-OAEP with SHA-256.
"""
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from django.conf import settings

# Default key directory relative to the project root
DEFAULT_KEY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'keys'
)
DEFAULT_PRIVATE_KEY_PATH = os.path.join(DEFAULT_KEY_DIR, 'private.pem')
DEFAULT_PUBLIC_KEY_PATH = os.path.join(DEFAULT_KEY_DIR, 'public.pem')


def get_private_key_path() -> str:
    """Get the private key path from Django settings or default."""
    return getattr(settings, 'RSA_PRIVATE_KEY_PATH', DEFAULT_PRIVATE_KEY_PATH)


def get_public_key_path() -> str:
    """Get the public key path from Django settings or default."""
    return getattr(settings, 'RSA_PUBLIC_KEY_PATH', DEFAULT_PUBLIC_KEY_PATH)


def ensure_keys_exist(
    private_key_path: str = DEFAULT_PRIVATE_KEY_PATH,
    public_key_path: str = DEFAULT_PUBLIC_KEY_PATH
) -> None:
    """Ensure RSA key pair files exist, generating them if necessary.

    This is called at server startup so keys are always available
    without needing to manually run generate_rsa_keys.

    Args:
        private_key_path: Path to the private key PEM file.
        public_key_path: Path to the public key PEM file.
    """
    if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
        generate_rsa_key_pair(private_key_path, public_key_path)


def generate_rsa_key_pair(
    private_key_path: str = DEFAULT_PRIVATE_KEY_PATH,
    public_key_path: str = DEFAULT_PUBLIC_KEY_PATH,
    key_size: int = 2048
) -> None:
    """Generate RSA key pair and save to files.

    Args:
        private_key_path: Path to save the private key PEM file.
        public_key_path: Path to save the public key PEM file.
        key_size: Size of the RSA key in bits (default: 2048).
    """
    # Ensure the key directory exists
    os.makedirs(os.path.dirname(private_key_path), exist_ok=True)
    os.makedirs(os.path.dirname(public_key_path), exist_ok=True)

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )

    # Serialize private key to PEM
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Write private key to file
    with open(private_key_path, 'wb') as f:
        f.write(private_key_pem)

    # Get public key
    public_key = private_key.public_key()

    # Serialize public key to PEM
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Write public key to file
    with open(public_key_path, 'wb') as f:
        f.write(public_key_pem)


def load_private_key(private_key_path: str = DEFAULT_PRIVATE_KEY_PATH):
    """Load a private key from a PEM file.

    Args:
        private_key_path: Path to the private key PEM file.

    Returns:
        The private key object.

    Raises:
        FileNotFoundError: If the key file doesn't exist.
    """
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(
            f"Private key not found at: {private_key_path}"
        )

    with open(private_key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    return private_key


def load_public_key(public_key_path: str = DEFAULT_PUBLIC_KEY_PATH):
    """Load a public key from a PEM file.

    Args:
        public_key_path: Path to the public key PEM file.

    Returns:
        The public key object.

    Raises:
        FileNotFoundError: If the key file doesn't exist.
    """
    if not os.path.exists(public_key_path):
        raise FileNotFoundError(
            f"Public key not found at: {public_key_path}"
        )

    with open(public_key_path, 'rb') as f:
        public_key = serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )
    return public_key


def encrypt_data(public_key, data: str) -> bytes:
    """Encrypt data using RSA-OAEP with SHA-256.

    Args:
        public_key: The public key to encrypt with.
        data: The string data to encrypt.

    Returns:
        The encrypted data as bytes.
    """
    return public_key.encrypt(
        data.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def decrypt_data(private_key, encrypted_data: bytes) -> str:
    """Decrypt data using RSA-OAEP with SHA-256.

    Args:
        private_key: The private key to decrypt with.
        encrypted_data: The encrypted data bytes to decrypt.

    Returns:
        The decrypted string data.
    """
    decrypted_bytes = private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_bytes.decode('utf-8')