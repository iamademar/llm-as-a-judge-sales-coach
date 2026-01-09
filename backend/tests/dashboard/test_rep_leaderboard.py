"""
Unit tests for GET /overview/rep-leaderboard endpoint.

Tests cover:
- Basic leaderboard ranking by avg_composite
- Multiple reps with correct rank order
- Conversation count per rep
- Strongest/weakest dimension calculation per rep
- Trend comparison with previous period (include_trend=True)
- Trend calculation when no previous data
- include_trend=False skips trend calculation
- Limit parameter (default 10, max 50)
- Default date range (30 days)
- Custom date range filtering
- 90-day limit enforcement
- Date validation errors
- Organization filtering
- Empty result when no reps have data
- Multiple assessments per transcript (uses most recent)
"""
import pytest
from datetime import datetime, timedelta

from app.models import Representative, Transcript, Assessment


class TestRepLeaderboardBasics:
    """Tests for basic rep leaderboard functionality"""

    def test_rep_leaderboard_basic_ranking(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify reps are ranked by average composite score"""
        # Arrange: Create 3 reps with different scores
        reps_data = [
            ("rep1@test.com", "Alice", 5),  # Best
            ("rep2@test.com", "Bob", 3),    # Worst
            ("rep3@test.com", "Charlie", 4), # Middle
        ]

        for email, name, score in reps_data:
            rep = Representative(
                email=email,
                full_name=name,
                organization_id=sample_organization.id,
                is_active=True
            )
            db_session.add(rep)
            db_session.commit()

            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{name}",
                transcript=f"Conversation by {name}",
                metadata={}
            )
            db_session.add(transcript)
            db_session.commit()

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": score, "problem": score, "implication": score,
                    "need_payoff": score, "flow": score, "tone": score, "engagement": score
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/rep-leaderboard",
            headers=auth_headers
        )

        # Assert: Should be ranked Alice (5), Charlie (4), Bob (3)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 3

        assert data["items"][0]["rank"] == 1
        assert data["items"][0]["rep"] == "Alice"
        assert data["items"][0]["avg_composite"] == 5.0

        assert data["items"][1]["rank"] == 2
        assert data["items"][1]["rep"] == "Charlie"
        assert data["items"][1]["avg_composite"] == 4.0

        assert data["items"][2]["rank"] == 3
        assert data["items"][2]["rep"] == "Bob"
        assert data["items"][2]["avg_composite"] == 3.0

    def test_rep_leaderboard_includes_required_fields(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify each leaderboard item contains all required fields"""
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

        assessment = Assessment(
            transcript_id=transcript.id,
            scores={
                "situation": 5, "problem": 3, "implication": 4,  # tone is strongest (5), problem is weakest (3)
                "need_payoff": 4, "flow": 4, "tone": 5, "engagement": 4
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/rep-leaderboard",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

        item = data["items"][0]
        assert "rank" in item
        assert "rep" in item
        assert "conversation_count" in item
        assert "avg_composite" in item
        assert "strongest" in item
        assert "strongest_score" in item
        assert "weakest" in item
        assert "weakest_score" in item
        assert "trend" in item

        assert item["rep"] == "Test Rep"
        assert item["conversation_count"] == 1
        assert item["strongest"] == "Situation" or item["strongest"] == "Tone"  # Both have score 5
        assert item["weakest"] == "Problem"

    def test_rep_leaderboard_conversation_count(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify conversation_count reflects number of assessed transcripts"""
        # Arrange: Create rep with 3 conversations
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
                transcript=f"Conversation {i}",
                metadata={}
            )
            db_session.add(transcript)
            db_session.commit()

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": 4, "problem": 4, "implication": 4,
                    "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/rep-leaderboard",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["conversation_count"] == 3

    def test_rep_leaderboard_strongest_weakest_dimensions(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify strongest and weakest dimensions are correctly identified"""
        # Arrange
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        # Create 2 transcripts to average dimensions
        # Average: situation=5, problem=1, others=3
        scores_list = [
            {"situation": 5, "problem": 1, "implication": 3, "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3},
            {"situation": 5, "problem": 1, "implication": 3, "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3},
        ]

        for i, scores in enumerate(scores_list):
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
                scores=scores,
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/rep-leaderboard",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

        item = data["items"][0]
        assert item["strongest"] == "Situation"
        assert item["strongest_score"] == 5.0
        assert item["weakest"] == "Problem"
        assert item["weakest_score"] == 1.0


class TestRepLeaderboardTrend:
    """Tests for trend comparison with previous period"""

    def test_rep_leaderboard_trend_with_previous_data(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify trend calculation compares with previous period"""
        # Arrange: Create rep with data in both current and previous periods
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        now = datetime.utcnow()
        
        # Previous period: 31-60 days ago, score = 3.0
        prev_transcript = Transcript(
            representative_id=rep.id,
            buyer_id="PREV-BUYER",
            transcript="Previous conversation",
            metadata={},
            created_at=now - timedelta(days=45)
        )
        db_session.add(prev_transcript)
        db_session.commit()

        prev_assessment = Assessment(
            transcript_id=prev_transcript.id,
            scores={
                "situation": 3, "problem": 3, "implication": 3,
                "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(prev_assessment)

        # Current period: last 30 days, score = 4.0
        current_transcript = Transcript(
            representative_id=rep.id,
            buyer_id="CURRENT-BUYER",
            transcript="Current conversation",
            metadata={},
            created_at=now - timedelta(days=10)
        )
        db_session.add(current_transcript)
        db_session.commit()

        current_assessment = Assessment(
            transcript_id=current_transcript.id,
            scores={
                "situation": 4, "problem": 4, "implication": 4,
                "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(current_assessment)
        db_session.commit()

        # Act: Request with default 30-day range
        response = test_client.get(
            "/overview/rep-leaderboard?include_trend=true",
            headers=auth_headers
        )

        # Assert: Trend should be +1.0 (4.0 - 3.0)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["trend"] == 1.0

    def test_rep_leaderboard_trend_without_previous_data(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify trend is 0.0 when no previous period data exists"""
        # Arrange: Create rep with only current period data
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
            transcript="Current conversation",
            metadata={}
        )
        db_session.add(transcript)
        db_session.commit()

        assessment = Assessment(
            transcript_id=transcript.id,
            scores={
                "situation": 4, "problem": 4, "implication": 4,
                "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/rep-leaderboard?include_trend=true",
            headers=auth_headers
        )

        # Assert: Trend should be 0.0 (no previous data to compare)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["trend"] == 0.0

    def test_rep_leaderboard_include_trend_false(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify include_trend=false skips trend calculation"""
        # Arrange: Create rep with data
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

        assessment = Assessment(
            transcript_id=transcript.id,
            scores={
                "situation": 4, "problem": 4, "implication": 4,
                "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/rep-leaderboard?include_trend=false",
            headers=auth_headers
        )

        # Assert: Trend should be 0.0 (not calculated)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["trend"] == 0.0


class TestRepLeaderboardLimitAndPagination:
    """Tests for limit parameter and pagination"""

    def test_rep_leaderboard_limit_parameter(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify limit parameter restricts number of reps returned"""
        # Arrange: Create 15 reps
        for i in range(15):
            rep = Representative(
                email=f"rep{i}@test.com",
                full_name=f"Rep {i}",
                organization_id=sample_organization.id,
                is_active=True
            )
            db_session.add(rep)
            db_session.commit()

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
                    "situation": 4, "problem": 4, "implication": 4,
                    "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act: Request with limit=5
        response = test_client.get(
            "/overview/rep-leaderboard?limit=5",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5

    def test_rep_leaderboard_default_limit(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify default limit is 10"""
        # Arrange: Create 20 reps
        for i in range(20):
            rep = Representative(
                email=f"rep{i}@test.com",
                full_name=f"Rep {i}",
                organization_id=sample_organization.id,
                is_active=True
            )
            db_session.add(rep)
            db_session.commit()

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
                    "situation": 4, "problem": 4, "implication": 4,
                    "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1"
            )
            db_session.add(assessment)

        db_session.commit()

        # Act: No limit specified
        response = test_client.get(
            "/overview/rep-leaderboard",
            headers=auth_headers
        )

        # Assert: Should return 10 items (default limit)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10


class TestRepLeaderboardFiltering:
    """Tests for date range and organization filtering"""

    def test_rep_leaderboard_organization_filtering(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify leaderboard only shows reps from user's organization"""
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
                "situation": 5, "problem": 5, "implication": 5,
                "need_payoff": 5, "flow": 5, "tone": 5, "engagement": 5
            },
            coaching={"summary": "Excellent", "wins": [], "gaps": [], "next_actions": []},
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
                "situation": 4, "problem": 4, "implication": 4,
                "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
            },
            coaching={"summary": "Good", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(my_assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/rep-leaderboard",
            headers=auth_headers
        )

        # Assert: Should only see my org's rep
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["rep"] == "My Rep"

    def test_rep_leaderboard_custom_date_range(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify custom date_from and date_to parameters work"""
        # Arrange: Create rep with transcripts at different times
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        now = datetime.utcnow()

        # Old conversation (60 days ago)
        old_transcript = Transcript(
            representative_id=rep.id,
            buyer_id="OLD-BUYER",
            transcript="Old conversation",
            metadata={},
            created_at=now - timedelta(days=60)
        )
        db_session.add(old_transcript)
        db_session.commit()

        old_assessment = Assessment(
            transcript_id=old_transcript.id,
            scores={
                "situation": 2, "problem": 2, "implication": 2,
                "need_payoff": 2, "flow": 2, "tone": 2, "engagement": 2
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(old_assessment)

        # Recent conversation (10 days ago)
        recent_transcript = Transcript(
            representative_id=rep.id,
            buyer_id="RECENT-BUYER",
            transcript="Recent conversation",
            metadata={},
            created_at=now - timedelta(days=10)
        )
        db_session.add(recent_transcript)
        db_session.commit()

        recent_assessment = Assessment(
            transcript_id=recent_transcript.id,
            scores={
                "situation": 4, "problem": 4, "implication": 4,
                "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(recent_assessment)
        db_session.commit()

        # Act: Filter to last 30 days
        date_from = (now - timedelta(days=30)).isoformat() + "Z"
        date_to = now.isoformat() + "Z"

        response = test_client.get(
            f"/overview/rep-leaderboard?date_from={date_from}&date_to={date_to}",
            headers=auth_headers
        )

        # Assert: Should only see recent conversation (avg = 4.0, count = 1)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["avg_composite"] == 4.0
        assert data["items"][0]["conversation_count"] == 1

    def test_rep_leaderboard_90_day_limit_enforced(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify 90-day maximum range limit is enforced"""
        # Act: Request 92-day range (should fail)
        response = test_client.get(
            "/overview/rep-leaderboard?date_from=2025-08-01T00:00:00Z&date_to=2025-11-01T00:00:00Z",
            headers=auth_headers
        )

        # Assert: 400 Bad Request
        assert response.status_code == 400
        data = response.json()
        assert "90 days" in data["error"]["message"].lower()

    def test_rep_leaderboard_date_validation(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify error when date_from is after date_to"""
        # Act
        response = test_client.get(
            "/overview/rep-leaderboard?date_from=2025-12-01T00:00:00Z&date_to=2025-11-01T00:00:00Z",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "date_from" in data["error"]["message"].lower() or "before" in data["error"]["message"].lower()

    def test_rep_leaderboard_empty_result(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify empty result when no reps have data"""
        # Act: No data in database
        response = test_client.get(
            "/overview/rep-leaderboard",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestRepLeaderboardMultipleAssessments:
    """Tests for handling multiple assessments per transcript"""

    def test_rep_leaderboard_uses_most_recent_assessment(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify only most recent assessment per transcript is used"""
        # Arrange: Create rep with transcript having 2 assessments
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

        # Old assessment: score = 2.0
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

        # New assessment: score = 5.0 (should be used)
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
            "/overview/rep-leaderboard",
            headers=auth_headers
        )

        # Assert: Should use most recent assessment (5.0, not 2.0)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["avg_composite"] == 5.0
        assert data["items"][0]["conversation_count"] == 1  # Only one transcript
