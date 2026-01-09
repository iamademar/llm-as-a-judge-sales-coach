"""
JWT token creation and decoding.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict

import jwt

from app.core.jwt_config import jwt_settings


def create_access_token(sub: str) -> str:
    """
    Create a JWT access token.

    Args:
        sub: Subject identifier (typically user ID)

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expire = now + jwt_settings.access_token_expires

    payload = {
        "sub": sub,
        "type": "access",
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, jwt_settings.secret, algorithm=jwt_settings.algorithm)


def create_refresh_token(sub: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        sub: Subject identifier (typically user ID)

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expire = now + jwt_settings.refresh_token_expires

    payload = {
        "sub": sub,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, jwt_settings.secret, algorithm=jwt_settings.algorithm)


def decode_token(token: str) -> Dict:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload as dictionary

    Raises:
        jwt.InvalidTokenError: If token is invalid or expired
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidSignatureError: If token signature is invalid
    """
    return jwt.decode(token, jwt_settings.secret, algorithms=[jwt_settings.algorithm])
