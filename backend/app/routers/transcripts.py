"""
Transcript management endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.routers.deps import get_db
from app.core.jwt_dependency import get_current_user
from app.schemas.transcript import (
    TranscriptCreate,
    TranscriptInDB
)
from app.crud import transcript as transcript_crud
from app.models.user import User

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("", response_model=TranscriptInDB, status_code=201)
def create_transcript(
    data: TranscriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new transcript.
    
    Requires authentication. Creates a transcript record without assessment.
    To assess, call POST /assess separately.
    """
    from uuid import UUID
    
    # Parse representative_id if provided
    representative_id = None
    if data.representative_id:
        try:
            representative_id = UUID(data.representative_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid representative_id UUID format")
    
    transcript = transcript_crud.create(
        db,
        representative_id=representative_id,
        buyer_id=data.buyer_id,
        metadata=data.metadata,
        transcript=data.transcript
    )
    return transcript


@router.get("", response_model=List[TranscriptInDB])
def list_transcripts(
    skip: int = 0,
    limit: int = 100,
    representative_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List transcripts.
    
    Supports pagination via skip/limit and filtering by representative_id.
    Requires authentication.
    """
    from uuid import UUID
    
    if representative_id:
        try:
            rep_uuid = UUID(representative_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid representative_id UUID format")
        
        return transcript_crud.get_by_representative(db, rep_uuid, skip=skip, limit=limit)
    
    return transcript_crud.get_all(db, skip=skip, limit=limit)


@router.get("/{transcript_id}", response_model=TranscriptInDB)
def get_transcript(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific transcript by ID.
    
    Requires authentication.
    Returns 404 if transcript not found.
    """
    transcript = transcript_crud.get_by_id(db, transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript

