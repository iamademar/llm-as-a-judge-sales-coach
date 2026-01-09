"""
Response models for API endpoints.

This module contains all response schemas used across different features.
"""

from pydantic import BaseModel, Field

from app.schemas.assessment import AssessmentScores
from app.schemas.coaching import Coaching


class AssessResponse(BaseModel):
    """
    Response model for assessment endpoint.

    Returns a unique assessment ID along with scores and coaching feedback.
    """
    assessment_id: int = Field(..., ge=1, description="Unique assessment identifier")
    scores: AssessmentScores = Field(..., description="SPIN and quality scores")
    coaching: Coaching = Field(..., description="Coaching feedback and recommendations")
