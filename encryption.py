"""
Encryption utilities for storing sensitive API keys
Uses Fernet (symmetric encryption) from cryptography library
"""
import os
from cryptography.fernet import Fernet
from typing import Tuple

# Encryption key - should be stored as environment variable
# Generate once with: Fernet.generate_key().decode()
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', None)

def generate_encryption_key() -> str:
    """
    Generate a new encryption key
    Run this ONCE and store the result in your environment variables

    Returns:
        str: Base64-encoded encryption key
    """
    key = Fernet.generate_key()
    return key.decode()

def get_fernet() -> Fernet:
    """
    Get Fernet cipher instance

    Returns:
        Fernet: Cipher instance

    Raises:
        ValueError: If ENCRYPTION_KEY not set
    """
    if not ENCRYPTION_KEY:
        raise ValueError(
            "ENCRYPTION_KEY environment variable not set. "
            "Generate one with: python -c 'from encryption import generate_encryption_key; print(generate_encryption_key())'"
        )
    return Fernet(ENCRYPTION_KEY.encode())

def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key

    Args:
        api_key: Plain text API key

    Returns:
        str: Encrypted API key (base64 encoded)
    """
    f = get_fernet()
    encrypted = f.encrypt(api_key.encode())
    return encrypted.decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an API key

    Args:
        encrypted_key: Encrypted API key (base64 encoded string)

    Returns:
        str: Plain text API key
    """
    f = get_fernet()
    decrypted = f.decrypt(encrypted_key.encode())
    return decrypted.decode()

def encrypt_alpaca_keys(api_key: str, secret_key: str) -> Tuple[str, str]:
    """
    Encrypt both Alpaca API key and secret

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key

    Returns:
        tuple: (encrypted_api_key, encrypted_secret_key)
    """
    return (
        encrypt_api_key(api_key),
        encrypt_api_key(secret_key)
    )

def decrypt_alpaca_keys(encrypted_api_key: str, encrypted_secret_key: str) -> Tuple[str, str]:
    """
    Decrypt both Alpaca API key and secret

    Args:
        encrypted_api_key: Encrypted API key
        encrypted_secret_key: Encrypted secret key

    Returns:
        tuple: (api_key, secret_key)
    """
    return (
        decrypt_api_key(encrypted_api_key),
        decrypt_api_key(encrypted_secret_key)
    )

# For testing/setup
if __name__ == "__main__":
    print("=== Encryption Key Generator ===")
    print("\nGenerate a new encryption key:")
    print(f"ENCRYPTION_KEY={generate_encryption_key()}")
    print("\n⚠️  Save this key to your environment variables (Replit Secrets)")
    print("⚠️  Never commit this key to git!")
    print("\nExample usage:")
    print("  export ENCRYPTION_KEY='your-generated-key-here'")
