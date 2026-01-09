"""
Prompt template management endpoints.

Allows organization admins to customize SPIN assessment prompts.
Each organization gets a default v0 template; admins can create custom versions.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.jwt_dependency import get_current_user
from app.crud import prompt_template as template_crud
from app.models.user import User
from app.prompts.prompt_templates import SYSTEM, USER_TEMPLATE, build_prompt
from app.routers.deps import get_db
from app.schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplatePreview,
    PromptTemplateResponse,
    PromptTemplateUpdate,
)

router = APIRouter(prefix="/prompt-templates", tags=["prompt-templates"])

# Sample transcript for preview functionality
SAMPLE_TRANSCRIPT = """Rep: Hi, thanks for taking my call today. Can you tell me a bit about your current sales process?
Buyer: Sure, we use a basic CRM but it's not giving us the insights we need.
Rep: I see. What specific insights are you missing?
Buyer: Mainly around deal progression and rep performance.
Rep: How is that impacting your team's ability to hit targets?"""


def _require_admin(user: User) -> None:
    """Require user to be a superuser (admin)."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can manage prompt templates",
        )


def _require_org(user: User):
    """Require user to belong to an organization."""
    if not user.organization_id:
        raise HTTPException(
            status_code=400,
            detail="User must belong to an organization to manage prompt templates",
        )
    return user.organization_id


@router.get("/defaults", response_model=PromptTemplatePreview)
def get_default_template(current_user: User = Depends(get_current_user)):
    """
    Get the default system prompt templates.

    Returns the hardcoded defaults used as v0 for new organizations.
    Useful for reference when creating custom templates.
    """
    system, user = build_prompt(SAMPLE_TRANSCRIPT)
    return PromptTemplatePreview(
        system_prompt=SYSTEM,
        user_prompt=user,
        transcript_sample=SAMPLE_TRANSCRIPT,
    )


@router.get("", response_model=List[PromptTemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all prompt templates for the current organization.

    Returns templates sorted by active status (active first), then by update time.
    Requires authentication.
    """
    org_id = _require_org(current_user)
    templates = template_crud.get_by_org(db, org_id)
    return templates


@router.get("/active", response_model=PromptTemplateResponse)
def get_active_template(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the active prompt template for the current organization.

    Requires authentication.
    Returns 404 if no active template found.
    """
    org_id = _require_org(current_user)
    template = template_crud.get_active_for_org(db, org_id)
    if not template:
        raise HTTPException(
            status_code=404,
            detail="No active template found. Use POST /prompt-templates to create one.",
        )
    return template


@router.get("/{template_id}", response_model=PromptTemplateResponse)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific prompt template by ID.

    Requires authentication.
    Returns 404 if template not found or belongs to different organization.
    """
    from uuid import UUID

    org_id = _require_org(current_user)

    try:
        uuid_id = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    template = template_crud.get_by_id(db, uuid_id)
    if not template or template.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("", response_model=PromptTemplateResponse, status_code=201)
def create_template(
    data: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new prompt template for the organization.

    Requires admin privileges.
    If is_active is True, other templates for this org will be deactivated.
    """
    _require_admin(current_user)
    org_id = _require_org(current_user)

    template = template_crud.create(
        db,
        organization_id=org_id,
        name=data.name,
        version=data.version,
        system_prompt=data.system_prompt,
        user_template=data.user_template,
        is_active=data.is_active,
    )
    return template


@router.patch("/{template_id}", response_model=PromptTemplateResponse)
def update_template(
    template_id: str,
    data: PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing prompt template.

    Supports partial updates - only provided fields are updated.
    Requires admin privileges.
    Returns 404 if template not found.
    """
    from uuid import UUID

    _require_admin(current_user)
    org_id = _require_org(current_user)

    try:
        uuid_id = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    template = template_crud.get_by_id(db, uuid_id)
    if not template or template.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Template not found")

    update_kwargs = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = template_crud.update(db, template, **update_kwargs)
    return updated


@router.post("/{template_id}/activate", response_model=PromptTemplateResponse)
def activate_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set a template as the active one for the organization.

    Deactivates all other templates for this organization.
    Requires admin privileges.
    Returns 404 if template not found.
    """
    from uuid import UUID

    _require_admin(current_user)
    org_id = _require_org(current_user)

    try:
        uuid_id = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    template = template_crud.get_by_id(db, uuid_id)
    if not template or template.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Template not found")

    updated = template_crud.update(db, template, is_active=True)
    return updated


@router.post("/preview", response_model=PromptTemplatePreview)
def preview_template(
    data: PromptTemplateCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Preview how a template renders with a sample transcript.

    Useful for testing templates before saving or activating.
    Does not require admin privileges (read-only operation).
    """
    try:
        system, user = build_prompt(
            SAMPLE_TRANSCRIPT,
            system_prompt=data.system_prompt,
            user_template=data.user_template,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Template error: {e}")

    return PromptTemplatePreview(
        system_prompt=system,
        user_prompt=user,
        transcript_sample=SAMPLE_TRANSCRIPT,
    )


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a prompt template.

    Cannot delete the only template or the active template.
    Requires admin privileges.
    Returns 404 if template not found.
    """
    from uuid import UUID

    _require_admin(current_user)
    org_id = _require_org(current_user)

    try:
        uuid_id = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    template = template_crud.get_by_id(db, uuid_id)
    if not template or template.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Template not found")

    # Prevent deleting the only template
    all_templates = template_crud.get_by_org(db, org_id)
    if len(all_templates) <= 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the only template. Create another template first.",
        )

    # Prevent deleting active template
    if template.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active template. Activate another template first.",
        )

    template_crud.delete(db, template)
    return None

