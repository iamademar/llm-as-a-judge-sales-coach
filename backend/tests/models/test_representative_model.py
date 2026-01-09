"""
Unit tests for Representative ORM model.

Tests cover:
- Representative model creation and persistence
- User linkage (optional FK)
- Relationships (user, transcripts)
- Field validation
"""

import pytest
from datetime import datetime, timezone

from app.models import Representative, User, Transcript


class TestRepresentativeModel:
    """Tests for Representative ORM model"""

    def test_creates_representative_with_required_fields(self, db_session):
        """Create and persist a Representative with only required fields"""
        # Act
        rep = Representative(
            email="john.doe@company.com",
            full_name="John Doe"
        )
        db_session.add(rep)
        db_session.commit()

        # Assert
        assert rep.id is not None
        assert rep.email == "john.doe@company.com"
        assert rep.full_name == "John Doe"
        assert rep.department is None
        assert rep.is_active is True  # default
        assert rep.hire_date is None
        assert rep.created_at is not None
        assert isinstance(rep.created_at, datetime)

    def test_creates_representative_with_all_fields(self, db_session):
        """Create and persist a Representative with all fields populated"""
        # Arrange
        hire_date = datetime(2023, 1, 15, tzinfo=timezone.utc)

        # Act
        rep = Representative(
            email="john.doe@company.com",
            full_name="John Doe",
            department="Enterprise Sales",
            is_active=True,
            hire_date=hire_date
        )
        db_session.add(rep)
        db_session.commit()

        # Assert
        assert rep.id is not None
        assert rep.email == "john.doe@company.com"
        assert rep.full_name == "John Doe"
        assert rep.department == "Enterprise Sales"
        assert rep.is_active is True
        # SQLite doesn't preserve timezone, so compare date/time values only
        assert rep.hire_date.replace(tzinfo=None) == hire_date.replace(tzinfo=None)
        assert rep.created_at is not None

    def test_representative_email_must_be_unique(self, db_session):
        """Verify email uniqueness constraint"""
        # Arrange
        rep1 = Representative(
            email="duplicate@company.com",
            full_name="First Rep"
        )
        db_session.add(rep1)
        db_session.commit()

        # Act & Assert
        rep2 = Representative(
            email="duplicate@company.com",
            full_name="Second Rep"
        )
        db_session.add(rep2)
        
        with pytest.raises(Exception):  # SQLite raises IntegrityError
            db_session.commit()

    def test_representative_transcripts_relationship(self, db_session):
        """Test relationship with Transcript model"""
        # Arrange
        rep = Representative(
            email="sales@company.com",
            full_name="Sales Rep"
        )
        db_session.add(rep)
        db_session.commit()

        # Add transcripts
        t1 = Transcript(
            representative_id=rep.id,
            transcript="First conversation",
            buyer_id="buyer1"
        )
        t2 = Transcript(
            representative_id=rep.id,
            transcript="Second conversation",
            buyer_id="buyer2"
        )
        db_session.add_all([t1, t2])
        db_session.commit()

        # Act
        retrieved_rep = db_session.query(Representative).filter_by(id=rep.id).first()

        # Assert
        assert len(retrieved_rep.transcripts) == 2
        assert t1 in retrieved_rep.transcripts
        assert t2 in retrieved_rep.transcripts

    def test_cascade_delete_removes_transcripts(self, db_session):
        """Verify cascade delete removes transcripts when representative is deleted"""
        # Arrange
        rep = Representative(
            email="temp@company.com",
            full_name="Temporary Rep"
        )
        db_session.add(rep)
        db_session.commit()

        t1 = Transcript(representative_id=rep.id, transcript="Call 1")
        t2 = Transcript(representative_id=rep.id, transcript="Call 2")
        db_session.add_all([t1, t2])
        db_session.commit()

        rep_id = rep.id

        # Act - Delete representative
        db_session.delete(rep)
        db_session.commit()

        # Assert - Transcripts should be deleted
        transcripts = db_session.query(Transcript).filter_by(representative_id=rep_id).all()
        assert len(transcripts) == 0

    def test_representative_repr(self, db_session):
        """Verify __repr__ method returns useful string"""
        # Arrange
        rep = Representative(
            email="test@company.com",
            full_name="Test Representative",
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        # Act
        repr_str = repr(rep)

        # Assert
        assert "Representative" in repr_str
        assert f"id={rep.id}" in repr_str
        assert "name='Test Representative'" in repr_str
        assert "email='test@company.com'" in repr_str
        assert "is_active=True" in repr_str

    def test_deactivate_representative(self, db_session):
        """Test deactivating a representative"""
        # Arrange
        rep = Representative(
            email="active@company.com",
            full_name="Active Rep",
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        # Act
        rep.is_active = False
        db_session.commit()

        # Assert
        retrieved_rep = db_session.query(Representative).filter_by(id=rep.id).first()
        assert retrieved_rep.is_active is False

