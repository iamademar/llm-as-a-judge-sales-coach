"""
Unit tests for Representative CRUD operations.

Tests cover:
- Creating representatives
- Querying by ID, email
- Listing all/active representatives
- Updating representatives
- Deactivating representatives
- Email uniqueness constraint
"""

import pytest
from datetime import datetime, timezone

from app.models import Representative, User
from app.crud import representative as rep_crud


class TestRepresentativeCRUD:
    """Tests for Representative CRUD operations"""

    def test_create_representative_minimal(self, db_session):
        """Test creating a representative with minimal required fields"""
        # Act
        rep = rep_crud.create(
            db_session,
            email="john@company.com",
            full_name="John Doe"
        )

        # Assert
        assert rep.id is not None
        assert rep.email == "john@company.com"
        assert rep.full_name == "John Doe"
        assert rep.department is None
        assert rep.is_active is True
        assert rep.hire_date is None

    def test_create_representative_with_all_fields(self, db_session):
        """Test creating a representative with all fields"""
        # Arrange
        hire_date = datetime(2023, 6, 1, tzinfo=timezone.utc)

        # Act
        rep = rep_crud.create(
            db_session,
            email="jane@company.com",
            full_name="Jane Smith",
            department="Enterprise Sales",
            hire_date=hire_date
        )

        # Assert
        assert rep.id is not None
        assert rep.email == "jane@company.com"
        assert rep.full_name == "Jane Smith"
        assert rep.department == "Enterprise Sales"
        # SQLite doesn't preserve timezone, so compare date/time values only
        assert rep.hire_date.replace(tzinfo=None) == hire_date.replace(tzinfo=None)
        assert rep.is_active is True

    def test_create_normalizes_email(self, db_session):
        """Test that create normalizes email (lowercase, strip)"""
        # Act
        rep = rep_crud.create(
            db_session,
            email="  JOHN.DOE@Company.COM  ",
            full_name="John Doe"
        )

        # Assert
        assert rep.email == "john.doe@company.com"

    def test_get_by_id(self, db_session):
        """Test retrieving representative by ID"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="test@company.com",
            full_name="Test Rep"
        )

        # Act
        retrieved = rep_crud.get_by_id(db_session, rep.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == rep.id
        assert retrieved.email == rep.email

    def test_get_by_id_returns_none_if_not_found(self, db_session):
        """Test that get_by_id returns None for non-existent ID"""
        # Arrange
        import uuid
        fake_id = uuid.uuid4()

        # Act
        result = rep_crud.get_by_id(db_session, fake_id)

        # Assert
        assert result is None

    def test_get_by_email(self, db_session):
        """Test retrieving representative by email"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="email@company.com",
            full_name="Email Test"
        )

        # Act
        retrieved = rep_crud.get_by_email(db_session, "email@company.com")

        # Assert
        assert retrieved is not None
        assert retrieved.id == rep.id
        assert retrieved.email == rep.email

    def test_get_by_email_normalizes_input(self, db_session):
        """Test that get_by_email normalizes the search email"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="test@company.com",
            full_name="Test"
        )

        # Act - Search with different case and whitespace
        retrieved = rep_crud.get_by_email(db_session, "  TEST@Company.COM  ")

        # Assert
        assert retrieved is not None
        assert retrieved.id == rep.id

    def test_get_by_email_returns_none_if_not_found(self, db_session):
        """Test that get_by_email returns None for non-existent email"""
        # Act
        result = rep_crud.get_by_email(db_session, "nonexistent@company.com")

        # Assert
        assert result is None

    def test_get_all(self, db_session):
        """Test retrieving all representatives"""
        # Arrange
        rep1 = rep_crud.create(db_session, email="rep1@company.com", full_name="Rep 1")
        rep2 = rep_crud.create(db_session, email="rep2@company.com", full_name="Rep 2")
        rep3 = rep_crud.create(db_session, email="rep3@company.com", full_name="Rep 3")

        # Act
        all_reps = rep_crud.get_all(db_session)

        # Assert
        assert len(all_reps) == 3
        assert rep1 in all_reps
        assert rep2 in all_reps
        assert rep3 in all_reps

    def test_get_all_with_pagination(self, db_session):
        """Test pagination with skip and limit"""
        # Arrange
        for i in range(10):
            rep_crud.create(db_session, email=f"rep{i}@company.com", full_name=f"Rep {i}")

        # Act
        page1 = rep_crud.get_all(db_session, skip=0, limit=5)
        page2 = rep_crud.get_all(db_session, skip=5, limit=5)

        # Assert
        assert len(page1) == 5
        assert len(page2) == 5
        # Ensure no overlap
        page1_ids = {r.id for r in page1}
        page2_ids = {r.id for r in page2}
        assert len(page1_ids & page2_ids) == 0

    def test_get_active(self, db_session):
        """Test retrieving only active representatives"""
        # Arrange
        rep1 = rep_crud.create(db_session, email="active1@company.com", full_name="Active 1")
        rep2 = rep_crud.create(db_session, email="active2@company.com", full_name="Active 2")
        rep3 = rep_crud.create(db_session, email="inactive@company.com", full_name="Inactive")
        
        # Deactivate rep3
        rep3.is_active = False
        db_session.commit()

        # Act
        active_reps = rep_crud.get_active(db_session)

        # Assert
        assert len(active_reps) == 2
        assert rep1 in active_reps
        assert rep2 in active_reps
        assert rep3 not in active_reps

    def test_update_representative(self, db_session):
        """Test updating representative fields"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="original@company.com",
            full_name="Original Name",
            department="SMB Sales"
        )

        # Act
        updated = rep_crud.update(
            db_session,
            db_obj=rep,
            email="updated@company.com",
            full_name="Updated Name",
            department="Enterprise Sales"
        )

        # Assert
        assert updated.id == rep.id
        assert updated.email == "updated@company.com"
        assert updated.full_name == "Updated Name"
        assert updated.department == "Enterprise Sales"

    def test_update_partial_fields(self, db_session):
        """Test updating only some fields (partial update)"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="test@company.com",
            full_name="Test Rep",
            department="Sales"
        )
        original_email = rep.email
        original_department = rep.department

        # Act - Update only full_name
        updated = rep_crud.update(
            db_session,
            db_obj=rep,
            full_name="New Name"
        )

        # Assert
        assert updated.full_name == "New Name"
        assert updated.email == original_email  # unchanged
        assert updated.department == original_department  # unchanged

    def test_deactivate_representative(self, db_session):
        """Test deactivating a representative"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="active@company.com",
            full_name="Active Rep"
        )
        assert rep.is_active is True

        # Act
        deactivated = rep_crud.deactivate(db_session, db_obj=rep)

        # Assert
        assert deactivated.id == rep.id
        assert deactivated.is_active is False

    def test_email_uniqueness_constraint(self, db_session):
        """Test that duplicate emails are not allowed"""
        # Arrange
        rep_crud.create(
            db_session,
            email="duplicate@company.com",
            full_name="First Rep"
        )

        # Act & Assert
        with pytest.raises(Exception):  # Should raise IntegrityError
            rep_crud.create(
                db_session,
                email="duplicate@company.com",
                full_name="Second Rep"
            )

    def test_update_email_normalizes(self, db_session):
        """Test that update normalizes email"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="original@company.com",
            full_name="Test"
        )

        # Act
        updated = rep_crud.update(
            db_session,
            db_obj=rep,
            email="  UPDATED@Company.COM  "
        )

        # Assert
        assert updated.email == "updated@company.com"

