"""
Request models for API endpoints.

This module contains all request schemas used across different features.
"""

from typing import Dict
from pydantic import BaseModel, Field


class AssessRequest(BaseModel):
    """
    Request model for assessment endpoint.

    Requires a conversation transcript and supports optional metadata
    for tracking context (e.g., rep_id, call_date, customer_name).
    """
    transcript: str = Field(..., min_length=1, description="Conversation transcript to assess")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Optional metadata")
