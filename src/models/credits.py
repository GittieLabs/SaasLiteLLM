"""
Credit tracking models for billing and usage limits
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UUID, Index, Computed, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
import uuid
from .job_tracking import Base


class TeamCredits(Base):
    """
    Team credit balance and allocation tracking
    """
    __tablename__ = "team_credits"

    team_id = Column(String(255), primary_key=True)
    organization_id = Column(String(255), ForeignKey('organizations.organization_id'))
    credits_allocated = Column(Integer, default=0)
    credits_used = Column(Integer, default=0)
    # credits_remaining is computed in database as (credits_allocated - credits_used)
    credits_remaining = Column(Integer, Computed("credits_allocated - credits_used"), nullable=False)
    credit_limit = Column(Integer)
    auto_refill = Column(Boolean, default=False)
    refill_amount = Column(Integer)
    refill_period = Column(String(50))  # 'monthly', 'weekly', 'daily'
    last_refill_at = Column(DateTime)
    virtual_key = Column(String(500))  # LiteLLM virtual API key for this team
    # Budget mode: how credits are deducted
    budget_mode = Column(String(50), default='job_based', nullable=False)  # 'job_based', 'consumption_usd', 'consumption_tokens'
    credits_per_dollar = Column(Numeric(10, 2), default=10.0)  # Conversion rate for consumption_usd mode
    status = Column(String(20), default='active', nullable=False)  # 'active', 'suspended', 'paused'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_team_credits_org', 'organization_id'),
        Index('idx_team_credits_remaining', 'credits_remaining'),
    )

    def to_dict(self):
        return {
            "team_id": self.team_id,
            "organization_id": self.organization_id,
            "credits_allocated": self.credits_allocated,
            "credits_used": self.credits_used,
            "credits_remaining": self.credits_remaining,
            "credit_limit": self.credit_limit,
            "auto_refill": self.auto_refill,
            "refill_amount": self.refill_amount,
            "refill_period": self.refill_period,
            "last_refill_at": self.last_refill_at.isoformat() if self.last_refill_at else None,
            "budget_mode": self.budget_mode,
            "credits_per_dollar": float(self.credits_per_dollar) if self.credits_per_dollar else 10.0,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CreditTransaction(Base):
    """
    Audit log of all credit transactions (deductions, allocations, refunds)
    """
    __tablename__ = "credit_transactions"

    transaction_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(String(255), nullable=False)
    organization_id = Column(String(255))
    job_id = Column(PG_UUID(as_uuid=True), ForeignKey('jobs.job_id'))
    transaction_type = Column(String(50), nullable=False)  # 'deduction', 'allocation', 'refund', 'adjustment'
    credits_amount = Column(Integer, nullable=False)
    credits_before = Column(Integer, nullable=False)
    credits_after = Column(Integer, nullable=False)
    reason = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_credit_transactions_team', 'team_id', 'created_at'),
        Index('idx_credit_transactions_job', 'job_id'),
        Index('idx_credit_transactions_org', 'organization_id', 'created_at'),
        Index('idx_credit_transactions_type', 'transaction_type'),
    )

    def to_dict(self):
        return {
            "transaction_id": str(self.transaction_id),
            "team_id": self.team_id,
            "organization_id": self.organization_id,
            "job_id": str(self.job_id) if self.job_id else None,
            "transaction_type": self.transaction_type,
            "credits_amount": self.credits_amount,
            "credits_before": self.credits_before,
            "credits_after": self.credits_after,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
