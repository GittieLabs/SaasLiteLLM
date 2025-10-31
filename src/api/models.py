"""
Model Alias API endpoints for managing LiteLLM model aliases
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from ..models.model_aliases import ModelAlias, ModelAliasAccessGroup, ModelAccessGroup
from ..models.job_tracking import get_db
from ..services.litellm_service import get_litellm_service, LiteLLMServiceError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


# Request/Response Models
class ModelCreateRequest(BaseModel):
    model_alias: str = Field(..., description="User-facing alias (e.g., 'chat-fast')")
    display_name: str = Field(..., description="Display name")
    provider: str = Field(..., description="Provider (openai, anthropic, etc.)")
    actual_model: str = Field(..., description="Real model name (gpt-3.5-turbo, etc.)")
    access_groups: List[str] = Field(default_factory=list, description="Model access groups")
    description: Optional[str] = None
    pricing_input: Optional[float] = Field(None, description="Cost per 1M input tokens")
    pricing_output: Optional[float] = Field(None, description="Cost per 1M output tokens")
    credential_name: Optional[str] = Field(None, description="LiteLLM credential name to use")
    api_key: Optional[str] = Field(None, description="API key (optional, uses env if not provided)")
    api_base: Optional[str] = Field(None, description="Custom API base URL")


class ModelUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    actual_model: Optional[str] = None
    provider: Optional[str] = None
    access_groups: Optional[List[str]] = None
    description: Optional[str] = None
    pricing_input: Optional[float] = None
    pricing_output: Optional[float] = None
    status: Optional[str] = None


class ModelResponse(BaseModel):
    model_alias: str
    display_name: str
    provider: str
    actual_model: str
    litellm_model_id: Optional[str]
    access_groups: List[str]
    description: Optional[str]
    pricing_input: Optional[float]
    pricing_output: Optional[float]
    status: str
    teams_using: Optional[List[str]] = None
    created_at: str
    updated_at: str


# Endpoints
@router.post("/create", response_model=ModelResponse)
async def create_model(
    request: ModelCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new model alias - no longer uses LiteLLM proxy, stores directly in our database
    """
    # Check if alias already exists
    existing = db.query(ModelAlias).filter(
        ModelAlias.model_alias == request.model_alias
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Model alias '{request.model_alias}' already exists"
        )

    # Validate access groups exist
    if request.access_groups:
        for group_name in request.access_groups:
            group = db.query(ModelAccessGroup).filter(
                ModelAccessGroup.group_name == group_name
            ).first()
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail=f"Model access group '{group_name}' not found"
                )

    # Create model alias in SaaS database (direct provider integration, no LiteLLM proxy)
    model_alias = ModelAlias(
        model_alias=request.model_alias,
        display_name=request.display_name,
        provider=request.provider,
        actual_model=request.actual_model,
        litellm_model_id=None,  # No longer needed with direct provider integration
        description=request.description,
        pricing_input=Decimal(str(request.pricing_input)) if request.pricing_input else None,
        pricing_output=Decimal(str(request.pricing_output)) if request.pricing_output else None,
        status="active"
    )

    db.add(model_alias)
    db.flush()

    # Assign to access groups
    if request.access_groups:
        for group_name in request.access_groups:
            group = db.query(ModelAccessGroup).filter(
                ModelAccessGroup.group_name == group_name
            ).first()

            if group:
                assignment = ModelAliasAccessGroup(
                    model_alias_id=model_alias.id,
                    access_group_id=group.id
                )
                db.add(assignment)

    db.commit()
    db.refresh(model_alias)

    logger.info(f"Created model alias '{request.model_alias}' for provider '{request.provider}' with model '{request.actual_model}'")

    return ModelResponse(
        model_alias=model_alias.model_alias,
        display_name=model_alias.display_name,
        provider=model_alias.provider,
        actual_model=model_alias.actual_model,
        litellm_model_id=model_alias.litellm_model_id,
        access_groups=request.access_groups,
        description=model_alias.description,
        pricing_input=float(model_alias.pricing_input) if model_alias.pricing_input else None,
        pricing_output=float(model_alias.pricing_output) if model_alias.pricing_output else None,
        status=model_alias.status,
        created_at=model_alias.created_at.isoformat(),
        updated_at=model_alias.updated_at.isoformat()
    )


