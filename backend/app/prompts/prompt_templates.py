"""
Deterministic prompt templates for SPIN scoring.

This module provides immutable prompt templates calibrated for strict JSON output
aligned with the SPIN framework (Situation, Problem, Implication, Need-Payoff).
"""

# Immutable system prompt - instructs LLM behavior
SYSTEM = """You are a senior sales coach specializing in the SPIN (Situation, Problem, Implication, Need-Payoff) selling methodology.

Your task is to evaluate sales conversations and provide scoring and coaching feedback.

CRITICAL INSTRUCTIONS:
- Return STRICT JSON that exactly matches the provided JSON Schema
- Do NOT include any extra keys beyond those specified in the schema
- Do NOT wrap your response in markdown code blocks
- Ensure all scores are integers between 1 and 5 (inclusive)
- Base your assessment on evidence from the conversation transcript"""

# Immutable user prompt template with rubric and JSON schema
USER_TEMPLATE = """Evaluate the following sales conversation using the SPIN framework.

SCORING RUBRIC (1-5 scale):

**situation** (1-5): Quality of situation questions
- 1: No situation questions; jumps to pitch
- 2: Minimal context gathering; superficial questions
- 3: Adequate situation questions covering basic context
- 4: Good situation questions establishing clear current state
- 5: Excellent situation questions; thorough understanding of buyer's environment

**problem** (1-5): Quality of problem questions
- 1: No problem identification; ignores pain points
- 2: Weak problem exploration; misses key issues
- 3: Identifies some problems but lacks depth
- 4: Good problem identification with clear pain points
- 5: Exceptional problem discovery; uncovers hidden issues

**implication** (1-5): Quality of implication questions
- 1: No exploration of consequences; stays surface-level
- 2: Minimal urgency building; weak consequence exploration
- 3: Some implication questions but lacks impact
- 4: Good implication development building urgency
- 5: Outstanding implication questions creating compelling urgency

**need_payoff** (1-5): Quality of need-payoff questions
- 1: No connection between solution and buyer value
- 2: Weak value proposition; generic benefits
- 3: Adequate need-payoff with some value connection
- 4: Strong need-payoff linking solution to specific pains
- 5: Exceptional need-payoff; buyer articulates own value

**flow** (1-5): Adherence to SPIN sequence (S→P→I→N)
- 1: Random questioning; no discernible structure
- 2: Poor flow; jumps between stages inconsistently
- 3: Follows SPIN loosely; some stage mixing
- 4: Good SPIN sequence with clear progression
- 5: Excellent SPIN flow; natural and purposeful transitions

**tone** (1-5): Professional, empathetic, confident, adaptive communication
- 1: Pitchy, monologue-style; ignores buyer cues
- 2: Inconsistent tone; occasional empathy gaps
- 3: Mixed empathy and clarity; adequate professionalism
- 4: Strong tone; professional, warm, and responsive
- 5: Exceptional tone; adaptive, empathetic, confident, concise

**engagement** (1-5): Active listening, reflection, buyer talk-time
- 1: Dominates conversation; no active listening
- 2: Limited listening; minimal buyer participation
- 3: Adequate engagement; balanced talk-time
- 4: Good engagement; actively listens and reflects
- 5: Outstanding engagement; buyer-led insights and high talk-time

JSON SCHEMA (your response must match this exactly):
{{
  "type": "object",
  "properties": {{
    "scores": {{
      "type": "object",
      "properties": {{
        "situation": {{"type": "integer", "minimum": 1, "maximum": 5}},
        "problem": {{"type": "integer", "minimum": 1, "maximum": 5}},
        "implication": {{"type": "integer", "minimum": 1, "maximum": 5}},
        "need_payoff": {{"type": "integer", "minimum": 1, "maximum": 5}},
        "flow": {{"type": "integer", "minimum": 1, "maximum": 5}},
        "tone": {{"type": "integer", "minimum": 1, "maximum": 5}},
        "engagement": {{"type": "integer", "minimum": 1, "maximum": 5}}
      }},
      "required": ["situation", "problem", "implication", "need_payoff", "flow", "tone", "engagement"]
    }},
    "coaching": {{
      "type": "object",
      "properties": {{
        "summary": {{"type": "string"}},
        "wins": {{"type": "array", "items": {{"type": "string"}}}},
        "gaps": {{"type": "array", "items": {{"type": "string"}}}},
        "next_actions": {{"type": "array", "items": {{"type": "string"}}}}
      }},
      "required": ["summary", "wins", "gaps", "next_actions"]
    }}
  }},
  "required": ["scores", "coaching"]
}}

CONVERSATION TRANSCRIPT:
{transcript}

Provide your assessment as valid JSON matching the schema above."""


def build_prompt(
    transcript: str,
    *,
    system_prompt: str | None = None,
    user_template: str | None = None,
) -> tuple[str, str]:
    """
    Build system and user prompts for SPIN assessment.

    This function is deterministic - given the same transcript and templates,
    it will always produce the same prompts. This is critical for:
    - Reproducible evaluations
    - A/B testing different prompt versions
    - Debugging LLM responses

    Args:
        transcript: Sales conversation transcript with speaker tags (Rep:/Buyer:)
        system_prompt: Custom system prompt (falls back to default SYSTEM if None)
        user_template: Custom user template (falls back to default USER_TEMPLATE if None)

    Returns:
        Tuple of (system_prompt, user_prompt)

    Examples:
        >>> system, user = build_prompt("Rep: Hello\\nBuyer: Hi there")
        >>> "sales coach" in system
        True
        >>> "CONVERSATION TRANSCRIPT:" in user
        True
        >>> "Rep: Hello" in user
        True
        >>> # With custom templates
        >>> system, user = build_prompt("Rep: Hi", system_prompt="You are a coach.", user_template="Evaluate: {transcript}")
        >>> system
        'You are a coach.'
        >>> "Rep: Hi" in user
        True
    """
    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty")

    final_system = system_prompt if system_prompt else SYSTEM
    final_user_template = user_template if user_template else USER_TEMPLATE

    user_prompt = final_user_template.format(transcript=transcript)

    return final_system, user_prompt
