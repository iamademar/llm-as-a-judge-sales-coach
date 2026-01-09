"""
Tests for encryption utilities used for LLM credentials.

Tests the encryption functions in app.core.encryption:
- encrypt_api_key
- decrypt_api_key
- mask_api_key
- validate_api_key_format
- generate_encryption_key
"""
import pytest
import os

from app.core.encryption import (
    encrypt_api_key,
    decrypt_api_key,
    mask_api_key,
    validate_api_key_format,
    generate_encryption_key,
)


class TestEncryptDecrypt:
    """Tests for encrypt_api_key() and decrypt_api_key()"""

    def test_encrypt_decrypt_round_trip(self):
        """Test that encryption and decryption work correctly"""
        # Arrange
        original_key = "sk-test1234567890abcdef"

        # Act
        encrypted = encrypt_api_key(original_key)
        decrypted = decrypt_api_key(encrypted)

        # Assert
        assert encrypted != original_key
        assert decrypted == original_key

    def test_encrypt_different_keys_different_output(self):
        """Test that different keys produce different encrypted values"""
        # Arrange
        key1 = "sk-key1234567890abcdef"
        key2 = "sk-key0987654321fedcba"

        # Act
        encrypted1 = encrypt_api_key(key1)
        encrypted2 = encrypt_api_key(key2)

        # Assert
        assert encrypted1 != encrypted2

    def test_encrypt_same_key_different_output(self):
        """Test that encrypting same key twice gives different output (due to IV)"""
        # Arrange
        key = "sk-test1234567890abcdef"

        # Act
        encrypted1 = encrypt_api_key(key)
        encrypted2 = encrypt_api_key(key)

        # Assert
        # Fernet includes timestamp, so outputs will differ
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same value
        assert decrypt_api_key(encrypted1) == key
        assert decrypt_api_key(encrypted2) == key

    def test_encrypt_empty_key_raises_error(self):
        """Test that encrypting empty key raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            encrypt_api_key("")
        
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_decrypt_empty_key_raises_error(self):
        """Test that decrypting empty string raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            decrypt_api_key("")
        
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_decrypt_invalid_token_raises_error(self):
        """Test that decrypting invalid token raises ValueError"""
        # Arrange
        invalid_token = "not-a-valid-encrypted-token"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            decrypt_api_key(invalid_token)
        
        assert "decrypt" in str(exc_info.value).lower()

    def test_encrypt_long_key(self):
        """Test encrypting very long API key"""
        # Arrange
        long_key = "sk-" + "x" * 200

        # Act
        encrypted = encrypt_api_key(long_key)
        decrypted = decrypt_api_key(encrypted)

        # Assert
        assert decrypted == long_key

    def test_encrypt_special_characters(self):
        """Test encrypting keys with special characters"""
        # Arrange
        special_key = "sk-key_with-special.chars!@#$%"

        # Act
        encrypted = encrypt_api_key(special_key)
        decrypted = decrypt_api_key(encrypted)

        # Assert
        assert decrypted == special_key


class TestMaskApiKey:
    """Tests for mask_api_key()"""

    def test_mask_api_key_default(self):
        """Test masking with default visible chars (4)"""
        # Arrange
        key = "sk-test1234567890abcdef"

        # Act
        result = mask_api_key(key)

        # Assert
        assert result == "****...cdef"

    def test_mask_api_key_custom_visible_chars(self):
        """Test masking with custom number of visible chars"""
        # Arrange
        key = "sk-test1234567890abcdef"

        # Act
        result = mask_api_key(key, visible_chars=6)

        # Assert
        assert result == "****...abcdef"

    def test_mask_api_key_short_key(self):
        """Test masking key shorter than visible chars"""
        # Arrange
        key = "abc"

        # Act
        result = mask_api_key(key, visible_chars=4)

        # Assert
        assert result == "***"  # All stars

    def test_mask_api_key_empty(self):
        """Test masking empty string"""
        # Act
        result = mask_api_key("")

        # Assert
        assert result == ""

    def test_mask_api_key_exact_length(self):
        """Test masking key exactly equal to visible chars"""
        # Arrange
        key = "abcd"

        # Act
        result = mask_api_key(key, visible_chars=4)

        # Assert
        assert result == "****"

    def test_mask_api_key_one_char(self):
        """Test masking single character"""
        # Arrange
        key = "x"

        # Act
        result = mask_api_key(key, visible_chars=4)

        # Assert
        assert result == "*"

    def test_mask_api_key_anthropic(self):
        """Test masking Anthropic key format"""
        # Arrange
        key = "sk-ant-api03-long-key-here-1234567890"

        # Act
        result = mask_api_key(key)

        # Assert
        assert result == "****...7890"

    def test_mask_api_key_google(self):
        """Test masking Google key format"""
        # Arrange
        key = "AIzaSyTest1234567890abcdefghij"

        # Act
        result = mask_api_key(key)

        # Assert
        assert result == "****...ghij"


