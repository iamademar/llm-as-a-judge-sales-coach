"""
EvaluationRun model for storing prompt evaluation results.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Float, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import UUID


class EvaluationRun(Base):
    """
    Evaluation run results for a specific prompt template.
    
    Stores metrics (Pearson r, QWK, ±1 accuracy) for each dimension
    when evaluating a prompt template against a golden dataset.
    """
    __tablename__ = "evaluation_runs"

    id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique run identifier",
    )
    prompt_template_id = Column(
        UUID(),
        ForeignKey("prompt_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Prompt template that was evaluated",
    )
    dataset_id = Column(
        UUID(),
        ForeignKey("evaluation_datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Dataset used for this evaluation",
    )
    experiment_name = Column(
        String(100),
        nullable=True,
        comment="Optional experiment name for tracking iterations",
    )
    num_examples = Column(
        Integer,
        nullable=False,
        comment="Number of examples evaluated",
    )
    
    # Macro averages (overall performance)
    macro_pearson_r = Column(
        Float,
        nullable=True,
        comment="Macro-averaged Pearson correlation across all dimensions",
    )
    macro_qwk = Column(
        Float,
        nullable=True,
        comment="Macro-averaged Quadratic Weighted Kappa",
    )
    macro_plus_minus_one = Column(
        Float,
        nullable=True,
        comment="Macro-averaged ±1 accuracy",
    )
    
    # Per-dimension metrics (stored as JSON for flexibility)
    per_dimension_metrics = Column(
        JSON,
        nullable=False,
        comment="Metrics for each dimension: {dimension: {pearson_r, qwk, pm1}}",
    )
    
    # Metadata
    model_name = Column(
        String(50),
        nullable=True,
        comment="LLM model used (e.g., 'gpt-4o-mini')",
    )
    runtime_seconds = Column(
        Float,
        nullable=True,
        comment="Total evaluation runtime in seconds",
    )
    langsmith_url = Column(
        String(500),
        nullable=True,
        comment="URL to view this evaluation in LangSmith",
    )
    langsmith_experiment_id = Column(
        String(100),
        nullable=True,
        comment="LangSmith experiment/session ID",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Evaluation run timestamp",
    )

    # Relationships
    prompt_template = relationship("PromptTemplate", back_populates="evaluation_runs")
    dataset = relationship("EvaluationDataset", back_populates="evaluation_runs")

    def __repr__(self):
        return (
            f"<EvaluationRun(id={self.id}, "
            f"template={self.prompt_template_id}, "
            f"qwk={self.macro_qwk:.3f if self.macro_qwk else 'N/A'})>"
        )

