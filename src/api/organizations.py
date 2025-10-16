"""
Organizations API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from ..models.organizations import Organization
from ..models.job_tracking import Job, get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


# Request/Response Models
class OrganizationCreateRequest(BaseModel):
    organization_id: str
    name: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # Default team configuration
    create_default_team: bool = True
    default_team_name: Optional[str] = None
    default_team_access_groups: List[str] = Field(default_factory=list)
    default_team_credits: int = 0


class OrganizationResponse(BaseModel):
    organization_id: str
    name: str
    status: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    default_team: Optional[Dict[str, Any]] = None


# Endpoints
@router.get("", response_model=list)
async def list_organizations(
    db: Session = Depends(get_db)
):
    """
    List all organizations
    """
    orgs = db.query(Organization).filter(
        Organization.status == "active"
    ).all()

    return [OrganizationResponse(**org.to_dict()) for org in orgs]


@router.post("/create")
async def create_organization(
    request: OrganizationCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new organization and optionally create a default team

    Parameters:
    - create_default_team: If True, automatically creates a default team (default: True)
    - default_team_name: Name for the default team (defaults to organization name)
    - default_team_access_groups: Model access groups to assign to default team (optional)
    - default_team_credits: Credits to allocate to default team (default: 0)
    """
    # Check if organization already exists
    existing = db.query(Organization).filter(
        Organization.organization_id == request.organization_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Organization with ID '{request.organization_id}' already exists"
        )

    # Create organization
    org = Organization(
        organization_id=request.organization_id,
        name=request.name,
        org_metadata=request.metadata
    )

    db.add(org)
    db.commit()
    db.refresh(org)

    # Create default team if requested
    default_team_info = None
    if request.create_default_team:
        try:
            from ..models.model_aliases import ModelAccessGroup, TeamAccessGroup, ModelAlias, ModelAliasAccessGroup
            from ..models.credits import TeamCredits
            from ..services.litellm_service import get_litellm_service, LiteLLMServiceError

            # Generate team ID and name
            default_team_id = f"{request.organization_id}_default"
            default_team_alias = request.default_team_name or request.name

            logger.info(f"Creating default team '{default_team_id}' for organization '{request.organization_id}'")

            # Verify access groups exist and collect model aliases
            all_model_aliases = set()
            access_group_ids = []

            for group_name in request.default_team_access_groups:
                group = db.query(ModelAccessGroup).filter(
                    ModelAccessGroup.group_name == group_name
                ).first()

                if not group:
                    logger.warning(f"Model access group '{group_name}' not found, skipping")
                    continue

                access_group_ids.append((group_name, group.id))

                # Get all model aliases in this access group
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

            max_budget = request.default_team_credits * 0.10 if request.default_team_credits > 0 else None

            await litellm_service.create_team(
                team_id=default_team_id,
                team_alias=default_team_alias,
                organization_id=None,
                max_budget=max_budget,
                models=list(all_model_aliases),  # Set team's allowed model aliases
                metadata={
                    "saas_organization_id": request.organization_id,
                    "is_default_team": True,
                    "access_groups": request.default_team_access_groups
                }
            )

            logger.info(f"Created team {default_team_id} in LiteLLM with model aliases: {all_model_aliases}")

            # Generate virtual key
            if all_model_aliases:  # Only create key if there are model aliases
                key_response = await litellm_service.generate_key(
                    team_id=default_team_id,
                    key_alias=f"{default_team_id}_key",
                    max_budget=max_budget,
                    models=list(all_model_aliases),
                    metadata={
                        "created_by": "saas_api",
                        "access_groups": request.default_team_access_groups,
                        "is_default_team": True
                    }
                )
                virtual_key = key_response.get("key")
                logger.info(f"Generated virtual key for team {default_team_id}")
            else:
                logger.info(f"No model aliases configured, skipping virtual key generation for {default_team_id}")

            # Create team credits
            credits = TeamCredits(
                team_id=default_team_id,
                organization_id=request.organization_id,
                credits_allocated=request.default_team_credits,
                credits_used=0,
                virtual_key=virtual_key
            )
            db.add(credits)
            db.flush()

            # Assign access groups to team
            for group_name, group_id in access_group_ids:
                assignment = TeamAccessGroup(
                    team_id=default_team_id,
                    access_group_id=group_id
                )
                db.add(assignment)

            db.commit()

            default_team_info = {
                "team_id": default_team_id,
                "team_alias": default_team_alias,
                "virtual_key": virtual_key,
                "access_groups": request.default_team_access_groups,
                "allowed_model_aliases": sorted(list(all_model_aliases)),
                "credits_allocated": request.default_team_credits
            }

            logger.info(f"Successfully created default team for organization '{request.organization_id}'")

        except LiteLLMServiceError as e:
            logger.error(f"Failed to create default team in LiteLLM: {str(e)}")
            # Don't fail the organization creation, just log the error
            default_team_info = {
                "error": f"Failed to create default team: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating default team: {str(e)}")
            default_team_info = {
                "error": f"Unexpected error: {str(e)}"
            }

    response = org.to_dict()
    response["default_team"] = default_team_info

    return response


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    db: Session = Depends(get_db)
):
    """
    Get organization details
    """
    org = db.query(Organization).filter(
        Organization.organization_id == organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Organization '{organization_id}' not found"
        )

    return OrganizationResponse(**org.to_dict())


