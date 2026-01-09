"""
Unit tests for User SQLAlchemy ORM model.

Tests cover:
- User model creation and persistence
- Email uniqueness constraint
- Default values for boolean fields
- Created_at timestamp generation
- UUID primary key generation
"""

import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.models import User


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a database session for each test"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


class TestUserModel:
    """Tests for User ORM model"""

    def test_creates_user_and_queries_it_back(self, db_session):
        """Create and persist a User, then query it back"""
        # Arrange
        email = "test@example.com"
        hashed_password = "$2b$12$abcd1234"
        full_name = "Test User"

        # Act
        user = User(
            email=email, hashed_password=hashed_password, full_name=full_name
        )
        db_session.add(user)
        db_session.commit()

        # Query back
        retrieved_user = db_session.query(User).filter_by(email=email).first()

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.email == email
        assert retrieved_user.hashed_password == hashed_password
        assert retrieved_user.full_name == full_name
        assert retrieved_user.is_active is True  # Default value
        assert retrieved_user.is_superuser is False  # Default value
        assert retrieved_user.created_at is not None
        assert isinstance(retrieved_user.id, uuid.UUID)

    def test_user_email_uniqueness_constraint(self, db_session):
        """Test that duplicate email addresses raise IntegrityError"""
        # Arrange
        email = "duplicate@example.com"
        user1 = User(email=email, hashed_password="hash1")
        user2 = User(email=email, hashed_password="hash2")

        # Act
        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)

        # Assert
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_creates_user_with_minimal_fields(self, db_session):
        """Create user with only required fields (email and password)"""
        # Arrange
        email = "minimal@example.com"
        hashed_password = "$2b$12$xyz789"

        # Act
        user = User(email=email, hashed_password=hashed_password)
        db_session.add(user)
        db_session.commit()

        # Assert
        retrieved_user = db_session.query(User).filter_by(email=email).first()
        assert retrieved_user is not None
        assert retrieved_user.email == email
        assert retrieved_user.full_name is None
        assert retrieved_user.is_active is True
        assert retrieved_user.is_superuser is False

    def test_user_with_custom_flags(self, db_session):
        """Create user with custom is_active and is_superuser flags"""
        # Arrange
        email = "admin@example.com"
        user = User(
            email=email,
            hashed_password="hash123",
            is_active=False,
            is_superuser=True,
        )

        # Act
        db_session.add(user)
        db_session.commit()

        # Assert
        retrieved_user = db_session.query(User).filter_by(email=email).first()
        assert retrieved_user.is_active is False
        assert retrieved_user.is_superuser is True

    def test_user_id_is_uuid(self, db_session):
        """Test that user ID is generated as UUID"""
        # Arrange
        user = User(email="uuid@example.com", hashed_password="hash")

        # Act
        db_session.add(user)
        db_session.commit()

        # Assert
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
