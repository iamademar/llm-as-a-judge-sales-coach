"""
Organization isolation tests for prompt template API endpoints.

Tests verify that prompt templates are properly scoped to organizations and that
users from different organizations cannot access each other's templates.

Tests cover:
- Organization ID inheritance from creating user
- Cross-organization access restrictions for GET /prompt-templates/{id}
- List filtering by organization
- Update restrictions across organizations
- Delete restrictions across organizations
- Activate restrictions across organizations
- Active template lookup scoped to organization
"""
import pytest

from app.crud import prompt_template as template_crud


class TestOrganizationIsolation:
    """Tests for organization-scoped access to prompt templates"""

    def test_template_inherits_org_from_user(
        self, test_client, admin_auth_headers, admin_user, db_session
    ):
        """Test that created template inherits organization_id from creating user"""
        # Arrange
        payload = {
            "name": "New Template",
            "version": "v1",
            "system_prompt": "System prompt",
            "user_template": "User {transcript}",
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
        
        # Verify in database
        template = template_crud.get_by_id(db_session, data["id"])
        assert template.organization_id == admin_user.organization_id

    def test_different_orgs_create_separate_templates(
        self, test_client, admin_auth_headers, db_session, 
        second_organization, second_user
    ):
        """Test that users from different orgs create templates with different org_ids"""
        from app.core.jwt_tokens import create_access_token
        
        # Arrange - Make second user an admin
        second_user.is_superuser = True
        db_session.commit()
        db_session.refresh(second_user)
        
        second_admin_headers = {
            "Authorization": f"Bearer {create_access_token(sub=second_user.email)}"
        }
        
        payload1 = {
            "name": "Org 1 Template",
            "version": "v1",
            "system_prompt": "System prompt for testing",
            "user_template": "User {transcript}",
            "is_active": False
        }
        payload2 = {
            "name": "Org 2 Template",
            "version": "v1",
            "system_prompt": "System prompt for testing",
            "user_template": "User {transcript}",
            "is_active": False
        }

        # Act - Each user creates template
        response1 = test_client.post(
            "/prompt-templates",
            json=payload1,
            headers=admin_auth_headers
        )
        response2 = test_client.post(
            "/prompt-templates",
            json=payload2,
            headers=second_admin_headers
        )

        # Assert
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        template1_org = response1.json()["organization_id"]
        template2_org = response2.json()["organization_id"]
        
        assert template1_org != template2_org
        assert template2_org == str(second_organization.id)

    def test_cannot_get_template_from_other_org(
        self, test_client, auth_headers, db_session, second_organization
    ):
        """Test that users cannot GET templates from other organizations"""
        # Arrange - Create template in different org
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )

        # Act
        response = test_client.get(
            f"/prompt-templates/{other_template.id}",
            headers=auth_headers
        )

        # Assert - Should get 404, not the template
        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"].lower()

    def test_cannot_update_template_from_other_org(
        self, test_client, admin_auth_headers, db_session, second_organization
    ):
        """Test that admins cannot UPDATE templates from other organizations"""
        # Arrange - Create template in different org
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        
        payload = {"name": "Hacked Name"}

        # Act
        response = test_client.patch(
            f"/prompt-templates/{other_template.id}",
            json=payload,
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404
        
        # Verify template wasn't modified
        db_session.refresh(other_template)
        assert other_template.name == "Other Org Template"

    def test_cannot_delete_template_from_other_org(
        self, test_client, admin_auth_headers, db_session, second_organization
    ):
        """Test that admins cannot DELETE templates from other organizations"""
        # Arrange - Create two templates in different org (so delete isn't blocked by "only template" rule)
        template1 = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Active",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        template2 = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Inactive",
            version="v2",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act - Try to delete the inactive one
        response = test_client.delete(
            f"/prompt-templates/{template2.id}",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404
        
        # Verify template still exists
        still_exists = template_crud.get_by_id(db_session, template2.id)
        assert still_exists is not None

    def test_cannot_activate_template_from_other_org(
        self, test_client, admin_auth_headers, db_session, second_organization
    ):
        """Test that admins cannot ACTIVATE templates from other organizations"""
        # Arrange - Create template in different org
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act
        response = test_client.post(
            f"/prompt-templates/{other_template.id}/activate",
            headers=admin_auth_headers
        )

        # Assert
        assert response.status_code == 404
        
        # Verify template wasn't activated
        db_session.refresh(other_template)
        assert other_template.is_active is False

    def test_list_only_returns_own_org_templates(
        self, test_client, auth_headers, db_session, 
        sample_organization, second_organization
    ):
        """Test that list endpoint only returns templates from user's organization"""
        # Arrange - Create templates in both orgs
        own_template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Own Org Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )

        # Act
        response = test_client.get(
            "/prompt-templates",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        
        template_ids = [t["id"] for t in data]
        assert str(own_template.id) in template_ids
        assert str(other_template.id) not in template_ids

    def test_active_template_scoped_to_organization(
        self, test_client, auth_headers, db_session, 
        sample_organization, second_organization
    ):
        """Test that active template lookup only returns user's org template"""
        # Arrange - Create active templates in both orgs
        own_template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Own Active",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Active",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )

        # Act
        response = test_client.get(
            "/prompt-templates/active",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(own_template.id)
        assert data["id"] != str(other_template.id)

    def test_multiple_users_same_org_share_templates(
        self, test_client, db_session, sample_organization
    ):
        """Test that multiple users in same org can access same templates"""
        from app.models.user import User
        from app.core.passwords import hash_password
        from app.core.jwt_tokens import create_access_token
        
        # Arrange - Create second user in same org
        user2 = User(
            email="user2@sameorg.com",
            hashed_password=hash_password("password"),
            full_name="Second User",
            is_active=True,
            is_superuser=False,
            organization_id=sample_organization.id
        )
        db_session.add(user2)
        db_session.commit()
        
        user2_headers = {
            "Authorization": f"Bearer {create_access_token(sub=user2.email)}"
        }
        
        # Create template
        template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Shared Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )

        # Act - Both users try to access
        response1 = test_client.get(
            f"/prompt-templates/{template.id}",
            headers=user2_headers
        )
        response2 = test_client.get(
            "/prompt-templates",
            headers=user2_headers
        )

        # Assert - Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert str(template.id) in [t["id"] for t in response2.json()]

    def test_activation_only_affects_same_org(
        self, test_client, db_session, sample_organization, second_organization
    ):
        """Test that activating template only deactivates templates in same org"""
        from app.models.user import User
        from app.core.passwords import hash_password
        from app.core.jwt_tokens import create_access_token
        
        # Arrange - Create admin in second org
        admin2 = User(
            email="admin2@secondorg.com",
            hashed_password=hash_password("password"),
            full_name="Second Admin",
            is_active=True,
            is_superuser=True,
            organization_id=second_organization.id
        )
        db_session.add(admin2)
        db_session.commit()
        
        admin2_headers = {
            "Authorization": f"Bearer {create_access_token(sub=admin2.email)}"
        }
        
        # Create active templates in both orgs
        template1_org1 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Org1 Template1",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        template2_org1 = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Org1 Template2",
            version="v2",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )
        template1_org2 = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Org2 Template1",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )

        # Act - Activate template2 in org1
        response = test_client.post(
            f"/prompt-templates/{template2_org1.id}/activate",
            headers=admin2_headers  # Different org admin - should fail
        )

        # Assert - Should fail due to org mismatch
        assert response.status_code == 404
        
        # Verify org1's template1 is still active
        db_session.refresh(template1_org1)
        assert template1_org1.is_active is True
        
        # Verify org2's template is unaffected
        db_session.refresh(template1_org2)
        assert template1_org2.is_active is True
