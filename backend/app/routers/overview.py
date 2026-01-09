"""
Overview statistics endpoints for dashboard metrics.

Provides aggregated statistics across transcripts and assessments
with date range filtering and period-over-period comparisons.
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.routers.deps import get_db
from app.core.jwt_dependency import get_current_user
from app.schemas.overview import (
    OverviewStatisticsResponse,
    OverviewTrendsResponse,
    CoachingQueueResponse,
    CoachingQueueItem,
    OverviewInsightsResponse,
    OverviewInsight,
    RepLeaderboardResponse,
    RepLeaderboardItem,
    ModelHealthResponse
)
from app.models import Transcript, Assessment, Representative
from app.models.user import User

router = APIRouter(prefix="/overview", tags=["overview"])

# SPIN dimensions for composite score calculation
DIMENSIONS = ["situation", "problem", "implication", "need_payoff", "flow", "tone", "engagement"]


def calculate_composite_score(scores: dict) -> float:
    """
    Calculate composite SPIN score from individual dimension scores.
    
    Args:
        scores: Dictionary with dimension scores (1-5 scale)
        
    Returns:
        Average score across all 7 dimensions
    """
    return sum(scores.get(dim, 0) for dim in DIMENSIONS) / len(DIMENSIONS)


def calculate_statistics(
    db: Session,
    organization_id: str,
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    threshold: float
) -> dict:
    """
    Calculate overview statistics for a given period.
    
    Args:
        db: Database session
        organization_id: Organization UUID to filter by
        date_from: Start date (inclusive)
        date_to: End date (inclusive)
        threshold: Score threshold for "above target" calculation
        
    Returns:
        Dictionary with statistics: total_conversations, avg_composite_score,
        percentage_above_target, weakest_dimension, dimension_averages
    """
    # Query transcripts with their most recent assessment
    # Filter by organization through representative relationship
    query = (
        db.query(Transcript, Assessment)
        .join(Assessment, Transcript.id == Assessment.transcript_id)
        .outerjoin(Representative, Transcript.representative_id == Representative.id)
        .filter(Representative.organization_id == organization_id)
    )
    
    # Apply date filters
    if date_from:
        query = query.filter(Transcript.created_at >= date_from)
    if date_to:
        query = query.filter(Transcript.created_at <= date_to)
    
    # Get all transcript-assessment pairs
    results = query.all()
    
    # Handle multiple assessments per transcript - keep only the most recent
    transcript_assessments = {}
    for transcript, assessment in results:
        if transcript.id not in transcript_assessments:
            transcript_assessments[transcript.id] = assessment
        else:
            # Keep the most recent assessment
            if assessment.created_at > transcript_assessments[transcript.id].created_at:
                transcript_assessments[transcript.id] = assessment
    
    assessments = list(transcript_assessments.values())
    
    # If no data, return zeros
    if not assessments:
        return {
            "total_conversations": 0,
            "avg_composite_score": 0.0,
            "percentage_above_target": 0.0,
            "weakest_dimension": "N/A",
            "dimension_averages": {}
        }
    
    # Calculate composite scores
    composite_scores = [calculate_composite_score(a.scores) for a in assessments]
    
    # Calculate dimension averages
    dimension_averages = {}
    for dim in DIMENSIONS:
        scores = [a.scores.get(dim, 0) for a in assessments]
        dimension_averages[dim] = sum(scores) / len(scores) if scores else 0.0
    
    # Find weakest dimension
    weakest_dim = min(dimension_averages.items(), key=lambda x: x[1])[0]
    # Capitalize first letter and replace underscores
    weakest_dim_formatted = weakest_dim.replace("_", " ").title()
    
    # Calculate metrics
    total_conversations = len(assessments)
    avg_composite_score = sum(composite_scores) / len(composite_scores)
    above_target_count = sum(1 for score in composite_scores if score >= threshold)
    percentage_above_target = (above_target_count / total_conversations) * 100
    
    return {
        "total_conversations": total_conversations,
        "avg_composite_score": avg_composite_score,
        "percentage_above_target": percentage_above_target,
        "weakest_dimension": weakest_dim_formatted,
        "dimension_averages": dimension_averages
    }


def calculate_timeseries_statistics(
    db: Session,
    organization_id: str,
    date_from: datetime,
    date_to: datetime,
    threshold: float
) -> list[dict]:
    """
    Calculate daily SPIN dimension averages over a date range.

    Args:
        db: Database session
        organization_id: Organization UUID to filter by
        date_from: Start date (inclusive)
        date_to: End date (inclusive)
        threshold: Score threshold for percentage above target calculation

    Returns:
        List of dictionaries with daily dimension averages, conversation counts,
        and percentage above target:
        [
            {
                "date": "2025-11-27",
                "situation": 4.1,
                "problem": 3.8,
                ...
                "conversation_count": 12,
                "percent_above_target": 66.7
            }
        ]
    """
    from collections import defaultdict

    # Query all transcripts with their assessments in date range
    query = (
        db.query(Transcript, Assessment)
        .join(Assessment, Transcript.id == Assessment.transcript_id)
        .outerjoin(Representative, Transcript.representative_id == Representative.id)
        .filter(Representative.organization_id == organization_id)
        .filter(Transcript.created_at >= date_from)
        .filter(Transcript.created_at <= date_to)
        .order_by(Transcript.created_at, Assessment.created_at.desc())
    )

    results = query.all()

    # Handle multiple assessments per transcript - keep only most recent
    transcript_assessments = {}
    transcript_dates = {}  # Track which date each transcript belongs to

    for transcript, assessment in results:
        # Extract date (day) from transcript created_at
        transcript_date = transcript.created_at.date()

        if transcript.id not in transcript_assessments:
            transcript_assessments[transcript.id] = assessment
            transcript_dates[transcript.id] = transcript_date
        else:
            # Keep the most recent assessment
            if assessment.created_at > transcript_assessments[transcript.id].created_at:
                transcript_assessments[transcript.id] = assessment

    # Group assessments by date
    daily_assessments = defaultdict(list)
    for transcript_id, assessment in transcript_assessments.items():
        date_str = transcript_dates[transcript_id].isoformat()
        daily_assessments[date_str].append(assessment)

    # Calculate daily averages for each dimension
    trend_data = []
    current_date = date_from.date()
    end_date = date_to.date()

    while current_date <= end_date:
        date_str = current_date.isoformat()
        assessments_on_date = daily_assessments.get(date_str, [])

        if assessments_on_date:
            # Calculate averages for this day
            dimension_sums = {dim: 0.0 for dim in DIMENSIONS}
            count = len(assessments_on_date)

            # Calculate composite scores and threshold comparison
            composite_scores = [calculate_composite_score(a.scores) for a in assessments_on_date]
            above_target_count = sum(1 for score in composite_scores if score >= threshold)
            percent_above_target = (above_target_count / count) * 100 if count > 0 else 0.0

            for assessment in assessments_on_date:
                for dim in DIMENSIONS:
                    dimension_sums[dim] += assessment.scores.get(dim, 0)

            # Create data point with averages and volume/quality metrics
            data_point = {
                "date": date_str,
                "conversation_count": count,
                "percent_above_target": round(percent_above_target, 1),
            }
            for dim in DIMENSIONS:
                data_point[dim] = round(dimension_sums[dim] / count, 2)

            trend_data.append(data_point)
        # Skip days with no data (as per plan)

        current_date += timedelta(days=1)

    return trend_data


def aggregate_rep_assessments(
    db: Session,
    organization_id: str,
    date_from: Optional[datetime],
    date_to: Optional[datetime]
) -> dict:
    """
    Collect the latest assessment per transcript for each representative.
    """
    query = (
        db.query(Transcript, Assessment, Representative)
        .join(Assessment, Transcript.id == Assessment.transcript_id)
        .join(Representative, Transcript.representative_id == Representative.id)
        .filter(Representative.organization_id == organization_id)
    )

    if date_from:
        query = query.filter(Transcript.created_at >= date_from)
    if date_to:
        query = query.filter(Transcript.created_at <= date_to)

    results = query.order_by(Assessment.created_at.desc()).all()

    rep_assessments: dict[str, dict] = {}
    for transcript, assessment, representative in results:
        rep_id = str(representative.id)
        if rep_id not in rep_assessments:
            rep_assessments[rep_id] = {
                "rep": representative,
                "assessments": {}
            }

        # Keep latest assessment per transcript for this rep
        existing = rep_assessments[rep_id]["assessments"].get(transcript.id)
        if existing is None or assessment.created_at > existing.created_at:
            rep_assessments[rep_id]["assessments"][transcript.id] = assessment

    return rep_assessments


def calculate_rep_leaderboard_stats(rep_assessments: dict[str, dict]) -> dict[str, dict]:
    """
    Compute aggregated metrics per representative from assessment map.
    """
    leaderboard: dict[str, dict] = {}

    for rep_id, data in rep_assessments.items():
        assessments = list(data["assessments"].values())
        if not assessments:
            continue

        composite_scores = [calculate_composite_score(a.scores) for a in assessments]
        avg_composite = sum(composite_scores) / len(composite_scores)

        # Dimension averages to find strongest/weakest areas
        dimension_sums = {dim: 0.0 for dim in DIMENSIONS}
        for assessment in assessments:
            for dim in DIMENSIONS:
                dimension_sums[dim] += assessment.scores.get(dim, 0)

        dimension_averages = {
            dim: dimension_sums[dim] / len(assessments) if len(assessments) else 0.0
            for dim in DIMENSIONS
        }

        strongest_dim, strongest_score = max(dimension_averages.items(), key=lambda x: x[1])
        weakest_dim, weakest_score = min(dimension_averages.items(), key=lambda x: x[1])

        leaderboard[rep_id] = {
            "rep": data["rep"].full_name,
            "conversation_count": len(assessments),
            "avg_composite": avg_composite,
            "strongest": strongest_dim.replace("_", " ").title(),
            "strongest_score": strongest_score,
            "weakest": weakest_dim.replace("_", " ").title(),
            "weakest_score": weakest_score
        }

    return leaderboard


@router.get("/rep-leaderboard", response_model=RepLeaderboardResponse)
def get_rep_leaderboard(
    date_from: Optional[datetime] = Query(
        None,
        description="Start date for filtering (inclusive). Defaults to 30 days ago."
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="End date for filtering (inclusive). Defaults to now."
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum number of reps to return"
    ),
    include_trend: bool = Query(
        True,
        description="Whether to compare against previous period for trend metric"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get representative leaderboard for the overview page.

    Ranks reps by average composite SPIN score within the selected date range.
    Trend compares average composite to the previous equally sized window.
    """
    from fastapi import HTTPException

    # Default date range: last 30 days
    if date_to is None:
        date_to = datetime.utcnow()
    if date_from is None:
        date_from = date_to - timedelta(days=30)

    # Validate date range and enforce a 90-day limit
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be before or equal to date_to")

    date_range_days = (date_to - date_from).days
    if date_range_days > 90:
        raise HTTPException(
            status_code=400,
            detail="Date range cannot exceed 90 days. Please select a shorter time period."
        )

    organization_id = str(current_user.organization_id)

    # Current period stats
    rep_assessments = aggregate_rep_assessments(
        db=db,
        organization_id=organization_id,
        date_from=date_from,
        date_to=date_to
    )
    current_stats = calculate_rep_leaderboard_stats(rep_assessments)

    # Previous period stats for trend comparison
    prev_stats: dict[str, dict] = {}
    if include_trend:
        period_duration = date_to - date_from
        prev_date_to = date_from - timedelta(seconds=1)
        prev_date_from = prev_date_to - period_duration

        prev_assessments = aggregate_rep_assessments(
            db=db,
            organization_id=organization_id,
            date_from=prev_date_from,
            date_to=prev_date_to
        )
        prev_stats = calculate_rep_leaderboard_stats(prev_assessments)

    # Build ranked list sorted by average composite score
    sorted_reps = sorted(
        current_stats.items(),
        key=lambda item: item[1]["avg_composite"],
        reverse=True
    )

    items: list[RepLeaderboardItem] = []
    for idx, (rep_id, stats) in enumerate(sorted_reps[:limit], start=1):
        prev_avg = prev_stats.get(rep_id, {}).get("avg_composite")
        trend = 0.0
        if include_trend and prev_avg is not None:
            trend = round(stats["avg_composite"] - prev_avg, 2)

        items.append(
            RepLeaderboardItem(
                rank=idx,
                rep=stats["rep"],
                conversation_count=stats["conversation_count"],
                avg_composite=round(stats["avg_composite"], 2),
                strongest=stats["strongest"],
                strongest_score=round(stats["strongest_score"], 2),
                weakest=stats["weakest"],
                weakest_score=round(stats["weakest_score"], 2),
                trend=trend
            )
        )

    return RepLeaderboardResponse(items=items)


