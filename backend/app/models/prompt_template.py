"""
PromptTemplate model for organization-specific SPIN assessment prompts.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import UUID


class PromptTemplate(Base):
    """
    Prompt template for SPIN assessments.

    Each organization has at least one template (v0 default created automatically).
    Only one template per organization can be active at a time.
    """

    __tablename__ = "prompt_templates"

    id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique template identifier",
    )
    organization_id = Column(
        UUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this template belongs to",
    )
    name = Column(
        String(100),
        nullable=False,
        comment="Human-readable template name",
    )
    version = Column(
        String(20),
        nullable=False,
        default="v0",
        comment="Version identifier (e.g., 'v0', 'v1', 'custom_v2')",
    )
    system_prompt = Column(
        Text,
        nullable=False,
        comment="System prompt defining LLM behavior",
    )
    user_template = Column(
        Text,
        nullable=False,
        comment="User prompt template (must contain {transcript} placeholder)",
    )
    is_active = Column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="Only one template per org can be active",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Template creation timestamp",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Template last update timestamp",
    )

    # Relationships
    organization = relationship("Organization", back_populates="prompt_templates")
    evaluation_runs = relationship(
        "EvaluationRun",
        back_populates="prompt_template",
        cascade="all, delete-orphan",
        order_by="desc(EvaluationRun.created_at)",
    )

    @property
    def latest_evaluation(self):
        """Get the most recent evaluation run for this template."""
        return self.evaluation_runs[0] if self.evaluation_runs else None
    
    @property
    def best_qwk_score(self):
        """Get the best QWK score across all evaluations."""
        if not self.evaluation_runs:
            return None
        valid_runs = [run.macro_qwk for run in self.evaluation_runs if run.macro_qwk is not None]
        return max(valid_runs) if valid_runs else None

    def __repr__(self):
        return (
            f"<PromptTemplate(id={self.id}, "
            f"org={self.organization_id}, "
            f"name={self.name!r}, "
            f"version={self.version}, "
            f"is_active={self.is_active})>"
        )

