"""
Teams API endpoints with LiteLLM Integration
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.model_aliases import ModelAccessGroup, TeamAccessGroup, ModelAlias
from ..models.credits import TeamCredits
from ..services.credit_manager import get_credit_manager
from ..services.litellm_service import get_litellm_service, LiteLLMServiceError
from ..models.job_tracking import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teams", tags=["teams"])


# Request/Response Models
class TeamCreateRequest(BaseModel):
    organization_id: str
    team_id: str
    team_alias: Optional[str] = None
    access_groups: List[str]  # List of model access group names
    credits_allocated: int = 0
    metadata: Optional[Dict[str, Any]] = {}


class TeamUpdateRequest(BaseModel):
    team_alias: Optional[str] = None
    access_groups: Optional[List[str]] = None
    credits_allocated: Optional[int] = None
    credits_used: Optional[int] = None
    budget_mode: Optional[str] = None  # 'job_based', 'consumption_usd', 'consumption_tokens'
    credits_per_dollar: Optional[float] = None


class TeamResponse(BaseModel):
    team_id: str
    organization_id: str
    access_groups: List[str]
    allowed_model_aliases: List[str]  # Model aliases this team can use
    credits_allocated: int
    credits_remaining: int
    virtual_key: Optional[str] = None
    message: str


# Endpoints
@router.get("")
async def list_teams(
    db: Session = Depends(get_db)
):
    """
    List all teams
    """
    teams = db.query(TeamCredits).all()

    result = []
    for team_credits in teams:
        # Get assigned access groups
        assignments = db.query(TeamAccessGroup).filter(
            TeamAccessGroup.team_id == team_credits.team_id
        ).all()

        access_groups = []
        for assignment in assignments:
            group = db.query(ModelAccessGroup).filter(
                ModelAccessGroup.id == assignment.access_group_id
            ).first()
            if group:
                access_groups.append(group.group_name)

        result.append({
            "team_id": team_credits.team_id,
            "organization_id": team_credits.organization_id,
            "credits_allocated": team_credits.credits_allocated,
            "credits_remaining": team_credits.credits_remaining,
            "credits_used": team_credits.credits_used,
            "access_groups": access_groups,
            "virtual_key": team_credits.virtual_key if team_credits.virtual_key else None,
            "budget_mode": team_credits.budget_mode or "job_based",
            "credits_per_dollar": float(team_credits.credits_per_dollar) if team_credits.credits_per_dollar else 10.0,
            "status": team_credits.status or "active",
            "created_at": team_credits.created_at.isoformat() if team_credits.created_at else None
        })

    return result


@router.post("/create", response_model=TeamResponse)
async def create_team(
    request: TeamCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new team with model access groups, credits, and LiteLLM integration
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

    # Verify all access groups exist and collect all unique model aliases
    access_group_ids = []
    all_model_aliases = set()  # Collect all unique model aliases for LiteLLM team

    for group_name in request.access_groups:
        group = db.query(ModelAccessGroup).filter(
            ModelAccessGroup.group_name == group_name
        ).first()

        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Model access group '{group_name}' not found"
            )

        access_group_ids.append((group_name, group.id))

        # Get all model aliases in this access group
        from ..models.model_aliases import ModelAliasAccessGroup
        group_models = db.query(ModelAliasAccessGroup).filter(
            ModelAliasAccessGroup.access_group_id == group.id
        ).all()

        for assignment in group_models:
            model = db.query(ModelAlias).filter(
                ModelAlias.id == assignment.model_alias_id
            ).first()
            if model:
                all_model_aliases.add(model.model_alias)

    # Create team in LiteLLM
    litellm_service = get_litellm_service()
    virtual_key = None

    try:
        # Create team in LiteLLM with budget based on credits
        # Assuming $0.10 per credit for budget calculation (adjustable)
        max_budget = request.credits_allocated * 0.10 if request.credits_allocated > 0 else None

        # Create team in LiteLLM with model aliases
        await litellm_service.create_team(
            team_id=request.team_id,
            team_alias=request.team_alias or request.team_id,
            organization_id=None,  # Don't use LiteLLM's organization feature
            max_budget=max_budget,
            models=list(all_model_aliases),  # Set team's allowed model aliases
            metadata={
                **request.metadata,
                "saas_organization_id": request.organization_id,  # Track our org ID
                "access_groups": request.access_groups  # Track access groups
            }
        )

        logger.info(f"Created team {request.team_id} in LiteLLM with model aliases: {all_model_aliases}")

        # Generate virtual key for team with allowed model aliases
        key_response = await litellm_service.generate_key(
            team_id=request.team_id,
            key_alias=f"{request.team_id}_key",
            max_budget=max_budget,
            models=list(all_model_aliases),  # Allow all model aliases from access groups
            metadata={
                "created_by": "saas_api",
                "access_groups": request.access_groups  # Track which groups this key represents
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

    # Assign access groups to team
    for group_name, group_id in access_group_ids:
        assignment = TeamAccessGroup(
            team_id=request.team_id,
            access_group_id=group_id
        )
        db.add(assignment)

    db.commit()
    db.refresh(credits)

    return TeamResponse(
        team_id=request.team_id,
        organization_id=request.organization_id,
        access_groups=request.access_groups,
        allowed_model_aliases=sorted(list(all_model_aliases)),
        credits_allocated=credits.credits_allocated,
        credits_remaining=credits.credits_remaining,
        virtual_key=virtual_key,
        message=f"Team created successfully with LiteLLM integration"
    )


@router.get("/{team_id}")
async def get_team(
    team_id: str,
    db: Session = Depends(get_db)
):
    """
    Get team details
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

    # Get assigned access groups
    assignments = db.query(TeamAccessGroup).filter(
        TeamAccessGroup.team_id == team_id
    ).all()

    access_groups = []
    model_aliases = set()

    for assignment in assignments:
        group = db.query(ModelAccessGroup).filter(
            ModelAccessGroup.id == assignment.access_group_id
        ).first()
        if group:
            access_groups.append(group.group_name)

            # Get model aliases in this group
            from ..models.model_aliases import ModelAliasAccessGroup
            group_models = db.query(ModelAliasAccessGroup).filter(
                ModelAliasAccessGroup.access_group_id == group.id
            ).all()

            for model_assignment in group_models:
                model = db.query(ModelAlias).filter(
                    ModelAlias.id == model_assignment.model_alias_id
                ).first()
                if model:
                    model_aliases.add(model.model_alias)

    return {
        "team_id": team_id,
        "organization_id": credits.organization_id,
        "credits": credits.to_dict(),
        "access_groups": access_groups,
        "allowed_model_aliases": sorted(list(model_aliases)),
        "virtual_key": credits.virtual_key,
        "credits_allocated": credits.credits_allocated,
        "credits_remaining": credits.credits_remaining
    }


