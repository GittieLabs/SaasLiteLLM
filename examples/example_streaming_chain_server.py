"""
Example: Client Server - Middle tier between UI and SaaS API

This FastAPI server demonstrates the streaming chain:
UI (Browser) ← SSE ← Client Server (this file) ← SSE ← SaaS API ← LiteLLM

The server:
1. Receives requests from the UI
2. Forwards them to the SaaS API with authentication
3. Streams responses back to the UI in real-time
4. Manages job lifecycle

Run this server:
    python example_streaming_chain_server.py

Then open example_streaming_chain_ui.html in a browser
"""
import asyncio
import sys
import os

# Add parent directory to path so we can import typed_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

from typed_client import SaaSLLMClient, Message


# ============================================================================
# Configuration
# ============================================================================

# SaaS API configuration (could be environment variables)
SAAS_API_URL = "http://localhost:8003"
SAAS_VIRTUAL_KEY = "sk-1234"  # Replace with actual virtual key
SAAS_TEAM_ID = "team-alpha"

# Create FastAPI app
app = FastAPI(title="Client Server", version="1.0.0")

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your UI domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global SaaS client
saas_client: Optional[SaaSLLMClient] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request from UI to client server"""
    messages: List[Dict[str, str]]
    model_group: str = "chat-fast"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Non-streaming response to UI"""
    content: str
    usage: Optional[Dict[str, int]] = None
    job_id: str


# ============================================================================
# Lifecycle
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize SaaS client on startup"""
    global saas_client
    saas_client = SaaSLLMClient(
        api_url=SAAS_API_URL,
        virtual_key=SAAS_VIRTUAL_KEY,
        team_id=SAAS_TEAM_ID,
        timeout=120.0
    )
    print(f"Client Server started")
    print(f"Connected to SaaS API: {SAAS_API_URL}")
    print(f"Team: {SAAS_TEAM_ID}")


@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown"""
    global saas_client
    if saas_client:
        await saas_client.close()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Client Server",
        "status": "running",
        "saas_api": SAAS_API_URL,
        "team_id": SAAS_TEAM_ID
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Non-streaming chat endpoint

    Flow:
    1. Create job in SaaS API
    2. Make LLM call through SaaS API
    3. Return complete response to UI
    4. Complete job
    """
    if not saas_client:
        raise HTTPException(status_code=503, detail="Client not initialized")

    try:
        # Create job
        job_id = await saas_client.create_job(
            job_type="chat",
            metadata={"source": "client_server"}
        )

        # Make LLM call
        response = await saas_client.chat(
            model_group=request.model_group,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            purpose="chat_request",
            job_id=job_id
        )

        # Extract content
        content = response.choices[0].message.get("content", "")

        # Complete job
        await saas_client.complete_job(
            job_id=job_id,
            status="completed",
            result={"response": content}
        )

        # Return to UI
        return ChatResponse(
            content=content,
            usage=response.usage.model_dump() if response.usage else None,
            job_id=job_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint

    Flow:
    1. Create job in SaaS API
    2. Stream LLM response from SaaS API
    3. Forward stream to UI in real-time (zero buffering!)
    4. Complete job after stream ends

    This demonstrates the full streaming chain:
    UI ← SSE ← Client Server ← SSE ← SaaS API ← SSE ← LiteLLM
    """
    if not saas_client:
        raise HTTPException(status_code=503, detail="Client not initialized")

    async def stream_to_ui():
        """Generator that streams from SaaS API to UI"""
        job_id = None
        accumulated_content = ""

        try:
            # Create job
            job_id = await saas_client.create_job(
                job_type="streaming_chat",
                metadata={"source": "client_server", "stream": True}
            )

            # Send job ID to UI first
            yield f"data: {{'event': 'job_created', 'job_id': '{job_id}'}}\n\n"

            # Stream from SaaS API
            async for chunk in saas_client.chat_stream(
                model_group=request.model_group,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                purpose="streaming_chat",
                job_id=job_id
            ):
                # Extract content
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta and "content" in delta:
                        content = delta["content"]
                        accumulated_content += content

                        # Forward to UI immediately (no buffering!)
                        # Send as Server-Sent Event
                        yield f"data: {{'event': 'content', 'content': {repr(content)}}}\n\n"

                    # Send usage info if present
                    if chunk.usage:
                        usage_dict = chunk.usage.model_dump()
                        yield f"data: {{'event': 'usage', 'usage': {usage_dict}}}\n\n"

            # Send completion event
            yield f"data: {{'event': 'done'}}\n\n"

            # Complete job
            if job_id:
                await saas_client.complete_job(
                    job_id=job_id,
                    status="completed",
                    result={"response": accumulated_content}
                )

        except Exception as e:
            # Send error to UI
            error_msg = str(e).replace("'", "\\'")
            yield f"data: {{'event': 'error', 'error': '{error_msg}'}}\n\n"

            # Mark job as failed
            if job_id:
                try:
                    await saas_client.complete_job(
                        job_id=job_id,
                        status="failed",
                        result={"error": str(e)}
                    )
                except:
                    pass

    return StreamingResponse(
        stream_to_ui(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Client Server")
    print("=" * 60)
    print(f"Server will run at: http://localhost:8001")
    print(f"SaaS API: {SAAS_API_URL}")
    print(f"Team: {SAAS_TEAM_ID}")
    print()
    print("Open example_streaming_chain_ui.html in a browser to test")
    print("=" * 60)
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
