"""
Assessment scoring schemas.

This module contains scoring models for sales conversation assessment
using the SPIN framework (Situation, Problem, Implication, Need-Payoff).
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class AssessmentScores(BaseModel):
    """
    SPIN scoring model with additional conversation quality metrics.

    All scores must be integers in the range [1, 5] where:
    - 1 = Poor
    - 2 = Below Average
    - 3 = Average
    - 4 = Good
    - 5 = Excellent
    """
    situation: int = Field(..., ge=1, le=5, description="Quality of situation questions")
    problem: int = Field(..., ge=1, le=5, description="Quality of problem questions")
    implication: int = Field(..., ge=1, le=5, description="Quality of implication questions")
    need_payoff: int = Field(..., ge=1, le=5, description="Quality of need-payoff questions")
    flow: int = Field(..., ge=1, le=5, description="Overall conversation flow")
    tone: int = Field(..., ge=1, le=5, description="Tone and professionalism")
    engagement: int = Field(..., ge=1, le=5, description="Customer engagement level")

    @field_validator(
        "situation", "problem", "implication", "need_payoff",
        "flow", "tone", "engagement",
        mode="before"
    )
    @classmethod
    def validate_score_range(cls, v, info):
        """Ensure all scores are integers in valid range [1, 5]"""
        if not isinstance(v, int):
            raise ValueError(f"{info.field_name} must be an integer, got {type(v).__name__}")
        if v < 1 or v > 5:
            raise ValueError(f"{info.field_name} must be between 1 and 5, got {v}")
        return v


class AssessmentInDB(BaseModel):
    """
    Schema for assessment data from database.
    
    Includes all fields including IDs and timestamps.
    Used for API responses containing assessment data.
    """
    id: int = Field(..., description="Unique assessment identifier")
    transcript_id: int = Field(..., description="Reference to parent transcript")
    scores: Dict[str, Any] = Field(..., description="SPIN scores")
    coaching: Dict[str, Any] = Field(..., description="Coaching feedback")
    model_name: str = Field(..., description="LLM model identifier")
    prompt_version: str = Field(..., description="Prompt template version")
    latency_ms: Optional[int] = Field(None, description="LLM call latency in milliseconds")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)
