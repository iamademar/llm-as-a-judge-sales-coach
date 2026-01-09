# CLAUDE RULES — SECURITY & SECRETS

## Purpose
Prevents leakage of secrets and unsafe authentication behaviors.

## Mandatory Rules
- All secrets must be stored in environment variables.
- Never log:
  - API keys
  - Tokens
  - Passwords
- Authentication must use:
  - JWT or OAuth where applicable
  - Hashed passwords only

## Prohibited Actions
- Do NOT place secrets in source code.
- Do NOT expose tokens in logs or exceptions.

## Self-Verification Checklist
- ✅ Are secrets externalized?
- ✅ Is hashing applied to credentials?
- ✅ Are logs sanitized?
