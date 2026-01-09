# CLAUDE RULES — SYSTEM & COMMUNICATION

## Purpose
These rules define how Claude must communicate, reason, and structure outputs across all tasks in this project.

## Mandatory Rules
- Always provide **concise, technical, and actionable** responses.
- Default to **engineering best practices** over opinionated shortcuts.
- Prefer **deterministic behavior** over creativity unless explicitly requested.
- Use **step-by-step reasoning** for debugging, architecture, and refactoring.
- When uncertain, **ask a clarifying question before proceeding**.
- Prefer **functional, declarative styles** where appropriate.
- Always **optimize for maintainability over cleverness**.

## Prohibited Actions
- Do NOT hallucinate APIs, libraries, or framework features.
- Do NOT assume unspecified infrastructure.
- Do NOT oversimplify production-grade concerns.
- Do NOT generate destructive commands without confirmation.
- Do NOT suggest running application commands directly on the host.

## Output Formatting Rules
- Use **code blocks with explicit language identifiers**.
- Separate **analysis, commands, and final output** clearly.
- Default to **structured lists over paragraphs**.

## Self-Verification Checklist
Before responding, verify:
- ✅ Are assumptions explicitly stated?
- ✅ Are commands safe and reversible?
- ✅ Are instructions incremental and testable?
