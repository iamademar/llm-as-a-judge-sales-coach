"""
Tests for password hashing and verification.
"""
from app.core.passwords import hash_password, verify_password


def test_hash_password_returns_hashed_string():
    """Test that hash_password returns a hashed string."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed != password
    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_verify_password_with_correct_password_returns_true():
    """Test that verify_password returns True for correct password."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_with_wrong_password_returns_false():
    """Test that verify_password returns False for wrong password."""
    password = "test_password_123"
    wrong_password = "wrong_password_456"
    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False


def test_hash_password_generates_different_hashes():
    """Test that hash_password generates different hashes for same password."""
    password = "test_password_123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Different salts should produce different hashes
    assert hash1 != hash2
    # But both should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
