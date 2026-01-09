"""
Integration tests for prompt template API endpoints.

Tests cover all 9 endpoints from /prompt-templates router:
- GET /prompt-templates/defaults
- GET /prompt-templates
- GET /prompt-templates/active
- GET /prompt-templates/{id}
- POST /prompt-templates
- PATCH /prompt-templates/{id}
- POST /prompt-templates/{id}/activate
- POST /prompt-templates/preview
- DELETE /prompt-templates/{id}
"""
import pytest

from app.crud import prompt_template as template_crud


class TestGetDefaults:
    """Tests for GET /prompt-templates/defaults"""

    def test_get_defaults_returns_hardcoded_templates(self, test_client, auth_headers):
        """Test that defaults endpoint returns hardcoded system and user templates"""
        # Act
        response = test_client.get(
            "/prompt-templates/defaults",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "system_prompt" in data
        assert "user_prompt" in data
        assert "transcript_sample" in data
        assert "senior sales coach" in data["system_prompt"].lower()
        assert "{transcript}" not in data["user_prompt"]  # Should be rendered

    def test_get_defaults_requires_authentication(self, test_client):
        """Test that defaults endpoint requires authentication"""
        # Act
        response = test_client.get("/prompt-templates/defaults")

        # Assert
        assert response.status_code == 403

    def test_get_defaults_contains_sample_transcript(self, test_client, auth_headers):
        """Test that defaults include a sample transcript for preview"""
        # Act
        response = test_client.get(
            "/prompt-templates/defaults",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["transcript_sample"]) > 0
        assert "Rep:" in data["transcript_sample"]


class TestListTemplates:
    """Tests for GET /prompt-templates"""

    def test_list_templates_returns_org_templates(
        self, test_client, auth_headers, db_session, sample_prompt_template
    ):
        """Test listing returns all templates for user's organization"""
        # Act
        response = test_client.get(
            "/prompt-templates",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == str(sample_prompt_template.id)

    def test_list_templates_returns_empty_for_new_org(
        self, test_client, db_session, second_auth_headers
    ):
        """Test listing returns empty array for organization with no templates"""
        # Act
        response = test_client.get(
            "/prompt-templates",
            headers=second_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_templates_sorted_active_first(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test that templates are sorted with active first, then by updated_at"""
        # Arrange - Create multiple templates
        template1 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 1",
            version="v1",
            system_prompt="System prompt 1",
            user_template="User template {transcript}",
            is_active=False
        )
        template2 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 2",
            version="v2",
            system_prompt="System prompt 2",
            user_template="User template {transcript}",
            is_active=True
        )

        # Act
        response = test_client.get(
            "/prompt-templates",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        # Active template should be first
        assert data[0]["id"] == str(template2.id)
        assert data[0]["is_active"] is True

    def test_list_templates_requires_org_membership(
        self, test_client, db_session, sample_user
    ):
        """Test that user without organization gets error"""
        from app.core.jwt_tokens import create_access_token
        
        # Arrange - Remove org from user
        sample_user.organization_id = None
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {create_access_token(sub=sample_user.email)}"}

        # Act
        response = test_client.get(
            "/prompt-templates",
            headers=headers
        )

        # Assert
        assert response.status_code == 400
        assert "organization" in response.json()["error"]["message"].lower()


class TestGetActiveTemplate:
    """Tests for GET /prompt-templates/active"""

    def test_get_active_returns_active_template(
        self, test_client, auth_headers, sample_prompt_template
    ):
        """Test getting active template for organization"""
        # Act
        response = test_client.get(
            "/prompt-templates/active",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_prompt_template.id)
        assert data["is_active"] is True

    def test_get_active_404_when_no_active_template(
        self, test_client, second_auth_headers
    ):
        """Test 404 when organization has no active template"""
        # Act
        response = test_client.get(
            "/prompt-templates/active",
            headers=second_auth_headers
        )

        # Assert
        assert response.status_code == 404
        assert "No active template" in response.json()["error"]["message"]

    def test_get_active_error_message_helpful(
        self, test_client, second_auth_headers
    ):
        """Test error message includes helpful instructions"""
        # Act
        response = test_client.get(
            "/prompt-templates/active",
            headers=second_auth_headers
        )

        # Assert
        assert response.status_code == 404
        message = response.json()["error"]["message"]
        assert "POST /prompt-templates" in message


class TestGetTemplateById:
    """Tests for GET /prompt-templates/{id}"""

    def test_get_template_by_id_success(
        self, test_client, auth_headers, sample_prompt_template
    ):
        """Test getting specific template by ID"""
        # Act
        response = test_client.get(
            f"/prompt-templates/{sample_prompt_template.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_prompt_template.id)
        assert data["name"] == sample_prompt_template.name
        assert data["version"] == sample_prompt_template.version

    def test_get_template_404_for_nonexistent_id(
        self, test_client, auth_headers
    ):
        """Test 404 when template doesn't exist"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = test_client.get(
            f"/prompt-templates/{fake_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_get_template_400_for_invalid_uuid(
        self, test_client, auth_headers
    ):
        """Test 400 for invalid UUID format"""
        # Act
        response = test_client.get(
            "/prompt-templates/not-a-uuid",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        assert "Invalid UUID" in response.json()["error"]["message"]

    def test_get_template_only_returns_own_org_templates(
        self, test_client, auth_headers, db_session, second_organization
    ):
        """Test that users can only get templates from their organization"""
        # Arrange - Create template in different org
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Template",
            version="v1",
            system_prompt="System prompt",
            user_template="User template {transcript}",
            is_active=True
        )

        # Act
        response = test_client.get(
            f"/prompt-templates/{other_template.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404


class TestCreateTemplate:
    """Tests for POST /prompt-templates"""

    def test_create_template_success(
        self, test_client, admin_auth_headers, db_session
    ):
        """Test successful template creation by admin"""
        # Arrange
        payload = {
            "name": "Custom Template",
            "version": "v1",
            "system_prompt": "You are a custom sales coach",
            "user_template": "Analyze this transcript: {transcript}",
            "is_active": False
        }

        # Act
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["version"] == payload["version"]
        assert data["system_prompt"] == payload["system_prompt"]
        assert data["is_active"] is False
        assert "id" in data
        assert "organization_id" in data

    def test_create_template_inherits_org_from_user(
        self, test_client, admin_auth_headers, admin_user, db_session
    ):
        """Test that created template inherits organization_id from user"""
        # Arrange
        payload = {
            "name": "Test Template",
            "version": "v1",
            "system_prompt": "Test system prompt",
            "user_template": "Test {transcript}",
            "is_active": False
        }

        # Act
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["organization_id"] == str(admin_user.organization_id)

    def test_create_template_requires_admin(
        self, test_client, auth_headers
    ):
        """Test that non-admin users cannot create templates"""
        # Arrange
        payload = {
            "name": "Test Template",
            "version": "v1",
            "system_prompt": "Test system prompt",
            "user_template": "Test {transcript}",
            "is_active": False
        }

        # Act
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403
        assert "admin" in response.json()["error"]["message"].lower()

    def test_create_template_auto_deactivates_others_when_active(
        self, test_client, admin_auth_headers, db_session, sample_prompt_template
    ):
        """Test that creating active template deactivates others"""
        # Arrange - Ensure first template is active
        assert sample_prompt_template.is_active is True

        payload = {
            "name": "New Active Template",
            "version": "v2",
            "system_prompt": "New system prompt",
            "user_template": "New {transcript}",
            "is_active": True
        }

        # Act
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True

        # Verify old template was deactivated
        db_session.refresh(sample_prompt_template)
        assert sample_prompt_template.is_active is False

    def test_create_template_validates_transcript_placeholder(
        self, test_client, admin_auth_headers
    ):
        """Test that user_template must contain {transcript} placeholder"""
        # Arrange
        payload = {
            "name": "Invalid Template",
            "version": "v1",
            "system_prompt": "System prompt",
            "user_template": "Missing placeholder",
            "is_active": False
        }

        # Act
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert "transcript" in str(response_data).lower()


class TestUpdateTemplate:
    """Tests for PATCH /prompt-templates/{id}"""

    def test_update_template_partial(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test partial update of template (name only)"""
        # Arrange
        template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Original Name",
            version="v1",
            system_prompt="System prompt",
            user_template="User {transcript}",
            is_active=False
        )
        
        payload = {"name": "Updated Name"}

        # Act
        response = test_client.patch(
            f"/prompt-templates/{template.id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["version"] == "v1"  # Unchanged

    def test_update_template_full(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test full update of template"""
        # Arrange
        template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Original",
            version="v1",
            system_prompt="Original system",
            user_template="Original {transcript}",
            is_active=False
        )
        
        payload = {
            "name": "Updated Name",
            "version": "v2",
            "system_prompt": "Updated system",
            "user_template": "Updated {transcript}"
        }

        # Act
        response = test_client.patch(
            f"/prompt-templates/{template.id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["version"] == "v2"
        assert data["system_prompt"] == "Updated system"
        assert data["user_template"] == "Updated {transcript}"

    def test_update_template_requires_admin(
        self, test_client, auth_headers, sample_prompt_template
    ):
        """Test that non-admin cannot update templates"""
        # Arrange
        payload = {"name": "Hacked Name"}

        # Act
        response = test_client.patch(
            f"/prompt-templates/{sample_prompt_template.id}",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_update_template_404_for_nonexistent(
        self, test_client, admin_auth_headers
    ):
        """Test 404 when updating non-existent template"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"name": "New Name"}

        # Act
        response = test_client.patch(
            f"/prompt-templates/{fake_id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_update_template_validates_transcript_placeholder(
        self, test_client, admin_auth_headers, sample_prompt_template
    ):
        """Test that updating user_template validates {transcript} placeholder"""
        # Arrange
        payload = {"user_template": "Invalid template without placeholder"}

        # Act
        response = test_client.patch(
            f"/prompt-templates/{sample_prompt_template.id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert "transcript" in str(response_data).lower()


class TestActivateTemplate:
    """Tests for POST /prompt-templates/{id}/activate"""

    def test_activate_template_success(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test activating a template"""
        # Arrange
        template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Inactive Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act
        response = test_client.post(
            f"/prompt-templates/{template.id}/activate",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_activate_template_deactivates_others(
        self, test_client, admin_auth_headers, db_session, 
        sample_organization, sample_prompt_template
    ):
        """Test that activating template deactivates other templates"""
        # Arrange - Create second template
        assert sample_prompt_template.is_active is True
        
        template2 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 2",
            version="v2",
            system_prompt="System 2",
            user_template="User {transcript}",
            is_active=False
        )

        # Act
        response = test_client.post(
            f"/prompt-templates/{template2.id}/activate",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        db_session.refresh(sample_prompt_template)
        db_session.refresh(template2)
        assert sample_prompt_template.is_active is False
        assert template2.is_active is True

    def test_activate_template_requires_admin(
        self, test_client, auth_headers, sample_prompt_template
    ):
        """Test that non-admin cannot activate templates"""
        # Act
        response = test_client.post(
            f"/prompt-templates/{sample_prompt_template.id}/activate",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_activate_template_404_for_nonexistent(
        self, test_client, admin_auth_headers
    ):
        """Test 404 when activating non-existent template"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = test_client.post(
            f"/prompt-templates/{fake_id}/activate",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404


class TestPreviewTemplate:
    """Tests for POST /prompt-templates/preview"""

    def test_preview_template_renders_correctly(
        self, test_client, auth_headers
    ):
        """Test that preview renders template with sample transcript"""
        # Arrange
        payload = {
            "name": "Preview Test",
            "version": "v1",
            "system_prompt": "Custom system prompt",
            "user_template": "Custom user prompt: {transcript}",
            "is_active": False
        }

        # Act
        response = test_client.post(
            "/prompt-templates/preview",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "system_prompt" in data
        assert "user_prompt" in data
        assert "transcript_sample" in data
        assert data["system_prompt"] == "Custom system prompt"
        assert "Custom user prompt:" in data["user_prompt"]
        assert "{transcript}" not in data["user_prompt"]  # Should be rendered

    def test_preview_available_to_non_admins(
        self, test_client, auth_headers
    ):
        """Test that preview is available to non-admin users"""
        # Arrange
        payload = {
            "name": "Test",
            "version": "v1",
            "system_prompt": "System prompt for testing",
            "user_template": "User {transcript}",
            "is_active": False
        }

        # Act
        response = test_client.post(
            "/prompt-templates/preview",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200

    def test_preview_400_for_invalid_template(
        self, test_client, auth_headers
    ):
        """Test 422 when template has invalid syntax"""
        # Arrange - Missing {transcript} placeholder
        payload = {
            "name": "Invalid",
            "version": "v1",
            "system_prompt": "System prompt for testing",
            "user_template": "No placeholder",
            "is_active": False
        }

        # Act
        response = test_client.post(
            "/prompt-templates/preview",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 422


class TestDeleteTemplate:
    """Tests for DELETE /prompt-templates/{id}"""

    def test_delete_template_success(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test successful deletion of non-active template"""
        # Arrange - Create active and inactive templates
        active_template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Active",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        inactive_template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Inactive",
            version="v2",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act
        response = test_client.delete(
            f"/prompt-templates/{inactive_template.id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 204
        
        # Verify deletion
        deleted = template_crud.get_by_id(db_session, inactive_template.id)
        assert deleted is None

    def test_delete_template_400_when_only_template(
        self, test_client, admin_auth_headers, sample_prompt_template
    ):
        """Test that cannot delete the only template"""
        # Act
        response = test_client.delete(
            f"/prompt-templates/{sample_prompt_template.id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 400
        assert "only template" in response.json()["error"]["message"].lower()

    def test_delete_template_400_when_active(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test that cannot delete active template"""
        # Arrange - Create two templates
        active_template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Active",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Inactive",
            version="v2",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act
        response = test_client.delete(
            f"/prompt-templates/{active_template.id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 400
        assert "active template" in response.json()["error"]["message"].lower()

    def test_delete_template_requires_admin(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Test that non-admin cannot delete templates"""
        # Arrange
        template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Test",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act
        response = test_client.delete(
            f"/prompt-templates/{template.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_delete_template_404_for_nonexistent(
        self, test_client, admin_auth_headers
    ):
        """Test 404 when deleting non-existent template"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = test_client.delete(
            f"/prompt-templates/{fake_id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404
