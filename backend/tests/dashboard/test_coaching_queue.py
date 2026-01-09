"""
Unit tests for GET /overview/coaching-queue endpoint.

Tests cover:
- Basic queue retrieval with items below threshold
- Empty queue when all scores above threshold
- Limit parameter (default 10, max 50)
- Sorting by assessment created_at (newest first)
- Organization filtering (only current user's org)
- Date range filtering (date_from, date_to)
- Threshold parameter behavior
- Multiple assessments per transcript (uses most recent)
- Weakest dimension calculation
- total_count vs items length with limit
- Date validation (date_from > date_to)
"""
import pytest
from datetime import datetime, timedelta

from app.models import Representative, Transcript, Assessment


class TestCoachingQueueBasics:
    """Tests for basic coaching queue functionality"""

    def test_coaching_queue_returns_items_below_threshold(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify queue returns conversations with composite score below threshold"""
        # Arrange: Create rep with 2 transcripts - one below, one above threshold
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        # Transcript 1: Composite = 2.0 (below default threshold 3.5)
        t1 = Transcript(
            representative_id=rep.id,
            buyer_id="BUYER-001",
            transcript="Poor conversation",
            metadata={}
        )
        db_session.add(t1)
        db_session.commit()

        a1 = Assessment(
            transcript_id=t1.id,
            scores={
                "situation": 2, "problem": 2, "implication": 2,
                "need_payoff": 2, "flow": 2, "tone": 2, "engagement": 2
            },
            coaching={"summary": "Needs improvement", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(a1)

        # Transcript 2: Composite = 4.0 (above threshold, should NOT appear)
        t2 = Transcript(
            representative_id=rep.id,
            buyer_id="BUYER-002",
            transcript="Good conversation",
            metadata={}
        )
        db_session.add(t2)
        db_session.commit()

        a2 = Assessment(
            transcript_id=t2.id,
            scores={
                "situation": 4, "problem": 4, "implication": 4,
                "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
            },
            coaching={"summary": "Good job", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(a2)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/coaching-queue",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_count" in data
        assert len(data["items"]) == 1
        assert data["total_count"] == 1
        assert data["items"][0]["buyer"] == "BUYER-001"
        assert data["items"][0]["composite"] == 2.0

    def test_coaching_queue_empty_when_all_above_threshold(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify empty queue when all conversations are above threshold"""
        # Arrange: Create conversations with high scores
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        for i in range(3):
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i:03d}",
                transcript=f"Excellent conversation {i}",
                metadata={}
            )
            db_session.add(transcript)
            db_session.commit()

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": 5, "problem": 5, "implication": 5,
                    "need_payoff": 5, "flow": 5, "tone": 5, "engagement": 5
                },
                coaching={"summary": "Excellent", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/coaching-queue?threshold=3.5",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_count"] == 0

    def test_coaching_queue_includes_required_fields(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify each queue item contains all required fields"""
        # Arrange
        rep = Representative(
            email="rep@test.com",
            full_name="John Doe",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        transcript = Transcript(
            representative_id=rep.id,
            buyer_id="BUYER-TEST",
            transcript="Test conversation",
            metadata={}
        )
        db_session.add(transcript)
        db_session.commit()

        assessment = Assessment(
            transcript_id=transcript.id,
            scores={
                "situation": 2, "problem": 3, "implication": 1,  # implication is weakest
                "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3
            },
            coaching={"summary": "Needs work", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/coaching-queue",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        
        item = data["items"][0]
        assert "id" in item
        assert "rep" in item
        assert "buyer" in item
        assert "composite" in item
        assert "weakest_dim" in item
        assert "created_at" in item
        
        assert item["rep"] == "John Doe"
        assert item["buyer"] == "BUYER-TEST"
        assert item["weakest_dim"] == "Implication"  # Title-cased


class TestCoachingQueueSortingAndLimit:
    """Tests for sorting and pagination in coaching queue"""

    def test_coaching_queue_sorted_by_newest_first(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify queue items are sorted by assessment created_at desc"""
        # Arrange: Create 3 transcripts with different assessment times
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        # Create transcripts with different assessment timestamps
        for i, hours_ago in enumerate([10, 5, 15]):  # 5 hours ago should be first
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i:03d}",
                transcript=f"Conversation {i}",
                metadata={}
            )
            db_session.add(transcript)
            db_session.commit()

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": 2, "problem": 2, "implication": 2,
                    "need_payoff": 2, "flow": 2, "tone": 2, "engagement": 2
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1",
                created_at=datetime.utcnow() - timedelta(hours=hours_ago)
            )
            db_session.add(assessment)

        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/coaching-queue",
            headers=auth_headers
        )

        # Assert: Should be ordered by recency (5, 10, 15 hours ago)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        
        # Most recent first (5 hours ago = index 1)
        assert data["items"][0]["buyer"] == "BUYER-001"
        assert data["items"][1]["buyer"] == "BUYER-000"
        assert data["items"][2]["buyer"] == "BUYER-002"

    def test_coaching_queue_limit_parameter(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify limit parameter restricts number of items returned"""
        # Arrange: Create 15 transcripts below threshold
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        for i in range(15):
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i:03d}",
                transcript=f"Conversation {i}",
                metadata={}
            )
            db_session.add(transcript)
            db_session.commit()

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": 2, "problem": 2, "implication": 2,
                    "need_payoff": 2, "flow": 2, "tone": 2, "engagement": 2
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act: Request with limit=5
        response = test_client.get(
            "/overview/coaching-queue?limit=5",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total_count"] == 15  # Total should still be 15

    def test_coaching_queue_default_limit(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify default limit is 10"""
        # Arrange: Create 20 transcripts below threshold
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        for i in range(20):
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i:03d}",
                transcript=f"Conversation {i}",
                metadata={}
            )
            db_session.add(transcript)
            db_session.commit()

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": 2, "problem": 2, "implication": 2,
                    "need_payoff": 2, "flow": 2, "tone": 2, "engagement": 2
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act: No limit specified
        response = test_client.get(
            "/overview/coaching-queue",
            headers=auth_headers
        )

        # Assert: Should return 10 items (default limit)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total_count"] == 20