def format_delta(current: float, previous: float, is_percentage: bool = True, is_score: bool = False) -> str:
    """
    Format delta between current and previous values.

    Args:
        current: Current period value
        previous: Previous period value
        is_percentage: If True, format as percentage change
        is_score: If True, format as score difference (e.g., +0.2)

    Returns:
        Formatted delta string (e.g., "+18%", "-3%", "+0.2")
    """
    if previous == 0:
        # Avoid division by zero
        if current > 0:
            return "+100%" if is_percentage else "+100"
        return "0%" if is_percentage else "0"

    if is_score:
        # For scores, show absolute difference
        delta = current - previous
        sign = "+" if delta > 0 else ""
        return f"{sign}{delta:.1f}"
    else:
        # For counts/percentages, show percentage change
        delta = ((current - previous) / previous) * 100
        sign = "+" if delta > 0 else ""
        return f"{sign}{delta:.0f}%"


@router.get("/statistics")
def get_overview_statistics(
    date_from: Optional[datetime] = Query(
        None,
        description="Start date for filtering (inclusive). Defaults to 30 days ago."
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="End date for filtering (inclusive). Defaults to now."
    ),
    threshold: float = Query(
        3.5,
        ge=1.0,
        le=5.0,
        description="Score threshold for 'above target' calculation"
    ),
    include_deltas: bool = Query(
        True,
        description="Whether to calculate delta metrics compared to previous period"
    ),
    timeseries: bool = Query(
        False,
        description="If true, return daily time-series data instead of aggregate statistics"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overview statistics for the dashboard.

    **Two modes:**

    1. **Aggregate Mode** (default, `timeseries=false`):
       Returns single-snapshot metrics (total conversations, average score, etc.)
       Response type: OverviewStatisticsResponse

    2. **Time-Series Mode** (`timeseries=true`):
       Returns daily SPIN dimension averages for trend charts.
       Response type: OverviewTrendsResponse

    Requires authentication. Statistics are filtered by user's organization.
    """
    from fastapi import HTTPException

    # Validate user has an organization
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="Your account is not associated with an organization. Please contact support."
        )

    # Default date range: last 30 days
    if date_to is None:
        date_to = datetime.utcnow()
    if date_from is None:
        date_from = date_to - timedelta(days=30)

    # Validate date range
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be before or equal to date_to")

    # Enforce 90-day maximum range limit
    date_range_days = (date_to - date_from).days
    if date_range_days > 90:
        raise HTTPException(
            status_code=400,
            detail="Date range cannot exceed 90 days. Please select a shorter time period."
        )

    # TIME-SERIES MODE
    if timeseries:
        trend_data = calculate_timeseries_statistics(
            db=db,
            organization_id=str(current_user.organization_id),
            date_from=date_from,
            date_to=date_to,
            threshold=threshold
        )

        # Calculate metadata
        total_days = (date_to.date() - date_from.date()).days + 1
        days_with_data = len(trend_data)

        return OverviewTrendsResponse(
            trend_data=trend_data,
            total_days=total_days,
            days_with_data=days_with_data
        )
    
    # Calculate current period statistics
    current_stats = calculate_statistics(
        db=db,
        organization_id=str(current_user.organization_id),
        date_from=date_from,
        date_to=date_to,
        threshold=threshold
    )
    
    # Calculate deltas if requested
    delta_conversations = None
    delta_score = None
    delta_percentage = None
    
    if include_deltas:
        # Calculate previous period (same duration)
        period_duration = date_to - date_from
        prev_date_to = date_from - timedelta(seconds=1)  # End just before current period
        prev_date_from = prev_date_to - period_duration
        
        previous_stats = calculate_statistics(
            db=db,
            organization_id=str(current_user.organization_id),
            date_from=prev_date_from,
            date_to=prev_date_to,
            threshold=threshold
        )
        
        # Format deltas
        if previous_stats["total_conversations"] > 0:
            delta_conversations = format_delta(
                current_stats["total_conversations"],
                previous_stats["total_conversations"],
                is_percentage=True
            )
            delta_score = format_delta(
                current_stats["avg_composite_score"],
                previous_stats["avg_composite_score"],
                is_score=True
            )
            delta_percentage = format_delta(
                current_stats["percentage_above_target"],
                previous_stats["percentage_above_target"],
                is_percentage=True
            )
    
    return OverviewStatisticsResponse(
        total_conversations=current_stats["total_conversations"],
        avg_composite_score=round(current_stats["avg_composite_score"], 2),
        percentage_above_target=round(current_stats["percentage_above_target"], 1),
        weakest_dimension=current_stats["weakest_dimension"],
        dimension_averages={k: round(v, 2) for k, v in current_stats["dimension_averages"].items()},
        delta_conversations=delta_conversations,
        delta_score=delta_score,
        delta_percentage=delta_percentage
    )


@router.get("/coaching-queue", response_model=CoachingQueueResponse)
def get_coaching_queue(
    date_from: Optional[datetime] = Query(
        None,
        description="Start date for filtering (inclusive). Defaults to 30 days ago."
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="End date for filtering (inclusive). Defaults to now."
    ),
    threshold: float = Query(
        3.5,
        ge=1.0,
        le=5.0,
        description="Score threshold for coaching queue (conversations below this value)"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum number of items to return"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get coaching queue: conversations needing attention.

    Returns conversations with composite scores below the threshold,
    ordered by most recently analyzed first. Filtered by organization
    and date range.

    Requires authentication. Results are filtered by user's organization.
    """
    from fastapi import HTTPException

    # Default date range: last 30 days
    if date_to is None:
        date_to = datetime.utcnow()
    if date_from is None:
        date_from = date_to - timedelta(days=30)

    # Validate date range
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be before or equal to date_to")

    # Query transcripts with their most recent assessment
    # Filter by organization through representative relationship
    query = (
        db.query(Transcript, Assessment, Representative)
        .join(Assessment, Transcript.id == Assessment.transcript_id)
        .join(Representative, Transcript.representative_id == Representative.id)
        .filter(Representative.organization_id == str(current_user.organization_id))
        .filter(Transcript.created_at >= date_from)
        .filter(Transcript.created_at <= date_to)
        .order_by(Assessment.created_at.desc())
    )

    results = query.all()

    # Handle multiple assessments per transcript - keep only the most recent
    # Track which transcripts we've processed to ensure we only use the most recent assessment
    transcript_data = {}
    seen_transcripts = set()
    
    for transcript, assessment, representative in results:
        # Skip if we've already processed this transcript (query is ordered by assessment created_at desc)
        if transcript.id in seen_transcripts:
            continue
            
        seen_transcripts.add(transcript.id)
        
        # Calculate composite score for the most recent assessment
        composite_score = calculate_composite_score(assessment.scores)
        
        # Only include if below threshold
        if composite_score < threshold:
            # Find weakest dimension
            dimension_scores = {dim: assessment.scores.get(dim, 0) for dim in DIMENSIONS}
            weakest_dim = min(dimension_scores.items(), key=lambda x: x[1])[0]
            weakest_dim_formatted = weakest_dim.replace("_", " ").title()
            
            transcript_data[transcript.id] = {
                "transcript": transcript,
                "assessment": assessment,
                "representative": representative,
                "composite_score": composite_score,
                "weakest_dim": weakest_dim_formatted
            }

    # Sort by assessment created_at (newest first) and limit
    sorted_items = sorted(
        transcript_data.values(),
        key=lambda x: x["assessment"].created_at,
        reverse=True
    )[:limit]

    # Build response items
    items = [
        CoachingQueueItem(
            id=item["transcript"].id,
            rep=item["representative"].full_name,
            buyer=item["transcript"].buyer_id or "Unknown",
            composite=round(item["composite_score"], 1),
            weakest_dim=item["weakest_dim"],
            created_at=item["assessment"].created_at.isoformat()
        )
        for item in sorted_items
    ]

    return CoachingQueueResponse(
        items=items,
        total_count=len(transcript_data)
    )


@router.get("/insights", response_model=OverviewInsightsResponse)
def get_overview_insights(
    date_from: Optional[datetime] = Query(
        None,
        description="Start date for filtering (inclusive). Defaults to 30 days ago."
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="End date for filtering (inclusive). Defaults to now."
    ),
    threshold: float = Query(
        3.5,
        ge=1.0,
        le=5.0,
        description="Score threshold for coaching queue (conversations below this value)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate coaching insights for the overview page.

    Combines snapshot statistics, period deltas, and coaching backlog size
    into a concise set of bullet insights for quick scanning.
    """
    from fastapi import HTTPException

    # Default date range: last 30 days
    if date_to is None:
        date_to = datetime.utcnow()
    if date_from is None:
        date_from = date_to - timedelta(days=30)

    # Validate date range
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be before or equal to date_to")

    # Calculate current statistics
    current_stats = calculate_statistics(
        db=db,
        organization_id=str(current_user.organization_id),
        date_from=date_from,
        date_to=date_to,
        threshold=threshold
    )

    # Calculate previous period statistics for deltas
    period_duration = date_to - date_from
    prev_date_to = date_from - timedelta(seconds=1)
    prev_date_from = prev_date_to - period_duration
    previous_stats = calculate_statistics(
        db=db,
        organization_id=str(current_user.organization_id),
        date_from=prev_date_from,
        date_to=prev_date_to,
        threshold=threshold
    )

    insights: list[OverviewInsight] = []

    # If no data, return a single informative insight
    if current_stats["total_conversations"] == 0:
        insights.append(OverviewInsight(
            title="No conversations yet",
            detail="No assessed conversations in the selected window; add transcripts to see insights."
        ))
        return OverviewInsightsResponse(insights=insights)

    # Score trend
    delta_score = None
    if previous_stats["total_conversations"] > 0:
        delta_score = format_delta(
            current_stats["avg_composite_score"],
            previous_stats["avg_composite_score"],
            is_score=True
        )
    insights.append(OverviewInsight(
        title="Score trend",
        detail=f"Avg composite {current_stats['avg_composite_score']:.2f}" + (f" ({delta_score} vs prior period)" if delta_score else "")
    ))

    # Above-target rate
    delta_percentage = None
    if previous_stats["total_conversations"] > 0:
        delta_percentage = format_delta(
            current_stats["percentage_above_target"],
            previous_stats["percentage_above_target"],
            is_percentage=True
        )
    insights.append(OverviewInsight(
        title="Above-target rate",
        detail=f"{current_stats['percentage_above_target']:.1f}% of conversations meet the target" + (f" ({delta_percentage})" if delta_percentage else "")
    ))

    # Weakest dimension
    weakest_dim = current_stats["weakest_dimension"]
    weakest_score = 0.0
    if current_stats["dimension_averages"]:
        weakest_score = min(current_stats["dimension_averages"].values())
    insights.append(OverviewInsight(
        title="Weakest dimension",
        detail=f"{weakest_dim} remains lowest at {weakest_score:.2f}; prioritize coaching here."
    ))

    # Coaching backlog (reuse coaching queue logic without the limit)
    query = (
        db.query(Transcript, Assessment, Representative)
        .join(Assessment, Transcript.id == Assessment.transcript_id)
        .join(Representative, Transcript.representative_id == Representative.id)
        .filter(Representative.organization_id == str(current_user.organization_id))
        .filter(Transcript.created_at >= date_from)
        .filter(Transcript.created_at <= date_to)
        .order_by(Assessment.created_at.desc())
    )

    results = query.all()
    transcript_data = {}
    seen_transcripts = set()
    
    for transcript, assessment, representative in results:
        # Skip if we've already processed this transcript (query is ordered by assessment created_at desc)
        if transcript.id in seen_transcripts:
            continue
            
        seen_transcripts.add(transcript.id)
        
        # Calculate composite score for the most recent assessment
        composite_score = calculate_composite_score(assessment.scores)
        if composite_score < threshold:
            transcript_data[transcript.id] = {
                "assessment": assessment
            }

    backlog_count = len(transcript_data)
    insights.append(OverviewInsight(
        title="Coaching backlog",
        detail=f"{backlog_count} conversation{'s' if backlog_count != 1 else ''} below {threshold} need review."
    ))

    return OverviewInsightsResponse(insights=insights)


def derive_model_status(qwk: float) -> str:
    """
    Derive model health status from QWK score.

    Args:
        qwk: Quadratic Weighted Kappa score (0.0 to 1.0)

    Returns:
        Status string: "healthy", "warning", or "critical"
    """
    if qwk >= 0.70:
        return "healthy"
    elif qwk >= 0.50:
        return "warning"
    else:
        return "critical"


@router.get("/model-health", response_model=Optional[ModelHealthResponse])
def get_model_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get model health/calibration metrics for the overview dashboard.

    Returns metrics from the latest evaluation run for the active template,
    combined with recent production latency data.

    Returns None if no active template or no evaluation data exists.
    """
    from app.models.prompt_template import PromptTemplate
    from app.models.evaluation_run import EvaluationRun
    from app.crud import prompt_template as template_crud

    # 1. Get active template for organization
    org_id = str(current_user.organization_id)
    active_template = template_crud.get_active_for_org(db, org_id)

    if not active_template:
        return None

    # 2. Get latest evaluation run for active template
    latest_eval = (
        db.query(EvaluationRun)
        .filter(EvaluationRun.prompt_template_id == active_template.id)
        .order_by(EvaluationRun.created_at.desc())
        .first()
    )

    if not latest_eval or latest_eval.macro_qwk is None:
        return None

    # 3. Calculate average latency from recent assessments using same model
    # Filter by model_name and get last 100 assessments
    # Need to use a subquery approach for proper LIMIT with AVG
    from sqlalchemy import select

    # Subquery to get last 100 assessments with latency
    recent_assessments_subquery = (
        select(Assessment.latency_ms)
        .join(Transcript, Assessment.transcript_id == Transcript.id)
        .join(Representative, Transcript.representative_id == Representative.id)
        .filter(Representative.organization_id == org_id)
        .filter(Assessment.model_name == latest_eval.model_name)
        .filter(Assessment.latency_ms.isnot(None))
        .order_by(Assessment.created_at.desc())
        .limit(100)
        .subquery()
    )

    avg_latency = db.query(func.avg(recent_assessments_subquery.c.latency_ms)).scalar()

    # Convert to int or None
    avg_latency_ms = int(avg_latency) if avg_latency else None

    # 4. Derive status from QWK score
    status = derive_model_status(latest_eval.macro_qwk)

    # 5. Build response
    return ModelHealthResponse(
        model_name=latest_eval.model_name or "unknown",
        prompt_version=active_template.version,
        last_eval_date=latest_eval.created_at,
        macro_pearson_r=latest_eval.macro_pearson_r or 0.0,
        macro_qwk=latest_eval.macro_qwk,
        avg_latency_ms=avg_latency_ms,
        status=status
    )
