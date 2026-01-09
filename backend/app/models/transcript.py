"""
Transcript model for storing sales conversations.
"""

from sqlalchemy import Column, BigInteger, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Float

from app.database import Base
from app.models.user import UUID


class Transcript(Base):
    """
    Sales conversation transcript model.

    Stores the raw conversation text along with metadata about participants.
    One transcript can have multiple assessments (e.g., different models/prompts).
    """
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    representative_id = Column(
        UUID(),
        ForeignKey("representatives.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to representative"
    )
    buyer_id = Column(String, nullable=True, index=True, comment="Buyer/customer identifier")
    call_metadata = Column("metadata", JSON, nullable=True, comment="Additional context (call_date, industry, etc.)")
    transcript = Column(Text, nullable=False, comment="Full conversation text with speaker tags")
    embedding = Column(
        Text,  # Use Text for SQLite compatibility; migration handles PostgreSQL ARRAY
        nullable=True,
        comment="Embedding vector for similarity search (JSON-encoded array)"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when transcript was created"
    )

    # Relationships
    representative = relationship("Representative", back_populates="transcripts")
    assessments = relationship("Assessment", back_populates="transcript_ref", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Transcript(id={self.id}, representative_id={self.representative_id!r}, buyer_id={self.buyer_id!r}, created_at={self.created_at})>"
