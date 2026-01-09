"""
Unit tests for SPIN scorer service.

Tests cover:
- Mock LLM integration (MOCK_LLM=true)
- Score validation and bounds checking
- Required keys validation
- Integration with prompt builder and JSON parser
- LangChain import availability
"""

import os
import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.services.scorer import score_transcript, MODEL_NAME


@pytest.fixture
def mock_template():
    """Create a mock prompt template for testing."""
    template = MagicMock()
    template.version = "spin_v1"
    template.system_prompt = "You are a SPIN assessment expert."
    template.user_template = "Assess this transcript: {transcript}"
    return template


@pytest.fixture
def org_id():
    """Generate a test organization ID."""
    return uuid.uuid4()


class TestScorerWithMockLLM:
    """Tests using mock LLM (MOCK_LLM=true)"""

    def test_score_transcript_returns_valid_structure(
        self, db_session, sample_organization, mock_template
    ):
        """score_transcript returns dict with scores and coaching"""
        # Mock the template lookup
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                transcript = "Rep: Hello, how can I help?\nBuyer: I need better analytics"
                data, model, version = score_transcript(
                    transcript,
                    organization_id=sample_organization.id,
                    db=db_session
                )

                # Verify return structure
                assert isinstance(data, dict)
                assert isinstance(model, str)
                assert isinstance(version, str)

                # Verify required top-level keys
                assert "scores" in data
                assert "coaching" in data

    def test_score_transcript_returns_metadata(
        self, db_session, sample_organization, mock_template
    ):
        """score_transcript returns model name and prompt version"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                transcript = "Rep: Hi\nBuyer: Hello"
                _, model, version = score_transcript(
                    transcript,
                    organization_id=sample_organization.id,
                    db=db_session
                )

                assert model == MODEL_NAME
                assert isinstance(version, str)
                assert len(version) > 0  # Version comes from DB template

    def test_score_transcript_validates_all_score_keys(
        self, db_session, sample_organization, mock_template
    ):
        """All required score keys are present in mock response"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                transcript = "Rep: Test\nBuyer: Test"
                data, _, _ = score_transcript(
                    transcript,
                    organization_id=sample_organization.id,
                    db=db_session
                )

                scores = data["scores"]
                required_keys = [
                    "situation", "problem", "implication", "need_payoff",
                    "flow", "tone", "engagement"
                ]

                for key in required_keys:
                    assert key in scores, f"Missing score key: {key}"

    def test_score_transcript_validates_score_bounds(
        self, db_session, sample_organization, mock_template
    ):
        """All scores are within valid range [1, 5]"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                transcript = "Rep: Test\nBuyer: Test"
                data, _, _ = score_transcript(
                    transcript,
                    organization_id=sample_organization.id,
                    db=db_session
                )

                scores = data["scores"]
                for key, value in scores.items():
                    assert isinstance(value, int), f"Score {key} must be int"
                    assert 1 <= value <= 5, f"Score {key}={value} out of range"

    def test_score_transcript_validates_coaching_keys(
        self, db_session, sample_organization, mock_template
    ):
        """All required coaching keys are present"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                transcript = "Rep: Test\nBuyer: Test"
                data, _, _ = score_transcript(
                    transcript,
                    organization_id=sample_organization.id,
                    db=db_session
                )

                coaching = data["coaching"]
                required_keys = ["summary", "wins", "gaps", "next_actions"]

                for key in required_keys:
                    assert key in coaching, f"Missing coaching key: {key}"

    def test_score_transcript_with_realistic_conversation(
        self, db_session, sample_organization, mock_template
    ):
        """Score a realistic multi-turn conversation"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                transcript = """Rep: Good morning! Thanks for taking the time today.
