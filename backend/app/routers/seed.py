"""
Public seed management endpoints.

Provides endpoints for viewing seeding status and triggering manual seeding.
No authentication required - this is a demo app.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import time
import logging

from app.routers.deps import get_db
from app.schemas.seed import (
    SeedStatusResponse,
    SeedTriggerResponse,
    OrganizationSeedInfo,
    SeedTotals,
    DateRange,
    SeedSummary,
)
from app.models.organization import Organization
from app.models.representative import Representative
from app.models.transcript import Transcript
from app.models.assessment import Assessment
from app.models.user import User
from app.seed import seed_demo_data, ORG_PROFILES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/seed", tags=["seed"])


@router.get("/status", response_model=SeedStatusResponse)
def get_seed_status(db: Session = Depends(get_db)):
    """
    Get current seeding status and data counts.

    Returns information about all organizations, representatives, transcripts,
    and assessments currently in the database. Identifies which organizations
    are demo organizations from the seed data.

    This is a public endpoint - no authentication required.
    """
    # Get demo org names from seed configuration
    demo_org_names = set(ORG_PROFILES.keys())

    # Query all organizations
    orgs = db.query(Organization).all()

    # Build organization info with counts
    org_infos = []
    for org in orgs:
        # Count representatives for this org
        rep_count = (
            db.query(Representative)
            .filter(Representative.organization_id == org.id)
            .count()
        )

        # Count transcripts for this org (via representative join)
        transcript_count = (
            db.query(Transcript)
            .join(Representative)
            .filter(Representative.organization_id == org.id)
            .count()
        )

        org_infos.append(
            OrganizationSeedInfo(
                id=org.id,
                name=org.name,
                rep_count=rep_count,
                transcript_count=transcript_count,
                is_demo_org=org.name in demo_org_names,
            )
        )

    # Calculate totals
    totals = SeedTotals(
        organizations=db.query(Organization).count(),
        representatives=db.query(Representative).count(),
        transcripts=db.query(Transcript).count(),
        assessments=db.query(Assessment).count(),
    )

    # Get date range from transcripts
    date_range = None
    min_date = db.query(func.min(Transcript.created_at)).scalar()
    max_date = db.query(func.max(Transcript.created_at)).scalar()
    if min_date and max_date:
        date_range = DateRange(earliest=min_date, latest=max_date)

    # Determine seeding level
    demo_orgs_found = sum(1 for info in org_infos if info.is_demo_org)
    if demo_orgs_found == 0:
        seeding_level = "none"
    elif demo_orgs_found < len(demo_org_names):
        seeding_level = "partial"
    else:
        seeding_level = "full"

    return SeedStatusResponse(
        is_seeded=totals.organizations > 0,
        seeding_level=seeding_level,
        organizations=org_infos,
        totals=totals,
        date_range=date_range,
    )


@router.post("/trigger", response_model=SeedTriggerResponse)
def trigger_seed(db: Session = Depends(get_db)):
    """
    Trigger manual seeding operation.

    **WARNING**: This endpoint DELETES ALL existing data in the database
    (all organizations, users, representatives, transcripts, and assessments)
    before creating fresh demo data.

    This operation:
    1. Captures counts of existing data
    2. Deletes all data in correct dependency order
    3. Calls seed_demo_data() to create fresh demo data
    4. Returns summary of what was deleted and created

    This is a public endpoint - no authentication required (demo app only).
    """
    logger.info("Starting seed operation - deleting all data and reseeding")
    start_time = time.time()

    try:
        # Step 1: Capture counts before deletion
        before_orgs = db.query(Organization).count()
        before_reps = db.query(Representative).count()
        before_transcripts = db.query(Transcript).count()
        before_assessments = db.query(Assessment).count()
        before_users = db.query(User).count()

        logger.info(
            f"Before deletion: {before_orgs} orgs, {before_users} users, "
            f"{before_reps} reps, {before_transcripts} transcripts, {before_assessments} assessments"
        )

        # Step 2: Delete ALL existing data (in correct order for foreign keys)
        # Delete in reverse dependency order
        logger.info("Deleting all assessments...")
        db.query(Assessment).delete()

        logger.info("Deleting all transcripts...")
        db.query(Transcript).delete()

        logger.info("Deleting all representatives...")
        db.query(Representative).delete()

        logger.info("Deleting all users...")
        db.query(User).delete()

        logger.info("Deleting all organizations...")
        db.query(Organization).delete()

        db.commit()
        logger.info("All data deleted successfully")

        # Step 3: Run seeding (creates fresh demo data)
        logger.info("Starting demo data seeding...")
        seed_demo_data()  # Existing function handles its own session
        logger.info("Demo data seeding completed")

        # Step 4: Count newly created data
        after_orgs = db.query(Organization).count()
        after_reps = db.query(Representative).count()
        after_transcripts = db.query(Transcript).count()
        after_assessments = db.query(Assessment).count()

        logger.info(
            f"After seeding: {after_orgs} orgs, {after_reps} reps, "
            f"{after_transcripts} transcripts, {after_assessments} assessments"
        )

    except Exception as e:
        logger.error(f"Seed operation failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Seeding failed: {str(e)}"
        )

    duration = time.time() - start_time
    logger.info(f"Seed operation completed in {duration:.2f} seconds")

    return SeedTriggerResponse(
        success=True,
        message="All data deleted and demo data seeded successfully",
        summary=SeedSummary(
            organizations_deleted=before_orgs,
            representatives_deleted=before_reps,
            transcripts_deleted=before_transcripts,
            assessments_deleted=before_assessments,
            users_deleted=before_users,
            organizations_created=after_orgs,
            representatives_created=after_reps,
            transcripts_created=after_transcripts,
            assessments_created=after_assessments,
            duration_seconds=round(duration, 2),
        ),
    )
