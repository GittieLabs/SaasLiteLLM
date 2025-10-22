"""
Database models for job-based cost tracking
"""
from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, JSON, Enum, Boolean,
    ForeignKey, Index, func, ARRAY
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session, sessionmaker
import uuid
import enum
from datetime import datetime

Base = declarative_base()


# Database session management
def get_db():
    """Dependency for database session (to be configured with actual engine)"""
    from ..config.settings import settings
    from sqlalchemy import create_engine
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Job(Base):
    """
    Main job tracking table.
    Represents a business operation that may involve multiple LLM calls.
    """
    __tablename__ = "jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    job_type = Column(String(100), nullable=False, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Custom metadata for your SaaS business logic
    job_metadata = Column(JSON, default=dict)

    # Error tracking
    error_message = Column(String(1000), nullable=True)

    # New fields for multi-tenant and credit tracking
    organization_id = Column(String(255), nullable=True, index=True)
    external_task_id = Column(String(255), nullable=True, index=True)  # Your SaaS app's task ID
    credit_applied = Column(Boolean, default=False)
    model_groups_used = Column(ARRAY(String), default=list)  # Array of model group names used

    __table_args__ = (
        Index('idx_team_created', 'team_id', 'created_at'),
        Index('idx_team_status', 'team_id', 'status'),
        Index('idx_job_type_created', 'job_type', 'created_at'),
    )

    def to_dict(self):
        return {
            "job_id": str(self.job_id),
            "team_id": self.team_id,
            "user_id": self.user_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.job_metadata,
            "error_message": self.error_message,
            "organization_id": self.organization_id,
            "external_task_id": self.external_task_id,
            "credit_applied": self.credit_applied,
            "model_groups_used": self.model_groups_used or []
        }


class LLMCall(Base):
    """
    Individual LLM API calls within a job.
    Tracks costs and performance per call.
    """
    __tablename__ = "llm_calls"

    call_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.job_id', ondelete='CASCADE'), nullable=False, index=True)

    # LiteLLM tracking
    litellm_request_id = Column(String(255), nullable=True, unique=True)
    model_used = Column(String(100), nullable=True)

    # Token usage
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost tracking (in USD)
    cost_usd = Column(Numeric(10, 6), default=0.0)  # Legacy field
    input_cost_usd = Column(Numeric(10, 8), nullable=True)  # Cost for input tokens
    output_cost_usd = Column(Numeric(10, 8), nullable=True)  # Cost for output tokens
    provider_cost_usd = Column(Numeric(10, 8), nullable=True)  # What LiteLLM charged us
    client_cost_usd = Column(Numeric(10, 8), nullable=True)  # What we charge client (with markup)

    # Model pricing at time of call (per 1M tokens)
    model_pricing_input = Column(Numeric(10, 6), nullable=True)  # Input price per 1M tokens for resolved model
    model_pricing_output = Column(Numeric(10, 6), nullable=True)  # Output price per 1M tokens for resolved model

    # Performance metrics
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Purpose/categorization within job
    purpose = Column(String(200), nullable=True)

    # Store request/response for debugging (optional)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)

    # Error tracking
    error = Column(String(1000), nullable=True)

    # New fields for model group tracking
    model_group_used = Column(String(100), nullable=True, index=True)  # e.g., "ResumeAgent"
    resolved_model = Column(String(200), nullable=True)  # Actual model after resolution

    __table_args__ = (
        Index('idx_job_created', 'job_id', 'created_at'),
    )

    def to_dict(self):
        return {
            "call_id": str(self.call_id),
            "job_id": str(self.job_id),
            "model_used": self.model_used,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": float(self.cost_usd) if self.cost_usd else 0.0,
            "input_cost_usd": float(self.input_cost_usd) if self.input_cost_usd else 0.0,
            "output_cost_usd": float(self.output_cost_usd) if self.output_cost_usd else 0.0,
            "provider_cost_usd": float(self.provider_cost_usd) if self.provider_cost_usd else 0.0,
            "client_cost_usd": float(self.client_cost_usd) if self.client_cost_usd else 0.0,
            "model_pricing_input": float(self.model_pricing_input) if self.model_pricing_input else None,
            "model_pricing_output": float(self.model_pricing_output) if self.model_pricing_output else None,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "purpose": self.purpose,
            "error": self.error,
            "model_group_used": self.model_group_used,
            "resolved_model": self.resolved_model
        }


class JobCostSummary(Base):
    """
    Aggregated cost summary per job.
    Updated when job completes.
    """
    __tablename__ = "job_cost_summaries"

    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.job_id', ondelete='CASCADE'), primary_key=True)

    # Aggregated counts
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)

    # Token aggregation
    total_prompt_tokens = Column(Integer, default=0)
    total_completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost aggregation (actual LiteLLM costs)
    total_cost_usd = Column(Numeric(12, 6), default=0.0)

    # Performance
    avg_latency_ms = Column(Integer, nullable=True)
    total_duration_seconds = Column(Integer, nullable=True)

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "job_id": str(self.job_id),
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": float(self.total_cost_usd) if self.total_cost_usd else 0.0,
            "avg_latency_ms": self.avg_latency_ms,
            "total_duration_seconds": self.total_duration_seconds,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None
        }


class TeamUsageSummary(Base):
    """
    Team-level usage analytics by period (daily/monthly).
    For your internal billing and analytics.
    """
    __tablename__ = "team_usage_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(String(255), nullable=False, index=True)
    period = Column(String(50), nullable=False)  # Format: "2024-10" or "2024-10-08"
    period_type = Column(String(20), default="monthly")  # "daily" or "monthly"

    # Job counts
    total_jobs = Column(Integer, default=0)
    successful_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    cancelled_jobs = Column(Integer, default=0)

    # Cost totals
    total_cost_usd = Column(Numeric(12, 2), default=0.0)
    total_tokens = Column(Integer, default=0)

    # Per job type breakdown
    job_type_breakdown = Column(JSON, default=dict)
    # Example: {"document_analysis": {"count": 50, "cost_usd": 5.20}, ...}

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_team_period', 'team_id', 'period', unique=True),
    )

    def to_dict(self):
        return {
            "team_id": self.team_id,
            "period": self.period,
            "period_type": self.period_type,
            "total_jobs": self.total_jobs,
            "successful_jobs": self.successful_jobs,
            "failed_jobs": self.failed_jobs,
            "cancelled_jobs": self.cancelled_jobs,
            "total_cost_usd": float(self.total_cost_usd) if self.total_cost_usd else 0.0,
            "total_tokens": self.total_tokens,
            "job_type_breakdown": self.job_type_breakdown,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None
        }


class WebhookRegistration(Base):
    """
    Webhook registrations for job events.
    """
    __tablename__ = "webhook_registrations"

    webhook_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(String(255), nullable=False, index=True)
    webhook_url = Column(String(500), nullable=False)
    events = Column(JSON, default=list)  # ["job.completed", "job.failed"]
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)

    # Auth for webhook calls (optional)
    auth_header = Column(String(500), nullable=True)

    def to_dict(self):
        return {
            "webhook_id": str(self.webhook_id),
            "team_id": self.team_id,
            "webhook_url": self.webhook_url,
            "events": self.events,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None
        }
