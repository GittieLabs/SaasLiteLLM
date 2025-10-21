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


class ReplenishCreditsRequest(BaseModel):
    """Request model for replenishing credits from payment"""
    credits: int
    payment_type: str  # 'subscription' or 'one_time'
    payment_amount_usd: Optional[float] = None  # Actual USD amount paid
    reason: Optional[str] = None


class ConfigureAutoRefillRequest(BaseModel):
    """Request model for configuring automatic credit refills"""
    enabled: bool
    refill_amount: Optional[int] = None
    refill_period: Optional[str] = None  # 'monthly', 'weekly', 'daily'


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


@router.post("/teams/{team_id}/replenish")
async def replenish_credits(
    team_id: str,
    request: ReplenishCreditsRequest,
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Replenish credits from a payment (subscription or one-time purchase). ADMIN ONLY.

    This endpoint should be called after processing a payment to add credits to the team's balance.
    Creates a transaction record with type 'subscription_payment' or 'one_time_payment'.

    Requires: Admin authentication (JWT Bearer token or X-Admin-Key header)
    """
    from ..models.credits import TeamCredits, CreditTransaction
    from datetime import datetime

    # Validate payment_type
    if request.payment_type not in ['subscription', 'one_time']:
        raise HTTPException(
            status_code=400,
            detail="payment_type must be 'subscription' or 'one_time'"
        )

    # Validate credits amount
    if request.credits <= 0:
        raise HTTPException(
            status_code=400,
            detail="credits must be a positive integer"
        )

    # Get team credits
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == team_id
    ).first()

    if not team_credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )

    # Record current balance
    credits_before = team_credits.credits_allocated

    # Add credits
    team_credits.credits_allocated += request.credits

    # Update last_refill_at for subscription payments
    if request.payment_type == 'subscription':
        team_credits.last_refill_at = datetime.utcnow()

    # Create transaction record
    transaction_type = f"{request.payment_type}_payment"
    reason = request.reason or f"Credit replenishment from {request.payment_type} payment"

    if request.payment_amount_usd:
        reason += f" (${request.payment_amount_usd:.2f} USD)"

    transaction = CreditTransaction(
        team_id=team_id,
        organization_id=team_credits.organization_id,
        transaction_type=transaction_type,
        credits_amount=request.credits,
        credits_before=credits_before,
        credits_after=team_credits.credits_allocated,
        reason=reason
    )

    db.add(transaction)
    db.commit()
    db.refresh(team_credits)
    db.refresh(transaction)

    return {
        "team_id": team_id,
        "credits_added": request.credits,
        "credits_before": credits_before,
        "credits_after": team_credits.credits_allocated,
        "payment_type": request.payment_type,
        "payment_amount_usd": request.payment_amount_usd,
        "transaction": transaction.to_dict()
    }


@router.post("/teams/{team_id}/configure-auto-refill")
async def configure_auto_refill(
    team_id: str,
    request: ConfigureAutoRefillRequest,
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Configure automatic credit refills for a team. ADMIN ONLY.

    When enabled, credits will be automatically replenished at the specified interval.
    This is typically tied to subscription billing cycles.

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

    # Validate refill_period if provided
    if request.enabled and request.refill_period:
        if request.refill_period not in ['monthly', 'weekly', 'daily']:
            raise HTTPException(
                status_code=400,
                detail="refill_period must be 'monthly', 'weekly', or 'daily'"
            )

    # Validate refill_amount if enabling
    if request.enabled:
        if request.refill_amount is None or request.refill_amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="refill_amount must be a positive integer when enabling auto-refill"
            )
        if request.refill_period is None:
            raise HTTPException(
                status_code=400,
                detail="refill_period must be specified when enabling auto-refill"
            )

    # Update auto-refill configuration
    team_credits.auto_refill = request.enabled

    if request.enabled:
        team_credits.refill_amount = request.refill_amount
        team_credits.refill_period = request.refill_period
    else:
        # When disabling, we keep the settings but mark as disabled
        team_credits.refill_amount = request.refill_amount if request.refill_amount else team_credits.refill_amount
        team_credits.refill_period = request.refill_period if request.refill_period else team_credits.refill_period

    db.commit()
    db.refresh(team_credits)

    return {
        "team_id": team_id,
        "auto_refill_enabled": team_credits.auto_refill,
        "refill_amount": team_credits.refill_amount,
        "refill_period": team_credits.refill_period,
        "last_refill_at": team_credits.last_refill_at.isoformat() if team_credits.last_refill_at else None,
        "message": f"Auto-refill {'enabled' if request.enabled else 'disabled'} successfully"
    }
