"""
Tests for LLM credential CRUD operations.

Tests the CRUD functions in app.crud.llm_credential:
- get_by_id
- get_by_org
- get_by_org_and_provider
- get_decrypted_api_key
- create
- update
- delete
- get_masked_key
"""
import pytest
import uuid

from app.crud import llm_credential as cred_crud
from app.models.llm_credential import LLMProvider


class TestGetById:
    """Tests for get_by_id()"""

    def test_get_by_id_success(self, db_session, sample_llm_credential):
        """Test retrieving credential by ID"""
        # Act
        result = cred_crud.get_by_id(db_session, sample_llm_credential.id)

        # Assert
        assert result is not None
        assert result.id == sample_llm_credential.id
        assert result.provider == LLMProvider.OPENAI

    def test_get_by_id_not_found(self, db_session):
        """Test that non-existent ID returns None"""
        # Arrange
        fake_id = uuid.uuid4()

        # Act
        result = cred_crud.get_by_id(db_session, fake_id)

        # Assert
        assert result is None


class TestGetByOrg:
    """Tests for get_by_org()"""

    def test_get_by_org_empty(self, db_session, sample_organization):
        """Test getting credentials when none exist"""
        # Act
        result = cred_crud.get_by_org(db_session, sample_organization.id)

        # Assert
        assert result == []

    def test_get_by_org_single(self, db_session, sample_llm_credential, sample_organization):
        """Test getting single credential"""
        # Act
        result = cred_crud.get_by_org(db_session, sample_organization.id)

        # Assert
        assert len(result) == 1
        assert result[0].id == sample_llm_credential.id

    def test_get_by_org_multiple(self, db_session, sample_organization):
        """Test getting multiple credentials for organization"""
        # Arrange - Create credentials for multiple providers
        cred1 = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.OPENAI,
            api_key="sk-test1234567890abcdef"
        )
        cred2 = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-test1234567890"
        )
        cred3 = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.GOOGLE,
            api_key="AIzaSyTest1234567890"
        )

        # Act
        result = cred_crud.get_by_org(db_session, sample_organization.id)

        # Assert
        assert len(result) == 3
        provider_values = [c.provider.value for c in result]
        assert "openai" in provider_values
        assert "anthropic" in provider_values
        assert "google" in provider_values

    def test_get_by_org_organization_isolation(
        self, db_session, sample_organization, second_organization
    ):
        """Test that credentials are isolated by organization"""
        # Arrange
        cred1 = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.OPENAI,
            api_key="sk-test1234567890abcdef"
        )
        cred2 = cred_crud.create(
            db_session,
            organization_id=second_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-test1234567890"
        )

        # Act
        org1_creds = cred_crud.get_by_org(db_session, sample_organization.id)
        org2_creds = cred_crud.get_by_org(db_session, second_organization.id)

        # Assert
        assert len(org1_creds) == 1
        assert len(org2_creds) == 1
        assert org1_creds[0].provider == LLMProvider.OPENAI
        assert org2_creds[0].provider == LLMProvider.ANTHROPIC


class TestGetByOrgAndProvider:
    """Tests for get_by_org_and_provider()"""

    def test_get_by_org_and_provider_success(
        self, db_session, sample_llm_credential, sample_organization
    ):
        """Test retrieving specific credential by org and provider"""
        # Act
        result = cred_crud.get_by_org_and_provider(
            db_session, sample_organization.id, LLMProvider.OPENAI
        )

        # Assert
        assert result is not None
        assert result.id == sample_llm_credential.id
        assert result.provider == LLMProvider.OPENAI

    def test_get_by_org_and_provider_not_found(self, db_session, sample_organization):
        """Test that non-existent provider returns None"""
        # Act
        result = cred_crud.get_by_org_and_provider(
            db_session, sample_organization.id, LLMProvider.ANTHROPIC
        )

        # Assert
        assert result is None

    def test_get_by_org_and_provider_only_active(self, db_session, sample_organization):
        """Test that only active credentials are returned"""
        # Arrange - Create inactive credential
        cred = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.OPENAI,
            api_key="sk-test1234567890abcdef"
        )
        cred.is_active = False
        db_session.commit()

        # Act
        result = cred_crud.get_by_org_and_provider(
            db_session, sample_organization.id, LLMProvider.OPENAI
        )

        # Assert
        assert result is None


