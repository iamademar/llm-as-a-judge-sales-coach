# CLAUDE RULES — TESTING STRATEGY

## Purpose
Defines safe, incremental testing practices for modern and legacy code.

## Mandatory Rules
- Default test DB: **SQLite**
- Use PostgreSQL ONLY if SQLite fails due to DB-specific behavior.
- PostgreSQL tests MUST use:
  - @pytest.mark.integration
  - OR tests/integration/

- When modifying untested code:
  - First create **Characterization Tests**
  - Lock in existing outputs BEFORE refactoring.

## Prohibited Actions
- Do NOT rewrite logic without tests first.
- Do NOT require PostgreSQL for unit tests without justification.

## Characterization Testing Rule
When legacy logic lacks tests:
- Capture outputs
- Document side effects
- THEN refactor

## Self-Verification Checklist
- ✅ Is this a unit or integration test?
- ✅ Is SQLite sufficient?
- ✅ Is behavior locked before change?
