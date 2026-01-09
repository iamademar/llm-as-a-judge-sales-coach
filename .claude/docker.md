# CLAUDE RULES — DOCKER & ENVIRONMENT

## Purpose
Ensures all development, execution, and troubleshooting assume a Docker environment.

## Mandatory Rules
- Always assume this is a **Docker-based FastAPI + PostgreSQL stack**.
- Always use:
  docker compose up -d
  docker compose exec app bash
  docker compose restart app
  docker compose logs -f app

- Assume ports:
  App → 8001  
  Main DB → 5434  
  Test DB → 5435  

- Always suggest:
  curl http://localhost:8001/health  
  http://localhost:8001/docs  

## Prohibited Actions
- Do NOT suggest running:
  python, pip, uvicorn, pytest directly on host.
- Do NOT assume local virtualenv usage.

## Troubleshooting Rules
- If container fails → docker compose logs
- If DB fails → docker compose ps
- If port conflicts → docker compose down && docker compose up -d
- If disk full → docker system prune -a (with warning)

## Self-Verification Checklist
- ✅ Are all commands Docker-based?
- ✅ Are ports verified?
- ✅ Are logs checked before guessing?
