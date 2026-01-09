"""
Organization schemas for request/response validation.

Pydantic models for organization data validation and serialization.
"""
import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class OrganizationBase(BaseModel):
    """
    Base organization schema with common fields.

    Used as a base for create and output schemas.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Organization name"
    )
    description: Optional[str] = Field(
        None,
        description="Organization description"
    )


class OrganizationCreate(OrganizationBase):
    """
    Schema for creating an organization.

    Inherits name and description from OrganizationBase.
    """

    pass


class OrganizationOut(OrganizationBase):
    """
    Schema for organization output (API responses).

    Includes all fields that should be exposed to clients.
    """

    id: uuid.UUID = Field(..., description="Organization ID")
    is_active: bool = Field(..., description="Whether organization is active")

    model_config = ConfigDict(from_attributes=True)
