"""
CRUD operations for Organization model.

Provides functions for creating, reading, and managing organizations.
"""
from typing import Optional, List
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.organization import Organization


def get_by_id(db: Session, id: uuid.UUID) -> Optional[Organization]:
    """
    Get an organization by ID.

    Args:
        db: Database session
        id: Organization UUID

    Returns:
        Organization object if found, None otherwise
    """
    return db.query(Organization).filter(Organization.id == id).first()


def get_by_name(db: Session, name: str) -> Optional[Organization]:
    """
    Get an organization by name (case-insensitive).

    Args:
        db: Database session
        name: Organization name (will be normalized)

    Returns:
        Organization object if found, None otherwise

    Note:
        Name matching is case-insensitive for consistent lookups
    """
    normalized_name = name.strip()
    return db.query(Organization).filter(
        func.lower(Organization.name) == func.lower(normalized_name)
    ).first()


def get_active(db: Session, skip: int = 0, limit: int = 100) -> List[Organization]:
    """
    Get all active organizations with pagination.

    Args:
        db: Database session
        skip: Number of records to skip (pagination offset)
        limit: Maximum number of records to return

    Returns:
        List of active Organization objects
    """
    return (
        db.query(Organization)
        .filter(Organization.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create(
    db: Session,
    *,
    name: str,
    description: Optional[str] = None
) -> Organization:
    """
    Create a new organization.

    Args:
        db: Database session
        name: Organization name (will be trimmed)
        description: Optional organization description

    Returns:
        Created organization object

    Note:
        Organization is created as active by default.
        Caller should verify name uniqueness before calling this function.
    """
    org = Organization(
        name=name.strip(),
        description=description,
        is_active=True
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org
