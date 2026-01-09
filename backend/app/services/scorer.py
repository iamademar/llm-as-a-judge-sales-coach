"""
SPIN scoring service using LLM-based assessment.

This module orchestrates the complete scoring pipeline:
1. Fetch organization's active prompt template from database
2. Build calibrated prompt from transcript using the template
3. Call LLM via provider-agnostic client
4. Parse and validate JSON response
5. Return structured assessment with metadata

Note: Each organization must have an active prompt template in the database.
Default templates are created automatically when organizations are seeded.
"""

import os
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.crud import prompt_template as template_crud
from app.prompts.prompt_templates import build_prompt
from app.services.llm_client import call_json
from app.utils.json_guardrails import parse_json_strict


# Model name from environment with sensible default
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")


def score_transcript(
    transcript: str,
    organization_id: Optional[uuid.UUID] = None,
    db: Optional[Session] = None,
) -> tuple[dict, str, str]:
    """
    Score a sales transcript using SPIN framework via LLM.

    This is the main scoring pipeline that:
    1. Fetches organization's active prompt template from database
    2. Builds calibrated prompt (system + user) using the template
    3. Calls LLM to generate assessment
    4. Parses and validates JSON response
    5. Validates score ranges and required keys
    6. Returns assessment data with metadata

    Args:
        transcript: Sales conversation transcript with speaker tags (Rep:/Buyer:)
        organization_id: Organization UUID for fetching prompt template and LLM credentials
        db: Database session for template and credential lookup

    Returns:
        Tuple of (assessment_data, model_name, prompt_version) where:
        - assessment_data: dict with "scores" and "coaching" keys
        - model_name: LLM model identifier used
        - prompt_version: Prompt template version identifier

    Raises:
        ValueError: If transcript is empty, no active template found, or JSON parsing fails
        AssertionError: If scores are out of range [1, 5] or required keys missing

    Examples:
        >>> os.environ["MOCK_LLM"] = "true"
        >>> # Note: Requires organization with active template in test DB
        >>> data, model, version = score_transcript("Rep: Hi\\nBuyer: Hello", org_id, db)
        >>> "scores" in data and "coaching" in data
        True
    """
    # Step 1: Fetch organization's active prompt template
    if not organization_id or not db:
        raise ValueError("organization_id and db are required for scoring")

    template = template_crud.get_active_for_org(db, organization_id)
    if not template:
        raise ValueError(
            "No active prompt template found for organization. "
            "Please ensure a default template was created during setup."
        )

    # Step 2: Build calibrated prompt using org's template
    system, user = build_prompt(
        transcript,
        system_prompt=template.system_prompt,
        user_template=template.user_template,
    )
    prompt_version = template.version

    # Step 3: Call LLM (mock or real provider)
    raw_json = call_json(
        system,
        user,
        model=MODEL_NAME,
        temperature=0.0,
        response_format_json=True,
        organization_id=organization_id,
        db=db,
    )

    # Step 4: Parse JSON with guardrails
    data = parse_json_strict(raw_json)

    # Step 5: Validate required keys
    assert "scores" in data, "Missing required key 'scores' in LLM response"
    assert "coaching" in data, "Missing required key 'coaching' in LLM response"

    # Step 6: Validate score bounds (all must be 1-5)
    scores = data["scores"]
    required_score_keys = [
        "situation", "problem", "implication", "need_payoff",
        "flow", "tone", "engagement"
    ]

    for key in required_score_keys:
        assert key in scores, f"Missing required score key '{key}'"
        score_value = scores[key]
        assert isinstance(score_value, int), \
            f"Score '{key}' must be integer, got {type(score_value).__name__}"
        assert 1 <= score_value <= 5, \
            f"Score '{key}' must be in range [1, 5], got {score_value}"

    # Step 7: Validate coaching structure
    coaching = data["coaching"]
    required_coaching_keys = ["summary", "wins", "gaps", "next_actions"]

    for key in required_coaching_keys:
        assert key in coaching, f"Missing required coaching key '{key}'"

    # Return assessment with metadata for tracking
    return data, MODEL_NAME, prompt_version
