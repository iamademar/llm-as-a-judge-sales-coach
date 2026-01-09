"""
Common/shared schemas used across the application.

This module contains reusable models like error responses, metadata,
and other cross-cutting concerns.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Standard error response model.

    Used for consistent error messaging across all API endpoints.
    """
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, str]] = Field(default=None, description="Additional error details")


class Metadata(BaseModel):
    """
    Common metadata model for requests.

    Used to track context like rep_id, call_date, customer_name, etc.
    """
    data: Dict[str, str] = Field(default_factory=dict, description="Key-value metadata pairs")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get metadata value by key with optional default"""
        return self.data.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Set metadata value by key"""
        self.data[key] = value
