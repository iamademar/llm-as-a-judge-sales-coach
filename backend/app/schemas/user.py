"""
User schemas for request/response validation.

Pydantic models for user data validation and serialization.
"""
import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator, ValidationError, ConfigDict
from pydantic_core import PydanticCustomError


class UserCreate(BaseModel):
    """
    Schema for creating a new user.

    Used for user registration requests.
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ..., min_length=8, description="User password (min 8 characters)"
    )
    full_name: Optional[str] = Field(None, description="User's full name")

    # Organization assignment (exactly one must be provided)
    organization_id: Optional[uuid.UUID] = Field(
        None,
        description="Join existing organization by ID"
    )
    organization_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Create new organization with this name"
    )

    @model_validator(mode='after')
    def validate_organization(self):
        """Ensure exactly one organization option is provided."""
        has_id = self.organization_id is not None
        has_name = self.organization_name is not None

        if not has_id and not has_name:
            raise PydanticCustomError(
                "value_error",
                "Must provide either organization_id or organization_name"
            )

        if has_id and has_name:
            raise PydanticCustomError(
                "value_error",
                "Cannot provide both organization_id and organization_name"
            )

        return self


class UserOut(BaseModel):
    """
    Schema for user output (excludes sensitive fields).

    Used for API responses containing user data.
    """

    id: uuid.UUID = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(..., description="Whether user account is active")
    is_superuser: bool = Field(
        ..., description="Whether user has superuser privileges"
    )
    organization_id: Optional[uuid.UUID] = Field(
        None, description="Organization this user belongs to"
    )

    model_config = ConfigDict(from_attributes=True)
