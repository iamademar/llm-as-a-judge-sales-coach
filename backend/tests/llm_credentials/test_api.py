"""
Integration tests for LLM credential API endpoints.

Tests cover:
- Listing supported providers (GET /llm-credentials/providers)
- Listing credentials (GET /llm-credentials)
- Creating credentials (POST /llm-credentials)
- Updating credentials (PATCH /llm-credentials/{id})
- Deleting credentials (DELETE /llm-credentials/{id})
- Admin authorization enforcement
- Organization isolation
- API key encryption and masking
"""
import pytest
import uuid

from app.crud import llm_credential as cred_crud
from app.models.llm_credential import LLMProvider


class TestListProviders:
    """Tests for GET /llm-credentials/providers"""

    def test_list_providers_success(self, test_client, auth_headers):
        """Test successfully listing all supported LLM providers"""
        # Act
        response = test_client.get(
            "/llm-credentials/providers",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        providers = data["providers"]
        assert len(providers) >= 3  # OpenAI, Anthropic, Google
        
        # Check provider structure
        provider_ids = [p["id"] for p in providers]
        assert "openai" in provider_ids
        assert "anthropic" in provider_ids
        assert "google" in provider_ids
        
        # Verify provider info structure
        for provider in providers:
            assert "id" in provider
            assert "name" in provider
            assert "description" in provider
            assert "default_model" in provider
            assert "key_prefix" in provider
            assert "docs_url" in provider

    def test_list_providers_requires_auth(self, test_client):
        """Test that listing providers requires authentication"""
        # Act - No auth headers
        response = test_client.get("/llm-credentials/providers")

        # Assert
        assert response.status_code in [401, 403]


class TestListCredentials:
    """Tests for GET /llm-credentials"""

    def test_list_credentials_empty(self, test_client, admin_auth_headers, db_session):
        """Test listing when no credentials exist"""
        # Act
        response = test_client.get(
            "/llm-credentials",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "credentials" in data
        assert data["credentials"] == []
        assert "providers" in data

    def test_list_credentials_with_data(self, test_client, admin_auth_headers, sample_llm_credential, db_session):
        """Test listing credentials for organization"""
        # Act
        response = test_client.get(
            "/llm-credentials",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["credentials"]) == 1
        
        cred = data["credentials"][0]
        assert cred["provider"] == "openai"
        assert cred["default_model"] == "gpt-4o-mini"
        assert cred["is_active"] is True
        assert "masked_key" in cred
        assert "id" in cred
        assert "organization_id" in cred
        assert "created_at" in cred
        assert "updated_at" in cred

    def test_list_credentials_api_keys_masked(self, test_client, admin_auth_headers, sample_llm_credential, db_session):
        """Test that API keys are properly masked in response"""
        # Act
        response = test_client.get(
            "/llm-credentials",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        cred = data["credentials"][0]
        
        # Check that key is masked (shows only last 4 chars)
        assert cred["masked_key"].startswith("****...")
        assert len(cred["masked_key"]) > 7  # ****... + at least some chars
        assert "sk-test1234567890abcdef" not in str(data)  # Full key never exposed

    def test_list_credentials_organization_isolation(
        self, test_client, admin_auth_headers, second_auth_headers, 
        sample_llm_credential, sample_organization, second_organization, db_session
    ):
        """Test that users can only see their own organization's credentials"""
        # Arrange - Create credential for second org
        cred_crud.create(
            db_session,
            organization_id=second_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-test1234567890",
            default_model="claude-3-5-sonnet-20241022"
        )

        # Act - First org user
        response1 = test_client.get(
            "/llm-credentials",
            headers=admin_auth_headers
        )

        # Act - Second org user
        response2 = test_client.get(
            "/llm-credentials",
            headers=second_auth_headers
        )

        # Assert - Each sees only their own credentials
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert len(data1["credentials"]) == 1
        assert len(data2["credentials"]) == 1
        
        assert data1["credentials"][0]["provider"] == "openai"
        assert data2["credentials"][0]["provider"] == "anthropic"

    def test_list_credentials_requires_auth(self, test_client):
        """Test that listing credentials requires authentication"""
        # Act
        response = test_client.get("/llm-credentials")

        # Assert
        assert response.status_code in [401, 403]

    def test_list_credentials_requires_organization(self, test_client, db_session):
        """Test that user must belong to an organization"""
        # Arrange - Create user without organization
        from app.models import User
        from app.core.passwords import hash_password
        from app.core.jwt_tokens import create_access_token
        
        user_no_org = User(
            email="noorg@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="No Org User",
            is_active=True,
            is_superuser=True,
            organization_id=None  # No organization
        )
        db_session.add(user_no_org)
        db_session.commit()
        
        token = create_access_token(sub=user_no_org.email)
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = test_client.get("/llm-credentials", headers=headers)

        # Assert
        assert response.status_code == 400
        data = response.json()
        # Check detail exists in response (may be in different formats)
        detail = data.get("detail", str(data))
        assert "organization" in str(detail).lower()


class TestCreateCredential:
    """Tests for POST /llm-credentials"""

    def test_create_credential_success(self, test_client, admin_auth_headers, db_session):
        """Test successfully creating a new LLM credential"""
        # Arrange
        payload = {
            "provider": "openai",
            "api_key": "sk-test1234567890abcdefghij",
            "default_model": "gpt-4o"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "openai"
        assert data["default_model"] == "gpt-4o"
        assert data["is_active"] is True
        assert "masked_key" in data
        assert data["masked_key"].startswith("****...")
        assert "id" in data
        assert "organization_id" in data

    def test_create_credential_minimal_fields(self, test_client, admin_auth_headers, db_session):
        """Test creating credential with only required fields"""
        # Arrange
        payload = {
            "provider": "anthropic",
            "api_key": "sk-ant-test1234567890abcdefghij"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "anthropic"
        assert data["default_model"] is None
        assert data["is_active"] is True

    def test_create_credential_duplicate_provider(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test that duplicate provider returns 409 Conflict"""
        # Arrange - sample_llm_credential already has OpenAI
        payload = {
            "provider": "openai",
            "api_key": "sk-another1234567890abcdef"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        detail = data.get("detail", str(data))
        assert "already exists" in str(detail)

    def test_create_credential_invalid_openai_key_format(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test that invalid OpenAI key format is rejected"""
        # Arrange - Key doesn't start with sk-
        payload = {
            "provider": "openai",
            "api_key": "invalid-key-format-1234567890"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", str(data))
        assert "sk-" in str(detail)

    def test_create_credential_invalid_anthropic_key_format(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test that invalid Anthropic key format is rejected"""
        # Arrange - Key doesn't start with sk-ant-
        payload = {
            "provider": "anthropic",
            "api_key": "sk-wrongprefix1234567890"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", str(data))
        assert "sk-ant-" in str(detail)

    def test_create_credential_key_too_short(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test that too short API keys are rejected"""
        # Arrange
        payload = {
            "provider": "openai",
            "api_key": "sk-short"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        # Pydantic validation returns 422, custom validation returns 400
        assert response.status_code in [400, 422]
        data = response.json()
        detail = data.get("detail", str(data))
        assert "short" in str(detail).lower() or "min_length" in str(detail).lower()

    def test_create_credential_requires_admin(
        self, test_client, auth_headers, db_session
    ):
        """Test that only admins can create credentials"""
        # Arrange - auth_headers is for non-admin user
        payload = {
            "provider": "openai",
            "api_key": "sk-test1234567890abcdefghij"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        detail = data.get("detail", str(data))
        assert "admin" in str(detail).lower()

    def test_create_credential_requires_auth(self, test_client):
        """Test that creating credential requires authentication"""
        # Arrange
        payload = {
            "provider": "openai",
            "api_key": "sk-test1234567890abcdefghij"
        }

        # Act
        response = test_client.post("/llm-credentials", json=payload)

        # Assert
        assert response.status_code in [401, 403]

    def test_create_credential_google_provider(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test creating credential for Google provider"""
        # Arrange
        payload = {
            "provider": "google",
            "api_key": "AIzaSyTest1234567890abcdefghij",
            "default_model": "gemini-1.5-flash"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "google"
        assert data["default_model"] == "gemini-1.5-flash"


class TestUpdateCredential:
    """Tests for PATCH /llm-credentials/{id}"""

    def test_update_credential_api_key(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test updating credential API key"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "api_key": "sk-newkey1234567890abcdefghij"
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(cred_id)
        assert data["masked_key"].startswith("****...")
        # Verify the key was actually updated in DB
        db_session.refresh(sample_llm_credential)
        decrypted = cred_crud.get_decrypted_api_key(
            db_session, sample_llm_credential.organization_id, LLMProvider.OPENAI
        )
        assert decrypted == "sk-newkey1234567890abcdefghij"

    def test_update_credential_default_model(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test updating credential default model"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "default_model": "gpt-4-turbo"
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["default_model"] == "gpt-4-turbo"

    def test_update_credential_is_active(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test updating credential active status"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "is_active": False
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_update_credential_multiple_fields(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test updating multiple fields at once"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "api_key": "sk-updated1234567890abcdefghij",
            "default_model": "gpt-4o",
            "is_active": False
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["default_model"] == "gpt-4o"
        assert data["is_active"] is False

    def test_update_credential_invalid_key_format(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test that invalid key format is rejected on update"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "api_key": "invalid-format-key"
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 400

    def test_update_credential_not_found(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test updating non-existent credential returns 404"""
        # Arrange
        fake_id = uuid.uuid4()
        payload = {
            "default_model": "gpt-4o"
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{fake_id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_update_credential_invalid_uuid(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test that invalid UUID format returns 400"""
        # Arrange
        payload = {
            "default_model": "gpt-4o"
        }

        # Act
        response = test_client.patch(
            "/llm-credentials/not-a-uuid",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 400

    def test_update_credential_organization_isolation(
        self, test_client, admin_auth_headers, second_organization, db_session
    ):
        """Test that users cannot update other organization's credentials"""
        # Arrange - Create credential for second org
        second_cred = cred_crud.create(
            db_session,
            organization_id=second_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-test1234567890",
            default_model="claude-3-5-sonnet-20241022"
        )
        
        payload = {
            "default_model": "claude-3-opus-20240229"
        }

        # Act - Try to update with first org's admin
        response = test_client.patch(
            f"/llm-credentials/{second_cred.id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_update_credential_requires_admin(
        self, test_client, auth_headers, sample_llm_credential, db_session
    ):
        """Test that only admins can update credentials"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "default_model": "gpt-4o"
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_update_credential_requires_auth(
        self, test_client, sample_llm_credential
    ):
        """Test that updating requires authentication"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "default_model": "gpt-4o"
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload
        )

        # Assert
        assert response.status_code in [401, 403]


class TestDeleteCredential:
    """Tests for DELETE /llm-credentials/{id}"""

    def test_delete_credential_success(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test successfully deleting a credential"""
        # Arrange
        cred_id = sample_llm_credential.id

        # Act
        response = test_client.delete(
            f"/llm-credentials/{cred_id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 204
        
        # Verify credential is deleted
        deleted_cred = cred_crud.get_by_id(db_session, cred_id)
        assert deleted_cred is None

    def test_delete_credential_not_found(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test deleting non-existent credential returns 404"""
        # Arrange
        fake_id = uuid.uuid4()

        # Act
        response = test_client.delete(
            f"/llm-credentials/{fake_id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_delete_credential_invalid_uuid(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test that invalid UUID format returns 400"""
        # Act
        response = test_client.delete(
            "/llm-credentials/not-a-uuid",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 400

    def test_delete_credential_organization_isolation(
        self, test_client, admin_auth_headers, second_organization, db_session
    ):
        """Test that users cannot delete other organization's credentials"""
        # Arrange - Create credential for second org
        second_cred = cred_crud.create(
            db_session,
            organization_id=second_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-test1234567890",
            default_model="claude-3-5-sonnet-20241022"
        )

        # Act - Try to delete with first org's admin
        response = test_client.delete(
            f"/llm-credentials/{second_cred.id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404
        
        # Verify credential still exists
        still_exists = cred_crud.get_by_id(db_session, second_cred.id)
        assert still_exists is not None

    def test_delete_credential_requires_admin(
        self, test_client, auth_headers, sample_llm_credential, db_session
    ):
        """Test that only admins can delete credentials"""
        # Arrange
        cred_id = sample_llm_credential.id

        # Act
        response = test_client.delete(
            f"/llm-credentials/{cred_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403
        
        # Verify credential still exists
        still_exists = cred_crud.get_by_id(db_session, cred_id)
        assert still_exists is not None

    def test_delete_credential_requires_auth(
        self, test_client, sample_llm_credential
    ):
        """Test that deleting requires authentication"""
        # Arrange
        cred_id = sample_llm_credential.id

        # Act
        response = test_client.delete(f"/llm-credentials/{cred_id}")

        # Assert
        assert response.status_code in [401, 403]
