"""
Credits API endpoints (Minimal Version)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ..services.credit_manager import get_credit_manager, InsufficientCreditsError
from ..models.job_tracking import get_db
from ..auth.dependencies import verify_virtual_key

router = APIRouter(prefix="/api/credits", tags=["credits"])


# Request/Response Models
class AddCreditsRequest(BaseModel):
    credits: int
    reason: Optional[str] = "Manual credit allocation"


# Endpoints
@router.get("/teams/{team_id}/balance")
async def get_credit_balance(
    team_id: str,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Get credit balance for a team.

    Requires: Authorization header with virtual API key
    """
    # Verify authenticated team matches requested team
    if team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access credit balance for a different team"
        )

    credit_manager = get_credit_manager(db)
    credits = credit_manager.get_team_credits(team_id)

    if not credits:
        raise HTTPException(
            status_code=404,
            detail=f"No credit account found for team '{team_id}'"
        )

    return credits.to_dict()


@router.post("/teams/{team_id}/add")
async def add_credits(
    team_id: str,
    request: AddCreditsRequest,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Add credits to a team's balance.

    Requires: Authorization header with virtual API key
    """
    # Verify authenticated team matches requested team
    if team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot add credits to a different team"
        )

    credit_manager = get_credit_manager(db)

    try:
        transaction = credit_manager.allocate_credits(
            team_id=team_id,
            credits_amount=request.credits,
            reason=request.reason
        )

        return {
            "team_id": team_id,
            "credits_added": request.credits,
            "transaction": transaction.to_dict()
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/teams/{team_id}/transactions")
async def get_credit_transactions(
    team_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Get credit transaction history for a team.

    Requires: Authorization header with virtual API key
    """
    # Verify authenticated team matches requested team
    if team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access credit transactions for a different team"
        )

    credit_manager = get_credit_manager(db)
    transactions = credit_manager.get_credit_transactions(
        team_id=team_id,
        limit=limit
    )

    return {
        "team_id": team_id,
        "total": len(transactions),
        "transactions": [t.to_dict() for t in transactions]
    }


@router.post("/teams/{team_id}/check")
async def check_credits(
    team_id: str,
    credits_needed: int = 1,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Check if team has sufficient credits.

    Requires: Authorization header with virtual API key
    """
    # Verify authenticated team matches requested team
    if team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot check credits for a different team"
        )

    credit_manager = get_credit_manager(db)

    try:
        credit_manager.check_credits_available(team_id, credits_needed)
        credits = credit_manager.get_team_credits(team_id)

        return {
            "team_id": team_id,
            "has_credits": True,
            "credits_remaining": credits.credits_remaining,
            "credits_needed": credits_needed
        }

    except InsufficientCreditsError as e:
        return {
            "team_id": team_id,
            "has_credits": False,
            "error": str(e),
            "credits_needed": credits_needed
        }
