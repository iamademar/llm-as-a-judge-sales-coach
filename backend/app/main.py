"""
FastAPI application entrypoint for SPIN Scoring + Coaching API.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import (
    health,
    assess,
    auth,
    representatives,
    transcripts,
    llm_credentials,
    prompt_templates,
    evaluations,
    overview,
    seed,
)
from app.core.logging import StructuredLoggingMiddleware, configure_logging
from app.core.errors import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from app.core.config import settings
from app.startup import run_startup_tasks

# Configure logging
configure_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks: migrations and demo data seeding."""
    run_startup_tasks()
    yield
    # Cleanup code can go here if needed


app = FastAPI(
    title="SPIN Sales Conversation Scorer",
    description="Prompt-only LLMPAA for SPIN scoring and coaching",
    version="0.1.0",
    lifespan=lifespan,
)

# Dynamic CORS configuration
allowed_origins = ["http://localhost:3000", "https://frontend.icyforest-aa3b4633.southeastasia.azurecontainerapps.io"]

# Add production frontend URL if configured
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware
app.add_middleware(StructuredLoggingMiddleware)

# Add exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(assess.router)
app.include_router(auth.router)
app.include_router(representatives.router)
app.include_router(transcripts.router)
app.include_router(llm_credentials.router)
app.include_router(prompt_templates.router)
app.include_router(evaluations.router)
app.include_router(overview.router)
app.include_router(seed.router)


@app.get("/")
def root() -> dict:
    """
    Root endpoint redirects to /health.

    Returns:
        dict: Health status
    """
    return {"ok": True}
