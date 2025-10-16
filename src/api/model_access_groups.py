"""
Model Access Group API endpoints for managing collections of model aliases
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.model_aliases import ModelAccessGroup, ModelAliasAccessGroup, ModelAlias
from ..models.job_tracking import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/model-access-groups", tags=["model-access-groups"])


# Request/Response Models
class AccessGroupCreateRequest(BaseModel):
    group_name: str = Field(..., description="Unique group identifier (e.g., 'basic-chat')")
    display_name: str = Field(..., description="Display name")
    model_aliases: List[str] = Field(default_factory=list, description="Model aliases to include")
    description: Optional[str] = None


class AccessGroupUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class AccessGroupModelsRequest(BaseModel):
    model_aliases: List[str] = Field(..., description="Model aliases to assign to this group")


class AccessGroupResponse(BaseModel):
    group_name: str
    display_name: str
    description: Optional[str]
    status: str
    model_aliases: List[Dict[str, Any]]
    teams_using: Optional[List[str]] = None
    created_at: str
    updated_at: str


# Endpoints
@router.post("/create", response_model=AccessGroupResponse)
async def create_access_group(
    request: AccessGroupCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new model access group
    """
    # Check if group already exists
    existing = db.query(ModelAccessGroup).filter(
        ModelAccessGroup.group_name == request.group_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Model access group '{request.group_name}' already exists"
        )

    # Validate all model aliases exist
    if request.model_aliases:
        for alias in request.model_aliases:
            model = db.query(ModelAlias).filter(
                ModelAlias.model_alias == alias
            ).first()
            if not model:
                raise HTTPException(
                    status_code=404,
                    detail=f"Model alias '{alias}' not found"
                )

    # Create access group
    access_group = ModelAccessGroup(
        group_name=request.group_name,
        display_name=request.display_name,
        description=request.description,
        status="active"
    )

    db.add(access_group)
    db.flush()

    # Assign model aliases
    if request.model_aliases:
        for alias in request.model_aliases:
            model = db.query(ModelAlias).filter(
                ModelAlias.model_alias == alias
            ).first()

            if model:
                assignment = ModelAliasAccessGroup(
                    model_alias_id=model.id,
                    access_group_id=access_group.id
                )
                db.add(assignment)

    db.commit()
    db.refresh(access_group)

    # Build response with model aliases
    model_aliases = [
        {
            "model_alias": assignment.model_alias.model_alias,
            "display_name": assignment.model_alias.display_name,
            "provider": assignment.model_alias.provider,
            "actual_model": assignment.model_alias.actual_model
        }
        for assignment in access_group.model_alias_assignments
        if assignment.model_alias
    ]

    return AccessGroupResponse(
        group_name=access_group.group_name,
        display_name=access_group.display_name,
        description=access_group.description,
        status=access_group.status,
        model_aliases=model_aliases,
        created_at=access_group.created_at.isoformat(),
        updated_at=access_group.updated_at.isoformat()
    )


@router.get("", response_model=List[AccessGroupResponse])
async def list_access_groups(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all model access groups with optional filters
    """
    query = db.query(ModelAccessGroup)

    if status:
        query = query.filter(ModelAccessGroup.status == status)

    groups = query.all()

    result = []
    for group in groups:
        # Get model aliases for this group
        model_aliases = [
            {
                "model_alias": assignment.model_alias.model_alias,
                "display_name": assignment.model_alias.display_name,
                "provider": assignment.model_alias.provider,
                "actual_model": assignment.model_alias.actual_model
            }
            for assignment in group.model_alias_assignments
            if assignment.model_alias
        ]

        # Get teams using this group
        teams_using = [
            assignment.team_id
            for assignment in group.team_assignments
        ]

        result.append(AccessGroupResponse(
            group_name=group.group_name,
            display_name=group.display_name,
            description=group.description,
            status=group.status,
            model_aliases=model_aliases,
            teams_using=teams_using if teams_using else None,
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat()
        ))

    return result


@router.get("/{group_name}", response_model=AccessGroupResponse)
async def get_access_group(
    group_name: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific model access group by name
    """
    group = db.query(ModelAccessGroup).filter(
        ModelAccessGroup.group_name == group_name
    ).first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Model access group '{group_name}' not found"
        )

    # Get model aliases
    model_aliases = [
        {
            "model_alias": assignment.model_alias.model_alias,
            "display_name": assignment.model_alias.display_name,
            "provider": assignment.model_alias.provider,
            "actual_model": assignment.model_alias.actual_model
        }
        for assignment in group.model_alias_assignments
        if assignment.model_alias
    ]

    # Get teams using this group
    teams_using = [
        assignment.team_id
        for assignment in group.team_assignments
    ]

    return AccessGroupResponse(
        group_name=group.group_name,
        display_name=group.display_name,
        description=group.description,
        status=group.status,
        model_aliases=model_aliases,
        teams_using=teams_using if teams_using else None,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat()
    )


