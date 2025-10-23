"""
Streaming LLM endpoint for SaaS API
Supports Server-Sent Events (SSE) for real-time streaming
"""
from fastapi import HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import httpx
import json
import uuid

from .saas_api import LLMCallRequest, get_db
from .auth.dependencies import verify_virtual_key
from .models.job_tracking import Job, LLMCall, JobStatus
from .models.credits import TeamCredits
from .services.model_resolver import ModelResolver, ModelResolutionError
from .config.settings import settings
from .utils.cost_calculator import (
    calculate_token_costs,
    apply_markup,
    get_model_pricing
)


async def make_llm_call_stream(
    job_id: str,
    request: LLMCallRequest,
    db: Session = Depends(get_db),
    authenticated_team_id: str = Depends(verify_virtual_key)
):
    """
    Make a streaming LLM call within a job context.
    Returns Server-Sent Events (SSE) stream.

    Supports:
    - Text streaming
    - Structured output streaming (response_format)
    - Function calling streaming (tools)
    - All OpenAI parameters

    The stream forwards directly from LiteLLM to minimize latency.
    """
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

    if not team_credits or not team_credits.virtual_key:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{job.team_id}' not found or has no virtual key"
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

    # Track model group usage
    if not job.model_groups_used:
        job.model_groups_used = []
    if request.model_group not in job.model_groups_used:
        job.model_groups_used.append(request.model_group)
        db.commit()

    # Create streaming generator
    async def stream_llm_response():
        litellm_url = f"{settings.litellm_proxy_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {team_credits.virtual_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": primary_model,
            "messages": request.messages,
            "temperature": request.temperature,
            "stream": True,  # Enable streaming
            "user": job.team_id,
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
        accumulated_tool_calls = []
        accumulated_tokens = {"prompt": 0, "completion": 0, "total": 0}
        litellm_request_id = None
        start_time = datetime.utcnow()
        has_error = False
        error_message = None

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

                                        # Function/tool calls
                                        if "delta" in choice and "tool_calls" in choice["delta"]:
                                            # Accumulate tool calls (they stream incrementally)
                                            for tool_call_delta in choice["delta"]["tool_calls"]:
                                                # This needs special handling to merge deltas
                                                pass  # LiteLLM handles this

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

            # Get model pricing for the resolved model
            pricing = get_model_pricing(primary_model)

            # Calculate complete costs with token pricing
            token_costs = calculate_token_costs(
                prompt_tokens=accumulated_tokens["prompt"],
                completion_tokens=accumulated_tokens["completion"],
                input_price_per_million=pricing["input"],
                output_price_per_million=pricing["output"]
            )

            # Apply team markup
            markup_percentage = float(team_credits.cost_markup_percentage) if team_credits.cost_markup_percentage else 0.0
            markup_costs = apply_markup(
                provider_cost_usd=token_costs["provider_cost_usd"],
                markup_percentage=markup_percentage
            )

            # Store LLM call record with complete cost tracking
            llm_call = LLMCall(
                job_id=job.job_id,
                litellm_request_id=litellm_request_id,
                model_used=primary_model,
                model_group_used=request.model_group,
                resolved_model=primary_model,
                prompt_tokens=accumulated_tokens["prompt"],
                completion_tokens=accumulated_tokens["completion"],
                total_tokens=accumulated_tokens["total"],
                cost_usd=token_costs["provider_cost_usd"],  # Legacy field
                input_cost_usd=token_costs["input_cost_usd"],
                output_cost_usd=token_costs["output_cost_usd"],
                provider_cost_usd=token_costs["provider_cost_usd"],
                client_cost_usd=markup_costs["client_cost_usd"],
                model_pricing_input=pricing["input"],
                model_pricing_output=pricing["output"],
                latency_ms=latency_ms,
                purpose=request.purpose,
                request_data={"messages": request.messages, "model_group": request.model_group},
                response_data={"content": accumulated_content, "streaming": True}
            )

            db.add(llm_call)
            db.commit()

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

            # Send error to client
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
