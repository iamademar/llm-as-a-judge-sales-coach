"""
CRUD operations for EvaluationRun model.

Provides functions for managing evaluation runs and results.
"""
import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.evaluation_run import EvaluationRun


def get_by_id(db: Session, run_id: uuid.UUID) -> Optional[EvaluationRun]:
    """
    Get an evaluation run by ID.

    Args:
        db: Database session
        run_id: Run UUID

    Returns:
        EvaluationRun object if found, None otherwise
    """
    return db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()


def get_by_template(db: Session, template_id: uuid.UUID) -> List[EvaluationRun]:
    """
    Get all evaluation runs for a prompt template.

    Args:
        db: Database session
        template_id: PromptTemplate UUID

    Returns:
        List of EvaluationRun objects, ordered by created_at desc
    """
    return (
        db.query(EvaluationRun)
        .filter(EvaluationRun.prompt_template_id == template_id)
        .order_by(EvaluationRun.created_at.desc())
        .all()
    )


def get_by_dataset(db: Session, dataset_id: uuid.UUID) -> List[EvaluationRun]:
    """
    Get all evaluation runs using a specific dataset.

    Args:
        db: Database session
        dataset_id: EvaluationDataset UUID

    Returns:
        List of EvaluationRun objects, ordered by created_at desc
    """
    return (
        db.query(EvaluationRun)
        .filter(EvaluationRun.dataset_id == dataset_id)
        .order_by(EvaluationRun.created_at.desc())
        .all()
    )


def create(
    db: Session,
    *,
    prompt_template_id: uuid.UUID,
    dataset_id: Optional[uuid.UUID] = None,
    experiment_name: Optional[str] = None,
    num_examples: int,
    macro_pearson_r: Optional[float] = None,
    macro_qwk: Optional[float] = None,
    macro_plus_minus_one: Optional[float] = None,
    per_dimension_metrics: Dict,
    model_name: Optional[str] = None,
    runtime_seconds: Optional[float] = None,
) -> EvaluationRun:
    """
    Create a new evaluation run.

    Args:
        db: Database session
        prompt_template_id: PromptTemplate UUID
        dataset_id: EvaluationDataset UUID
        experiment_name: Optional experiment name
        num_examples: Number of examples evaluated
        macro_pearson_r: Macro-averaged Pearson r
        macro_qwk: Macro-averaged QWK
        macro_plus_minus_one: Macro-averaged ±1 accuracy
        per_dimension_metrics: Per-dimension metrics dict
        model_name: LLM model used
        runtime_seconds: Runtime in seconds

    Returns:
        Created EvaluationRun object
    """
    run = EvaluationRun(
        prompt_template_id=prompt_template_id,
        dataset_id=dataset_id,
        experiment_name=experiment_name,
        num_examples=num_examples,
        macro_pearson_r=macro_pearson_r,
        macro_qwk=macro_qwk,
        macro_plus_minus_one=macro_plus_minus_one,
        per_dimension_metrics=per_dimension_metrics,
        model_name=model_name,
        runtime_seconds=runtime_seconds,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_latest_for_template(db: Session, template_id: uuid.UUID) -> Optional[EvaluationRun]:
    """
    Get the most recent evaluation run for a template.

    Args:
        db: Database session
        template_id: PromptTemplate UUID

    Returns:
        Latest EvaluationRun if found, None otherwise
    """
    return (
        db.query(EvaluationRun)
        .filter(EvaluationRun.prompt_template_id == template_id)
        .order_by(EvaluationRun.created_at.desc())
        .first()
    )


def get_best_run_for_template(db: Session, template_id: uuid.UUID) -> Optional[EvaluationRun]:
    """
    Get the evaluation run with highest QWK score for a template.

    Args:
        db: Database session
        template_id: PromptTemplate UUID

    Returns:
        Best EvaluationRun (by QWK) if found, None otherwise
    """
    return (
        db.query(EvaluationRun)
        .filter(
            EvaluationRun.prompt_template_id == template_id,
            EvaluationRun.macro_qwk.isnot(None)
        )
        .order_by(EvaluationRun.macro_qwk.desc())
        .first()
    )


def get_by_organization(db: Session, organization_id: uuid.UUID) -> List[EvaluationRun]:
    """
    Get all evaluation runs for an organization (via template relationship).

    Args:
        db: Database session
        organization_id: Organization UUID

    Returns:
        List of EvaluationRun objects, ordered by created_at desc
    """
    from app.models.prompt_template import PromptTemplate

    return (
        db.query(EvaluationRun)
        .join(PromptTemplate)
        .filter(PromptTemplate.organization_id == organization_id)
        .order_by(EvaluationRun.created_at.desc())
        .all()
    )

