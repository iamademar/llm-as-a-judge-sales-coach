import os
import pytest


def test_app_env_exists():
    """Smoke test: verify APP_ENV environment variable is set"""
    app_env = os.getenv("APP_ENV")
    assert app_env is not None, "APP_ENV environment variable should be set"
    assert app_env == "dev", f"Expected APP_ENV to be 'dev', got '{app_env}'"


def test_mock_llm_flag_exists():
    """Smoke test: verify MOCK_LLM environment variable is set"""
    mock_llm = os.getenv("MOCK_LLM")
    assert mock_llm is not None, "MOCK_LLM environment variable should be set"
    assert mock_llm == "true", f"Expected MOCK_LLM to be 'true', got '{mock_llm}'"


def test_database_env_vars_exist():
    """Smoke test: verify database environment variables are set"""
    assert os.getenv("DB_HOST") is not None
    assert os.getenv("DB_USER") is not None
    assert os.getenv("DB_PASS") is not None
    assert os.getenv("DB_NAME") is not None
