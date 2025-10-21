"""
Credits API endpoints (Minimal Version)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ..services.credit_manager import get_credit_manager, InsufficientCreditsError
from ..models.job_tracking import get_db
from ..auth.dependencies import verify_virtual_key, verify_admin_auth

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
    _ = Depends(verify_admin_auth)
):
    """
    Add credits to a team's balance. ADMIN ONLY.

    Requires: Admin authentication (JWT Bearer token or X-Admin-Key header)
    """

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


class UpdateConversionRatesRequest(BaseModel):
    """Request model for updating team-specific conversion rates"""
    tokens_per_credit: Optional[int] = None
    credits_per_dollar: Optional[float] = None


@router.patch("/teams/{team_id}/conversion-rates")
async def update_conversion_rates(
    team_id: str,
    request: UpdateConversionRatesRequest,
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Update team-specific conversion rates for credit calculations. ADMIN ONLY.

    - tokens_per_credit: Number of tokens equivalent to 1 credit (for consumption_tokens mode)
    - credits_per_dollar: Number of credits per dollar (for consumption_usd mode)

    If not set or set to None, the system will use default values.

    Requires: Admin authentication (JWT Bearer token or X-Admin-Key header)
    """
    from ..models.credits import TeamCredits

    # Get team credits
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == team_id
    ).first()

    if not team_credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )

    # Validate values
    if request.tokens_per_credit is not None:
        if request.tokens_per_credit <= 0:
            raise HTTPException(
                status_code=400,
                detail="tokens_per_credit must be a positive integer"
            )
        team_credits.tokens_per_credit = request.tokens_per_credit

    if request.credits_per_dollar is not None:
        if request.credits_per_dollar <= 0:
            raise HTTPException(
                status_code=400,
                detail="credits_per_dollar must be a positive number"
            )
        team_credits.credits_per_dollar = request.credits_per_dollar

    db.commit()
    db.refresh(team_credits)

    return {
        "team_id": team_id,
        "tokens_per_credit": team_credits.tokens_per_credit,
        "credits_per_dollar": float(team_credits.credits_per_dollar) if team_credits.credits_per_dollar else None,
        "message": "Conversion rates updated successfully"
    }


@router.get("/teams/{team_id}/conversion-rates")
async def get_conversion_rates(
    team_id: str,
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Get team-specific conversion rates for credit calculations. ADMIN ONLY.

    Requires: Admin authentication (JWT Bearer token or X-Admin-Key header)
    """
    from ..models.credits import TeamCredits
    from ..api.constants import DEFAULT_TOKENS_PER_CREDIT, DEFAULT_CREDITS_PER_DOLLAR

    # Get team credits
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == team_id
    ).first()

    if not team_credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )

    return {
        "team_id": team_id,
        "tokens_per_credit": team_credits.tokens_per_credit if team_credits.tokens_per_credit else DEFAULT_TOKENS_PER_CREDIT,
        "credits_per_dollar": float(team_credits.credits_per_dollar) if team_credits.credits_per_dollar else DEFAULT_CREDITS_PER_DOLLAR,
        "budget_mode": team_credits.budget_mode,
        "using_defaults": {
            "tokens_per_credit": team_credits.tokens_per_credit is None,
            "credits_per_dollar": team_credits.credits_per_dollar is None
        }
    }
