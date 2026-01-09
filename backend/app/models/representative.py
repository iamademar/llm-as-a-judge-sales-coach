"""
Representative model for sales reps being coached.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import UUID


class Representative(Base):
    """
    Sales representative model.
    
    Stores information about sales reps whose conversations are being assessed.
    Representatives do not have login access - they are subjects of assessment only.
    """
    __tablename__ = "representatives"

    id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique representative identifier"
    )
    
    # Rep information
    full_name = Column(
        String,
        nullable=False,
        index=True,
        comment="Representative's full name"
    )
    email = Column(
        String,
        nullable=False,
        unique=True,
        index=True,
        comment="Representative's email address"
    )
    
    # Optional organizational info
    department = Column(
        String,
        nullable=True,
        comment="Department or team (e.g., 'Enterprise Sales', 'SMB')"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether representative is currently active"
    )
    
    # Timestamps
    hire_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date when rep joined"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )

    # Organization relationship
    organization_id = Column(
        UUID(),
        ForeignKey("organizations.id"),
        nullable=True,  # Nullable initially for migration; required in app logic
        index=True,
        comment="Organization this representative belongs to",
    )
    organization = relationship("Organization", back_populates="representatives")
    
    # Relationships
    transcripts = relationship("Transcript", back_populates="representative", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Representative(id={self.id}, name={self.full_name!r}, email={self.email!r}, is_active={self.is_active})>"

