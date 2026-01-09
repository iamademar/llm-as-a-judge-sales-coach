"""
CRUD operations for Transcript model.

Provides functions for creating, reading, and managing transcripts.
"""
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy.orm import Session

from app.models.transcript import Transcript


def get_by_id(db: Session, id: int) -> Optional[Transcript]:
    """
    Get a transcript by ID.
    
    Args:
        db: Database session
        id: Transcript ID
        
    Returns:
        Transcript object if found, None otherwise
    """
    return db.query(Transcript).filter(Transcript.id == id).first()


def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Transcript]:
    """
    Get all transcripts with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of Transcript objects
    """
    return db.query(Transcript).offset(skip).limit(limit).all()


def get_by_representative(
    db: Session,
    representative_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Transcript]:
    """
    Get all transcripts for a specific representative.
    
    Args:
        db: Database session
        representative_id: Representative UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of Transcript objects for the representative
    """
    return (
        db.query(Transcript)
        .filter(Transcript.representative_id == representative_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create(
    db: Session,
    *,
    representative_id: Optional[uuid.UUID] = None,
    buyer_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    transcript: str
) -> Transcript:
    """
    Create a new transcript.
    
    Args:
        db: Database session
        representative_id: Optional representative UUID
        buyer_id: Optional buyer/customer identifier
        metadata: Optional additional call metadata
        transcript: Full conversation text with speaker tags
        
    Returns:
        Created Transcript object
    """
    transcript_obj = Transcript(
        representative_id=representative_id,
        buyer_id=buyer_id,
        call_metadata=metadata,
        transcript=transcript,
    )
    db.add(transcript_obj)
    db.commit()
    db.refresh(transcript_obj)
    return transcript_obj

