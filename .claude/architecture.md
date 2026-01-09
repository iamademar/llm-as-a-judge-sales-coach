# CLAUDE RULES — FASTAPI ARCHITECTURE

## Purpose
Defines canonical project structure and clean architecture boundaries.

## Mandatory Rules
- Always align with this structure:

app/main.py        → App initialization & router mounting  
routers/           → API route definitions  
models/            → ORM / SQL models  
schemas/           → Pydantic request & response models  
services/          → Business logic  
dependencies.py   → Shared dependency injection  
core/              → Config, DB, security utilities  
tests/             → Mirrors feature structure  

- Enforce **Separation of Concerns**.
- Business logic MUST NOT live in routers.
- Routers must remain **thin orchestration layers**.
- Services must be **pure and testable**.
- Prefer **Receive Object, Return Object (RORO)** patterns.
- Use **descriptive boolean variables** (`is_active`, `has_access`).

## Prohibited Actions
- Do NOT place database logic in route handlers.
- Do NOT mix schemas with models.
- Do NOT embed configuration inside business logic.

## Self-Verification Checklist
- ✅ Is routing separate from logic?
- ✅ Are schemas isolated from DB models?
- ✅ Is the service layer testable independently?
