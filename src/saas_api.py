"""
SaaS API Wrapper for LiteLLM
Provides job-based cost tracking abstraction layer
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import httpx
import uuid

from .config.settings import settings
from .models.job_tracking import (
    Base, Job, LLMCall, JobCostSummary, TeamUsageSummary,
    WebhookRegistration, JobStatus
)

# Import new API routers
from .api import organizations, model_groups, teams, credits

# Import authentication
from .auth.dependencies import verify_virtual_key

# Create FastAPI app
app = FastAPI(
    title="SaaS LLM API",
    description="Job-based LLM API with cost tracking and model group management",
    version="2.0.0"
)

# Add CORS middleware to allow browser-based admin panel to connect
# IMPORTANT: CORS is a BROWSER-ONLY security feature!
#
# Server-side team clients (Python requests, Node.js, curl, Go http, etc.)
# completely IGNORE CORS restrictions. They are NOT affected by this config.
#
# CORS only applies to JavaScript running in web browsers (like the admin panel).
# Team API authentication is via Bearer tokens, which works regardless of CORS.
#
# This CORS config is specifically for the browser-based admin panel (Next.js).

# Build CORS origins list dynamically from environment variables
cors_origins = [
    # Local development
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
]

# Add production admin panel URL if configured
# In Railway, set: ADMIN_PANEL_URL=https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}
if settings.admin_panel_url:
    cors_origins.append(settings.admin_panel_url)

# Add additional CORS origins if configured (comma-separated)
if settings.additional_cors_origins:
    additional = [
        origin.strip()
        for origin in settings.additional_cors_origins.split(',')
        if origin.strip()
    ]
    cors_origins.extend(additional)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers (including X-Admin-Key)
)

# Include new routers
app.include_router(organizations.router)
app.include_router(model_groups.router)
app.include_router(teams.router)
app.include_router(credits.router)

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@app.on_event("startup")
async def startup_event():
    """Ensure database tables exist on startup"""
    # Import all models to ensure they're registered with Base
    from .models import organizations, model_groups, credits

    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Request/Response Models
class JobCreateRequest(BaseModel):
    team_id: str
    user_id: Optional[str] = None
    job_type: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    created_at: str


class LLMCallRequest(BaseModel):
    model_group: str  # Name of model group (e.g., "ResumeAgent", "ParsingAgent")
    messages: List[Dict[str, str]]
    purpose: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None


class LLMCallResponse(BaseModel):
    call_id: str
    response: Dict[str, Any]
    metadata: Dict[str, Any]


class JobCompleteRequest(BaseModel):
    status: str  # "completed" or "failed"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    error_message: Optional[str] = None


class JobCompleteResponse(BaseModel):
    job_id: str
    status: str
    completed_at: str
    costs: Dict[str, Any]
    calls: List[Dict[str, Any]]


# Helper Functions
async def call_litellm(
    model: str,
    messages: List[Dict[str, str]],
    virtual_key: str,
    team_id: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Call LiteLLM proxy with resolved model and team-specific virtual key.
    Returns response with usage and cost data.
    """
    litellm_url = f"{settings.litellm_proxy_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {virtual_key}",  # Use team virtual key
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,  # Resolved model from model group
        "messages": messages,
        "temperature": temperature,
        "user": team_id,  # For LiteLLM tracking
    }

    if max_tokens:
        payload["max_tokens"] = max_tokens

    async with httpx.AsyncClient() as client:
        response = await client.post(litellm_url, json=payload, headers=headers, timeout=120.0)
        response.raise_for_status()
        return response.json()


def calculate_job_costs(db: Session, job_id: uuid.UUID) -> Dict[str, Any]:
    """Calculate aggregated costs for a job"""
    calls = db.query(LLMCall).filter(LLMCall.job_id == job_id).all()

    if not calls:
        return {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0
        }

    total_calls = len(calls)
    successful_calls = len([c for c in calls if not c.error])
    failed_calls = total_calls - successful_calls
    total_tokens = sum(c.total_tokens for c in calls)
    total_cost_usd = sum(float(c.cost_usd) for c in calls)
    avg_latency_ms = int(sum(c.latency_ms for c in calls if c.latency_ms) / len([c for c in calls if c.latency_ms])) if any(c.latency_ms for c in calls) else 0

    return {
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost_usd, 6),
        "avg_latency_ms": avg_latency_ms
    }


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "saas-llm-api"}


