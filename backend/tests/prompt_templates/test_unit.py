"""
Unit tests for prompt templates.

Tests cover:
- Deterministic prompt generation (snapshot testing)
- Required schema keys presence
- Error handling for invalid inputs
- Immutability and consistency
"""

import pytest

from app.prompts.prompt_templates import SYSTEM, USER_TEMPLATE, build_prompt


class TestPromptTemplatesConstants:
    """Tests for immutable prompt constants"""

    def test_system_prompt_contains_key_instructions(self):
        """System prompt includes critical instructions"""
        assert "senior sales coach" in SYSTEM.lower()
        assert "SPIN" in SYSTEM
        assert "strict json" in SYSTEM.lower() or "STRICT JSON" in SYSTEM
        assert "schema" in SYSTEM.lower()

    def test_system_prompt_prohibits_extra_keys(self):
        """System prompt explicitly forbids extra keys"""
        assert "extra keys" in SYSTEM.lower() or "extra key" in SYSTEM.lower()

    def test_user_template_contains_rubric(self):
        """User template includes scoring rubric"""
        assert "RUBRIC" in USER_TEMPLATE.upper()
        assert "situation" in USER_TEMPLATE.lower()
        assert "problem" in USER_TEMPLATE.lower()
        assert "implication" in USER_TEMPLATE.lower()
        assert "need_payoff" in USER_TEMPLATE.lower()
        assert "flow" in USER_TEMPLATE.lower()
        assert "tone" in USER_TEMPLATE.lower()
        assert "engagement" in USER_TEMPLATE.lower()

    def test_user_template_contains_json_schema(self):
        """User template includes JSON schema definition"""
        assert "JSON SCHEMA" in USER_TEMPLATE.upper() or "schema" in USER_TEMPLATE.lower()
        assert '"scores"' in USER_TEMPLATE
        assert '"coaching"' in USER_TEMPLATE
        assert '"minimum": 1' in USER_TEMPLATE
        assert '"maximum": 5' in USER_TEMPLATE

    def test_user_template_has_transcript_placeholder(self):
        """User template has placeholder for transcript injection"""
        assert "{transcript}" in USER_TEMPLATE
        assert "CONVERSATION" in USER_TEMPLATE.upper() or "TRANSCRIPT" in USER_TEMPLATE.upper()


class TestBuildPrompt:
    """Tests for build_prompt function"""

    def test_build_prompt_returns_tuple(self):
        """build_prompt returns tuple of two strings"""
        transcript = "Rep: Hello\nBuyer: Hi there"
        result = build_prompt(transcript)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)

    def test_build_prompt_system_matches_constant(self):
        """System prompt from build_prompt matches SYSTEM constant"""
        transcript = "Rep: Hello\nBuyer: Hi there"
        system, _ = build_prompt(transcript)

        assert system == SYSTEM

    def test_build_prompt_injects_transcript(self):
        """build_prompt correctly injects transcript into user prompt"""
        transcript = "Rep: Good morning, how can I help?\nBuyer: I need a solution for X"
        _, user = build_prompt(transcript)

        assert transcript in user
        assert "Rep: Good morning" in user
        assert "Buyer: I need a solution" in user

    def test_build_prompt_is_deterministic(self):
        """build_prompt produces identical output for same input"""
        transcript = "Rep: Hello\nBuyer: Hi there"

        system1, user1 = build_prompt(transcript)
        system2, user2 = build_prompt(transcript)

        assert system1 == system2
        assert user1 == user2

    def test_build_prompt_different_transcripts_different_output(self):
        """Different transcripts produce different user prompts"""
        transcript1 = "Rep: Hello\nBuyer: Hi"
        transcript2 = "Rep: Good morning\nBuyer: Good day"

        _, user1 = build_prompt(transcript1)
        _, user2 = build_prompt(transcript2)

        assert user1 != user2
        assert "Hello" in user1
        assert "Good morning" in user2

    def test_build_prompt_empty_transcript_raises(self):
        """Empty transcript raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            build_prompt("")

        error = str(exc_info.value)
        assert "empty" in error.lower()

    def test_build_prompt_whitespace_only_transcript_raises(self):
        """Whitespace-only transcript raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            build_prompt("   \n\n  ")

        error = str(exc_info.value)
        assert "empty" in error.lower()


