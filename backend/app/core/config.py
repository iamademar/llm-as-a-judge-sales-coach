"""
Application configuration from environment variables.
"""
import os
from typing import Optional


class Settings:
    """
    Application settings loaded from environment variables.

    Required:
        - API_KEY: API key for securing endpoints

    Optional:
        - MODEL_NAME: LLM model name (default: gpt-4)
        - MOCK_LLM: Whether to use mock LLM responses (default: false)
        - FEATURE_SIM: Enable similarity search with embeddings (default: false)
        - DATABASE_URL: Database connection string
        - LOG_LEVEL: Logging level (default: INFO)
    """

    def __init__(self):
        # Required settings
        self.API_KEY: str = self._get_required("API_KEY")

        # Optional settings
        self.MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4")
        self.MOCK_LLM: bool = os.getenv("MOCK_LLM", "false").lower() == "true"
        self.FEATURE_SIM: bool = os.getenv("FEATURE_SIM", "false").lower() == "true"
        self.DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.APP_ENV: str = os.getenv("APP_ENV", "development")

        # Frontend URL for CORS (optional, defaults to localhost)
        self.FRONTEND_URL: Optional[str] = os.getenv("FRONTEND_URL")

        # JWT settings
        self.JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        # Encryption settings (for LLM credential storage)
        # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        self.ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")

        # LangSmith settings (optional)
        self.LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY")
        self.LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "spin-scoring")

    def _get_required(self, key: str) -> str:
        """Get required environment variable or raise error."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value


# Global settings instance
settings = Settings()
