"""
Tests for JWT token creation and decoding.
"""
import pytest
from jwt.exceptions import InvalidSignatureError

from app.core.jwt_tokens import create_access_token, create_refresh_token, decode_token


def test_create_access_token_returns_valid_token():
    """Test that create_access_token returns a decodable token."""
    sub = "user123"
    token = create_access_token(sub)

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = decode_token(token)
    assert payload["sub"] == sub
    assert payload["type"] == "access"


def test_create_refresh_token_returns_valid_token():
    """Test that create_refresh_token returns a decodable token."""
    sub = "user456"
    token = create_refresh_token(sub)

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = decode_token(token)
    assert payload["sub"] == sub
    assert payload["type"] == "refresh"


def test_access_token_has_correct_type_claim():
    """Test that access token has type claim set to 'access'."""
    sub = "user789"
    token = create_access_token(sub)
    payload = decode_token(token)

    assert payload["type"] == "access"


def test_refresh_token_has_correct_type_claim():
    """Test that refresh token has type claim set to 'refresh'."""
    sub = "user101"
    token = create_refresh_token(sub)
    payload = decode_token(token)

    assert payload["type"] == "refresh"


def test_access_token_has_exp_claim():
    """Test that access token has expiration claim."""
    sub = "user202"
    token = create_access_token(sub)
    payload = decode_token(token)

    assert "exp" in payload
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > 0


def test_refresh_token_has_exp_claim():
    """Test that refresh token has expiration claim."""
    sub = "user303"
    token = create_refresh_token(sub)
    payload = decode_token(token)

    assert "exp" in payload
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > 0


def test_access_token_has_iat_claim():
    """Test that access token has issued at claim."""
    sub = "user404"
    token = create_access_token(sub)
    payload = decode_token(token)

    assert "iat" in payload
    assert isinstance(payload["iat"], int)
    assert payload["iat"] > 0


def test_decode_token_with_invalid_signature_raises_error():
    """Test that decode_token raises error for invalid signature."""
    # Create a valid token
    token = create_access_token("user505")

    # Tamper with the token
    parts = token.split(".")
    if len(parts) == 3:
        # Change one character in the signature
        tampered_token = f"{parts[0]}.{parts[1]}.{parts[2][:-1]}X"

        with pytest.raises(InvalidSignatureError):
            decode_token(tampered_token)


def test_decode_token_with_completely_invalid_token_raises_error():
    """Test that decode_token raises error for completely invalid token."""
    invalid_token = "not.a.valid.token"

    with pytest.raises(Exception):
        decode_token(invalid_token)


def test_refresh_token_exp_is_greater_than_access_token_exp():
    """Test that refresh token expiration is greater than access token."""
    sub = "user606"
    access_token = create_access_token(sub)
    refresh_token = create_refresh_token(sub)

    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_token)

    assert refresh_payload["exp"] > access_payload["exp"]
