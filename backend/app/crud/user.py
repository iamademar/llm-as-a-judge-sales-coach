"""
CRUD operations for User model.

Provides functions for creating, reading, and authenticating users.
"""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.passwords import hash_password, verify_password
from app.models.user import User


def get_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email address.

    Args:
        db: Database session
        email: User email address (will be normalized)

    Returns:
        User object if found, None otherwise

    Note:
        Email is normalized (lowercased and stripped) for consistent lookups
    """
    normalized_email = email.strip().lower()
    return db.query(User).filter(User.email == normalized_email).first()


def create(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    is_superuser: bool = False,
    organization_id: Optional[uuid.UUID] = None
) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        email: User email address (will be normalized)
        password: Plain text password (will be hashed)
        full_name: Optional full name
        is_superuser: Whether user has superuser privileges
        organization_id: Optional organization UUID this user belongs to

    Returns:
        Created User object

    Note:
        - Email is normalized (lowercased and stripped)
        - Password is hashed using bcrypt before storage
        - is_active defaults to True (from model default)
    """
    normalized_email = email.strip().lower()
    hashed_password = hash_password(password)

    user = User(
        email=normalized_email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_superuser=is_superuser,
        organization_id=organization_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(
    db: Session, *, email: str, password: str
) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User email address
        password: Plain text password to verify

    Returns:
        User object if authentication succeeds, None otherwise

    Note:
        Returns None if user not found or password doesn't match
    """
    user = get_by_email(db, email)
    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
