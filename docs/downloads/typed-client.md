# Download Typed Client

Get the type-safe Python client to integrate with the SaaS LiteLLM API.

## Quick Download

**File:** `typed_client.py`

[:octicons-download-24: Download typed_client.py](../examples/typed_client.py){ .md-button .md-button--primary }

## Installation

### Step 1: Download the Client

Choose one of these methods:

**Method A: Direct Download**
```bash
# Download from your SaaS API server
curl -O http://YOUR_DOMAIN:8003/examples/typed_client.py
```

**Method B: GitHub (if available)**
```bash
curl -O https://raw.githubusercontent.com/YOUR_ORG/SaasLiteLLM/main/examples/typed_client.py
```

**Method C: Copy from Repository**
```bash
# If you have repo access
cp /path/to/SaasLiteLLM/examples/typed_client.py your_project/saas_litellm_client.py
```

### Step 2: Install Dependencies

```bash
pip install httpx pydantic
```

### Step 3: Configure

Create a `.env` file:

```bash
# .env
SAAS_LITELLM_API_URL=http://your-domain:8003
SAAS_LITELLM_TEAM_ID=your-team-id
SAAS_LITELLM_VIRTUAL_KEY=sk-your-virtual-key-here
```

## Client Source Code

If you prefer to copy/paste, here's the complete client:

```python
"""
Type-safe client for SaaS LiteLLM API

This client provides full type safety using Pydantic models and supports
both streaming and non-streaming responses.
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


class JobCompletionResult(BaseModel):
    """Job completion response"""
    job_id: str
    status: str
    credits_remaining: int
    total_calls: int


# ============================================================================
# Type-safe Client
# ============================================================================

T = TypeVar('T', bound=BaseModel)


class SaaSLLMClient:
    """
    Type-safe async client for SaaS LiteLLM API

    Features:
    - Type hints and Pydantic validation
    - Context manager support (async with)
    - Automatic job management
    - Streaming and non-streaming
    - Structured outputs with Pydantic models
    """

    def __init__(
        self,
        base_url: str,
        team_id: str,
        virtual_key: str,
        timeout: float = 120.0
    ):
        """
        Initialize client

        Args:
            base_url: SaaS API base URL (e.g., "http://localhost:8003")
            team_id: Your team ID
            virtual_key: Your team's virtual API key
            timeout: Request timeout in seconds (default: 120)
        """
        self.base_url = base_url.rstrip('/')
        self.team_id = team_id
        self.virtual_key = virtual_key
        self.timeout = timeout

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
            job_type: Type of job (e.g., "chat", "analysis", "extraction")
            metadata: Optional metadata dictionary

        Returns:
            Job ID (UUID string)
        """
        response = await self.client.post(
            f"{self.base_url}/api/jobs/create",
            json={
                "team_id": self.team_id,
                "job_type": job_type,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        job_response = JobResponse(**response.json())
        return job_response.job_id

    async def complete_job(
        self,
        job_id: str,
        status: str = "completed",
        metadata: Optional[Dict[str, Any]] = None
    ) -> JobCompletionResult:
        """
        Complete a job

        Args:
            job_id: Job ID from create_job()
            status: Final status ("completed" or "failed")
            metadata: Optional result metadata

        Returns:
            JobCompletionResult with credits remaining
        """
        response = await self.client.post(
            f"{self.base_url}/api/jobs/{job_id}/complete",
            json={
                "status": status,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        return JobCompletionResult(**response.json())

    # ========================================================================
    # Chat Completions (Non-streaming)
    # ========================================================================

    async def chat(
        self,
        job_id: str,
        messages: List[Union[Dict[str, str], Message]],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> ChatCompletionResponse:
        """
        Make a non-streaming chat completion call

        Args:
            job_id: Job ID from create_job()
            messages: List of message dictionaries
            model: Model name (e.g., "gpt-4", "claude-3-opus")
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Reduce repetition (-2.0 to 2.0)
            presence_penalty: Encourage new topics (-2.0 to 2.0)
            stop: Stop sequence(s)

        Returns:
            ChatCompletionResponse with full response
        """
        # Convert Message objects to dicts
        message_dicts = [
            msg.model_dump() if isinstance(msg, BaseModel) else msg
            for msg in messages
        ]

        # Build request payload
        payload = {
            "model": model,
            "messages": message_dicts,
            "temperature": temperature,
        }

        # Add optional parameters
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if stop is not None:
            payload["stop"] = stop

        response = await self.client.post(
            f"{self.base_url}/api/jobs/{job_id}/llm-call",
            json=payload
        )
        response.raise_for_status()

        return ChatCompletionResponse(**response.json())

    # ========================================================================
    # Chat Completions (Streaming)
    # ========================================================================

    async def chat_stream(
        self,
        job_id: str,
        messages: List[Union[Dict[str, str], Message]],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Make a streaming chat completion call

        Args:
            Same as chat() method

        Yields:
            StreamChunk objects as they arrive
        """
        # Convert Message objects to dicts
        message_dicts = [
            msg.model_dump() if isinstance(msg, BaseModel) else msg
            for msg in messages
        ]

        # Build request payload
        payload = {
            "model": model,
            "messages": message_dicts,
            "temperature": temperature,
        }

        # Add optional parameters
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if stop is not None:
            payload["stop"] = stop

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/jobs/{job_id}/llm-call-stream",
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
    # Structured Outputs
    # ========================================================================

    async def structured_output(
        self,
        job_id: str,
        messages: List[Union[Dict[str, str], Message]],
        response_model: Type[T],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> T:
        """
        Get a type-safe structured output using Pydantic model

        Args:
            job_id: Job ID from create_job()
            messages: List of messages
            response_model: Pydantic model class for the response
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Instance of response_model

        Example:
            class Person(BaseModel):
                name: str
                age: int
                email: str

            person = await client.structured_output(
                job_id=job_id,
                messages=[{"role": "user", "content": "Extract: John, 30, john@example.com"}],
                response_model=Person
            )
        """
        # Build JSON schema from Pydantic model
        schema = response_model.model_json_schema()

        response = await self.chat(
            job_id=job_id,
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Parse response content as Pydantic model
        content = response.choices[0].message.get("content", "")
        return response_model.model_validate_json(content)
```

