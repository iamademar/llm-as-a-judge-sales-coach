"""
Unit tests for Pydantic schemas.

Tests cover:
- Score validation (bounds, type checking)
- Default values for coaching lists
- Required fields
- Round-trip serialization/deserialization
"""

import pytest
from pydantic import ValidationError

from app.schemas import (
    AssessmentScores,
    Coaching,
    AssessRequest,
    AssessResponse,
)


class TestAssessmentScores:
    """Tests for AssessmentScores model"""

    def test_valid_scores_all_ones(self):
        """Valid scores at lower bound (all 1s)"""
        scores = AssessmentScores(
            situation=1,
            problem=1,
            implication=1,
            need_payoff=1,
            flow=1,
            tone=1,
            engagement=1,
        )
        assert scores.situation == 1
        assert scores.problem == 1
        assert scores.implication == 1
        assert scores.need_payoff == 1
        assert scores.flow == 1
        assert scores.tone == 1
        assert scores.engagement == 1

    def test_valid_scores_all_fives(self):
        """Valid scores at upper bound (all 5s)"""
        scores = AssessmentScores(
            situation=5,
            problem=5,
            implication=5,
            need_payoff=5,
            flow=5,
            tone=5,
            engagement=5,
        )
        assert scores.situation == 5
        assert scores.problem == 5
        assert scores.implication == 5
        assert scores.need_payoff == 5
        assert scores.flow == 5
        assert scores.tone == 5
        assert scores.engagement == 5

    def test_valid_scores_mixed_range(self):
        """Valid scores with mixed values in range"""
        scores = AssessmentScores(
            situation=2,
            problem=3,
            implication=4,
            need_payoff=5,
            flow=1,
            tone=3,
            engagement=4,
        )
        assert scores.situation == 2
        assert scores.problem == 3
        assert scores.implication == 4
        assert scores.need_payoff == 5
        assert scores.flow == 1
        assert scores.tone == 3
        assert scores.engagement == 4

    def test_invalid_score_below_lower_bound(self):
        """Score below 1 should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            AssessmentScores(
                situation=0,  # Invalid: below lower bound
                problem=3,
                implication=3,
                need_payoff=3,
                flow=3,
                tone=3,
                engagement=3,
            )
        error = exc_info.value
        assert "situation" in str(error)
        assert "must be between 1 and 5" in str(error)

    def test_invalid_score_above_upper_bound(self):
        """Score above 5 should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            AssessmentScores(
                situation=3,
                problem=6,  # Invalid: above upper bound
                implication=3,
                need_payoff=3,
                flow=3,
                tone=3,
                engagement=3,
            )
        error = exc_info.value
        assert "problem" in str(error)
        assert "must be between 1 and 5" in str(error)

    def test_invalid_score_negative(self):
        """Negative score should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            AssessmentScores(
                situation=3,
                problem=3,
                implication=-1,  # Invalid: negative
                need_payoff=3,
                flow=3,
                tone=3,
                engagement=3,
            )
        error = exc_info.value
        assert "implication" in str(error)
        assert "must be between 1 and 5" in str(error)

    def test_invalid_score_string_type(self):
        """String instead of int should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            AssessmentScores(
                situation=3,
                problem=3,
                implication=3,
                need_payoff="3",  # Invalid: string instead of int
                flow=3,
                tone=3,
                engagement=3,
            )
        error = exc_info.value
        assert "need_payoff" in str(error)
        assert "must be an integer" in str(error)

    def test_invalid_score_float_type(self):
        """Float instead of int should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            AssessmentScores(
                situation=3,
                problem=3,
                implication=3,
                need_payoff=3,
                flow=3.5,  # Invalid: float instead of int
                tone=3,
                engagement=3,
            )
        error = exc_info.value
        assert "flow" in str(error)
        assert "must be an integer" in str(error)

    def test_missing_required_field(self):
        """Missing required field should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            AssessmentScores(
                situation=3,
                problem=3,
                implication=3,
                need_payoff=3,
                flow=3,
                tone=3,
                # engagement is missing
            )
        error = exc_info.value
        assert "engagement" in str(error)
        assert "Field required" in str(error)


class TestCoaching:
    """Tests for Coaching model"""

    def test_coaching_with_all_fields(self):
        """Coaching with all fields populated"""
        coaching = Coaching(
            summary="Great job overall!",
            wins=["Good rapport", "Clear questions"],
            gaps=["Need more implication questions"],
            next_actions=["Practice SPIN framework", "Review call recordings"],
        )
        assert coaching.summary == "Great job overall!"
        assert coaching.wins == ["Good rapport", "Clear questions"]
        assert coaching.gaps == ["Need more implication questions"]
        assert coaching.next_actions == ["Practice SPIN framework", "Review call recordings"]

    def test_coaching_defaults_empty_lists(self):
        """Coaching with only summary should default lists to []"""
        coaching = Coaching(summary="Needs improvement")
        assert coaching.summary == "Needs improvement"
        assert coaching.wins == []
        assert coaching.gaps == []
        assert coaching.next_actions == []

    def test_coaching_partial_lists(self):
        """Coaching with some lists populated, others defaulting"""
        coaching = Coaching(
            summary="Mixed performance",
            wins=["Good opener"],
            # gaps and next_actions not provided
        )
        assert coaching.summary == "Mixed performance"
        assert coaching.wins == ["Good opener"]
        assert coaching.gaps == []
        assert coaching.next_actions == []

    def test_coaching_empty_summary_invalid(self):
        """Empty summary string should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Coaching(summary="")
        error = exc_info.value
        assert "summary" in str(error)

    def test_coaching_missing_summary_invalid(self):
        """Missing summary field should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Coaching(
                wins=["Good job"],
                gaps=["Need work"],
            )
        error = exc_info.value
        assert "summary" in str(error)
        assert "Field required" in str(error)


