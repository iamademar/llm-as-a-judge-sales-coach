"""
Database models package.

Exports all ORM models for use in migrations and application code.

Note: Import order matters for table creation. Organization must be imported
before User and Representative since they have foreign keys to organizations.
"""

from app.database import Base
from app.models.organization import Organization  # Must be first (FK target)
from app.models.user import User
from app.models.representative import Representative
from app.models.transcript import Transcript
from app.models.assessment import Assessment
from app.models.llm_credential import LLMCredential, LLMProvider
from app.models.prompt_template import PromptTemplate
from app.models.evaluation_dataset import EvaluationDataset
from app.models.evaluation_run import EvaluationRun

__all__ = [
    "Base",
    "Organization",
    "User",
    "Representative",
    "Transcript",
    "Assessment",
    "LLMCredential",
    "LLMProvider",
    "PromptTemplate",
    "EvaluationDataset",
    "EvaluationRun",
]