class TestGetDecryptedApiKey:
    """Tests for get_decrypted_api_key()"""

    def test_get_decrypted_api_key_success(self, db_session, sample_llm_credential, sample_organization):
        """Test successfully decrypting API key"""
        # Act
        result = cred_crud.get_decrypted_api_key(
            db_session, sample_organization.id, LLMProvider.OPENAI
        )

        # Assert
        assert result is not None
        assert result == "sk-test1234567890abcdef"

    def test_get_decrypted_api_key_not_found(self, db_session, sample_organization):
        """Test that non-existent credential returns None"""
        # Act
        result = cred_crud.get_decrypted_api_key(
            db_session, sample_organization.id, LLMProvider.ANTHROPIC
        )

        # Assert
        assert result is None

    def test_get_decrypted_api_key_different_providers(self, db_session, sample_organization):
        """Test decrypting keys for different providers"""
        # Arrange
        openai_key = "sk-openai1234567890abcdef"
        anthropic_key = "sk-ant-anthropic1234567890"
        
        cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.OPENAI,
            api_key=openai_key
        )
        cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key=anthropic_key
        )

        # Act
        openai_result = cred_crud.get_decrypted_api_key(
            db_session, sample_organization.id, LLMProvider.OPENAI
        )
        anthropic_result = cred_crud.get_decrypted_api_key(
            db_session, sample_organization.id, LLMProvider.ANTHROPIC
        )

        # Assert
        assert openai_result == openai_key
        assert anthropic_result == anthropic_key