Buyer: No problem, happy to chat.
Rep: Can you tell me about your current sales process?
Buyer: We use spreadsheets mainly. It's getting messy.
Rep: How is that impacting your team's productivity?
Buyer: We're spending too much time on admin instead of selling.
Rep: What would it mean if this continues?
Buyer: We'd probably miss our quarterly targets.
Rep: If you had a solution that automated this, how would that help?
Buyer: That would free up at least 10 hours per week."""

                data, model, version = score_transcript(
                    transcript,
                    organization_id=sample_organization.id,
                    db=db_session
                )

                # Verify structure
                assert "scores" in data
                assert "coaching" in data
                assert model == MODEL_NAME
                assert isinstance(version, str) and len(version) > 0

                # Verify all scores are valid
                for key, value in data["scores"].items():
                    assert 1 <= value <= 5


class TestScorerValidation:
    """Tests for validation and error handling"""

    def test_score_transcript_with_out_of_range_scores_raises(
        self, db_session, sample_organization, mock_template
    ):
        """Scores outside [1, 5] range raise AssertionError"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                # Patch call_json to return invalid scores
                invalid_json = """{
                    "scores": {
                        "situation": 6,
                        "problem": 3,
                        "implication": 3,
                        "need_payoff": 3,
                        "flow": 3,
                        "tone": 3,
                        "engagement": 3
                    },
                    "coaching": {
                        "summary": "Test",
                        "wins": [],
                        "gaps": [],
                        "next_actions": []
                    }
                }"""

                with patch("app.services.scorer.call_json", return_value=invalid_json):
                    with pytest.raises(AssertionError) as exc_info:
                        score_transcript(
                            "Rep: test\nBuyer: test",
                            organization_id=sample_organization.id,
                            db=db_session
                        )

                    error = str(exc_info.value)
                    assert "must be in range [1, 5]" in error.lower()

    def test_score_transcript_with_missing_scores_key_raises(
        self, db_session, sample_organization, mock_template
    ):
        """Missing 'scores' key raises AssertionError"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                invalid_json = """{
                    "coaching": {
                        "summary": "Test",
                        "wins": [],
                        "gaps": [],
                        "next_actions": []
                    }
                }"""

                with patch("app.services.scorer.call_json", return_value=invalid_json):
                    with pytest.raises(AssertionError) as exc_info:
                        score_transcript(
                            "Rep: test\nBuyer: test",
                            organization_id=sample_organization.id,
                            db=db_session
                        )

                    error = str(exc_info.value)
                    assert "scores" in error.lower()

    def test_score_transcript_with_missing_coaching_key_raises(
        self, db_session, sample_organization, mock_template
    ):
        """Missing 'coaching' key raises AssertionError"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                invalid_json = """{
                    "scores": {
                        "situation": 3,
                        "problem": 3,
                        "implication": 3,
                        "need_payoff": 3,
                        "flow": 3,
                        "tone": 3,
                        "engagement": 3
                    }
                }"""

                with patch("app.services.scorer.call_json", return_value=invalid_json):
                    with pytest.raises(AssertionError) as exc_info:
                        score_transcript(
                            "Rep: test\nBuyer: test",
                            organization_id=sample_organization.id,
                            db=db_session
                        )

                    error = str(exc_info.value)
                    assert "coaching" in error.lower()

    def test_score_transcript_with_missing_score_dimension_raises(
        self, db_session, sample_organization, mock_template
    ):
        """Missing score dimension raises AssertionError"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                # Missing 'implication' score
                invalid_json = """{
                    "scores": {
                        "situation": 3,
                        "problem": 3,
                        "need_payoff": 3,
                        "flow": 3,
                        "tone": 3,
                        "engagement": 3
                    },
                    "coaching": {
                        "summary": "Test",
                        "wins": [],
                        "gaps": [],
                        "next_actions": []
                    }
                }"""

                with patch("app.services.scorer.call_json", return_value=invalid_json):
                    with pytest.raises(AssertionError) as exc_info:
                        score_transcript(
                            "Rep: test\nBuyer: test",
                            organization_id=sample_organization.id,
                            db=db_session
                        )

                    error = str(exc_info.value)
                    assert "implication" in error.lower()

    def test_score_transcript_with_non_integer_score_raises(
        self, db_session, sample_organization, mock_template
    ):
        """Non-integer score raises AssertionError"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                invalid_json = """{
                    "scores": {
                        "situation": 3.5,
                        "problem": 3,
                        "implication": 3,
                        "need_payoff": 3,
                        "flow": 3,
                        "tone": 3,
                        "engagement": 3
                    },
                    "coaching": {
                        "summary": "Test",
                        "wins": [],
                        "gaps": [],
                        "next_actions": []
                    }
                }"""

                with patch("app.services.scorer.call_json", return_value=invalid_json):
                    with pytest.raises(AssertionError) as exc_info:
                        score_transcript(
                            "Rep: test\nBuyer: test",
                            organization_id=sample_organization.id,
                            db=db_session
                        )

                    error = str(exc_info.value)
                    assert "must be integer" in error.lower()


class TestScorerIntegration:
    """Integration tests verifying end-to-end pipeline"""

    def test_scorer_integrates_with_prompt_builder(
        self, db_session, sample_organization, mock_template
    ):
        """Scorer uses prompt builder correctly"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                with patch("app.services.scorer.build_prompt") as mock_build:
                    mock_build.return_value = ("system prompt", "user prompt")

                    with patch("app.services.scorer.call_json") as mock_call:
                        mock_call.return_value = '{"scores":{"situation":3,"problem":3,"implication":3,"need_payoff":3,"flow":3,"tone":3,"engagement":3},"coaching":{"summary":"test","wins":[],"gaps":[],"next_actions":[]}}'

                        transcript = "Rep: test\nBuyer: test"
                        score_transcript(
                            transcript,
                            organization_id=sample_organization.id,
                            db=db_session
                        )

                        # Verify build_prompt was called with transcript and template prompts
                        mock_build.assert_called_once()
                        call_args = mock_build.call_args
                        assert transcript in call_args[0]

    def test_scorer_integrates_with_llm_client(
        self, db_session, sample_organization, mock_template
    ):
        """Scorer calls LLM client with correct parameters"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                with patch("app.services.scorer.call_json") as mock_call:
                    mock_call.return_value = '{"scores":{"situation":3,"problem":3,"implication":3,"need_payoff":3,"flow":3,"tone":3,"engagement":3},"coaching":{"summary":"test","wins":[],"gaps":[],"next_actions":[]}}'

                    score_transcript(
                        "Rep: test\nBuyer: test",
                        organization_id=sample_organization.id,
                        db=db_session
                    )

                    # Verify call_json was called with correct args
                    mock_call.assert_called_once()
                    call_args = mock_call.call_args
                    assert call_args.kwargs["model"] == MODEL_NAME
                    assert call_args.kwargs["temperature"] == 0.0
                    assert call_args.kwargs["response_format_json"] is True

    def test_scorer_integrates_with_json_parser(
        self, db_session, sample_organization, mock_template
    ):
        """Scorer uses JSON parser with guardrails"""
        with patch("app.services.scorer.template_crud.get_active_for_org", return_value=mock_template):
            with patch.dict(os.environ, {"MOCK_LLM": "true"}):
                # Test with code-fenced JSON
                fenced_json = """```json
{
    "scores": {
        "situation": 4,
        "problem": 3,
        "implication": 5,
        "need_payoff": 2,
        "flow": 4,
        "tone": 5,
        "engagement": 3
    },
    "coaching": {
        "summary": "Good job",
        "wins": ["Clear questions"],
        "gaps": ["More implication"],
        "next_actions": ["Practice"]
    }
}
```"""

                with patch("app.services.scorer.call_json", return_value=fenced_json):
                    data, _, _ = score_transcript(
                        "Rep: test\nBuyer: test",
                        organization_id=sample_organization.id,
                        db=db_session
                    )

                    # Verify JSON was parsed correctly despite code fences
                    assert data["scores"]["situation"] == 4
                    assert data["scores"]["implication"] == 5
                    assert data["coaching"]["summary"] == "Good job"


class TestLangChainImports:
    """Sanity tests for LangChain package availability"""

    def test_langchain_prompts_import_available(self):
        """LangChain ChatPromptTemplate can be imported"""
        try:
            from langchain.prompts import ChatPromptTemplate
            # Verify it's a class/type
            assert ChatPromptTemplate is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ChatPromptTemplate: {e}")

    def test_langchain_openai_import_available(self):
        """LangChain OpenAI ChatOpenAI can be imported"""
        try:
            from langchain_openai import ChatOpenAI
            # Verify it's a class/type
            assert ChatOpenAI is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ChatOpenAI: {e}")

    def test_langchain_package_installed(self):
        """LangChain core package is installed"""
        try:
            import langchain
            # Package should have basic attributes
            assert hasattr(langchain, "__version__") or hasattr(langchain, "__file__")
        except ImportError as e:
            pytest.fail(f"LangChain package not installed: {e}")
