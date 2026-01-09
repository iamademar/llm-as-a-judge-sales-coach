"""
Representative schemas for request/response validation.

Pydantic models for representative data validation and serialization.
"""
import uuid
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RepresentativeBase(BaseModel):
    """
    Base schema with common representative fields.
    """
    email: EmailStr = Field(..., description="Representative's email address")
    full_name: str = Field(..., description="Representative's full name")
    department: Optional[str] = Field(None, description="Department or team")
    is_active: bool = Field(True, description="Whether representative is active")


class RepresentativeCreate(BaseModel):
    """
    Schema for creating a new representative.

    Used for representative registration/creation requests.
    """
    email: EmailStr = Field(..., description="Representative's email address")
    full_name: str = Field(..., description="Representative's full name")
    department: Optional[str] = Field(None, description="Department or team")
    hire_date: Optional[datetime] = Field(None, description="Date when rep joined")


class RepresentativeUpdate(BaseModel):
    """
    Schema for updating an existing representative.

    All fields are optional to support partial updates.
    """
    email: Optional[EmailStr] = Field(None, description="Representative's email address")
    full_name: Optional[str] = Field(None, description="Representative's full name")
    department: Optional[str] = Field(None, description="Department or team")
    is_active: Optional[bool] = Field(None, description="Whether representative is active")
    hire_date: Optional[datetime] = Field(None, description="Date when rep joined")


class RepresentativeInDB(RepresentativeBase):
    """
    Schema for representative data from database.

    Includes all fields including IDs and timestamps.
    Used for API responses containing representative data.
    """
    id: uuid.UUID = Field(..., description="Unique representative identifier")
    hire_date: Optional[datetime] = Field(None, description="Date when rep joined")
    created_at: datetime = Field(..., description="Record creation timestamp")
    organization_id: Optional[uuid.UUID] = Field(
        None, description="Organization this representative belongs to"
    )

    model_config = ConfigDict(from_attributes=True)