class TestValidateApiKeyFormat:
    """Tests for validate_api_key_format()"""

    def test_validate_openai_valid(self):
        """Test valid OpenAI key format"""
        # Arrange
        key = "sk-test1234567890abcdefghij"

        # Act
        result = validate_api_key_format("openai", key)

        # Assert
        assert result is None

    def test_validate_openai_missing_prefix(self):
        """Test OpenAI key without sk- prefix"""
        # Arrange
        key = "test1234567890abcdefghij"

        # Act
        result = validate_api_key_format("openai", key)

        # Assert
        assert result is not None
        assert "sk-" in result

    def test_validate_openai_too_short(self):
        """Test OpenAI key that's too short"""
        # Arrange
        key = "sk-short"

        # Act
        result = validate_api_key_format("openai", key)

        # Assert
        assert result is not None
        assert "too short" in result.lower()

    def test_validate_anthropic_valid(self):
        """Test valid Anthropic key format"""
        # Arrange
        key = "sk-ant-test1234567890abcdefghij"

        # Act
        result = validate_api_key_format("anthropic", key)

        # Assert
        assert result is None

    def test_validate_anthropic_missing_prefix(self):
        """Test Anthropic key without sk-ant- prefix"""
        # Arrange
        key = "sk-test1234567890abcdefghij"

        # Act
        result = validate_api_key_format("anthropic", key)

        # Assert
        assert result is not None
        assert "sk-ant-" in result

    def test_validate_anthropic_too_short(self):
        """Test Anthropic key that's too short"""
        # Arrange
        key = "sk-ant-short"

        # Act
        result = validate_api_key_format("anthropic", key)

        # Assert
        assert result is not None
        assert "too short" in result.lower()

    def test_validate_google_valid(self):
        """Test valid Google key format"""
        # Arrange
        key = "AIzaSyTest1234567890abcdefghij"

        # Act
        result = validate_api_key_format("google", key)

        # Assert
        assert result is None

    def test_validate_google_too_short(self):
        """Test Google key that's too short"""
        # Arrange
        key = "AIza"

        # Act
        result = validate_api_key_format("google", key)

        # Assert
        assert result is not None
        assert "too short" in result.lower()

    def test_validate_empty_key(self):
        """Test validation with empty key"""
        # Act
        result = validate_api_key_format("openai", "")

        # Assert
        assert result is not None
        assert "cannot be empty" in result.lower()

    def test_validate_whitespace_key(self):
        """Test validation with whitespace-only key"""
        # Act
        result = validate_api_key_format("openai", "   ")

        # Assert
        assert result is not None
        assert "cannot be empty" in result.lower()

    def test_validate_none_key(self):
        """Test validation with None key"""
        # Act
        result = validate_api_key_format("openai", None)

        # Assert
        assert result is not None

    def test_validate_unknown_provider(self):
        """Test validation with unknown provider (should pass basic checks)"""
        # Arrange
        key = "some-random-key-1234567890"

        # Act - Unknown provider doesn't have specific validation
        result = validate_api_key_format("unknown_provider", key)

        # Assert
        # Should return None since no specific validation for unknown providers
        assert result is None


class TestGenerateEncryptionKey:
    """Tests for generate_encryption_key()"""

    def test_generate_encryption_key_returns_string(self):
        """Test that generate_encryption_key returns a string"""
        # Act
        key = generate_encryption_key()

        # Assert
        assert isinstance(key, str)
        assert len(key) > 0

    def test_generate_encryption_key_is_valid(self):
        """Test that generated key can be used for encryption"""
        # Arrange
        key = generate_encryption_key()
        test_data = "test-api-key-1234567890"
        
        # Act - Temporarily set environment variable
        original_key = os.environ.get("ENCRYPTION_KEY")
        try:
            os.environ["ENCRYPTION_KEY"] = key
            encrypted = encrypt_api_key(test_data)
            decrypted = decrypt_api_key(encrypted)
        finally:
            # Restore original key
            if original_key:
                os.environ["ENCRYPTION_KEY"] = original_key
            else:
                os.environ.pop("ENCRYPTION_KEY", None)

        # Assert
        assert decrypted == test_data

    def test_generate_encryption_key_unique(self):
        """Test that generated keys are unique"""
        # Act
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        # Assert
        assert key1 != key2

    def test_generate_encryption_key_base64_format(self):
        """Test that generated key is valid base64"""
        # Act
        key = generate_encryption_key()

        # Assert
        # Fernet keys are 44 characters (32 bytes base64 encoded)
        assert len(key) == 44
        # Should be alphanumeric with + / = characters
        assert all(c.isalnum() or c in ['+', '/', '=', '-', '_'] for c in key)