@router.get("/{organization_id}/teams")
async def list_organization_teams(
    organization_id: str,
    db: Session = Depends(get_db)
):
    """
    List all teams in an organization
    """
    # Verify organization exists
    org = db.query(Organization).filter(
        Organization.organization_id == organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Organization '{organization_id}' not found"
        )

    # Get all teams for this organization from TeamCredits
    from ..models.credits import TeamCredits
    teams = db.query(TeamCredits).filter(
        TeamCredits.organization_id == organization_id
    ).all()

    team_list = []
    for team in teams:
        # Get access groups for this team
        from ..models.model_aliases import TeamAccessGroup, ModelAccessGroup
        assignments = db.query(TeamAccessGroup).filter(
            TeamAccessGroup.team_id == team.team_id
        ).all()

        access_groups = []
        for assignment in assignments:
            group = db.query(ModelAccessGroup).filter(
                ModelAccessGroup.id == assignment.access_group_id
            ).first()
            if group:
                access_groups.append(group.group_name)

        team_list.append({
            "team_id": team.team_id,
            "access_groups": access_groups,
            "credits_allocated": team.credits_allocated,
            "credits_remaining": team.credits_remaining
        })

    return {
        "organization_id": organization_id,
        "team_count": len(team_list),
        "teams": team_list
    }


@router.get("/{organization_id}/usage")
async def get_organization_usage(
    organization_id: str,
    period: str,  # e.g., "2025-10"
    db: Session = Depends(get_db)
):
    """
    Get organization-wide usage for a period
    """
    # Verify organization exists
    org = db.query(Organization).filter(
        Organization.organization_id == organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Organization '{organization_id}' not found"
        )

    # Get all jobs for this org in the period
    from sqlalchemy import func
    from ..models.job_tracking import JobStatus, JobCostSummary

    jobs = db.query(Job).filter(
        Job.organization_id == organization_id,
        func.to_char(Job.created_at, 'YYYY-MM').like(f"{period}%")
    ).all()

    total_jobs = len(jobs)
    completed_jobs = len([j for j in jobs if j.status == JobStatus.COMPLETED])
    failed_jobs = len([j for j in jobs if j.status == JobStatus.FAILED])
    credits_used = len([j for j in jobs if j.credit_applied])

    # Get cost data
    job_ids = [j.job_id for j in jobs]
    costs = db.query(JobCostSummary).filter(
        JobCostSummary.job_id.in_(job_ids)
    ).all() if job_ids else []

    total_cost = sum(float(c.total_cost_usd) for c in costs)
    total_tokens = sum(c.total_tokens for c in costs)

    # Team breakdown
    team_breakdown = {}
    for job in jobs:
        if job.team_id not in team_breakdown:
            team_breakdown[job.team_id] = {
                "jobs": 0,
                "credits_used": 0
            }
        team_breakdown[job.team_id]["jobs"] += 1
        if job.credit_applied:
            team_breakdown[job.team_id]["credits_used"] += 1

    return {
        "organization_id": organization_id,
        "period": period,
        "summary": {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "credits_used": credits_used,
            "total_cost_usd": round(total_cost, 2),
            "total_tokens": total_tokens
        },
        "teams": team_breakdown
    }
