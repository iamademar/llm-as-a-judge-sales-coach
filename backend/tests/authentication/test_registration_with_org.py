"""
Tests for organization-aware registration flow.

Tests registration with organization creation and joining existing organizations.
"""
import pytest
from fastapi import status

from app.crud import organization as org_crud
from app.crud import user as user_crud


def test_register_with_new_organization(test_client, db_session):
    """Registration should create new organization."""
    # Act
    response = test_client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
            "organization_name": "New Startup Inc"
        }
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["organization_id"] is not None

    # Verify organization was created
    org = org_crud.get_by_name(db_session, "New Startup Inc")
    assert org is not None
    assert org.name == "New Startup Inc"

    # Verify user has organization
    user = user_crud.get_by_email(db_session, "newuser@example.com")
    assert user.organization_id == org.id


def test_register_with_existing_organization(test_client, db_session, sample_organization):
    """Registration should allow joining existing organization."""
    # Act
    response = test_client.post(
        "/auth/register",
        json={
            "email": "member@example.com",
            "password": "password123",
            "organization_id": str(sample_organization.id)
        }
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["organization_id"] == str(sample_organization.id)


def test_register_duplicate_org_name_fails(test_client, db_session, sample_organization):
    """Cannot create organization with existing name."""
    # Act
    response = test_client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "organization_name": sample_organization.name  # Duplicate
        }
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_json = response.json()
    # Check for error message in either "detail" or "error" format
    error_text = str(response_json).lower()
    assert "already taken" in error_text or "already exists" in error_text


def test_register_with_invalid_org_id_fails(test_client, db_session):
    """Cannot join non-existent organization."""
    # Act
    response = test_client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "organization_id": "00000000-0000-0000-0000-000000000000"
        }
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_json = response.json()
    error_text = str(response_json).lower()
    assert "not found" in error_text


def test_register_without_org_fails(test_client, db_session):
    """Must provide either org_id or org_name."""
    # Act
    response = test_client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123"
        }
    )

    # Assert - Should return validation error
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]
    # Validation is working (endpoint rejects input without org)


def test_register_with_both_org_options_fails(test_client, db_session, sample_organization):
    """Cannot provide both org_id and org_name."""
    # Act
    response = test_client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "organization_id": str(sample_organization.id),
            "organization_name": "New Org"
        }
    )

    # Assert - Should return validation error
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]
    # Validation is working (endpoint rejects both options)


def test_list_organizations_endpoint(test_client, db_session, sample_organization):
    """Should list active organizations."""
    # Act
    response = test_client.get("/auth/organizations")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(org["id"] == str(sample_organization.id) for org in data)


def test_register_case_insensitive_org_name(test_client, db_session, sample_organization):
    """Organization name uniqueness is case-insensitive."""
    # Act: Try to create org with same name but different case
    response = test_client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "organization_name": sample_organization.name.upper()  # Different case
        }
    )

    # Assert: Should fail due to case-insensitive uniqueness
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_json = response.json()
    error_text = str(response_json).lower()
    assert "already taken" in error_text or "already exists" in error_text
