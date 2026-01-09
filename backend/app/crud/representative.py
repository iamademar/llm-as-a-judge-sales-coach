"""
CRUD operations for Representative model.

Provides functions for creating, reading, updating, and managing representatives.
"""
from typing import Optional, List
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from app.models.representative import Representative


def get_by_id(db: Session, id: uuid.UUID) -> Optional[Representative]:
    """
    Get a representative by ID.

    Args:
        db: Database session
        id: Representative UUID

    Returns:
        Representative object if found, None otherwise
    """
    return db.query(Representative).filter(Representative.id == id).first()


def get_by_email(db: Session, email: str) -> Optional[Representative]:
    """
    Get a representative by email address.

    Args:
        db: Database session
        email: Representative email address (will be normalized)

    Returns:
        Representative object if found, None otherwise

    Note:
        Email is normalized (lowercased and stripped) for consistent lookups
    """
    normalized_email = email.strip().lower()
    return db.query(Representative).filter(Representative.email == normalized_email).first()


def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Representative]:
    """
    Get all representatives with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Representative objects
    """
    return db.query(Representative).offset(skip).limit(limit).all()


def get_active(db: Session) -> List[Representative]:
    """
    Get all active representatives.

    Args:
        db: Database session

    Returns:
        List of active Representative objects
    """
    return db.query(Representative).filter(Representative.is_active == True).all()


def create(
    db: Session,
    *,
    email: str,
    full_name: str,
    department: Optional[str] = None,
    hire_date: Optional[datetime] = None,
    organization_id: Optional[uuid.UUID] = None
) -> Representative:
    """
    Create a new representative.

    Args:
        db: Database session
        email: Representative email address (will be normalized)
        full_name: Representative's full name
        department: Optional department/team name
        hire_date: Optional hire date
        organization_id: Optional organization UUID this representative belongs to

    Returns:
        Created Representative object

    Note:
        - Email is normalized (lowercased and stripped)
        - is_active defaults to True (from model default)
    """
    normalized_email = email.strip().lower()

    representative = Representative(
        email=normalized_email,
        full_name=full_name,
        department=department,
        hire_date=hire_date,
        organization_id=organization_id,
    )
    db.add(representative)
    db.commit()
    db.refresh(representative)
    return representative


def update(
    db: Session,
    *,
    db_obj: Representative,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    hire_date: Optional[datetime] = None
) -> Representative:
    """
    Update an existing representative.

    Args:
        db: Database session
        db_obj: Representative object to update
        email: Optional new email address
        full_name: Optional new full name
        department: Optional new department
        is_active: Optional new active status
        hire_date: Optional new hire date

    Returns:
        Updated Representative object

    Note:
        Only provided fields are updated (partial updates supported)
    """
    update_data = {}
    
    if email is not None:
        update_data["email"] = email.strip().lower()
    if full_name is not None:
        update_data["full_name"] = full_name
    if department is not None:
        update_data["department"] = department
    if is_active is not None:
        update_data["is_active"] = is_active
    if hire_date is not None:
        update_data["hire_date"] = hire_date

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def deactivate(db: Session, *, db_obj: Representative) -> Representative:
    """
    Deactivate a representative (soft delete).

    Args:
        db: Database session
        db_obj: Representative object to deactivate

    Returns:
        Updated Representative object with is_active=False
    """
    db_obj.is_active = False
    db.commit()
    db.refresh(db_obj)
    return db_obj