class TestPromptSnapshot:
    """Snapshot tests for prompt determinism"""

    # Expected snapshot for a fixed transcript
    FIXTURE_TRANSCRIPT = "Rep: Hi, what challenges are you facing?\nBuyer: We need better analytics"

    def test_user_prompt_snapshot_matches_expected(self):
        """
        Snapshot test: User prompt matches expected structure.

        This test locks in the current prompt format. If you intentionally change
        the prompt template, update this snapshot test accordingly.
        """
        _, user = build_prompt(self.FIXTURE_TRANSCRIPT)

        # Verify key sections are present in expected order
        assert "SCORING RUBRIC" in user
        assert "JSON SCHEMA" in user
        assert "CONVERSATION TRANSCRIPT:" in user

        # Verify transcript appears after schema
        schema_pos = user.find("JSON SCHEMA")
        transcript_pos = user.find("CONVERSATION TRANSCRIPT:")
        fixture_pos = user.find(self.FIXTURE_TRANSCRIPT)

        assert schema_pos < transcript_pos < fixture_pos

        # Verify rubric appears before schema
        rubric_pos = user.find("SCORING RUBRIC")
        assert rubric_pos < schema_pos

    def test_user_prompt_length_consistency(self):
        """User prompt length is consistent for same transcript length"""
        transcript1 = "Rep: Hello\nBuyer: Hi"
        transcript2 = "Rep: Howdy\nBuyer: Hey"

        _, user1 = build_prompt(transcript1)
        _, user2 = build_prompt(transcript2)

        # Length should differ only by transcript length difference
        len_diff = abs(len(user1) - len(user2))
        transcript_len_diff = abs(len(transcript1) - len(transcript2))

        assert len_diff == transcript_len_diff

    def test_user_prompt_contains_all_spin_dimensions(self):
        """User prompt explicitly mentions all 7 scoring dimensions"""
        _, user = build_prompt("Rep: test\nBuyer: test")

        # All 7 dimensions must appear
        required_dimensions = [
            "situation",
            "problem",
            "implication",
            "need_payoff",
            "flow",
            "tone",
            "engagement"
        ]

        for dimension in required_dimensions:
            assert dimension in user.lower(), f"Missing dimension: {dimension}"


class TestPromptSchemaKeys:
    """Tests verifying JSON schema structure in prompt"""

    def test_schema_contains_all_required_score_keys(self):
        """JSON schema in prompt lists all required score fields"""
        _, user = build_prompt("Rep: test\nBuyer: test")

        # Extract schema section
        schema_start = user.find('"scores"')
        schema_end = user.find('"coaching"')
        scores_schema = user[schema_start:schema_end]

        required_keys = [
            '"situation"',
            '"problem"',
            '"implication"',
            '"need_payoff"',
            '"flow"',
            '"tone"',
            '"engagement"'
        ]

        for key in required_keys:
            assert key in scores_schema, f"Missing schema key: {key}"

    def test_schema_contains_all_required_coaching_keys(self):
        """JSON schema in prompt lists all required coaching fields"""
        _, user = build_prompt("Rep: test\nBuyer: test")

        # Extract coaching schema section
        coaching_start = user.find('"coaching"')
        coaching_section = user[coaching_start:]

        required_keys = [
            '"summary"',
            '"wins"',
            '"gaps"',
            '"next_actions"'
        ]

        for key in required_keys:
            assert key in coaching_section, f"Missing coaching key: {key}"

    def test_schema_specifies_score_bounds(self):
        """JSON schema specifies minimum and maximum for scores"""
        _, user = build_prompt("Rep: test\nBuyer: test")

        # Schema should specify bounds
        assert '"minimum": 1' in user
        assert '"maximum": 5' in user
        assert '"type": "integer"' in user

    def test_schema_specifies_required_fields(self):
        """JSON schema marks scores and coaching as required"""
        _, user = build_prompt("Rep: test\nBuyer: test")

        # Should have required arrays
        assert '"required"' in user
        assert '"scores"' in user
        assert '"coaching"' in user


class TestPromptEdgeCases:
    """Tests for edge cases and special characters"""

    def test_build_prompt_with_multiline_transcript(self):
        """Handles transcript with multiple turns"""
        transcript = """Rep: Good morning! How are you today?
Buyer: I'm well, thanks for asking.
Rep: Great! What brings you here today?
Buyer: We're looking to improve our sales process.
Rep: Tell me more about your current process."""

        _, user = build_prompt(transcript)

        # All turns should be preserved
        assert "Good morning" in user
        assert "I'm well" in user
        assert "improve our sales process" in user

    def test_build_prompt_with_special_characters(self):
        """Handles transcript with special characters"""
        transcript = 'Rep: What\'s your budget? $10,000?\nBuyer: Around $15k-$20k.'

        _, user = build_prompt(transcript)

        assert "$10,000" in user
        assert "$15k-$20k" in user
        assert "What's" in user

    def test_build_prompt_with_unicode(self):
        """Handles transcript with Unicode characters"""
        transcript = "Rep: Hello! 👋\nBuyer: Café discussions? ☕"

        _, user = build_prompt(transcript)

        assert "👋" in user
        assert "Café" in user
        assert "☕" in user

    def test_build_prompt_preserves_formatting(self):
        """Transcript formatting (newlines, spacing) is preserved"""
        transcript = "Rep: Line 1\n\nBuyer: Line 2 with  double  spaces"

        _, user = build_prompt(transcript)

        # Should preserve the transcript exactly as given
        assert transcript in user
