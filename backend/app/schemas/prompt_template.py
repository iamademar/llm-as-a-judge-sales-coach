"""
PromptTemplate schemas for request/response validation.

Pydantic models for prompt template data validation and serialization.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class PromptTemplateCreate(BaseModel):
    """Schema for creating a new prompt template."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Template name"
    )
    version: str = Field(
        default="v1", max_length=20, description="Version identifier"
    )
    system_prompt: str = Field(
        ..., min_length=10, description="System prompt defining LLM behavior"
    )
    user_template: str = Field(
        ...,
        min_length=10,
        description="User prompt template with {transcript} placeholder",
    )
    is_active: bool = Field(
        default=False, description="Set as active template for the organization"
    )

    @field_validator("user_template")
    @classmethod
    def validate_transcript_placeholder(cls, v: str) -> str:
        """Ensure user_template contains the {transcript} placeholder."""
        if "{transcript}" not in v:
            raise ValueError("user_template must contain {transcript} placeholder")
        return v


class PromptTemplateUpdate(BaseModel):
    """
    Schema for updating a prompt template.

    All fields are optional to support partial updates.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    version: Optional[str] = Field(None, max_length=20)
    system_prompt: Optional[str] = Field(None, min_length=10)
    user_template: Optional[str] = Field(None, min_length=10)
    is_active: Optional[bool] = None

    @field_validator("user_template")
    @classmethod
    def validate_transcript_placeholder(cls, v: Optional[str]) -> Optional[str]:
        """Ensure user_template contains the {transcript} placeholder if provided."""
        if v is not None and "{transcript}" not in v:
            raise ValueError("user_template must contain {transcript} placeholder")
        return v


class PromptTemplateResponse(BaseModel):
    """Schema for prompt template API responses."""

    id: uuid.UUID = Field(..., description="Template identifier")
    organization_id: uuid.UUID = Field(..., description="Organization identifier")
    name: str = Field(..., description="Template name")
    version: str = Field(..., description="Version identifier")
    system_prompt: str = Field(..., description="System prompt")
    user_template: str = Field(..., description="User prompt template")
    is_active: bool = Field(..., description="Whether this is the active template")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class PromptTemplatePreview(BaseModel):
    """Preview of a rendered prompt (for testing templates)."""

    system_prompt: str = Field(..., description="Rendered system prompt")
    user_prompt: str = Field(..., description="Rendered user prompt with transcript")
    transcript_sample: str = Field(
        ..., description="Sample transcript used for preview"
    )

