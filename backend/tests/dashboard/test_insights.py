"""
Unit tests for GET /overview/insights endpoint.

Tests cover:
- Empty data returns "No conversations yet" insight
- Score trend insight with delta calculation
- Above-target rate insight with percentage
- Weakest dimension insight
- Coaching backlog insight with count
- Previous period comparison deltas
- Date range filtering
- Threshold parameter affects backlog count
- Organization filtering
- Multiple assessments per transcript handling
"""
import pytest
from datetime import datetime, timedelta

from app.models import Representative, Transcript, Assessment


class TestInsightsBasics:
    """Tests for basic insights functionality"""

    def test_insights_empty_data_returns_default_message(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify empty data returns 'No conversations yet' insight"""
        # Act: No data in database
        response = test_client.get(
            "/overview/insights",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert len(data["insights"]) == 1
        assert data["insights"][0]["title"] == "No conversations yet"
        assert "add transcripts" in data["insights"][0]["detail"].lower()

    def test_insights_returns_all_four_insights(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify response includes score trend, above-target rate, weakest dimension, and backlog"""
        # Arrange: Create data
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
                "situation": 4, "problem": 3, "implication": 2,  # implication is weakest
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
            "/overview/insights",
            headers=auth_headers
        )

        # Assert: Should have 4 insights
        assert response.status_code == 200
        data = response.json()
        assert len(data["insights"]) == 4

        # Check insight titles
        titles = [insight["title"] for insight in data["insights"]]
        assert "Score trend" in titles
        assert "Above-target rate" in titles
        assert "Weakest dimension" in titles
        assert "Coaching backlog" in titles

    def test_insights_structure(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify each insight has title and detail fields"""
        # Arrange: Create data
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
            "/overview/insights",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        
        for insight in data["insights"]:
            assert "title" in insight
            assert "detail" in insight
            assert isinstance(insight["title"], str)
            assert isinstance(insight["detail"], str)
            assert len(insight["title"]) > 0
            assert len(insight["detail"]) > 0


class TestScoreTrendInsight:
    """Tests for score trend insight"""

    def test_insights_score_trend_includes_average(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify score trend insight shows average composite score"""
        # Arrange: Create data with known score
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

        # Composite score will be 4.0
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
            "/overview/insights",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        
        score_insight = next(i for i in data["insights"] if i["title"] == "Score trend")
        assert "4.00" in score_insight["detail"] or "4.0" in score_insight["detail"]

    def test_insights_score_trend_with_delta(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify score trend includes comparison to previous period"""
        # Arrange: Create data in both current and previous periods
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

        # Act
        response = test_client.get(
            "/overview/insights",
            headers=auth_headers
        )

        # Assert: Should show improvement (+1.0)
        assert response.status_code == 200
        data = response.json()
        
        score_insight = next(i for i in data["insights"] if i["title"] == "Score trend")
        assert "+1.0" in score_insight["detail"]
        assert "prior period" in score_insight["detail"].lower()


class TestAboveTargetRateInsight:
    """Tests for above-target rate insight"""

    def test_insights_above_target_rate_shows_percentage(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify above-target rate insight shows percentage"""
        # Arrange: Create 4 conversations, 2 above threshold
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        for i, score in enumerate([5, 4, 3, 2]):  # 5 and 4 are above 3.5
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i}",
                transcript=f"Conversation {i}",
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
            "/overview/insights?threshold=3.5",
            headers=auth_headers
        )

        # Assert: 2 out of 4 = 50%
        assert response.status_code == 200
        data = response.json()
        
        rate_insight = next(i for i in data["insights"] if i["title"] == "Above-target rate")
        assert "50" in rate_insight["detail"]
        assert "%" in rate_insight["detail"]

    def test_insights_above_target_rate_respects_threshold(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify above-target rate changes with threshold parameter"""
        # Arrange: Create conversations with scores 2, 3, 4, 5
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        for i, score in enumerate([2, 3, 4, 5]):
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i}",
                transcript=f"Conversation {i}",
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

        # Act: With threshold=4.5, only 5 is above
        response = test_client.get(
            "/overview/insights?threshold=4.5",
            headers=auth_headers
        )

        # Assert: 1 out of 4 = 25%
        assert response.status_code == 200
        data = response.json()
        
        rate_insight = next(i for i in data["insights"] if i["title"] == "Above-target rate")
        assert "25" in rate_insight["detail"]


class TestWeakestDimensionInsight:
    """Tests for weakest dimension insight"""

    def test_insights_weakest_dimension_identified(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify weakest dimension is correctly identified"""
        # Arrange: Create data where implication is weakest
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
                "situation": 4, "problem": 4, "implication": 2,  # Weakest
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
            "/overview/insights",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        
        weakest_insight = next(i for i in data["insights"] if i["title"] == "Weakest dimension")
        assert "Implication" in weakest_insight["detail"]
        assert "2." in weakest_insight["detail"]  # Score should be shown

    def test_insights_weakest_dimension_coaching_recommendation(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify weakest dimension insight includes coaching recommendation"""
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
                "situation": 4, "problem": 4, "implication": 2,
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
            "/overview/insights",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        
        weakest_insight = next(i for i in data["insights"] if i["title"] == "Weakest dimension")
        assert "coaching" in weakest_insight["detail"].lower() or "prioritize" in weakest_insight["detail"].lower()


class TestCoachingBacklogInsight:
    """Tests for coaching backlog insight"""

    def test_insights_coaching_backlog_count(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify coaching backlog shows count of conversations below threshold"""
        # Arrange: Create 3 conversations, 2 below threshold
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        for i, score in enumerate([2, 3, 5]):  # 2 and 3 are below 3.5
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i}",
                transcript=f"Conversation {i}",
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
            "/overview/insights?threshold=3.5",
            headers=auth_headers
        )

        # Assert: 2 conversations below threshold
        assert response.status_code == 200
        data = response.json()
        
        backlog_insight = next(i for i in data["insights"] if i["title"] == "Coaching backlog")
        assert "2 conversation" in backlog_insight["detail"]
        assert "3.5" in backlog_insight["detail"]

    def test_insights_coaching_backlog_respects_threshold(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify coaching backlog count changes with threshold parameter"""
        # Arrange: Create conversations with scores 2, 3, 4, 5
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        for i, score in enumerate([2, 3, 4, 5]):
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i}",
                transcript=f"Conversation {i}",
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

        # Act: With threshold=4.5, 3 are below (2, 3, 4)
        response = test_client.get(
            "/overview/insights?threshold=4.5",
            headers=auth_headers
        )

        # Assert: 3 conversations below threshold
        assert response.status_code == 200
        data = response.json()
        
        backlog_insight = next(i for i in data["insights"] if i["title"] == "Coaching backlog")
        assert "3 conversation" in backlog_insight["detail"]

    def test_insights_coaching_backlog_singular_vs_plural(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify coaching backlog uses singular 'conversation' when count is 1"""
        # Arrange: Create 1 conversation below threshold
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
                "situation": 2, "problem": 2, "implication": 2,
                "need_payoff": 2, "flow": 2, "tone": 2, "engagement": 2
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/insights",
            headers=auth_headers
        )

        # Assert: Should use singular form
        assert response.status_code == 200
        data = response.json()
        
        backlog_insight = next(i for i in data["insights"] if i["title"] == "Coaching backlog")
        # Should say "1 conversation" not "1 conversations"
        assert "1 conversation" in backlog_insight["detail"]
        assert "1 conversations" not in backlog_insight["detail"]


