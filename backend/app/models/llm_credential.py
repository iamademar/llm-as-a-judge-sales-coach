"""
LLM Credential model for storing encrypted API keys per organization.
"""
import uuid
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import UUID


class LLMProvider(enum.Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMCredential(Base):
    """
    LLM Credential model for storing encrypted API keys.

    Each organization can have one credential per LLM provider.
    API keys are stored encrypted using Fernet symmetric encryption.
    """

    __tablename__ = "llm_credentials"

    id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique credential identifier",
    )
    organization_id = Column(
        UUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this credential belongs to",
    )
    provider = Column(
        Enum(
            LLMProvider,
            name="llmprovider",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
        comment="LLM provider (openai, anthropic, google)",
    )
    encrypted_api_key = Column(
        Text,
        nullable=False,
        comment="Fernet-encrypted API key",
    )
    default_model = Column(
        String,
        nullable=True,
        comment="Default model name for this provider",
    )
    is_active = Column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        comment="Whether this credential is active",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Credential creation timestamp",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Credential last update timestamp",
    )

    # Relationships
    organization = relationship("Organization", back_populates="llm_credentials")

    def __repr__(self):
        return (
            f"<LLMCredential(id={self.id}, "
            f"organization_id={self.organization_id}, "
            f"provider={self.provider.value}, "
            f"is_active={self.is_active})>"
        )
