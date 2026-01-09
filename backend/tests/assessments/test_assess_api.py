"""
Integration tests for the /assess endpoint.

Tests cover:
- POST /assess - Create assessment with SPIN scoring
- GET /assess - List assessments with pagination
- GET /assess/by-transcript/{transcript_id} - Get assessments by transcript
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Transcript, Assessment, Representative, User, Organization, PromptTemplate


def test_assess_endpoint_success(
    test_client: TestClient,
    db_session: Session,
    auth_headers: dict,
    sample_user: User,
    sample_prompt_template: PromptTemplate,
):
    """
    Test successful assessment flow with MOCK_LLM=true.

    Verifies:
    - 200 response
    - Valid response structure
    - DB rows created
    """
    payload = {
        "transcript": "Rep: Hi there\nBuyer: Hello",
        "metadata": {"buyer_id": "b1"}
    }

    response = test_client.post(
        "/assess",
        json=payload,
        headers=auth_headers
    )

    # Assert response
    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "assessment_id" in data
    assert "scores" in data
    assert "coaching" in data

    # Validate scores structure
    scores = data["scores"]
    required_score_keys = [
        "situation", "problem", "implication", "need_payoff",
        "flow", "tone", "engagement"
    ]
    for key in required_score_keys:
        assert key in scores
        assert 1 <= scores[key] <= 5

    # Validate coaching structure
    coaching = data["coaching"]
    assert "summary" in coaching
    assert "wins" in coaching
    assert "gaps" in coaching
    assert "next_actions" in coaching
    assert isinstance(coaching["wins"], list)
    assert isinstance(coaching["gaps"], list)
    assert isinstance(coaching["next_actions"], list)

    # Verify DB persistence
    transcripts = db_session.query(Transcript).all()
    assessments = db_session.query(Assessment).all()

    assert len(transcripts) == 1
    assert len(assessments) == 1

    transcript = transcripts[0]
    assert transcript.transcript == payload["transcript"]
    assert transcript.buyer_id == "b1"

    assessment = assessments[0]
    assert assessment.transcript_id == transcript.id
    assert assessment.model_name is not None
    assert assessment.prompt_version is not None
    assert assessment.latency_ms is not None


def test_assess_endpoint_llm_failure(
    test_client: TestClient,
    db_session: Session,
    auth_headers: dict,
    sample_prompt_template: PromptTemplate,
):
    """
    Test that LLM failures return 502 with error details.

    Simulates scorer failure by monkeypatching.
    """
    payload = {
        "transcript": "Rep: Test\nBuyer: Test",
        "metadata": {}
    }

    # Monkeypatch scorer to raise exception
    with patch("app.routers.assess.score_transcript") as mock_scorer:
        mock_scorer.side_effect = Exception("LLM service unavailable")

        response = test_client.post(
            "/assess",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 502
        data = response.json()
        # Error is wrapped in "error" object by error handler
        assert "error" in data
        assert "message" in data["error"]
        assert "LLM failed" in data["error"]["message"]

    # Verify no DB rows created on failure
    transcripts = db_session.query(Transcript).all()
    assessments = db_session.query(Assessment).all()

    # Transcript should not be committed due to rollback
    assert len(transcripts) == 0
    assert len(assessments) == 0


def test_assess_endpoint_missing_transcript(test_client: TestClient, auth_headers: dict):
    """Test that missing transcript field returns validation error."""
    payload = {"metadata": {}}

    response = test_client.post(
        "/assess",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 422
    data = response.json()
    # Validation errors are wrapped in "error" object
    assert "error" in data


def test_assess_endpoint_empty_metadata(
    test_client: TestClient,
    db_session: Session,
    auth_headers: dict,
    sample_prompt_template: PromptTemplate,
):
    """Test that empty metadata is handled gracefully."""
    payload = {
        "transcript": "Rep: Quick test\nBuyer: Okay",
        "metadata": {}
    }

    response = test_client.post(
        "/assess",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "assessment_id" in data

    # Verify DB persistence with None values for representative_id/buyer_id
    transcript = db_session.query(Transcript).first()
    assert transcript.representative_id is None
    assert transcript.buyer_id is None


def test_assess_endpoint_unauthorized(test_client: TestClient):
    """Test that missing authentication returns 403."""
    payload = {
        "transcript": "Rep: Test\nBuyer: Test",
        "metadata": {}
    }

    response = test_client.post(
        "/assess",
        json=payload,
        # No auth headers
    )

    assert response.status_code == 403


def test_list_assessments_pagination(
    test_client: TestClient,
    db_session: Session,
    auth_headers: dict,
):
    """
    Test GET /assess with pagination parameters.
    
    Creates multiple assessments and tests skip/limit.
    """
    # Create multiple transcripts and assessments
    for i in range(5):
        transcript = Transcript(
            transcript=f"Test transcript {i}",
            buyer_id=f"buyer_{i}",
        )
        db_session.add(transcript)
        db_session.flush()
        
        assessment = Assessment(
            transcript_id=transcript.id,
            scores={
                "situation": 3,
                "problem": 3,
                "implication": 3,
                "need_payoff": 3,
                "flow": 3,
                "tone": 3,
                "engagement": 3,
            },
            coaching={
                "summary": f"Summary {i}",
                "wins": [],
                "gaps": [],
                "next_actions": [],
            },
            model_name="test-model",
            prompt_version="v1",
            latency_ms=100,
        )
        db_session.add(assessment)
    
    db_session.commit()

    # Test default pagination
    response = test_client.get("/assess", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5

    # Test skip parameter
    response = test_client.get("/assess?skip=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Test limit parameter
    response = test_client.get("/assess?limit=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test skip + limit
    response = test_client.get("/assess?skip=1&limit=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_assessments_filter_by_transcript(
    test_client: TestClient,
    db_session: Session,
    auth_headers: dict,
):
    """
    Test GET /assess with transcript_id filter.
    
    Creates multiple transcripts with assessments and filters by transcript_id.
    """
    # Create transcript 1 with 2 assessments
    transcript1 = Transcript(transcript="Transcript 1", buyer_id="buyer1")
    db_session.add(transcript1)
    db_session.flush()
    
    for i in range(2):
        assessment = Assessment(
            transcript_id=transcript1.id,
            scores={
                "situation": 3,
                "problem": 3,
                "implication": 3,
                "need_payoff": 3,
                "flow": 3,
                "tone": 3,
                "engagement": 3,
            },
            coaching={
                "summary": f"Summary 1-{i}",
                "wins": [],
                "gaps": [],
                "next_actions": [],
            },
            model_name="test-model",
            prompt_version="v1",
            latency_ms=100,
        )
        db_session.add(assessment)
    
    # Create transcript 2 with 1 assessment
    transcript2 = Transcript(transcript="Transcript 2", buyer_id="buyer2")
    db_session.add(transcript2)
    db_session.flush()
    
    assessment = Assessment(
        transcript_id=transcript2.id,
        scores={
            "situation": 4,
            "problem": 4,
            "implication": 4,
            "need_payoff": 4,
            "flow": 4,
            "tone": 4,
            "engagement": 4,
        },
        coaching={
            "summary": "Summary 2",
            "wins": [],
            "gaps": [],
            "next_actions": [],
        },
        model_name="test-model",
        prompt_version="v1",
        latency_ms=100,
    )
    db_session.add(assessment)
    db_session.commit()

    # Filter by transcript1
    response = test_client.get(
        f"/assess?transcript_id={transcript1.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(a["transcript_id"] == transcript1.id for a in data)

    # Filter by transcript2
    response = test_client.get(
        f"/assess?transcript_id={transcript2.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["transcript_id"] == transcript2.id


def test_get_assessments_by_transcript(
    test_client: TestClient,
    db_session: Session,
    auth_headers: dict,
):
    """
    Test GET /assess/by-transcript/{transcript_id} endpoint.
    
    Verifies retrieving all assessments for a specific transcript.
    """
    # Create transcript with multiple assessments
    transcript = Transcript(transcript="Test transcript", buyer_id="buyer1")
    db_session.add(transcript)
    db_session.flush()
    
    assessment_count = 3
    for i in range(assessment_count):
        assessment = Assessment(
            transcript_id=transcript.id,
            scores={
                "situation": i + 1,
                "problem": i + 1,
                "implication": i + 1,
                "need_payoff": i + 1,
                "flow": i + 1,
                "tone": i + 1,
                "engagement": i + 1,
            },
            coaching={
                "summary": f"Summary {i}",
                "wins": [],
                "gaps": [],
                "next_actions": [],
            },
            model_name="test-model",
            prompt_version=f"v{i}",
            latency_ms=100,
        )
        db_session.add(assessment)
    
    db_session.commit()

    # Get assessments by transcript ID
    response = test_client.get(
        f"/assess/by-transcript/{transcript.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == assessment_count
    assert all(a["transcript_id"] == transcript.id for a in data)
    
    # Verify different prompt versions
    versions = [a["prompt_version"] for a in data]
    assert "v0" in versions
    assert "v1" in versions
    assert "v2" in versions


def test_get_assessments_by_transcript_not_found(
    test_client: TestClient,
    auth_headers: dict,
):
    """
    Test GET /assess/by-transcript/{transcript_id} with non-existent transcript.
    
    Should return empty list, not an error.
    """
    response = test_client.get(
        "/assess/by-transcript/99999",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_assessments_unauthorized(test_client: TestClient):
    """Test that GET /assess requires authentication."""
    response = test_client.get("/assess")
    assert response.status_code == 403


def test_get_assessments_by_transcript_unauthorized(test_client: TestClient):
    """Test that GET /assess/by-transcript/{transcript_id} requires authentication."""
    response = test_client.get("/assess/by-transcript/1")
    assert response.status_code == 403
