"""
Authorization and security tests for LLM credentials.

Tests focus on:
- Admin-only access enforcement
- Organization isolation
- Authentication requirements
- User without organization handling
"""
import pytest

from app.crud import llm_credential as cred_crud
from app.models.llm_credential import LLMProvider


class TestAdminOnlyAccess:
    """Tests that write operations require admin privileges"""

    def test_create_requires_admin(self, test_client, auth_headers, db_session):
        """Test that non-admin cannot create credentials"""
        # Arrange
        payload = {
            "provider": "openai",
            "api_key": "sk-test1234567890abcdefghij"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=auth_headers  # Non-admin user
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        detail = data.get("detail", str(data))
        assert "admin" in str(detail).lower()

    def test_update_requires_admin(
        self, test_client, auth_headers, sample_llm_credential, db_session
    ):
        """Test that non-admin cannot update credentials"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "default_model": "gpt-4o"
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload,
            headers=auth_headers  # Non-admin user
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        detail = data.get("detail", str(data))
        assert "admin" in str(detail).lower()

    def test_delete_requires_admin(
        self, test_client, auth_headers, sample_llm_credential, db_session
    ):
        """Test that non-admin cannot delete credentials"""
        # Arrange
        cred_id = sample_llm_credential.id

        # Act
        response = test_client.delete(
            f"/llm-credentials/{cred_id}",
            headers=auth_headers  # Non-admin user
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        detail = data.get("detail", str(data))
        assert "admin" in str(detail).lower()

    def test_admin_can_create(self, test_client, admin_auth_headers, db_session):
        """Test that admin can create credentials"""
        # Arrange
        payload = {
            "provider": "openai",
            "api_key": "sk-test1234567890abcdefghij"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 201

    def test_admin_can_update(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test that admin can update credentials"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "default_model": "gpt-4o"
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200

    def test_admin_can_delete(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test that admin can delete credentials"""
        # Arrange
        cred_id = sample_llm_credential.id

        # Act
        response = test_client.delete(
            f"/llm-credentials/{cred_id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 204

    def test_list_does_not_require_admin(
        self, test_client, auth_headers, sample_llm_credential, db_session
    ):
        """Test that listing credentials doesn't require admin (read-only)"""
        # Act
        response = test_client.get(
            "/llm-credentials",
            headers=auth_headers  # Non-admin user
        )

        # Assert
        assert response.status_code == 200

    def test_list_providers_does_not_require_admin(
        self, test_client, auth_headers, db_session
    ):
        """Test that listing providers doesn't require admin"""
        # Act
        response = test_client.get(
            "/llm-credentials/providers",
            headers=auth_headers  # Non-admin user
        )

        # Assert
        assert response.status_code == 200


class TestOrganizationIsolation:
    """Tests that credentials are properly isolated by organization"""

    def test_cannot_view_other_org_credentials(
        self, test_client, admin_auth_headers, second_auth_headers,
        sample_organization, second_organization, db_session
    ):
        """Test that organizations cannot see each other's credentials"""
        # Arrange - Create credentials for both orgs
        org1_cred = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.OPENAI,
            api_key="sk-org1key1234567890"
        )
        org2_cred = cred_crud.create(
            db_session,
            organization_id=second_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-org2key1234567890"
        )

        # Act - List credentials for each org
        response1 = test_client.get(
            "/llm-credentials",
            headers=admin_auth_headers  # First org admin
        )
        response2 = test_client.get(
            "/llm-credentials",
            headers=second_auth_headers  # Second org user
        )

        # Assert
        data1 = response1.json()
        data2 = response2.json()
        
        assert len(data1["credentials"]) == 1
        assert len(data2["credentials"]) == 1
        assert data1["credentials"][0]["provider"] == "openai"
        assert data2["credentials"][0]["provider"] == "anthropic"

    def test_cannot_update_other_org_credentials(
        self, test_client, admin_auth_headers, second_organization, db_session
    ):
        """Test that admin cannot update other organization's credentials"""
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

    def test_cannot_delete_other_org_credentials(
        self, test_client, admin_auth_headers, second_organization, db_session
    ):
        """Test that admin cannot delete other organization's credentials"""
        # Arrange - Create credential for second org
        second_cred = cred_crud.create(
            db_session,
            organization_id=second_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-test1234567890"
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

    def test_multiple_orgs_same_provider(
        self, test_client, admin_auth_headers, second_auth_headers,
        sample_organization, second_organization, db_session
    ):
        """Test that different orgs can have credentials for same provider"""
        # Arrange - Create OpenAI credentials for both orgs
        cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.OPENAI,
            api_key="sk-org1key1234567890"
        )
        cred_crud.create(
            db_session,
            organization_id=second_organization.id,
            provider=LLMProvider.OPENAI,
            api_key="sk-org2key0987654321"
        )

        # Act - List credentials for each org
        response1 = test_client.get(
            "/llm-credentials",
            headers=admin_auth_headers
        )
        response2 = test_client.get(
            "/llm-credentials",
            headers=second_auth_headers
        )

        # Assert - Both have OpenAI credentials
        data1 = response1.json()
        data2 = response2.json()
        
        assert len(data1["credentials"]) == 1
        assert len(data2["credentials"]) == 1
        assert data1["credentials"][0]["provider"] == "openai"
        assert data2["credentials"][0]["provider"] == "openai"
        
        # But masked keys should be different
        assert data1["credentials"][0]["masked_key"] != data2["credentials"][0]["masked_key"]


class TestAuthenticationRequired:
    """Tests that all endpoints require authentication"""

    def test_list_providers_requires_auth(self, test_client):
        """Test that listing providers requires authentication"""
        # Act
        response = test_client.get("/llm-credentials/providers")

        # Assert
        assert response.status_code in [401, 403]

    def test_list_credentials_requires_auth(self, test_client):
        """Test that listing credentials requires authentication"""
        # Act
        response = test_client.get("/llm-credentials")

        # Assert
        assert response.status_code in [401, 403]

    def test_create_requires_auth(self, test_client):
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

    def test_update_requires_auth(self, test_client, sample_llm_credential):
        """Test that updating credential requires authentication"""
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

    def test_delete_requires_auth(self, test_client, sample_llm_credential):
        """Test that deleting credential requires authentication"""
        # Arrange
        cred_id = sample_llm_credential.id

        # Act
        response = test_client.delete(f"/llm-credentials/{cred_id}")

        # Assert
        assert response.status_code in [401, 403]


class TestUserWithoutOrganization:
    """Tests for users without organization membership"""

    def test_list_without_organization(self, test_client, db_session):
        """Test that user without organization gets proper error"""
        # Arrange - Create user without organization
        from app.models import User
        from app.core.passwords import hash_password
        from app.core.jwt_tokens import create_access_token
        
        user_no_org = User(
            email="noorg@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="No Org User",
            is_active=True,
            is_superuser=False,
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
        detail = data.get("detail", str(data))
        assert "organization" in str(detail).lower()

    def test_create_without_organization(self, test_client, db_session):
        """Test that admin without organization cannot create credentials"""
        # Arrange - Create admin user without organization
        from app.models import User
        from app.core.passwords import hash_password
        from app.core.jwt_tokens import create_access_token
        
        admin_no_org = User(
            email="adminnoorg@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Admin No Org",
            is_active=True,
            is_superuser=True,
            organization_id=None  # No organization
        )
        db_session.add(admin_no_org)
        db_session.commit()
        
        token = create_access_token(sub=admin_no_org.email)
        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "provider": "openai",
            "api_key": "sk-test1234567890abcdefghij"
        }

        # Act
        response = test_client.post("/llm-credentials", json=payload, headers=headers)

        # Assert
        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", str(data))
        assert "organization" in str(detail).lower()

    def test_list_providers_works_without_organization(self, test_client, db_session):
        """Test that listing providers works even without organization"""
        # Arrange - Create user without organization
        from app.models import User
        from app.core.passwords import hash_password
        from app.core.jwt_tokens import create_access_token
        
        user_no_org = User(
            email="noorg@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="No Org User",
            is_active=True,
            is_superuser=False,
            organization_id=None
        )
        db_session.add(user_no_org)
        db_session.commit()
        
        token = create_access_token(sub=user_no_org.email)
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = test_client.get("/llm-credentials/providers", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) >= 3


class TestSecurityBestPractices:
    """Tests for security best practices"""

    def test_api_keys_never_exposed_in_list(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test that full API keys are never exposed in list response"""
        # Act
        response = test_client.get(
            "/llm-credentials",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        response_text = response.text
        
        # Full key should never appear in response
        assert "sk-test1234567890abcdef" not in response_text
        
        # But masked version should be present
        data = response.json()
        assert "****..." in data["credentials"][0]["masked_key"]

    def test_api_keys_never_exposed_in_create(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test that full API keys are never exposed in create response"""
        # Arrange
        payload = {
            "provider": "anthropic",
            "api_key": "sk-ant-secretkey1234567890abcdef"
        }

        # Act
        response = test_client.post(
            "/llm-credentials",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 201
        response_text = response.text
        
        # Full key should never appear in response
        assert "sk-ant-secretkey1234567890abcdef" not in response_text
        
        # But masked version should be present
        data = response.json()
        assert "****..." in data["masked_key"]

    def test_api_keys_never_exposed_in_update(
        self, test_client, admin_auth_headers, sample_llm_credential, db_session
    ):
        """Test that full API keys are never exposed in update response"""
        # Arrange
        cred_id = sample_llm_credential.id
        payload = {
            "api_key": "sk-newsecretkey1234567890abcdef"
        }

        # Act
        response = test_client.patch(
            f"/llm-credentials/{cred_id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        response_text = response.text
        
        # Full key should never appear in response
        assert "sk-newsecretkey1234567890abcdef" not in response_text
        
        # But masked version should be present
        data = response.json()
        assert "****..." in data["masked_key"]
