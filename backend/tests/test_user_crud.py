"""
Unit tests for User CRUD operations.

Tests cover:
- User creation with password hashing
- Authentication (success and failure cases)
- Email normalization (lowercase, strip)
- get_by_email lookups
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.crud import user as user_crud
from app.models.user import User


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


class TestUserCRUD:
    """Tests for user CRUD operations"""

    def test_create_user(self, db_session):
        """Test creating a user with hashed password"""
        # Arrange
        email = "test@example.com"
        password = "securepassword123"
        full_name = "Test User"

        # Act
        user = user_crud.create(
            db_session, email=email, password=password, full_name=full_name
        )

        # Assert
        assert user.id is not None
        assert user.email == email
        assert user.full_name == full_name
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.hashed_password != password  # Password should be hashed
        assert len(user.hashed_password) > 0

    def test_create_user_with_superuser_flag(self, db_session):
        """Test creating a superuser"""
        # Arrange
        email = "admin@example.com"
        password = "adminpass123"

        # Act
        user = user_crud.create(
            db_session,
            email=email,
            password=password,
            is_superuser=True,
        )

        # Assert
        assert user.is_superuser is True
        assert user.is_active is True

    def test_get_by_email_found(self, db_session):
        """Test getting a user by email when user exists"""
        # Arrange
        email = "find@example.com"
        password = "password123"
        user_crud.create(db_session, email=email, password=password)

        # Act
        found_user = user_crud.get_by_email(db_session, email)

        # Assert
        assert found_user is not None
        assert found_user.email == email

    def test_get_by_email_not_found(self, db_session):
        """Test getting a user by email when user doesn't exist"""
        # Act
        found_user = user_crud.get_by_email(db_session, "nonexistent@example.com")

        # Assert
        assert found_user is None

    def test_get_by_email_normalization_lowercase(self, db_session):
        """Test email normalization: lookup with different case"""
        # Arrange
        email = "test@example.com"
        password = "password123"
        user_crud.create(db_session, email=email, password=password)

        # Act - query with uppercase
        found_user = user_crud.get_by_email(db_session, "TEST@EXAMPLE.COM")

        # Assert
        assert found_user is not None
        assert found_user.email == email

    def test_get_by_email_normalization_strip(self, db_session):
        """Test email normalization: strip whitespace"""
        # Arrange
        email = "test@example.com"
        password = "password123"
        user_crud.create(db_session, email=email, password=password)

        # Act - query with whitespace
        found_user = user_crud.get_by_email(db_session, "  test@example.com  ")

        # Assert
        assert found_user is not None
        assert found_user.email == email

    def test_create_normalizes_email(self, db_session):
        """Test that create() normalizes email on insertion"""
        # Arrange
        email_with_caps_and_spaces = "  Test@Example.COM  "
        password = "password123"

        # Act
        user = user_crud.create(db_session, email=email_with_caps_and_spaces, password=password)

        # Assert
        assert user.email == "test@example.com"

    def test_authenticate_success(self, db_session):
        """Test successful authentication with correct credentials"""
        # Arrange
        email = "auth@example.com"
        password = "correctpassword123"
        user_crud.create(db_session, email=email, password=password)

        # Act
        authenticated_user = user_crud.authenticate(
            db_session, email=email, password=password
        )

        # Assert
        assert authenticated_user is not None
        assert authenticated_user.email == email

    def test_authenticate_wrong_password(self, db_session):
        """Test authentication fails with wrong password"""
        # Arrange
        email = "auth@example.com"
        correct_password = "correctpassword123"
        wrong_password = "wrongpassword456"
        user_crud.create(db_session, email=email, password=correct_password)

        # Act
        authenticated_user = user_crud.authenticate(
            db_session, email=email, password=wrong_password
        )

        # Assert
        assert authenticated_user is None

    def test_authenticate_nonexistent_user(self, db_session):
        """Test authentication fails for nonexistent user"""
        # Act
        authenticated_user = user_crud.authenticate(
            db_session, email="nonexistent@example.com", password="anypassword"
        )

        # Assert
        assert authenticated_user is None

    def test_authenticate_with_normalized_email(self, db_session):
        """Test authentication works with normalized email"""
        # Arrange
        email = "auth@example.com"
        password = "password123"
        user_crud.create(db_session, email=email, password=password)

        # Act - authenticate with uppercase email
        authenticated_user = user_crud.authenticate(
            db_session, email="AUTH@EXAMPLE.COM", password=password
        )

        # Assert
        assert authenticated_user is not None
        assert authenticated_user.email == email
