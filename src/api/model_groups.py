"""
Model Groups API endpoints (Minimal Version)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
from ..models.model_groups import ModelGroup, ModelGroupModel, TeamModelGroup
from ..models.job_tracking import get_db

router = APIRouter(prefix="/api/model-groups", tags=["model-groups"])


# Request/Response Models
class ModelConfig(BaseModel):
    model_name: str
    priority: int = 0


class ModelGroupCreateRequest(BaseModel):
    group_name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    models: List[ModelConfig]


class ModelGroupResponse(BaseModel):
    model_group_id: str
    group_name: str
    display_name: Optional[str]
    description: Optional[str]
    status: str
    models: List[dict]


# Endpoints
@router.post("/create", response_model=ModelGroupResponse)
async def create_model_group(
    request: ModelGroupCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new model group (e.g., ResumeAgent, ParsingAgent)
    """
    # Check if group name already exists
    existing = db.query(ModelGroup).filter(
        ModelGroup.group_name == request.group_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Model group '{request.group_name}' already exists"
        )

    # Create model group
    model_group = ModelGroup(
        group_name=request.group_name,
        display_name=request.display_name or request.group_name,
        description=request.description
    )

    db.add(model_group)
    db.flush()  # Get the ID before adding models

    # Add models
    for model_config in request.models:
        model = ModelGroupModel(
            model_group_id=model_group.model_group_id,
            model_name=model_config.model_name,
            priority=model_config.priority
        )
        db.add(model)

    db.commit()
    db.refresh(model_group)

    return ModelGroupResponse(
        model_group_id=str(model_group.model_group_id),
        group_name=model_group.group_name,
        display_name=model_group.display_name,
        description=model_group.description,
        status=model_group.status,
        models=[m.to_dict() for m in sorted(model_group.models, key=lambda x: x.priority)]
    )


@router.get("", response_model=List[ModelGroupResponse])
async def list_model_groups(
    db: Session = Depends(get_db)
):
    """
    List all model groups
    """
    groups = db.query(ModelGroup).filter(
        ModelGroup.status == "active"
    ).all()

    return [
        ModelGroupResponse(
            model_group_id=str(g.model_group_id),
            group_name=g.group_name,
            display_name=g.display_name,
            description=g.description,
            status=g.status,
            models=[m.to_dict() for m in sorted(g.models, key=lambda x: x.priority)]
        )
        for g in groups
    ]


@router.get("/{group_name}", response_model=ModelGroupResponse)
async def get_model_group(
    group_name: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific model group by name
    """
    group = db.query(ModelGroup).filter(
        ModelGroup.group_name == group_name
    ).first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Model group '{group_name}' not found"
        )

    return ModelGroupResponse(
        model_group_id=str(group.model_group_id),
        group_name=group.group_name,
        display_name=group.display_name,
        description=group.description,
        status=group.status,
        models=[m.to_dict() for m in sorted(group.models, key=lambda x: x.priority)]
    )


@router.put("/{group_name}/models")
async def update_model_group_models(
    group_name: str,
    models: List[ModelConfig],
    db: Session = Depends(get_db)
):
    """
    Update models in a model group (replaces all existing models)
    """
    group = db.query(ModelGroup).filter(
        ModelGroup.group_name == group_name
    ).first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Model group '{group_name}' not found"
        )

    # Delete existing models
    db.query(ModelGroupModel).filter(
        ModelGroupModel.model_group_id == group.model_group_id
    ).delete()

    # Add new models
    for model_config in models:
        model = ModelGroupModel(
            model_group_id=group.model_group_id,
            model_name=model_config.model_name,
            priority=model_config.priority
        )
        db.add(model)

    db.commit()
    db.refresh(group)

    return {
        "group_name": group.group_name,
        "models": [m.to_dict() for m in sorted(group.models, key=lambda x: x.priority)]
    }


@router.delete("/{group_name}")
async def delete_model_group(
    group_name: str,
    db: Session = Depends(get_db)
):
    """
    Delete a model group
    """
    group = db.query(ModelGroup).filter(
        ModelGroup.group_name == group_name
    ).first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Model group '{group_name}' not found"
        )

    # Check if any teams are using this group
    assignments = db.query(TeamModelGroup).filter(
        TeamModelGroup.model_group_id == group.model_group_id
    ).count()

    if assignments > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete model group '{group_name}'. It is assigned to {assignments} team(s)."
        )

    db.delete(group)
    db.commit()

    return {"message": f"Model group '{group_name}' deleted successfully"}
