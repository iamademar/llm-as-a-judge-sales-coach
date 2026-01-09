"""
CRUD operations for EvaluationDataset model.

Provides functions for managing evaluation datasets (golden sets).
"""
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.evaluation_dataset import EvaluationDataset


def get_by_id(db: Session, dataset_id: uuid.UUID) -> Optional[EvaluationDataset]:
    """
    Get an evaluation dataset by ID.

    Args:
        db: Database session
        dataset_id: Dataset UUID

    Returns:
        EvaluationDataset object if found, None otherwise
    """
    return db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()


def get_by_org(db: Session, organization_id: uuid.UUID) -> List[EvaluationDataset]:
    """
    Get all evaluation datasets for an organization.

    Args:
        db: Database session
        organization_id: Organization UUID

    Returns:
        List of EvaluationDataset objects, ordered by created_at desc
    """
    return (
        db.query(EvaluationDataset)
        .filter(EvaluationDataset.organization_id == organization_id)
        .order_by(EvaluationDataset.created_at.desc())
        .all()
    )


def create(
    db: Session,
    *,
    organization_id: uuid.UUID,
    name: str,
    description: Optional[str] = None,
    source_type: str = "csv",
    source_path: Optional[str] = None,
    num_examples: int,
) -> EvaluationDataset:
    """
    Create a new evaluation dataset.

    Args:
        db: Database session
        organization_id: Organization UUID
        name: Dataset name
        description: Dataset description
        source_type: Source type (csv, langsmith, database)
        source_path: File path or LangSmith dataset ID
        num_examples: Number of examples in dataset

    Returns:
        Created EvaluationDataset object
    """
    dataset = EvaluationDataset(
        organization_id=organization_id,
        name=name,
        description=description,
        source_type=source_type,
        source_path=source_path,
        num_examples=num_examples,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def update(
    db: Session,
    dataset: EvaluationDataset,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    source_type: Optional[str] = None,
    source_path: Optional[str] = None,
    num_examples: Optional[int] = None,
) -> EvaluationDataset:
    """
    Update an existing evaluation dataset.

    Args:
        db: Database session
        dataset: EvaluationDataset object to update
        name: New dataset name
        description: New description
        source_type: New source type
        source_path: New source path
        num_examples: New example count

    Returns:
        Updated EvaluationDataset object
    """
    if name is not None:
        dataset.name = name
    if description is not None:
        dataset.description = description
    if source_type is not None:
        dataset.source_type = source_type
    if source_path is not None:
        dataset.source_path = source_path
    if num_examples is not None:
        dataset.num_examples = num_examples

    db.commit()
    db.refresh(dataset)
    return dataset


def delete(db: Session, dataset: EvaluationDataset) -> None:
    """
    Delete an evaluation dataset.

    Args:
        db: Database session
        dataset: EvaluationDataset object to delete
    """
    db.delete(dataset)
    db.commit()