@router.put("/{group_name}", response_model=AccessGroupResponse)
async def update_access_group(
    group_name: str,
    request: AccessGroupUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a model access group's metadata
    """
    group = db.query(ModelAccessGroup).filter(
        ModelAccessGroup.group_name == group_name
    ).first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Model access group '{group_name}' not found"
        )

    # Update fields
    if request.display_name is not None:
        group.display_name = request.display_name

    if request.description is not None:
        group.description = request.description

    if request.status is not None:
        group.status = request.status

    db.commit()
    db.refresh(group)

    # Build response
    model_aliases = [
        {
            "model_alias": assignment.model_alias.model_alias,
            "display_name": assignment.model_alias.display_name,
            "provider": assignment.model_alias.provider,
            "actual_model": assignment.model_alias.actual_model
        }
        for assignment in group.model_alias_assignments
        if assignment.model_alias
    ]

    teams_using = [
        assignment.team_id
        for assignment in group.team_assignments
    ]

    return AccessGroupResponse(
        group_name=group.group_name,
        display_name=group.display_name,
        description=group.description,
        status=group.status,
        model_aliases=model_aliases,
        teams_using=teams_using if teams_using else None,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat()
    )


@router.put("/{group_name}/models", response_model=AccessGroupResponse)
async def update_access_group_models(
    group_name: str,
    request: AccessGroupModelsRequest,
    db: Session = Depends(get_db)
):
    """
    Update the model aliases assigned to an access group
    """
    group = db.query(ModelAccessGroup).filter(
        ModelAccessGroup.group_name == group_name
    ).first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Model access group '{group_name}' not found"
        )

    # Validate all model aliases exist
    for alias in request.model_aliases:
        model = db.query(ModelAlias).filter(
            ModelAlias.model_alias == alias
        ).first()
        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Model alias '{alias}' not found"
            )

    # Remove existing assignments
    db.query(ModelAliasAccessGroup).filter(
        ModelAliasAccessGroup.access_group_id == group.id
    ).delete()

    # Create new assignments
    for alias in request.model_aliases:
        model = db.query(ModelAlias).filter(
            ModelAlias.model_alias == alias
        ).first()

        if model:
            assignment = ModelAliasAccessGroup(
                model_alias_id=model.id,
                access_group_id=group.id
            )
            db.add(assignment)

    db.commit()
    db.refresh(group)

    # Build response
    model_aliases = [
        {
            "model_alias": assignment.model_alias.model_alias,
            "display_name": assignment.model_alias.display_name,
            "provider": assignment.model_alias.provider,
            "actual_model": assignment.model_alias.actual_model
        }
        for assignment in group.model_alias_assignments
        if assignment.model_alias
    ]

    teams_using = [
        assignment.team_id
        for assignment in group.team_assignments
    ]

    return AccessGroupResponse(
        group_name=group.group_name,
        display_name=group.display_name,
        description=group.description,
        status=group.status,
        model_aliases=model_aliases,
        teams_using=teams_using if teams_using else None,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat()
    )


@router.delete("/{group_name}")
async def delete_access_group(
    group_name: str,
    db: Session = Depends(get_db)
):
    """
    Delete a model access group
    """
    group = db.query(ModelAccessGroup).filter(
        ModelAccessGroup.group_name == group_name
    ).first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Model access group '{group_name}' not found"
        )

    # Check if any teams are using this group
    if group.team_assignments:
        team_ids = [assignment.team_id for assignment in group.team_assignments]
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete access group '{group_name}' - still in use by teams: {', '.join(team_ids)}"
        )

    # Delete from database (cascades to assignments)
    db.delete(group)
    db.commit()

    return {"message": f"Model access group '{group_name}' deleted successfully"}