@router.get("", response_model=List[ModelResponse])
async def list_models(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    access_group: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all model aliases with optional filters
    """
    query = db.query(ModelAlias)

    if status:
        query = query.filter(ModelAlias.status == status)

    if provider:
        query = query.filter(ModelAlias.provider == provider)

    if access_group:
        # Join with access groups to filter by group name
        query = query.join(
            ModelAliasAccessGroup,
            ModelAlias.id == ModelAliasAccessGroup.model_alias_id
        ).join(
            ModelAccessGroup,
            ModelAliasAccessGroup.access_group_id == ModelAccessGroup.id
        ).filter(
            ModelAccessGroup.group_name == access_group
        )

    models = query.all()

    result = []
    for model in models:
        # Get access groups for this model
        access_group_names = [
            assignment.access_group.group_name
            for assignment in model.access_group_assignments
            if assignment.access_group
        ]

        # Get teams using this model (via access groups)
        teams_using = db.query(func.distinct(func.unnest([])))  # Placeholder
        # TODO: Implement teams query

        result.append(ModelResponse(
            model_alias=model.model_alias,
            display_name=model.display_name,
            provider=model.provider,
            actual_model=model.actual_model,
            litellm_model_id=model.litellm_model_id,
            access_groups=access_group_names,
            description=model.description,
            pricing_input=float(model.pricing_input) if model.pricing_input else None,
            pricing_output=float(model.pricing_output) if model.pricing_output else None,
            status=model.status,
            teams_using=None,  # TODO
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat()
        ))

    return result


@router.get("/{alias}", response_model=ModelResponse)
async def get_model(
    alias: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific model alias by its alias name
    """
    model = db.query(ModelAlias).filter(
        ModelAlias.model_alias == alias
    ).first()

    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model alias '{alias}' not found"
        )

    # Get access groups
    access_group_names = [
        assignment.access_group.group_name
        for assignment in model.access_group_assignments
        if assignment.access_group
    ]

    return ModelResponse(
        model_alias=model.model_alias,
        display_name=model.display_name,
        provider=model.provider,
        actual_model=model.actual_model,
        litellm_model_id=model.litellm_model_id,
        access_groups=access_group_names,
        description=model.description,
        pricing_input=float(model.pricing_input) if model.pricing_input else None,
        pricing_output=float(model.pricing_output) if model.pricing_output else None,
        status=model.status,
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat()
    )


@router.put("/{alias}", response_model=ModelResponse)
async def update_model(
    alias: str,
    request: ModelUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a model alias
    """
    model = db.query(ModelAlias).filter(
        ModelAlias.model_alias == alias
    ).first()

    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model alias '{alias}' not found"
        )

    # Update fields
    if request.display_name is not None:
        model.display_name = request.display_name

    if request.actual_model is not None:
        model.actual_model = request.actual_model

    if request.provider is not None:
        model.provider = request.provider

    if request.description is not None:
        model.description = request.description

    if request.pricing_input is not None:
        model.pricing_input = Decimal(str(request.pricing_input))

    if request.pricing_output is not None:
        model.pricing_output = Decimal(str(request.pricing_output))

    if request.status is not None:
        model.status = request.status

    # Update access groups if provided
    if request.access_groups is not None:
        # Validate all groups exist
        for group_name in request.access_groups:
            group = db.query(ModelAccessGroup).filter(
                ModelAccessGroup.group_name == group_name
            ).first()
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail=f"Model access group '{group_name}' not found"
                )

        # Remove existing assignments
        db.query(ModelAliasAccessGroup).filter(
            ModelAliasAccessGroup.model_alias_id == model.id
        ).delete()

        # Create new assignments
        for group_name in request.access_groups:
            group = db.query(ModelAccessGroup).filter(
                ModelAccessGroup.group_name == group_name
            ).first()
            if group:
                assignment = ModelAliasAccessGroup(
                    model_alias_id=model.id,
                    access_group_id=group.id
                )
                db.add(assignment)

    db.commit()
    db.refresh(model)

    logger.info(f"Updated model alias '{alias}'")

    # Get updated access groups
    access_group_names = [
        assignment.access_group.group_name
        for assignment in model.access_group_assignments
        if assignment.access_group
    ]

    return ModelResponse(
        model_alias=model.model_alias,
        display_name=model.display_name,
        provider=model.provider,
        actual_model=model.actual_model,
        litellm_model_id=model.litellm_model_id,
        access_groups=access_group_names,
        description=model.description,
        pricing_input=float(model.pricing_input) if model.pricing_input else None,
        pricing_output=float(model.pricing_output) if model.pricing_output else None,
        status=model.status,
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat()
    )


@router.delete("/{alias}")
async def delete_model(
    alias: str,
    db: Session = Depends(get_db)
):
    """
    Delete a model alias
    """
    model = db.query(ModelAlias).filter(
        ModelAlias.model_alias == alias
    ).first()

    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model alias '{alias}' not found"
        )

    # Delete from SaaS database (cascades to assignments)
    db.delete(model)
    db.commit()

    logger.info(f"Deleted model alias '{alias}'")

    return {"message": f"Model alias '{alias}' deleted successfully"}
