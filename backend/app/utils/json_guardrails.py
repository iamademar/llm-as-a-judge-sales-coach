"""
JSON parsing utilities with guardrails for LLM outputs.

This module provides robust JSON parsing that handles common LLM output issues
like code fence wrapping and extra whitespace.
"""

import json
import re


def parse_json_strict(raw: str) -> dict:
    """
    Parse JSON with fallback strategies for LLM-generated content.

    Attempts multiple parsing strategies:
    1. Direct json.loads() on raw input
    2. Strip code fences (``` or ```json) and whitespace, then retry
    3. Raise ValueError with debugging context if all strategies fail

    Args:
        raw: Raw string that may contain JSON (possibly wrapped in code fences)

    Returns:
        Parsed JSON as a dictionary

    Raises:
        ValueError: If JSON cannot be parsed after all strategies, includes
                   first ~120 chars of input for debugging

    Examples:
        >>> parse_json_strict('{"key": "value"}')
        {'key': 'value'}

        >>> parse_json_strict('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}

        >>> parse_json_strict('```\\n{"key": "value"}\\n```')
        {'key': 'value'}
    """
    # Strategy 1: Try parsing as-is
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 2: Strip code fences and whitespace
    # Remove leading/trailing whitespace and newlines
    cleaned = raw.strip()

    # Pattern to match code fences with optional language specifier
    # Matches: ```json ... ``` or ``` ... ```
    fence_pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    match = re.match(fence_pattern, cleaned, re.DOTALL)

    if match:
        # Extract content between fences
        cleaned = match.group(1).strip()
    else:
        # Even without full fence pattern, strip any leading/trailing backticks
        cleaned = cleaned.strip('`').strip()

    # Try parsing cleaned version
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError) as e:
        # Strategy 3: Raise with context
        preview = raw[:120] if len(raw) > 120 else raw
        raise ValueError(
            f"Failed to parse JSON after cleanup strategies. "
            f"Error: {str(e)}. "
            f"Input preview (first 120 chars): {preview!r}"
        )
