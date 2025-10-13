"""
Credit Management Service
Handles credit checking, deduction, allocation, and transaction logging
"""
from typing import Optional
from sqlalchemy.orm import Session
import uuid
from ..models.credits import TeamCredits, CreditTransaction


class InsufficientCreditsError(Exception):
    """Raised when team has insufficient credits"""
    pass


class CreditManager:
    """
    Service for managing team credits and transactions
    """

    def __init__(self, db: Session):
        self.db = db

    def get_team_credits(self, team_id: str) -> Optional[TeamCredits]:
        """
        Get credit balance for a team
        """
        return self.db.query(TeamCredits).filter(
            TeamCredits.team_id == team_id
        ).first()

    def check_credits_available(self, team_id: str, credits_needed: int = 1) -> bool:
        """
        Check if team has sufficient credits available

        Args:
            team_id: Team to check
            credits_needed: Number of credits required (default 1)

        Returns:
            True if credits available

        Raises:
            InsufficientCreditsError: If insufficient credits
        """
        credits = self.get_team_credits(team_id)

        if not credits:
            raise InsufficientCreditsError(
                f"No credit account found for team '{team_id}'"
            )

        if credits.credits_remaining < credits_needed:
            raise InsufficientCreditsError(
                f"Insufficient credits. Team has {credits.credits_remaining} credits remaining, "
                f"but {credits_needed} required. Allocated: {credits.credits_allocated}, "
                f"Used: {credits.credits_used}"
            )

        return True

    def deduct_credit(
        self,
        team_id: str,
        job_id: Optional[uuid.UUID] = None,
        credits_amount: int = 1,
        reason: str = "Job completed successfully"
    ) -> CreditTransaction:
        """
        Deduct credits from a team's balance

        Args:
            team_id: Team to deduct from
            job_id: Associated job ID (if any)
            credits_amount: Number of credits to deduct
            reason: Reason for deduction

        Returns:
            CreditTransaction record

        Raises:
            InsufficientCreditsError: If insufficient credits
        """
        # Get team credits
        credits = self.get_team_credits(team_id)

        if not credits:
            raise InsufficientCreditsError(f"No credit account found for team '{team_id}'")

        # Check sufficient credits
        if credits.credits_remaining < credits_amount:
            raise InsufficientCreditsError(
                f"Cannot deduct {credits_amount} credits. Only {credits.credits_remaining} remaining."
            )

        # Record state before deduction
        credits_before = credits.credits_remaining

        # Deduct credits
        credits.credits_used += credits_amount

        # Create transaction record
        transaction = CreditTransaction(
            team_id=team_id,
            organization_id=credits.organization_id,
            job_id=job_id,
            transaction_type="deduction",
            credits_amount=credits_amount,
            credits_before=credits_before,
            credits_after=credits_before - credits_amount,
            reason=reason
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(credits)
        self.db.refresh(transaction)

        return transaction

    def allocate_credits(
        self,
        team_id: str,
        credits_amount: int,
        reason: str = "Credit allocation",
        organization_id: Optional[str] = None
    ) -> CreditTransaction:
        """
        Allocate (add) credits to a team's balance

        Args:
            team_id: Team to allocate to
            credits_amount: Number of credits to add
            reason: Reason for allocation
            organization_id: Organization ID (if applicable)

        Returns:
            CreditTransaction record
        """
        # Get or create team credits
        credits = self.get_team_credits(team_id)

        if not credits:
            credits = TeamCredits(
                team_id=team_id,
                organization_id=organization_id,
                credits_allocated=0,
                credits_used=0
            )
            self.db.add(credits)
            self.db.flush()

        # Record state before allocation
        credits_before = credits.credits_remaining

        # Add credits
        credits.credits_allocated += credits_amount

        # Create transaction record
        transaction = CreditTransaction(
            team_id=team_id,
            organization_id=organization_id or credits.organization_id,
            transaction_type="allocation",
            credits_amount=credits_amount,
            credits_before=credits_before,
            credits_after=credits_before + credits_amount,
            reason=reason
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(credits)
        self.db.refresh(transaction)

        return transaction

    def refund_credit(
        self,
        team_id: str,
        job_id: Optional[uuid.UUID] = None,
        credits_amount: int = 1,
        reason: str = "Credit refund"
    ) -> CreditTransaction:
        """
        Refund credits to a team (undo deduction)

        Args:
            team_id: Team to refund
            job_id: Associated job ID (if any)
            credits_amount: Number of credits to refund
            reason: Reason for refund

        Returns:
            CreditTransaction record
        """
        credits = self.get_team_credits(team_id)

        if not credits:
            raise ValueError(f"No credit account found for team '{team_id}'")

        # Record state before refund
        credits_before = credits.credits_remaining

        # Refund credits (decrease credits_used)
        credits.credits_used = max(0, credits.credits_used - credits_amount)

        # Create transaction record
        transaction = CreditTransaction(
            team_id=team_id,
            organization_id=credits.organization_id,
            job_id=job_id,
            transaction_type="refund",
            credits_amount=credits_amount,
            credits_before=credits_before,
            credits_after=credits_before + credits_amount,
            reason=reason
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(credits)
        self.db.refresh(transaction)

        return transaction

    def get_credit_transactions(
        self,
        team_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        job_id: Optional[uuid.UUID] = None,
        limit: int = 100
    ) -> list[CreditTransaction]:
        """
        Get credit transactions with optional filters

        Args:
            team_id: Filter by team
            organization_id: Filter by organization
            job_id: Filter by job
            limit: Maximum number of records to return

        Returns:
            List of CreditTransaction records
        """
        query = self.db.query(CreditTransaction)

        if team_id:
            query = query.filter(CreditTransaction.team_id == team_id)

        if organization_id:
            query = query.filter(CreditTransaction.organization_id == organization_id)

        if job_id:
            query = query.filter(CreditTransaction.job_id == job_id)

        return query.order_by(CreditTransaction.created_at.desc()).limit(limit).all()


def get_credit_manager(db: Session) -> CreditManager:
    """
    Factory function to get a CreditManager instance
    """
    return CreditManager(db)
