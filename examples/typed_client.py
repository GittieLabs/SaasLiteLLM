"""
Type-safe client for SaaS LiteLLM API

This client provides full type safety using Pydantic models and supports
both streaming and non-streaming responses. It's compatible with Instructor
for structured outputs.

Example Usage:
    # Basic usage
    client = SaaSLLMClient(
        api_url="http://localhost:8003",
        virtual_key="sk-xxx...",
        team_id="team-alpha"
    )

    # Create job
    job_id = await client.create_job("chat")

    # Make typed call
    response = await client.chat(
        model_group="chat-fast",
        messages=[{"role": "user", "content": "Hello"}]
    )

    # Stream typed call
    async for chunk in client.chat_stream(
        model_group="chat-fast",
        messages=[{"role": "user", "content": "Write essay"}]
    ):
        print(chunk)
"""
from typing import Optional, List, Dict, Any, AsyncGenerator, TypeVar, Type, Union
from pydantic import BaseModel, Field
import httpx
import json


# ============================================================================
# Request/Response Models
# ============================================================================

class Message(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name of the speaker")


class FunctionCall(BaseModel):
    """Function call from the model"""
    name: str
    arguments: str  # JSON string


class ToolCall(BaseModel):
    """Tool call from the model"""
    id: str
    type: str
    function: FunctionCall


class ChatChoice(BaseModel):
    """Single choice in chat completion"""
    index: int
    message: Optional[Dict[str, Any]] = None
    delta: Optional[Dict[str, Any]] = None  # For streaming
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    """Token usage information"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """Non-streaming chat completion response"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Optional[Usage] = None


class StreamChunk(BaseModel):
    """Streaming chat completion chunk"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Optional[Usage] = None


class JobResponse(BaseModel):
    """Job creation response"""
    job_id: str
    team_id: str
    status: str
    created_at: str


# ============================================================================
# Type-safe Client
# ============================================================================

T = TypeVar('T', bound=BaseModel)


class SaaSLLMClient:
    """
    Type-safe client for SaaS LiteLLM API

    Supports:
    - Typed request/response models
    - Streaming and non-streaming
    - Instructor-compatible structured outputs
    - Function calling
    """

    def __init__(
        self,
        api_url: str,
        virtual_key: str,
        team_id: str,
        timeout: float = 120.0
    ):
        """
        Initialize client

        Args:
            api_url: SaaS API base URL (e.g., "http://localhost:8003")
            virtual_key: Team virtual key for authentication
            team_id: Team ID
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.virtual_key = virtual_key
        self.team_id = team_id
        self.timeout = timeout
        self.current_job_id: Optional[str] = None

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {virtual_key}",
                "Content-Type": "application/json"
            }
        )

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ========================================================================
    # Job Management
    # ========================================================================

    async def create_job(
        self,
        job_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new job

        Args:
            job_type: Type of job (e.g., "chat", "agent_task")
            metadata: Optional metadata dictionary

        Returns:
            Job ID
        """
        response = await self.client.post(
            f"{self.api_url}/api/jobs/create",
            json={
                "team_id": self.team_id,
                "job_type": job_type,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        job_response = JobResponse(**response.json())
        self.current_job_id = job_response.job_id
        return job_response.job_id

    async def complete_job(
        self,
        job_id: Optional[str] = None,
        status: str = "completed",
        result: Optional[Dict[str, Any]] = None
    ):
        """
        Complete a job

        Args:
            job_id: Job ID (uses current_job_id if not provided)
            status: Final status ("completed", "failed")
            result: Optional result data
        """
        job_id = job_id or self.current_job_id
        if not job_id:
            raise ValueError("No job ID provided and no current job")

        await self.client.post(
            f"{self.api_url}/api/jobs/{job_id}/complete",
            json={
                "status": status,
                "result": result or {}
            }
        )

        if job_id == self.current_job_id:
            self.current_job_id = None

    # ========================================================================
    # Chat Completions (Non-streaming)
    # ========================================================================

    async def chat(
        self,
        model_group: str,
        messages: List[Union[Dict[str, str], Message]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
        purpose: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> ChatCompletionResponse:
        """
        Make a non-streaming chat completion call

        Args:
            model_group: Model group name (e.g., "chat-fast")
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Response format for structured outputs
            tools: List of tools for function calling
            tool_choice: Tool choice strategy
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop: Stop sequences
            purpose: Purpose of the call (for tracking)
            job_id: Job ID (uses current_job_id if not provided)

        Returns:
            ChatCompletionResponse with full response
        """
        job_id = job_id or self.current_job_id
        if not job_id:
            raise ValueError("No job ID provided and no current job. Call create_job() first.")

        # Convert Message objects to dicts
        message_dicts = [
            msg.model_dump() if isinstance(msg, BaseModel) else msg
            for msg in messages
        ]

        # Build request payload
        payload = {
            "model_group": model_group,
            "messages": message_dicts,
            "temperature": temperature,
        }

        # Add optional parameters
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format is not None:
            payload["response_format"] = response_format
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if stop is not None:
            payload["stop"] = stop
        if purpose is not None:
            payload["purpose"] = purpose

        response = await self.client.post(
            f"{self.api_url}/api/jobs/{job_id}/llm-call",
            json=payload
        )
        response.raise_for_status()

        return ChatCompletionResponse(**response.json())

    # ========================================================================
    # Chat Completions (Streaming)
    # ========================================================================

    async def chat_stream(
        self,
        model_group: str,
        messages: List[Union[Dict[str, str], Message]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
        purpose: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Make a streaming chat completion call

        Args:
            Same as chat() method

        Yields:
            StreamChunk objects as they arrive
        """
        job_id = job_id or self.current_job_id
        if not job_id:
            raise ValueError("No job ID provided and no current job. Call create_job() first.")

        # Convert Message objects to dicts
        message_dicts = [
            msg.model_dump() if isinstance(msg, BaseModel) else msg
            for msg in messages
        ]

        # Build request payload
        payload = {
            "model_group": model_group,
            "messages": message_dicts,
            "temperature": temperature,
        }

        # Add optional parameters
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format is not None:
            payload["response_format"] = response_format
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if stop is not None:
            payload["stop"] = stop
        if purpose is not None:
            payload["purpose"] = purpose

        async with self.client.stream(
            "POST",
            f"{self.api_url}/api/jobs/{job_id}/llm-call-stream",
            json=payload
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk_data = line[6:]  # Remove "data: " prefix

                    if chunk_data == "[DONE]":
                        break

                    try:
                        chunk_json = json.loads(chunk_data)

                        # Handle error chunks
                        if "error" in chunk_json:
                            raise Exception(f"Stream error: {chunk_json['error']}")

                        yield StreamChunk(**chunk_json)

                    except json.JSONDecodeError:
                        continue

    # ========================================================================
    # Instructor-Compatible Structured Outputs
    # ========================================================================

    async def structured_output(
        self,
        model_group: str,
        messages: List[Union[Dict[str, str], Message]],
        response_model: Type[T],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        purpose: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> T:
        """
        Get a structured output using Pydantic model

        This is compatible with Instructor's approach but uses the SaaS API.

        Args:
            model_group: Model group name
            messages: List of messages
            response_model: Pydantic model class for the response
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            purpose: Purpose of the call
            job_id: Job ID

        Returns:
            Instance of response_model

        Example:
            class Person(BaseModel):
                name: str
                age: int

            person = await client.structured_output(
                model_group="chat-fast",
                messages=[{"role": "user", "content": "Extract: John is 30"}],
                response_model=Person
            )
        """
        # Build JSON schema from Pydantic model
        schema = response_model.model_json_schema()

        response = await self.chat(
            model_group=model_group,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": schema,
                    "strict": True
                }
            },
            purpose=purpose,
            job_id=job_id
        )

        # Parse response content as Pydantic model
        content = response.choices[0].message.get("content", "")
        return response_model.model_validate_json(content)

    async def structured_output_stream(
        self,
        model_group: str,
        messages: List[Union[Dict[str, str], Message]],
        response_model: Type[T],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        purpose: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a structured output (yields partial JSON)

        Args:
            Same as structured_output()

        Yields:
            Partial JSON strings as they arrive

        Note:
            You'll need to accumulate the full JSON and then parse it with
            response_model.model_validate_json(accumulated_json)
        """
        # Build JSON schema from Pydantic model
        schema = response_model.model_json_schema()

        async for chunk in self.chat_stream(
            model_group=model_group,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": schema,
                    "strict": True
                }
            },
            purpose=purpose,
            job_id=job_id
        ):
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta and "content" in delta:
                    yield delta["content"]