@router.put("/{team_id}/access-groups")
async def assign_access_groups(
    team_id: str,
    access_groups: List[str],
    db: Session = Depends(get_db)
):
    """
    Assign model access groups to a team (replaces existing assignments)
    Also updates the team's allowed models in LiteLLM
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

    # Verify all access groups exist and collect model aliases
    access_group_ids = []
    all_model_aliases = set()

    for group_name in access_groups:
        group = db.query(ModelAccessGroup).filter(
            ModelAccessGroup.group_name == group_name
        ).first()

        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Model access group '{group_name}' not found"
            )

        access_group_ids.append(group.id)

        # Get model aliases in this group
        from ..models.model_aliases import ModelAliasAccessGroup
        group_models = db.query(ModelAliasAccessGroup).filter(
            ModelAliasAccessGroup.access_group_id == group.id
        ).all()

        for assignment in group_models:
            model = db.query(ModelAlias).filter(
                ModelAlias.id == assignment.model_alias_id
            ).first()
            if model:
                all_model_aliases.add(model.model_alias)

    # Update team's allowed models in LiteLLM
    litellm_service = get_litellm_service()
    try:
        await litellm_service.update_team_models(
            team_id=team_id,
            model_aliases=list(all_model_aliases)
        )
        logger.info(f"Updated team {team_id} models in LiteLLM: {all_model_aliases}")
    except LiteLLMServiceError as e:
        logger.warning(f"Failed to update team models in LiteLLM: {str(e)}")
        # Continue anyway - SaaS DB will be updated

    # Delete existing assignments
    db.query(TeamAccessGroup).filter(
        TeamAccessGroup.team_id == team_id
    ).delete()

    # Create new assignments
    for group_id in access_group_ids:
        assignment = TeamAccessGroup(
            team_id=team_id,
            access_group_id=group_id
        )
        db.add(assignment)

    db.commit()

    return {
        "team_id": team_id,
        "access_groups": access_groups,
        "allowed_model_aliases": sorted(list(all_model_aliases)),
        "message": "Model access groups assigned successfully"
    }


@router.put("/{team_id}")
async def update_team(
    team_id: str,
    request: TeamUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update team details including credits, budget mode, and access groups
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

    # Update credits and budget mode if provided
    if request.credits_allocated is not None:
        credits.credits_allocated = request.credits_allocated

    if request.credits_used is not None:
        credits.credits_used = request.credits_used

    if request.budget_mode is not None:
        if request.budget_mode not in ['job_based', 'consumption_usd', 'consumption_tokens']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid budget_mode: {request.budget_mode}. Must be one of: job_based, consumption_usd, consumption_tokens"
            )
        credits.budget_mode = request.budget_mode

    if request.credits_per_dollar is not None:
        credits.credits_per_dollar = request.credits_per_dollar

    # Update access groups if provided
    if request.access_groups is not None:
        # Verify all access groups exist and collect model aliases
        access_group_ids = []
        all_model_aliases = set()

        for group_name in request.access_groups:
            group = db.query(ModelAccessGroup).filter(
                ModelAccessGroup.group_name == group_name
            ).first()

            if not group:
                raise HTTPException(
                    status_code=404,
                    detail=f"Model access group '{group_name}' not found"
                )

            access_group_ids.append(group.id)

            # Get model aliases in this group
            from ..models.model_aliases import ModelAliasAccessGroup
            group_models = db.query(ModelAliasAccessGroup).filter(
                ModelAliasAccessGroup.access_group_id == group.id
            ).all()

            for assignment in group_models:
                model = db.query(ModelAlias).filter(
                    ModelAlias.id == assignment.model_alias_id
                ).first()
                if model:
                    all_model_aliases.add(model.model_alias)

        # Update team's allowed models in LiteLLM
        litellm_service = get_litellm_service()
        try:
            await litellm_service.update_team_models(
                team_id=team_id,
                model_aliases=list(all_model_aliases)
            )
            logger.info(f"Updated team {team_id} models in LiteLLM: {all_model_aliases}")
        except LiteLLMServiceError as e:
            logger.warning(f"Failed to update team models in LiteLLM: {str(e)}")
            # Continue anyway - SaaS DB will be updated

        # Delete existing assignments
        db.query(TeamAccessGroup).filter(
            TeamAccessGroup.team_id == team_id
        ).delete()

        # Create new assignments
        for group_id in access_group_ids:
            assignment = TeamAccessGroup(
                team_id=team_id,
                access_group_id=group_id
            )
            db.add(assignment)

    db.commit()
    db.refresh(credits)

    return {
        "team_id": team_id,
        "credits_allocated": credits.credits_allocated,
        "credits_used": credits.credits_used,
        "credits_remaining": credits.credits_remaining,
        "budget_mode": credits.budget_mode,
        "credits_per_dollar": float(credits.credits_per_dollar) if credits.credits_per_dollar else 10.0,
        "message": "Team updated successfully"
    }


@router.delete("/{team_id}")
async def delete_team(
    team_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a team (cannot delete default teams ending with '_default')
    """
    # Check if it's a default team
    if team_id.endswith('_default'):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete default team '{team_id}'. Default teams are protected from deletion."
        )

    # Verify team exists
    credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == team_id
    ).first()

    if not credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )

    # Delete team's access group assignments
    db.query(TeamAccessGroup).filter(
        TeamAccessGroup.team_id == team_id
    ).delete()

    # Delete team credits
    db.delete(credits)

    # Note: We don't delete from LiteLLM as it may have historical data
    # LiteLLM teams can be manually archived if needed

    db.commit()

    return {
        "team_id": team_id,
        "message": f"Team '{team_id}' deleted successfully"
    }


@router.put("/{team_id}/suspend")
async def suspend_team(
    team_id: str,
    db: Session = Depends(get_db)
):
    """
    Suspend a team - prevents them from making any API calls
    """
    credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == team_id
    ).first()

    if not credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )

    credits.status = "suspended"
    db.commit()

    return {
        "team_id": team_id,
        "status": "suspended",
        "message": f"Team '{team_id}' has been suspended"
    }


@router.put("/{team_id}/resume")
async def resume_team(
    team_id: str,
    db: Session = Depends(get_db)
):
    """
    Resume a suspended or paused team - allows them to make API calls again
    """
    credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == team_id
    ).first()

    if not credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )

    credits.status = "active"
    db.commit()

    return {
        "team_id": team_id,
        "status": "active",
        "message": f"Team '{team_id}' has been resumed"
    }
