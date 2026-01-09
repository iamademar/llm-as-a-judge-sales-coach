# CLAUDE RULES — LEGACY & SAFE REFACTORING

## Purpose
Controls how new behavior and refactors are safely introduced into fragile codebases.

## Mandatory Rules
- Prefer **small, reversible refactors**.
- Avoid **big bang rewrites**.
- Introduce new logic via:
  - Sprout Method
  - Sprout Class

- Apply **Scratch Refactoring** for risky changes:
  - Work in throwaway file or branch
  - Import only proven improvements

## Prohibited Actions
- Do NOT directly inject complex logic into fragile legacy code.
- Do NOT refactor untested code without characterization tests.

## Sprout Rule
If adding new behavior:
- Create new method/class
- Call from legacy location
- Preserve original behavior

## Scratch Rule
For risky refactors:
- Clone logic
- Refactor freely
- Re-integrate safely

## Self-Verification Checklist
- ✅ Is behavior preserved?
- ✅ Was this change reversible?
- ✅ Is new logic isolated?