## Usage Examples

### Basic Usage

```python
import asyncio
from saas_litellm_client import SaaSLLMClient

async def main():
    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="your-team-id",
        virtual_key="sk-your-virtual-key"
    ) as client:

        # Create job
        job_id = await client.create_job("chat_example")

        # Make LLM call
        response = await client.chat(
            job_id=job_id,
            messages=[
                {"role": "user", "content": "What is Python?"}
            ]
        )

        print(response.choices[0].message["content"])

        # Complete job
        await client.complete_job(job_id, "completed")

asyncio.run(main())
```

### Streaming Example

```python
async def stream_example():
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("streaming_chat")

        print("Assistant: ", end="", flush=True)

        async for chunk in client.chat_stream(
            job_id=job_id,
            messages=[{"role": "user", "content": "Write a short poem"}]
        ):
            if chunk.choices:
                content = chunk.choices[0].delta.get("content", "")
                print(content, end="", flush=True)

        await client.complete_job(job_id, "completed")
```

### Structured Output Example

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    email: str

async def extract_person():
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("person_extraction")

        person = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": "Extract: Sarah Johnson, 28, sarah@example.com"
            }],
            response_model=Person
        )

        print(f"Name: {person.name}, Age: {person.age}")

        await client.complete_job(job_id, "completed")
```

## Next Steps

- **[See Full Examples](../examples/basic-usage.md)** - More usage patterns
- **[Streaming Guide](../integration/streaming.md)** - Real-time responses
- **[Structured Outputs](../integration/structured-outputs.md)** - Type-safe extraction
- **[Error Handling](../integration/error-handling.md)** - Handle failures

## Support

Having issues? Check the [troubleshooting guide](../integration/error-handling.md) or contact support.
