"""
Encryption utilities for secure API key storage.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC).
Encryption key must be set via ENCRYPTION_KEY environment variable.
"""
import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    """
    Get Fernet instance using encryption key from environment.

    Returns:
        Configured Fernet instance

    Raises:
        ValueError: If ENCRYPTION_KEY is not set or invalid
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "ENCRYPTION_KEY environment variable is required for credential encryption. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    try:
        # Ensure key is properly encoded
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key)
    except Exception as e:
        raise ValueError(
            f"Invalid ENCRYPTION_KEY format. Must be a valid Fernet key. Error: {e}"
        )


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for secure storage.

    Args:
        api_key: Plain text API key

    Returns:
        Base64-encoded encrypted string

    Raises:
        ValueError: If encryption key is not configured
    """
    if not api_key:
        raise ValueError("API key cannot be empty")

    fernet = _get_fernet()
    encrypted = fernet.encrypt(api_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an encrypted API key.

    Args:
        encrypted_key: Base64-encoded encrypted string

    Returns:
        Decrypted plain text API key

    Raises:
        ValueError: If decryption fails or key is invalid
    """
    if not encrypted_key:
        raise ValueError("Encrypted key cannot be empty")

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except InvalidToken:
        raise ValueError(
            "Failed to decrypt API key. The encryption key may have changed."
        )


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """
    Mask an API key for display, showing only the last few characters.

    Args:
        api_key: Plain text API key
        visible_chars: Number of characters to show at the end (default: 4)

    Returns:
        Masked string like "****...xxxx"
    """
    if not api_key:
        return ""

    if len(api_key) <= visible_chars:
        return "*" * len(api_key)

    return f"****...{api_key[-visible_chars:]}"


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded encryption key string

    Note:
        Use this to generate ENCRYPTION_KEY for your environment.
    """
    return Fernet.generate_key().decode()


def validate_api_key_format(provider: str, api_key: str) -> Optional[str]:
    """
    Validate API key format for a given provider.

    Args:
        provider: LLM provider name (openai, anthropic, google)
        api_key: API key to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not api_key or not api_key.strip():
        return "API key cannot be empty"

    api_key = api_key.strip()

    # Provider-specific format validation
    if provider == "openai":
        if not api_key.startswith("sk-"):
            return "OpenAI API keys should start with 'sk-'"
        if len(api_key) < 20:
            return "OpenAI API key appears too short"

    elif provider == "anthropic":
        if not api_key.startswith("sk-ant-"):
            return "Anthropic API keys should start with 'sk-ant-'"
        if len(api_key) < 20:
            return "Anthropic API key appears too short"

    elif provider == "google":
        # Google API keys have varied formats
        if len(api_key) < 10:
            return "Google API key appears too short"

    return None

