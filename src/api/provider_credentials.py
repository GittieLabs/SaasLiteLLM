"""
Provider Credentials API endpoints
Manage AI provider API keys for organizations
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.provider_credentials import ProviderCredential, ProviderType
from ..models.job_tracking import get_db
from cryptography.fernet import InvalidToken
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/provider-credentials", tags=["provider-credentials"])


# Request/Response Models
class ProviderCredentialCreateRequest(BaseModel):
    organization_id: str
    provider: str  # openai, anthropic, gemini, fireworks
    api_key: str
    api_base: Optional[str] = None
    credential_name: str
    created_by: Optional[str] = None


class ProviderCredentialUpdateRequest(BaseModel):
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    credential_name: Optional[str] = None
    is_active: Optional[bool] = None
    updated_by: Optional[str] = None


class ProviderCredentialResponse(BaseModel):
    credential_id: str
    organization_id: str
    provider: str
    credential_name: str
    api_base: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    has_api_key: bool


# Endpoints
@router.get("")
async def list_provider_credentials(
    organization_id: Optional[str] = None,
    provider: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    List provider credentials with optional filters
    """
    query = db.query(ProviderCredential)

    if organization_id:
        query = query.filter(ProviderCredential.organization_id == organization_id)

    if provider:
        try:
            provider_enum = ProviderType(provider.lower())
            query = query.filter(ProviderCredential.provider == provider_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider: {provider}. Must be one of: openai, anthropic, gemini, fireworks"
            )

    if active_only:
        query = query.filter(ProviderCredential.is_active == True)

    credentials = query.all()

    return [cred.to_dict() for cred in credentials]


