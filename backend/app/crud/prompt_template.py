"""
CRUD operations for PromptTemplate model.

Provides functions for managing organization-specific prompt templates.
Each organization gets a default v0 template created from hardcoded defaults.
"""
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate


def get_by_id(db: Session, template_id: uuid.UUID) -> Optional[PromptTemplate]:
    """
    Get a template by ID.

    Args:
        db: Database session
        template_id: Template UUID

    Returns:
        PromptTemplate object if found, None otherwise
    """
    return db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()


def get_by_org(db: Session, organization_id: uuid.UUID) -> List[PromptTemplate]:
    """
    Get all templates for an organization.

    Args:
        db: Database session
        organization_id: Organization UUID

    Returns:
        List of PromptTemplate objects, active first, then by updated_at desc
    """
    return (
        db.query(PromptTemplate)
        .filter(PromptTemplate.organization_id == organization_id)
        .order_by(PromptTemplate.is_active.desc(), PromptTemplate.updated_at.desc())
        .all()
    )


def get_active_for_org(
    db: Session, organization_id: uuid.UUID
) -> Optional[PromptTemplate]:
    """
    Get the active template for an organization.

    Args:
        db: Database session
        organization_id: Organization UUID

    Returns:
        Active PromptTemplate if found, None otherwise
    """
    return (
        db.query(PromptTemplate)
        .filter(
            PromptTemplate.organization_id == organization_id,
            PromptTemplate.is_active == True,
        )
        .first()
    )


def create(
    db: Session,
    *,
    organization_id: uuid.UUID,
    name: str,
    version: str,
    system_prompt: str,
    user_template: str,
    is_active: bool = False,
) -> PromptTemplate:
    """
    Create a new prompt template.

    Args:
        db: Database session
        organization_id: Organization UUID
        name: Template name
        version: Version identifier
        system_prompt: System prompt text
        user_template: User prompt template (must contain {transcript})
        is_active: Whether to set as active (deactivates others if True)

    Returns:
        Created PromptTemplate object
    """
    # If setting as active, deactivate others for this org
    if is_active:
        _deactivate_org_templates(db, organization_id)

    template = PromptTemplate(
        organization_id=organization_id,
        name=name,
        version=version,
        system_prompt=system_prompt,
        user_template=user_template,
        is_active=is_active,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def create_default_for_org(db: Session, organization_id: uuid.UUID) -> PromptTemplate:
    """
    Create the default v0 template for a new organization.

    Uses the hardcoded SYSTEM and USER_TEMPLATE from prompt_templates.py.
    This is automatically set as active.

    Args:
        db: Database session
        organization_id: Organization UUID

    Returns:
        Created PromptTemplate object (v0, active)
    """
    from app.prompts.prompt_templates import SYSTEM, USER_TEMPLATE

    return create(
        db,
        organization_id=organization_id,
        name="Default SPIN Assessment",
        version="v0",
        system_prompt=SYSTEM,
        user_template=USER_TEMPLATE,
        is_active=True,
    )


def update(
    db: Session,
    template: PromptTemplate,
    *,
    name: Optional[str] = None,
    version: Optional[str] = None,
    system_prompt: Optional[str] = None,
    user_template: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> PromptTemplate:
    """
    Update an existing prompt template.

    Args:
        db: Database session
        template: PromptTemplate object to update
        name: New template name
        version: New version identifier
        system_prompt: New system prompt
        user_template: New user template
        is_active: New active status

    Returns:
        Updated PromptTemplate object
    """
    if name is not None:
        template.name = name
    if version is not None:
        template.version = version
    if system_prompt is not None:
        template.system_prompt = system_prompt
    if user_template is not None:
        template.user_template = user_template
    if is_active is not None:
        if is_active:
            _deactivate_org_templates(db, template.organization_id)
        template.is_active = is_active

    db.commit()
    db.refresh(template)
    return template


def delete(db: Session, template: PromptTemplate) -> None:
    """
    Delete a prompt template.

    Args:
        db: Database session
        template: PromptTemplate object to delete
    """
    db.delete(template)
    db.commit()


def _deactivate_org_templates(db: Session, organization_id: uuid.UUID) -> None:
    """
    Deactivate all templates for an organization.

    Called before setting a new template as active to ensure only one is active.

    Args:
        db: Database session
        organization_id: Organization UUID
    """
    db.query(PromptTemplate).filter(
        PromptTemplate.organization_id == organization_id,
        PromptTemplate.is_active == True,
    ).update({"is_active": False})