class TestCoachingQueueFiltering:
    """Tests for date range and threshold filtering"""

    def test_coaching_queue_organization_filtering(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify queue only shows conversations from user's organization"""
        # Arrange: Create another organization
        from app.models.organization import Organization
        
        other_org = Organization(name="Other Org")
        db_session.add(other_org)
        db_session.commit()

        # Create rep in other org
        other_rep = Representative(
            email="other@test.com",
            full_name="Other Rep",
            organization_id=other_org.id,
            is_active=True
        )
        db_session.add(other_rep)
        db_session.commit()

        # Create transcript for other org
        other_transcript = Transcript(
            representative_id=other_rep.id,
            buyer_id="OTHER-BUYER",
            transcript="Other org conversation",
            metadata={}
        )
        db_session.add(other_transcript)
        db_session.commit()

        other_assessment = Assessment(
            transcript_id=other_transcript.id,
            scores={
                "situation": 1, "problem": 1, "implication": 1,
                "need_payoff": 1, "flow": 1, "tone": 1, "engagement": 1
            },
            coaching={"summary": "Bad", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(other_assessment)

        # Create rep in current user's org
        my_rep = Representative(
            email="my@test.com",
            full_name="My Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(my_rep)
        db_session.commit()

        my_transcript = Transcript(
            representative_id=my_rep.id,
            buyer_id="MY-BUYER",
            transcript="My org conversation",
            metadata={}
        )
        db_session.add(my_transcript)
        db_session.commit()

        my_assessment = Assessment(
            transcript_id=my_transcript.id,
            scores={
                "situation": 2, "problem": 2, "implication": 2,
                "need_payoff": 2, "flow": 2, "tone": 2, "engagement": 2
            },
            coaching={"summary": "Needs work", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(my_assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/coaching-queue",
            headers=auth_headers
        )

        # Assert: Should only see my org's data
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["buyer"] == "MY-BUYER"

    def test_coaching_queue_threshold_parameter(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify threshold parameter affects which items appear in queue"""
        # Arrange: Create transcripts with composite scores: 2.0, 3.0, 4.0
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        for i, score_val in enumerate([2, 3, 4]):
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{score_val}",
                transcript=f"Conversation {i}",
                metadata={}
            )
            db_session.add(transcript)
            db_session.commit()

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": score_val, "problem": score_val, "implication": score_val,
                    "need_payoff": score_val, "flow": score_val, "tone": score_val, "engagement": score_val
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act: With threshold=3.5, should include 2.0 and 3.0 (not 4.0)
        response = test_client.get(
            "/overview/coaching-queue?threshold=3.5",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        buyers = [item["buyer"] for item in data["items"]]
        assert "BUYER-2" in buyers
        assert "BUYER-3" in buyers
        assert "BUYER-4" not in buyers

    def test_coaching_queue_date_filtering(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify date_from and date_to parameters filter correctly"""
        # Arrange: Create transcripts with different dates
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        now = datetime.utcnow()
        dates = [
            now - timedelta(days=40),  # Old (outside 30-day window)
            now - timedelta(days=10),  # Recent (inside window)
            now - timedelta(days=5),   # Recent (inside window)
        ]

        for i, date in enumerate(dates):
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i}",
                transcript=f"Conversation {i}",
                metadata={},
                created_at=date
            )
            db_session.add(transcript)
            db_session.commit()

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": 2, "problem": 2, "implication": 2,
                    "need_payoff": 2, "flow": 2, "tone": 2, "engagement": 2
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act: Filter to last 30 days
        date_from = (now - timedelta(days=30)).isoformat() + "Z"
        date_to = now.isoformat() + "Z"

        response = test_client.get(
            f"/overview/coaching-queue?date_from={date_from}&date_to={date_to}",
            headers=auth_headers
        )

        # Assert: Should only include recent conversations (indices 1 and 2)
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        buyers = [item["buyer"] for item in data["items"]]
        assert "BUYER-1" in buyers
        assert "BUYER-2" in buyers
        assert "BUYER-0" not in buyers

    def test_coaching_queue_date_validation(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify error when date_from is after date_to"""
        # Act
        response = test_client.get(
            "/overview/coaching-queue?date_from=2025-12-01T00:00:00Z&date_to=2025-11-01T00:00:00Z",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "date_from" in data["error"]["message"].lower() or "before" in data["error"]["message"].lower()


class TestCoachingQueueMultipleAssessments:
    """Tests for handling multiple assessments per transcript"""

    def test_coaching_queue_uses_most_recent_assessment(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify only most recent assessment per transcript is used"""
        # Arrange: Create transcript with 2 assessments
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        transcript = Transcript(
            representative_id=rep.id,
            buyer_id="BUYER-001",
            transcript="Test conversation",
            metadata={}
        )
        db_session.add(transcript)
        db_session.commit()

        # Old assessment: Below threshold
        old_assessment = Assessment(
            transcript_id=transcript.id,
            scores={
                "situation": 2, "problem": 2, "implication": 2,
                "need_payoff": 2, "flow": 2, "tone": 2, "engagement": 2
            },
            coaching={"summary": "Old", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        db_session.add(old_assessment)
        db_session.commit()

        # New assessment: Above threshold (should remove from queue)
        new_assessment = Assessment(
            transcript_id=transcript.id,
            scores={
                "situation": 5, "problem": 5, "implication": 5,
                "need_payoff": 5, "flow": 5, "tone": 5, "engagement": 5
            },
            coaching={"summary": "New", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1",
            created_at=datetime.utcnow()
        )
        db_session.add(new_assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/coaching-queue",
            headers=auth_headers
        )

        # Assert: Should NOT appear in queue (most recent is above threshold)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total_count"] == 0

    def test_coaching_queue_weakest_dimension_calculation(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify weakest dimension is correctly identified and formatted"""
        # Arrange
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        transcript = Transcript(
            representative_id=rep.id,
            buyer_id="BUYER-001",
            transcript="Test conversation",
            metadata={}
        )
        db_session.add(transcript)
        db_session.commit()

        # Create assessment where "need_payoff" is weakest
        assessment = Assessment(
            transcript_id=transcript.id,
            scores={
                "situation": 3, "problem": 3, "implication": 3,
                "need_payoff": 1,  # Weakest
                "flow": 3, "tone": 3, "engagement": 3
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/coaching-queue",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["weakest_dim"] == "Need Payoff"  # Title-cased with space
