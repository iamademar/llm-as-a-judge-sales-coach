"""
Assessment router for SPIN scoring and coaching.
"""
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.routers.deps import get_db
from app.core.jwt_dependency import get_current_user
from app.schemas import AssessRequest, AssessResponse, AssessmentScores, Coaching, AssessmentInDB
from app.services.scorer import score_transcript
from app.models import Transcript, Assessment
from app.models.user import User

router = APIRouter(prefix="/assess", tags=["assess"])


@router.post("", response_model=AssessResponse)
def assess(
    req: AssessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AssessResponse:
    """
    Assess a sales conversation using SPIN framework.
    
    Authentication: Requires valid JWT Bearer token.

    Args:
        req: AssessRequest containing transcript and metadata
        db: Database session (injected)
        current_user: Authenticated user from JWT token

    Returns:
        AssessResponse with assessment_id, scores, and coaching

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 502 if LLM scoring fails
    """
    # 1) Persist transcript
    transcript = Transcript(
        representative_id=req.metadata.get("representative_id"),
        buyer_id=req.metadata.get("buyer_id"),
        call_metadata=req.metadata,
        transcript=req.transcript,
    )
    db.add(transcript)
    db.flush()

    # 2) Score via LLM
    # Get organization_id from authenticated user
    organization_id = current_user.organization_id if current_user.organization_id else None

    start_time = time.time()
    try:
        data, model_name, prompt_ver = score_transcript(
            req.transcript,
            organization_id=organization_id,
            db=db,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"LLM failed: {e}")

    latency_ms = int((time.time() - start_time) * 1000)

    # 3) Persist assessment
    assessment = Assessment(
        transcript_id=transcript.id,
        scores=data["scores"],
        coaching=data["coaching"],
        model_name=model_name,
        prompt_version=prompt_ver,
        latency_ms=latency_ms,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return AssessResponse(
        assessment_id=assessment.id,
        scores=AssessmentScores(**data["scores"]),
        coaching=Coaching(**data["coaching"]),
    )


@router.get("", response_model=List[AssessmentInDB])
def list_assessments(
    skip: int = 0,
    limit: int = 100,
    transcript_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List assessments.
    
    Supports pagination via skip/limit and filtering by transcript_id.
    Requires authentication.
    """
    query = db.query(Assessment)
    
    if transcript_id is not None:
        query = query.filter(Assessment.transcript_id == transcript_id)
    
    assessments = query.offset(skip).limit(limit).all()
    return assessments


@router.get("/by-transcript/{transcript_id}", response_model=List[AssessmentInDB])
def get_assessments_by_transcript(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all assessments for a specific transcript.
    
    Requires authentication.
    """
    assessments = db.query(Assessment).filter(Assessment.transcript_id == transcript_id).all()
    return assessments
