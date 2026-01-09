"""
Unit tests for JSON guardrails utility.

Tests cover:
- Valid JSON parsing
- JSON wrapped in code fences (``` and ```json)
- Whitespace and newline handling
- Error cases with proper error messages
"""

import pytest

from app.utils.json_guardrails import parse_json_strict


class TestParseJsonStrictValidCases:
    """Tests for valid JSON parsing scenarios"""

    def test_parses_simple_object(self):
        """Parse simple JSON object"""
        raw = '{"key": "value"}'
        result = parse_json_strict(raw)
        assert result == {"key": "value"}

    def test_parses_nested_object(self):
        """Parse nested JSON object"""
        raw = '{"outer": {"inner": "value", "number": 42}}'
        result = parse_json_strict(raw)
        assert result == {"outer": {"inner": "value", "number": 42}}

    def test_parses_array(self):
        """Parse JSON array"""
        raw = '[1, 2, 3, "four"]'
        result = parse_json_strict(raw)
        assert result == [1, 2, 3, "four"]

    def test_parses_object_with_array(self):
        """Parse JSON object containing arrays"""
        raw = '{"items": [1, 2, 3], "name": "test"}'
        result = parse_json_strict(raw)
        assert result == {"items": [1, 2, 3], "name": "test"}

    def test_parses_complex_assessment_structure(self):
        """Parse complex nested structure similar to assessment response"""
        raw = '''{
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
                "wins": ["Clear questions", "Good rapport"],
                "gaps": ["Need more implication questions"],
                "next_actions": ["Practice SPIN", "Review recordings"]
            }
        }'''
        result = parse_json_strict(raw)
        assert result["scores"]["situation"] == 4
        assert result["coaching"]["summary"] == "Good job"
        assert len(result["coaching"]["wins"]) == 2


class TestParseJsonStrictCodeFences:
    """Tests for JSON wrapped in code fences"""

    def test_parses_json_in_triple_backticks(self):
        """Parse JSON wrapped in ``` code fence"""
        raw = '```\n{"key": "value"}\n```'
        result = parse_json_strict(raw)
        assert result == {"key": "value"}

    def test_parses_json_in_json_fence(self):
        """Parse JSON wrapped in ```json code fence"""
        raw = '```json\n{"key": "value"}\n```'
        result = parse_json_strict(raw)
        assert result == {"key": "value"}

    def test_parses_json_fence_no_newlines(self):
        """Parse JSON in code fence without newlines"""
        raw = '```{"key": "value"}```'
        result = parse_json_strict(raw)
        assert result == {"key": "value"}

    def test_parses_json_fence_with_extra_whitespace(self):
        """Parse JSON in code fence with extra whitespace"""
        raw = '```json\n\n  {"key": "value"}  \n\n```'
        result = parse_json_strict(raw)
        assert result == {"key": "value"}

    def test_parses_complex_json_in_fence(self):
        """Parse complex JSON structure in code fence"""
        raw = '''```json
        {
            "scores": {"situation": 4},
            "coaching": {
                "summary": "Test",
                "wins": ["Good"],
                "gaps": [],
                "next_actions": ["Practice"]
            }
        }
        ```'''
        result = parse_json_strict(raw)
        assert result["scores"]["situation"] == 4
        assert result["coaching"]["wins"] == ["Good"]

    def test_parses_array_in_code_fence(self):
        """Parse array in code fence"""
        raw = '```\n[1, 2, 3]\n```'
        result = parse_json_strict(raw)
        assert result == [1, 2, 3]


class TestParseJsonStrictWhitespace:
    """Tests for whitespace handling"""

    def test_parses_with_leading_whitespace(self):
        """Parse JSON with leading whitespace"""
        raw = '   \n\n  {"key": "value"}'
        result = parse_json_strict(raw)
        assert result == {"key": "value"}

    def test_parses_with_trailing_whitespace(self):
        """Parse JSON with trailing whitespace"""
        raw = '{"key": "value"}  \n\n  '
        result = parse_json_strict(raw)
        assert result == {"key": "value"}

    def test_parses_with_surrounding_whitespace(self):
        """Parse JSON with whitespace on both sides"""
        raw = '\n\n  {"key": "value"}  \n\n'
        result = parse_json_strict(raw)
        assert result == {"key": "value"}

    def test_parses_minified_json(self):
        """Parse minified JSON without whitespace"""
        raw = '{"key":"value","nested":{"inner":42}}'
        result = parse_json_strict(raw)
        assert result == {"key": "value", "nested": {"inner": 42}}


