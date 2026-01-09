"""
CRUD operations for LLMCredential model.

Provides functions for managing organization LLM API credentials.
All API keys are encrypted before storage and decrypted on retrieval.
"""
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.encryption import decrypt_api_key, encrypt_api_key, mask_api_key
from app.models.llm_credential import LLMCredential, LLMProvider


def get_by_id(db: Session, credential_id: uuid.UUID) -> Optional[LLMCredential]:
    """
    Get a credential by ID.

    Args:
        db: Database session
        credential_id: Credential UUID

    Returns:
        LLMCredential object if found, None otherwise
    """
    return db.query(LLMCredential).filter(LLMCredential.id == credential_id).first()


def get_by_org(db: Session, organization_id: uuid.UUID) -> List[LLMCredential]:
    """
    Get all credentials for an organization.

    Args:
        db: Database session
        organization_id: Organization UUID

    Returns:
        List of LLMCredential objects
    """
    return (
        db.query(LLMCredential)
        .filter(LLMCredential.organization_id == organization_id)
        .order_by(LLMCredential.provider)
        .all()
    )


def get_by_org_and_provider(
    db: Session, organization_id: uuid.UUID, provider: LLMProvider
) -> Optional[LLMCredential]:
    """
    Get a specific credential for an organization and provider.

    Args:
        db: Database session
        organization_id: Organization UUID
        provider: LLM provider enum

    Returns:
        LLMCredential if found, None otherwise
    """
    return (
        db.query(LLMCredential)
        .filter(
            LLMCredential.organization_id == organization_id,
            LLMCredential.provider == provider,
            LLMCredential.is_active == True,
        )
        .first()
    )


def get_decrypted_api_key(
    db: Session, organization_id: uuid.UUID, provider: LLMProvider
) -> Optional[str]:
    """
    Get the decrypted API key for an organization and provider.

    This is the primary function for internal use when making LLM calls.

    Args:
        db: Database session
        organization_id: Organization UUID
        provider: LLM provider enum

    Returns:
        Decrypted API key string if found, None otherwise

    Raises:
        ValueError: If decryption fails
    """
    credential = get_by_org_and_provider(db, organization_id, provider)
    if not credential:
        return None

    return decrypt_api_key(credential.encrypted_api_key)


def create(
    db: Session,
    *,
    organization_id: uuid.UUID,
    provider: LLMProvider,
    api_key: str,
    default_model: Optional[str] = None,
) -> LLMCredential:
    """
    Create a new LLM credential.

    Args:
        db: Database session
        organization_id: Organization UUID
        provider: LLM provider enum
        api_key: Plain text API key (will be encrypted)
        default_model: Optional default model name

    Returns:
        Created LLMCredential object

    Raises:
        ValueError: If a credential already exists for this org/provider
    """
    # Check for existing credential
    existing = get_by_org_and_provider(db, organization_id, provider)
    if existing:
        raise ValueError(
            f"Credential for provider '{provider.value}' already exists. Use update instead."
        )

    encrypted_key = encrypt_api_key(api_key)

    credential = LLMCredential(
        organization_id=organization_id,
        provider=provider,
        encrypted_api_key=encrypted_key,
        default_model=default_model,
        is_active=True,
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential


def update(
    db: Session,
    credential: LLMCredential,
    *,
    api_key: Optional[str] = None,
    default_model: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> LLMCredential:
    """
    Update an existing LLM credential.

    Args:
        db: Database session
        credential: LLMCredential object to update
        api_key: New plain text API key (will be encrypted)
        default_model: New default model name
        is_active: New active status

    Returns:
        Updated LLMCredential object
    """
    if api_key is not None:
        credential.encrypted_api_key = encrypt_api_key(api_key)

    if default_model is not None:
        credential.default_model = default_model

    if is_active is not None:
        credential.is_active = is_active

    db.commit()
    db.refresh(credential)
    return credential


def delete(db: Session, credential: LLMCredential) -> None:
    """
    Delete an LLM credential.

    Args:
        db: Database session
        credential: LLMCredential object to delete
    """
    db.delete(credential)
    db.commit()


def get_masked_key(credential: LLMCredential) -> str:
    """
    Get a masked version of the API key for display.

    Args:
        credential: LLMCredential object

    Returns:
        Masked string like "****...xxxx"
    """
    try:
        decrypted = decrypt_api_key(credential.encrypted_api_key)
        return mask_api_key(decrypted)
    except ValueError:
        return "****...????  (decryption error)"

