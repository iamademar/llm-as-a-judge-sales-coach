"""
Security utilities for API authentication.
"""
from typing import Optional, Union
from fastapi import Header, HTTPException, status, Depends
from app.core.config import settings
from app.core.jwt_dependency import get_current_user_optional
from app.models.user import User


def require_api_key(x_api_key: str = Header(None)) -> str:
    """
    Dependency to require valid API key in x-api-key header.

    Args:
        x_api_key: API key from x-api-key header

    Returns:
        str: The validated API key

    Raises:
        HTTPException: 401 if API key is missing or invalid

    Usage:
        @router.post("/protected", dependencies=[Depends(require_api_key)])
        def protected_route():
            return {"message": "success"}
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide x-api-key header.",
        )

    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return x_api_key


def require_api_key_or_jwt(
    x_api_key: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Union[str, User]:
    """
    Dependency to require either valid API key OR valid JWT token.
    
    Accepts authentication via either:
    - X-API-Key header with valid API key
    - Authorization header with valid JWT Bearer token
    
    Args:
        x_api_key: Optional API key from X-API-Key header
        current_user: Optional user from JWT token (via dependency)
    
    Returns:
        Union[str, User]: The API key string or authenticated User object
    
    Raises:
        HTTPException: 401 if neither authentication method is valid
    
    Usage:
        @router.post("/protected")
        def protected_route(auth: Union[str, User] = Depends(require_api_key_or_jwt)):
            return {"message": "success"}
    """
    # Check JWT authentication first
    if current_user:
        return current_user
    
    # Check API key authentication
    if x_api_key and x_api_key == settings.API_KEY:
        return x_api_key
    
    # Neither authentication method succeeded
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either X-API-Key header or valid JWT token.",
    )
