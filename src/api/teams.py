"""
Teams API endpoints with LiteLLM Integration
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.model_groups import ModelGroup, TeamModelGroup
from ..models.credits import TeamCredits
from ..services.credit_manager import get_credit_manager
from ..services.litellm_service import get_litellm_service, LiteLLMServiceError
from ..models.job_tracking import get_db
from ..auth.dependencies import verify_admin_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teams", tags=["teams"])


# Request/Response Models
class TeamCreateRequest(BaseModel):
    organization_id: str
    team_id: str
    team_alias: Optional[str] = None
    model_groups: List[str]  # List of model group names
    credits_allocated: int = 0
    metadata: Optional[Dict[str, Any]] = {}


class TeamResponse(BaseModel):
    team_id: str
    organization_id: str
    model_groups: List[str]
    allowed_models: List[str]  # Actual model names for direct OpenAI-compatible calls
    credits_allocated: int
    credits_remaining: int
    virtual_key: Optional[str] = None
    message: str


# Endpoints
@router.post("/create", response_model=TeamResponse)
async def create_team(
    request: TeamCreateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key)
):
    """
    Create a new team with model groups, credits, and LiteLLM integration.

    Requires: X-Admin-Key header with MASTER_KEY
    """
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

    # Check if team already exists
    existing_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == request.team_id
    ).first()

    if existing_credits:
        raise HTTPException(
            status_code=400,
            detail=f"Team '{request.team_id}' already exists"
        )

    # Verify all model groups exist and collect all unique model names
    model_group_ids = []
    all_model_names = set()  # Collect all unique model names for virtual key

    for group_name in request.model_groups:
        group = db.query(ModelGroup).filter(
            ModelGroup.group_name == group_name
        ).first()

        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Model group '{group_name}' not found"
            )

        model_group_ids.append((group_name, group.model_group_id))

        # Get all models in this group for virtual key configuration
        from ..models.model_groups import ModelGroupModel
        group_models = db.query(ModelGroupModel).filter(
            ModelGroupModel.model_group_id == group.model_group_id
        ).all()

        for model in group_models:
            all_model_names.add(model.model_name)

    # Create team in LiteLLM
    litellm_service = get_litellm_service()
    virtual_key = None

    try:
        # Create team in LiteLLM with budget based on credits
        # Assuming $0.10 per credit for budget calculation (adjustable)
        max_budget = request.credits_allocated * 0.10 if request.credits_allocated > 0 else None

        # Note: Not passing organization_id to LiteLLM since it requires org to exist in LiteLLM's DB
        # We track organization in our SaaS API database instead
        await litellm_service.create_team(
            team_id=request.team_id,
            team_alias=request.team_alias or request.team_id,
            organization_id=None,  # Don't use LiteLLM's organization feature
            max_budget=max_budget,
            metadata={
                **request.metadata,
                "saas_organization_id": request.organization_id  # Track our org ID in metadata
            }
        )

        logger.info(f"Created team {request.team_id} in LiteLLM")

        # Generate virtual key for team with allowed models
        # Convert model group names to actual model names for LiteLLM
        key_response = await litellm_service.generate_key(
            team_id=request.team_id,
            key_alias=f"{request.team_id}_key",
            max_budget=max_budget,
            models=list(all_model_names),  # Allow all models from assigned model groups
            metadata={
                "created_by": "saas_api",
                "model_groups": request.model_groups  # Track which groups this key represents
            }
        )

        virtual_key = key_response.get("key")
        logger.info(f"Generated virtual key for team {request.team_id}")

    except LiteLLMServiceError as e:
        logger.error(f"LiteLLM integration failed for team {request.team_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create team in LiteLLM: {str(e)}"
        )

    # Create team credits with virtual key
    credits = TeamCredits(
        team_id=request.team_id,
        organization_id=request.organization_id,
        credits_allocated=request.credits_allocated,
        credits_used=0,
        virtual_key=virtual_key
    )
    db.add(credits)
    db.flush()

    # Assign model groups to team
    for group_name, group_id in model_group_ids:
        assignment = TeamModelGroup(
            team_id=request.team_id,
            model_group_id=group_id
        )
        db.add(assignment)

    db.commit()
    db.refresh(credits)

    return TeamResponse(
        team_id=request.team_id,
        organization_id=request.organization_id,
        model_groups=request.model_groups,
        allowed_models=sorted(list(all_model_names)),
        credits_allocated=credits.credits_allocated,
        credits_remaining=credits.credits_remaining,
        virtual_key=virtual_key,
        message=f"Team created successfully with LiteLLM integration"
    )


@router.get("/{team_id}")
async def get_team(
    team_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key)
):
    """
    Get team details.

    Requires: X-Admin-Key header with MASTER_KEY
    """
    # Get credits
    credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == team_id
    ).first()

    if not credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )

    # Get assigned model groups
    assignments = db.query(TeamModelGroup).filter(
        TeamModelGroup.team_id == team_id
    ).all()

    model_groups = []
    for assignment in assignments:
        group = db.query(ModelGroup).filter(
            ModelGroup.model_group_id == assignment.model_group_id
        ).first()
        if group:
            model_groups.append(group.group_name)

    return {
        "team_id": team_id,
        "organization_id": credits.organization_id,
        "credits": credits.to_dict(),
        "model_groups": model_groups
    }


@router.put("/{team_id}/model-groups")
async def assign_model_groups(
    team_id: str,
    model_groups: List[str],
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key)
):
    """
    Assign model groups to a team (replaces existing assignments).

    Requires: X-Admin-Key header with MASTER_KEY
    """
    # Verify team exists
    credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == team_id
    ).first()

    if not credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )

    # Verify all model groups exist
    model_group_ids = []
    for group_name in model_groups:
        group = db.query(ModelGroup).filter(
            ModelGroup.group_name == group_name
        ).first()

        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Model group '{group_name}' not found"
            )

        model_group_ids.append(group.model_group_id)

    # Delete existing assignments
    db.query(TeamModelGroup).filter(
        TeamModelGroup.team_id == team_id
    ).delete()

    # Create new assignments
    for group_id in model_group_ids:
        assignment = TeamModelGroup(
            team_id=team_id,
            model_group_id=group_id
        )
        db.add(assignment)

    db.commit()

    return {
        "team_id": team_id,
        "model_groups": model_groups,
        "message": "Model groups assigned successfully"
    }
