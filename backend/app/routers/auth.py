"""
Authentication router for user registration, login, and token management.

Endpoints:
- POST /auth/register: Register new user
- POST /auth/login: Login with credentials, get token pair
- GET /auth/me: Get current user info (requires access token)
- POST /auth/refresh: Refresh access token using refresh token
"""
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.jwt_dependency import get_current_user
from app.core.jwt_tokens import create_access_token, create_refresh_token, decode_token
from app.crud import user as user_crud
from app.crud import organization as org_crud
from app.routers.deps import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserCreate, UserOut
from app.schemas.organization import OrganizationOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserOut:
    """
    Register a new user with organization.

    User must either:
    - Create a new organization (provide organization_name)
    - Join existing organization (provide organization_id)

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user data (excluding password)

    Raises:
        HTTPException(400): If email exists, org name taken, or org not found
    """
    # Check if user already exists
    existing_user = user_crud.get_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Handle organization assignment
    organization_id: uuid.UUID

    if user_data.organization_name:
        # Create new organization
        existing_org = org_crud.get_by_name(db, name=user_data.organization_name)
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization name '{user_data.organization_name}' is already taken",
            )

        new_org = org_crud.create(
            db,
            name=user_data.organization_name,
            description=None
        )
        organization_id = new_org.id

    else:  # user_data.organization_id
        # Join existing organization
        org = org_crud.get_by_id(db, id=user_data.organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found",
            )
        if not org.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization is not active",
            )
        organization_id = org.id

    # Create user with organization
    user = user_crud.create(
        db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        organization_id=organization_id,
    )

    return UserOut.model_validate(user)


@router.get("/organizations", response_model=List[OrganizationOut])
def list_organizations(
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
) -> List[OrganizationOut]:
    """
    List active organizations (for registration form).

    Args:
        db: Database session
        skip: Pagination offset
        limit: Max results to return

    Returns:
        List of active organizations
    """
    orgs = org_crud.get_active(db, skip=skip, limit=limit)
    return [OrganizationOut.model_validate(org) for org in orgs]


@router.post("/login", response_model=TokenPair)
def login(
    credentials: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenPair:
    """
    Login with email and password.

    Args:
        credentials: Login credentials (email, password)
        db: Database session

    Returns:
        JWT token pair (access_token, refresh_token)

    Raises:
        HTTPException(401): If credentials are invalid
    """
    # Authenticate user
    user = user_crud.authenticate(
        db, email=credentials.email, password=credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    access_token = create_access_token(sub=user.email)
    refresh_token = create_refresh_token(sub=user.email)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserOut)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserOut:
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from JWT token (dependency)

    Returns:
        Current user data (excluding password)

    Note:
        Requires valid access token in Authorization header
    """
    return UserOut.model_validate(current_user)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    refresh_data: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenPair:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token data
        db: Database session

    Returns:
        New JWT token pair

    Raises:
        HTTPException(401): If refresh token is invalid or wrong type
    """
    # Decode and validate refresh token
    try:
        payload = decode_token(refresh_data.refresh_token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type is "refresh"
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user email
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user exists and is active
    user = user_crud.get_by_email(db, email=email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new token pair
    access_token = create_access_token(sub=user.email)
    refresh_token = create_refresh_token(sub=user.email)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )
