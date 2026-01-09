"""
Transcript schemas for request/response validation.

Pydantic models for transcript data validation and serialization.
"""
from typing import Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_serializer, ConfigDict, model_serializer


class TranscriptBase(BaseModel):
    """
    Base schema with common transcript fields.
    """
    representative_id: Optional[str] = Field(None, description="Representative UUID (as string)")
    buyer_id: Optional[str] = Field(None, description="Buyer/customer identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional call metadata (call_date, industry, etc.)")
    transcript: str = Field(..., description="Full conversation text with speaker tags")


class TranscriptCreate(BaseModel):
    """
    Schema for creating a new transcript.
    
    Used for transcript creation requests.
    """
    representative_id: Optional[str] = Field(None, description="Representative UUID (as string)")
    buyer_id: Optional[str] = Field(None, description="Buyer/customer identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional call metadata")
    transcript: str = Field(..., description="Full conversation text with speaker tags")


class TranscriptInDB(BaseModel):
    """
    Schema for transcript data from database.
    
    Includes all fields including IDs and timestamps.
    Used for API responses containing transcript data.
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: int = Field(..., description="Unique transcript identifier")
    representative_id: Optional[Union[str, UUID]] = Field(None, description="Representative UUID (as string)")
    buyer_id: Optional[str] = Field(None, description="Buyer/customer identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional call metadata", validation_alias="call_metadata")
    transcript: str = Field(..., description="Full conversation text with speaker tags")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    @field_serializer('representative_id', when_used='always')
    def serialize_representative_id(self, value: Optional[Union[str, UUID]]) -> Optional[str]:
        """Convert UUID to string"""
        if value is None:
            return None
        return str(value)

