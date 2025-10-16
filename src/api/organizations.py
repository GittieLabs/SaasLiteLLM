"""
Organizations API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.organizations import Organization
from ..models.job_tracking import Job, get_db
from ..auth.dependencies import verify_admin_auth

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


# Request/Response Models
class OrganizationCreateRequest(BaseModel):
    organization_id: str
    name: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OrganizationResponse(BaseModel):
    organization_id: str
    name: str
    status: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


# Endpoints
@router.get("", response_model=list)
async def list_organizations(
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    List all organizations.

    Requires: Admin authentication (JWT Bearer token or X-Admin-Key header)
    """
    orgs = db.query(Organization).filter(
        Organization.status == "active"
    ).all()

    return [OrganizationResponse(**org.to_dict()) for org in orgs]


@router.post("/create", response_model=OrganizationResponse)
async def create_organization(
    request: OrganizationCreateRequest,
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Create a new organization.

    Requires: Admin authentication (JWT Bearer token or X-Admin-Key header)
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

    return OrganizationResponse(**org.to_dict())


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Get organization details.

    Requires: Admin authentication (JWT Bearer token or X-Admin-Key header)
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
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    List all teams in an organization.

    Requires: Admin authentication (JWT Bearer token or X-Admin-Key header)
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

    # Get all jobs for this organization to extract unique team_ids
    jobs = db.query(Job.team_id).filter(
        Job.organization_id == organization_id
    ).distinct().all()

    team_ids = [job.team_id for job in jobs]

    return {
        "organization_id": organization_id,
        "team_count": len(team_ids),
        "teams": team_ids
    }


@router.get("/{organization_id}/usage")
async def get_organization_usage(
    organization_id: str,
    period: str,  # e.g., "2025-10"
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Get organization-wide usage for a period.

    Requires: Admin authentication (JWT Bearer token or X-Admin-Key header)
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
