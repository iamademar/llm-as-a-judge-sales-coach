"""
Organization model for multi-tenant support.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import UUID


class Organization(Base):
    """
    Organization model for multi-tenant support.

    Stores organization information. Users and representatives belong to exactly
    one organization.
    """

    __tablename__ = "organizations"

    id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique organization identifier",
    )
    name = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
        comment="Organization name (unique)",
    )
    description = Column(
        String,
        nullable=True,
        comment="Organization description",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether organization is active",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Organization creation timestamp",
    )

    # Relationships
    users = relationship("User", back_populates="organization")
    representatives = relationship("Representative", back_populates="organization")
    llm_credentials = relationship("LLMCredential", back_populates="organization")
    prompt_templates = relationship("PromptTemplate", back_populates="organization")
    evaluation_datasets = relationship("EvaluationDataset", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name!r}, is_active={self.is_active})>"