class TestAssessRequest:
    """Tests for AssessRequest model"""

    def test_assess_request_with_transcript_only(self):
        """AssessRequest with only transcript (metadata defaults to {})"""
        request = AssessRequest(transcript="Sales Rep: Hello customer...")
        assert request.transcript == "Sales Rep: Hello customer..."
        assert request.metadata == {}

    def test_assess_request_with_metadata(self):
        """AssessRequest with transcript and metadata"""
        request = AssessRequest(
            transcript="Sales Rep: Hello customer...",
            metadata={
                "rep_id": "12345",
                "call_date": "2025-01-15",
                "customer_name": "Acme Corp",
            },
        )
        assert request.transcript == "Sales Rep: Hello customer..."
        assert request.metadata == {
            "rep_id": "12345",
            "call_date": "2025-01-15",
            "customer_name": "Acme Corp",
        }

    def test_assess_request_empty_transcript_invalid(self):
        """Empty transcript should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            AssessRequest(transcript="")
        error = exc_info.value
        assert "transcript" in str(error)

    def test_assess_request_missing_transcript_invalid(self):
        """Missing transcript field should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            AssessRequest(metadata={"rep_id": "123"})
        error = exc_info.value
        assert "transcript" in str(error)
        assert "Field required" in str(error)


class TestAssessResponse:
    """Tests for AssessResponse model"""

    def test_assess_response_complete(self):
        """AssessResponse with all nested models"""
        scores = AssessmentScores(
            situation=4,
            problem=3,
            implication=2,
            need_payoff=5,
            flow=4,
            tone=5,
            engagement=3,
        )
        coaching = Coaching(
            summary="Good start, needs practice",
            wins=["Clear voice"],
            gaps=["More questions"],
            next_actions=["Study SPIN"],
        )
        response = AssessResponse(
            assessment_id=42,
            scores=scores,
            coaching=coaching,
        )
        assert response.assessment_id == 42
        assert response.scores.situation == 4
        assert response.scores.problem == 3
        assert response.coaching.summary == "Good start, needs practice"
        assert response.coaching.wins == ["Clear voice"]

    def test_assess_response_round_trip_serialization(self):
        """AssessResponse should round-trip through dict correctly"""
        scores = AssessmentScores(
            situation=1,
            problem=2,
            implication=3,
            need_payoff=4,
            flow=5,
            tone=1,
            engagement=2,
        )
        coaching = Coaching(
            summary="Test summary",
            wins=["Win 1", "Win 2"],
            gaps=["Gap 1"],
            next_actions=["Action 1", "Action 2", "Action 3"],
        )
        original = AssessResponse(
            assessment_id=999,
            scores=scores,
            coaching=coaching,
        )

        # Serialize to dict, then deserialize back
        data = original.model_dump()
        reconstructed = AssessResponse(**data)

        # Verify all fields match
        assert reconstructed.assessment_id == original.assessment_id
        assert reconstructed.scores.situation == original.scores.situation
        assert reconstructed.scores.problem == original.scores.problem
        assert reconstructed.scores.implication == original.scores.implication
        assert reconstructed.scores.need_payoff == original.scores.need_payoff
        assert reconstructed.scores.flow == original.scores.flow
        assert reconstructed.scores.tone == original.scores.tone
        assert reconstructed.scores.engagement == original.scores.engagement
        assert reconstructed.coaching.summary == original.coaching.summary
        assert reconstructed.coaching.wins == original.coaching.wins
        assert reconstructed.coaching.gaps == original.coaching.gaps
        assert reconstructed.coaching.next_actions == original.coaching.next_actions

    def test_assess_response_invalid_assessment_id_zero(self):
        """AssessResponse with assessment_id=0 should raise ValidationError"""
        scores = AssessmentScores(
            situation=3, problem=3, implication=3,
            need_payoff=3, flow=3, tone=3, engagement=3,
        )
        coaching = Coaching(summary="Test")

        with pytest.raises(ValidationError) as exc_info:
            AssessResponse(
                assessment_id=0,  # Invalid: must be >= 1
                scores=scores,
                coaching=coaching,
            )
        error = exc_info.value
        assert "assessment_id" in str(error)

    def test_assess_response_invalid_assessment_id_negative(self):
        """AssessResponse with negative assessment_id should raise ValidationError"""
        scores = AssessmentScores(
            situation=3, problem=3, implication=3,
            need_payoff=3, flow=3, tone=3, engagement=3,
        )
        coaching = Coaching(summary="Test")

        with pytest.raises(ValidationError) as exc_info:
            AssessResponse(
                assessment_id=-1,  # Invalid: must be >= 1
                scores=scores,
                coaching=coaching,
            )
        error = exc_info.value
        assert "assessment_id" in str(error)

    def test_assess_response_missing_required_fields(self):
        """AssessResponse missing required fields should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            AssessResponse(assessment_id=1)  # Missing scores and coaching
        error = exc_info.value
        assert "scores" in str(error) or "coaching" in str(error)
