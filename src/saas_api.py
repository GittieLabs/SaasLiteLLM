"""
SaaS API Wrapper for LiteLLM
Provides job-based cost tracking abstraction layer
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import httpx
import uuid

from config.settings import settings
from models.job_tracking import (
    Base, Job, LLMCall, JobCostSummary, TeamUsageSummary,
    WebhookRegistration, JobStatus
)

# Create FastAPI app
app = FastAPI(
    title="SaaS LLM API",
    description="Job-based LLM API with cost tracking",
    version="1.0.0"
)

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    messages: List[Dict[str, str]],
    team_id: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Call LiteLLM proxy with team-specific virtual key.
    Returns response with usage and cost data.
    """
    # Get team's virtual API key from LiteLLM
    # For now, using master key - in production, you'd use team-specific keys
    litellm_url = f"http://localhost:{settings.port}/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-3.5-turbo",  # Default model - could be configurable
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
async def create_job(request: JobCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new job for tracking multiple LLM calls.
    Teams use this to start a business operation.
    """
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
    db: Session = Depends(get_db)
):
    """
    Make an LLM call within a job context.
    Automatically tracks costs and associates with job.
    """
    # Get job
    job = db.query(Job).filter(Job.job_id == uuid.UUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update job status to in_progress if pending
    if job.status == JobStatus.PENDING:
        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.utcnow()
        db.commit()

    # Call LiteLLM
    start_time = datetime.utcnow()
    try:
        litellm_response = await call_litellm(
            messages=request.messages,
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

        # Store LLM call record
        llm_call = LLMCall(
            job_id=job.job_id,
            litellm_request_id=litellm_response.get("id"),
            model_used=litellm_response.get("model", "gpt-3.5-turbo"),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            purpose=request.purpose,
            request_data={"messages": request.messages},
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
                "latency_ms": latency_ms
            }
        )

    except Exception as e:
        # Record failed call
        llm_call = LLMCall(
            job_id=job.job_id,
            purpose=request.purpose,
            error=str(e),
            request_data={"messages": request.messages}
        )
        db.add(llm_call)
        db.commit()

        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")


@app.post("/api/jobs/{job_id}/complete", response_model=JobCompleteResponse)
async def complete_job(
    job_id: str,
    request: JobCompleteRequest,
    db: Session = Depends(get_db)
):
    """
    Mark job as complete and return aggregated costs.
    This is when you calculate total cost for the business operation.
    """
    job = db.query(Job).filter(Job.job_id == uuid.UUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update job status
    job.status = JobStatus(request.status)
    job.completed_at = datetime.utcnow()
    if request.error_message:
        job.error_message = request.error_message
    if request.metadata:
        job.job_metadata.update(request.metadata)

    db.commit()

    # Calculate costs
    costs = calculate_job_costs(db, job.job_id)

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
            "tokens": call.total_tokens,
            "latency_ms": call.latency_ms,
            "error": call.error
        }
        for call in calls
    ]

    return JobCompleteResponse(
        job_id=str(job.job_id),
        status=job.status.value,
        completed_at=job.completed_at.isoformat(),
        costs=costs,
        calls=calls_data
    )


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job details"""
    job = db.query(Job).filter(Job.job_id == uuid.UUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job.to_dict()


@app.get("/api/jobs/{job_id}/costs")
async def get_job_costs(job_id: str, db: Session = Depends(get_db)):
    """
    Get detailed cost breakdown for a job.
    This endpoint is for YOUR internal use - not exposed to teams.
    """
    job = db.query(Job).filter(Job.job_id == uuid.UUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

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
    db: Session = Depends(get_db)
):
    """
    Get team usage summary for a period.
    For your internal billing and analytics.
    """
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
    db: Session = Depends(get_db)
):
    """List jobs for a team"""
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
