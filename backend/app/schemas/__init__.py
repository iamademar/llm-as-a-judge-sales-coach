"""
Pydantic schemas for request/response validation and serialization.

Organized by concern:
- assessment: Scoring models for SPIN framework
- coaching: Coaching feedback and recommendations
- request: API request models
- response: API response models
- common: Shared/reusable models
"""

# Assessment schemas
from app.schemas.assessment import AssessmentScores, AssessmentInDB

# Coaching schemas
from app.schemas.coaching import Coaching

# Request schemas
from app.schemas.request import AssessRequest

# Response schemas
from app.schemas.response import AssessResponse

# Common schemas
from app.schemas.common import ErrorResponse, Metadata

# Representative schemas
from app.schemas.representative import (
    RepresentativeBase,
    RepresentativeCreate,
    RepresentativeUpdate,
    RepresentativeInDB,
)

# Transcript schemas
from app.schemas.transcript import (
    TranscriptBase,
    TranscriptCreate,
    TranscriptInDB,
)

# LLM Credential schemas
from app.schemas.llm_credential import (
    LLMProviderEnum,
    LLMCredentialCreate,
    LLMCredentialUpdate,
    LLMCredentialResponse,
    LLMCredentialListResponse,
    ProviderInfo,
    ProviderListResponse,
    PROVIDER_INFO,
)

# Prompt Template schemas
from app.schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplatePreview,
)

# Evaluation schemas
from app.schemas.evaluation import (
    EvaluationDatasetCreate,
    EvaluationDatasetUpdate,
    EvaluationDatasetResponse,
    EvaluationRunResponse,
    RunEvaluationRequest,
    EvaluationMetricsSummary,
    EvaluationRunListResponse,
)

# Overview schemas
from app.schemas.overview import (
    OverviewStatisticsResponse,
    DimensionStats,
)

__all__ = [
    # Assessment
    "AssessmentScores",
    "AssessmentInDB",
    # Coaching
    "Coaching",
    # Request
    "AssessRequest",
    # Response
    "AssessResponse",
    # Common
    "ErrorResponse",
    "Metadata",
    # Representative
    "RepresentativeBase",
    "RepresentativeCreate",
    "RepresentativeUpdate",
    "RepresentativeInDB",
    # Transcript
    "TranscriptBase",
    "TranscriptCreate",
    "TranscriptInDB",
    # LLM Credentials
    "LLMProviderEnum",
    "LLMCredentialCreate",
    "LLMCredentialUpdate",
    "LLMCredentialResponse",
    "LLMCredentialListResponse",
    "ProviderInfo",
    "ProviderListResponse",
    "PROVIDER_INFO",
    # Prompt Templates
    "PromptTemplateCreate",
    "PromptTemplateUpdate",
    "PromptTemplateResponse",
    "PromptTemplatePreview",
    # Evaluation
    "EvaluationDatasetCreate",
    "EvaluationDatasetUpdate",
    "EvaluationDatasetResponse",
    "EvaluationRunResponse",
    "RunEvaluationRequest",
    "EvaluationMetricsSummary",
    "EvaluationRunListResponse",
    # Overview
    "OverviewStatisticsResponse",
    "DimensionStats",
]
