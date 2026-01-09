"""
LLM Credential schemas for request/response validation.

Pydantic models for LLM credential data validation and serialization.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class LLMProviderEnum(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class ProviderInfo(BaseModel):
    """Information about a supported LLM provider."""
    id: str = Field(..., description="Provider identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Provider description")
    default_model: str = Field(..., description="Default model for this provider")
    key_prefix: str = Field(..., description="Expected API key prefix")
    docs_url: str = Field(..., description="Link to API documentation")


# Static provider information
PROVIDER_INFO: List[ProviderInfo] = [
    ProviderInfo(
        id="openai",
        name="OpenAI",
        description="GPT-4, GPT-3.5, and other OpenAI models",
        default_model="gpt-4o-mini",
        key_prefix="sk-",
        docs_url="https://platform.openai.com/api-keys",
    ),
    ProviderInfo(
        id="anthropic",
        name="Anthropic",
        description="Claude 3 Opus, Sonnet, and Haiku models",
        default_model="claude-3-5-sonnet-20241022",
        key_prefix="sk-ant-",
        docs_url="https://console.anthropic.com/settings/keys",
    ),
    ProviderInfo(
        id="google",
        name="Google AI",
        description="Gemini Pro and other Google AI models",
        default_model="gemini-1.5-flash",
        key_prefix="AI",
        docs_url="https://aistudio.google.com/apikey",
    ),
]


class LLMCredentialCreate(BaseModel):
    """
    Schema for creating a new LLM credential.
    """
    provider: LLMProviderEnum = Field(..., description="LLM provider")
    api_key: str = Field(..., min_length=10, description="API key for the provider")
    default_model: Optional[str] = Field(None, description="Default model name")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Strip whitespace from API key."""
        return v.strip()


class LLMCredentialUpdate(BaseModel):
    """
    Schema for updating an existing LLM credential.

    All fields are optional to support partial updates.
    """
    api_key: Optional[str] = Field(None, min_length=10, description="New API key")
    default_model: Optional[str] = Field(None, description="New default model name")
    is_active: Optional[bool] = Field(None, description="Whether credential is active")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace from API key if provided."""
        return v.strip() if v else v


class LLMCredentialResponse(BaseModel):
    """
    Schema for LLM credential API responses.

    API keys are masked for security - only last 4 characters shown.
    """
    id: uuid.UUID = Field(..., description="Credential identifier")
    organization_id: uuid.UUID = Field(..., description="Organization identifier")
    provider: LLMProviderEnum = Field(..., description="LLM provider")
    masked_key: str = Field(..., description="Masked API key (e.g., ****...xxxx)")
    default_model: Optional[str] = Field(None, description="Default model name")
    is_active: bool = Field(..., description="Whether credential is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class LLMCredentialListResponse(BaseModel):
    """
    Schema for listing all credentials for an organization.
    """
    credentials: List[LLMCredentialResponse] = Field(
        default_factory=list, description="List of LLM credentials"
    )
    providers: List[ProviderInfo] = Field(
        default_factory=lambda: PROVIDER_INFO,
        description="Available provider information",
    )


class ProviderListResponse(BaseModel):
    """
    Schema for listing available providers.
    """
    providers: List[ProviderInfo] = Field(
        default_factory=lambda: PROVIDER_INFO,
        description="Available provider information",
    )

