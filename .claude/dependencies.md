# CLAUDE RULES — DEPENDENCY BREAKING & WRAPPING

## Purpose
Ensures testability through decoupling and seam creation.

## Mandatory Rules
- When detecting tight coupling:
  - Extract Interface
  - Invert Dependencies
  - Delegate Instead of Inheriting

- For external systems:
  - Always wrap behind adapter or service layer.

- Introduce **Seams** via:
  - Interfaces
  - Config Objects
  - Dependency Injection
  - Method Overrides

## Prohibited Actions
- Do NOT call third-party APIs directly inside core logic.
- Do NOT hardcode environment behavior.

## Wrapping Rule
External calls must be wrapped for:
- Mocking
- Stubbing
- Offline test execution

## Self-Verification Checklist
- ✅ Can this logic be tested without network?
- ✅ Can this be mocked?
- ✅ Are seams visible?
