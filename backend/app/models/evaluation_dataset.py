"""
EvaluationDataset model for tracking golden sets used to evaluate prompts.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import UUID


class EvaluationDataset(Base):
    """
    Golden evaluation dataset for prompt calibration.
    
    Tracks CSV files or LangSmith datasets used to evaluate prompts.
    Each dataset represents a collection of transcripts with human-labeled scores.
    """
    __tablename__ = "evaluation_datasets"

    id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique dataset identifier",
    )
    organization_id = Column(
        UUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this dataset belongs to",
    )
    name = Column(
        String(100),
        nullable=False,
        comment="Dataset name (e.g., 'sales-eval-v1', 'Q4-2024-golden-set')",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Description of dataset contents and purpose",
    )
    source_type = Column(
        String(20),
        nullable=False,
        default="csv",
        comment="Source type: 'csv', 'langsmith', or 'database'",
    )
    source_path = Column(
        String(500),
        nullable=True,
        comment="CSV file path or LangSmith dataset ID",
    )
    num_examples = Column(
        Integer,
        nullable=False,
        comment="Number of examples in the dataset",
    )
    langsmith_dataset_name = Column(
        String(200),
        nullable=True,
        comment="Slugified name used in LangSmith",
    )
    langsmith_dataset_id = Column(
        String(100),
        nullable=True,
        comment="LangSmith dataset ID after upload",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Dataset creation timestamp",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Dataset last update timestamp",
    )

    # Relationships
    organization = relationship("Organization", back_populates="evaluation_datasets")
    evaluation_runs = relationship(
        "EvaluationRun",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<EvaluationDataset(id={self.id}, "
            f"name={self.name!r}, "
            f"examples={self.num_examples})>"
        )

