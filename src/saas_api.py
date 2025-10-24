"""
SaaS API Wrapper for LiteLLM
Provides job-based cost tracking abstraction layer
Force rebuild: 2025-10-24 21:17
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
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
from .api.constants import (
    DEFAULT_TOKENS_PER_CREDIT,
    DEFAULT_CREDITS_PER_DOLLAR,
    MINIMUM_CREDITS_PER_JOB
)
from .utils.cost_calculator import (
    calculate_token_costs,
    apply_markup,
    get_model_pricing
)

# Import new API routers
from .api import organizations, model_groups, teams, credits, dashboard, models, model_access_groups, admin_users, jobs, provider_credentials

# Import authentication
from .auth.dependencies import verify_virtual_key

# Create FastAPI app
app = FastAPI(
    title="SaaS LLM API",
    description="Job-based LLM API with cost tracking and model group management",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3002",  # Admin panel (development)
        "http://localhost:3001",  # Backup admin panel port
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3001",
        "https://saaslitellm-admin.usegittie.com",  # Production admin panel
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include new routers
app.include_router(admin_users.router)
app.include_router(organizations.router)
app.include_router(model_groups.router)
app.include_router(teams.router)
app.include_router(credits.router)
app.include_router(dashboard.router)
app.include_router(models.router)
app.include_router(model_access_groups.router)
app.include_router(jobs.router)
app.include_router(provider_credentials.router)

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@app.on_event("startup")
async def startup_event():
    """Ensure database tables exist on startup"""
    # Import all models to ensure they're registered with Base
    from .models import organizations, model_groups, credits, admin_users

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
    model: str  # Model alias (e.g., "gpa-rag-chat") or model group (e.g., "ResumeAgent")
    messages: List[Dict[str, Any]]  # Changed to Any to support all message types
    purpose: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    # Support for structured outputs and function calling
    response_format: Optional[Dict[str, Any]] = None  # {"type": "json_object"} or JSON schema
    tools: Optional[List[Dict[str, Any]]] = None  # Function calling tools
    tool_choice: Optional[Any] = None  # "auto", "none", or specific tool
    # Additional OpenAI parameters
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None
    # Call-specific metadata to append to job metadata
    call_metadata: Optional[Dict[str, Any]] = None


class LLMCallResponse(BaseModel):
    call_id: str
    response: Dict[str, Any]
    metadata: Dict[str, Any]


class JobCompleteRequest(BaseModel):
    status: Literal["completed", "failed"]  # Only these two values are valid
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    error_message: Optional[str] = None


class JobMetadataUpdateRequest(BaseModel):
    """Request model for appending metadata to a job"""
    metadata: Dict[str, Any]


class JobCompleteResponse(BaseModel):
    job_id: str
    status: str
    completed_at: str
    costs: Dict[str, Any]
    calls: List[Dict[str, Any]]


class SingleCallJobRequest(BaseModel):
    """
    Request model for single-call job endpoint.
    Combines job creation, LLM call, and completion in one request.
    """
    team_id: str
    job_type: str
    model: str  # Model alias or model group
    messages: List[Dict[str, Any]]
    # Optional job metadata
    user_id: Optional[str] = None
    job_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # Optional LLM parameters
    purpose: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    response_format: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None


class SingleCallJobResponse(BaseModel):
    """
    Response model for single-call job endpoint.
    Returns both the LLM response and job completion data.
    """
    job_id: str
    status: str
    response: Dict[str, Any]  # LLM response content
    metadata: Dict[str, Any]  # Includes tokens, latency, model info
    costs: Dict[str, Any]  # Job cost summary
    completed_at: str


# Helper Functions
async def call_litellm(
    model: str,
    messages: List[Dict[str, Any]],
    virtual_key: Optional[str],
    team_id: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict[str, Any]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[Any] = None,
    top_p: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    presence_penalty: Optional[float] = None,
    stop: Optional[List[str]] = None,
    stream: bool = False,
    db: Optional[Session] = None,
    organization_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Call LLM provider - routes to direct provider API if credentials exist, otherwise uses LiteLLM proxy.

    This function intelligently routes requests:
    1. If organization_id provided and provider credentials exist → Direct provider API
    2. Otherwise → LiteLLM proxy (backward compatible)

    Returns response with usage and cost data.
    Supports all OpenAI parameters including structured outputs and function calling.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Try direct provider routing if we have DB access and organization_id
    if db is not None and organization_id is not None:
        try:
            from .services.direct_provider_service import get_direct_provider_service
            from .models.model_aliases import ModelAlias

            direct_service = get_direct_provider_service()

            # Check if model is an alias and resolve it
            actual_model = model
            provider = None

            model_alias_record = db.query(ModelAlias).filter(
                ModelAlias.model_alias == model,
                ModelAlias.status == "active"
            ).first()

            if model_alias_record:
                # Use the actual model and provider from the alias
                actual_model = model_alias_record.actual_model
                provider = model_alias_record.provider
                logger.info(f"Resolved model alias '{model}' -> '{actual_model}' (provider: {provider})")
            else:
                # Not an alias, detect provider from model name pattern
                provider = direct_service.detect_provider_from_model(model)

            # Try to get provider credentials
            credential_result = await direct_service.get_provider_credential(
                db=db,
                organization_id=organization_id,
                provider=provider
            )

            if credential_result:
                api_key, provider_name = credential_result
                logger.info(f"Routing to direct {provider_name} API for model {actual_model}")

                # Route to direct provider
                if stream:
                    # For streaming, return the httpx.Response object
                    return await direct_service.chat_completion_stream(
                        provider=provider_name,
                        api_key=api_key,
                        model=actual_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format=response_format,
                        tools=tools,
                        tool_choice=tool_choice,
                        top_p=top_p,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty,
                        stop=stop
                    )
                else:
                    # For non-streaming, return the dict response
                    return await direct_service.chat_completion(
                        provider=provider_name,
                        api_key=api_key,
                        model=actual_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format=response_format,
                        tools=tools,
                        tool_choice=tool_choice,
                        top_p=top_p,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty,
                        stop=stop
                    )
            else:
                logger.debug(f"No provider credentials found for {provider}, falling back to LiteLLM proxy")

        except Exception as e:
            logger.warning(f"Direct provider routing failed: {str(e)}, falling back to LiteLLM proxy")

    # Fall back to LiteLLM proxy (backward compatible)
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

    # Add optional parameters if provided
    if max_tokens:
        payload["max_tokens"] = max_tokens
    if response_format:
        payload["response_format"] = response_format
    if tools:
        payload["tools"] = tools
    if tool_choice:
        payload["tool_choice"] = tool_choice
    if top_p:
        payload["top_p"] = top_p
    if frequency_penalty:
        payload["frequency_penalty"] = frequency_penalty
    if presence_penalty:
        payload["presence_penalty"] = presence_penalty
    if stop:
        payload["stop"] = stop
    if stream:
        payload["stream"] = stream

    async with httpx.AsyncClient() as client:
        if stream:
            return await client.post(litellm_url, json=payload, headers=headers, timeout=120.0)
        else:
            response = await client.post(litellm_url, json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()
            return response.json()


def calculate_complete_costs(
    resolved_model: str,
    prompt_tokens: int,
    completion_tokens: int,
    markup_percentage: float
) -> Dict[str, Any]:
    """
    Calculate complete cost breakdown with pricing and markup.

    Returns dict with:
    - model_pricing_input: Input price per 1M tokens
    - model_pricing_output: Output price per 1M tokens
    - input_cost_usd: Cost for input tokens
    - output_cost_usd: Cost for output tokens
    - provider_cost_usd: Total provider cost
    - client_cost_usd: Provider cost with markup applied
    """
    # Get pricing for the resolved model (not the alias!)
    pricing = get_model_pricing(resolved_model)

    # Calculate token costs
    costs = calculate_token_costs(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        input_price_per_million=pricing["input"],
        output_price_per_million=pricing["output"]
    )

    # Apply markup
    markup_costs = apply_markup(
        provider_cost_usd=costs["provider_cost_usd"],
        markup_percentage=markup_percentage
    )

    # Return complete breakdown
    return {
        "model_pricing_input": pricing["input"],
        "model_pricing_output": pricing["output"],
        "input_cost_usd": costs["input_cost_usd"],
        "output_cost_usd": costs["output_cost_usd"],
        "provider_cost_usd": markup_costs["provider_cost_usd"],
        "client_cost_usd": markup_costs["client_cost_usd"]
    }


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
    # Use client_cost_usd (with markup) instead of legacy cost_usd
    total_cost_usd = sum(float(c.client_cost_usd) if c.client_cost_usd else 0.0 for c in calls)
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


@app.post("/api/jobs/create", response_model=JobCreateResponse, tags=["jobs"])
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


@app.post("/api/jobs/{job_id}/llm-call", response_model=LLMCallResponse, tags=["jobs"])
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
            model_group_name=request.model
        )
    except ModelResolutionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Track this model group usage (add to list if not already there)
    if not job.model_groups_used:
        job.model_groups_used = []
    if request.model not in job.model_groups_used:
        job.model_groups_used.append(request.model)
        db.commit()

    # Call LiteLLM with resolved model
    start_time = datetime.utcnow()
    try:
        litellm_response = await call_litellm(
            model=primary_model,
            messages=request.messages,
            virtual_key=getattr(team_credits, 'virtual_key', None),
            team_id=job.team_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
            tools=request.tools,
            tool_choice=request.tool_choice,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop=request.stop,
            db=db,
            organization_id=team_credits.organization_id
        )

        end_time = datetime.utcnow()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        # Extract usage and cost data
        usage = litellm_response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # Get resolved model from LiteLLM response (the ACTUAL model used, not the alias)
        resolved_model = litellm_response.get("model", primary_model)

        # Calculate complete costs with pricing and markup
        markup_percentage = float(team_credits.cost_markup_percentage) if team_credits.cost_markup_percentage else 0.0
        complete_costs = calculate_complete_costs(
            resolved_model=resolved_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            markup_percentage=markup_percentage
        )

        # Store LLM call record with complete cost tracking
        llm_call = LLMCall(
            job_id=job.job_id,
            litellm_request_id=litellm_response.get("id"),
            model_used=primary_model,
            model_group_used=request.model,
            resolved_model=resolved_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=complete_costs["provider_cost_usd"],  # Legacy field
            input_cost_usd=complete_costs["input_cost_usd"],
            output_cost_usd=complete_costs["output_cost_usd"],
            provider_cost_usd=complete_costs["provider_cost_usd"],
            client_cost_usd=complete_costs["client_cost_usd"],
            model_pricing_input=complete_costs["model_pricing_input"],
            model_pricing_output=complete_costs["model_pricing_output"],
            latency_ms=latency_ms,
            purpose=request.purpose,
            request_data={"messages": request.messages, "model": request.model},
            response_data=litellm_response
        )

        db.add(llm_call)
        db.commit()
        db.refresh(llm_call)

        # Append call-specific metadata to job metadata if provided
        if request.call_metadata:
            if job.job_metadata is None:
                job.job_metadata = {}

            job.job_metadata.update(request.call_metadata)

            # Mark the attribute as modified for SQLAlchemy to detect the change
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(job, 'job_metadata')
            db.commit()

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
                "model": request.model
            }
        )

    except Exception as e:
        # Record failed call
        llm_call = LLMCall(
            job_id=job.job_id,
            model_group_used=request.model,
            purpose=request.purpose,
            error=str(e),
            request_data={"messages": request.messages, "model": request.model}
        )
        db.add(llm_call)
        db.commit()

        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")


@app.post("/api/jobs/{job_id}/llm-call-stream", tags=["jobs"])
async def make_llm_call_stream(
    job_id: str,
    request: LLMCallRequest,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Make a streaming LLM call within a job context using Server-Sent Events (SSE).

    Supports:
    - Real-time text streaming
    - Structured output streaming (response_format)
    - Function calling streaming (tools)
    - All OpenAI parameters

    The stream forwards directly from LiteLLM to minimize latency.

    Requires: Authorization header with virtual API key
    """
    from fastapi.responses import StreamingResponse
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

    # Get team credentials
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == job.team_id
    ).first()

    if not team_credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{job.team_id}' not found"
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
            model_group_name=request.model
        )
    except ModelResolutionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Track model group usage
    if not job.model_groups_used:
        job.model_groups_used = []
    if request.model not in job.model_groups_used:
        job.model_groups_used.append(request.model)
        db.commit()

    # Capture virtual_key and team_id before generator to avoid DetachedInstanceError
    virtual_key_value = getattr(team_credits, 'virtual_key', None)
    team_id_value = job.team_id

    # Create streaming generator
    async def stream_llm_response():
        litellm_url = f"{settings.litellm_proxy_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {virtual_key_value}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": primary_model,
            "messages": request.messages,
            "temperature": request.temperature,
            "stream": True,  # Enable streaming
            "user": team_id_value,
        }

        # Add optional parameters
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.response_format:
            payload["response_format"] = request.response_format
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.top_p:
            payload["top_p"] = request.top_p
        if request.frequency_penalty:
            payload["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty:
            payload["presence_penalty"] = request.presence_penalty
        if request.stop:
            payload["stop"] = request.stop

        # Track accumulated response for database storage
        accumulated_content = ""
        accumulated_tokens = {"prompt": 0, "completion": 0, "total": 0}
        litellm_request_id = None
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream('POST', litellm_url, json=payload, headers=headers, timeout=120.0) as response:
                    response.raise_for_status()

                    # Stream chunks to client
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk_data = line[6:]  # Remove "data: " prefix

                            if chunk_data == "[DONE]":
                                yield f"data: [DONE]\n\n"
                                break

                            try:
                                import json
                                chunk_json = json.loads(chunk_data)

                                # Extract request ID from first chunk
                                if litellm_request_id is None:
                                    litellm_request_id = chunk_json.get("id")

                                # Accumulate content
                                if "choices" in chunk_json:
                                    for choice in chunk_json["choices"]:
                                        # Text content
                                        if "delta" in choice and "content" in choice["delta"]:
                                            accumulated_content += choice["delta"]["content"]

                                # Extract usage if present (usually in last chunk)
                                if "usage" in chunk_json:
                                    accumulated_tokens = {
                                        "prompt": chunk_json["usage"].get("prompt_tokens", 0),
                                        "completion": chunk_json["usage"].get("completion_tokens", 0),
                                        "total": chunk_json["usage"].get("total_tokens", 0)
                                    }

                                # Stream to client immediately (no buffering)
                                yield f"data: {chunk_data}\n\n"

                            except json.JSONDecodeError:
                                continue

            # After streaming completes, store in database
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            # Calculate cost (fallback to model pricing if not provided)
            cost_usd = 0.0
            from .models.model_aliases import ModelAlias
            model_record = db.query(ModelAlias).filter(
                ModelAlias.model_alias == primary_model
            ).first()

            if model_record and model_record.pricing_input and model_record.pricing_output:
                cost_usd = (
                    (accumulated_tokens["prompt"] * float(model_record.pricing_input) / 1_000_000) +
                    (accumulated_tokens["completion"] * float(model_record.pricing_output) / 1_000_000)
                )

            # Store LLM call record
            llm_call = LLMCall(
                job_id=job.job_id,
                litellm_request_id=litellm_request_id,
                model_used=primary_model,
                model_group_used=request.model,
                resolved_model=primary_model,  # For streaming, we don't get actual model in response
                prompt_tokens=accumulated_tokens["prompt"],
                completion_tokens=accumulated_tokens["completion"],
                total_tokens=accumulated_tokens["total"],
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                purpose=request.purpose,
                request_data={"messages": request.messages, "model": request.model},
                response_data={"content": accumulated_content, "streaming": True}
            )

            db.add(llm_call)
            db.commit()

        except Exception as e:
            # Record failed call
            llm_call = LLMCall(
                job_id=job.job_id,
                model_group_used=request.model,
                purpose=request.purpose,
                error=str(e),
                request_data={"messages": request.messages, "model": request.model}
            )
            db.add(llm_call)
            db.commit()

            # Send error to client
            import json
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_llm_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.post("/api/jobs/create-and-call", response_model=SingleCallJobResponse, tags=["jobs"])
async def create_and_call_job(
    request: SingleCallJobRequest,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Single-call job endpoint: Creates job, makes LLM call, and completes job in one request.

    This is a convenience endpoint for scenarios where you only need to make a single LLM call.
    It reduces latency by ~66% compared to the 3-step process (create → call → complete).

    Perfect for:
    - Chat applications with single-turn responses
    - Simple text generation tasks
    - Any workflow that only requires one LLM call per job

    For multi-call scenarios (e.g., complex agents), use the separate endpoints.

    Requires: Authorization header with virtual API key
    """
    from .models.credits import TeamCredits
    from .services.model_resolver import ModelResolver, ModelResolutionError
    from .services.credit_manager import get_credit_manager, InsufficientCreditsError

    # Verify that the authenticated team matches the request
    if request.team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail=f"API key does not belong to team '{request.team_id}'"
        )

    # Get team credits and virtual key
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == request.team_id
    ).first()

    if not team_credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{request.team_id}' not found"
        )

    # Step 1: Create job
    job = Job(
        team_id=request.team_id,
        user_id=request.user_id,
        job_type=request.job_type,
        status=JobStatus.IN_PROGRESS,  # Start in progress
        job_metadata=request.job_metadata,
        started_at=datetime.utcnow()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Step 2: Resolve model and make LLM call
    model_resolver = ModelResolver(db)

    try:
        primary_model, fallback_models = model_resolver.resolve_model_group(
            team_id=job.team_id,
            model_group_name=request.model
        )
    except ModelResolutionError as e:
        # Mark job as failed before raising
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=403, detail=str(e))

    # Track model group usage
    job.model_groups_used = [request.model]
    db.commit()

    # Call LiteLLM
    start_time = datetime.utcnow()
    llm_call_successful = False
    llm_response_content = None
    total_tokens = 0
    latency_ms = 0

    try:
        litellm_response = await call_litellm(
            model=primary_model,
            messages=request.messages,
            virtual_key=getattr(team_credits, 'virtual_key', None),
            team_id=job.team_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
            tools=request.tools,
            tool_choice=request.tool_choice,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop=request.stop,
            db=db,
            organization_id=team_credits.organization_id
        )

        end_time = datetime.utcnow()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        # Extract usage and cost data
        usage = litellm_response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # Extract cost
        cost_usd = 0.0
        if "_hidden_params" in litellm_response:
            cost_usd = litellm_response["_hidden_params"].get("response_cost", 0.0)
        if not cost_usd and "cost" in usage:
            cost_usd = usage.get("cost", 0.0)

        # Fallback to database pricing
        if not cost_usd:
            from .models.model_aliases import ModelAlias
            model_record = db.query(ModelAlias).filter(
                ModelAlias.model_alias == primary_model
            ).first()

            if model_record and model_record.pricing_input and model_record.pricing_output:
                cost_usd = (
                    (prompt_tokens * float(model_record.pricing_input) / 1_000_000) +
                    (completion_tokens * float(model_record.pricing_output) / 1_000_000)
                )

        # Store LLM call record
        llm_call = LLMCall(
            job_id=job.job_id,
            litellm_request_id=litellm_response.get("id"),
            model_used=primary_model,
            model_group_used=request.model,
            resolved_model=litellm_response.get("model", primary_model),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            purpose=request.purpose,
            request_data={"messages": request.messages, "model": request.model},
            response_data=litellm_response
        )

        db.add(llm_call)
        db.commit()

        llm_call_successful = True
        llm_response_content = {
            "content": litellm_response["choices"][0]["message"]["content"],
            "finish_reason": litellm_response["choices"][0]["finish_reason"]
        }

    except Exception as e:
        # Record failed call
        llm_call = LLMCall(
            job_id=job.job_id,
            model_group_used=request.model,
            purpose=request.purpose,
            error=str(e),
            request_data={"messages": request.messages, "model": request.model}
        )
        db.add(llm_call)
        db.commit()

        # Mark job as failed
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = str(e)
        db.commit()

        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    # Step 3: Complete job and deduct credits
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.utcnow()

    # Calculate costs
    costs = calculate_job_costs(db, job.job_id)

    # Credit deduction (same logic as complete_job endpoint)
    credit_manager = get_credit_manager(db)

    if llm_call_successful and not job.credit_applied and team_credits:
        try:
            # Calculate credits to deduct based on budget mode
            credits_to_deduct = MINIMUM_CREDITS_PER_JOB

            if team_credits.budget_mode == "consumption_usd":
                credits_per_dollar = float(team_credits.credits_per_dollar) if team_credits.credits_per_dollar else DEFAULT_CREDITS_PER_DOLLAR
                credits_to_deduct = int(costs["total_cost_usd"] * credits_per_dollar)
                credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, credits_to_deduct)
            elif team_credits.budget_mode == "consumption_tokens":
                # Use team-specific tokens_per_credit if available, otherwise use default
                tokens_per_credit = team_credits.tokens_per_credit if team_credits.tokens_per_credit else DEFAULT_TOKENS_PER_CREDIT
                credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, costs["total_tokens"] // tokens_per_credit)

            credit_manager.deduct_credit(
                team_id=job.team_id,
                job_id=job.job_id,
                credits_amount=credits_to_deduct,
                reason=f"Single-call job {job.job_type} completed ({team_credits.budget_mode} mode: {credits_to_deduct} credits)"
            )
            job.credit_applied = True

        except InsufficientCreditsError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Job {job.job_id} completed but couldn't deduct credit: {str(e)}")

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
        total_duration_seconds=int((job.completed_at - job.created_at).total_seconds())
    )
    db.merge(cost_summary)
    db.commit()

    # Refresh team credits to get updated balance
    db.refresh(team_credits)

    # Add credit information to costs
    costs["credit_applied"] = job.credit_applied
    costs["credits_remaining"] = team_credits.credits_remaining if team_credits else None

    return SingleCallJobResponse(
        job_id=str(job.job_id),
        status=job.status.value,
        response=llm_response_content,
        metadata={
            "tokens_used": total_tokens,
            "latency_ms": latency_ms,
            "model": request.model
        },
        costs=costs,
        completed_at=job.completed_at.isoformat()
    )


@app.post("/api/jobs/create-and-call-stream", tags=["jobs"])
async def create_and_call_job_stream(
    request: SingleCallJobRequest,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Single-call streaming job endpoint: Creates job, streams LLM call, and completes job.

    Perfect for chat applications that need real-time token streaming.

    This endpoint:
    1. Creates a job
    2. Streams the LLM response via Server-Sent Events (SSE)
    3. Automatically completes the job and deducts credits after streaming finishes

    Returns: Server-Sent Events stream with LLM response chunks

    Requires: Authorization header with virtual API key
    """
    from fastapi.responses import StreamingResponse
    from .models.credits import TeamCredits
    from .services.model_resolver import ModelResolver, ModelResolutionError
    from .services.credit_manager import get_credit_manager, InsufficientCreditsError

    # Verify that the authenticated team matches the request
    if request.team_id != authenticated_team_id:
        raise HTTPException(
            status_code=403,
            detail=f"API key does not belong to team '{request.team_id}'"
        )

    # Get team credits and virtual key
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == request.team_id
    ).first()

    if not team_credits:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{request.team_id}' not found"
        )

    # Step 1: Create job
    job = Job(
        team_id=request.team_id,
        user_id=request.user_id,
        job_type=request.job_type,
        status=JobStatus.IN_PROGRESS,
        job_metadata=request.job_metadata,
        started_at=datetime.utcnow()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Capture values before generator to avoid DetachedInstanceError
    job_id_value = job.job_id
    team_id_value = job.team_id
    virtual_key_value = getattr(team_credits, 'virtual_key', None)
    organization_id_value = team_credits.organization_id
    budget_mode = team_credits.budget_mode
    credits_per_dollar = team_credits.credits_per_dollar
    tokens_per_credit = team_credits.tokens_per_credit

    # Step 2: Resolve model
    model_resolver = ModelResolver(db)

    try:
        primary_model, fallback_models = model_resolver.resolve_model_group(
            team_id=job.team_id,
            model_group_name=request.model
        )
    except ModelResolutionError as e:
        # Mark job as failed before raising
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=403, detail=str(e))

    # Track model group usage
    job.model_groups_used = [request.model]
    db.commit()

    # Create streaming generator
    async def stream_and_complete():
        import logging
        logger = logging.getLogger(__name__)

        # Send immediate keepalive to establish connection
        yield ": keepalive\n\n"

        # Track accumulated response for database storage
        accumulated_content = ""
        accumulated_tokens = {"prompt": 0, "completion": 0, "total": 0}
        litellm_request_id = None
        start_time = datetime.utcnow()
        llm_call_successful = False

        # Log stream start
        logger.info(f"[STREAM-START] job_id={job_id_value}, model={primary_model}, org={organization_id_value}")
        logger.info(f"[STREAM-START] Has org_id: {organization_id_value is not None}, Has virtual_key: {virtual_key_value is not None}")

        try:
            # Use call_litellm with streaming - this routes through direct provider service
            stream_response = await call_litellm(
                model=primary_model,
                messages=request.messages,
                virtual_key=virtual_key_value,
                team_id=team_id_value,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_format,
                tools=request.tools,
                tool_choice=request.tool_choice,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop=request.stop,
                stream=True,
                db=db,
                organization_id=organization_id_value
            )

            # Log stream response received
            logger.info(f"[STREAM-RESPONSE] Received stream_response, type={type(stream_response).__name__}")
            logger.info(f"[STREAM-RESPONSE] Status will be checked on context enter")

            # Stream response is an httpx.Response object - iterate over it
            chunk_counter = 0
            async with stream_response:
                stream_response.raise_for_status()
                logger.info(f"[STREAM-RESPONSE] Status code: {stream_response.status_code}, Headers: {dict(stream_response.headers)}")

                # Stream chunks to client
                async for line in stream_response.aiter_lines():
                    chunk_counter += 1
                    if line.startswith("data: "):
                        chunk_data = line[6:]  # Remove "data: " prefix

                        if chunk_data == "[DONE]":
                            yield f"data: [DONE]\n\n"
                            break

                        try:
                            import json
                            chunk_json = json.loads(chunk_data)

                            # Extract request ID from first chunk
                            if litellm_request_id is None:
                                litellm_request_id = chunk_json.get("id")
                                logger.info(f"[STREAM-CHUNK-1] First chunk, request_id={litellm_request_id}")

                            # Accumulate content
                            has_content = False
                            if "choices" in chunk_json:
                                for choice in chunk_json["choices"]:
                                    if "delta" in choice and "content" in choice["delta"]:
                                        content_piece = choice["delta"]["content"]
                                        accumulated_content += content_piece
                                        has_content = True

                            # Log every 10th chunk with sample content
                            if chunk_counter % 10 == 0:
                                preview = accumulated_content[:100] if accumulated_content else "(no content yet)"
                                logger.info(f"[STREAM-CHUNK-{chunk_counter}] Accumulated so far: {len(accumulated_content)} chars, preview: {preview}...")

                            # Extract usage if present (usually in last chunk)
                            if "usage" in chunk_json:
                                accumulated_tokens = {
                                    "prompt": chunk_json["usage"].get("prompt_tokens", 0),
                                    "completion": chunk_json["usage"].get("completion_tokens", 0),
                                    "total": chunk_json["usage"].get("total_tokens", 0)
                                }
                                logger.info(f"[STREAM-USAGE] Received usage tokens: {accumulated_tokens}")

                            # Stream to client immediately
                            yield f"data: {chunk_data}\n\n"

                        except json.JSONDecodeError:
                            logger.warning(f"[STREAM-CHUNK] JSONDecodeError on chunk {chunk_counter}")
                            continue

            # After streaming completes, store in database
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            # Calculate cost (fallback to model pricing if not provided)
            cost_usd = 0.0
            from .models.model_aliases import ModelAlias
            model_record = db.query(ModelAlias).filter(
                ModelAlias.model_alias == primary_model
            ).first()

            if model_record and model_record.pricing_input and model_record.pricing_output:
                cost_usd = (
                    (accumulated_tokens["prompt"] * float(model_record.pricing_input) / 1_000_000) +
                    (accumulated_tokens["completion"] * float(model_record.pricing_output) / 1_000_000)
                )

            # Store LLM call record
            llm_call = LLMCall(
                job_id=job_id_value,
                litellm_request_id=litellm_request_id,
                model_used=primary_model,
                model_group_used=request.model,
                resolved_model=primary_model,
                prompt_tokens=accumulated_tokens["prompt"],
                completion_tokens=accumulated_tokens["completion"],
                total_tokens=accumulated_tokens["total"],
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                purpose=request.purpose,
                request_data={"messages": request.messages, "model": request.model},
                response_data={"content": accumulated_content, "streaming": True}
            )

            db.add(llm_call)
            db.commit()
            llm_call_successful = True

            # Log final streaming summary
            logger.info(f"[STREAM-COMPLETE] Total chunks: {chunk_counter}, Content length: {len(accumulated_content)} chars, Tokens: {accumulated_tokens}")

            # Step 3: Complete job and deduct credits
            job_to_complete = db.query(Job).filter(Job.job_id == job_id_value).first()
            if job_to_complete:
                job_to_complete.status = JobStatus.COMPLETED
                job_to_complete.completed_at = datetime.utcnow()

                # Calculate costs
                costs = calculate_job_costs(db, job_id_value)

                # Credit deduction based on budget mode
                credit_manager = get_credit_manager(db)
                team_credits_refresh = db.query(TeamCredits).filter(
                    TeamCredits.team_id == team_id_value
                ).first()

                if llm_call_successful and not job_to_complete.credit_applied and team_credits_refresh:
                    try:
                        # Calculate credits to deduct based on budget mode
                        credits_to_deduct = MINIMUM_CREDITS_PER_JOB

                        if budget_mode == "consumption_usd":
                            credits_per_dollar_val = float(credits_per_dollar) if credits_per_dollar else DEFAULT_CREDITS_PER_DOLLAR
                            credits_to_deduct = int(costs["total_cost_usd"] * credits_per_dollar_val)
                            credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, credits_to_deduct)
                        elif budget_mode == "consumption_tokens":
                            tokens_per_credit_val = tokens_per_credit if tokens_per_credit else DEFAULT_TOKENS_PER_CREDIT
                            credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, costs["total_tokens"] // tokens_per_credit_val)

                        credit_manager.deduct_credit(
                            team_id=team_id_value,
                            job_id=job_id_value,
                            credits_amount=credits_to_deduct,
                            reason=f"Streaming single-call job {request.job_type} completed ({budget_mode} mode: {credits_to_deduct} credits)"
                        )
                        job_to_complete.credit_applied = True

                    except InsufficientCreditsError as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Job {job_id_value} completed but couldn't deduct credit: {str(e)}")

                db.commit()

                # Store cost summary
                cost_summary = JobCostSummary(
                    job_id=job_id_value,
                    total_calls=costs["total_calls"],
                    successful_calls=costs["successful_calls"],
                    failed_calls=costs["failed_calls"],
                    total_tokens=costs["total_tokens"],
                    total_cost_usd=costs["total_cost_usd"],
                    avg_latency_ms=costs["avg_latency_ms"],
                    total_duration_seconds=int((job_to_complete.completed_at - job_to_complete.created_at).total_seconds())
                )
                db.merge(cost_summary)
                db.commit()

        except Exception as e:
            # Log the exception with full traceback
            import traceback
            logger.error(f"[STREAM-ERROR] Exception during streaming: {str(e)}")
            logger.error(f"[STREAM-ERROR] Traceback:\n{traceback.format_exc()}")

            # Record failed call
            llm_call = LLMCall(
                job_id=job_id_value,
                model_group_used=request.model,
                purpose=request.purpose,
                error=str(e),
                request_data={"messages": request.messages, "model": request.model}
            )
            db.add(llm_call)

            # Mark job as failed
            job_to_fail = db.query(Job).filter(Job.job_id == job_id_value).first()
            if job_to_fail:
                job_to_fail.status = JobStatus.FAILED
                job_to_fail.completed_at = datetime.utcnow()
                job_to_fail.error_message = str(e)

            db.commit()

            # Send error to client
            import json
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_and_complete(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.post("/api/jobs/{job_id}/complete", response_model=JobCompleteResponse, tags=["jobs"])
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
    from .models.credits import TeamCredits
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

    # Update job status (convert to uppercase for enum)
    job.status = JobStatus(request.status.upper())
    job.completed_at = datetime.utcnow()
    if request.error_message:
        job.error_message = request.error_message
    if request.metadata:
        job.job_metadata.update(request.metadata)

    # Calculate costs
    costs = calculate_job_costs(db, job.job_id)

    # Credit deduction logic with flexible budget modes
    credit_manager = get_credit_manager(db)

    # Get team's budget mode
    team_credits = db.query(TeamCredits).filter(
        TeamCredits.team_id == job.team_id
    ).first()

    # Deduct credit only if:
    # 1. Job status is "completed" (not "failed")
    # 2. Credit hasn't already been applied
    # Note: We trust the client's status field - if they mark as "completed", we charge
    # This allows retries where some calls fail but job ultimately succeeds
    if (request.status == "completed" and
        not job.credit_applied and
        team_credits):

        try:
            # Calculate credits to deduct based on budget mode
            credits_to_deduct = MINIMUM_CREDITS_PER_JOB  # Default: job_based (1 credit)

            if team_credits.budget_mode == "consumption_usd":
                # Credits based on actual USD cost
                # Use team-specific or default credits_per_dollar
                credits_per_dollar = float(team_credits.credits_per_dollar) if team_credits.credits_per_dollar else DEFAULT_CREDITS_PER_DOLLAR
                credits_to_deduct = int(costs["total_cost_usd"] * credits_per_dollar)
                # Minimum 1 credit for any successful job
                credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, credits_to_deduct)
            elif team_credits.budget_mode == "consumption_tokens":
                # Credits based on tokens used
                # Use team-specific tokens_per_credit if available, otherwise use default
                tokens_per_credit = team_credits.tokens_per_credit if team_credits.tokens_per_credit else DEFAULT_TOKENS_PER_CREDIT
                credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, costs["total_tokens"] // tokens_per_credit)
            # else: job_based mode, use MINIMUM_CREDITS_PER_JOB (1 credit)

            # Deduct credits
            credit_manager.deduct_credit(
                team_id=job.team_id,
                job_id=job.job_id,
                credits_amount=credits_to_deduct,
                reason=f"Job {job.job_type} completed ({team_credits.budget_mode} mode: {credits_to_deduct} credits)"
            )
            job.credit_applied = True

            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Deducted {credits_to_deduct} credits for job {job_id} "
                f"(mode: {team_credits.budget_mode}, cost: ${costs['total_cost_usd']}, tokens: {costs['total_tokens']})"
            )
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

    # Get updated credit balance (refresh the existing team_credits object)
    db.refresh(team_credits)

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


@app.get("/api/jobs/{job_id}", tags=["jobs"])
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


@app.patch("/api/jobs/{job_id}/metadata", tags=["jobs"])
async def update_job_metadata(
    job_id: str,
    request: JobMetadataUpdateRequest,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Append metadata to a job's existing metadata.

    This endpoint allows teams to enrich job metadata during execution,
    particularly useful for:
    - Chat applications tracking conversation turns
    - Multi-step agent workflows recording intermediate results
    - Adding business context as the job progresses

    The provided metadata will be merged with existing job metadata.

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

    # Initialize job_metadata if None
    if job.job_metadata is None:
        job.job_metadata = {}

    # Merge new metadata with existing metadata
    job.job_metadata.update(request.metadata)

    # Mark the attribute as modified for SQLAlchemy to detect the change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(job, 'job_metadata')

    db.commit()
    db.refresh(job)

    return {
        "job_id": str(job.job_id),
        "metadata": job.job_metadata,
        "updated_at": datetime.utcnow().isoformat()
    }


@app.get("/api/jobs/{job_id}/costs", tags=["jobs"])
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


@app.get("/api/teams/{team_id}/usage", tags=["teams"])
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


@app.get("/api/teams/{team_id}/jobs", tags=["jobs"])
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
