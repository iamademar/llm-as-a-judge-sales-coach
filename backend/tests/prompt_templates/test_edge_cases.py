"""
Edge case tests for prompt template API endpoints.

Tests cover:
- Authentication requirements
- Authorization checks (admin vs non-admin)
- Input validation
- Delete safeguards
- Activation logic
- Users without organization
"""
import pytest


class TestAuthenticationRequired:
    """Tests that all endpoints require authentication"""

    def test_get_defaults_requires_auth(self, test_client):
        """Test GET /defaults requires authentication"""
        response = test_client.get("/prompt-templates/defaults")
        assert response.status_code == 403

    def test_list_templates_requires_auth(self, test_client):
        """Test GET /prompt-templates requires authentication"""
        response = test_client.get("/prompt-templates")
        assert response.status_code == 403

    def test_get_active_requires_auth(self, test_client):
        """Test GET /active requires authentication"""
        response = test_client.get("/prompt-templates/active")
        assert response.status_code == 403

    def test_get_by_id_requires_auth(self, test_client, sample_prompt_template):
        """Test GET /{id} requires authentication"""
        response = test_client.get(f"/prompt-templates/{sample_prompt_template.id}")
        assert response.status_code == 403

    def test_create_requires_auth(self, test_client):
        """Test POST /prompt-templates requires authentication"""
        payload = {
            "name": "Test",
            "version": "v1",
            "system_prompt": "System prompt for testing",
            "user_template": "User {transcript}"
        }
        response = test_client.post("/prompt-templates", json=payload)
        assert response.status_code == 403

    def test_update_requires_auth(self, test_client, sample_prompt_template):
        """Test PATCH /{id} requires authentication"""
        response = test_client.patch(
            f"/prompt-templates/{sample_prompt_template.id}",
            json={"name": "New Name"}
        )
        assert response.status_code == 403

    def test_activate_requires_auth(self, test_client, sample_prompt_template):
        """Test POST /{id}/activate requires authentication"""
        response = test_client.post(
            f"/prompt-templates/{sample_prompt_template.id}/activate"
        )
        assert response.status_code == 403

    def test_preview_requires_auth(self, test_client):
        """Test POST /preview requires authentication"""
        payload = {
            "name": "Test",
            "version": "v1",
            "system_prompt": "System prompt for testing",
            "user_template": "User {transcript}"
        }
        response = test_client.post("/prompt-templates/preview", json=payload)
        assert response.status_code == 403

    def test_delete_requires_auth(self, test_client, sample_prompt_template):
        """Test DELETE /{id} requires authentication"""
        response = test_client.delete(
            f"/prompt-templates/{sample_prompt_template.id}"
        )
        assert response.status_code == 403

    def test_invalid_token_returns_401(self, test_client):
        """Test that invalid JWT token returns 401"""
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}
        response = test_client.get(
            "/prompt-templates/defaults",
            headers=invalid_headers
        )
        assert response.status_code == 401


