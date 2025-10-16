"""
Dashboard API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models.organizations import Organization
from ..models.model_groups import ModelGroup
from ..models.credits import TeamCredits
from ..models.job_tracking import get_db

router = APIRouter(prefix="/api/stats", tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard_stats(
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics
    """
    # Count organizations
    organizations_count = db.query(Organization).filter(
        Organization.status == "active"
    ).count()

    # Count teams
    teams_count = db.query(TeamCredits).count()

    # Count model groups
    model_groups_count = db.query(ModelGroup).filter(
        ModelGroup.status == "active"
    ).count()

    # Sum total credits allocated across all teams
    total_credits = db.query(TeamCredits).all()
    total_credits_allocated = sum(t.credits_allocated for t in total_credits)
    total_credits_remaining = sum(t.credits_remaining for t in total_credits)

    return {
        "organizations": organizations_count,
        "teams": teams_count,
        "modelGroups": model_groups_count,
        "totalCredits": total_credits_allocated,
        "creditsRemaining": total_credits_remaining,
        "creditsUsed": total_credits_allocated - total_credits_remaining
    }
