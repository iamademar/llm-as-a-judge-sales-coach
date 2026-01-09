"""
Representative management endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.routers.deps import get_db
from app.core.jwt_dependency import get_current_user
from app.schemas.representative import (
    RepresentativeCreate,
    RepresentativeUpdate,
    RepresentativeInDB
)
from app.crud import representative as rep_crud
from app.models.user import User

router = APIRouter(prefix="/representatives", tags=["representatives"])


@router.post("", response_model=RepresentativeInDB, status_code=201)
def create_representative(
    data: RepresentativeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new representative.
    
    Requires authentication. Validates that email is unique.
    The representative automatically inherits the organization_id from the creating user.
    """
    # Check if email already exists
    existing = rep_crud.get_by_email(db, email=data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    rep = rep_crud.create(
        db,
        email=data.email,
        full_name=data.full_name,
        department=data.department,
        hire_date=data.hire_date,
        organization_id=current_user.organization_id
    )
    return rep


@router.get("", response_model=List[RepresentativeInDB])
def list_representatives(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all representatives.
    
    Supports pagination via skip/limit and filtering for active representatives only.
    Requires authentication.
    """
    if active_only:
        return rep_crud.get_active(db)
    return rep_crud.get_all(db, skip=skip, limit=limit)


@router.get("/{rep_id}", response_model=RepresentativeInDB)
def get_representative(
    rep_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific representative by ID.
    
    Requires authentication.
    Returns 404 if representative not found.
    """
    from uuid import UUID
    
    try:
        uuid_id = UUID(rep_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    rep = rep_crud.get_by_id(db, uuid_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Representative not found")
    return rep


@router.patch("/{rep_id}", response_model=RepresentativeInDB)
def update_representative(
    rep_id: str,
    data: RepresentativeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a representative.
    
    Supports partial updates - only provided fields are updated.
    Requires authentication.
    Returns 404 if representative not found.
    """
    from uuid import UUID
    
    try:
        uuid_id = UUID(rep_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    rep = rep_crud.get_by_id(db, uuid_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Representative not found")
    
    update_data = data.model_dump(exclude_unset=True)
    updated = rep_crud.update(db, db_obj=rep, **update_data)
    return updated


@router.post("/{rep_id}/deactivate", response_model=RepresentativeInDB)
def deactivate_representative(
    rep_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deactivate a representative (soft delete).
    
    Sets is_active to False rather than deleting the record.
    Requires authentication.
    Returns 404 if representative not found.
    """
    from uuid import UUID
    
    try:
        uuid_id = UUID(rep_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    rep = rep_crud.get_by_id(db, uuid_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Representative not found")
    
    return rep_crud.deactivate(db, db_obj=rep)

