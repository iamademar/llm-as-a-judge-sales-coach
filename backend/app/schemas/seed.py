"""
Pydantic schemas for seed management endpoints.

Defines response models for seeding status and trigger operations.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class OrganizationSeedInfo(BaseModel):
    """Information about a single organization's seeded data."""

    id: UUID = Field(..., description="Organization UUID")
    name: str = Field(..., description="Organization name")
    rep_count: int = Field(..., description="Number of representatives in this organization")
    transcript_count: int = Field(..., description="Number of transcripts for this organization")
    is_demo_org: bool = Field(..., description="Whether this is a demo organization from seed data")

    model_config = ConfigDict(from_attributes=True)


class SeedTotals(BaseModel):
    """Total counts across all seeded data."""

    organizations: int = Field(..., description="Total number of organizations")
    representatives: int = Field(..., description="Total number of representatives")
    transcripts: int = Field(..., description="Total number of transcripts")
    assessments: int = Field(..., description="Total number of assessments")


class DateRange(BaseModel):
    """Date range for seeded transcript data."""

    earliest: datetime = Field(..., description="Earliest transcript date")
    latest: datetime = Field(..., description="Latest transcript date")


class SeedStatusResponse(BaseModel):
    """Response model for GET /seed/status endpoint."""

    is_seeded: bool = Field(..., description="Whether any data exists in the database")
    seeding_level: str = Field(..., description="Seeding level: 'none', 'partial', or 'full'")
    organizations: List[OrganizationSeedInfo] = Field(..., description="List of organizations with seed info")
    totals: SeedTotals = Field(..., description="Total counts across all data")
    date_range: Optional[DateRange] = Field(None, description="Date range of transcripts (if any exist)")


class SeedSummary(BaseModel):
    """Summary of seed operation results."""

    organizations_deleted: int = Field(..., description="Number of organizations deleted")
    representatives_deleted: int = Field(..., description="Number of representatives deleted")
    transcripts_deleted: int = Field(..., description="Number of transcripts deleted")
    assessments_deleted: int = Field(..., description="Number of assessments deleted")
    users_deleted: int = Field(..., description="Number of users deleted")
    organizations_created: int = Field(..., description="Number of organizations created")
    representatives_created: int = Field(..., description="Number of representatives created")
    transcripts_created: int = Field(..., description="Number of transcripts created")
    assessments_created: int = Field(..., description="Number of assessments created")
    duration_seconds: float = Field(..., description="Total operation duration in seconds")


class SeedTriggerResponse(BaseModel):
    """Response model for POST /seed/trigger endpoint."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable message about the operation")
    summary: SeedSummary = Field(..., description="Detailed summary of what was deleted and created")