class TestInsightsFiltering:
    """Tests for date range and organization filtering"""

    def test_insights_organization_filtering(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify insights only include data from user's organization"""
        # Arrange: Create another organization
        from app.models.organization import Organization
        
        other_org = Organization(name="Other Org")
        db_session.add(other_org)
        db_session.commit()

        # Create rep in other org with low scores
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
                "situation": 1, "problem": 1, "implication": 1,
                "need_payoff": 1, "flow": 1, "tone": 1, "engagement": 1
            },
            coaching={"summary": "Bad", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(other_assessment)

        # Create rep in current user's org with high scores
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
                "situation": 5, "problem": 5, "implication": 5,
                "need_payoff": 5, "flow": 5, "tone": 5, "engagement": 5
            },
            coaching={"summary": "Excellent", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="v1"
        )
        db_session.add(my_assessment)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/insights",
            headers=auth_headers
        )

        # Assert: Should show high score (5.0), not low score (1.0)
        assert response.status_code == 200
        data = response.json()
        
        score_insight = next(i for i in data["insights"] if i["title"] == "Score trend")
        assert "5." in score_insight["detail"]
        assert "1." not in score_insight["detail"]

    def test_insights_date_filtering(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify date_from and date_to parameters filter correctly"""
        # Arrange: Create conversations at different times
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        now = datetime.utcnow()

        # Old conversation (60 days ago) with low score
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

        # Recent conversation (10 days ago) with high score
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
                "situation": 5, "problem": 5, "implication": 5,
                "need_payoff": 5, "flow": 5, "tone": 5, "engagement": 5
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
            f"/overview/insights?date_from={date_from}&date_to={date_to}",
            headers=auth_headers
        )

        # Assert: Should show recent score (5.0), not old score (2.0)
        assert response.status_code == 200
        data = response.json()
        
        score_insight = next(i for i in data["insights"] if i["title"] == "Score trend")
        assert "5." in score_insight["detail"]

    def test_insights_date_validation(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify error when date_from is after date_to"""
        # Act
        response = test_client.get(
            "/overview/insights?date_from=2025-12-01T00:00:00Z&date_to=2025-11-01T00:00:00Z",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "date_from" in data["error"]["message"].lower() or "before" in data["error"]["message"].lower()


class TestInsightsMultipleAssessments:
    """Tests for handling multiple assessments per transcript"""

    def test_insights_uses_most_recent_assessment(
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
            "/overview/insights",
            headers=auth_headers
        )

        # Assert: Should use most recent assessment (5.0, not 2.0)
        assert response.status_code == 200
        data = response.json()
        
        score_insight = next(i for i in data["insights"] if i["title"] == "Score trend")
        assert "5." in score_insight["detail"]
        assert "2." not in score_insight["detail"]
