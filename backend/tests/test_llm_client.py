"""
Tests for LLM client with mock and real provider integration.

These tests verify:
- Mock mode functionality (default for testing)
- Provider detection from model names
- LLM instance creation with proper configuration
- Error handling for missing API keys
- Integration with LangChain for OpenAI and Anthropic
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from app.services.llm_client import (
    call_json,
    _detect_provider,
    _create_llm_instance,
    _invoke_llm,
)


class TestMockMode:
    """Test mock LLM mode for testing without API calls."""

    def test_mock_mode_returns_valid_json(self, monkeypatch):
        """Mock mode should return valid SPIN assessment JSON."""
        monkeypatch.setenv("MOCK_LLM", "true")

        result = call_json(
            system="You are a helpful assistant",
            user="Analyze this conversation",
            model="gpt-4o-mini"
        )

        assert "scores" in result
        assert "coaching" in result
        assert "situation" in result
        assert "problem" in result

    def test_mock_mode_case_insensitive(self, monkeypatch):
        """MOCK_LLM should work with True, TRUE, true."""
        for value in ["true", "True", "TRUE"]:
            monkeypatch.setenv("MOCK_LLM", value)
            result = call_json(
                system="Test",
                user="Test",
                model="gpt-4"
            )
            assert "scores" in result

    def test_mock_mode_disabled_by_default(self, monkeypatch):
        """When MOCK_LLM is not set, should attempt real LLM call."""
        monkeypatch.delenv("MOCK_LLM", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Should raise error because no API key is set
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            call_json(
                system="Test",
                user="Test",
                model="gpt-4o-mini"
            )


class TestProviderDetection:
    """Test automatic provider detection from model names."""

    def test_detect_openai_models(self):
        """Should detect OpenAI from gpt- prefix."""
        assert _detect_provider("gpt-4") == "openai"
        assert _detect_provider("gpt-4-turbo") == "openai"
        assert _detect_provider("gpt-4o-mini") == "openai"
        assert _detect_provider("gpt-3.5-turbo") == "openai"
        assert _detect_provider("o1-preview") == "openai"

    def test_detect_anthropic_models(self):
        """Should detect Anthropic from claude- prefix."""
        assert _detect_provider("claude-3-opus") == "anthropic"
        assert _detect_provider("claude-3-sonnet") == "anthropic"
        assert _detect_provider("claude-3-haiku") == "anthropic"
        assert _detect_provider("claude-3.5-sonnet") == "anthropic"

    def test_detect_case_insensitive(self):
        """Provider detection should be case-insensitive."""
        assert _detect_provider("GPT-4") == "openai"
        assert _detect_provider("Claude-3-Opus") == "anthropic"
        assert _detect_provider("GPT-4O-MINI") == "openai"

    def test_detect_google_models(self):
        """Should detect Google from gemini- prefix."""
        assert _detect_provider("gemini-1.5-pro") == "google"
        assert _detect_provider("gemini-1.5-flash") == "google"
        assert _detect_provider("gemini-pro") == "google"

    def test_detect_unknown_model_raises_error(self):
        """Should raise ValueError for unknown model prefixes."""
        with pytest.raises(ValueError, match="Cannot determine provider"):
            _detect_provider("unknown-model-123")

        with pytest.raises(ValueError, match="Cannot determine provider"):
            _detect_provider("cohere-command-r")


class TestLLMInstanceCreation:
    """Test LLM instance creation with proper configuration."""

    @patch("langchain_openai.ChatOpenAI")
    def test_create_openai_instance_with_json_mode(self, mock_chat_openai, monkeypatch):
        """Should create OpenAI instance with JSON mode enabled."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        _create_llm_instance(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.7,
            response_format_json=True
        )

        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["api_key"] == "sk-test-key"
        assert call_kwargs["model_kwargs"]["response_format"]["type"] == "json_object"

    @patch("langchain_openai.ChatOpenAI")
    def test_create_openai_instance_without_json_mode(self, mock_chat_openai, monkeypatch):
        """Should create OpenAI instance without JSON mode when disabled."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        _create_llm_instance(
            provider="openai",
            model="gpt-4",
            temperature=0.0,
            response_format_json=False
        )

        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs.get("model_kwargs") is None

    def test_create_openai_without_api_key_raises_error(self, monkeypatch):
        """Should raise ValueError when OPENAI_API_KEY is missing."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            _create_llm_instance(
                provider="openai",
                model="gpt-4",
                temperature=0.0,
                response_format_json=False
            )

    @patch("langchain_anthropic.ChatAnthropic")
    def test_create_anthropic_instance(self, mock_chat_anthropic, monkeypatch):
        """Should create Anthropic instance with proper configuration."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

        _create_llm_instance(
            provider="anthropic",
            model="claude-3-sonnet",
            temperature=0.5,
            response_format_json=True
        )

        mock_chat_anthropic.assert_called_once()
        call_kwargs = mock_chat_anthropic.call_args[1]
        assert call_kwargs["model"] == "claude-3-sonnet"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["anthropic_api_key"] == "sk-ant-test-key"

    def test_create_anthropic_without_api_key_raises_error(self, monkeypatch):
        """Should raise ValueError when ANTHROPIC_API_KEY is missing."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError, match="Anthropic API key not configured"):
            _create_llm_instance(
                provider="anthropic",
                model="claude-3-opus",
                temperature=0.0,
                response_format_json=False
            )

    def test_create_unsupported_provider_raises_error(self, monkeypatch):
        """Should raise ValueError for unsupported providers."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            _create_llm_instance(
                provider="cohere",
                model="command-r",
                temperature=0.0,
                response_format_json=False
            )


class TestLLMInvocation:
    """Test LLM invocation with prompts."""

    def test_invoke_llm_formats_messages_correctly(self):
        """Should format system and user messages correctly."""
        from langchain_core.messages import SystemMessage, HumanMessage

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"result": "success"}'
        mock_llm.invoke.return_value = mock_response

        result = _invoke_llm(
            mock_llm,
            system="You are helpful",
            user="Say hello"
        )

        # Verify LLM was invoked with correct message types
        mock_llm.invoke.assert_called_once()
        messages = mock_llm.invoke.call_args[0][0]
        assert len(messages) == 2
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)
        assert messages[0].content == "You are helpful"
        assert messages[1].content == "Say hello"

        # Verify response content is returned
        assert result == '{"result": "success"}'


class TestEndToEndIntegration:
    """Test end-to-end integration with mocked LangChain."""

    @patch("langchain_openai.ChatOpenAI")
    def test_full_openai_flow(self, mock_chat_openai, monkeypatch):
        """Test complete flow from call_json to OpenAI response."""
        monkeypatch.setenv("MOCK_LLM", "false")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"scores": {"situation": 4}, "coaching": {"summary": "Good"}}'
        mock_llm_instance.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm_instance

        result = call_json(
            system="Analyze conversations",
            user="Rate this call",
            model="gpt-4o-mini",
            temperature=0.3,
            response_format_json=True
        )

        # Verify OpenAI was initialized correctly
        mock_chat_openai.assert_called_once()
        init_kwargs = mock_chat_openai.call_args[1]
        assert init_kwargs["model"] == "gpt-4o-mini"
        assert init_kwargs["temperature"] == 0.3

        # Verify result
        assert "scores" in result
        assert "coaching" in result

    @patch("langchain_anthropic.ChatAnthropic")
    def test_full_anthropic_flow(self, mock_chat_anthropic, monkeypatch):
        """Test complete flow from call_json to Anthropic response."""
        monkeypatch.setenv("MOCK_LLM", "false")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"scores": {"problem": 5}, "coaching": {"summary": "Excellent"}}'
        mock_llm_instance.invoke.return_value = mock_response
        mock_chat_anthropic.return_value = mock_llm_instance

        result = call_json(
            system="You are a sales coach",
            user="Evaluate this pitch",
            model="claude-3-sonnet",
            temperature=0.0
        )

        # Verify Anthropic was initialized correctly
        mock_chat_anthropic.assert_called_once()
        init_kwargs = mock_chat_anthropic.call_args[1]
        assert init_kwargs["model"] == "claude-3-sonnet"
        assert init_kwargs["temperature"] == 0.0

        # Verify result
        assert "scores" in result
        assert "coaching" in result
