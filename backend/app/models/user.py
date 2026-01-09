"""
User model for authentication and authorization.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UUID(TypeDecorator):
    """
    Platform-independent UUID type.

    Uses PostgreSQL UUID type when available, otherwise uses CHAR(36) for SQLite.
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value) if not isinstance(value, uuid.UUID) else value
        else:
            return str(value) if value else None

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return (
                uuid.UUID(value) if not isinstance(value, uuid.UUID) else value
            )


class User(Base):
    """
    User model for authentication.

    Stores user credentials, profile information, and access control flags.
    """

    __tablename__ = "users"

    id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique user identifier",
    )
    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique)",
    )
    hashed_password = Column(
        String, nullable=False, comment="Bcrypt hashed password"
    )
    full_name = Column(String, nullable=True, comment="User's full name")
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether user account is active",
    )
    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user has superuser privileges",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Account creation timestamp",
    )

    # Organization relationship
    organization_id = Column(
        UUID(),
        ForeignKey("organizations.id"),
        nullable=True,  # Nullable initially for migration; will be required in app logic
        index=True,
        comment="Organization this user belongs to",
    )
    organization = relationship("Organization", back_populates="users")