class TestAuthorizationChecks:
    """Tests for admin vs non-admin authorization"""

    def test_non_admin_cannot_create(self, test_client, auth_headers):
        """Test that non-admin users cannot create templates"""
        payload = {
            "name": "Test",
            "version": "v1",
            "system_prompt": "System prompt for testing",
            "user_template": "User {transcript}",
            "is_active": False
        }
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "admin" in response.json()["error"]["message"].lower()

    def test_non_admin_cannot_update(self, test_client, auth_headers, sample_prompt_template):
        """Test that non-admin users cannot update templates"""
        response = test_client.patch(
            f"/prompt-templates/{sample_prompt_template.id}",
            json={"name": "New Name"},
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "admin" in response.json()["error"]["message"].lower()

    def test_non_admin_cannot_delete(self, test_client, auth_headers, sample_prompt_template):
        """Test that non-admin users cannot delete templates"""
        response = test_client.delete(
            f"/prompt-templates/{sample_prompt_template.id}",
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "admin" in response.json()["error"]["message"].lower()

    def test_non_admin_cannot_activate(self, test_client, auth_headers, sample_prompt_template):
        """Test that non-admin users cannot activate templates"""
        response = test_client.post(
            f"/prompt-templates/{sample_prompt_template.id}/activate",
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "admin" in response.json()["error"]["message"].lower()

    def test_non_admin_can_preview(self, test_client, auth_headers):
        """Test that non-admin users CAN preview templates"""
        payload = {
            "name": "Test",
            "version": "v1",
            "system_prompt": "System prompt for testing",
            "user_template": "User {transcript}",
            "is_active": False
        }
        response = test_client.post(
            "/prompt-templates/preview",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_non_admin_can_list(self, test_client, auth_headers):
        """Test that non-admin users CAN list templates"""
        response = test_client.get(
            "/prompt-templates",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_non_admin_can_get_by_id(self, test_client, auth_headers, sample_prompt_template):
        """Test that non-admin users CAN get templates by ID"""
        response = test_client.get(
            f"/prompt-templates/{sample_prompt_template.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_non_admin_can_get_active(self, test_client, auth_headers, sample_prompt_template):
        """Test that non-admin users CAN get active template"""
        response = test_client.get(
            "/prompt-templates/active",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_non_admin_can_get_defaults(self, test_client, auth_headers):
        """Test that non-admin users CAN get defaults"""
        response = test_client.get(
            "/prompt-templates/defaults",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestValidation:
    """Tests for input validation"""

    def test_missing_transcript_placeholder_in_create(self, test_client, admin_auth_headers):
        """Test that create validates {transcript} placeholder"""
        payload = {
            "name": "Invalid",
            "version": "v1",
            "system_prompt": "System prompt",
            "user_template": "Missing the placeholder"
        }
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )
        assert response.status_code == 422
        response_data = response.json()
        assert "transcript" in str(response_data).lower()

    def test_missing_transcript_placeholder_in_update(
        self, test_client, admin_auth_headers, sample_prompt_template
    ):
        """Test that update validates {transcript} placeholder"""
        payload = {"user_template": "Missing the placeholder"}
        response = test_client.patch(
            f"/prompt-templates/{sample_prompt_template.id}",
            json=payload,
            headers=admin_auth_headers
        )
        assert response.status_code == 422
        response_data = response.json()
        assert "transcript" in str(response_data).lower()

    def test_empty_name_rejected(self, test_client, admin_auth_headers):
        """Test that empty name is rejected"""
        payload = {
            "name": "",
            "version": "v1",
            "system_prompt": "System prompt",
            "user_template": "User {transcript}"
        }
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )
        assert response.status_code == 422

    def test_system_prompt_too_short(self, test_client, admin_auth_headers):
        """Test that system prompt must meet minimum length"""
        payload = {
            "name": "Test",
            "version": "v1",
            "system_prompt": "Short",  # Too short
            "user_template": "User {transcript}"
        }
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )
        assert response.status_code == 422

    def test_user_template_too_short(self, test_client, admin_auth_headers):
        """Test that user template must meet minimum length"""
        payload = {
            "name": "Test",
            "version": "v1",
            "system_prompt": "System prompt that is long enough",
            "user_template": "{trans}"  # Too short - needs {transcript} placeholder and min 10 chars
        }
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )
        assert response.status_code == 422

    def test_invalid_uuid_format_in_get(self, test_client, auth_headers):
        """Test that invalid UUID format returns 400"""
        response = test_client.get(
            "/prompt-templates/not-a-uuid",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid UUID" in response.json()["error"]["message"]

    def test_invalid_uuid_format_in_update(self, test_client, admin_auth_headers):
        """Test that invalid UUID format returns 400"""
        response = test_client.patch(
            "/prompt-templates/not-a-uuid",
            json={"name": "Test"},
            headers=admin_auth_headers
        )
        assert response.status_code == 400
        assert "Invalid UUID" in response.json()["error"]["message"]

    def test_invalid_uuid_format_in_activate(self, test_client, admin_auth_headers):
        """Test that invalid UUID format returns 400"""
        response = test_client.post(
            "/prompt-templates/not-a-uuid/activate",
            headers=admin_auth_headers
        )
        assert response.status_code == 400
        assert "Invalid UUID" in response.json()["error"]["message"]

    def test_invalid_uuid_format_in_delete(self, test_client, admin_auth_headers):
        """Test that invalid UUID format returns 400"""
        response = test_client.delete(
            "/prompt-templates/not-a-uuid",
            headers=admin_auth_headers
        )
        assert response.status_code == 400
        assert "Invalid UUID" in response.json()["error"]["message"]

    def test_name_exceeds_max_length(self, test_client, admin_auth_headers):
        """Test that name cannot exceed maximum length"""
        payload = {
            "name": "A" * 101,  # Max is 100
            "version": "v1",
            "system_prompt": "System prompt",
            "user_template": "User {transcript}"
        }
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )
        assert response.status_code == 422


class TestDeleteSafeguards:
    """Tests for delete operation safeguards"""

    def test_cannot_delete_only_template(
        self, test_client, admin_auth_headers, sample_prompt_template
    ):
        """Test that cannot delete the only template in organization"""
        response = test_client.delete(
            f"/prompt-templates/{sample_prompt_template.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 400
        assert "only template" in response.json()["error"]["message"].lower()

    def test_cannot_delete_active_template(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test that cannot delete active template"""
        from app.crud import prompt_template as template_crud
        
        # Arrange - Create two templates
        active = template_crud.create(
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
            f"/prompt-templates/{active.id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 400
        assert "active template" in response.json()["error"]["message"].lower()

    def test_must_activate_another_before_deleting_active(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test workflow: activate another, then delete previously active"""
        from app.crud import prompt_template as template_crud
        
        # Arrange - Create two templates
        template1 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 1",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        template2 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 2",
            version="v2",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act - Activate template2
        activate_response = test_client.post(
            f"/prompt-templates/{template2.id}/activate",
            headers=admin_auth_headers
        )
        assert activate_response.status_code == 200

        # Now delete template1 (no longer active)
        delete_response = test_client.delete(
            f"/prompt-templates/{template1.id}",
            headers=admin_auth_headers
        )

        # Assert
        assert delete_response.status_code == 204

    def test_can_delete_after_creating_replacement(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test that can delete template after creating a replacement"""
        from app.crud import prompt_template as template_crud
        
        # Arrange - Create first template
        template1 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 1",
            version="v1",
            system_prompt="System prompt for testing",
            user_template="User {transcript}",
            is_active=False
        )

        # Create second template
        payload = {
            "name": "Template 2",
            "version": "v2",
            "system_prompt": "System prompt 2 for testing",
            "user_template": "User {transcript}",
            "is_active": True
        }
        create_response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=admin_auth_headers
        )
        assert create_response.status_code == 201

        # Now delete template1
        delete_response = test_client.delete(
            f"/prompt-templates/{template1.id}",
            headers=admin_auth_headers
        )

        # Assert
        assert delete_response.status_code == 204


class TestActivationLogic:
    """Tests for template activation logic"""

    def test_only_one_template_active_per_org(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test that only one template can be active per organization"""
        from app.crud import prompt_template as template_crud
        
        # Arrange - Create two templates
        template1 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 1",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        template2 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 2",
            version="v2",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act - Activate template2
        response = test_client.post(
            f"/prompt-templates/{template2.id}/activate",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        
        # Verify only template2 is active
        db_session.refresh(template1)
        db_session.refresh(template2)
        assert template1.is_active is False
        assert template2.is_active is True

    def test_creating_with_is_active_true_deactivates_others(
        self, test_client, admin_auth_headers, db_session, sample_prompt_template
    ):
        """Test that creating template with is_active=True deactivates others"""
        # Arrange - Ensure existing template is active
        assert sample_prompt_template.is_active is True

        payload = {
            "name": "New Active",
            "version": "v2",
            "system_prompt": "System prompt for testing",
            "user_template": "User {transcript}",
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
        db_session.refresh(sample_prompt_template)
        assert sample_prompt_template.is_active is False

    def test_updating_with_is_active_true_deactivates_others(
        self, test_client, admin_auth_headers, db_session, sample_organization
    ):
        """Test that updating template with is_active=True deactivates others"""
        from app.crud import prompt_template as template_crud
        
        # Arrange - Create two templates
        template1 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 1",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        template2 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Template 2",
            version="v2",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act - Update template2 to be active
        response = test_client.patch(
            f"/prompt-templates/{template2.id}",
            json={"is_active": True},
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        db_session.refresh(template1)
        assert template1.is_active is False


class TestNoOrganization:
    """Tests for users without organization"""

    def test_user_without_org_cannot_list_templates(
        self, test_client, db_session, sample_user
    ):
        """Test that user without org_id gets 400 error"""
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

    def test_user_without_org_cannot_get_active(
        self, test_client, db_session, sample_user
    ):
        """Test that user without org_id gets 400 error"""
        from app.core.jwt_tokens import create_access_token
        
        # Arrange
        sample_user.organization_id = None
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {create_access_token(sub=sample_user.email)}"}

        # Act
        response = test_client.get(
            "/prompt-templates/active",
            headers=headers
        )

        # Assert
        assert response.status_code == 400
        assert "organization" in response.json()["error"]["message"].lower()

    def test_user_without_org_cannot_get_by_id(
        self, test_client, db_session, sample_user, sample_prompt_template
    ):
        """Test that user without org_id gets 400 error"""
        from app.core.jwt_tokens import create_access_token
        
        # Arrange
        sample_user.organization_id = None
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {create_access_token(sub=sample_user.email)}"}

        # Act
        response = test_client.get(
            f"/prompt-templates/{sample_prompt_template.id}",
            headers=headers
        )

        # Assert
        assert response.status_code == 400
        assert "organization" in response.json()["error"]["message"].lower()

    def test_admin_without_org_cannot_create(
        self, test_client, db_session, admin_user
    ):
        """Test that admin without org_id gets 400 error"""
        from app.core.jwt_tokens import create_access_token
        
        # Arrange
        admin_user.organization_id = None
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {create_access_token(sub=admin_user.email)}"}
        
        payload = {
            "name": "Test",
            "version": "v1",
            "system_prompt": "System prompt",
            "user_template": "User {transcript}"
        }

        # Act
        response = test_client.post(
            "/prompt-templates",
            json=payload,
            headers=headers
        )

        # Assert
        assert response.status_code == 400
        assert "organization" in response.json()["error"]["message"].lower()
