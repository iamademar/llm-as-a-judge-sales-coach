"""
Integration tests for transcript API endpoints.

Tests cover:
- Creating transcripts (success, with/without representative, auth required)
- Listing transcripts (all, pagination, filtering by representative)
- Getting transcript by ID (success, not found)
- Authentication and authorization checks
"""
import pytest

from app.models import Transcript
from app.crud import transcript as transcript_crud
from app.crud import representative as rep_crud


class TestCreateTranscript:
    """Tests for POST /transcripts"""

    def test_create_transcript_success(self, test_client, auth_headers, db_session):
        """Test successful transcript creation"""
        # Arrange
        payload = {
            "buyer_id": "ACME-001",
            "metadata": {"call_date": "2024-01-15", "industry": "SaaS"},
            "transcript": "Rep: Hello, how are you?\nBuyer: I'm great, thanks!"
        }

        # Act
        response = test_client.post(
            "/transcripts",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["buyer_id"] == payload["buyer_id"]
        assert data["metadata"] == payload["metadata"]
        assert data["transcript"] == payload["transcript"]
        assert data["representative_id"] is None
        assert "id" in data
        assert "created_at" in data

    def test_create_transcript_with_representative(self, test_client, auth_headers, db_session):
        """Test creating transcript with representative_id"""
        # Arrange - Create a representative
        rep = rep_crud.create(
            db_session,
            email="rep@company.com",
            full_name="Test Rep"
        )

        payload = {
            "representative_id": str(rep.id),
            "buyer_id": "ACME-002",
            "transcript": "Rep: Hello!\nBuyer: Hi!"
        }

        # Act
        response = test_client.post(
            "/transcripts",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["representative_id"] == str(rep.id)
        assert data["buyer_id"] == payload["buyer_id"]

    def test_create_transcript_minimal_fields(self, test_client, auth_headers, db_session):
        """Test creating transcript with only required field (transcript text)"""
        # Arrange
        payload = {
            "transcript": "Minimal transcript content"
        }

        # Act
        response = test_client.post(
            "/transcripts",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["transcript"] == payload["transcript"]
        assert data["buyer_id"] is None
        assert data["representative_id"] is None
        assert data["metadata"] is None

    def test_create_transcript_invalid_representative_id(self, test_client, auth_headers, db_session):
        """Test that invalid representative_id UUID format returns 400"""
        # Arrange
        payload = {
            "representative_id": "not-a-uuid",
            "transcript": "Test transcript"
        }

        # Act
        response = test_client.post(
            "/transcripts",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        # Check both possible error formats
        error_message = data.get("detail") or data.get("error", {}).get("message", "")
        assert "Invalid representative_id UUID format" in str(error_message)

    def test_create_transcript_requires_auth(self, test_client, db_session):
        """Test that creating transcript requires authentication"""
        # Arrange
        payload = {
            "transcript": "Test transcript"
        }

        # Act
        response = test_client.post(
            "/transcripts",
            json=payload
        )

        # Assert
        assert response.status_code in [401, 403]  # FastAPI JWT returns 403

    def test_create_transcript_missing_required_field(self, test_client, auth_headers, db_session):
        """Test that missing transcript field returns 422"""
        # Arrange
        payload = {
            "buyer_id": "ACME-001"
            # Missing "transcript" field
        }

        # Act
        response = test_client.post(
            "/transcripts",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 422


class TestListTranscripts:
    """Tests for GET /transcripts"""

    def test_list_transcripts_success(self, test_client, auth_headers, db_session):
        """Test listing all transcripts"""
        # Arrange - Create some transcripts
        for i in range(3):
            transcript_crud.create(
                db_session,
                transcript=f"Transcript {i}"
            )

        # Act
        response = test_client.get(
            "/transcripts",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_list_transcripts_pagination(self, test_client, auth_headers, db_session):
        """Test transcript listing with pagination"""
        # Arrange - Create transcripts
        for i in range(5):
            transcript_crud.create(
                db_session,
                transcript=f"Transcript {i}"
            )

        # Act
        response = test_client.get(
            "/transcripts?skip=2&limit=2",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2

    def test_list_transcripts_filter_by_representative(self, test_client, auth_headers, db_session):
        """Test filtering transcripts by representative_id"""
        # Arrange - Create representatives and transcripts
        rep1 = rep_crud.create(
            db_session,
            email="rep1@company.com",
            full_name="Rep 1"
        )
        rep2 = rep_crud.create(
            db_session,
            email="rep2@company.com",
            full_name="Rep 2"
        )

        # Create transcripts for rep1
        for i in range(2):
            transcript_crud.create(
                db_session,
                representative_id=rep1.id,
                transcript=f"Rep1 transcript {i}"
            )

        # Create transcripts for rep2
        transcript_crud.create(
            db_session,
            representative_id=rep2.id,
            transcript="Rep2 transcript"
        )

        # Act - Filter by rep1
        response = test_client.get(
            f"/transcripts?representative_id={rep1.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for transcript in data:
            assert transcript["representative_id"] == str(rep1.id)

    def test_list_transcripts_invalid_representative_id(self, test_client, auth_headers, db_session):
        """Test that invalid representative_id format returns 400"""
        # Act
        response = test_client.get(
            "/transcripts?representative_id=not-a-uuid",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        # Check both possible error formats
        error_message = data.get("detail") or data.get("error", {}).get("message", "")
        assert "Invalid representative_id UUID format" in str(error_message)

    def test_list_transcripts_requires_auth(self, test_client, db_session):
        """Test that listing transcripts requires authentication"""
        # Act
        response = test_client.get("/transcripts")

        # Assert
        assert response.status_code in [401, 403]  # FastAPI JWT returns 403


class TestGetTranscript:
    """Tests for GET /transcripts/{transcript_id}"""

    def test_get_transcript_success(self, test_client, auth_headers, db_session):
        """Test getting a transcript by ID"""
        # Arrange
        transcript = transcript_crud.create(
            db_session,
            buyer_id="ACME-001",
            transcript="Test transcript content"
        )

        # Act
        response = test_client.get(
            f"/transcripts/{transcript.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transcript.id
        assert data["buyer_id"] == "ACME-001"
        assert data["transcript"] == "Test transcript content"

    def test_get_transcript_not_found(self, test_client, auth_headers, db_session):
        """Test that getting non-existent transcript returns 404"""
        # Act
        response = test_client.get(
            "/transcripts/99999",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        # Check both possible error formats
        error_message = data.get("detail") or data.get("error", {}).get("message", "")
        assert "Transcript not found" in str(error_message)

    def test_get_transcript_requires_auth(self, test_client, db_session):
        """Test that getting transcript requires authentication"""
        # Arrange
        transcript = transcript_crud.create(
            db_session,
            transcript="Test transcript"
        )

        # Act
        response = test_client.get(f"/transcripts/{transcript.id}")

        # Assert
        assert response.status_code in [401, 403]  # FastAPI JWT returns 403


class TestTranscriptIntegration:
    """Integration tests combining multiple operations"""

    def test_create_and_retrieve_workflow(self, test_client, auth_headers, db_session):
        """Test creating and then retrieving a transcript"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="workflow@company.com",
            full_name="Workflow Rep"
        )

        create_payload = {
            "representative_id": str(rep.id),
            "buyer_id": "ACME-WORKFLOW",
            "metadata": {"source": "zoom", "duration_minutes": 30},
            "transcript": "Complete workflow transcript"
        }

        # Act 1: Create
        create_response = test_client.post(
            "/transcripts",
            json=create_payload,
            headers=auth_headers
        )

        assert create_response.status_code == 201
        transcript_id = create_response.json()["id"]

        # Act 2: Retrieve
        get_response = test_client.get(
            f"/transcripts/{transcript_id}",
            headers=auth_headers
        )

        # Assert
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == transcript_id
        assert data["representative_id"] == str(rep.id)
        assert data["buyer_id"] == "ACME-WORKFLOW"
        assert data["metadata"]["source"] == "zoom"
        assert data["transcript"] == "Complete workflow transcript"

    def test_representative_with_multiple_transcripts(self, test_client, auth_headers, db_session):
        """Test that one representative can have multiple transcripts"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="multi@company.com",
            full_name="Multi Transcript Rep"
        )

        # Act - Create multiple transcripts
        for i in range(3):
            response = test_client.post(
                "/transcripts",
                json={
                    "representative_id": str(rep.id),
                    "buyer_id": f"BUYER-{i}",
                    "transcript": f"Transcript {i}"
                },
                headers=auth_headers
            )
            assert response.status_code == 201

        # Act - List transcripts for this rep
        list_response = test_client.get(
            f"/transcripts?representative_id={rep.id}",
            headers=auth_headers
        )

        # Assert
        assert list_response.status_code == 200
        transcripts = list_response.json()
        assert len(transcripts) == 3
        for transcript in transcripts:
            assert transcript["representative_id"] == str(rep.id)
