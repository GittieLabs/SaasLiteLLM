"""
Jobs API endpoints for monitoring and analytics
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from ..models.job_tracking import Job, LLMCall, JobCostSummary, JobStatus, get_db
from ..models.credits import TeamCredits
from ..auth.dependencies import verify_admin_auth
import uuid

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# Response Models
class JobSummary(BaseModel):
    job_id: str
    team_id: str
    user_id: Optional[str]
    job_type: str
    status: str
    created_at: str
    completed_at: Optional[str]
    # Aggregated metrics
    total_calls: int
    successful_calls: int
    failed_calls: int
    retry_count: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: int
    credit_applied: bool
    # First-level metadata
    job_metadata: Optional[Dict[str, Any]]


class LLMCallDetail(BaseModel):
    call_id: str
    model_used: Optional[str]
    model_group_used: Optional[str]
    purpose: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: Optional[int]
    created_at: str
    error: Optional[str]
    request_data: Optional[Dict[str, Any]]
    response_data: Optional[Dict[str, Any]]


class JobDetail(BaseModel):
    job: JobSummary
    calls: List[LLMCallDetail]


class JobListResponse(BaseModel):
    jobs: List[JobSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrganizationJobStats(BaseModel):
    organization_id: str
    organization_name: Optional[str]
    # Aggregated across all teams
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    in_progress_jobs: int
    total_teams: int
    total_llm_calls: int
    successful_calls: int
    failed_calls: int
    total_tokens: int
    total_cost_usd: float
    total_credits_used: int
    # Top teams by usage
    top_teams: List[Dict[str, Any]]


# Endpoints
@router.get("/teams/{team_id}", response_model=JobListResponse)
async def list_team_jobs(
    team_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    job_id_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    List jobs for a team with pagination and filters

    Filters:
    - status: Filter by job status (pending, in_progress, completed, failed)
    - job_type: Filter by job type
    - start_date: ISO format date (e.g., 2024-10-01)
    - end_date: ISO format date (e.g., 2024-10-31)
    - job_id_filter: Partial match on job_id
    """
    # Verify team exists
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == team_id
    ).first()

    if not team_credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )

    # Build query
    query = db.query(Job).filter(Job.team_id == team_id)

    # Apply filters
    if status:
        try:
            # Convert to uppercase for enum matching
            query = query.filter(Job.status == JobStatus(status.upper()))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: pending, in_progress, completed, failed"
            )

    if job_type:
        query = query.filter(Job.job_type == job_type)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Job.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid start_date format: {start_date}. Use ISO format (YYYY-MM-DD)"
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            # Include the entire end date
            end_dt = end_dt + timedelta(days=1)
            query = query.filter(Job.created_at < end_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid end_date format: {end_date}. Use ISO format (YYYY-MM-DD)"
            )

    if job_id_filter:
        # Partial match on job_id
        query = query.filter(Job.job_id.cast(db.bind.dialect.type_descriptor(db.String)).contains(job_id_filter))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(page_size).all()

    # Build response with aggregated metrics (exclude jobs with no LLM calls)
    job_summaries = []
    for job in jobs:
        # Get aggregated call metrics
        calls = db.query(LLMCall).filter(LLMCall.job_id == job.job_id).all()

        total_calls = len(calls)

        # Skip jobs with no LLM calls (orphaned/abandoned jobs)
        if total_calls == 0:
            continue

        successful_calls = len([c for c in calls if not c.error])
        failed_calls = len([c for c in calls if c.error])

        # Count retries (calls after the first one with same purpose)
        purpose_counts = {}
        for call in calls:
            purpose = call.purpose or "default"
            purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1
        retry_count = sum(count - 1 for count in purpose_counts.values() if count > 1)

        total_tokens = sum(c.total_tokens or 0 for c in calls)
        total_cost_usd = sum(float(c.cost_usd) for c in calls)
        latencies = [c.latency_ms for c in calls if c.latency_ms]
        avg_latency_ms = int(sum(latencies) / len(latencies)) if latencies else 0

        job_summaries.append(JobSummary(
            job_id=str(job.job_id),
            team_id=job.team_id,
            user_id=job.user_id,
            job_type=job.job_type,
            status=job.status.value,
            created_at=job.created_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            retry_count=retry_count,
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost_usd, 6),
            avg_latency_ms=avg_latency_ms,
            credit_applied=job.credit_applied,
            job_metadata=job.job_metadata
        ))

    total_pages = (total + page_size - 1) // page_size

    return JobListResponse(
        jobs=job_summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/teams/{team_id}/{job_id}", response_model=JobDetail)
async def get_job_detail(
    team_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Get detailed information about a specific job including all LLM calls
    """
    # Get job
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job_id format: {job_id}"
        )

    job = db.query(Job).filter(
        and_(Job.job_id == job_uuid, Job.team_id == team_id)
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found for team '{team_id}'"
        )

    # Get all calls for this job
    calls = db.query(LLMCall).filter(
        LLMCall.job_id == job_uuid
    ).order_by(LLMCall.created_at).all()

    # Build job summary
    total_calls = len(calls)
    successful_calls = len([c for c in calls if not c.error])
    failed_calls = len([c for c in calls if c.error])

    purpose_counts = {}
    for call in calls:
        purpose = call.purpose or "default"
        purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1
    retry_count = sum(count - 1 for count in purpose_counts.values() if count > 1)

    total_tokens = sum(c.total_tokens or 0 for c in calls)
    total_cost_usd = sum(float(c.cost_usd) for c in calls)
    latencies = [c.latency_ms for c in calls if c.latency_ms]
    avg_latency_ms = int(sum(latencies) / len(latencies)) if latencies else 0

    job_summary = JobSummary(
        job_id=str(job.job_id),
        team_id=job.team_id,
        user_id=job.user_id,
        job_type=job.job_type,
        status=job.status.value,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        total_calls=total_calls,
        successful_calls=successful_calls,
        failed_calls=failed_calls,
        retry_count=retry_count,
        total_tokens=total_tokens,
        total_cost_usd=round(total_cost_usd, 6),
        avg_latency_ms=avg_latency_ms,
        credit_applied=job.credit_applied,
        job_metadata=job.job_metadata
    )

    # Build call details
    call_details = []
    for call in calls:
        call_details.append(LLMCallDetail(
            call_id=str(call.call_id),
            model_used=call.model_used,
            model_group_used=call.model_group_used,
            purpose=call.purpose,
            prompt_tokens=call.prompt_tokens or 0,
            completion_tokens=call.completion_tokens or 0,
            total_tokens=call.total_tokens or 0,
            cost_usd=round(float(call.cost_usd), 6),
            latency_ms=call.latency_ms,
            created_at=call.created_at.isoformat(),
            error=call.error,
            request_data=call.request_data,
            response_data=call.response_data
        ))

    return JobDetail(
        job=job_summary,
        calls=call_details
    )


@router.get("/organizations/{organization_id}/stats", response_model=OrganizationJobStats)
async def get_organization_job_stats(
    organization_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Get aggregated job statistics for an entire organization

    Provides a high-level overview of all jobs across all teams in an organization
    """
    # Verify organization exists
    from ..models.organizations import Organization
    org = db.query(Organization).filter(
        Organization.organization_id == organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Organization '{organization_id}' not found"
        )

    # Get all teams in organization
    teams = db.query(TeamCredits).filter(
        TeamCredits.organization_id == organization_id
    ).all()

    team_ids = [t.team_id for t in teams]

    if not team_ids:
        # No teams in organization
        return OrganizationJobStats(
            organization_id=organization_id,
            organization_name=org.name,
            total_jobs=0,
            completed_jobs=0,
            failed_jobs=0,
            in_progress_jobs=0,
            total_teams=0,
            total_llm_calls=0,
            successful_calls=0,
            failed_calls=0,
            total_tokens=0,
            total_cost_usd=0.0,
            total_credits_used=0,
            top_teams=[]
        )

    # Build job query for all teams
    job_query = db.query(Job).filter(Job.team_id.in_(team_ids))

    # Apply date filters
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            job_query = job_query.filter(Job.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid start_date format: {start_date}"
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
            job_query = job_query.filter(Job.created_at < end_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid end_date format: {end_date}"
            )

    # Get all jobs
    jobs = job_query.all()
    job_ids = [j.job_id for j in jobs]

    # Aggregate job stats
    total_jobs = len(jobs)
    completed_jobs = len([j for j in jobs if j.status == JobStatus.COMPLETED])
    failed_jobs = len([j for j in jobs if j.status == JobStatus.FAILED])
    in_progress_jobs = len([j for j in jobs if j.status == JobStatus.IN_PROGRESS])

    # Get all LLM calls for these jobs
    if job_ids:
        calls = db.query(LLMCall).filter(LLMCall.job_id.in_(job_ids)).all()
    else:
        calls = []

    total_llm_calls = len(calls)
    successful_calls = len([c for c in calls if not c.error])
    failed_calls = len([c for c in calls if c.error])
    total_tokens = sum(c.total_tokens or 0 for c in calls)
    total_cost_usd = sum(float(c.cost_usd) for c in calls)

    # Calculate total credits used
    total_credits_used = sum(t.credits_used for t in teams)

    # Get top teams by job count
    team_job_counts = {}
    for job in jobs:
        team_job_counts[job.team_id] = team_job_counts.get(job.team_id, 0) + 1

    top_teams = sorted(
        [
            {
                "team_id": team_id,
                "job_count": count,
                "credits_used": next((t.credits_used for t in teams if t.team_id == team_id), 0)
            }
            for team_id, count in team_job_counts.items()
        ],
        key=lambda x: x["job_count"],
        reverse=True
    )[:10]  # Top 10 teams

    return OrganizationJobStats(
        organization_id=organization_id,
        organization_name=org.name,
        total_jobs=total_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        in_progress_jobs=in_progress_jobs,
        total_teams=len(teams),
        total_llm_calls=total_llm_calls,
        successful_calls=successful_calls,
        failed_calls=failed_calls,
        total_tokens=total_tokens,
        total_cost_usd=round(total_cost_usd, 6),
        total_credits_used=total_credits_used,
        top_teams=top_teams
    )


class OrganizationAnalytics(BaseModel):
    organization_id: str
    organization_name: Optional[str]
    # Summary stats
    total_spend: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    # Daily spend breakdown
    daily_spend: List[Dict[str, Any]]  # [{date: "2024-10-20", spend: 0.005}]
    # Spend per team (top 10)
    spend_per_team: List[Dict[str, Any]]  # [{team_id: "...", spend: 0.005, successful: 3, failed: 0, tokens: 60}]
    # Top models by spend
    top_models: List[Dict[str, Any]]  # [{model: "gpt-4", spend: 0.005, count: 10}]
    # Provider usage breakdown
    provider_usage: List[Dict[str, Any]]  # [{provider: "openai", spend: 0.005, successful: 3, failed: 0, tokens: 60}]


@router.get("/organizations/{organization_id}/analytics", response_model=OrganizationAnalytics)
async def get_organization_analytics(
    organization_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _ = Depends(verify_admin_auth)
):
    """
    Get comprehensive analytics for an organization including:
    - Daily spend breakdown
    - Spend per team
    - Top models by spend
    - Provider usage breakdown
    """
    # Verify organization exists
    from ..models.organizations import Organization
    org = db.query(Organization).filter(
        Organization.organization_id == organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Organization '{organization_id}' not found"
        )

    # Get all teams in organization
    teams = db.query(TeamCredits).filter(
        TeamCredits.organization_id == organization_id
    ).all()

    team_ids = [t.team_id for t in teams]

    if not team_ids:
        # No teams in organization - return empty analytics
        return OrganizationAnalytics(
            organization_id=organization_id,
            organization_name=org.name,
            total_spend=0.0,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            total_tokens=0,
            daily_spend=[],
            spend_per_team=[],
            top_models=[],
            provider_usage=[]
        )

    # Build job query for all teams
    job_query = db.query(Job).filter(Job.team_id.in_(team_ids))

    # Apply date filters
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            job_query = job_query.filter(Job.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid start_date format: {start_date}"
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
            job_query = job_query.filter(Job.created_at < end_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid end_date format: {end_date}"
            )

    # Get all jobs
    jobs = job_query.all()
    job_ids = [j.job_id for j in jobs]

    # Get all LLM calls for these jobs
    if job_ids:
        calls = db.query(LLMCall).filter(LLMCall.job_id.in_(job_ids)).all()
    else:
        calls = []

    # Summary stats
    total_requests = len(calls)
    successful_requests = len([c for c in calls if not c.error])
    failed_requests = len([c for c in calls if c.error])
    total_tokens = sum(c.total_tokens or 0 for c in calls)
    total_spend = sum(float(c.cost_usd) for c in calls)

    # Daily spend breakdown
    daily_spend_map = {}
    for call in calls:
        date_str = call.created_at.date().isoformat()
        if date_str not in daily_spend_map:
            daily_spend_map[date_str] = 0.0
        daily_spend_map[date_str] += float(call.cost_usd)

    daily_spend = [
        {"date": date, "spend": round(spend, 6)}
        for date, spend in sorted(daily_spend_map.items())
    ]

    # Spend per team (aggregate by team_id from jobs)
    team_spend_map = {}
    for job in jobs:
        team_id = job.team_id
        if team_id not in team_spend_map:
            team_spend_map[team_id] = {
                "spend": 0.0,
                "successful": 0,
                "failed": 0,
                "tokens": 0
            }

        # Get calls for this job
        job_calls = [c for c in calls if c.job_id == job.job_id]
        for call in job_calls:
            team_spend_map[team_id]["spend"] += float(call.cost_usd)
            team_spend_map[team_id]["tokens"] += call.total_tokens or 0
            if call.error:
                team_spend_map[team_id]["failed"] += 1
            else:
                team_spend_map[team_id]["successful"] += 1

    spend_per_team = sorted(
        [
            {
                "team_id": team_id,
                "spend": round(data["spend"], 6),
                "successful": data["successful"],
                "failed": data["failed"],
                "tokens": data["tokens"]
            }
            for team_id, data in team_spend_map.items()
        ],
        key=lambda x: x["spend"],
        reverse=True
    )[:10]  # Top 10 teams

    # Top models by spend
    model_spend_map = {}
    for call in calls:
        model = call.model_used or "unknown"
        if model not in model_spend_map:
            model_spend_map[model] = {"spend": 0.0, "count": 0}
        model_spend_map[model]["spend"] += float(call.cost_usd)
        model_spend_map[model]["count"] += 1

    top_models = sorted(
        [
            {
                "model": model,
                "spend": round(data["spend"], 6),
                "count": data["count"]
            }
            for model, data in model_spend_map.items()
        ],
        key=lambda x: x["spend"],
        reverse=True
    )[:10]  # Top 10 models

    # Provider usage breakdown (extract provider from model name)
    def extract_provider(model_name):
        if not model_name:
            return "unknown"
        model_lower = model_name.lower()
        if "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower or "google" in model_lower:
            return "google"
        elif "llama" in model_lower or "meta" in model_lower:
            return "meta"
        else:
            return "other"

    provider_spend_map = {}
    for call in calls:
        provider = extract_provider(call.model_used)
        if provider not in provider_spend_map:
            provider_spend_map[provider] = {
                "spend": 0.0,
                "successful": 0,
                "failed": 0,
                "tokens": 0
            }
        provider_spend_map[provider]["spend"] += float(call.cost_usd)
        provider_spend_map[provider]["tokens"] += call.total_tokens or 0
        if call.error:
            provider_spend_map[provider]["failed"] += 1
        else:
            provider_spend_map[provider]["successful"] += 1

    provider_usage = sorted(
        [
            {
                "provider": provider,
                "spend": round(data["spend"], 6),
                "successful": data["successful"],
                "failed": data["failed"],
                "tokens": data["tokens"]
            }
            for provider, data in provider_spend_map.items()
        ],
        key=lambda x: x["spend"],
        reverse=True
    )

    return OrganizationAnalytics(
        organization_id=organization_id,
        organization_name=org.name,
        total_spend=round(total_spend, 6),
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        total_tokens=total_tokens,
        daily_spend=daily_spend,
        spend_per_team=spend_per_team,
        top_models=top_models,
        provider_usage=provider_usage
    )
