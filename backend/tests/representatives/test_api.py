"""
Integration tests for representative API endpoints.

Tests cover:
- Creating representatives (success, duplicate, auth required)
- Listing representatives (all, pagination, active only)
- Getting representative by ID (success, not found, invalid UUID)
- Updating representatives (full, partial)
- Deactivating representatives
- Authentication and authorization checks
"""
import pytest
from datetime import datetime, timezone

from app.models import Representative
from app.crud import representative as rep_crud


class TestCreateRepresentative:
    """Tests for POST /representatives"""

    def test_create_representative_success(self, test_client, auth_headers, db_session):
        """Test successful representative creation"""
        # Arrange
        payload = {
            "email": "new.rep@company.com",
            "full_name": "New Sales Rep",
            "department": "Enterprise Sales",
            "hire_date": "2024-01-15T00:00:00Z"
        }

        # Act
        response = test_client.post(
            "/representatives",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["full_name"] == payload["full_name"]
        assert data["department"] == payload["department"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_representative_minimal_fields(self, test_client, auth_headers, db_session):
        """Test creating representative with only required fields"""
        # Arrange
        payload = {
            "email": "minimal@company.com",
            "full_name": "Minimal Rep"
        }

        # Act
        response = test_client.post(
            "/representatives",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["full_name"] == payload["full_name"]
        assert data["department"] is None
        assert data["hire_date"] is None
        assert data["is_active"] is True

    def test_create_representative_duplicate_email(self, test_client, auth_headers, db_session):
        """Test that duplicate email returns 400 error"""
        # Arrange - Create first representative
        rep_crud.create(
            db_session,
            email="duplicate@company.com",
            full_name="First Rep"
        )

        payload = {
            "email": "duplicate@company.com",
            "full_name": "Second Rep"
        }

        # Act
        response = test_client.post(
            "/representatives",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        # Duplicate email should return 400 Bad Request

    def test_create_representative_requires_auth(self, test_client, db_session):
        """Test that creating representative requires authentication"""
        # Arrange
        payload = {
            "email": "noauth@company.com",
            "full_name": "No Auth Rep"
        }

        # Act - No auth headers
        response = test_client.post("/representatives", json=payload)

        # Assert
        assert response.status_code in [401, 403]  # FastAPI JWT returns 403

    def test_create_representative_invalid_email(self, test_client, auth_headers, db_session):
        """Test that invalid email format is rejected"""
        # Arrange
        payload = {
            "email": "not-an-email",
            "full_name": "Invalid Email Rep"
        }

        # Act
        response = test_client.post(
            "/representatives",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 422  # Validation error


class TestListRepresentatives:
    """Tests for GET /representatives"""

    def test_list_all_representatives(self, test_client, auth_headers, db_session):
        """Test listing all representatives"""
        # Arrange - Create multiple representatives
        rep_crud.create(db_session, email="rep1@company.com", full_name="Rep 1")
        rep_crud.create(db_session, email="rep2@company.com", full_name="Rep 2")
        rep_crud.create(db_session, email="rep3@company.com", full_name="Rep 3")

        # Act
        response = test_client.get("/representatives", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("id" in rep for rep in data)
        assert all("email" in rep for rep in data)

    def test_list_representatives_with_pagination(self, test_client, auth_headers, db_session):
        """Test pagination with skip and limit"""
        # Arrange - Create 10 representatives
        for i in range(10):
            rep_crud.create(db_session, email=f"rep{i}@company.com", full_name=f"Rep {i}")

        # Act
        response = test_client.get(
            "/representatives?skip=2&limit=5",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_list_active_representatives_only(self, test_client, auth_headers, db_session):
        """Test filtering for active representatives only"""
        # Arrange
        rep1 = rep_crud.create(db_session, email="active1@company.com", full_name="Active 1")
        rep2 = rep_crud.create(db_session, email="active2@company.com", full_name="Active 2")
        rep3 = rep_crud.create(db_session, email="inactive@company.com", full_name="Inactive")
        
        # Deactivate rep3
        rep_crud.deactivate(db_session, db_obj=rep3)

        # Act
        response = test_client.get(
            "/representatives?active_only=true",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(rep["is_active"] is True for rep in data)

    def test_list_representatives_empty(self, test_client, auth_headers, db_session):
        """Test listing when no representatives exist"""
        # Act
        response = test_client.get("/representatives", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json() == []

    def test_list_representatives_requires_auth(self, test_client, db_session):
        """Test that listing requires authentication"""
        # Act
        response = test_client.get("/representatives")

        # Assert
        assert response.status_code in [401, 403]  # FastAPI JWT returns 403


class TestGetRepresentative:
    """Tests for GET /representatives/{rep_id}"""

    def test_get_representative_success(self, test_client, auth_headers, db_session):
        """Test getting a specific representative"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="get@company.com",
            full_name="Get Rep",
            department="Sales"
        )

        # Act
        response = test_client.get(
            f"/representatives/{rep.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "get@company.com"
        assert data["full_name"] == "Get Rep"
        assert data["department"] == "Sales"

    def test_get_representative_not_found(self, test_client, auth_headers, db_session):
        """Test getting non-existent representative returns 404"""
        # Arrange
        import uuid
        fake_id = uuid.uuid4()

        # Act
        response = test_client.get(
            f"/representatives/{fake_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404
        # Non-existent representative should return 404 Not Found

    def test_get_representative_invalid_uuid(self, test_client, auth_headers, db_session):
        """Test that invalid UUID format returns 400"""
        # Act
        response = test_client.get(
            "/representatives/not-a-uuid",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        # Invalid UUID format should return 400 Bad Request

    def test_get_representative_requires_auth(self, test_client, db_session):
        """Test that getting representative requires authentication"""
        # Arrange
        rep = rep_crud.create(db_session, email="noauth@company.com", full_name="No Auth")

        # Act
        response = test_client.get(f"/representatives/{rep.id}")

        # Assert
        assert response.status_code in [401, 403]  # FastAPI JWT returns 403


class TestUpdateRepresentative:
    """Tests for PATCH /representatives/{rep_id}"""

    def test_update_representative_full(self, test_client, auth_headers, db_session):
        """Test updating all fields of a representative"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="original@company.com",
            full_name="Original Name",
            department="SMB"
        )

        payload = {
            "email": "updated@company.com",
            "full_name": "Updated Name",
            "department": "Enterprise"
        }

        # Act
        response = test_client.patch(
            f"/representatives/{rep.id}",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@company.com"
        assert data["full_name"] == "Updated Name"
        assert data["department"] == "Enterprise"

    def test_update_representative_partial(self, test_client, auth_headers, db_session):
        """Test partial update (only some fields)"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="partial@company.com",
            full_name="Original Name",
            department="Sales"
        )

        payload = {
            "full_name": "New Name Only"
        }

        # Act
        response = test_client.patch(
            f"/representatives/{rep.id}",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "New Name Only"
        assert data["email"] == "partial@company.com"  # Unchanged
        assert data["department"] == "Sales"  # Unchanged

    def test_update_representative_not_found(self, test_client, auth_headers, db_session):
        """Test updating non-existent representative returns 404"""
        # Arrange
        import uuid
        fake_id = uuid.uuid4()
        payload = {"full_name": "New Name"}

        # Act
        response = test_client.patch(
            f"/representatives/{fake_id}",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_update_representative_invalid_uuid(self, test_client, auth_headers, db_session):
        """Test that invalid UUID format returns 400"""
        # Act
        response = test_client.patch(
            "/representatives/not-a-uuid",
            json={"full_name": "New Name"},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400

    def test_update_representative_requires_auth(self, test_client, db_session):
        """Test that updating requires authentication"""
        # Arrange
        rep = rep_crud.create(db_session, email="noauth@company.com", full_name="No Auth")

        # Act
        response = test_client.patch(
            f"/representatives/{rep.id}",
            json={"full_name": "New Name"}
        )

        # Assert
        assert response.status_code in [401, 403]  # FastAPI JWT returns 403


class TestDeactivateRepresentative:
    """Tests for POST /representatives/{rep_id}/deactivate"""

    def test_deactivate_representative_success(self, test_client, auth_headers, db_session):
        """Test deactivating a representative"""
        # Arrange
        rep = rep_crud.create(
            db_session,
            email="deactivate@company.com",
            full_name="Deactivate Rep"
        )
        assert rep.is_active is True

        # Act
        response = test_client.post(
            f"/representatives/{rep.id}/deactivate",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["email"] == "deactivate@company.com"

    def test_deactivate_already_inactive(self, test_client, auth_headers, db_session):
        """Test deactivating an already inactive representative"""
        # Arrange
        rep = rep_crud.create(db_session, email="inactive@company.com", full_name="Inactive")
        rep_crud.deactivate(db_session, db_obj=rep)

        # Act
        response = test_client.post(
            f"/representatives/{rep.id}/deactivate",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_deactivate_representative_not_found(self, test_client, auth_headers, db_session):
        """Test deactivating non-existent representative returns 404"""
        # Arrange
        import uuid
        fake_id = uuid.uuid4()

        # Act
        response = test_client.post(
            f"/representatives/{fake_id}/deactivate",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_deactivate_representative_invalid_uuid(self, test_client, auth_headers, db_session):
        """Test that invalid UUID format returns 400"""
        # Act
        response = test_client.post(
            "/representatives/not-a-uuid/deactivate",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400

    def test_deactivate_representative_requires_auth(self, test_client, db_session):
        """Test that deactivating requires authentication"""
        # Arrange
        rep = rep_crud.create(db_session, email="noauth@company.com", full_name="No Auth")

        # Act
        response = test_client.post(f"/representatives/{rep.id}/deactivate")

        # Assert
        assert response.status_code in [401, 403]  # FastAPI JWT returns 403

