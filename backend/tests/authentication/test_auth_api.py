"""
Integration tests for authentication endpoints.

Tests cover:
- User registration (success and duplicate email)
- Login with credentials
- Getting current user with access token
- Token refresh with refresh token
- Invalid credentials and token handling
"""
import pytest

from app.core.jwt_tokens import create_access_token, create_refresh_token


class TestRegisterEndpoint:
    """Tests for POST /auth/register"""

    def test_register_success(self, test_client, db_session):
        """Test successful user registration"""
        # Arrange
        payload = {
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User",
            "organization_name": "Test Org",
        }

        # Act
        response = test_client.post("/auth/register", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["full_name"] == payload["full_name"]
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be in response

    def test_register_duplicate_email(self, test_client, db_session):
        """Test registration with duplicate email returns 400"""
        # Arrange
        payload = {
            "email": "duplicate@example.com",
            "password": "password123",
            "organization_name": "Duplicate Test Org",
        }

        # Create first user
        test_client.post("/auth/register", json=payload)

        # Act - try to register again with same email
        response = test_client.post("/auth/register", json=payload)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        # Handle both direct detail and error wrapper formats
        error_msg = response_data.get("detail") or response_data.get("error", {}).get("message", "")
        assert "already registered" in error_msg.lower()

    def test_register_minimal_fields(self, test_client, db_session):
        """Test registration with only required fields"""
        # Arrange
        payload = {
            "email": "minimal@example.com",
            "password": "password123",
            "organization_name": "Minimal Org",
        }

        # Act
        response = test_client.post("/auth/register", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["full_name"] is None


class TestLoginEndpoint:
    """Tests for POST /auth/login"""

    def test_login_success(self, test_client, db_session):
        """Test successful login returns token pair"""
        # Arrange - register user first
        register_payload = {
            "email": "loginuser@example.com",
            "password": "password123",
            "organization_name": "Login Test Org",
        }
        test_client.post("/auth/register", json=register_payload)

        login_payload = {
            "email": "loginuser@example.com",
            "password": "password123",
        }

        # Act
        response = test_client.post("/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    def test_login_wrong_password(self, test_client, db_session):
        """Test login with wrong password returns 401"""
        # Arrange - register user
        test_client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "correctpass", "organization_name": "Wrong Pass Org"},
        )

        # Act - try to login with wrong password
        response = test_client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "wrongpass"},
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error", {}).get("message", "")
        assert "incorrect" in error_msg.lower()

    def test_login_nonexistent_user(self, test_client, db_session):
        """Test login with nonexistent email returns 401"""
        # Act
        response = test_client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "anypass"},
        )

        # Assert
        assert response.status_code == 401


class TestMeEndpoint:
    """Tests for GET /auth/me"""

    def test_me_with_valid_token(self, test_client, db_session):
        """Test /me with valid access token returns user data"""
        # Arrange - register and login
        test_client.post(
            "/auth/register",
            json={
                "email": "meuser@example.com",
                "password": "password123",
                "full_name": "Me User",
                "organization_name": "Me Test Org",
            },
        )
        login_response = test_client.post(
            "/auth/login",
            json={"email": "meuser@example.com", "password": "password123"},
        )
        access_token = login_response.json()["access_token"]

        # Act
        response = test_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "meuser@example.com"
        assert data["full_name"] == "Me User"
        assert data["is_active"] is True

    def test_me_without_token(self, test_client, db_session):
        """Test /me without token returns 403"""
        # Act
        response = test_client.get("/auth/me")

        # Assert
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403

    def test_me_with_invalid_token(self, test_client, db_session):
        """Test /me with invalid token returns 401"""
        # Act
        response = test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        # Assert
        assert response.status_code == 401

    def test_me_with_refresh_token(self, test_client, db_session):
        """Test /me with refresh token (wrong type) returns 401"""
        # Arrange - create a refresh token
        refresh_token = create_refresh_token(sub="user@example.com")

        # Act - try to use refresh token as access token
        response = test_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error", {}).get("message", "")
        assert "invalid token type" in error_msg.lower()


class TestRefreshEndpoint:
    """Tests for POST /auth/refresh"""

    def test_refresh_with_valid_token(self, test_client, db_session):
        """Test refresh with valid refresh token returns new token pair"""
        # Arrange - register and login
        test_client.post(
            "/auth/register",
            json={"email": "refreshuser@example.com", "password": "password123", "organization_name": "Refresh Org"},
        )
        login_response = test_client.post(
            "/auth/login",
            json={"email": "refreshuser@example.com", "password": "password123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Act
        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # New tokens are returned (they may be identical if generated in same second due to timing)
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    def test_refresh_with_invalid_token(self, test_client, db_session):
        """Test refresh with invalid token returns 401"""
        # Act
        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error", {}).get("message", "")
        assert "invalid" in error_msg.lower()

    def test_refresh_with_access_token(self, test_client, db_session):
        """Test refresh with access token (wrong type) returns 401"""
        # Arrange - create an access token
        access_token = create_access_token(sub="user@example.com")

        # Act - try to use access token as refresh token
        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": access_token},
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error", {}).get("message", "")
        assert "invalid token type" in error_msg.lower()
