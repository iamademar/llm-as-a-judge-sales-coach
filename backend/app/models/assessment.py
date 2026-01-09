"""
Assessment model for storing SPIN framework evaluations.
"""

from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Assessment(Base):
    """
    SPIN framework assessment model.

    Stores LLM-generated scores and coaching feedback for a transcript.
    Tracks model name and prompt version for reproducibility and evaluation.
    """
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transcript_id = Column(
        Integer,
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent transcript"
    )
    scores = Column(
        JSON,
        nullable=False,
        comment="SPIN scores: {situation, problem, implication, need_payoff, flow, tone, engagement}"
    )
    coaching = Column(
        JSON,
        nullable=False,
        comment="Coaching feedback: {summary, wins, gaps, next_actions}"
    )
    model_name = Column(
        String,
        nullable=False,
        index=True,
        comment="LLM model identifier (e.g., 'gpt-4o-mini', 'claude-3-sonnet')"
    )
    prompt_version = Column(
        String,
        nullable=False,
        index=True,
        comment="Prompt template version (e.g., 'spin_v1', 'spin_v2')"
    )
    latency_ms = Column(
        Integer,
        nullable=True,
        comment="LLM call latency in milliseconds"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when assessment was created"
    )

    # Relationship to transcript
    transcript_ref = relationship("Transcript", back_populates="assessments")

    def __repr__(self):
        return (
            f"<Assessment(id={self.id}, transcript_id={self.transcript_id}, "
            f"model={self.model_name!r}, prompt_version={self.prompt_version!r})>"
        )