@app.post("/api/jobs/create", response_model=JobCreateResponse)
async def create_job(
    request: JobCreateRequest,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Create a new job for tracking multiple LLM calls.
    Teams use this to start a business operation.

    Requires: Authorization header with virtual API key
    """
    # Verify that the authenticated team matches the request
    if request.team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail=f"API key does not belong to team '{request.team_id}'"
        )

    job = Job(
        team_id=request.team_id,
        user_id=request.user_id,
        job_type=request.job_type,
        status=JobStatus.PENDING,
        job_metadata=request.metadata
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return JobCreateResponse(
        job_id=str(job.job_id),
        status=job.status.value,
        created_at=job.created_at.isoformat()
    )


@app.post("/api/jobs/{job_id}/llm-call", response_model=LLMCallResponse)
async def make_llm_call(
    job_id: str,
    request: LLMCallRequest,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Make an LLM call within a job context using model group resolution.
    Automatically tracks costs and associates with job.

    Requires: Authorization header with virtual API key
    """
    from .models.credits import TeamCredits
    from .services.model_resolver import ModelResolver, ModelResolutionError

    # Get job
    job = db.query(Job).filter(Job.job_id == uuid.UUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify job belongs to authenticated team
    if job.team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Job does not belong to your team"
        )

    # Get team credits and virtual key
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == job.team_id
    ).first()

    if not team_credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{job.team_id}' not found"
        )

    if not team_credits.virtual_key:
        raise HTTPException(
            status_code=500,
            detail=f"Team '{job.team_id}' has no virtual key configured"
        )

    # Update job status to in_progress if pending
    if job.status == JobStatus.PENDING:
        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.utcnow()
        db.commit()

    # Resolve model group to actual model
    model_resolver = ModelResolver(db)

    try:
        primary_model, fallback_models = model_resolver.resolve_model_group(
            team_id=job.team_id,
            model_group_name=request.model_group
        )
    except ModelResolutionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Track this model group usage (add to list if not already there)
    if not job.model_groups_used:
        job.model_groups_used = []
    if request.model_group not in job.model_groups_used:
        job.model_groups_used.append(request.model_group)
        db.commit()

    # Call LiteLLM with resolved model
    start_time = datetime.utcnow()
    try:
        litellm_response = await call_litellm(
            model=primary_model,
            messages=request.messages,
            virtual_key=team_credits.virtual_key,
            team_id=job.team_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        end_time = datetime.utcnow()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        # Extract usage and cost data
        usage = litellm_response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # Calculate cost (LiteLLM includes this in response metadata)
        # For now, estimate: gpt-3.5-turbo is $0.0005/1K prompt, $0.0015/1K completion
        cost_usd = (prompt_tokens * 0.0005 / 1000) + (completion_tokens * 0.0015 / 1000)

        # Store LLM call record with model group tracking
        llm_call = LLMCall(
            job_id=job.job_id,
            litellm_request_id=litellm_response.get("id"),
            model_used=litellm_response.get("model", primary_model),
            model_group_used=request.model_group,
            resolved_model=primary_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            purpose=request.purpose,
            request_data={"messages": request.messages, "model_group": request.model_group},
            response_data=litellm_response
        )

        db.add(llm_call)
        db.commit()
        db.refresh(llm_call)

        # Return response (without exposing model or cost to client)
        return LLMCallResponse(
            call_id=str(llm_call.call_id),
            response={
                "content": litellm_response["choices"][0]["message"]["content"],
                "finish_reason": litellm_response["choices"][0]["finish_reason"]
            },
            metadata={
                "tokens_used": total_tokens,
                "latency_ms": latency_ms,
                "model_group": request.model_group
            }
        )

    except Exception as e:
        # Record failed call
        llm_call = LLMCall(
            job_id=job.job_id,
            model_group_used=request.model_group,
            purpose=request.purpose,
            error=str(e),
            request_data={"messages": request.messages, "model_group": request.model_group}
        )
        db.add(llm_call)
        db.commit()

        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")


@app.post("/api/jobs/{job_id}/complete", response_model=JobCompleteResponse)
async def complete_job(
    job_id: str,
    request: JobCompleteRequest,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Mark job as complete, deduct credits if successful, and return aggregated costs.
    Credits are only deducted for successfully completed jobs with no failed calls.

    Requires: Authorization header with virtual API key
    """
    from .services.credit_manager import get_credit_manager, InsufficientCreditsError

    job = db.query(Job).filter(Job.job_id == uuid.UUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify job belongs to authenticated team
    if job.team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Job does not belong to your team"
        )

    # Update job status
    job.status = JobStatus(request.status)
    job.completed_at = datetime.utcnow()
    if request.error_message:
        job.error_message = request.error_message
    if request.metadata:
        job.job_metadata.update(request.metadata)

    # Calculate costs
    costs = calculate_job_costs(db, job.job_id)

    # Credit deduction logic
    credit_manager = get_credit_manager(db)

    # Deduct credit only if:
    # 1. Job status is "completed" (not "failed")
    # 2. No failed LLM calls
    # 3. Credit hasn't already been applied
    if (request.status == "completed" and
        costs["failed_calls"] == 0 and
        not job.credit_applied):

        try:
            # Deduct 1 credit for successful job
            credit_manager.deduct_credit(
                team_id=job.team_id,
                job_id=job.job_id,
                credits_amount=1,
                reason=f"Job {job.job_type} completed successfully"
            )
            job.credit_applied = True
        except InsufficientCreditsError as e:
            # Log the error but don't fail the job completion
            # The job is already done, we just can't charge for it
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Job {job_id} completed but couldn't deduct credit: {str(e)}"
            )
    else:
        # Job failed or had errors - no credit deduction
        job.credit_applied = False

    db.commit()

    # Store cost summary
    cost_summary = JobCostSummary(
        job_id=job.job_id,
        total_calls=costs["total_calls"],
        successful_calls=costs["successful_calls"],
        failed_calls=costs["failed_calls"],
        total_tokens=costs["total_tokens"],
        total_cost_usd=costs["total_cost_usd"],
        avg_latency_ms=costs["avg_latency_ms"],
        total_duration_seconds=int((job.completed_at - job.created_at).total_seconds()) if job.completed_at else None
    )
    db.merge(cost_summary)  # Use merge to handle updates
    db.commit()

    # Get all calls for response
    calls = db.query(LLMCall).filter(LLMCall.job_id == job.job_id).all()
    calls_data = [
        {
            "call_id": str(call.call_id),
            "purpose": call.purpose,
            "model_group": call.model_group_used,
            "tokens": call.total_tokens,
            "latency_ms": call.latency_ms,
            "error": call.error
        }
        for call in calls
    ]

    # Get updated credit balance
    from .models.credits import TeamCredits
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == job.team_id
    ).first()

    # Add credit information to costs
    costs["credit_applied"] = job.credit_applied
    costs["credits_remaining"] = team_credits.credits_remaining if team_credits else None

    return JobCompleteResponse(
        job_id=str(job.job_id),
        status=job.status.value,
        completed_at=job.completed_at.isoformat(),
        costs=costs,
        calls=calls_data
    )


@app.get("/api/jobs/{job_id}")
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Get job details.

    Requires: Authorization header with virtual API key
    """
    job = db.query(Job).filter(Job.job_id == uuid.UUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify job belongs to authenticated team
    if job.team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Job does not belong to your team"
        )

    return job.to_dict()


@app.get("/api/jobs/{job_id}/costs")
async def get_job_costs(
    job_id: str,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Get detailed cost breakdown for a job.
    This endpoint is for YOUR internal use - not exposed to teams.

    Requires: Authorization header with virtual API key
    """
    job = db.query(Job).filter(Job.job_id == uuid.UUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify job belongs to authenticated team
    if job.team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Job does not belong to your team"
        )

    calls = db.query(LLMCall).filter(LLMCall.job_id == job.job_id).all()

    breakdown = [
        {
            "call_id": str(call.call_id),
            "model": call.model_used,
            "purpose": call.purpose,
            "prompt_tokens": call.prompt_tokens,
            "completion_tokens": call.completion_tokens,
            "cost_usd": float(call.cost_usd),
            "created_at": call.created_at.isoformat()
        }
        for call in calls
    ]

    total_cost = sum(float(call.cost_usd) for call in calls)

    return {
        "job_id": str(job.job_id),
        "team_id": job.team_id,
        "job_type": job.job_type,
        "status": job.status.value,
        "costs": {
            "total_cost_usd": round(total_cost, 6),
            "breakdown": breakdown
        }
    }


@app.get("/api/teams/{team_id}/usage")
async def get_team_usage(
    team_id: str,
    period: str,  # e.g., "2024-10" or "2024-10-08"
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Get team usage summary for a period.
    For your internal billing and analytics.

    Requires: Authorization header with virtual API key
    """
    # Verify authenticated team matches requested team
    if team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access usage data for a different team"
        )
    # Get or create summary
    summary = db.query(TeamUsageSummary).filter(
        TeamUsageSummary.team_id == team_id,
        TeamUsageSummary.period == period
    ).first()

    if not summary:
        # Calculate on-the-fly
        # Get all jobs for team in period
        jobs = db.query(Job).filter(
            Job.team_id == team_id,
            func.to_char(Job.created_at, 'YYYY-MM').like(f"{period}%")
        ).all()

        total_jobs = len(jobs)
        successful_jobs = len([j for j in jobs if j.status == JobStatus.COMPLETED])
        failed_jobs = len([j for j in jobs if j.status == JobStatus.FAILED])

        # Get costs
        job_ids = [j.job_id for j in jobs]
        costs = db.query(JobCostSummary).filter(JobCostSummary.job_id.in_(job_ids)).all()
        total_cost = sum(float(c.total_cost_usd) for c in costs)
        total_tokens = sum(c.total_tokens for c in costs)

        # Job type breakdown
        job_type_breakdown = {}
        for job in jobs:
            if job.job_type not in job_type_breakdown:
                job_type_breakdown[job.job_type] = {"count": 0, "cost_usd": 0.0}
            job_type_breakdown[job.job_type]["count"] += 1

        for cost in costs:
            job = next((j for j in jobs if j.job_id == cost.job_id), None)
            if job:
                job_type_breakdown[job.job_type]["cost_usd"] += float(cost.total_cost_usd)

        return {
            "team_id": team_id,
            "period": period,
            "summary": {
                "total_jobs": total_jobs,
                "successful_jobs": successful_jobs,
                "failed_jobs": failed_jobs,
                "total_cost_usd": round(total_cost, 2),
                "total_tokens": total_tokens,
                "avg_cost_per_job": round(total_cost / total_jobs, 4) if total_jobs > 0 else 0.0
            },
            "job_types": job_type_breakdown
        }

    return summary.to_dict()


@app.get("/api/teams/{team_id}/jobs")
async def list_team_jobs(
    team_id: str,
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    List jobs for a team.

    Requires: Authorization header with virtual API key
    """
    # Verify authenticated team matches requested team
    if team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access jobs for a different team"
        )

    query = db.query(Job).filter(Job.team_id == team_id)

    if status:
        query = query.filter(Job.status == JobStatus(status))

    jobs = query.order_by(Job.created_at.desc()).limit(limit).offset(offset).all()

    return {
        "team_id": team_id,
        "total": len(jobs),
        "jobs": [job.to_dict() for job in jobs]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,  # Different port from LiteLLM (8002 local, 8000 production)
        reload=True
    )
