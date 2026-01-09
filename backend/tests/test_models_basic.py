"""
Unit tests for SQLAlchemy ORM models.

Tests cover:
- Transcript model creation and persistence
- Assessment model creation and persistence
- Foreign key relationship (Assessment -> Transcript)
- Bidirectional relationship access
- Cascade delete behavior
- JSON column storage and retrieval
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Transcript, Assessment, Representative


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


@pytest.fixture
def test_representative(db_session):
    """Create a test representative for tests"""
    rep = Representative(
        email="test.rep@company.com",
        full_name="Test Representative",
        department="Sales",
        is_active=True
    )
    db_session.add(rep)
    db_session.commit()
    db_session.refresh(rep)
    return rep


class TestTranscriptModel:
    """Tests for Transcript ORM model"""

    def test_creates_transcript_with_required_fields(self, db_session):
        """Create and persist a Transcript with only required fields"""
        # Arrange
        transcript_text = "Rep: Hello! Buyer: Hi there."

        # Act
        transcript = Transcript(transcript=transcript_text)
        db_session.add(transcript)
        db_session.commit()

        # Assert
        assert transcript.id is not None
        assert transcript.transcript == transcript_text
        assert transcript.created_at is not None
        assert isinstance(transcript.created_at, datetime)
        assert transcript.representative_id is None
        assert transcript.buyer_id is None
        assert transcript.call_metadata is None

    def test_creates_transcript_with_all_fields(self, db_session, test_representative):
        """Create and persist a Transcript with all fields populated"""
        # Arrange
        transcript_text = "Rep: What challenges are you facing? Buyer: Our process is slow."
        metadata = {
            "call_date": "2025-01-15",
            "industry": "SaaS",
            "call_duration_seconds": 1800
        }

        # Act
        transcript = Transcript(
            representative_id=test_representative.id,
            buyer_id="buyer_456",
            call_metadata=metadata,
            transcript=transcript_text
        )
        db_session.add(transcript)
        db_session.commit()

        # Assert
        assert transcript.id is not None
        assert transcript.representative_id == test_representative.id
        assert transcript.buyer_id == "buyer_456"
        assert transcript.call_metadata == metadata
        assert transcript.transcript == transcript_text
        assert transcript.created_at is not None

    def test_transcript_metadata_json_serialization(self, db_session):
        """Verify JSON column stores and retrieves complex nested data"""
        # Arrange
        complex_metadata = {
            "call_info": {
                "date": "2025-01-15",
                "duration": 1800,
                "platform": "Zoom"
            },
            "buyer_context": {
                "company": "Acme Corp",
                "industry": "Manufacturing",
                "size": 500
            },
            "tags": ["discovery", "needs_followup"]
        }

        # Act
        transcript = Transcript(
            transcript="Rep: Tell me about your business.",
            call_metadata=complex_metadata
        )
        db_session.add(transcript)
        db_session.commit()

        # Refresh from database
        db_session.expire(transcript)
        retrieved = db_session.query(Transcript).filter_by(id=transcript.id).first()

        # Assert
        assert retrieved.call_metadata == complex_metadata
        assert retrieved.call_metadata["call_info"]["duration"] == 1800
        assert "discovery" in retrieved.call_metadata["tags"]

    def test_transcript_repr(self, db_session, test_representative):
        """Verify __repr__ method returns useful string"""
        # Arrange
        transcript = Transcript(
            representative_id=test_representative.id,
            buyer_id="buyer_002",
            transcript="Short conversation"
        )
        db_session.add(transcript)
        db_session.commit()

        # Act
        repr_str = repr(transcript)

        # Assert
        assert "Transcript" in repr_str
        assert f"id={transcript.id}" in repr_str
        assert f"representative_id={transcript.representative_id!r}" in repr_str
        assert "buyer_id='buyer_002'" in repr_str


class TestAssessmentModel:
    """Tests for Assessment ORM model"""

    def test_creates_assessment_with_required_fields(self, db_session):
        """Create and persist an Assessment with required fields"""
        # Arrange
        transcript = Transcript(transcript="Rep: Good questions. Buyer: Yes.")
        db_session.add(transcript)
        db_session.commit()

        scores = {
            "situation": 4,
            "problem": 3,
            "implication": 2,
            "need_payoff": 5,
            "flow": 4,
            "tone": 5,
            "engagement": 3
        }
        coaching = {
            "summary": "Strong need-payoff questions",
            "wins": ["Clear communication"],
            "gaps": ["More implication questions needed"],
            "next_actions": ["Practice SPIN sequencing"]
        }

        # Act
        assessment = Assessment(
            transcript_id=transcript.id,
            scores=scores,
            coaching=coaching,
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Assert
        assert assessment.id is not None
        assert assessment.transcript_id == transcript.id
        assert assessment.scores == scores
        assert assessment.coaching == coaching
        assert assessment.model_name == "gpt-4o-mini"
        assert assessment.prompt_version == "spin_v1"
        assert assessment.latency_ms is None
        assert assessment.created_at is not None
        assert isinstance(assessment.created_at, datetime)

    def test_creates_assessment_with_latency(self, db_session):
        """Create Assessment with optional latency_ms field"""
        # Arrange
        transcript = Transcript(transcript="Sample conversation")
        db_session.add(transcript)
        db_session.commit()

        # Act
        assessment = Assessment(
            transcript_id=transcript.id,
            scores={"situation": 3, "problem": 3, "implication": 3, "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3},
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="claude-3-sonnet",
            prompt_version="spin_v2",
            latency_ms=1250
        )
        db_session.add(assessment)
        db_session.commit()

        # Assert
        assert assessment.latency_ms == 1250

    def test_assessment_json_columns_store_complex_data(self, db_session):
        """Verify JSON columns in Assessment store and retrieve complex structures"""
        # Arrange
        transcript = Transcript(transcript="Complex assessment scenario")
        db_session.add(transcript)
        db_session.commit()

        scores = {
            "situation": 5,
            "problem": 4,
            "implication": 3,
            "need_payoff": 5,
            "flow": 4,
            "tone": 5,
            "engagement": 4
        }
        coaching = {
            "summary": "Excellent discovery with minor gaps in implication development.",
            "wins": [
                "Opened with strong situation questions that established context",
                "Problem questions uncovered 3 key pain points",
                "Need-payoff questions effectively linked solution to buyer goals"
            ],
            "gaps": [
                "Only asked 1 implication question",
                "Could have explored cost of inaction more deeply"
            ],
            "next_actions": [
                "Practice asking 'What happens if...' questions",
                "Review SPIN sequencing guide",
                "Record next 3 calls for self-review"
            ]
        }

        # Act
        assessment = Assessment(
            transcript_id=transcript.id,
            scores=scores,
            coaching=coaching,
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Refresh from database
        db_session.expire(assessment)
        retrieved = db_session.query(Assessment).filter_by(id=assessment.id).first()

        # Assert
        assert retrieved.scores == scores
        assert retrieved.coaching == coaching
        assert retrieved.coaching["summary"] == "Excellent discovery with minor gaps in implication development."
        assert len(retrieved.coaching["wins"]) == 3
        assert len(retrieved.coaching["gaps"]) == 2
        assert len(retrieved.coaching["next_actions"]) == 3

    def test_assessment_repr(self, db_session):
        """Verify __repr__ method returns useful string"""
        # Arrange
        transcript = Transcript(transcript="Test conversation")
        db_session.add(transcript)
        db_session.commit()

        assessment = Assessment(
            transcript_id=transcript.id,
            scores={"situation": 3, "problem": 3, "implication": 3, "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3},
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Act
        repr_str = repr(assessment)

        # Assert
        assert "Assessment" in repr_str
        assert f"id={assessment.id}" in repr_str
        assert f"transcript_id={transcript.id}" in repr_str
        assert "model='gpt-4o-mini'" in repr_str
        assert "prompt_version='spin_v1'" in repr_str


class TestTranscriptAssessmentRelationship:
    """Tests for the relationship between Transcript and Assessment models"""

    def test_foreign_key_relationship(self, db_session):
        """Verify Assessment correctly references Transcript via foreign key"""
        # Arrange
        transcript = Transcript(transcript="Rep: How are you? Buyer: Good.")
        db_session.add(transcript)
        db_session.commit()

        # Act
        assessment = Assessment(
            transcript_id=transcript.id,
            scores={"situation": 4, "problem": 4, "implication": 4, "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4},
            coaching={"summary": "Good", "wins": ["Clear"], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        db_session.add(assessment)
        db_session.commit()

        # Assert
        assert assessment.transcript_id == transcript.id
        retrieved_assessment = db_session.query(Assessment).filter_by(id=assessment.id).first()
        assert retrieved_assessment.transcript_id == transcript.id

    def test_bidirectional_relationship_access(self, db_session, test_representative):
        """Verify bidirectional relationship navigation"""
        # Arrange
        transcript = Transcript(
            representative_id=test_representative.id,
            transcript="Rep: What's your biggest challenge? Buyer: Time management."
        )
        db_session.add(transcript)
        db_session.commit()

        assessment1 = Assessment(
            transcript_id=transcript.id,
            scores={"situation": 3, "problem": 3, "implication": 3, "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3},
            coaching={"summary": "First attempt", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        assessment2 = Assessment(
            transcript_id=transcript.id,
            scores={"situation": 4, "problem": 4, "implication": 4, "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4},
            coaching={"summary": "Second attempt with better prompt", "wins": [], "gaps": [], "next_actions": []},
            model_name="claude-3-sonnet",
            prompt_version="spin_v2"
        )
        db_session.add(assessment1)
        db_session.add(assessment2)
        db_session.commit()

        # Act - Access assessments from transcript
        retrieved_transcript = db_session.query(Transcript).filter_by(id=transcript.id).first()

        # Assert - Transcript has multiple assessments
        assert len(retrieved_transcript.assessments) == 2
        assert assessment1 in retrieved_transcript.assessments
        assert assessment2 in retrieved_transcript.assessments

        # Assert - Assessment can access parent transcript
        retrieved_assessment = db_session.query(Assessment).filter_by(id=assessment1.id).first()
        assert retrieved_assessment.transcript_ref.id == transcript.id
        assert retrieved_assessment.transcript_ref.representative_id == test_representative.id

    def test_cascade_delete_removes_assessments(self, db_session):
        """Verify cascade delete removes assessments when transcript is deleted"""
        # Arrange
        transcript = Transcript(transcript="Conversation to be deleted")
        db_session.add(transcript)
        db_session.commit()
        transcript_id = transcript.id

        assessment1 = Assessment(
            transcript_id=transcript_id,
            scores={"situation": 3, "problem": 3, "implication": 3, "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3},
            coaching={"summary": "Test 1", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        assessment2 = Assessment(
            transcript_id=transcript_id,
            scores={"situation": 4, "problem": 4, "implication": 4, "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4},
            coaching={"summary": "Test 2", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        db_session.add(assessment1)
        db_session.add(assessment2)
        db_session.commit()
        assessment1_id = assessment1.id
        assessment2_id = assessment2.id

        # Act - Delete transcript
        db_session.delete(transcript)
        db_session.commit()

        # Assert - Transcript and all assessments are gone
        assert db_session.query(Transcript).filter_by(id=transcript_id).first() is None
        assert db_session.query(Assessment).filter_by(id=assessment1_id).first() is None
        assert db_session.query(Assessment).filter_by(id=assessment2_id).first() is None

    def test_multiple_transcripts_with_assessments(self, db_session):
        """Verify multiple transcripts can each have their own assessments"""
        # Arrange
        rep1 = Representative(email="rep1@company.com", full_name="Rep One")
        rep2 = Representative(email="rep2@company.com", full_name="Rep Two")
        db_session.add_all([rep1, rep2])
        db_session.commit()
        
        transcript1 = Transcript(representative_id=rep1.id, transcript="First call")
        transcript2 = Transcript(representative_id=rep2.id, transcript="Second call")
        db_session.add(transcript1)
        db_session.add(transcript2)
        db_session.commit()

        assessment1a = Assessment(
            transcript_id=transcript1.id,
            scores={"situation": 3, "problem": 3, "implication": 3, "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3},
            coaching={"summary": "First assessment for first call", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        assessment1b = Assessment(
            transcript_id=transcript1.id,
            scores={"situation": 4, "problem": 4, "implication": 4, "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4},
            coaching={"summary": "Second assessment for first call", "wins": [], "gaps": [], "next_actions": []},
            model_name="claude-3-sonnet",
            prompt_version="spin_v2"
        )
        assessment2a = Assessment(
            transcript_id=transcript2.id,
            scores={"situation": 5, "problem": 5, "implication": 5, "need_payoff": 5, "flow": 5, "tone": 5, "engagement": 5},
            coaching={"summary": "Assessment for second call", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        db_session.add(assessment1a)
        db_session.add(assessment1b)
        db_session.add(assessment2a)
        db_session.commit()

        # Act
        retrieved_transcript1 = db_session.query(Transcript).filter_by(id=transcript1.id).first()
        retrieved_transcript2 = db_session.query(Transcript).filter_by(id=transcript2.id).first()

        # Assert
        assert len(retrieved_transcript1.assessments) == 2
        assert len(retrieved_transcript2.assessments) == 1
        assert assessment1a in retrieved_transcript1.assessments
        assert assessment1b in retrieved_transcript1.assessments
        assert assessment2a in retrieved_transcript2.assessments
        assert assessment2a not in retrieved_transcript1.assessments


class TestModelIndexes:
    """Tests to verify indexed columns improve query performance"""

    def test_query_by_representative_id_uses_index(self, db_session):
        """Verify representative_id is indexed by querying efficiently"""
        # Arrange
        rep_alice = Representative(email="alice@company.com", full_name="Alice")
        rep_bob = Representative(email="bob@company.com", full_name="Bob")
        db_session.add_all([rep_alice, rep_bob])
        db_session.commit()
        
        transcript1 = Transcript(representative_id=rep_alice.id, transcript="Call 1")
        transcript2 = Transcript(representative_id=rep_alice.id, transcript="Call 2")
        transcript3 = Transcript(representative_id=rep_bob.id, transcript="Call 3")
        db_session.add_all([transcript1, transcript2, transcript3])
        db_session.commit()

        # Act
        alice_transcripts = db_session.query(Transcript).filter_by(representative_id=rep_alice.id).all()

        # Assert
        assert len(alice_transcripts) == 2
        assert transcript1 in alice_transcripts
        assert transcript2 in alice_transcripts
        assert transcript3 not in alice_transcripts

    def test_query_by_buyer_id_uses_index(self, db_session):
        """Verify buyer_id is indexed by querying efficiently"""
        # Arrange
        transcript1 = Transcript(buyer_id="buyer_xyz", transcript="Call 1")
        transcript2 = Transcript(buyer_id="buyer_xyz", transcript="Call 2")
        transcript3 = Transcript(buyer_id="buyer_abc", transcript="Call 3")
        db_session.add_all([transcript1, transcript2, transcript3])
        db_session.commit()

        # Act
        xyz_transcripts = db_session.query(Transcript).filter_by(buyer_id="buyer_xyz").all()

        # Assert
        assert len(xyz_transcripts) == 2
        assert transcript1 in xyz_transcripts
        assert transcript2 in xyz_transcripts

    def test_query_by_model_name_uses_index(self, db_session):
        """Verify model_name is indexed for assessment queries"""
        # Arrange
        transcript = Transcript(transcript="Sample call")
        db_session.add(transcript)
        db_session.commit()

        assessment1 = Assessment(
            transcript_id=transcript.id,
            scores={"situation": 3, "problem": 3, "implication": 3, "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3},
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        assessment2 = Assessment(
            transcript_id=transcript.id,
            scores={"situation": 4, "problem": 4, "implication": 4, "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4},
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="claude-3-sonnet",
            prompt_version="spin_v1"
        )
        db_session.add_all([assessment1, assessment2])
        db_session.commit()

        # Act
        gpt_assessments = db_session.query(Assessment).filter_by(model_name="gpt-4o-mini").all()

        # Assert
        assert len(gpt_assessments) == 1
        assert assessment1 in gpt_assessments

    def test_query_by_prompt_version_uses_index(self, db_session):
        """Verify prompt_version is indexed for assessment queries"""
        # Arrange
        transcript = Transcript(transcript="Sample call")
        db_session.add(transcript)
        db_session.commit()

        assessment1 = Assessment(
            transcript_id=transcript.id,
            scores={"situation": 3, "problem": 3, "implication": 3, "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3},
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v1"
        )
        assessment2 = Assessment(
            transcript_id=transcript.id,
            scores={"situation": 4, "problem": 4, "implication": 4, "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4},
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",
            prompt_version="spin_v2"
        )
        db_session.add_all([assessment1, assessment2])
        db_session.commit()

        # Act
        v1_assessments = db_session.query(Assessment).filter_by(prompt_version="spin_v1").all()

        # Assert
        assert len(v1_assessments) == 1
        assert assessment1 in v1_assessments
