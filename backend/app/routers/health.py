"""
Health check endpoint for monitoring and readiness probes.
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        dict: Simple status indicator {"ok": true}
    """
    return {"ok": True}
