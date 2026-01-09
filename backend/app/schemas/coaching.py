"""
Coaching-specific schemas.

This module contains models for coaching feedback, recommendations,
and actionable insights for sales representatives.
"""

from typing import List
from pydantic import BaseModel, Field


class Coaching(BaseModel):
    """
    Coaching feedback model with summary and actionable insights.

    Provides structured feedback including wins (strengths),
    gaps (areas for improvement), and next actions (concrete steps).
    """
    summary: str = Field(..., min_length=1, description="High-level coaching summary")
    wins: List[str] = Field(default_factory=list, description="Things done well")
    gaps: List[str] = Field(default_factory=list, description="Areas for improvement")
    next_actions: List[str] = Field(default_factory=list, description="Specific action items")
