"""
LLM Credentials management endpoints.

Allows organization admins to manage LLM provider API keys.
All API keys are encrypted at rest and never returned in full.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.encryption import validate_api_key_format
from app.core.jwt_dependency import get_current_user
from app.crud import llm_credential as cred_crud
from app.models.llm_credential import LLMProvider
from app.models.user import User
from app.routers.deps import get_db
from app.schemas.llm_credential import (
    LLMCredentialCreate,
    LLMCredentialListResponse,
    LLMCredentialResponse,
    LLMCredentialUpdate,
    LLMProviderEnum,
    PROVIDER_INFO,
    ProviderListResponse,
)

router = APIRouter(prefix="/llm-credentials", tags=["llm-credentials"])


def _require_admin(user: User) -> None:
    """Require user to be a superuser (admin)."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can manage LLM credentials",
        )


def _require_org(user: User) -> UUID:
    """Require user to belong to an organization."""
    if not user.organization_id:
        raise HTTPException(
            status_code=400,
            detail="User must belong to an organization to manage LLM credentials",
        )
    return user.organization_id


def _provider_enum_to_model(provider: LLMProviderEnum) -> LLMProvider:
    """Convert schema enum to model enum."""
    return LLMProvider(provider.value)


def _credential_to_response(cred) -> LLMCredentialResponse:
    """Convert a credential model to response schema with masked key."""
    return LLMCredentialResponse(
        id=cred.id,
        organization_id=cred.organization_id,
        provider=LLMProviderEnum(cred.provider.value),
        masked_key=cred_crud.get_masked_key(cred),
        default_model=cred.default_model,
        is_active=cred.is_active,
        created_at=cred.created_at,
        updated_at=cred.updated_at,
    )


@router.get("/providers", response_model=ProviderListResponse)
def list_providers(
    current_user: User = Depends(get_current_user),
):
    """
    List all supported LLM providers.

    Returns information about each provider including default models
    and documentation links.
    """
    return ProviderListResponse(providers=PROVIDER_INFO)


@router.get("", response_model=LLMCredentialListResponse)
def list_credentials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all LLM credentials for the current user's organization.

    API keys are masked for security - only last 4 characters shown.
    Requires authentication.
    """
    org_id = _require_org(current_user)

    credentials = cred_crud.get_by_org(db, org_id)
    credential_responses = [_credential_to_response(cred) for cred in credentials]

    return LLMCredentialListResponse(
        credentials=credential_responses,
        providers=PROVIDER_INFO,
    )


@router.post("", response_model=LLMCredentialResponse, status_code=201)
def create_credential(
    data: LLMCredentialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new LLM credential.

    Only one credential per provider per organization.
    Requires admin privileges.
    """
    _require_admin(current_user)
    org_id = _require_org(current_user)

    # Validate API key format
    validation_error = validate_api_key_format(data.provider.value, data.api_key)
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)

    # Check for existing credential
    provider_model = _provider_enum_to_model(data.provider)
    existing = cred_crud.get_by_org_and_provider(db, org_id, provider_model)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Credential for {data.provider.value} already exists. Use PATCH to update.",
        )

    credential = cred_crud.create(
        db,
        organization_id=org_id,
        provider=provider_model,
        api_key=data.api_key,
        default_model=data.default_model,
    )

    return _credential_to_response(credential)


@router.patch("/{credential_id}", response_model=LLMCredentialResponse)
def update_credential(
    credential_id: str,
    data: LLMCredentialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing LLM credential.

    Supports partial updates - only provided fields are updated.
    Requires admin privileges.
    """
    _require_admin(current_user)
    org_id = _require_org(current_user)

    try:
        uuid_id = UUID(credential_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    credential = cred_crud.get_by_id(db, uuid_id)
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Ensure credential belongs to user's organization
    if credential.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Validate new API key format if provided
    if data.api_key:
        validation_error = validate_api_key_format(
            credential.provider.value, data.api_key
        )
        if validation_error:
            raise HTTPException(status_code=400, detail=validation_error)

    update_kwargs = {}
    if data.api_key is not None:
        update_kwargs["api_key"] = data.api_key
    if data.default_model is not None:
        update_kwargs["default_model"] = data.default_model
    if data.is_active is not None:
        update_kwargs["is_active"] = data.is_active

    updated = cred_crud.update(db, credential, **update_kwargs)
    return _credential_to_response(updated)


@router.delete("/{credential_id}", status_code=204)
def delete_credential(
    credential_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an LLM credential.

    Permanently removes the credential. Requires admin privileges.
    """
    _require_admin(current_user)
    org_id = _require_org(current_user)

    try:
        uuid_id = UUID(credential_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    credential = cred_crud.get_by_id(db, uuid_id)
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Ensure credential belongs to user's organization
    if credential.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Credential not found")

    cred_crud.delete(db, credential)
    return None