@router.post("/create", response_model=ProviderCredentialResponse)
async def create_provider_credential(
    request: ProviderCredentialCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new provider credential with encrypted API key
    """
    # Validate provider
    try:
        provider_enum = ProviderType(request.provider.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {request.provider}. Must be one of: openai, anthropic, gemini, fireworks"
        )

    # Verify organization exists
    from ..models.organizations import Organization
    org = db.query(Organization).filter(
        Organization.organization_id == request.organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Organization '{request.organization_id}' not found"
        )

    # Create credential
    credential = ProviderCredential(
        organization_id=request.organization_id,
        provider=provider_enum,
        credential_name=request.credential_name,
        api_base=request.api_base,
        created_by=request.created_by
    )

    # Set encrypted API key
    try:
        credential.set_api_key(request.api_key)
    except Exception as e:
        logger.error(f"Failed to encrypt API key: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to encrypt API key: {str(e)}"
        )

    # Check for unique constraint violation (one active credential per provider per org)
    try:
        db.add(credential)
        db.commit()
        db.refresh(credential)
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError creating credential: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Organization '{request.organization_id}' already has an active credential for provider '{request.provider}'. Deactivate the existing one first or update it."
        )

    logger.info(f"Created provider credential {credential.credential_id} for org {request.organization_id}, provider {request.provider}")

    return ProviderCredentialResponse(**credential.to_dict())


@router.get("/{credential_id}")
async def get_provider_credential(
    credential_id: str,
    include_api_key: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get provider credential details

    WARNING: Set include_api_key=true to expose decrypted API key.
    Only use when absolutely necessary and ensure response is secured.
    """
    credential = db.query(ProviderCredential).filter(
        ProviderCredential.credential_id == credential_id
    ).first()

    if not credential:
        raise HTTPException(
            status_code=404,
            detail=f"Provider credential '{credential_id}' not found"
        )

    if include_api_key:
        return credential.to_dict_with_key()
    else:
        return credential.to_dict()


@router.get("/organization/{organization_id}")
async def get_organization_credentials(
    organization_id: str,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all provider credentials for an organization
    """
    # Verify organization exists
    from ..models.organizations import Organization
    org = db.query(Organization).filter(
        Organization.organization_id == organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Organization '{organization_id}' not found"
        )

    query = db.query(ProviderCredential).filter(
        ProviderCredential.organization_id == organization_id
    )

    if active_only:
        query = query.filter(ProviderCredential.is_active == True)

    credentials = query.all()

    return {
        "organization_id": organization_id,
        "credentials": [cred.to_dict() for cred in credentials]
    }


@router.get("/organization/{organization_id}/provider/{provider}")
async def get_active_credential_for_provider(
    organization_id: str,
    provider: str,
    include_api_key: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get the active provider credential for a specific provider and organization

    This is the main endpoint used by the LLM call service to retrieve credentials.
    """
    # Validate provider
    try:
        provider_enum = ProviderType(provider.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {provider}. Must be one of: openai, anthropic, gemini, fireworks"
        )

    credential = db.query(ProviderCredential).filter(
        ProviderCredential.organization_id == organization_id,
        ProviderCredential.provider == provider_enum,
        ProviderCredential.is_active == True
    ).first()

    if not credential:
        raise HTTPException(
            status_code=404,
            detail=f"No active credential found for organization '{organization_id}' and provider '{provider}'"
        )

    if include_api_key:
        return credential.to_dict_with_key()
    else:
        return credential.to_dict()


@router.put("/{credential_id}")
async def update_provider_credential(
    credential_id: str,
    request: ProviderCredentialUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update provider credential
    """
    credential = db.query(ProviderCredential).filter(
        ProviderCredential.credential_id == credential_id
    ).first()

    if not credential:
        raise HTTPException(
            status_code=404,
            detail=f"Provider credential '{credential_id}' not found"
        )

    # Update fields if provided
    if request.api_key is not None:
        try:
            credential.set_api_key(request.api_key)
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to encrypt API key: {str(e)}"
            )

    if request.api_base is not None:
        credential.api_base = request.api_base

    if request.credential_name is not None:
        credential.credential_name = request.credential_name

    if request.is_active is not None:
        credential.is_active = request.is_active

    if request.updated_by is not None:
        credential.updated_by = request.updated_by

    try:
        db.commit()
        db.refresh(credential)
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError updating credential: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Update would violate unique constraint. Organization can only have one active credential per provider."
        )

    logger.info(f"Updated provider credential {credential_id}")

    return credential.to_dict()


@router.delete("/{credential_id}")
async def delete_provider_credential(
    credential_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a provider credential

    WARNING: This will permanently delete the credential.
    Consider deactivating instead by setting is_active=false.
    """
    credential = db.query(ProviderCredential).filter(
        ProviderCredential.credential_id == credential_id
    ).first()

    if not credential:
        raise HTTPException(
            status_code=404,
            detail=f"Provider credential '{credential_id}' not found"
        )

    org_id = credential.organization_id
    provider = credential.provider.value

    db.delete(credential)
    db.commit()

    logger.info(f"Deleted provider credential {credential_id} for org {org_id}, provider {provider}")

    return {
        "credential_id": credential_id,
        "message": f"Provider credential deleted successfully"
    }


@router.put("/{credential_id}/deactivate")
async def deactivate_provider_credential(
    credential_id: str,
    db: Session = Depends(get_db)
):
    """
    Deactivate a provider credential (safer than deletion)
    """
    credential = db.query(ProviderCredential).filter(
        ProviderCredential.credential_id == credential_id
    ).first()

    if not credential:
        raise HTTPException(
            status_code=404,
            detail=f"Provider credential '{credential_id}' not found"
        )

    credential.is_active = False
    db.commit()

    return {
        "credential_id": credential_id,
        "is_active": False,
        "message": "Provider credential deactivated successfully"
    }


@router.put("/{credential_id}/activate")
async def activate_provider_credential(
    credential_id: str,
    db: Session = Depends(get_db)
):
    """
    Activate a provider credential

    Note: Will fail if another credential for the same org+provider is already active.
    """
    credential = db.query(ProviderCredential).filter(
        ProviderCredential.credential_id == credential_id
    ).first()

    if not credential:
        raise HTTPException(
            status_code=404,
            detail=f"Provider credential '{credential_id}' not found"
        )

    credential.is_active = True

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError activating credential: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot activate: organization already has an active credential for this provider. Deactivate the other one first."
        )

    return {
        "credential_id": credential_id,
        "is_active": True,
        "message": "Provider credential activated successfully"
    }
