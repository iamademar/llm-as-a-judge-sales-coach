"""
JWT authentication dependency for FastAPI routes.

Provides get_current_user dependency that validates JWT access tokens
and returns the authenticated user.
"""
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.jwt_tokens import decode_token
from app.crud import user as user_crud
from app.routers.deps import get_db
from app.models.user import User

# HTTPBearer security scheme for extracting Bearer tokens
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Dependency to get the current authenticated user from JWT access token.

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User object if authentication succeeds

    Raises:
        HTTPException(401): If token is invalid, expired, wrong type,
                           user not found, or user is inactive

    Usage:
        @router.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    token = credentials.credentials

    # Decode and validate token
    try:
        payload = decode_token(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type is "access"
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user email from subject claim
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Lookup user in database
    user = user_crud.get_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_optional)],
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    """
    Optional dependency to get the current authenticated user from JWT access token.
    
    Returns None if no token is provided or if authentication fails.
    Does not raise exceptions - use this for optional authentication.

    Args:
        credentials: Optional HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User object if authentication succeeds, None otherwise

    Usage:
        @router.get("/maybe-protected")
        def maybe_protected_route(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"user_id": user.id}
            return {"message": "Anonymous access"}
    """
    if not credentials:
        return None
    
    token = credentials.credentials

    # Decode and validate token
    try:
        payload = decode_token(token)
    except InvalidTokenError:
        return None

    # Verify token type is "access"
    token_type = payload.get("type")
    if token_type != "access":
        return None

    # Extract user email from subject claim
    email = payload.get("sub")
    if email is None:
        return None

    # Lookup user in database
    user = user_crud.get_by_email(db, email=email)
    if user is None:
        return None

    # Verify user is active
    if not user.is_active:
        return None

    return user
