"""
Tests for API authentication and error handling.
"""
import pytest

from app.core.jwt_tokens import create_access_token
from app.crud import user as user_crud
from app.models import Organization


def test_missing_jwt_token_returns_403(test_client, db_session):
    """Test that requests without Authorization header return 403."""
    response = test_client.post(
        "/assess",
        json={"transcript": "Rep: Hi\nBuyer: Hello", "metadata": {}},
    )

    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "HTTPException"
    assert "request_id" in data["error"]


def test_invalid_jwt_token_returns_401(test_client, db_session):
    """Test that requests with invalid JWT token return 401."""
    response = test_client.post(
        "/assess",
        headers={"Authorization": "Bearer invalid-token-here"},
        json={"transcript": "Rep: Hi\nBuyer: Hello", "metadata": {}},
    )

    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "HTTPException"
    assert "request_id" in data["error"]


def test_valid_jwt_token_allows_access(test_client, db_session):
    """Test that requests with valid JWT token are processed."""
    # Create test organization and user
    org = Organization(name="Test Org")
    db_session.add(org)
    db_session.flush()
    
    user = user_crud.create(
        db_session,
        email="testuser@example.com",
        password="TestPass123!",
        full_name="Test User",
        organization_id=org.id
    )
    
    # Create valid access token
    access_token = create_access_token(user.email)
    
    response = test_client.post(
        "/assess",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"transcript": "Rep: Hi there\nBuyer: Hello", "metadata": {}},
    )

    # Should succeed (200) or fail with LLM error (502), but not auth error (401/403)
    assert response.status_code in [200, 502]
    if response.status_code == 502:
        # LLM failure, but auth passed
        data = response.json()
        assert "error" in data
        assert "LLM" in data["error"]["message"] or "Internal" in data["error"]["message"]


def test_health_endpoint_is_public(test_client, db_session):
    """Test that /health endpoint does not require authentication."""
    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_validation_error_returns_consistent_format(test_client, db_session):
    """Test that validation errors return consistent error format."""
    # Create test organization and user
    org = Organization(name="Test Org Validation")
    db_session.add(org)
    db_session.flush()
    
    user = user_crud.create(
        db_session,
        email="validationtest@example.com",
        password="TestPass123!",
        full_name="Validation Test User",
        organization_id=org.id
    )
    
    # Create valid access token
    access_token = create_access_token(user.email)
    
    response = test_client.post(
        "/assess",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"metadata": {}},  # Missing required 'transcript' field
    )

    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "ValidationError"
    assert "validation" in data["error"]["message"].lower()
    assert "request_id" in data["error"]
    assert "details" in data["error"]


def test_response_includes_request_id_header(test_client, db_session):
    """Test that all responses include X-Request-ID header."""
    response = test_client.get("/health")

    assert "X-Request-ID" in response.headers
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) > 0


def test_structured_logs_on_request(test_client, db_session, caplog):
    """Test that requests generate structured JSON logs."""
    with caplog.at_level("INFO"):
        response = test_client.get("/health")

    # Check that logs were generated
    assert len(caplog.records) > 0

    # Find the structured log record
    log_found = False
    for record in caplog.records:
        if "request_id" in record.message and "method" in record.message:
            log_found = True
            # Verify it's JSON-like structure
            assert "GET" in record.message or "POST" in record.message
            assert "status_code" in record.message
            assert "latency_ms" in record.message
            break

    assert log_found, "Structured log not found in captured logs"


def test_error_response_includes_request_id(test_client, db_session):
    """Test that error responses include request_id from middleware."""
    response = test_client.post(
        "/assess",
        json={"transcript": "test"},  # Will fail auth (no JWT token)
    )

    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert "request_id" in data["error"]

    # Verify request_id matches header
    request_id_header = response.headers.get("X-Request-ID")
    assert data["error"]["request_id"] == request_id_header
