"""
Structured logging middleware and utilities.
"""
import json
import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests with structured JSON format.

    Logs include:
    - request_id: Unique identifier for each request
    - method: HTTP method
    - path: Request path
    - status_code: Response status code
    - latency_ms: Request processing time in milliseconds
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log structured data."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log exception
            latency_ms = int((time.time() - start_time) * 1000)
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "latency_ms": latency_ms,
                "error": str(exc),
            }
            logger.error(json.dumps(log_data))
            raise

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Log request details
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }

        # Use appropriate log level based on status code
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


def configure_logging(log_level: str = "INFO"):
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",  # Simple format since we use JSON
        handlers=[logging.StreamHandler()],
    )
