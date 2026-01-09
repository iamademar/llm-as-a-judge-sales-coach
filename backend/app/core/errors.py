"""
Global exception handlers for consistent error responses.
"""
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def get_request_id(request: Request) -> str:
    """Get request ID from request state, or generate a fallback."""
    return getattr(request.state, "request_id", "unknown")


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent error format.

    Returns JSON with:
    - error.type: Exception class name
    - error.message: Error message
    - error.request_id: Request identifier
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.detail,
                "request_id": get_request_id(request),
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors with consistent format.

    Includes validation error details in the response.
    """
    # Convert errors to serializable format
    errors = []
    for error in exc.errors():
        serializable_error = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        }
        # Convert any non-serializable input values to strings
        if "input" in error:
            try:
                # Try to include input if it's serializable
                serializable_error["input"] = error["input"]
            except (TypeError, ValueError):
                # If not serializable, convert to string
                serializable_error["input"] = str(error["input"])
        errors.append(serializable_error)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "request_id": get_request_id(request),
                "details": errors,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other exceptions with consistent format.

    Prevents leaking sensitive information by providing generic error message.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": "Internal server error",
                "request_id": get_request_id(request),
            }
        },
    )