class TestParseJsonStrictErrorCases:
    """Tests for error handling"""

    def test_raises_on_invalid_json(self):
        """Raise ValueError on truly invalid JSON"""
        raw = '{key: value}'  # Missing quotes
        with pytest.raises(ValueError) as exc_info:
            parse_json_strict(raw)
        error = str(exc_info.value)
        assert "Failed to parse JSON" in error
        assert "{key: value}" in error  # Should include preview

    def test_raises_on_incomplete_json(self):
        """Raise ValueError on incomplete JSON"""
        raw = '{"key": "value"'  # Missing closing brace
        with pytest.raises(ValueError) as exc_info:
            parse_json_strict(raw)
        error = str(exc_info.value)
        assert "Failed to parse JSON" in error

    def test_raises_on_empty_string(self):
        """Raise ValueError on empty string"""
        raw = ''
        with pytest.raises(ValueError) as exc_info:
            parse_json_strict(raw)
        error = str(exc_info.value)
        assert "Failed to parse JSON" in error

    def test_raises_on_plain_text(self):
        """Raise ValueError on plain text (not JSON)"""
        raw = 'This is just plain text, not JSON'
        with pytest.raises(ValueError) as exc_info:
            parse_json_strict(raw)
        error = str(exc_info.value)
        assert "Failed to parse JSON" in error
        assert "This is just plain text" in error

    def test_raises_with_preview_on_long_input(self):
        """Error message includes preview (first 120 chars) for long input"""
        raw = '{"invalid": ' + 'x' * 200  # Invalid JSON that's very long
        with pytest.raises(ValueError) as exc_info:
            parse_json_strict(raw)
        error = str(exc_info.value)
        assert "Failed to parse JSON" in error
        # Should show preview, not entire input
        assert len(error) < 300  # Reasonable error message length
        assert "first 120 chars" in error

    def test_raises_on_json_with_trailing_comma(self):
        """Raise ValueError on JSON with trailing comma (invalid JSON)"""
        raw = '{"key": "value",}'  # Trailing comma is invalid JSON
        with pytest.raises(ValueError) as exc_info:
            parse_json_strict(raw)
        error = str(exc_info.value)
        assert "Failed to parse JSON" in error


class TestParseJsonStrictEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_parses_empty_object(self):
        """Parse empty JSON object"""
        raw = '{}'
        result = parse_json_strict(raw)
        assert result == {}

    def test_parses_empty_array(self):
        """Parse empty JSON array"""
        raw = '[]'
        result = parse_json_strict(raw)
        assert result == []

    def test_parses_json_with_escaped_quotes(self):
        """Parse JSON with escaped quotes in strings"""
        raw = '{"message": "He said \\"Hello\\""}'
        result = parse_json_strict(raw)
        assert result == {"message": 'He said "Hello"'}

    def test_parses_json_with_unicode(self):
        """Parse JSON with Unicode characters"""
        raw = '{"greeting": "Hello 世界", "emoji": "👋"}'
        result = parse_json_strict(raw)
        assert result == {"greeting": "Hello 世界", "emoji": "👋"}

    def test_parses_json_with_numbers(self):
        """Parse JSON with various number types"""
        raw = '{"int": 42, "float": 3.14, "negative": -10, "exp": 1.5e2}'
        result = parse_json_strict(raw)
        assert result == {"int": 42, "float": 3.14, "negative": -10, "exp": 150.0}

    def test_parses_json_with_booleans_and_null(self):
        """Parse JSON with boolean and null values"""
        raw = '{"active": true, "disabled": false, "value": null}'
        result = parse_json_strict(raw)
        assert result == {"active": True, "disabled": False, "value": None}

    def test_parses_json_with_only_backticks(self):
        """Parse JSON with backticks but not full fence"""
        raw = '`{"key": "value"}`'
        result = parse_json_strict(raw)
        assert result == {"key": "value"}

    def test_parses_assessment_response_in_fence(self):
        """Parse realistic assessment response in code fence"""
        raw = '''```json
{
  "scores": {
    "situation": 4,
    "problem": 3,
    "implication": 2,
    "need_payoff": 5,
    "flow": 4,
    "tone": 5,
    "engagement": 3
  },
  "coaching": {
    "summary": "Strong need-payoff questions but needs more implication development.",
    "wins": [
      "Excellent need-payoff questions connecting solution to buyer pains",
      "Professional and confident tone throughout",
      "Good situation questions to establish context"
    ],
    "gaps": [
      "Limited implication questions to build urgency",
      "Could improve flow by transitioning more smoothly between SPIN stages"
    ],
    "next_actions": [
      "Practice asking 'What happens if...' questions to develop implications",
      "Review SPIN sequencing: S→P→I→N",
      "Role-play scenarios focusing on implication stage"
    ]
  }
}
```'''
        result = parse_json_strict(raw)
        assert result["scores"]["situation"] == 4
        assert result["scores"]["need_payoff"] == 5
        assert len(result["coaching"]["wins"]) == 3
        assert len(result["coaching"]["gaps"]) == 2
        assert len(result["coaching"]["next_actions"]) == 3
        assert "implication" in result["coaching"]["summary"].lower()