class TestCreate:
    """Tests for create()"""

    def test_create_success(self, db_session, sample_organization):
        """Test successfully creating a credential"""
        # Arrange
        api_key = "sk-test1234567890abcdef"

        # Act
        result = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.OPENAI,
            api_key=api_key,
            default_model="gpt-4o-mini"
        )

        # Assert
        assert result is not None
        assert result.id is not None
        assert result.organization_id == sample_organization.id
        assert result.provider == LLMProvider.OPENAI
        assert result.default_model == "gpt-4o-mini"
        assert result.is_active is True
        assert result.encrypted_api_key is not None
        assert result.encrypted_api_key != api_key  # Should be encrypted

    def test_create_without_default_model(self, db_session, sample_organization):
        """Test creating credential without default model"""
        # Act
        result = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-test1234567890"
        )

        # Assert
        assert result.default_model is None
        assert result.is_active is True

    def test_create_duplicate_provider_raises_error(
        self, db_session, sample_llm_credential, sample_organization
    ):
        """Test that creating duplicate provider raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            cred_crud.create(
                db_session,
                organization_id=sample_organization.id,
                provider=LLMProvider.OPENAI,  # Already exists
                api_key="sk-another1234567890"
            )
        
        assert "already exists" in str(exc_info.value).lower()

    def test_create_api_key_is_encrypted(self, db_session, sample_organization):
        """Test that API key is encrypted in database"""
        # Arrange
        plain_key = "sk-test1234567890abcdef"

        # Act
        result = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.OPENAI,
            api_key=plain_key
        )

        # Assert
        assert result.encrypted_api_key != plain_key
        # Verify we can decrypt it back
        decrypted = cred_crud.get_decrypted_api_key(
            db_session, sample_organization.id, LLMProvider.OPENAI
        )
        assert decrypted == plain_key


class TestUpdate:
    """Tests for update()"""

    def test_update_api_key(self, db_session, sample_llm_credential, sample_organization):
        """Test updating API key"""
        # Arrange
        new_key = "sk-newkey1234567890abcdef"

        # Act
        result = cred_crud.update(
            db_session,
            sample_llm_credential,
            api_key=new_key
        )

        # Assert
        assert result.id == sample_llm_credential.id
        # Verify key was updated
        decrypted = cred_crud.get_decrypted_api_key(
            db_session, sample_organization.id, LLMProvider.OPENAI
        )
        assert decrypted == new_key

    def test_update_default_model(self, db_session, sample_llm_credential):
        """Test updating default model"""
        # Act
        result = cred_crud.update(
            db_session,
            sample_llm_credential,
            default_model="gpt-4-turbo"
        )

        # Assert
        assert result.default_model == "gpt-4-turbo"

    def test_update_is_active(self, db_session, sample_llm_credential):
        """Test updating active status"""
        # Arrange
        assert sample_llm_credential.is_active is True

        # Act
        result = cred_crud.update(
            db_session,
            sample_llm_credential,
            is_active=False
        )

        # Assert
        assert result.is_active is False

    def test_update_multiple_fields(self, db_session, sample_llm_credential, sample_organization):
        """Test updating multiple fields at once"""
        # Arrange
        new_key = "sk-updated1234567890"

        # Act
        result = cred_crud.update(
            db_session,
            sample_llm_credential,
            api_key=new_key,
            default_model="gpt-4o",
            is_active=False
        )

        # Assert
        assert result.default_model == "gpt-4o"
        assert result.is_active is False
        decrypted = cred_crud.get_decrypted_api_key(
            db_session, sample_organization.id, LLMProvider.OPENAI
        )
        # Note: Won't find it because is_active=False
        assert decrypted is None
        
        # Check by getting credential directly
        db_session.refresh(sample_llm_credential)
        from app.core.encryption import decrypt_api_key
        assert decrypt_api_key(sample_llm_credential.encrypted_api_key) == new_key

    def test_update_no_changes(self, db_session, sample_llm_credential):
        """Test updating with no changes"""
        # Arrange
        original_model = sample_llm_credential.default_model

        # Act
        result = cred_crud.update(db_session, sample_llm_credential)

        # Assert
        assert result.default_model == original_model


class TestDelete:
    """Tests for delete()"""

    def test_delete_success(self, db_session, sample_llm_credential):
        """Test successfully deleting a credential"""
        # Arrange
        cred_id = sample_llm_credential.id

        # Act
        cred_crud.delete(db_session, sample_llm_credential)

        # Assert
        deleted = cred_crud.get_by_id(db_session, cred_id)
        assert deleted is None

    def test_delete_removes_from_database(self, db_session, sample_organization):
        """Test that delete actually removes from database"""
        # Arrange
        cred = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.ANTHROPIC,
            api_key="sk-ant-test1234567890"
        )
        cred_id = cred.id

        # Act
        cred_crud.delete(db_session, cred)

        # Assert
        assert cred_crud.get_by_id(db_session, cred_id) is None
        assert cred_crud.get_by_org_and_provider(
            db_session, sample_organization.id, LLMProvider.ANTHROPIC
        ) is None


class TestGetMaskedKey:
    """Tests for get_masked_key()"""

    def test_get_masked_key_success(self, db_session, sample_llm_credential):
        """Test getting masked API key"""
        # Act
        result = cred_crud.get_masked_key(sample_llm_credential)

        # Assert
        assert result.startswith("****...")
        assert result.endswith("cdef")  # Last 4 chars of sk-test1234567890abcdef
        assert "sk-test1234567890abcdef" not in result

    def test_get_masked_key_format(self, db_session, sample_organization):
        """Test masked key format for different keys"""
        # Arrange
        cred = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.OPENAI,
            api_key="sk-verylongkey1234567890abcdefghijklmnop"
        )

        # Act
        result = cred_crud.get_masked_key(cred)

        # Assert
        assert result == "****...mnop"  # Last 4 chars

    def test_get_masked_key_short_key(self, db_session, sample_organization):
        """Test masking very short keys"""
        # Arrange - Create with short test key
        cred = cred_crud.create(
            db_session,
            organization_id=sample_organization.id,
            provider=LLMProvider.GOOGLE,
            api_key="AIzaShortKey"  # 12 chars
        )

        # Act
        result = cred_crud.get_masked_key(cred)

        # Assert
        assert result.startswith("****...")
        assert "tKey" in result  # Last 4 chars
